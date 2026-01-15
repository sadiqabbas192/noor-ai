import os
import sys

# Ensure package is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google import genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY1") or os.getenv("GEMINI_API_KEY")
if not key:
    print("No API Key found")
    sys.exit(1)

client = genai.Client(api_key=key)

try:
    print("Listing Models...")
    for m in client.models.list():
        print(f"Model: {m.name}")
except Exception as e:
    print(f"Error: {e}")
