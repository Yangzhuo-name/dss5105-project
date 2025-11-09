# src/retriever.py
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from src.config import OPENAI_API_KEY, EMBEDDING_MODEL

VECTOR_STORE_DIR = "./vector_store"


def load_vector_store():
    """Load persisted Chroma vector database"""
    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        model=EMBEDDING_MODEL
    )
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_DIR,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"}  # 确保使用cosine距离
    )
    return vector_store


def search(query: str, top_k: int = 5, with_scores: bool = False):
    """
    Search for relevant chunks in vector database
    
    Args:
        query: User's question
        top_k: Number of results to return
        with_scores: If True, attach similarity scores to documents
    
    Returns:
        List of Document objects (with scores if requested)
    """
    vector_store = load_vector_store()
    
    if with_scores:
        # Return documents with similarity scores
        results = vector_store.similarity_search_with_score(query, k=top_k)
        
        # Attach scores to document metadata
        processed_results = []
        for doc, score in results:
            doc.metadata["score"] = float(score)
            processed_results.append(doc)
        
        return processed_results
    else:
        # Return documents without scores
        return vector_store.similarity_search(query, k=top_k)


if __name__ == "__main__":
    # Test retrieval
    test_query = "When is rent due?"
    print(f"Testing query: {test_query}\n")
    
    results = search(test_query, top_k=3, with_scores=True)
    
    for i, doc in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Score: {doc.metadata.get('score', 'N/A')}")
        print(f"  Page: {doc.metadata.get('page', 'N/A')}")
        print(f"  Content: {doc.page_content[:150]}...")
        print()