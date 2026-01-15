import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import get_db_connection

def verify_preface():
    print("🔎 Verifying Special Sections Ingestion...")
    conn = get_db_connection()
    
    sections = {
        0.1: "Preface Text",
        0.2: "Preface Hadith",
        0.3: "Introduction"
    }
    
    with conn.cursor() as cur:
        for h_no, label in sections.items():
            # Cast to NUMERIC explicit or just pass param
            cur.execute("SELECT hadith_text FROM hadiths WHERE hadith_no = %s", (h_no,))
            row = cur.fetchone()
            
            if row:
                print(f"✅ Found {label} (ID: {h_no}): {row[0][:50]}...")
            else:
                print(f"❌ Missing {label} (ID: {h_no})")

if __name__ == "__main__":
    verify_preface()
