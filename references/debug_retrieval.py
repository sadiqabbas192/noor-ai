import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.retrieval import retrieve_context
from core.database import get_pinecone_client

def debug_query(query):
    print(f"🔎 Query: '{query}'")
    
    # 1. Check raw Pinecone results
    pc = get_pinecone_client()
    index = pc.Index("kitab-sulaym")
    
    # Generate embedding (using the service)
    from services.embedding import generate_query_embedding
    vector = generate_query_embedding(query)
    
    print("   -> Querying Pinecone (Top 10)...")
    results = index.query(
        namespace="noor_ai:kitab_sulaym:english:hadith",
        vector=vector,
        top_k=10,
        include_metadata=True
    )
    
    print("\n   --- Top Matches ---")
    found_preface = False
    for match in results['matches']:
        md = match.get('metadata', {})
        h_no = md.get('hadith_no')
        score = match['score']
        text = md.get('text', 'N/A')
        print(f"   ID: {h_no} | Score: {score:.4f} | Text: {text[:50]}...")
        if str(h_no) in ['0.1', '0.2', '0.3']:
            found_preface = True
            
    if not found_preface:
        print("\n❌ Preface/Introduction (0.1, 0.2, 0.3) NOT found in top 10.")
    else:
        print("\n✅ Preface found in top results.")

if __name__ == "__main__":
    debug_query("explain the preface")
