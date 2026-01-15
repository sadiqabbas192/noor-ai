import os
from dotenv import load_dotenv

load_dotenv()

# Environment Variables
DB_URL = os.getenv("NEON_DB_URL")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Models (Updated list from user)
AVAILABLE_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-3-flash-preview"
]

# Keys - Handled in services/gemini.py but config can expose placeholders if needed
# For now, keys are accessed directly via os.getenv in the service.

DEBUG_MODE = False
ALLOWED_INTENTS = ["scholar", "reasoning"]
FORBIDDEN_KEYWORDS = [] # Can add later if needed
