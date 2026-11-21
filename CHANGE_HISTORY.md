# Журнал изменений проекта (Change History)

## [2026-11-21] — Контрольная точка №2 (KT2): Полноценный RAG, Бенчмарк и Корпус
### Добавлено:
- Полноценный корпус знаний из 30 документов (`D01.md` – `D30.md`) по ГОСТ 34.602-2020, паттернам проектирования (SOLID, GoF) и микросервисной архитектуре.
- Самописная реализация алгоритма Okapi BM25 в `app/rag/bm25.py` со Snowball-стеммером для русского языка.
- Модуль chunking Markdown-документов по заголовкам второго и третьего уровня (`app/rag/corpus.py`).
- RAG-пайплайн с вызовом LLM и строгой верификацией источников (`app/api/services.py`).
- Бенчмарк-набор на 15 вопросов: 10 обычных с >=3 релевантными документами и 5 вопросов-ловушек (`benchmark/questions.jsonl`).
- Автоматизированный скрипт расчёта метрик Recall@k, MRR, CRR (`benchmark/run.py`).
- Интеграционные и юнит-тесты (`tests/test_bm25.py`, `tests/test_corpus.py`, `tests/test_api.py`).
- Правила для агентов `AGENTS.md` и спецификации `spec/product/kt2.md`, `spec/tech/rag.md`.

## [2026-11-21] — Контрольная точка №1 (KT1): Спецификация и веб-интерфейс
### Добавлено:
- Базовый веб-интерфейс валидатора (`app/templates/index.html`, `app/static/style.css`, `app/static/app.js`).
- Спецификации продукта и сценариев в `spec/product/product.md`, `spec/product/scenarios.md`.
- Техническая архитектура и требования к качеству в `spec/tech/architecture.md`, `spec/tech/quality.md`.
- Контейнеризация приложения (`Dockerfile`, `docker-compose.yaml`).
