"""
Phase 3-4: RAG ingestion.

Loads every .md file under knowledge_base/{databases,design,selection,operations}/,
chunks it, embeds each chunk with Ollama (qwen3-embedding:0.6b), and builds a
FAISS index saved to vectorstore/.

Run from the project root:
    python scripts/ingest.py
"""

from pathlib import Path

import frontmatter
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base"
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"

EMBEDDING_MODEL = "qwen3-embedding:0.6b"

# subfolder name -> "category" metadata value, used when a doc has no frontmatter
CATEGORY_FOLDERS = {"databases", "design", "selection", "operations"}

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def load_documents() -> list[Document]:
    """Walk knowledge_base/, turn each .md file into a Document with metadata."""
    docs: list[Document] = []

    if not KB_DIR.exists():
        raise FileNotFoundError(
            f"Expected knowledge base at {KB_DIR}, but it doesn't exist. "
            "Check that knowledge_base/ sits at the project root."
        )

    md_files = sorted(KB_DIR.rglob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No .md files found under {KB_DIR}")

    for path in md_files:
        relative = path.relative_to(KB_DIR)
        folder = relative.parts[0] if len(relative.parts) > 1 else "uncategorized"

        post = frontmatter.load(path)
        text = post.content.strip()
        if not text:
            print(f"  [skip] {relative} — empty after stripping frontmatter")
            continue

        # Prefer explicit frontmatter metadata; fall back to path-derived values.
        metadata = {
            "source": str(relative).replace("\\", "/"),
            "category": post.get("category", folder),
            "technology": post.get("technology", path.stem if folder == "databases" else None),
            "topic": post.get("topic", path.stem),
        }
        # Drop None values — FAISS/metadata filtering doesn't like them.
        metadata = {k: v for k, v in metadata.items() if v is not None}

        docs.append(Document(page_content=text, metadata=metadata))

    return docs


def chunk_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"  {len(docs)} documents -> {len(chunks)} chunks")
    return chunks


def build_index(chunks: list[Document]) -> None:
    print(f"  Embedding {len(chunks)} chunks with '{EMBEDDING_MODEL}' via Ollama...")
    print("  (this calls your local Ollama server — make sure `ollama serve` is running)")

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(chunks, embeddings)

    VECTORSTORE_DIR.mkdir(exist_ok=True)
    vectorstore.save_local(str(VECTORSTORE_DIR))
    print(f"  Saved FAISS index to {VECTORSTORE_DIR}")


def main() -> None:
    print("1. Loading markdown documents...")
    docs = load_documents()
    print(f"  Loaded {len(docs)} documents")

    print("2. Chunking...")
    chunks = chunk_documents(docs)

    print("3. Building FAISS index...")
    build_index(chunks)

    print("\nDone. Run scripts/test_retrieval.py to sanity-check retrieval.")


if __name__ == "__main__":
    main()