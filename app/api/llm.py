"""LLM-клиент на чистом urllib (без внешних HTTP-библиотек)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class LLMError(Exception):
    """Ошибка при обращении к LLM API."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Не следует по редиректам, чтобы заголовок Authorization не утёк."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise LLMError(
            f"LLM API вернул редирект {code} на {newurl!r}. "
            "Проверьте LLM_BASE_URL."
        )


class LLMClient:
    """Клиент к OpenAI-совместимому API (OpenRouter, etc.)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._opener = urllib.request.build_opener(_NoRedirectHandler)

    def chat(self, messages: list[dict[str, Any]]) -> str:
        """Выполняет POST /chat/completions и возвращает текстовый ответ ассистента."""
        url = f"{self._base_url}/chat/completions"
        payload = json.dumps(
            {"model": self._model, "messages": messages}
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
                "HTTP-Referer": "https://github.com/RAG-Ilya-Ivan",
                "X-Title": "RAG Validator",
            },
            method="POST",
        )

        try:
            with self._opener.open(req, timeout=self._timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise LLMError(
                f"HTTP {exc.code} от LLM API: {body_text[:500]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"Ошибка соединения с LLM API: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMError("Таймаут при обращении к LLM API.") from exc

        try:
            data = json.loads(body)
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMError(
                f"Неожиданный формат ответа LLM: {body[:500]}"
            ) from exc
