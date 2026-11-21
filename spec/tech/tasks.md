# Задачи и распределение ответственности

## Обозначения

| Символ | Значение |
|---|---|
| 🔵 | Иван Овчинников |
| 🟢 | Илья |
| ⚪ | Совместно |

---

## Эпик 1: Корпус знаний

| ID | Задача | Файлы / артефакты | Кто | КТ |
|---|---|---|---|---|
| C-01 | Собрать ≥ 30 md-файлов best-practices и ГОСТов | `data/corpus/*.md` | 🔵 | КТ1: ≥ 10, КТ2: ≥ 30 |
| C-02 | Оформить единую структуру заголовков (`##`, `###`) | — | 🔵 | КТ1 |
| C-03 | Добавить метаданные в начало каждого файла (YAML frontmatter) | — | 🔵 | КТ2 |

### Список документов корпуса (целевой)

**ГОСТы:**
- `gost_34_602.md` — ГОСТ 34.602-89: ТЗ на АС
- `gost_19_201.md` — ГОСТ 19.201-78: требования к ПО
- `gost_34_201.md` — ГОСТ 34.201-89: виды, комплектность документации
- `gost_19_106.md` — ГОСТ 19.106-78: требования к программным документам
- `gost_r_51904.md` — ГОСТ Р 51904: ПО встраиваемых систем

**Архитектурные паттерны:**
- `microservices_patterns.md` — Database-per-Service, API Gateway, Saga
- `microservices_caching.md` — Cache-Aside, Read-Through, Write-Through
- `microservices_observability.md` — Logging, Metrics, Tracing
- `resilience_patterns.md` — Circuit Breaker, Retry, Bulkhead, Timeout
- `api_design.md` — REST best practices, versioning, error codes
- `security_patterns.md` — OWASP Top 10, AuthN/AuthZ, secrets management
- `deployment_patterns.md` — Blue-Green, Canary, Rolling Update
- `data_patterns.md` — CQRS, Event Sourcing, Outbox
- `scalability_patterns.md` — Horizontal scaling, Load Balancing, Sharding
- `testing_patterns.md` — TDD, Test Pyramid, Contract Testing
- *(и другие до 30 файлов)*

---

## Эпик 2: RAG-движок

| ID | Задача | Файлы | Кто | КТ |
|---|---|---|---|---|
| R-01 | Нормализация текста: lowercase, пунктуация, стоп-слова | `app/rag/text.py` | 🔵 | КТ1 |
| R-02 | Snowball-стеммер (русский) | `app/rag/text.py` | 🔵 | КТ1 |
| R-03 | Чанкер Markdown (по `##` и `###`) | `app/rag/corpus.py` | 🔵 | КТ1 |
| R-04 | Загрузчик корпуса из директории | `app/rag/corpus.py` | 🔵 | КТ1 |
| R-05 | Построение BM25-индекса (IDF, avgdl) | `app/rag/bm25.py` | 🔵 | КТ1 |
| R-06 | Скоринг BM25 для запроса | `app/rag/bm25.py` | 🔵 | КТ1 |
| R-07 | Агрегация по документам, top-k | `app/rag/search.py` | 🔵 | КТ1 |
| R-08 | Порог релевантности (refusal gate) | `app/rag/search.py` | 🔵 | КТ2 |

---

## Эпик 3: FastAPI-бэкенд

| ID | Задача | Файлы | Кто | КТ |
|---|---|---|---|---|
| B-01 | Инициализация приложения, монтирование роутера | `app/main.py` | 🔵 | КТ1 |
| B-02 | Эндпоинт `GET /` (HTML-интерфейс) | `app/api/routes.py` | 🔵 | КТ1 |
| B-03 | Эндпоинт `POST /validate` (Pydantic-валидация, вызов RAG) | `app/api/routes.py` | 🔵 | КТ1 |
| B-04 | Обрезка длинных запросов (MAX_QUERY_CHARS) | `app/api/routes.py` | 🔵 | КТ2 |
| B-05 | Глобальный exception handler (HTTP 500) | `app/main.py` | 🔵 | КТ2 |
| B-06 | Конфигурация через `.env` / `config.py` | `app/config.py` | 🔵 | КТ1 |

---

## Эпик 4: LLM-клиент

| ID | Задача | Файлы | Кто | КТ |
|---|---|---|---|---|
| L-01 | HTTP-клиент к OpenAI-compatible API | `app/api/llm.py` | 🔵 | КТ1 |
| L-02 | Формирование системного и пользовательского промпта | `app/api/llm.py` | 🔵 | КТ1 |
| L-03 | Парсинг и валидация JSON-ответа LLM | `app/api/llm.py` | 🔵 | КТ1 |
| L-04 | Таймаут (30 с) и fallback-ответ | `app/api/llm.py` | 🔵 | КТ2 |
| L-05 | Retry (1 повтор при 5xx от LLM) | `app/api/llm.py` | 🔵 | КТ2 |

---

## Эпик 5: Бенчмарк

| ID | Задача | Файлы | Кто | КТ |
|---|---|---|---|---|
| BM-01 | Написать ≥ 20 вопросов + 5 trap в JSONL | `benchmark/questions.jsonl` | 🔵 | КТ2 |
| BM-02 | Скрипт вычисления Recall@5 и MRR | `benchmark/run.py` | 🔵 | КТ2 |
| BM-03 | Скрипт вычисления CRR (trap-вопросы) | `benchmark/run.py` | 🔵 | КТ2 |
| BM-04 | Вывод отчёта бенчмарка в stdout | `benchmark/run.py` | 🔵 | КТ2 |

---

## Эпик 6: Frontend

| ID | Задача | Файлы | Кто | КТ |
|---|---|---|---|---|
| F-01 | Базовая HTML-форма (textarea + кнопка) | `app/templates/index.html` | 🟢 | КТ1 |
| F-02 | Fetch-запрос к `POST /validate` | `app/static/js/main.js` | 🟢 | КТ1 |
| F-03 | UI-состояния: idle / loading / result / refusal / error | `app/static/js/main.js` | 🟢 | КТ1 |
| F-04 | Подсветка нарушений по severity (high/medium/low) | `app/static/css/style.css` | 🟢 | КТ2 |
| F-05 | Отображение источников (ссылки на документ + раздел) | `app/templates/index.html` | 🟢 | КТ2 |
| F-06 | Адаптивная верстка (mobile-friendly) | `app/static/css/style.css` | 🟢 | КТ2 |

---

## Эпик 7: Инфраструктура (Docker)

| ID | Задача | Файлы | Кто | КТ |
|---|---|---|---|---|
| D-01 | `Dockerfile` (multi-stage build) | `Dockerfile` | 🟢 | КТ1 |
| D-02 | `docker-compose.yml` (сервис app + опционально LLM) | `docker-compose.yml` | 🟢 | КТ1 |
| D-03 | `.env.example` с комментариями | `.env.example` | 🟢 | КТ1 |
| D-04 | Health-check в docker-compose | `docker-compose.yml` | 🟢 | КТ2 |

---

## Эпик 8: Тестирование

| ID | Задача | Файлы | Кто | КТ |
|---|---|---|---|---|
| T-01 | Юнит-тесты `text.py` | `tests/unit/test_text.py` | 🟢 | КТ2 |
| T-02 | Юнит-тесты `corpus.py` | `tests/unit/test_corpus.py` | 🟢 | КТ2 |
| T-03 | Юнит-тесты `bm25.py` | `tests/unit/test_bm25.py` | 🟢 | КТ2 |
| T-04 | Юнит-тесты `search.py` | `tests/unit/test_search.py` | 🟢 | КТ2 |
| T-05 | Интеграционные тесты `POST /validate` | `tests/integration/test_routes.py` | 🟢 | КТ2 |
| T-06 | Тест refusal (trap-запросы) | `tests/integration/test_routes.py` | 🟢 | КТ2 |
| T-07 | Настройка `conftest.py` и фикстур | `tests/conftest.py` | 🟢 | КТ2 |
| T-08 | CI-конфигурация | `.github/workflows/ci.yml` | 🟢 | КТ2 |

---

## Эпик 9: Документация

| ID | Задача | Файлы | Кто | КТ |
|---|---|---|---|---|
| DOC-01 | Финальный `README.md` (установка, запуск, метрики) | `README.md` | 🟢 | КТ2 |
| DOC-02 | Docstrings в модулях `app/rag/` | `app/rag/*.py` | ⚪ | КТ2 |

---

## Временной план (ориентировочный)

```
Неделя 1-2  │ C-01, C-02, R-01..R-07, B-01..B-03, B-06, L-01..L-03
             │ D-01, D-02, D-03, F-01, F-02, F-03
             │                              ← КТ1
Неделя 3-4  │ C-03, R-08, B-04, B-05, L-04, L-05
             │ BM-01..BM-04
             │ F-04, F-05, F-06
             │ T-01..T-08, D-04
             │ DOC-01, DOC-02             ← КТ2
```
