import requests
import time
import sys
import json
import re

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    # Wait for server to start
    print("Waiting for server...")
    for _ in range(10):
        try:
            resp = requests.get(f"{base_url}/health")
            if resp.status_code == 200:
                print("Server is up!")
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        print("Server failed to start.")
        sys.exit(1)

    # Test Ask (Success)
    print("Testing /ask (Metadata & Filtering)...")
    payload = {"question": "What did Imam Ali (AS) say about leadership?"}
    try:
        resp = requests.post(f"{base_url}/ask", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Response: {data}")
            assert "answer" in data
            assert "references" in data
            assert "intent" in data
            assert "confidence" in data
            assert "model" in data
            assert "api_key" in data
            
            # Check filtering: References should only contain those in answer text
            citations_in_text = set(re.findall(r"\[HADITH_NO:([0-9\.]+)\]", data["answer"]))
            text_refs = {f"HADITH_NO:{c}" for c in citations_in_text}
            json_refs = set(data["references"])
            
            assert text_refs == json_refs, f"Mismatch: Text Refs={text_refs}, JSON Refs={json_refs}"
            print("PASS - Fields present and references filtered correctly.")

    except Exception as e:
        print(f"Failed to call /ask: {e}")

if __name__ == "__main__":
    test_api()
