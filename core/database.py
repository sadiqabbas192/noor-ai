import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pinecone import Pinecone
from .config import DB_URL, PINECONE_API_KEY

_db_conn = None
_pinecone_client = None

def get_db_connection():
    global _db_conn
    
    # 1. Liveness Check if connection exists
    if _db_conn is not None and not _db_conn.closed:
        try:
            with _db_conn.cursor() as cur:
                cur.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"⚠️  Database connection stale, reconnecting... ({e})")
            _db_conn = None # Force reconnect
            
    # 2. Connect if needed
    if _db_conn is None or _db_conn.closed:
        if not DB_URL:
            raise ValueError("NEON_DB_URL not set")
        try:
            # Add keepalives to prevent idle timeouts
            _db_conn = psycopg2.connect(
                DB_URL, 
                keepalives=1, 
                keepalives_idle=30, 
                keepalives_interval=10, 
                keepalives_count=5
            )
        except Exception as e:
            print(f"Postgres Connection Error: {e}")
            raise
    return _db_conn

def get_pinecone_client():
    global _pinecone_client
    if _pinecone_client is None:
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not set")
        _pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    return _pinecone_client

def init_db():
    conn = get_db_connection()
    # Ensure tables exist (Basic check)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY, 
                name TEXT, 
                author TEXT, 
                language TEXT
            );
            CREATE TABLE IF NOT EXISTS hadiths (
                id TEXT PRIMARY KEY, -- Composite book_id_hadith_no used as ID text? Or Serial? 
                                     -- Schema check earlier showed ID as INTEGER.
                                     -- And constraints on (book_id, hadith_no).
                                     -- Let's respect existing schema if possible, or adapt.
                                     -- Existing schema had ID as INTEGER (SERIAL probably).
                                     -- We will rely on existing schema.
                book_id TEXT REFERENCES books(id),
                hadith_no INTEGER,
                hadith_text TEXT,
                UNIQUE(book_id, hadith_no)
            );
        """)
    conn.commit()
