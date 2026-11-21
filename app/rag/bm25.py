"""Реализация Okapi BM25 с нуля."""
from __future__ import annotations

import math
from collections import Counter

from app.rag.text import tokenize


class BM25Index:
    """Инвертированный индекс с оценкой по формуле Okapi BM25.

    Parameters
    ----------
    k1 : float
        Параметр насыщения термина (term-frequency saturation). По умолчанию 1.2.
    b : float
        Параметр нормализации длины документа. По умолчанию 0.75.
    """

    def __init__(self, k1: float = 1.2, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

        # Данные, заполняемые методом build()
        self._documents: list[str] = []
        self._doc_tokens: list[list[str]] = []
        self._doc_lengths: list[int] = []
        self._avgdl: float = 0.0
        # inverted index: term -> {doc_idx: tf}
        self._inverted: dict[str, dict[int, int]] = {}
        # document frequency per term
        self._df: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Построение индекса
    # ------------------------------------------------------------------

    def build(self, documents: list[str]) -> None:
        """Строит инвертированный индекс по списку текстовых документов."""
        self._documents = documents
        self._doc_tokens = [tokenize(doc) for doc in documents]
        self._doc_lengths = [len(tokens) for tokens in self._doc_tokens]
        total_tokens = sum(self._doc_lengths)
        n = len(documents)
        self._avgdl = total_tokens / n if n > 0 else 0.0

        # Строим инвертированный индекс
        self._inverted = {}
        self._df = {}
        for doc_idx, tokens in enumerate(self._doc_tokens):
            term_counts = Counter(tokens)
            for term, tf in term_counts.items():
                if term not in self._inverted:
                    self._inverted[term] = {}
                self._inverted[term][doc_idx] = tf
                self._df[term] = self._df.get(term, 0) + 1

    # ------------------------------------------------------------------
    # Оценка
    # ------------------------------------------------------------------

    def _idf(self, term: str) -> float:
        """IDF по формуле: ln(1 + (N - df + 0.5) / (df + 0.5))."""
        n = len(self._documents)
        df = self._df.get(term, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        """Считает BM25-оценку для одного документа."""
        dl = self._doc_lengths[doc_idx]
        avgdl = self._avgdl
        k1 = self.k1
        b = self.b

        result = 0.0
        for term in query_tokens:
            idf = self._idf(term)
            tf = self._inverted.get(term, {}).get(doc_idx, 0)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * dl / avgdl) if avgdl > 0 else 1.0
            result += idf * (numerator / denominator)
        return result

    # ------------------------------------------------------------------
    # Поиск
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        """Возвращает список (doc_idx, score), отсортированный по убыванию score."""
        query_tokens = tokenize(query)
        if not query_tokens or not self._documents:
            return []

        # Находим документы, содержащие хотя бы один терм запроса
        candidate_docs: set[int] = set()
        for term in query_tokens:
            candidate_docs.update(self._inverted.get(term, {}).keys())

        scored = [
            (doc_idx, self.score(query_tokens, doc_idx))
            for doc_idx in candidate_docs
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
