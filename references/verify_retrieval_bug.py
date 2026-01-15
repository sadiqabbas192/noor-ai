import sys
import os
from unittest.mock import MagicMock, patch
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.retrieval import retrieve_context
from core.database import get_db_connection

def verify():
    # 1. Check if DB has ID 0
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT book_id, hadith_no FROM hadiths WHERE hadith_no = 0")
        row = cur.fetchone()
        if not row:
            print("❌ PREFACE (ID 0) NOT FOUND IN DB! Run ingestion first.")
            return
        print(f"✅ Found Preface in DB: {row}")

    # 2. Mock Pinecone to return ID 0
    mock_pinecone = MagicMock()
    mock_index = MagicMock()
    mock_pinecone.Index.return_value = mock_index
    
    # Mock search result
    mock_index.query.return_value = {
        'matches': [
            {
                'id': 'kitab_sulaym_0',
                'score': 0.99,
                'metadata': {
                    'book_id': 'kitab_sulaym',
                    'hadith_no': 0 # The problematic value
                }
            }
        ]
    }
    
    with patch('core.retrieval.get_pinecone_client', return_value=mock_pinecone):
        # 3. Call retrieval
        print("running retrieval...")
        results = retrieve_context("test query")
        
        # 4. Assert
        if len(results) == 1 and results[0]['hadith_no'] == 0:
            print("✅ SUCCESS: Retrieved Preface (ID 0) successfully.")
        else:
            print(f"❌ FAILURE: Results: {results}")

if __name__ == "__main__":
    verify()
