"""FastAPI приложение — RAG-валидатор архитектурных решений и ТЗ."""
from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.api.services import ValidationResult, validate_document

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Инициализация приложения
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RAG-валидатор архитектурных решений и ТЗ",
    description=(
        "Принимает черновик ТЗ или описание архитектуры и возвращает "
        "список нарушений со ссылками на источники (BM25 + LLM)."
    ),
    version="0.1.0",
)

# Статика и шаблоны
_BASE_DIR = Path(__file__).parent

_static_dir = _BASE_DIR / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

templates = Jinja2Templates(directory=str(_BASE_DIR / "templates"))


# ---------------------------------------------------------------------------
# Схема запроса
# ---------------------------------------------------------------------------


class ValidateRequest(BaseModel):
    text: str


# ---------------------------------------------------------------------------
# Хелпер для сериализации ValidationResult
# ---------------------------------------------------------------------------


def _result_to_dict(result: ValidationResult) -> dict:
    return asdict(result)


# ---------------------------------------------------------------------------
# Роуты
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Главная страница — рендерит templates/index.html."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/validate", response_class=JSONResponse)
async def validate(body: ValidateRequest) -> JSONResponse:
    """Принимает текст и возвращает ValidationResult в JSON.

    Используется веб-интерфейсом.
    """
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Поле 'text' не должно быть пустым.")
    try:
        result = validate_document(body.text)
    except Exception as exc:
        logger.exception("Unexpected error during validation")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return JSONResponse(content=_result_to_dict(result))


@app.post("/api/validate", response_class=JSONResponse)
async def api_validate(body: ValidateRequest) -> JSONResponse:
    """То же самое что /validate, но предназначено для бенчмарка / API-клиентов."""
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Поле 'text' не должно быть пустым.")
    try:
        result = validate_document(body.text)
    except Exception as exc:
        logger.exception("Unexpected error during API validation")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return JSONResponse(content=_result_to_dict(result))


# ---------------------------------------------------------------------------
# Запуск напрямую
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
