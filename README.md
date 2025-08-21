🧠 Local RAG System (Retrieval-Augmented Generation)
====================================================

This project is a **fully local Retrieval-Augmented Generation (RAG) pipeline** for document parsing, semantic search, and question answering --- designed to work **without relying on cloud services** like AWS or OpenAI.

It was developed during my internship at **eResult** as a proof-of-concept for a **secure, transparent, and modular RAG workflow**.

* * * * *

🚀 Key Features
---------------

-   ✅ **Local vector storage** with ChromaDB

-   ✅ **Embeddings** via SentenceTransformers (all-MiniLM-L6-v2)

-   ✅ **PDF-to-JSON parsing** with custom rule-based logic (no LLMs needed)

-   ✅ **Optional LLM inference** using Together.ai + Mixtral

-   ✅ **Deterministic & transparent processing** (no black-box steps)

* * * * *

⚙️ Setup Instructions
---------------------

### 1\. Clone & Install Dependencies

```
git clone https://github.com/YourUsername/local-rag-poc.git
cd Local-RAG-System
pip install -r requirements.txt
```

### 2\. Configure Paths & Keys

-   Update your **data directory** in `src/config.py`:

    `DATA_DIR = r"your/data/directory"`

-   Create a `.env` file in the project root (never commit this!):

    `TOGETHER_API_KEY=your-together-api-key`

### 3\. (Optional) Update Model Choice

In `src/config.py`, you can swap the default embedding model.

* * * * *

🧩 Pipeline Overview
--------------------

### 🔹 Preprocessing

-   Page-by-page text extraction

-   Paragraph splitting

-   Title + context inference using sentence embeddings

-   No LLM required

### 🔹 Vector Indexing

-   Converts JSON content into **paragraph-level vectors**

-   Embeds with `all-MiniLM-L6-v2`

-   Stores in **ChromaDB** with metadata

### 🔹 Question Answering

-   Embeds user queries with the same model

-   Retrieves top matches from Chroma

-   (Optional) Uses Together.ai Mixtral for natural language answers

* * * * *

💻 How to Use
-------------

### Step 1: Convert PDF → JSON

```
python src/run_preprocess.py
```

Creates structured `.json` files inside the `data/` folder.

### Step 2: Reindex Documents

```
python src/reindex.py
```

Builds or refreshes the **ChromaDB** index.

### Step 3: Launch Chat Interface

```
streamlit run src/streamlit_app.py
```

Opens a **Streamlit web app** where you can query your documents interactively.

* * * * *

📌 Notes
--------

-   SentenceTransformer indexing works at paragraph-level (no need for aggressive chunking).

-   Chunking into 3--10 pages shows **minimal difference** in retrieval quality.

-   All parsing and indexing steps are **deterministic** and explainable.

* * * * *

🔒 Security Notice
------------------

-   This repository **does not include any API keys or proprietary documents**.

-   Always keep keys in a **`.env` file** (excluded via `.gitignore`).

-   Do not upload embeddings or Chroma indexes generated from private company documents.