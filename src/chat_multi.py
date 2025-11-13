# src/chat_multi.py
"""
功能2：多RAG综合回答
用于需要综合多个条款的复杂问题
"""

from openai import OpenAI
from src.retriever import search
from src.config import OPENAI_API_KEY, THRESHOLD_CAN_ANSWER
import re

client = OpenAI(api_key=OPENAI_API_KEY)

# 功能2的专用参数
RELEVANCE_THRESHOLD = 0.80  # 收集相关chunks的阈值（比0.65宽松）
TOP_K_COMPREHENSIVE = 50    # 检索的候选数量

# System prompt for comprehensive answers
COMPREHENSIVE_SYSTEM_PROMPT = """You are a professional tenancy agreement assistant.

Your task is to provide COMPREHENSIVE answers by synthesizing information from MULTIPLE contract clauses.

Rules:
1. Review ALL provided clauses carefully
2. Synthesize them into a complete, organized answer
3. Use clear structure (numbered lists, categories, etc.)
4. Include ALL relevant requirements, not just the main ones
5. Be thorough but concise
6. Use simple, tenant-friendly language

Answer format for "What to do" questions:
1. [First requirement/step]
2. [Second requirement/step]
3. [Third requirement/step]
...

Answer format for "Who is responsible" questions:
**Tenant responsibilities:**
- [Item 1]
- [Item 2]

**Landlord responsibilities:**
- [Item 1]
- [Item 2]
"""


def format_comprehensive_context(relevant_chunks):
    """格式化多个chunks给LLM"""
    context_parts = []
    
    # 按topic分组
    topics = {}
    for chunk in relevant_chunks:
        topic = chunk.metadata.get('topic', 'general')
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(chunk)
    
    # 格式化
    for topic, chunks in topics.items():
        context_parts.append(f"\n=== Topic: {topic.upper()} ===")
        for i, chunk in enumerate(chunks, 1):
            page = chunk.metadata.get('page', '?')
            score = chunk.metadata.get('score', 1.0)
            text = re.sub(r'\s+', ' ', chunk.page_content.strip())
            context_parts.append(f"\n[Clause {i} - Page {page}, Relevance: {1-score:.2f}]\n{text}")
    
    return "\n".join(context_parts)


def ask_comprehensive(query: str, active_pdf_path: str):
    """
    功能2：多RAG综合回答
    
    适用于需要综合多个条款的问题，如：
    - "退房前要做什么？"
    - "Who is responsible for repairs?"
    - "What are my payment obligations?"
    
    Returns:
        dict with:
        - can_answer: bool
        - answer: str
        - num_clauses_used: int
        - topics_covered: list
        - is_comprehensive: True (标记这是综合回答)
    """
    
    print(f"\n[comprehensive] 🔍 处理综合性问题: {query}")
    
    # 1. 检索大量候选
    results = search(
        query,
        top_k=TOP_K_COMPREHENSIVE,
        with_scores=True,
        active_pdf_path=active_pdf_path
    )
    
    if not results:
        return {
            "can_answer": False,
            "answer": "未找到相关信息",
            "num_clauses_used": 0,
            "topics_covered": [],
            "is_comprehensive": True
        }
    
    # 2. 先判断整体能否回答（用严格的0.65阈值）
    best_score = results[0].metadata.get('score', 1.0)
    print(f"[comprehensive] 📊 最佳匹配分数: {best_score:.3f}")
    
    if best_score >= THRESHOLD_CAN_ANSWER:
        print(f"[comprehensive] ❌ 分数不够 (>= {THRESHOLD_CAN_ANSWER}), 无法回答")
        return {
            "can_answer": False,
            "answer": (
                "我在租赁合同中没有找到足够相关的信息来回答这个问题。\n\n"
                "建议联系客服获取帮助。"
            ),
            "num_clauses_used": 0,
            "topics_covered": [],
            "is_comprehensive": True,
            "show_cta": True,
            "score": best_score
        }
    
    # 3. 能回答！收集所有相关的chunks（用宽松的0.80阈值）
    relevant_chunks = [
        r for r in results 
        if r.metadata.get('score', 1.0) < RELEVANCE_THRESHOLD
    ]
    
    print(f"[comprehensive] ✅ 找到 {len(relevant_chunks)} 个相关条款")
    
    if len(relevant_chunks) == 0:
        # 理论上不应该发生（因为best_score < 0.65）
        relevant_chunks = results[:3]
        print(f"[comprehensive] ⚠️  降级：使用top-3条款")
    
    # 4. 统计覆盖的topics
    topics_covered = list(set(
        chunk.metadata.get('topic', 'general') 
        for chunk in relevant_chunks
    ))
    
    print(f"[comprehensive] 📋 覆盖的主题: {topics_covered}")
    
    # 5. 格式化context
    context = format_comprehensive_context(relevant_chunks)
    
    # 6. 构建prompt
    user_prompt = f"""Question: {query}

I have found {len(relevant_chunks)} relevant clauses from the tenancy agreement covering {len(topics_covered)} different topics.

Please provide a COMPREHENSIVE answer that synthesizes ALL the information below:

{context}

Remember:
- Include ALL relevant points from ALL clauses
- Organize the answer clearly (use lists/categories)
- Be thorough but concise
- Use tenant-friendly language"""
    
    # 7. 调用GPT生成综合答案
    try:
        print(f"[comprehensive] 🤖 调用GPT生成综合答案...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": COMPREHENSIVE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,  # 稍高一点，允许更好的综合
            max_tokens=800    # 综合答案可能更长
        )
        
        answer_text = response.choices[0].message.content.strip()
        print(f"[comprehensive] ✅ 答案已生成 ({len(answer_text)} 字符)")
        
    except Exception as e:
        print(f"[comprehensive] ❌ GPT调用失败: {str(e)}")
        return {
            "can_answer": False,
            "answer": "生成答案时出现技术问题，请稍后重试或联系客服。",
            "num_clauses_used": len(relevant_chunks),
            "topics_covered": topics_covered,
            "is_comprehensive": True,
            "show_cta": True,
            "error": str(e)
        }
    
    # 8. 构建引用信息（显示用了哪些页的条款）
    pages_used = sorted(set(
        chunk.metadata.get('page', '?') 
        for chunk in relevant_chunks
    ))
    
    reference_summary = {
        "pages": pages_used,
        "num_clauses": len(relevant_chunks),
        "topics": topics_covered
    }
    
    return {
        "can_answer": True,
        "answer": answer_text,
        "reference": reference_summary,
        "num_clauses_used": len(relevant_chunks),
        "topics_covered": topics_covered,
        "is_comprehensive": True,
        "show_cta": False,
        "score": best_score
    }


# 检测关键词：判断是否需要综合回答
COMPREHENSIVE_KEYWORDS = [
    # 中文
    '要做什么', '需要做什么', '有哪些', '包括什么', '都有什么',
    '所有', '全部', '完整', '详细',
    
    # 英文
    'what to do', 'what should', 'what must', 'what do i need',
    'steps', 'requirements', 'obligations', 'responsibilities',
    'all', 'complete', 'comprehensive', 'everything',
    'list', 'include', 'cover',
]

def needs_comprehensive_answer(query: str) -> bool:
    """判断问题是否需要综合回答"""
    query_lower = query.lower()
    
    for keyword in COMPREHENSIVE_KEYWORDS:
        if keyword in query_lower:
            print(f"[detect] 🎯 检测到综合性关键词: '{keyword}'")
            return True
    
    return False


if __name__ == "__main__":
    # 测试
    test_queries = [
        "What do I need to do before moving out?",
        "Who is responsible for repairs?",
        "退房前要做什么？",
        "What are all my payment obligations?",
    ]
    
    for q in test_queries:
        print("\n" + "="*80)
        print(f"测试: {q}")
        print("="*80)
        
        if needs_comprehensive_answer(q):
            print("✅ 需要综合回答")
        else:
            print("❌ 不需要综合回答")