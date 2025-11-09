# src/rag_chain.py

from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from src.config import OPENAI_API_KEY, EMBEDDING_MODEL, CHAT_MODEL
from src.retriever import search

TOP_K = 3  # 检索仍然3条，但只展示最相关的1条

SYSTEM_PROMPT = """
You are a helpful assistant that answers questions based ONLY on the provided tenancy agreement.

Rules:
1. Answer in a clear and friendly tone.
2. If the agreement does not cover the question, say: "The agreement does not specify."
3. DO NOT hallucinate.
4. DO NOT output references in your main answer. References will be added later.
"""

def answer(question: str):
    # 1) Retrieve contract clauses
    results = search(question, top_k=TOP_K)

    # Top-1 for reference (most relevant)
    top_clause = results[0]
    top_text = top_clause.page_content.strip()
    page_num = top_clause.metadata.get("page", top_clause.metadata.get("page_number", "Unknown"))

    # 2) Build context for LLM (still use top-3 as knowledge)
    context = "\n\n".join([doc.page_content for doc in results])

    # 3) Prepare LLM
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=CHAT_MODEL,
        temperature=0.2
    )

    # 4) Prompt LLM
    messages = [
        ("system", SYSTEM_PROMPT),
        ("user", f"Context:\n{context}\n\nQuestion: {question}")
    ]

    response = llm.invoke(messages)

    # 5) Assemble final formatted answer
    final_answer = (
        f"{response.content.strip()}\n\n"
        f"Reference:\n"
        f"- Clause (Page {page_num}): \"{top_text}\""
    )

    return final_answer


if __name__ == "__main__":
    print(answer("When is rent due?"))
