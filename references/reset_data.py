import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import get_pinecone_client, get_db_connection

def reset_system():
    # 1. Reset Pinecone
    try:
        pc = get_pinecone_client()
        index_name = "kitab-sulaym"
        if index_name in pc.list_indexes().names():
            print(f"🗑️ Deleting Pinecone index: {index_name}...")
            pc.delete_index(index_name)
            print("✅ Index deleted.")
        else:
            print("ℹ️ Index not found, nothing to delete.")
    except Exception as e:
        print(f"❌ Error resetting Pinecone: {e}")

    # 2. Clear Postgres (Optional but good for clean state)
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            print("🗑️ Truncating Postgres tables...")
            cur.execute("TRUNCATE TABLE hadiths, books CASCADE;")
        conn.commit()
        print("✅ Database cleared.")
    except Exception as e:
        print(f"❌ Error clearing Postgres: {e}")

if __name__ == "__main__":
    reset_system()
