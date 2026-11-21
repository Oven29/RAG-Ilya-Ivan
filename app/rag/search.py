"""Поисковый движок на основе BM25 + корпуса."""
from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

from app.rag.bm25 import BM25Index
from app.rag.corpus import Fragment, load_corpus


@dataclass
class SearchResult:
    doc_id: str
    title: str
    section: str
    text: str
    score: float
    category: str


class RAGRetriever:
    """Retriever, объединяющий корпус и BM25-индекс."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._fragments: list[Fragment] = []
        self._index = BM25Index()
        self._doc_meta: dict[str, dict] = {}  # doc_id -> {title, category}
        self._load()

    def _load(self) -> None:
        """Загружает корпус и строит BM25-индекс по всем фрагментам."""
        documents = load_corpus(self._data_dir)

        for doc in documents:
            self._doc_meta[doc.doc_id] = {
                "title": doc.title,
                "category": doc.category,
            }
            self._fragments.extend(doc.fragments)

        texts = [frag.search_text for frag in self._fragments]
        self._index.build(texts)

    def retrieve(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Выполняет поиск. Для каждого документа берёт лучший фрагмент,
        сортирует по score и возвращает top_k результатов."""
        # Ищем top_k * 5 фрагментов, чтобы взять лучший из каждого doc
        raw = self._index.search(query, top_k=top_k * 5)

        # Агрегация: лучший фрагмент на документ
        best: dict[str, tuple[Fragment, float]] = {}
        for frag_idx, score in raw:
            frag = self._fragments[frag_idx]
            if frag.doc_id not in best or score > best[frag.doc_id][1]:
                best[frag.doc_id] = (frag, score)

        # Сортируем по убыванию score
        sorted_docs = sorted(best.values(), key=lambda x: x[1], reverse=True)

        results: list[SearchResult] = []
        for frag, score in sorted_docs[:top_k]:
            meta = self._doc_meta.get(frag.doc_id, {})
            results.append(
                SearchResult(
                    doc_id=frag.doc_id,
                    title=frag.title,
                    section=frag.section,
                    text=frag.text,
                    score=score,
                    category=meta.get("category", ""),
                )
            )
        return results


@functools.lru_cache(maxsize=1)
def get_default_retriever() -> RAGRetriever:
    """Синглтон-retriever. Данные ищутся в data относительно корня проекта."""
    root = Path(__file__).resolve().parent.parent.parent
    data_dir = root / "data"
    return RAGRetriever(data_dir)
