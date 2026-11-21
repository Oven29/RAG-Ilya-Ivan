# -*- coding: utf-8 -*-
from pathlib import Path
from app.rag.corpus import load_corpus, chunk_document

ROOT = Path(__file__).resolve().parent.parent

def test_load_all_30_documents():
    data_dir = ROOT / "data"
    docs = load_corpus(data_dir)
    assert len(docs) == 30, f"Expected 30 documents, got {len(docs)}"
    for doc in docs:
        assert doc.doc_id.startswith("D")
        assert len(doc.fragments) > 0
        assert len(doc.title) > 0

def test_chunk_document():
    sample_md = """# Заголовок документа

## Раздел 1
Текст первого раздела.

## Раздел 2
Текст второго раздела.
"""
    frags = chunk_document("D99", "Тест", sample_md)
    assert len(frags) >= 2
    sections = [f.section for f in frags]
    assert "Раздел 1" in sections
    assert "Раздел 2" in sections
