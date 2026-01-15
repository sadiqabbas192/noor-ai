import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("NEON_DB_URL")

try:
    conn = psycopg2.connect(DB_URL)
    with conn.cursor() as cur:
        # Check current database name
        cur.execute("SELECT current_database();")
        print(f"Connected to database: {cur.fetchone()[0]}")
        
        # List all tables in public schema
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Tables in public schema:")
        for t in tables:
            print(f"- {t[0]}")
            
except Exception as e:
    print(f"Error: {e}")
