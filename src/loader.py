# src/loader.py

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config import CHUNK_SIZE, CHUNK_OVERLAP

def load_and_chunk_pdf(pdf_path: str):
    """读取 PDF 并切成 chunk 列表"""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = splitter.split_documents(pages)
    return chunks

if __name__ == "__main__":
    chunks = load_and_chunk_pdf("./data/tenancy_agreement.pdf")
    print(f"Total Chunks: {len(chunks)}")
    print(chunks[0].page_content)
