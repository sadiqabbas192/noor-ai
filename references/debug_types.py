import sys
import os
import decimal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import get_db_connection

def debug_types():
    print("🔎 Debugging Type Mismatch (Float vs Decimal)...")
    conn = get_db_connection()
    
    # 1. Fetch 0.1 from DB
    with conn.cursor() as cur:
        cur.execute("SELECT hadith_no FROM hadiths WHERE hadith_no = 0.1")
        row = cur.fetchone()
        if not row:
            print("❌ DB Query failed to find 0.1")
            return
        
        db_val = row[0]
        print(f"   DB Value: {db_val} | Type: {type(db_val)}")
        
    # 2. Compare with Python float
    py_val = 0.1
    print(f"   Python Value: {py_val} | Type: {type(py_val)}")
    
    if db_val == py_val:
        print("✅ Equality Check: PASS")
    else:
        print("❌ Equality Check: FAIL")
        print(f"   Reason: {repr(db_val)} != {repr(py_val)}")
        
    # 3. Compare with cast
    if float(db_val) == py_val:
         print("✅ Equality Check (with float cast): PASS")

if __name__ == "__main__":
    debug_types()
