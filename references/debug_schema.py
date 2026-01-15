import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("NEON_DB_URL")

try:
    conn = psycopg2.connect(DB_URL)
    with conn.cursor() as cur:
        # Check columns for hadiths
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'hadiths'
        """)
        columns = cur.fetchall()
        print("Columns in 'hadiths':")
        for col in columns:
            print(f"- {col}")

        # Check keys/constraints
        cur.execute("""
            SELECT
                tc.constraint_name, 
                tc.constraint_type, 
                kcu.column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu 
                  ON tc.constraint_name = kcu.constraint_name 
                  AND tc.table_schema = kcu.table_schema 
            WHERE tc.table_name = 'hadiths';
        """)
        constraints = cur.fetchall()
        print("\nConstraints on 'hadiths':")
        for c in constraints:
            print(f"- {c}")

except Exception as e:
    print(f"Error: {e}")
