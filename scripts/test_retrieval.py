"""
Phase 5: test retrieval against the FAISS index built by ingest.py.

Run from the project root:
    python scripts/test_retrieval.py
"""

from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"

# Queries chosen to exercise different parts of the knowledge base.
# Edit these once you've run ingest.py with your real 27 docs.
TEST_QUERIES = [
    "How do I prevent double booking under high concurrency?",
    "When should I use MySQL vs MongoDB?",
    "How do I design indexes for a query-heavy workload?",
    "What is the difference between normalization and denormalization?",
]


def main() -> None:
    if not VECTORSTORE_DIR.exists():
        raise FileNotFoundError(
            f"No vectorstore found at {VECTORSTORE_DIR}. Run scripts/ingest.py first."
        )

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True
    )

    for query in TEST_QUERIES:
        print("=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)
        results = vectorstore.similarity_search_with_score(query, k=3)
        for doc, score in results:
            print(f"\n  score={score:.4f}  source={doc.metadata.get('source')}")
            print(f"  category={doc.metadata.get('category')}  "
                  f"technology={doc.metadata.get('technology', '-')}")
            print(f"  {doc.page_content[:150].strip()}...")
        print()


if __name__ == "__main__":
    main()