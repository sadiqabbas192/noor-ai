# Noor-AI Developer Documentation

**Noor-AI** is a production-grade Retrieval-Augmented Generation (RAG) system specialized for authoritative religious texts. It employs a **Hybrid Search** strategy (Semantic Vector Search + Deterministic SQL Lookup) to ensure high precision, verbatim accuracy, and citation integrity.

## 📂 Project Structure

The project follows a modular architecture:

```
d:/noor-ai/
├── .env                # Secrets (API Keys, DB Config)
├── main.py             # CLI Entry Point & Argument Parsing
├── requirements.txt    # Python dependencies
├── hadith_cleaned.json # Raw Dataset (Kitab Sulaym)
├── core/               # Application Core Logic
│   ├── config.py       # Global Configuration
│   ├── database.py     # Database Connections
│   ├── ingestion.py    # ETL Pipeline
│   ├── retrieval.py    # Hybrid Retriever
│   ├── reasoning.py    # LLM Orchestrator
│   └── orchestrator.py # Chat Loop
└── services/           # External Services
    └── embedding.py    # Gemini Embedding Service Wrapper
```

## 🏗️ System Architecture

### 1. Ingestion Pipeline (`core/ingestion.py`)

Responsible for transforming raw text into searchable assets.

- **Preprocessing**: Handles special sections like `Preface` (mapped to `ID: 0`) and `Introduction` (mapped to `ID: -1`).
- **Chunking**: Uses `RecursiveCharacterTextSplitter` (350 chars, 50 overlap) for granular retrieval.
- **Embedding**: Generates 768-dimensional vectors using **`models/gemini-embedding-001`**.
- **Storage Strategy**:
  - **Vectors (Pinecone)**: Stores embeddings with metadata (Book ID, Hadith No).
  - **Content (Postgres)**: Stores the full, authoritative text for verbatim reconstruction.

### 2. Retrieval Engine (`core/retrieval.py`)

Executes a two-stage retrieval process:

1. **Semantic Search**: specific `noor_ai:{book_id}:english:hadith` namespace in Pinecone is queried for top-k matches.
2. **Relational Lookup**: The system queries Postgres for the canonical text corresponding to the retrieved IDs.
    - *Crucial Logic*: Explicit handling for `hadith_no: 0` ensures Preface content is strictly retrieved and not discarded as "falsey".

### 3. Database Layer (`database.py`)

- **Connection Management**: Implements a robust connection handler using `psycopg2`.
- **Resilience**: Features **TCP Keepalives** (`keepalives_idle=30`) and **Auto-Reconnection** logic to handle dropped SSL connections typical in serverless Postgres environments (e.g., Neon).

## 🛠️ Development & Verification

### Verification Scripts

We maintain standalone scripts to verify core system stability:

- **`verify_db.py`**: Simulates a dropped connection and asserts that `get_db_connection()` successfully reconnects.
- **`verify_retrieval_bug.py`**: Mocks the Pinecone response to verify that `hadith_no: 0` is correctly processed by the Python retrieval logic.

### Common Development Tasks

**Resetting the World**
If you change embedding models or chunking strategies, you must reset the data:

```bash
python reset_data.py  # Clears Pinecone Index and Postgres Tables
python main.py ingest --file hadith_cleaned.json
```

**Running Tests**

```bash
python -m unittest discover tests/
```

## 🤝 Contribution Guidelines

1. **Strict Typing**: All new functions must have Python type hints.
2. **Zero-Hallucination**: Any changes to `reasoning.py` must maintain the strict "I do not know" fallback behavior.
3. **Efficiency**: Use the `get_db_connection` singleton; do not open new pools per request.
