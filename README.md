
# RAG Ingestion Pipeline

**(Load → Chunk → Embed → Retrieve) + PostgreSQL pgvector + Gemma3:1b**

This project implements a complete Retrieval-Augmented Generation (RAG) pipeline using a custom ingestion workflow, PostgreSQL with **pgvector**, and **Gemma3:1b** served locally through **Ollama**.

## 1. Features

* PDF ingestion (loader)
* Text chunking
* Vector embedding generation
* Storage in PostgreSQL + pgvector
* FastAPI backend to query embeddings + LLM
* Local Gemma3:1b inference via Ollama
* Streaming RAG responses

## 2. How to Run
### **1. Create `.env` file**

Copy the example file and fill in your PostgreSQL credentials:

```
cp .env.example.txt .env
```

Edit values as needed.

---

### **2. Install dependencies**

If using `pip`:

```
pip install -r requirements.txt
```

If using Poetry:

```
poetry add <dependency-name>
```

(Install each dependency listed in `requirements.txt`.)

---

### **3. Prepare your PDF files**

Place your documents inside:

```
data/raw/
```

They will be processed during ingestion.

---

### **4. Start PostgreSQL + pgvector**

This project provides a Docker Compose setup.

```
docker compose up
```

The `init.sql` script will:

* Create the database
* Enable the pgvector extension
* Create the `embeddings` table for storing vectors

---

### **5. Run the ingestion pipeline**

Generate embeddings from your PDF files:

```
poetry run python src/ingestion/ingestion.py
```

---

### **6. Host Gemma3:1b locally (Ollama)**

Install Ollama: [https://ollama.com/](https://ollama.com/)

Commands:

```
ollama pull gemma3:1b
ollama run gemma3:1b
ollama ps          # verify running model
```

---

### **7. Start the FastAPI server**

Run the RAG backend API:

```
poetry run uvicorn src.main:app --reload
```

---

### **8. Ask a question (RAG Query)**

Example request using cURL:

```
curl --no-buffer -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"What is RAG"}' \
  http://localhost:8000/rag/stream
```
