# rag.py
from __future__ import annotations

import argparse
import os
from typing import List, Tuple

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

PDF_PATH = "////PATH /////Angabe_MRK.pdf"
CHROMA_DIR = "chroma_db"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
TOP_K = 4


def make_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def build_vectorstore(
    pdf_path: str = PDF_PATH,
    chroma_dir: str = CHROMA_DIR,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> int:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

    loader = PyPDFLoader(pdf_path)
    documents: List[Document] = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documents)
    print(f"Anzahl Chunks: {len(chunks)}")

    embeddings = make_embeddings()

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=chroma_dir,
    )
    vectordb.persist()
    print(f" Vectorstore erstellt und gespeichert in: {chroma_dir}")
    return len(chunks)


def load_vectordb() -> Chroma:
    embeddings = make_embeddings()
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )


def query_rag(query: str, k: int = TOP_K, search_type: str = "similarity") -> List[Document]:
    vectordb = load_vectordb()
    retriever = vectordb.as_retriever(
        search_type=search_type,          # "similarity" oder "mmr"
        search_kwargs={"k": k},
    )
    return retriever.invoke(query)


def retrieve_context(
    query: str,
    k: int = TOP_K,
    search_type: str = "similarity",
    max_chars_per_doc: int = 1200,
) -> Tuple[str, List[str]]:
    docs = query_rag(query, k=k, search_type=search_type)
    if not docs:
        return "", []

    parts: List[str] = []
    sources: List[str] = []
    seen = set()

    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unbekannt")
        page = d.metadata.get("page", None)
        src_line = f"{src}" + (f" (Seite {page})" if page is not None else "")

        if src_line not in seen:
            sources.append(src_line)
            seen.add(src_line)

        text = (d.page_content or "").strip()
        if max_chars_per_doc and len(text) > max_chars_per_doc:
            text = text[:max_chars_per_doc] + " ..."

        parts.append(f"[{i}] {src_line}\n{text}")

    return "\n\n".join(parts), sources


def rag_answer_prompt(query: str, k: int = TOP_K, search_type: str = "similarity"):
    context, sources = retrieve_context(query, k=k, search_type=search_type)
    if not context:
        return "", []
    prompt_block = (
        "Nutze den folgenden Kontext, wenn er relevant ist. "
        "Wenn der Kontext nicht passt, ignoriere ihn.\n\n"
        f"KONTEXT:\n{context}\n"
    )
    return prompt_block, sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--k", type=int, default=TOP_K)
    parser.add_argument("--search-type", type=str, default="similarity", choices=["similarity", "mmr"])
    args = parser.parse_args()

    if args.build:
        build_vectorstore()

    if args.query:
        docs = query_rag(args.query, k=args.k, search_type=args.search_type)
        for i, d in enumerate(docs, 1):
            print("=" * 50)
            print(f"Treffer {i} | source={d.metadata.get('source')} | page={d.metadata.get('page')}")
            print((d.page_content or "")[:800], "...\n")

    if args.interactive:
        while True:
            q = input("\nFrage an RAG (oder 'exit'): ").strip()
            if q.lower() in ("exit", "quit"):
                break
            docs = query_rag(q, k=args.k, search_type=args.search_type)
            for i, d in enumerate(docs, 1):
                print("=" * 50)
                print(f"Treffer {i} | source={d.metadata.get('source')} | page={d.metadata.get('page')}")
                print((d.page_content or "")[:800], "...\n")


if __name__ == "__main__":
    main()
