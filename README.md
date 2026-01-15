# Noor-AI v1.0

> **A scholarly, evidence-bound Islamic reasoning system.**

**Noor-AI** is a **Shia** scholarly Islamic reasoning system designed to answer questions using **only** authoritative text from ingested hadith books (specifically *Kitab Sulaym ibn Qays*, the first Shia Hadith book). It utilizes a Retrieval-Augmented Generation (RAG) architecture to ensure strict citation enforcement and zero hallucination.

It is built for students, researchers, and developers who need accurate, evidence-bound answers derived directly from source texts.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Postgres Database** (e.g., Neon.tech) for authoritative text storage.
- **Pinecone API Key** for vector search.
- **Google Gemini API Key** for embeddings and reasoning.

### Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-org/noor-ai.git
    cd noor-ai
    ```

2. **Set up Environment Variables**:
    Create a `.env` file in the root directory:

    ```env
    NEON_DB_URL=postgresql://user:password@host/dbname?sslmode=require
    PINECONE_API_KEY=your_pinecone_key
    GEMINI_API_KEY1=your_gemini_key
    ```

3. **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

---

## 📖 Usage Guide

### 1. Ingest Data (ETL)

Before the system can answer questions, raw text must be processed into vector embeddings. Noor-AI handles special sections like **Prefaces** and **Introductions** distinctly.

```bash
# Ingest the default dataset (Kitab Sulaym)
python main.py ingest --file hadith_cleaned.json
```

*This process splits the text, generates `gemini-embedding-001` vectors, and stores them in Pinecone.*

### 2. Interactive Chat

Launch the scholarly reasoning engine.

```bash
python main.py chat
```

**Example Interaction:**

```
👋 Welcome to Noor-AI
Type 'exit' to stop.

You: What did the Prophet say about Imam Ali at Ghadir?

------------------------------------------------------------
Intent : scholarly_reasoning
Response : The Holy Prophet (SAW) said: "Whose ever Mawla I am, Ali also is his Mawla". [HADITH_NO:6]
Confidence : high
why this answer : Derived from 1 authoritative traditions. Strictly evidence-bound.
Model Used : gemini-2.5-flash
------------------------------------------------------------
```

---

## Test Prompts

> Tell me about Imam Ali talking to the sun as per what the Holy Prophet told him and how did the sun reply to Imam Ali. Also quote the entire incident and give hadith no and page number from the book.

> What did Imam Jafar Sadiq(as) said about this book?

> What is the story of the black stone?

> who killed Lady Fatimah(sa) and how?

## 🛡️ Key Features

- **Strict Citation Enforcement**: Every claim in the response is backed by a specific source ID (e.g., `[HADITH_NO:12]`). If a claim cannot be cited, it is not generated.
- **Zero Hallucination Architecture**: The model is constrained to answer *only* using the retrieved context. It explicitly says "I do not know" if the information is missing from the source.
- **Preface & Meta-Content Support**: capable of retrieving and reasoning about non-hadith content such as book prefaces (e.g., Imam Jafar Sadiq's (as) commentary on the book).
- **Resilient Connectivity**: Built-in auto-reconnection logic handles long-running sessions, preventing SSL/TCP timeouts commonly found in cloud databases.

---

## 🔧 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **SSL Connection Closed** | Long idle times in cloud DBs. | The system now includes auto-reconnect logic. effective in v1.1. |
| **"I do not know"** | Context missing or query mismatch. | Ensure the topic exists in *Kitab Sulaym*. Rephrase query. |
| **Ingestion Errors** | API Quota limits. | Check your Gemini/Pinecone quotas. The script handles some retries. |

---

## 📜 License

[MIT License](LICENSE)
