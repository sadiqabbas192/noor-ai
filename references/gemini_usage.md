# Multi-Model & API Key Rotation Strategy

This document outlines the strategy used in **Brand Brain** to maximize reliability and leverage free tier limits by rotating across multiple Gemini models and API keys.

## 1. The Core Concept

The goal is to avoid `RESOURCE_EXHAUSTED` (429) errors and single points of failure. We achieve this by:

1. **Multiple API Keys**: Creating a pool of keys (e.g., `GEMINI_API_KEY1` to `GEMINI_API_KEY11`).
2. **Multiple Models**: Leveraging the entire Gemini 2.5/2.0 family (Pro, Flash, Flash-Lite).
3. **Round-Robin Rotation**: Using Python's `itertools.cycle` to infinitely rotate through these resources.
4. **Automatic Retry**: If a call fails, we catch the exception and immediately retry with the *next* key/model in the cycle.

## 2. Implementation Logic

### A. Key Rotation

We store keys in a list and wrap them in an iterator that loops indefinitely.

```python
from itertools import cycle
import os

def init_gemini_keys():
    # 1. Load Keys
    keys = [
        ("KEY_1", os.getenv("GEMINI_API_KEY1")),
        ("KEY_2", os.getenv("GEMINI_API_KEY2")),
        # ... add as many as you have
    ]
    
    # 2. Filter Valid Keys
    valid_keys = [k for k in keys if k[1]]
    
    # 3. Create Infinite Cycle
    global _gemini_key_cycle
    _gemini_key_cycle = cycle(valid_keys)

def get_gemini_client():
    # 4. Fetch Next Key
    key_name, api_key = next(_gemini_key_cycle)
    return genai.Client(api_key=api_key), key_name
```

### B. Model Rotation

Similarly, we rotate through models. This allows us to use `Flash` for speed/cost, but fallback to `Pro` or `Lite` if quotas are hit.

```python
AVAILABLE_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-3-flash-preview"
]

_gemini_model_cycle = cycle(AVAILABLE_MODELS)

def get_gemini_model() -> str:
    return next(_gemini_model_cycle)
```

### C. The Safe Wrapper

The critical piece is a wrapper function [safe_generate_content](file:///d:/brand-brain/brand_brain/services/gemini.py#59-89) that handles the retry logic.

```python
def safe_generate_content(model=None, contents=None, max_retries=4):
    for attempt in range(max_retries):
        try:
            # 1. Select Resource
            # Use specific model if requested, otherwise rotate
            current_model = model if model else get_gemini_model()
            
            # Get next client (which gets next API key)
            client, key_name = get_gemini_client()
            
            # 2. Attempt Call
            response = client.models.generate_content(
                model=current_model, 
                contents=contents
            )
            
            # 3. Attach Metadata (Optional: for Transparency)
            response._usage_info = {
                "model_name": current_model,
                "api_key_name": key_name
            }
            return response
            
        except Exception as e:
            # 4. On Failure: Loop continues -> Next Key/Model is picked automatically!
            print(f"⚠️ Failed with {current_model}/{key_name}: {e}")
            continue
    
    raise RuntimeError("❌ All retries exhausted.")
```

## 3. Advantages

* **Zero Downtime**: If one key hits a limit, the next one picks up immediately.
* **Maximized Free Tier**: You can use the free limits of *every* model variant combined.
* **Simplicity**: No complex state management; `cycle()` handles the pointer.

## 4. Usage in Other Projects

To adapt this:

1. Copy the [init_gemini_keys](file:///d:/brand-brain/brand_brain/services/gemini.py#8-35) and [safe_generate_content](file:///d:/brand-brain/brand_brain/services/gemini.py#59-89) functions.
2. Define your `AVAILABLE_MODELS` list based on your needs.
3. Replace direct library calls (e.g., `client.generate_content`) with [safe_generate_content(contents=...)](file:///d:/brand-brain/brand_brain/services/gemini.py#59-89).
