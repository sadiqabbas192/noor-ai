from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import logging

from core.orchestrator import chat_session

router = APIRouter()

class Question(BaseModel):
    question: str

class Answer(BaseModel):
    answer: str
    references: List[str]
    intent: str
    confidence: str
    model: str
    api_key: str

@router.get("/")
def root():
    return {"message": "Welcome to Noor-AI API"}

@router.post("/ask", response_model=Answer)
def ask_question(q: Question):
    try:
        # Call the core orchestrator
        # chat_session handles retrieval, reasoning, and validation
        response = chat_session(q.question)
        
        # Check safety/validation status
        if response.get("safety_status") != "PASS":
            refusal_answer = response.get("answer", "I cannot answer this question due to safety constraints.")
            return Answer(
                answer=refusal_answer, 
                references=[],
                intent=response.get("intent", "scholarly_reasoning"),
                confidence="low",
                model="unknown",
                api_key="unknown"
            )

        # Success case
        answer_text = response.get("answer", "")
        
        # Filter references to only those actually cited in the text
        # Logic: Find all [HADITH_NO:X] in the text
        import re
        citations = re.findall(r"\[HADITH_NO:([0-9\.]+)\]", answer_text)
        # Format them back as HADITH_NO:X to match the expected output format
        # Use a generic set to avoid duplicates, though list order might be nice to preserve if desired.
        # User output had ["HADITH_NO:0.2", ...]. list(dict.fromkeys(...)) preserves order.
        references = [f"HADITH_NO:{c}" for c in list(dict.fromkeys(citations))]
        
        # Metadata
        usage_info = response.get("usage_info", {})
        
        return Answer(
            answer=answer_text, 
            references=references,
            intent=response.get("intent", "scholarly_reasoning"),
            confidence=response.get("confidence_level", "unknown"),
            model=usage_info.get("model_name", "unknown"),
            api_key=usage_info.get("api_key_name", "unknown")
        )

    except Exception as e:
        # "If Gemini fails -> return HTTP 503 with safe message"
        # "Do NOT leak stack traces"
        logging.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service currently unavailable")

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/version")
def version_info():
    return {
        "name": "Noor-AI",
        "version": "1.1.0-dev",
        "interface": "fastapi"
    }
