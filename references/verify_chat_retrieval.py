import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.retrieval import retrieve_context

def verify_chat():
    print("🔎 Verifying Full Retrieval Pipeline...")
    query = "explain the preface"
    print(f"   Query: '{query}'")
    
    try:
        results = retrieve_context(query)
        print(f"\n✅ Retrieved {len(results)} items.")
        
        found_preface = False
        for item in results:
            # Item is formatted string or dict? 
            # retrieve_context returns LIST of DICT now (per my last edit to retrieval.py)
            # checking logic...
            content = item.get('content', '')
            h_no = item.get('hadith_no')
            print(f"   [ID: {h_no}] {content[:50]}...")
            
            if str(h_no) in ['0.1', '0.2']:
                found_preface = True
                
        if found_preface:
            print("\n✅ SUCCESS: Context contains Preface content.")
        else:
            print("\n❌ FAILURE: Preface content missing from context.")
            
    except Exception as e:
        print(f"❌ Error during retrieval: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_chat()
