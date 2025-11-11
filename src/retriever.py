# src/retriever.py
import os, hashlib, json, shutil
from typing import Tuple

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# For modern LangChain:
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# If you're on OLD LangChain (<0.1.0), replace the two lines above with:
# from langchain.document_loaders import PyPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.config import OPENAI_API_KEY, EMBEDDING_MODEL

VECTOR_STORE_BASE_DIR = "./vector_store"
SIG_FILENAME = "store_signature.json"   # records md5 + source path


# ---------- helpers ----------
def _md5(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return "no-file"

def _persist_dir_for_pdf(pdf_path: str) -> Tuple[str, str]:
    """
    Use file CONTENT signature for a unique per-file directory.
    """
    sig = _md5(pdf_path)
    d = os.path.join(VECTOR_STORE_BASE_DIR, sig)
    os.makedirs(d, exist_ok=True)
    return d, sig

def _write_signature(persist_dir: str, pdf_path: str, sig: str):
    with open(os.path.join(persist_dir, SIG_FILENAME), "w", encoding="utf-8") as f:
        json.dump({"pdf_path": pdf_path, "md5": sig}, f, indent=2)

def _read_signature(persist_dir: str) -> dict:
    p = os.path.join(persist_dir, SIG_FILENAME)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ---------- build / load ----------
def _build_store(pdf_path: str, persist_dir: str) -> Tuple[Chroma, int]:
    print(f"[retriever] Building store from: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    print(f"[retriever] Split into {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)
    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_metadata={"hnsw:space": "cosine"},
    )
    store.persist()
    return store, len(chunks)

def _load_or_rebuild(pdf_path: str) -> Tuple[Chroma, str]:
    persist_dir, sig = _persist_dir_for_pdf(pdf_path)

    # If signature mismatches (or missing), nuke & rebuild to avoid staleness
    recorded = _read_signature(persist_dir)
    needs_rebuild = (recorded.get("md5") != sig)

    if needs_rebuild:
        # clear the dir so we don't accidentally reuse stale sqlite
        if os.path.isdir(persist_dir):
            for name in os.listdir(persist_dir):
                p = os.path.join(persist_dir, name)
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    try:
                        os.remove(p)
                    except:
                        pass

        store, n_chunks = _build_store(pdf_path, persist_dir)
        _write_signature(persist_dir, pdf_path, sig)
        print(f"[retriever] Persisted to: {persist_dir}")
        if n_chunks == 0:
            print("[retriever][WARN] 0 chunks created — PDF may be empty or loader failed.")
        return store, persist_dir

    # Signature matches → load existing
    print(f"[retriever] Loading existing store: {persist_dir}")
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)
    store = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )
    return store, persist_dir


# ---------- public API ----------
def search(query: str, top_k: int = 5, with_scores: bool = False, *, active_pdf_path: str):
    """
    Search chunks for the specified PDF. Rebuilds the store automatically
    if the on-disk signature doesn't match the current file content.

    NOTE: active_pdf_path is REQUIRED to avoid circular imports.
    """
    pdf = active_pdf_path
    if not pdf or not os.path.exists(pdf):
        raise FileNotFoundError(f"Active PDF not found: {pdf}")

    store, persist_dir = _load_or_rebuild(pdf)
    print(f"[retriever] Query: {query}")
    print(f"[retriever] Using store: {persist_dir}")

    if with_scores:
        pairs = store.similarity_search_with_score(query, k=top_k)
        out = []
        top_scores = []
        for doc, score in pairs:
            doc.metadata["score"] = float(score)
            out.append(doc)
            top_scores.append(float(score))
        if top_scores:
            print(f"[retriever] Top scores: {top_scores}")
        return out
    else:
        return store.similarity_search(query, k=top_k)


# Quick sanity test (run: python -m src.retriever)
if __name__ == "__main__":
    pdf_path = "./data/tenancy_agreement.pdf"
    rs = search("What's the diplomatic clause?", top_k=3, with_scores=True, active_pdf_path=pdf_path)
    for i, d in enumerate(rs, 1):
        print(f"{i}) score={d.metadata.get('score')} page={d.metadata.get('page')} text={d.page_content[:140]}...")
