# Obsidian RAG Vault

A personal Retrieval-Augmented Generation (RAG) system tailored for **Obsidian Vaults**. It automatically scans, preprocesses, embeds, and indexes Markdown notes into a PostgreSQL vector database, allowing you to ask questions and receive context-aware answers with source citations from your personal knowledge base.

---

## ✨ Key Features

- **Automated Vault Scanning & Syncing**: Recursively scans `.md` files within your designated Obsidian Vault.
- **Incremental Sync & Smart Deduplication**:
  - Uses **MD5 Content Hashing** to detect file modifications.
  - **New files**: Automatically embedded and stored in PostgreSQL.
  - **Modified files**: Re-embedded and updated seamlessly.
  - **Unchanged files**: Fast-tracked and skipped to save API calls and compute.
- **Markdown & Metadata Preprocessing**: Strips YAML frontmatter, cleans syntax formatting, and splits documents into manageable chunks.
- **Vector Database**: Powered by **PostgreSQL** with the `pgvector` extension for efficient cosine similarity search.
- **Flexible LLM & Embedding Integrations**: Connects locally via **LM Studio** or any OpenAI-compatible API endpoint (supports models like `nomic-embed-text`, `qwen-embedding`, `gemma`, etc.).
- **Interactive RAG CLI**: Direct terminal interface for querying your vault with real-time answer generation and source file attribution.

---

## 📁 Project Structure

```text
rag-vault/
├── Rag-app/
│   ├── main.py          # Entry point: Vault synchronization & CLI chat loop
│   ├── database.py      # PostgreSQL & pgvector connection, table schema, CRUD operations
│   ├── chunker.py       # Frontmatter extraction, text cleaning & MD5 hashing
│   ├── embedder.py      # Vector embedding generator via LM Studio / OpenAI API
│   ├── loader.py        # Scans and reads .md files from Obsidian Vault
│   ├── retriever.py     # Top-K vector similarity search (Cosine Distance via pgvector)
│   ├── prompt_builder.py# Formats context blocks and constructs RAG prompt messages
│   ├── ai_model.py      # Interface for LLM completion requests
│   ├── dockerfile       # Dockerfile for Python application environment
│   ├── requirements.txt # Python package dependencies
│   └── .env             # Environment configuration file
├── docker-compose.yml   # Docker Compose config for PostgreSQL + pgvector container
└── README.md            # Project documentation
```

---

## ⚙️ Architecture & RAG Pipeline

```text
[ Obsidian Vault (.md) ]
         │
         ▼
[ Loader & Chunker ] ──(MD5 Check)──► [ Database (Unchanged? Skip) ]
         │
         ▼ (New / Modified)
[ Embedder (LM Studio API) ]
         │
         ▼
[ PostgreSQL + pgvector ]
         │
  [ User Query ]
         │
         ▼
[ Vector Search (Top-K) ] ──► [ Prompt Builder ] ──► [ LLM Generation ] ──► [ Answer + Citations ]
```

---

## 🛠️ Setup & Running

### 1. System Requirements

- **Python**: `3.10` or higher
- **Docker & Docker Compose**: Installed and running
- **LM Studio** (or an OpenAI-compatible API server running locally or remotely)

---

### 2. Environment Configuration (`.env`)

Create a `.env` file in the `Rag-app/` directory (or set environment variables in your environment) based on the template below:

```env
# Database Credentials
DB_HOST=localhost
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=adminpassword
DB_NAME=vector_db_service

# LLM & Embedding Service (LM Studio / OpenAI compatible)
LM_STUDIO_URL=http://127.0.0.1:1234/v1
MODEL=text-embedding-nomic-embed-text-v1.5
LLM_MODEL=gemma

# Path to your local Obsidian Vault
VAULT_PATH=C:/path/to/your/Obsidian/Vault
```

---

### 3. Launch Vector Database Container

Spin up PostgreSQL with `pgvector` pre-configured:

```bash
docker-compose up -d
```

---

### 4. Install Dependencies

Navigate to the `Rag-app` directory and install the required Python libraries:

```bash
cd Rag-app
pip install -r requirements.txt
```

---

### 5. Execute Vault Sync & Start CLI Chat

Run `main.py` to automatically sync your vault and open the interactive terminal assistant:

```bash
python main.py
```

Example usage inside the terminal:

```text
--- SYNC VAULT TO DATABASE ---
Found 42 markdown files in vault.
Statistics: 40 files up to date (skipped), 2 files new or updated.
Completed: processed 2/2 files.

============================================================
🤖 RAG SYSTEM READY! Enter your question (type 'exit' or 'q' to quit).
============================================================

Question: What are my key goals for Q3?

AI is thinking...

AI:
Based on your notes, your key goals for Q3 are...

Sources: Work/Q3_Goals.md, Projects/Roadmap.md
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
