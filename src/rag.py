# rag.py
from __future__ import annotations

import os
from typing import List, Tuple

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 

'''
RecurisiveCharacterTextSplitter:
    A text splitter that recursively splits text into chunks based on specified separators.
    First it searches for paragraphs, if its smaller then the chunk size defined it keeps the chunk

    if not it searches for new lines, if its smaller then the chunk size defined it keeps the chunk

    if not it searches for spaces, if its smaller then the chunk size defined it keeps the chunk
'''


from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Use absolute paths based on project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDF_DIR = os.getenv("PDF_DIR", os.path.join(PROJECT_ROOT, "data", "pdfs"))
CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(PROJECT_ROOT, "data", "chroma"))
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.0"))

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K = int(os.getenv("TOP_K", "4"))


def make_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def build_vectorstore(
    pdf_path: str | None = None,
    pdf_dir: str = PDF_DIR,
    chroma_dir: str = CHROMA_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> int:
    embeddings = make_embeddings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

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

    all_chunks: List[Document] = []
    for p in paths:
        loader = PyPDFLoader(p)
        docs = loader.load()

        # Quelle als Dateiname speichern (nicht voller Pfad)
        for d in docs:
            d.metadata["source_file"] = os.path.basename(p)

        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)

    print(f"Anzahl PDFs: {len(paths)} | Anzahl Chunks: {len(all_chunks)}")

    vectordb = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=chroma_dir,
    )
    vectordb.persist()
    print(f"Vectorstore erstellt und gespeichert in: {chroma_dir}")
    return len(all_chunks)



def load_vectordb() -> Chroma:
    embeddings = make_embeddings()
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )

def _distance_to_confidence(score: float) -> float:
    """
    Chroma gibt bei similarity_search_with_score typischerweise eine DISTANZ zurück:
    - bei Cosine: 0.0 = identisch, 1.0 = sehr unähnlich
    Wir mappen das grob auf confidence in [0..1] via (1 - dist), clamp.
    """
    if score is None:
        return 0.0
    conf = 1.0 - float(score)
    if conf < 0.0:
        conf = 0.0
    if conf > 1.0:
        conf = 1.0
    return conf


def query_rag_with_scores(query: str, k: int = TOP_K) -> List[tuple[Document, float]]:
    vectordb = load_vectordb()
    # returns: List[(Document, score)]
    return vectordb.similarity_search_with_score(query, k=k)


def retrieve_context(
    query: str,
    k: int = TOP_K,
    max_chars_per_doc: int = 1200,
    min_confidence: float = MIN_CONFIDENCE,
) -> Tuple[str, List[str]]:
    # Option A: hole Scores direkt (statt retriever.invoke)
    results = query_rag_with_scores(query, k=k)

    if not results:
        return "", []

    # Sortiere zur Sicherheit nach bester (niedrigster Distanz / höchste Confidence)
    results_sorted = sorted(results, key=lambda x: x[1])

    best_doc, best_score = results_sorted[0]
    best_conf = _distance_to_confidence(best_score)

    # Wenn der beste Treffer schon zu schlecht ist: kein Kontext -> "nicht in Dokumenten"
    if best_conf < min_confidence:
        return "", []

    parts: List[str] = []
    sources: List[str] = []
    seen = set()

    for i, (d, score) in enumerate(results_sorted, start=1):
        conf = _distance_to_confidence(score)

        # Optional: Filter auch für weitere Treffer (nicht nur best)
        if conf < min_confidence:
            continue

        src = d.metadata.get("source_file", "unbekannt")
        page = d.metadata.get("page", None)
        src_line = f"{src}" + (f" (Seite {page})" if page is not None else "")

        if src_line not in seen:
            sources.append(src_line)
            seen.add(src_line)

        text = (d.page_content or "").strip()
        if max_chars_per_doc and len(text) > max_chars_per_doc:
            text = text[:max_chars_per_doc] + " ..."

        parts.append(f"[{i}] {src_line} | conf={conf:.2f}\n{text}")

    if not parts:
        return "", []

    return "\n\n".join(parts), sources


def index_all_pdfs() -> str:
    n_chunks = build_vectorstore(pdf_path=None)
    return f"Index fertig. Chunks: {n_chunks}. DB: {CHROMA_DIR}"

def auto_index_if_needed() -> str:
    """
    Checks if the vector database exists and has data.
    If not, automatically indexes all PDFs.
    Returns status message.
    """
    # Check if chroma directory exists and has data
    if os.path.exists(CHROMA_DIR) and os.path.isdir(CHROMA_DIR):
        # Check if directory is not empty
        if any(os.scandir(CHROMA_DIR)):
            return f"Vector database already exists at {CHROMA_DIR}. Skipping auto-index."

    # Check if PDF directory exists
    if not os.path.exists(PDF_DIR) or not os.path.isdir(PDF_DIR):
        return f"PDF directory {PDF_DIR} not found. Skipping auto-index."

    # Check if there are any PDFs
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    if not pdf_files:
        return f"No PDFs found in {PDF_DIR}. Skipping auto-index."

    # Auto-index PDFs
    try:
        print(f"Auto-indexing {len(pdf_files)} PDFs from {PDF_DIR}...")
        n_chunks = build_vectorstore(pdf_path=None)
        return f"Auto-indexed {len(pdf_files)} PDFs into {n_chunks} chunks. DB: {CHROMA_DIR}"
    except Exception as e:
        return f"Auto-index failed: {str(e)}"
