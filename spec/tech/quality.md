# Стандарты качества

## Тестирование

### Покрытие кода

| Метрика | Целевое значение |
|---|---|
| Общее покрытие (line coverage) | **≥ 70%** |
| Покрытие `app/rag/` | ≥ 80% (критическая бизнес-логика) |
| Покрытие `app/api/` | ≥ 70% |

Инструмент: `pytest` + `pytest-cov`

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=70
```

### Структура тестов

```
tests/
├── unit/
│   ├── test_text.py          # нормализация, стемминг, стоп-слова
│   ├── test_corpus.py        # чанкинг markdown, загрузка корпуса
│   ├── test_bm25.py          # IDF, scoring, edge cases (пустой запрос, нет совпадений)
│   └── test_search.py        # агрегация, порог refusal
├── integration/
│   ├── test_routes.py        # POST /validate — успех, refusal, ошибки
│   └── test_llm.py           # мок LLM API
└── conftest.py               # фикстуры: мини-корпус, тестовый индекс
```

### Типы тестов

| Тип | Описание |
|---|---|
| **Unit** | Изолированные тесты каждого модуля с моками зависимостей |
| **Integration** | Тесты FastAPI endpoints через `httpx.AsyncClient` или `TestClient` |
| **Benchmark** | Автономный скрипт (`benchmark/run.py`), не входит в pytest |

---

## Линтинг и форматирование

### Ruff

Инструмент: [`ruff`](https://docs.astral.sh/ruff/)

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "C4"]
ignore = []
```

Запуск:
```bash
ruff check app/ tests/ benchmark/
ruff format --check app/ tests/ benchmark/
```

**Критерий приёмки:** 0 ошибок, 0 предупреждений.

---

## Метрики бенчмарка

Бенчмарк запускается отдельно от unit-тестов командой:

```bash
python benchmark/run.py
```

### Recall@5

Доля запросов, для которых хотя бы один из 5 возвращённых документов является релевантным по ground truth.

$$\text{Recall@5} = \frac{|\{q : \exists d \in \text{top5}(q), d \in R_q\}|}{|Q|}$$

**Порог:** ≥ 0.70

---

### MRR (Mean Reciprocal Rank)

$$\text{MRR} = \frac{1}{|Q|} \sum_{q} \frac{1}{\text{rank}(q)}$$

где `rank(q)` — позиция первого релевантного документа в результатах.

**Порог:** ≥ 0.60 *(ориентир)*

---

### LLM Accuracy

Доля запросов, где нарушения, выявленные LLM, совпадают с эталонной разметкой (ручная оценка аннотатора).

**Порог:** ≥ 0.70 *(ориентир)*

---

### CRR (Correct Refusal Rate)

Доля trap-вопросов (вне предметной области), на которые система правильно ответила отказом.

$$\text{CRR} = \frac{\text{корректно отклонённые trap-вопросы}}{\text{всего trap-вопросов}}$$

**Порог:** = 1.0 (жёсткий — все trap-вопросы должны отклоняться)

---

### Формат отчёта бенчмарка

```
=== RAG Benchmark Report ===
Questions evaluated : 25
Trap questions      : 5

Recall@5            : 0.80  [PASS ✓]
MRR                 : 0.65  [PASS ✓]
LLM Accuracy        : 0.72  [PASS ✓]
CRR                 : 1.00  [PASS ✓]

Failed queries:
  q07 — ожидался gost_34_602.md, возвращён microservices_patterns.md
  ...
```

---

## CI-пайплайн

### Триггеры

| Событие | Действие |
|---|---|
| `git push` (любая ветка) | Линтер + тесты |
| `git push main` | Линтер + тесты + docker build |
| Pull Request | Линтер + тесты + отчёт coverage в PR |

### Шаги пайплайна

```yaml
# .github/workflows/ci.yml (пример)
steps:
  - name: Install dependencies
    run: pip install -r requirements.txt

  - name: Lint
    run: |
      ruff check app/ tests/ benchmark/
      ruff format --check app/ tests/ benchmark/

  - name: Test
    run: pytest --cov=app --cov-fail-under=70

  - name: Build Docker image
    run: docker build -t rag-validator .
    if: github.ref == 'refs/heads/main'
```

**Критерий прохождения CI:** все шаги зелёные. Merge в `main` запрещён при красном CI.

---

## Версионирование и зависимости

```toml
# pyproject.toml
[project]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "httpx>=0.27",
    "snowballstemmer>=2.2",
    "jinja2>=3.1",
    "pydantic>=2.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.4",
]
```
