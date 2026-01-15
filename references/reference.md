# Brand Brain Architecture Guide

This document explains how **Brand Brain** is built, detailing the data pipeline, retrieval mechanisms, embedding strategies, and the knowledge system. It serves as a blueprint for developers building similar Retrieval-Augmented Generation (RAG) applications using Gemini, Pinecone, and Postgres.

## 1. High-Level Architecture

Brand Brain follows a **Hybrid RAG** architecture. It separates **Reasoning** (LLM) from **Memory** (Database + Vector Store) to ensure responses are accurate, on-brand, and hallucination-free.

### Core Components

* **Orchestrator**: Python logic that manages the flow.
* **LLM (Brain)**: `gemini-2.5-flash` (for fast reasoning & tool use).
* **Embeddings**: `gemini-embedding-001` (for semantic understanding).
* **Vector Store (Long-Term Memory)**: `Pinecone` (Serverless).
* **Relational DB (Content Store)**: `Postgres` (Neon).
* **Live Data**: Google Search Tool (via Gemini).

---

## 2. Data Pickup & Ingestion Pipeline

The "Knowledge Pickup" process transforms raw brand data into a format the AI can query.

### A. Data Sources

Data is picked up from two primary sources:

1. **Static Files/JSON**: Brand guidelines, mission statements, and competitor analysis provided manually.
2. **Grounding-Assisted Ingestion (Type B Memory)**: The system proactively searches the web (using Gemini's Google Search Tool) to find "evergreen" brand philosophy on official websites, parses it into JSON, and ingests it automatically.

### B. Semantic Asset Extraction

Raw data is not just dumped; it is categorized. The [extract_assets](file:///d:/brand-brain/notebook-dev/brand_brain_v1.7_exec.py#73-102) function maps input fields to specific **Memory Types**:

* **Asset Type**: `guideline` (rules), `copy` (examples), `website` (facts).
* **Vector Type**: `brand_voice` (style/tone), `strategy` (mission/competitors).

*Why?* This allows targeted retrieval. If the user asks "How should I sound?", we only search the `brand_voice` space, ignoring irrelevant `strategy` documents.

### C. Chunking

Text is split into smaller, manageable pieces to ensure precise retrieval.

* **Method**: `RecursiveCharacterTextSplitter`
* **Size**: 350 characters
* **Overlap**: 50 characters (preserves context between chunks)

---

## 3. How Embeddings Are Created

Embeddings turn text into arrays of numbers (vectors) that represent meaning.

* **Model**: `gemini-embedding-001`
* **Dimensions**: 768
* **Configuration**:
  * **Ingestion**: `task_type='RETRIEVAL_DOCUMENT'` (Optimizes vector for being found).
  * **Querying**: `task_type='RETRIEVAL_QUERY'` (Optimizes vector for finding things).

**The Process:**

1. Text Chunk -> API Call (`embed_content`) -> Vector `[0.12, -0.45, ...]`
2. The system handles failures gracefully (skips invalid chunks) and tracks token counts.

---

## 4. Database & Knowledge System

Brand Brain uses a **Hybrid Database Strategy** to balance speed (Vector) with interpretability (SQL).

### A. Vector Database (Pinecone)

Stores the **searchable meaning**.

* **Index**: `brand-brain-index`
* **Metric**: Cosine Similarity.
* **Namespace Isolation**: `{org_id}:{brand_uuid}:{vector_type}`
  * *Example*: `org_123:brand_abc:brand_voice`
  * *Benefit*: Keeps data for different brands and different context types completely separate. No cross-contamination.

### B. Relational Database (Postgres)

Stores the **actual content** and relationship metadata.

* **`brand_assets`**: The source of truth (full text, source version, confidence score).
* **`brand_chunks`**: The specific text segments corresponding to vectors.
* **`embeddings`**: Metadata linking chunks to models.

### C. The Link

Pinecone stores the `chunk_id` alongside the vector. When a search happens:

1. Pinecone finds the top `chunk_id`s based on similarity.
2. The system uses these IDs to `SELECT` the actual text from Postgres.

* *Why?* Vector stores are expensive and bad at storing large text. SQL is cheap and reliable.

---

## 5. Retrieval & Reasoning (The Knowledge Loop)

When a user asks a question, the system follows a strict "Reasoning Loop":

### Step 1: Safety & Intent Check

Before thinking, the system checks:

* **Intent Classifier**: Is the user asking for something allowed? (e.g., "justify_decision" is okay, "write a poem" might be blocked).
* **Keyword Guard**: Are there forbidden words (e.g., "cheap", "clearance")?
* **Semantic Drift**: Does the query match the Brand's "Centroid" (core voice)? If the query is too off-topic, it is rejected immediately.

### Step 2: Context Retrieval

If safe, it converts the query into a vector and searches the specific namespace (e.g., `brand_voice`).

* **Filtering (v1.6)**: It retrieves candidates and filters out any marked as `deprecated` or low `confidence` in Postgres.

### Step 3: Ephemeral Fetch (Optional)

If the user asks about current events (e.g., "latest trends"), the system performs a **Live Fetch**.

* It asks Gemini to "Google Search this and summarize".
* This data is used *once* for the answer and **never saved** to the database (Type C Memory), preventing database pollution with temporary news.

### Step 4: Final Reasoning

The LLM (`gemini-2.5-flash`) receives a strict prompt:
> "You are [Brand X]. Use this retrieved CONTEXT as your source of truth. Do not invent facts."

It combines:

1. User Query
2. Retrieved Brand Memory (Trusted)
3. Live Data (Contextual)

The result is a formulated, on-brand response.

---

## Guide for Building Similar AI Apps

To replicate this:

1. **Define Your Schema**: Don't just dump text. Categorize it (`policy`, `voice`, `product`).
2. **Hybrid Storage**: Use Pinecone for search, Postgres/SQL for data management. Don't rely on the vector store to hold your content.
3. **Strict Ingestion**: Build a robust "Pickup" pipeline that chunks and embeds consistently.
4. **Guardrails First**: Implement safety checks *before* the expensive LLM call.
5. **Task Types Matter**: Use `RETRIEVAL_DOCUMENT` for storage and `RETRIEVAL_QUERY` for search when using Gemini Embeddings.
