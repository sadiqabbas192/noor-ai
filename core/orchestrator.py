from typing import Dict, Any
import re
from .config import DEBUG_MODE
from .retrieval import retrieve_context
from .reasoning import generate_scholarly_response

def print_debug(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)

def validate_citations(response_text: str, context: list) -> Dict:
    """
    Validates that the response only cites hadiths present in the retrieval context.
    """
    context_ids = set()
    for c in context:
        if 'hadith_no' in c:
            context_ids.add(c['hadith_no'])
            
    # Find all citations used in response [HADITH_NO:X]
    citations = re.findall(r"\[HADITH_NO:([0-9\.]+)\]", response_text)
    # Convert to float for comparison if needed, or string
    # But context uses original types.
    # Let's keep as float for set comparison if they are numbers.
    cited_ids = set(float(c) for c in citations)
    
    unknown_ids = cited_ids - context_ids
    if unknown_ids:
        return {
            "status": "FAIL",
            "reason": f"Hallucination Detected: Cited HADITH_NOs {unknown_ids} not found in retrieved context {context_ids}."
        }
    return {"status": "PASS"}

def chat_session(user_query: str) -> Dict[str, Any]:
    print_debug(f"\n💬 User: {user_query}")
    
    # 1. Retrieval
    context = retrieve_context(user_query, top_k=5)
    
    # 2. Reasoning
    response_obj = generate_scholarly_response(user_query, context)
    
    # 3. Validation
    validation = validate_citations(response_obj['answer'], context)
    
    # Enrich response object for CLI Renderer
    result = {
        "answer": response_obj['answer'],
        "confidence_level": "high" if context else "low", # Simple logic for now
        "intent": "scholarly_reasoning", # Static intent for Noor-AI
        "brand_elements_used": [f"HADITH_NO:{c['hadith_no']}" for c in context if 'hadith_no' in c],
        "memory_sources": ["authoritative_hadith"],
        "safety_status": response_obj.get("safety_status", "PASS"),
        "usage_info": response_obj.get("usage_info", {}),
        "live_context_used": False, # Noor-AI relies on static books
        "retrieved_count": len(context)
    }

    if validation['status'] == 'FAIL':
        print_debug(f"   🛡️ Safety Block: {validation['reason']}")
        result["answer"] = "I cannot answer this question because the generated response referenced hadiths that were not retrieved (Hallucination Guard)."
        result["safety_status"] = "BLOCKED_HALLUCINATION"
        result["validation_error"] = validation['reason']

    return result
