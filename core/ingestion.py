import json
import os
import uuid
import sys
from typing import Dict, List, Any

# Adjust path import if needed, assuming this is running from root via main.py
from .database import get_db_connection, get_pinecone_client, init_db
from services.embedding import generate_embedding

# Use UUID for internal tracking if desired, but we stick to (book_id, hadith_no) as canonical ID
# We will use UUID for strict vector ID if we want randomness, but deterministic is better for Noor-AI.
# Reference implementation uses UUIDv5 for determinism.

def upsert_book(conn, book_id, book_name, author_name, language):
    """Upserts book information."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO books (id, name, author, language)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE 
            SET name = EXCLUDED.name,
                author = EXCLUDED.author,
                language = EXCLUDED.language
        """, (book_id, book_name, author_name, language))
    conn.commit()

def upsert_hadith(conn, book_id, hadith_no, hadith_text):
    """Upserts a single hadith."""
    with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO hadiths (book_id, hadith_no, hadith_text)
            VALUES (%s, %s, %s)
            ON CONFLICT (book_id, hadith_no) DO UPDATE 
            SET hadith_text = EXCLUDED.hadith_text
        """, (book_id, hadith_no, hadith_text))
    conn.commit()

def ingest_brand(file_path: str): # Renamed to generic ingest function, keeping param name relevant
    print(f"\n🧠 Ingesting Data from: {file_path}")
    
    # Initialize Clients
    init_db() 
    conn = get_db_connection()
    pc = get_pinecone_client()
    index_name = "kitab-sulaym" 
    
    # Create Index if not exists
    if index_name not in pc.list_indexes().names():
        from pinecone import ServerlessSpec
        print(f"Creating index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    index = pc.Index(index_name)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        return

    # Allow single object or list
    books = [data] if isinstance(data, dict) else data

    total_chunks = 0
    
    for book in books:
        # 1. Process Book Info
        info = book.get('book_information', {})
        book_id = info.get('book_id')
        language = info.get('language', 'english') # Default english
        
        if not book_id:
            print("⚠️ Skipping book with missing book_id")
            continue

        print(f"📘 Processing Book: {info.get('book_name')} ({book_id})")
        try:
            upsert_book(
                conn,
                book_id=book_id,
                book_name=info.get('book_name'),
                author_name=info.get('author_name'),
                language=language
            )
        except Exception as e:
             print(f"❌ Failed to upsert book info: {e}")
             continue

        # 2. Process Hadiths
        hadiths = book.get('hadiths', [])
        
        # 2.1 Process Special Sections (Preface & Introduction)
        # 2.1 Process Special Sections
        # Strategy: Use Decimal-like IDs for sorting
        # 0.1 = Preface Text
        # 0.2 = Preface Hadith
        # 0.3 = Introduction
        
        preface = book.get('preface', {})
        preface_text_content = preface.get('preface_text')
        preface_hadith_content = preface.get('preface_hadith')
        introduction_content = book.get('introduction').strip() if book.get('introduction') else None
        
        special_sections = []
        if preface_text_content:
             print(f"   -> Found Preface Text (Assigning ID: 0.1)")
             special_sections.append({"hadith_no": 0.1, "hadith_text": preface_text_content})

        if preface_hadith_content:
            print(f"   -> Found Preface Hadith (Assigning ID: 0.2)")
            special_sections.append({"hadith_no": 0.2, "hadith_text": preface_hadith_content})

        if introduction_content:
             print(f"   -> Found Introduction (Assigning ID: 0.3)")
             special_sections.append({"hadith_no": 0.3, "hadith_text": introduction_content})
             
        # Combine special sections with regular hadiths
        all_content_items = special_sections + hadiths
        
        vectors_to_upsert = []
        
        # Namespace format: noor_ai:{book_id}:{language}:hadith
        namespace = f"noor_ai:{book_id}:{language}:hadith"
        
        print(f"   -> Target Namespace: {namespace}")
        
        count = 0
        
        for item in all_content_items:
            h_no = item.get('hadith_no')
            text = item.get('hadith_text')

            if h_no is None or not text: # Check for None explicitly for ID 0
                continue
            
            # Deterministic ID for Vector
            vector_id = f"{book_id}_{h_no}"

            try:
                # Postgres Upsert
                upsert_hadith(conn, book_id, h_no, text)

                # Generate Embedding
                embedding = generate_embedding(text)
                
                if not embedding:
                    print(f"⚠️ Skipping hadith {h_no} due to embedding failure")
                    continue
                
                # Prepare Metadata
                metadata = {
                    "book_id": book_id,
                    "hadith_no": h_no,
                    "language": language,
                    "source": f"hadith_no:{h_no}"
                }
                
                vectors_to_upsert.append((vector_id, embedding, metadata))
                count += 1
                total_chunks += 1
                
            except Exception as e:
                print(f"❌ Failed to process hadith {h_no}: {e}")
                continue

        # Bulk Upsert to Pinecone
        if vectors_to_upsert:
            print(f"   -> Upserting {len(vectors_to_upsert)} vectors...")
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                index.upsert(vectors=batch, namespace=namespace)
        
        # Validation Summary for this book
        print(f"   ✅ Processed {count} hadiths.")

    print(f"\n✅ Ingestion Pipeline Completed. Total Chunks: {total_chunks}")
