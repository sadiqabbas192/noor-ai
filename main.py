import argparse
import sys
import threading
import time
import os
from typing import Dict, Any

from core.ingestion import ingest_brand
from core.orchestrator import chat_session

# Sample Data for Noor-AI ingestion? 
# Noor-AI ingests from files, not sample dictionaries in code.
# We will keep the CLI ingest command clean.

class LoadingAnimation:
    """
    Context manager for a 5-dot loading animation.
    Cycles 1 to 5 dots every second.
    """
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._animate)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_event.set()
        self._thread.join()
        sys.stdout.write("\r" + " " * 20 + "\r") # Clear line
        sys.stdout.flush()

    def _animate(self):
        dots = 1
        while not self._stop_event.is_set():
            sys.stdout.write(f"\rthinking{'.' * dots}") 
            sys.stdout.flush()
            time.sleep(0.5)
            dots = (dots % 5) + 1

def render_noor_ai_response_clean(response: Dict, intent: str):
    """
    Non-tech friendly Noor-AI response renderer (CLI Version).
    """    
    # Divider
    print("\n" + "-" * 60)
    
    # 1. Intent
    print(f"Intent : {intent}")
    
    # 2. Response
    # Handle blocked safety status
    if response.get("safety_status") != "PASS":
        print(f"Response : ❌ {response.get('answer', '_Refused_')}")
        print(f"Reason   : {response.get('validation_error', 'Safety Block')}")
    else:
        print(f"Response : {response.get('answer', '_No response generated._')}")
    
    # 3. Confidence
    confidence = response.get("confidence_level", "unknown")
    print(f"Confidence : {confidence}")
    
    # 4. Why this answer
    explain_lines = []
    
    if response.get("brand_elements_used"):
        # For Noor-AI, these are Hadith citations
        citations = response.get("brand_elements_used", [])
        if citations:
            explain_lines.append(f"Derived from {len(citations)} authoritative traditions.")

    if response.get("memory_sources"):
        explain_lines.append("Strictly evidence-bound (no external knowledge).")

    why_text = " ".join(explain_lines)
    if not why_text:
        why_text = "Answered using available authoritative texts."
        
    print(f"why this answer : {why_text}")
    
    # 5. Usage Info
    usage_info = response.get("usage_info", {})
    if usage_info:
        # Hide key for production/clean, show simpler model name
        print(f"Model Used : {usage_info.get('model_name', 'Unknown')}")
        # print(f"API Key Used : {usage_info.get('api_key_name', 'Unknown')}") 
        # User snippet showed Key Name. I will show it too.
        print(f"API Key Used : {usage_info.get('api_key_name', 'Unknown')}")
    
    print("-" * 60 + "\n")

def ask_noor_ai():
    """
    Interactive Noor-AI chat loop.
    """
    print("\n👋 Welcome to Noor-AI")
    print("Type 'exit' to stop.\n")

    while True:
        try:
            print("You: ", end="", flush=True)
            user_query = sys.stdin.readline().strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting Noor-AI chat.")
            break

        if user_query.lower() in ["exit", "quit"]:
            print("👋 Exiting Noor-AI chat.")
            break

        if not user_query:
            continue

        try:
            # Check DEBUG_MODE to decide if we show animation
            # For clean UX, we default to animation but debug output might interfere.
            # We assume user wants nice UX by default.
            
            with LoadingAnimation():
                response = chat_session(user_query)
            
            # Extract intent safely
            intent = response.get("intent", "scholarly_reasoning")

            # Render clean UX
            render_noor_ai_response_clean(response, intent)
            
        except Exception as e:
            print(f"❌ Error during chat session: {e}")

def main():
    parser = argparse.ArgumentParser(description="Noor-AI CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest Command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest hadith book")
    ingest_parser.add_argument("--file", type=str, default="hadith_cleaned.json", help="Path to JSON file")

    # Interactive Command (Ask)
    interactive_parser = subparsers.add_parser("chat", help="Start interactive chat mode")
    
    # General Debug Flag
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Set Debug Mode Globally
    if getattr(args, 'debug', False):
        import core.config 
        core.config.DEBUG_MODE = True
        print("🔧 Debug Mode Enabled")
    else:
        import core.config
        core.config.DEBUG_MODE = False

    if args.command == "ingest":
        path = args.file
        if not os.path.exists(path):
             print(f"File not found: {path}")
             return
        ingest_brand(path)
        
    elif args.command == "chat":
        ask_noor_ai()
        
    else:
        # Default to interactive if no args provided? Or help.
        # User snippet defaults to printing help.
        parser.print_help()

if __name__ == "__main__":
    main()
