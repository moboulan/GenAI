# RAG Service

Handles document ingestion, chunking, embedding, and similarity search over pgvector.

## TODO

- `ingest.py`: CLI for converting DOCX/PPTX/PDF to markdown chunks with metadata.
- `embeddings.py`: Interface to local embedding model (text-embedding-3-large, Instructor, etc.).
- `api/main.py`: FastAPI endpoints for `/search`, `/upsert`, and `/healthz`.
