# -*- coding: utf-8 -*-
from app.rag.bm25 import BM25Index
from app.rag.text import tokenize, normalize

def test_tokenize_russian():
    tokens = tokenize("Привет, Мир! Проверка алгоритма BM25...")
    assert "привет" in tokens
    assert "мир" in tokens
    assert "проверк" in tokens  # stemmed

def test_bm25_basic_ranking():
    corpus = [
        "Архитектура микросервисов требует наличия шлюза API Gateway и кэширования",
        "Рецепты домашней кухни и приготовление супа борщ",
        "База данных PostgreSQL обеспечивает надежное хранение транзакций"
    ]
    index = BM25Index()
    index.build(corpus)

    results = index.search("микросервисы API Gateway", top_k=2)
    assert len(results) > 0
    top_doc_idx, top_score = results[0]
    assert top_doc_idx == 0
    assert top_score > 0.0

def test_bm25_empty_query():
    corpus = ["Тестовый документ номер один"]
    index = BM25Index()
    index.build(corpus)
    res = index.search("", top_k=5)
    assert res == []
