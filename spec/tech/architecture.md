# Архитектура системы

## Общая схема

```
Пользователь
     │
     │  HTTP GET /
     ▼
 Web UI (HTML/JS)
     │
     │  POST /validate  { "query": "..." }
     ▼
 FastAPI (app/main.py + app/api/routes.py)
     │
     │  search(query, top_k=5)
     ▼
 RAG Engine (app/rag/)
     ├── text.py      ← нормализация, токенизация, стемминг
     ├── corpus.py    ← загрузка и чанкинг .md файлов
     ├── bm25.py      ← Okapi BM25 индекс
     └── search.py    ← оркестрация поиска, порог relevance
     │
     │  top-5 чанков (или refusal если score < 1.0)
     ▼
 LLM Client (app/api/llm.py)
     │  OpenAI-compatible Chat Completions API
     ▼
 JSON Response → FastAPI → Web UI
                                         ▲
                              BM25 Index ┘ ← Corpus (data/corpus/*.md)
```

## Компоненты

### `app/rag/` — RAG-движок

| Файл | Ответственность |
|---|---|
| `text.py` | Нормализация текста: lowercase, удаление знаков препинания, Snowball-стемминг (ru), стоп-слова |
| `corpus.py` | Загрузка `*.md` из `data/corpus/`, чанкинг по заголовкам `##` / `###` |
| `bm25.py` | Построение и хранение инвертированного индекса BM25, скоринг |
| `search.py` | Поиск top-k чанков, агрегация по документам, применение порога relevance |

### `app/api/` — API-слой

| Файл | Ответственность |
|---|---|
| `routes.py` | FastAPI router: `POST /validate`, входная валидация (Pydantic), форматирование ответа |
| `llm.py` | HTTP-клиент к LLM API, построение промпта, парсинг JSON-ответа, таймаут и retry |

### `app/templates/` — Jinja2-шаблоны

| Файл | Ответственность |
|---|---|
| `index.html` | Основная страница: форма, spinner, блок результата, блок refusal, блок ошибки |

### `app/static/` — Статика

| Директория | Содержимое |
|---|---|
| `css/` | Стили, включая подсветку нарушений (severity: high / medium / low) |
| `js/` | Fetch-запрос к `/validate`, управление UI-состояниями |

### `data/corpus/` — Корпус знаний

≥ 30 Markdown-файлов, структурированных по темам:

```
data/corpus/
├── gost_34_602.md              # ГОСТ 34.602-89: ТЗ на АС
├── gost_19_201.md              # ГОСТ 19.201-78: требования к ПО
├── microservices_patterns.md   # Паттерны микросервисов
├── microservices_caching.md    # Кэширование
├── microservices_observability.md  # Мониторинг и трейсинг
├── resilience_patterns.md      # Circuit breaker, retry
└── ...
```

## Поток обработки запроса

```
1. Пользователь → POST /validate {"query": "<текст>"}
        │
2. routes.py: Pydantic-валидация входа, обрезка до max_chars
        │
3. text.py: нормализация (lowercase → стемминг → токены)
        │
4. search.py: BM25.score(tokens) для каждого чанка
             агрегация: score документа = max(score чанков)
             top-5 документов
        │
5. Если max_score < 1.0 → {"refused": true, ...} → ответ
        │
6. llm.py: формирование промпта (system + context + query)
           POST к LLM API (timeout=30s)
        │
7. llm.py: парсинг JSON из ответа LLM
           валидация схемы (violations[], sources[], refused, summary)
        │
8. routes.py → JSONResponse → Web UI
```

## Схема данных API

### Запрос (`POST /validate`)

```json
{
  "query": "string (1–4000 символов)"
}
```

### Ответ (успех)

```json
{
  "refused": false,
  "summary": "Найдено 2 нарушения",
  "violations": [
    {
      "text": "Описание нарушения",
      "source": "ГОСТ 34.602-89, раздел 4.5",
      "severity": "high"
    }
  ],
  "sources": ["gost_34_602.md"]
}
```

### Ответ (refusal)

```json
{
  "refused": true,
  "summary": "Запрос не относится к предметной области системы",
  "violations": [],
  "sources": []
}
```

## Обработка ошибок

| Ситуация | Поведение | HTTP-код |
|---|---|---|
| Пустой запрос | Pydantic ValidationError | 422 |
| Запрос > max_chars | Обрезка + предупреждение в ответе | 200 |
| BM25 score < порога | `refused: true` в JSON | 200 |
| Таймаут LLM (> 30 с) | Fallback: `{"refused": false, "summary": "LLM timeout", ...}` | 504 |
| Невалидный JSON от LLM | Логирование + HTTP 500 | 500 |
| Любая необработанная ошибка | HTTP 500 + сообщение | 500 |

## Конфигурация (`config.py` / `.env`)

| Параметр | Значение по умолчанию | Описание |
|---|---|---|
| `CORPUS_DIR` | `data/corpus` | Директория корпуса |
| `BM25_K1` | `1.2` | Параметр насыщения BM25 |
| `BM25_B` | `0.75` | Параметр нормализации длины BM25 |
| `TOP_K` | `5` | Число возвращаемых документов |
| `RELEVANCE_THRESHOLD` | `1.0` | Минимальный score для не-refusal |
| `MAX_QUERY_CHARS` | `4000` | Максимальная длина запроса (символы) |
| `LLM_API_URL` | `http://localhost:11434/v1` | URL LLM API |
| `LLM_MODEL` | `llama3` | Модель LLM |
| `LLM_TIMEOUT` | `30` | Таймаут запроса к LLM (секунды) |
