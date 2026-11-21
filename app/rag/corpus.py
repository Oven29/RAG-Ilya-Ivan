"""Загрузка и чанкинг корпуса документов."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Fragment:
    doc_id: str
    title: str
    section: str
    text: str
    search_text: str


@dataclass
class Document:
    doc_id: str
    title: str
    category: str
    file: str
    fragments: list[Fragment] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Чанкинг
# ---------------------------------------------------------------------------

def chunk_document(doc_id: str, title: str, text: str) -> list[Fragment]:
    """Разбивает markdown-документ на фрагменты по ## и ### заголовкам.

    Первый блок до первого ## называется «Введение».
    """
    fragments: list[Fragment] = []

    # Разбиваем по заголовкам уровней 2 и 3
    # Паттерн: строка, начинающаяся с ## или ###
    pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    def _make_fragment(section: str, content: str) -> Fragment:
        content = content.strip()
        search_text = f"{title}. {section}.\n{content}"
        return Fragment(
            doc_id=doc_id,
            title=title,
            section=section,
            text=content,
            search_text=search_text,
        )

    if not matches:
        # Нет заголовков — весь текст как одно «Введение»
        fragments.append(_make_fragment("Введение", text.strip()))
        return fragments

    # Текст до первого заголовка
    intro_text = text[: matches[0].start()].strip()
    if intro_text:
        fragments.append(_make_fragment("Введение", intro_text))

    # Итерируемся по заголовкам
    for i, match in enumerate(matches):
        section_name = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            fragments.append(_make_fragment(section_name, content))

    return fragments


# ---------------------------------------------------------------------------
# Загрузка корпуса
# ---------------------------------------------------------------------------

def load_corpus(data_dir: Path) -> list[Document]:
    """Читает documents.jsonl, затем каждый md-файл и строит корпус."""
    index_file = data_dir / "documents.jsonl"
    if not index_file.exists():
        raise FileNotFoundError(f"Не найден файл индекса: {index_file}")

    documents: list[Document] = []

    with index_file.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            meta = json.loads(line)
            doc_id = meta.get("id") or meta.get("doc_id", "")
            title = meta.get("title", doc_id)
            category = meta.get("category", "")
            file_name = meta.get("file", "")

            md_path = data_dir / file_name if file_name else None
            if md_path and md_path.exists():
                md_text = md_path.read_text(encoding="utf-8")
            else:
                md_text = meta.get("text", "")

            fragments = chunk_document(doc_id, title, md_text)
            doc = Document(
                doc_id=doc_id,
                title=title,
                category=category,
                file=file_name,
                fragments=fragments,
            )
            documents.append(doc)

    return documents
