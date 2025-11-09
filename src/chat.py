# src/chat.py
from openai import OpenAI
from src.retriever import search
from src.config import OPENAI_API_KEY, TOP_K_RETRIEVAL, TOP_K_CONTEXT
import re

client = OpenAI(api_key=OPENAI_API_KEY)

# ========== CONFIDENCE THRESHOLDS ==========
# Based on Chroma COSINE distance: 0-2 range, lower = more similar
# Benchmark results: 0.56-0.63 for exact matches
THRESHOLD_HIGH = 0.70      # < 0.70: High confidence (direct answer)
THRESHOLD_MEDIUM = 0.90    # 0.70-0.90: Medium confidence (related but unclear)
# > 0.90: Low confidence (not relevant)

# ========== SYSTEM PROMPT ==========
SYSTEM_PROMPT = """You are a professional tenancy agreement assistant for Singapore properties.

Your role:
- Answer questions based ONLY on the provided contract clauses
- Use clear, simple language suitable for tenants
- Structure answers: direct answer first, then key details, then exceptions
- If multiple clauses are relevant, synthesize into one coherent answer
- Never invent information not in the contract

Answer format:
1. Direct answer (1-2 sentences)
2. Key details or conditions (if applicable)
3. Important notes or exceptions (if any)

If the contract doesn't specify something, clearly state: "The agreement does not specify this."
"""


def calculate_confidence(results):
    """
    Determine confidence level based on retrieval scores
    
    Returns:
        tuple: (best_score, confidence_level)
    """
    if not results or len(results) == 0:
        return 1.0, "low"
    
    scores = [float(r.metadata.get("score", 1.0)) for r in results]
    best_score = scores[0]
    
    # Simple threshold-based classification (no downgrade logic)
    if best_score < THRESHOLD_HIGH:
        confidence = "high"
    elif best_score < THRESHOLD_MEDIUM:
        confidence = "medium"
    else:
        confidence = "low"
    
    return best_score, confidence


def format_context(results, max_clauses=TOP_K_CONTEXT):
    """Format retrieved clauses for LLM consumption"""
    context_parts = []
    for i, doc in enumerate(results[:max_clauses], 1):
        page = doc.metadata.get("page", "?")
        text = doc.page_content.strip()
        # Clean up excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        context_parts.append(f"[Clause {i} - Page {page}]\n{text}")
    
    return "\n\n".join(context_parts)


def extract_reference(results):
    """Extract the most relevant clause for display"""
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
    Main chatbot function
    
    Returns:
        dict with keys:
        - confidence: "high"/"medium"/"low"
        - answer: str (formatted response)
        - reference: dict or None (clause + page number)
        - show_cta: bool (show contact support button)
        - score: float (for debugging)
    """
    
    # Step 1: Retrieve relevant clauses
    results = search(query, top_k=TOP_K_RETRIEVAL, with_scores=True)
    
    # Step 2: Calculate confidence
    score, confidence = calculate_confidence(results)
    
    # ========== LOW CONFIDENCE CASE ==========
    if confidence == "low":
        return {
            "confidence": "Low",
            "answer": (
                "I couldn't find relevant information in your tenancy agreement for this question.\n\n"
                "**Possible reasons:**\n"
                "• This topic is not covered in the agreement\n"
                "• The question requires legal interpretation beyond the contract terms\n\n"
                "**Recommendation:** Contact our support team for personalized assistance with this matter."
            ),
            "reference": None,
            "show_cta": True,
            "score": score
        }
    
    # ========== MEDIUM CONFIDENCE CASE ==========
    if confidence == "medium":
        reference = extract_reference(results)
        return {
            "confidence": "Medium",
            "answer": (
                f"I found related information in your agreement (see reference below, Page {reference['page']}).\n\n"
                "However, this may require interpretation based on your specific situation. "
                "I recommend reviewing the clause and contacting support if you need clarification."
            ),
            "reference": reference,
            "show_cta": True,
            "score": score
        }
    
    # ========== HIGH CONFIDENCE CASE ==========
    # Format context for LLM
    context = format_context(results, max_clauses=TOP_K_CONTEXT)
    
    # Build prompt
    user_prompt = f"""Question: {query}

Relevant Contract Clauses:
{context}

Please provide a clear, accurate answer based on these clauses."""

    # Call GPT
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=500
        )
        
        answer_text = response.choices[0].message.content.strip()
        
    except Exception as e:
        # Fallback if API fails
        answer_text = (
            "I apologize, but I'm experiencing technical difficulties. "
            "Please try again or contact support."
        )
        return {
            "confidence": "Error",
            "answer": answer_text,
            "reference": None,
            "show_cta": True,
            "score": score
        }
    
    # Extract reference
    reference = extract_reference(results)
    
    return {
        "confidence": "High",
        "answer": answer_text,
        "reference": reference,
        "show_cta": False,
        "score": score
    }
