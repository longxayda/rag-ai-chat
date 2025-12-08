-- Enable pgvector extension (safe even if already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop table if you want to recreate it
DROP TABLE IF EXISTS embeddings;

-- Create a single-table RAG schema
CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,               -- chunk id
    text TEXT NOT NULL,                -- chunk text
    embedding VECTOR(384) NOT NULL,    -- pgvector column
    chunk_index INT NOT NULL,          -- chunk index for ordering
    metadata JSONB,                    -- any metadata from your chunker
    created_at TIMESTAMP DEFAULT NOW() -- optional timestamp
);

-- Recommended index for faster similarity search
-- IVF flat index (tunable for performance)
-- Uncomment if you want approximate search:
-- CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Exact search index (recommended for small datasets)
CREATE INDEX IF NOT EXISTS embeddings_cosine_idx
ON embeddings
USING hnsw (embedding vector_cosine_ops);
