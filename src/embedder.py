# src/embedder.py
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from src.loader import load_and_chunk_pdf
from src.config import OPENAI_API_KEY, EMBEDDING_MODEL

VECTOR_STORE_DIR = "./vector_store"

def build_vector_store(pdf_path: str):
    """加载 PDF → 切 chunks → 生成 embedding → 持久化到 Chroma"""
    print("  Loading and chunking PDF...")
    chunks = load_and_chunk_pdf(pdf_path)

    print(f" Total chunks: {len(chunks)}")
    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        model=EMBEDDING_MODEL
    )

    print(" Generating embeddings and creating Chroma vector store...")
    print("   Using COSINE distance metric...")
    
    # 明确指定使用 cosine 距离
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_STORE_DIR,
        collection_metadata={"hnsw:space": "cosine"}  # 关键修改：使用cosine
    )

    print(" Persisting vector store...")
    vector_store.persist()
    print(f" Vector store created successfully at: {VECTOR_STORE_DIR}")
    print(f"   Distance metric: COSINE (0-2 range, lower is better)")


if __name__ == "__main__":
    # 检查PDF文件是否存在
    pdf_path = "./data/tenancy_agreement.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"   Error: PDF file not found at {pdf_path}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Please ensure the PDF is in the correct location.")
        sys.exit(1)
    
    print(f"Starting vector store generation...")
    print(f"PDF path: {pdf_path}")
    print(f"Output directory: {VECTOR_STORE_DIR}")
    print("="*60)
    
    build_vector_store(pdf_path)