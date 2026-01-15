import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import get_db_connection
import time

print("Testing database connection...")
try:
    conn = get_db_connection()
    print("Initial connection successful.")
    
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        print("Initial query successful.")
        
    print("Simulating connection close...")
    conn.close()
    
    print("Requesting connection again (should reconnect)...")
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        print("Reconnection query successful.")
        
    print("✅ Verification passed.")
except Exception as e:
    print(f"❌ Verification failed: {e}")
