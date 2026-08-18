"""
Phase 5 (extended after the Phase F re-ingest): test retrieval against the
FAISS index built by ingest.py.

Run from the project root:
    python scripts/test_retrieval.py

ORIGINAL_QUERIES were written for the first 27-doc corpus and are kept as a
regression check -- they should still return sensible results after the
118-chunk re-ingest. NEW_CORPUS_QUERIES specifically target content that
only exists in the expanded knowledge base (the *_deep.md docs and the six
case studies under case_studies/), added when that content was ingested for
the first time -- their purpose is to confirm the new material actually
surfaces, not just that it was embedded.

DUPLICATE_TOPIC_CHECKS probes topics where both a shallow original doc and a
newer *_deep.md (or otherwise more detailed) doc now coexist in the index
(e.g. indexing.md vs indexing_deep.md). This doesn't fail anything -- it's
diagnostic output so a human can see which version similarity search is
actually preferring, to inform the Phase C cleanup decision (merge/replace
the shallow doc, or leave both).
"""

from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"
EMBEDDING_MODEL = "qwen3-embedding:0.6b"

ORIGINAL_QUERIES = [
    "How do I prevent double booking under high concurrency?",
    "When should I use MySQL vs MongoDB?",
    "How do I design indexes for a query-heavy workload?",
    "What is the difference between normalization and denormalization?",
]

# Targets deep docs and case studies that only entered the index in the
# Phase F re-ingest -- confirms the new content is actually retrievable,
# not just present in vectorstore/.
NEW_CORPUS_QUERIES = [
    "How should I choose a shard key and avoid hotspots?",
    "How do idempotency keys prevent duplicate processing on retry?",
    "Cursor-based pagination versus offset pagination at scale",
    "Full worked example of a ticket booking database design",
    "How does an e-commerce platform handle inventory and order consistency?",
    "What database architecture anti-patterns should I avoid?",
    "How do read replicas and replication lag affect consistency?",
]

# (query, doc likely to represent the "shallow" version, doc likely to
# represent the "deep" version) -- used only to print which one ranks higher.
DUPLICATE_TOPIC_CHECKS = [
    ("How do I design and choose indexes?", "design/indexing.md", "design/indexing_deep.md"),
    ("How should caching and cache invalidation work?", "design/caching.md", None),
    ("When should I shard or partition a database?",
     "design/partitioning_replication_sharding.md", "design/sharding_deep.md"),
    ("How do I design a search architecture?", "design/search_architecture.md", None),
]


def _print_results(query: str, results) -> None:
    print("=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)
    for doc, score in results:
        print(f"\n  score={score:.4f}  source={doc.metadata.get('source')}")
        print(f"  category={doc.metadata.get('category')}  "
              f"technology={doc.metadata.get('technology', '-')}")
        print(f"  {doc.page_content[:150].strip()}...")
    print()


def main() -> None:
    if not VECTORSTORE_DIR.exists():
        raise FileNotFoundError(
            f"No vectorstore found at {VECTORSTORE_DIR}. Run scripts/ingest.py first."
        )

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR), embeddings, allow_dangerous_deserialization=True
    )

    print("\n########## REGRESSION: original 27-doc-era queries ##########\n")
    for query in ORIGINAL_QUERIES:
        _print_results(query, vectorstore.similarity_search_with_score(query, k=3))

    print("\n########## NEW CONTENT: deep docs + case studies ##########\n")
    for query in NEW_CORPUS_QUERIES:
        _print_results(query, vectorstore.similarity_search_with_score(query, k=3))

    print("\n########## DUPLICATE-TOPIC DIAGNOSTIC (shallow vs deep) ##########\n")
    for query, shallow_source, deep_source in DUPLICATE_TOPIC_CHECKS:
        print("-" * 70)
        print(f"QUERY: {query}")
        print(f"  watching for: shallow={shallow_source}  deep={deep_source or '(none exists yet)'}")
        results = vectorstore.similarity_search_with_score(query, k=5)
        for rank, (doc, score) in enumerate(results, start=1):
            source = doc.metadata.get("source")
            tag = ""
            if source == shallow_source:
                tag = "  <-- SHALLOW"
            elif deep_source and source == deep_source:
                tag = "  <-- DEEP"
            print(f"  #{rank}  score={score:.4f}  {source}{tag}")
        print()


if __name__ == "__main__":
    main()