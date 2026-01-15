import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import get_db_connection

def migrate():
    print("🔄 Migrating 'hadiths' table schema...")
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check current type (optional, but good for safety)
            # We just force the alter
            print("   -> Altering column 'hadith_no' TYPE to NUMERIC...")
            cur.execute("ALTER TABLE hadiths ALTER COLUMN hadith_no TYPE NUMERIC;")
        conn.commit()
        print("✅ Migration successful: hadith_no is now NUMERIC.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
