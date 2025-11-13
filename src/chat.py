# src/chat.py
"""
主聊天模块（整合功能1和功能2）
使用二分类：能答/不能答
"""

from openai import OpenAI
from src.retriever import search  
from src.config import OPENAI_API_KEY, TOP_K_RETRIEVAL, TOP_K_CONTEXT, THRESHOLD_CAN_ANSWER
from src.chat_multi import ask_comprehensive, needs_comprehensive_answer
import re
import hashlib
from typing import Dict, Any

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Active contract management
_ACTIVE_PDF_PATH = "./data/tenancy_agreement.pdf"
_ACTIVE_HASH = None

def _md5(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return "no-file"

def set_active_pdf(path: str):
    global _ACTIVE_PDF_PATH, _ACTIVE_HASH
    _ACTIVE_PDF_PATH = path
    _ACTIVE_HASH = _md5(path)
    print(f"[chat] Active PDF set to: {_ACTIVE_PDF_PATH}")

def get_active_pdf() -> str:
    return _ACTIVE_PDF_PATH

def debug_info() -> Dict[str, Any]:
    return {
        "pdf_path": _ACTIVE_PDF_PATH,
        "pdf_sig": _ACTIVE_HASH or _md5(_ACTIVE_PDF_PATH),
    }

# System prompt (功能1用)
SYSTEM_PROMPT = """You are a professional tenancy agreement assistant for Singapore properties.

Your role:
- Answer questions based ONLY on the provided contract clauses
- Use clear, simple language suitable for tenants
- Structure answers: direct answer first, then key details, then exceptions
- Never invent information not in the contract

Answer format:
1. Direct answer (1-2 sentences)
2. Key details or conditions (if applicable)
3. Important notes or exceptions (if any)

If the contract doesn't specify something, clearly state: "The agreement does not specify this."
"""


def format_context(results, max_clauses=TOP_K_CONTEXT):
    """Format retrieved clauses for LLM consumption."""
    context_parts = []
    for i, doc in enumerate(results[:max_clauses], 1):
        page = doc.metadata.get("page", "?")
        text = doc.page_content.strip()
        text = re.sub(r'\s+', ' ', text)
        context_parts.append(f"[Clause {i} - Page {page}]\n{text}")
    return "\n\n".join(context_parts)


def extract_reference(results):
    """Extract the most relevant clause for display."""
    if not results:
        return None

    main_doc = results[0]
    clause_text = re.sub(r'\s+', ' ', main_doc.page_content.strip())
    page = main_doc.metadata.get("page", "Unknown")

    return {
        "text": clause_text,
        "page": page
    }


def ask(query: str):
    """
    主入口函数 - 自动选择功能1或功能2
    
    功能1：单条款回答（普通问题）
    功能2：多RAG综合回答（综合性问题）
    
    Returns:
        dict with keys:
        - can_answer: bool
        - answer: str
        - reference: dict or None
        - show_cta: bool
        - score: float
        - is_comprehensive: bool (if功能2)
        - num_clauses_used: int (if功能2)
        - topics_covered: list (if功能2)
    """
    
    print(f"\n[chat] " + "="*50)
    print(f"[chat] 💬 Query: {query}")
    print(f"[chat] " + "="*50)
    
    # ========== 判断：需要综合回答吗？ ==========
    if needs_comprehensive_answer(query):
        print(f"[chat] 🎯 使用功能2：多RAG综合回答")
        return ask_comprehensive(query, _ACTIVE_PDF_PATH)
    
    # ========== 功能1：普通单条款回答 ==========
    print(f"[chat] 📌 使用功能1：单条款回答")
    
    # 1) Retrieve relevant clauses
    results = search(
        query,
        top_k=TOP_K_RETRIEVAL,
        with_scores=True,
        active_pdf_path=_ACTIVE_PDF_PATH,
    )

    if not results:
        return {
            "can_answer": False,
            "answer": "未找到相关信息",
            "reference": None,
            "show_cta": True,
            "score": 1.0,
            "is_comprehensive": False
        }

    # 2) Calculate confidence
    best_score = results[0].metadata.get("score", 1.0)
    print(f"[chat] 📊 Score: {best_score:.3f}")
    
    # ===== 不能回答 =====
    if best_score >= THRESHOLD_CAN_ANSWER:
        print(f"[chat] ❌ 无法回答 (score >= {THRESHOLD_CAN_ANSWER})")
        return {
            "can_answer": False,
            "answer": (
                "我在租赁合同中没有找到相关信息来回答这个问题。\n\n"
                "建议联系客服获取帮助。"
            ),
            "reference": None,
            "show_cta": True,
            "score": best_score,
            "is_comprehensive": False
        }

    # ===== 能回答 =====
    print(f"[chat] ✅ 可以回答 (score < {THRESHOLD_CAN_ANSWER})")
    
    # 3) Prepare context for LLM
    context = format_context(results, max_clauses=TOP_K_CONTEXT)
    user_prompt = f"""Question: {query}

Relevant Contract Clauses:
{context}

Please provide a clear, accurate answer based on these clauses."""

    # 4) Call GPT
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        answer_text = response.choices[0].message.content.strip()
        print(f"[chat] 📝 Answer generated")
        
    except Exception as e:
        print(f"[chat] ❌ API Error: {str(e)}")
        return {
            "can_answer": False,
            "answer": "生成答案时出现技术问题，请稍后重试。",
            "reference": None,
            "show_cta": True,
            "score": best_score,
            "is_comprehensive": False,
            "error": str(e)
        }

    # 5) Attach reference
    reference = extract_reference(results)
    
    print(f"[chat] ✅ Response complete\n")
    
    return {
        "can_answer": True,
        "answer": answer_text,
        "reference": reference,
        "show_cta": False,
        "score": best_score,
        "is_comprehensive": False
    }