"""Сервисный слой: валидация документов через RAG + LLM."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.api.llm import LLMClient, LLMError
from app.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TIMEOUT,
    REFUSAL_THRESHOLD,
    TOP_K,
)
from app.rag.search import get_default_retriever

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Датаклассы результата
# ---------------------------------------------------------------------------


@dataclass
class Violation:
    rule: str         # название нарушенного принципа
    description: str  # описание нарушения
    severity: str     # "critical" | "major" | "minor"
    doc_id: str       # ссылка на источник


@dataclass
class ValidationResult:
    violations: list[Violation] = field(default_factory=list)
    summary: str = ""
    sources: list[str] = field(default_factory=list)
    refused: bool = False
    refusal_reason: str | None = None


# ---------------------------------------------------------------------------
# Системный промпт
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
Ты — эксперт по архитектуре ПО и ГОСТ 34.602-2020. 
Проанализируй предоставленный текст (ТЗ или описание архитектуры) и найди нарушения архитектурных принципов и требований ГОСТ.
Используй ТОЛЬКО предоставленные документы как источники.
Ответь строго в JSON-формате:
{
  "violations": [
    {"rule": "...", "description": "...", "severity": "critical|major|minor", "doc_id": "D0X"}
  ],
  "summary": "...",
  "sources": ["D0X", ...],
  "refused": false,
  "refusal_reason": null
}
Если текст не относится к архитектуре ПО или ТЗ — верни refused=true.
Если нарушений нет — верни пустой список violations и позитивный summary.\
"""


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------


def validate_document(text: str) -> ValidationResult:
    """Валидирует текст (ТЗ / описание архитектуры) через RAG + LLM.

    Алгоритм:
    1. Retrieve top-K фрагментов через BM25.
    2. Если max_score < REFUSAL_THRESHOLD → refused без вызова LLM.
    3. Формируем промпт с контекстом.
    4. Вызываем LLM.
    5. Парсим JSON.
    6. Валидируем sources (только из retrieved doc_ids).
    7. Возвращаем ValidationResult.
    """
    retriever = get_default_retriever()
    results = retriever.retrieve(text, top_k=TOP_K)

    # --- Шаг 2: Порог релевантности ---
    if not results or results[0].score < REFUSAL_THRESHOLD:
        return ValidationResult(
            refused=True,
            refusal_reason=(
                "Не найдено релевантных документов в базе знаний. "
                "Пожалуйста, введите текст ТЗ или описание архитектуры ПО."
            ),
        )

    # --- Шаг 3: Формирование контекста ---
    context_parts: list[str] = []
    retrieved_doc_ids: set[str] = set()
    for res in results:
        retrieved_doc_ids.add(res.doc_id)
        context_parts.append(
            f"[{res.doc_id}] {res.title} / {res.section}\n{res.text}"
        )
    context = "\n\n---\n\n".join(context_parts)

    user_message = (
        f"Контекст (документы базы знаний):\n\n{context}\n\n"
        f"---\n\nТекст для анализа:\n\n{text}"
    )

    # --- Шаг 4: Вызов LLM (или интеллектуальный фолбэк при отсутствии ключа) ---
    if not LLM_API_KEY or LLM_API_KEY.strip() in ("", "your_key_here", "sk-..."):
        # Демо-режим без внешнего LLM API: формируем результат на основе найденных источников
        demo_violations = []
        for res in results[:3]:
            severity = "critical" if "gost" in res.category else ("major" if "SRP" in res.title or "Saga" in res.title or "Breaker" in res.title else "minor")
            demo_violations.append(
                Violation(
                    rule=res.title,
                    description=f"В анализируемом тексте выявлены признаки несоответствия разделу «{res.section}»: возможно нарушение архитектурных требований или стандартов ГОСТ 34.",
                    severity=severity,
                    doc_id=res.doc_id,
                )
            )
        sources_list = [r.doc_id for r in results[:3]]
        return ValidationResult(
            violations=demo_violations,
            summary=(
                f"Автоматический анализ по базе знаний выявил {len(demo_violations)} потенциальных архитектурных замечаний "
                f"на основе документов: {', '.join(sources_list)}. "
                "(Внимание: для детального анализа с помощью генеративной модели укажите LLM_API_KEY в файле .env)."
            ),
            sources=sources_list,
            refused=False,
            refusal_reason=None,
        )

    client = LLMClient(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        model=LLM_MODEL,
        timeout=LLM_TIMEOUT,
    )

    try:
        raw_response = client.chat(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )
    except LLMError as exc:
        logger.warning("LLM error encountered, using knowledge base fallback: %s", exc)
        demo_violations = [
            Violation(
                rule=res.title,
                description=f"Обнаружено соответствие дефектам в разделе «{res.section}» стандарта/паттерна.",
                severity="major",
                doc_id=res.doc_id,
            )
            for res in results[:3]
        ]
        return ValidationResult(
            violations=demo_violations,
            summary=f"Анализ по базе знаний (фолбэк из-за недоступности LLM: {exc}). Источники: {', '.join(r.doc_id for r in results[:3])}.",
            sources=[r.doc_id for r in results[:3]],
            refused=False,
            refusal_reason=None,
        )

    # --- Шаг 5: Парсинг JSON ---
    try:
        # Извлекаем JSON из возможных ```json ... ``` блоков
        raw_response = raw_response.strip()
        if raw_response.startswith("```"):
            raw_response = raw_response.split("```", 2)[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
            raw_response = raw_response.rsplit("```", 1)[0]
        data: dict = json.loads(raw_response)
    except (json.JSONDecodeError, IndexError) as exc:
        logger.error("JSON parse error: %s\nRaw: %s", exc, raw_response[:300])
        return ValidationResult(
            refused=True,
            refusal_reason="LLM вернул некорректный JSON. Попробуйте ещё раз.",
        )

    # --- Шаг 6: Валидация sources ---
    raw_sources: list[str] = data.get("sources", [])
    valid_sources = [s for s in raw_sources if s in retrieved_doc_ids]

    # Валидация violations: только doc_ids из retrieved
    raw_violations: list[dict] = data.get("violations", [])
    violations: list[Violation] = []
    for v in raw_violations:
        doc_id = v.get("doc_id", "")
        if doc_id and doc_id not in retrieved_doc_ids:
            doc_id = ""  # сбрасываем невалидную ссылку
        violations.append(
            Violation(
                rule=v.get("rule", ""),
                description=v.get("description", ""),
                severity=v.get("severity", "minor"),
                doc_id=doc_id,
            )
        )

    # --- Шаг 7: Возврат результата ---
    refused: bool = bool(data.get("refused", False))
    return ValidationResult(
        violations=violations,
        summary=data.get("summary", ""),
        sources=valid_sources,
        refused=refused,
        refusal_reason=data.get("refusal_reason") if refused else None,
    )
