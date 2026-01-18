# rag.py - RAG (Retrieval-Augmented Generation) for PDF-based Q&A
from __future__ import annotations

import os
from typing import List, Tuple

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# RecursiveCharacterTextSplitter:
# Splits text into chunks using a hierarchy of separators to preserve meaning:
#   1. First tries "\n\n" (paragraphs) - keeps complete thoughts together
#   2. Then "\n" (lines) - preserves list items, headings
#   3. Then " " (spaces) - breaks at word boundaries
#   4. Finally "" (chars) - last resort to stay under chunk_size
# The "recursive" part: if a chunk is too big (i.e bigger then chunk_size defined by us), it tries the next separator level.
# chunk_overlap ensures context isn't lost at boundaries (e.g., 200 chars shared between chunks)

# Configuration - can be overridden via environment variables
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDF_DIR = os.getenv("PDF_DIR", os.path.join(PROJECT_ROOT, "data", "pdfs"))
CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(PROJECT_ROOT, "data", "chroma"))

# all-MiniLM-L6-v2: lightweight sentence transformer, outputs 384-dim vectors
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.0"))  # 0-1, filter threshold
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))            # max chars per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))      # shared chars between chunks
TOP_K = int(os.getenv("TOP_K", "4"))                        # number of results to retrieve


def make_embeddings() -> HuggingFaceEmbeddings:
    """Creates embedding model that converts text to semantic vectors."""
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def build_vectorstore(
    pdf_path: str | None = None,
    pdf_dir: str = PDF_DIR,
    chroma_dir: str = CHROMA_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> int:
    """
    Indexes PDFs into the vector database. This is the "indexing phase" of RAG:
    PDF -> text extraction -> chunking -> embedding -> store in Chroma
    """
    embeddings = make_embeddings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Collect PDF paths (single file or all from directory)
    paths: List[str] = []
    if pdf_path:
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
        paths = [pdf_path]
    else:
        if not os.path.isdir(pdf_dir):
            raise FileNotFoundError(f"PDF-Ordner nicht gefunden: {pdf_dir}")
        paths = [
            os.path.join(pdf_dir, f)
            for f in os.listdir(pdf_dir)
            if f.lower().endswith(".pdf")
        ]
        if not paths:
            raise FileNotFoundError(f"Keine PDFs in {pdf_dir} gefunden.")

    # Process each PDF: load pages, add metadata, split into chunks
    all_chunks: List[Document] = []
    for p in paths:
        loader = PyPDFLoader(p)
        docs = loader.load()  # one Document per page

        for d in docs:
            d.metadata["source_file"] = os.path.basename(p)

        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)

    print(f"Anzahl PDFs: {len(paths)} | Anzahl Chunks: {len(all_chunks)}")

    # Create vector DB: embeds all chunks and builds search index
    vectordb = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=chroma_dir,
    )
    vectordb.persist()
    print(f"Vectorstore erstellt und gespeichert in: {chroma_dir}")
    return len(all_chunks)


def load_vectordb() -> Chroma:
    """Loads existing vector database for querying."""
    embeddings = make_embeddings()
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )


def _distance_to_confidence(score: float) -> float:
    """
    Converts Chroma's cosine distance to confidence (0-1).
    Chroma returns distance where 0=identical, 1=unrelated.
    We flip it: confidence = 1 - distance
    """
    if score is None:
        return 0.0
    conf = 1.0 - float(score)
    return max(0.0, min(1.0, conf))  # clamp to [0,1]


def query_rag_with_scores(query: str, k: int = TOP_K) -> List[tuple[Document, float]]:
    """
    Similarity search: embeds query, finds k nearest document chunks.
    Returns list of (Document, distance_score) tuples.
    """
    vectordb = load_vectordb()
    return vectordb.similarity_search_with_score(query, k=k)


def retrieve_context(
    query: str,
    k: int = TOP_K,
    max_chars_per_doc: int = 1200,
    min_confidence: float = MIN_CONFIDENCE,
) -> Tuple[str, List[str]]:
    """
    Main retrieval function - finds relevant chunks for a query.
    Returns (formatted_context, list_of_sources) for the LLM prompt.
    """
    results = query_rag_with_scores(query, k=k)

    if not results:
        return "", []

    # Sort by distance (lower = better match)
    results_sorted = sorted(results, key=lambda x: x[1])

    # Check if best result meets confidence threshold
    best_doc, best_score = results_sorted[0]
    best_conf = _distance_to_confidence(best_score)
    if best_conf < min_confidence:
        return "", []

    parts: List[str] = []
    sources: List[str] = []
    seen = set()

    for i, (d, score) in enumerate(results_sorted, start=1):
        conf = _distance_to_confidence(score)
        if conf < min_confidence:
            continue

        # Build source citation
        src = d.metadata.get("source_file", "unbekannt")
        page = d.metadata.get("page", None)
        src_line = f"{src}" + (f" (Seite {page})" if page is not None else "")

        if src_line not in seen:
            sources.append(src_line)
            seen.add(src_line)

        # Truncate long texts
        text = (d.page_content or "").strip()
        if max_chars_per_doc and len(text) > max_chars_per_doc:
            text = text[:max_chars_per_doc] + " ..."

        parts.append(f"[{i}] {src_line} | conf={conf:.2f}\n{text}")

    if not parts:
        return "", []

    return "\n\n".join(parts), sources


def index_all_pdfs() -> str:
    """Triggers manual re-indexing of all PDFs."""
    n_chunks = build_vectorstore(pdf_path=None)
    return f"Index fertig. Chunks: {n_chunks}. DB: {CHROMA_DIR}"


def auto_index_if_needed() -> str:
    """Auto-indexes PDFs on startup if vector DB doesn't exist yet."""
    # Skip if DB already exists
    if os.path.exists(CHROMA_DIR) and os.path.isdir(CHROMA_DIR):
        if any(os.scandir(CHROMA_DIR)):
            return f"Vector database already exists at {CHROMA_DIR}. Skipping auto-index."

    if not os.path.exists(PDF_DIR) or not os.path.isdir(PDF_DIR):
        return f"PDF directory {PDF_DIR} not found. Skipping auto-index."

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    if not pdf_files:
        return f"No PDFs found in {PDF_DIR}. Skipping auto-index."

    try:
        print(f"Auto-indexing {len(pdf_files)} PDFs from {PDF_DIR}...")
        n_chunks = build_vectorstore(pdf_path=None)
        return f"Auto-indexed {len(pdf_files)} PDFs into {n_chunks} chunks. DB: {CHROMA_DIR}"
    except Exception as e:
        return f"Auto-index failed: {str(e)}"
