# evaluation/evaluators/retrieval_eval.py
"""
Metric A: RAG Retrieval Recall@5.

For each benchmark question, runs the SAME retrieval path selection_agent
and review_agent actually use (not a separate simplified retriever), and
checks whether the expected source document(s) appear in the top 5 results.
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "agents"))
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"
QUESTIONS_PATH = Path(__file__).resolve().parent.parent / "retrieval_questions.json"


def _load_vectorstore():
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.load_local(str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True)


def score_question(vectorstore, question: dict) -> dict:
    results = vectorstore.similarity_search(question["question"], k=5)
    retrieved_sources = {doc.metadata.get("source") for doc in results}
    expected = set(question["expected_sources"])

    hits = expected & retrieved_sources
    recall = len(hits) / len(expected) if expected else None

    return {
        "question": question["question"],
        "category": question.get("category", "uncategorized"),
        "expected_sources": list(expected),
        "retrieved_sources": list(retrieved_sources),
        "recall_at_5": round(recall, 3) if recall is not None else None,
    }


def run_retrieval_eval() -> dict:
    questions = json.loads(QUESTIONS_PATH.read_text())
    vectorstore = _load_vectorstore()
    results = [score_question(vectorstore, q) for q in questions]

    scored = [r for r in results if r["recall_at_5"] is not None]
    avg_recall = sum(r["recall_at_5"] for r in scored) / len(scored) if scored else 0

    by_category: dict[str, list[float]] = {}
    for r in scored:
        by_category.setdefault(r["category"], []).append(r["recall_at_5"])
    per_category_avg = {
        cat: round(sum(vals) / len(vals), 3) for cat, vals in by_category.items()
    }

    return {
        "average_recall_at_5": round(avg_recall, 3),
        "per_category_recall_at_5": per_category_avg,
        "per_question": results,
    }


if __name__ == "__main__":
    result = run_retrieval_eval()
    print(json.dumps(result, indent=2))