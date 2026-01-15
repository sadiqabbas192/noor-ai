from typing import List, Dict
from .database import get_db_connection, get_pinecone_client
from services.embedding import generate_query_embedding
from psycopg2.extras import RealDictCursor
import core.config

def print_debug(*args):
    if core.config.DEBUG_MODE: print(*args)

def retrieve_context(query: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieves Hadiths from Pinecone and PostgreSQL.
    Adapts the User's retrieval pattern to Noor-AI domain.
    """
    namespace = "noor_ai:kitab_sulaym:english:hadith"
    print_debug(f"\n🔎 Querying Namespace {namespace}: '{query}'")
    
    query_embedding = generate_query_embedding(query)
    if not query_embedding:
        return []
    
    pc = get_pinecone_client()
    index_name = "kitab-sulaym" # Configured constant in original
    index = pc.Index(index_name)
    
    try:
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace="noor_ai:kitab_sulaym:english:hadith",
            include_metadata=True
        )
    except Exception as e:
        print(f"Pinecone Query Error: {e}")
        return []

    # 3. Process Results & Apply Keyword Boosting
    # User feedback: "explain preface" misses ID 0.1/0.2.
    # Boosting Strategy: If query mentions keywords, force inject IDs if not present.
    
    manual_ids = []
    q_lower = query.lower()
    
    if "preface" in q_lower:
        manual_ids.extend([("kitab_sulaym", 0.1), ("kitab_sulaym", 0.2)])
        print_debug("🚀 Boosting Preface (0.1, 0.2)")
        
    if "introduction" in q_lower or "intro" in q_lower:
        manual_ids.extend([("kitab_sulaym", 0.3)])
        print_debug("🚀 Boosting Introduction (0.3)")

    # Collect keys from Vector Search
    keys = []
    for match in results['matches']:
        md = match.get('metadata', {})
        bid = md.get('book_id')
        hno = md.get('hadith_no')
        if bid and hno is not None:
            # Keep as float or original type
            keys.append((bid, hno))
            
    # Prepend boosted IDs to ensure they are fetched
    final_keys = manual_ids + keys
    
    if not final_keys:
         print_debug("   ⚠️ No matches found in namespace:", namespace)
         return []
         
    # Deduplicate while preserving order (Boosted first)
    seen = set()
    unique_keys = []
    for k in final_keys:
        if k not in seen:
            seen.add(k)
            unique_keys.append(k)
            
    # 4. Fetch Text from Postgres
    conn = get_db_connection()

    # Construct WHERE clause for (book_id, hadith_no) pairs
    # WHERE (book_id = 'x' AND hadith_no = 1) OR ...
    where_clauses = [f"(book_id = %s AND hadith_no = %s)" for _ in unique_keys]
    query_sql = f"""
        SELECT book_id, hadith_no, hadith_text 
        FROM hadiths 
        WHERE {" OR ".join(where_clauses)}
    """
    
    # Flat list of params
    params = []
    for k in unique_keys:
        params.extend(k)
        
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query_sql, tuple(params))
        rows = cur.fetchall()
        
    # Map DB results
    # key: (book_id, hadith_no) -> text
    # Force float to match Python-side keys
    db_map = {}
    for row in rows:
        try:
             # Handle Decimal -> float
             h_val = float(row['hadith_no'])
             db_map[(row['book_id'], h_val)] = row['hadith_text']
        except:
             # Fallback for strings
             db_map[(row['book_id'], row['hadith_no'])] = row['hadith_text']
    
    context_items = []
    
    # We iterate over unique_keys to preserve rank order (Boosted -> High Score Vector)
    for key in unique_keys:
        if key in db_map:
            content = db_map[key]
            # Format: [HADITH_NO:X] Content...
            # Use strict casting for display if needed
            formatted_content = f"[HADITH_NO:{key[1]}] {content}"
            
            # Find the score for this key if it came from Pinecone results
            score = None
            for match in results['matches']:
                md = match.get('metadata', {})
                bid = md.get('book_id')
                hno = md.get('hadith_no')
                if (bid, hno) == key:
                    score = match['score']
                    break
            
            context_items.append({
                "content": formatted_content,
                "score": score, # Will be None for manually injected items
                "hadith_no": key[1],
                "book_id": key[0]
            })
            score_val = f"{score:.4f}" if score is not None else "BOOSTED"
            print_debug(f"   [{hno}] Score: {score_val} | Content: {content[:50]}...")

    return context_items
