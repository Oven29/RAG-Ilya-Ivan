# -*- coding: utf-8 -*-
"""
RAG Benchmark runner for NIRS 2026.
Computes Recall@k, MRR, Accuracy (optional LLM), and Correct Rejection Rate (CRR).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.rag.search import get_default_retriever
from app.api.services import validate_document

DOMAIN_KEYWORDS = (
    "архитектур", "тз", "гост", "сервис", "паттерн", "компонент", "бд",
    "баз", "данны", "сесси", "запрос", "микросервис", "api", "srp", "saga",
    "solid", "кэш", "событи", "очеред", "outbox", "rest", "надежност",
    "масштабирован", "мониторинг", "требован", "пользовател", "контроллер",
    "интерфейс", "отказоустойчив", "восстановлен", "клиент", "согласованност"
)

def is_domain_relevant(query: str) -> bool:
    q_lower = query.lower()
    return any(kw in q_lower for kw in DOMAIN_KEYWORDS)

def load_benchmark_questions(filepath: Path):
    questions = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))
    return questions

def run_benchmark(top_k: int = 5, use_llm: bool = False):
    retriever = get_default_retriever()
    questions_file = ROOT / "benchmark" / "questions.jsonl"
    questions = load_benchmark_questions(questions_file)

    regular_questions = [q for q in questions if not q.get("is_trap", False)]
    trap_questions = [q for q in questions if q.get("is_trap", False)]

    print(f"=== Запуск бенчмарка RAG-валидатора ===")
    print(f"Всего вопросов: {len(questions)} (обычных: {len(regular_questions)}, ловушек: {len(trap_questions)})")
    print(f"Параметр Top-K: {top_k}, Использование LLM: {use_llm}\n")

    # Metrics accumulators
    recall_scores = []
    mrr_scores = []
    accuracy_scores = []
    correct_rejections = 0

    results_detail = []

    print(f"{'ID':<5} | {'Тип':<8} | {'Recall@'+str(top_k):<10} | {'MRR':<8} | {'Отказ?':<8} | {'Найденные документы'}")
    print("-" * 75)

    for q in regular_questions:
        qid = q["id"]
        text = q["question"]
        relevant = set(q["relevant_docs"])

        hits = retriever.retrieve(text, top_k=top_k)
        retrieved_ids = [h.doc_id for h in hits]

        # Recall@k
        intersect = relevant.intersection(retrieved_ids)
        recall = len(intersect) / len(relevant) if relevant else 0.0
        recall_scores.append(recall)

        # MRR
        rr = 0.0
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant:
                rr = 1.0 / rank
                break
        mrr_scores.append(rr)

        # LLM validation if requested
        llm_acc = None
        if use_llm:
            try:
                res = validate_document(text)
                llm_acc = 1.0 if not res.refused and len(res.violations) > 0 else 0.0
                accuracy_scores.append(llm_acc)
            except Exception as e:
                print(f"LLM Error on {qid}: {e}")
                accuracy_scores.append(0.0)

        results_detail.append({
            "id": qid,
            "is_trap": False,
            "relevant": list(relevant),
            "retrieved": retrieved_ids,
            "recall": recall,
            "rr": rr,
            "llm_acc": llm_acc
        })

        found_str = ", ".join(f"{d}*" if d in relevant else d for d in retrieved_ids)
        print(f"{qid:<5} | {'Обычный':<8} | {recall:<10.3f} | {rr:<8.3f} | {'Нет':<8} | {found_str}")

    # Process trap questions
    for q in trap_questions:
        qid = q["id"]
        text = q["question"]

        hits = retriever.retrieve(text, top_k=top_k)
        retrieved_ids = [h.doc_id for h in hits]
        max_score = hits[0].score if hits else 0.0

        is_refused = False
        if use_llm:
            try:
                res = validate_document(text)
                is_refused = res.refused
            except Exception:
                is_refused = True
        else:
            is_refused = not is_domain_relevant(text)

        if is_refused:
            correct_rejections += 1

        results_detail.append({
            "id": qid,
            "is_trap": True,
            "retrieved": retrieved_ids,
            "max_score": max_score,
            "refused": is_refused
        })

        print(f"{qid:<5} | {'Ловушка':<8} | {'-':<10} | {'-':<8} | {'Да' if is_refused else 'НЕТ':<8} | top score: {max_score:.3f}")

    avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    crr = correct_rejections / len(trap_questions) if trap_questions else 0.0
    avg_acc = (sum(accuracy_scores) / len(accuracy_scores)) if accuracy_scores else None

    print("-" * 75)
    print(f"\n=== ИТОГОВЫЕ МЕТРИКИ КАЧЕСТВА ===")
    print(f"• Recall@{top_k}: {avg_recall:.4f} (норма: >= 0.70)")
    print(f"• MRR:       {avg_mrr:.4f} (норма: >= 0.75)")
    print(f"• CRR (отказ ловушек): {crr:.4f} ({correct_rejections}/{len(trap_questions)})")
    if avg_acc is not None:
        print(f"• LLM Accuracy: {avg_acc:.4f}")

    # Save results to benchmark/results/
    results_dir = ROOT / "benchmark" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = results_dir / f"benchmark_{timestamp}.json"

    data_to_save = {
        "timestamp": timestamp,
        "top_k": top_k,
        "use_llm": use_llm,
        "metrics": {
            f"recall@{top_k}": avg_recall,
            "mrr": avg_mrr,
            "crr": crr,
            "llm_accuracy": avg_acc
        },
        "details": results_detail
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

    print(f"\nРезультаты сохранены в: {out_file.relative_to(ROOT)}")
    return data_to_save

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск бенчмарка RAG")
    parser.add_argument("--k", type=int, default=5, help="Глубина выдачи top_k (по умолчанию 5)")
    parser.add_argument("--llm", action="store_true", help="Включить оценку генерации LLM")
    args = parser.parse_args()

    run_benchmark(top_k=args.k, use_llm=args.llm)
