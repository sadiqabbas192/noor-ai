from google import genai
import os
from itertools import cycle
from core.config import AVAILABLE_MODELS

_gemini_key_cycle = None
_gemini_model_cycle = cycle(AVAILABLE_MODELS)

def init_gemini_keys():
    global _gemini_key_cycle
    # Collect keys 1-11
    keys = []
    for i in range(1, 12): # 1 to 11
        key_name = f"GEMINI_API_KEY{i}"
        key_val = os.getenv(key_name)
        if key_val:
            keys.append((key_name, key_val))
            
    # Fallback to single key
    if not keys:
         single = os.getenv("GEMINI_API_KEY")
         if single:
             keys.append(("GEMINI_API_KEY", single))
    
    if not keys:
         raise ValueError("No Gemini API keys found.")
    
    _gemini_key_cycle = cycle(keys)

def get_gemini_model() -> str:
    global _gemini_model_cycle
    return next(_gemini_model_cycle)

def get_gemini_client():
    global _gemini_key_cycle
    if _gemini_key_cycle is None:
        init_gemini_keys()
    
    key_name, api_key = next(_gemini_key_cycle)
    return genai.Client(api_key=api_key), key_name

def safe_generate_content(model: str = None, contents=None, config=None, max_retries=4):
    """
    Safely call Gemini with automatic API key rotation on failure.
    If model is None, it rotates through the available models.
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            current_model = model if model else get_gemini_model()
            
            client, key_name = get_gemini_client()
            response = client.models.generate_content(
                model=current_model,
                contents=contents,
                config=config
            )
            
            # Attach usage info for debugging/display
            response._usage_info = {
                "model_name": current_model,
                "api_key_name": key_name
            }
            return response
            
        except Exception as e:
            last_error = e
            # Rotation happens naturally next call via get_gemini_model and get_gemini_client 
            # (which are cycles, but we need to ensure we actually pull next value if we loop)
            # Actually get_gemini_client returns next() every time it is called.
            # So simply calling it again in next iteration rotates key.
            # get_gemini_model returns next() every time.
            # So implementation handles rotation.
            # print(f"⚠️ Gemini call failed (attempt {attempt+1}/{max_retries}): {e}")
    
    raise RuntimeError(f"❌ All Gemini API keys exhausted. Last error: {last_error}")
