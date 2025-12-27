-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS embeddings;


DROP TABLE IF EXISTS heritage_links CASCADE;
DROP TABLE IF EXISTS people_links CASCADE;
DROP TABLE IF EXISTS festival_links CASCADE;

DROP TABLE IF EXISTS heritages CASCADE;
DROP TABLE IF EXISTS people CASCADE;
DROP TABLE IF EXISTS festivals CASCADE;


-- =========================
-- Documents table
-- =========================
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    file_hash TEXT UNIQUE,
    filename TEXT NOT NULL,
    source_path TEXT,
    status TEXT NOT NULL DEFAULT 'INITIALIZED',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =========================
-- Embeddings table
-- =========================

CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,               -- chunk id
    document_id UUID NOT NULL,         -- parent document
    text TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    chunk_index INT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE
);


CREATE TABLE heritages (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    type TEXT,
    year INT,
    description TEXT,
    image TEXT,
    category TEXT,
    document_id UUID REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT now()
);


CREATE TABLE people (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    birth_year INT,
    death_year INT,
    role TEXT NOT NULL,
    associated_place TEXT,
    description TEXT,
    document_id UUID REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT now()
);

DROP TABLE IF EXISTS festivals;

CREATE TABLE festivals (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    time TEXT,
    type TEXT,
    description TEXT,
    document_id UUID REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE heritage_links (
    id UUID PRIMARY KEY,
    heritage_id UUID NOT NULL REFERENCES heritages(id),
    related_heritage_id UUID REFERENCES heritages(id),
    person_id UUID REFERENCES people(id),
    festival_id UUID REFERENCES festivals(id),
    relation TEXT NOT NULL,
    document_id UUID REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT now(),

    CHECK (
        related_heritage_id IS NOT NULL
        OR person_id IS NOT NULL
        OR festival_id IS NOT NULL
    )
);

CREATE TABLE people_links (
    id UUID PRIMARY KEY,
    person_id UUID NOT NULL REFERENCES people(id),
    related_person_id UUID REFERENCES people(id),
    heritage_id UUID REFERENCES heritages(id),
    festival_id UUID REFERENCES festivals(id),
    relation TEXT NOT NULL,
    document_id UUID REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT now(),

    CHECK (
        related_person_id IS NOT NULL
        OR heritage_id IS NOT NULL
        OR festival_id IS NOT NULL
    )
);

CREATE TABLE festival_links (
    id UUID PRIMARY KEY,
    festival_id UUID NOT NULL REFERENCES festivals(id),
    heritage_id UUID REFERENCES heritages(id),
    person_id UUID REFERENCES people(id),
    relation TEXT NOT NULL,
    document_id UUID REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT now(),

    CHECK (
        heritage_id IS NOT NULL
        OR person_id IS NOT NULL
    )
);

CREATE TABLE extraction_logs (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE    status TEXT,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =========================
-- Task logs
-- =========================
DROP TABLE IF EXISTS task_logs;

CREATE TABLE task_logs (
    task_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id UUID NOT NULL,
    task_state TEXT NOT NULL DEFAULT 'INITIALIZED',
    task_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_task_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE
);

-- =========================
-- Vector index (ANN)
-- =========================
-- HNSW = approximate nearest neighbor (FAST)
CREATE INDEX IF NOT EXISTS embeddings_hnsw_idx
ON embeddings
USING hnsw (embedding vector_cosine_ops);

CREATE UNIQUE INDEX uniq_heritage_name_doc
ON heritages (LOWER(name), document_id);

CREATE UNIQUE INDEX uniq_people_name_doc
ON people (LOWER(name), document_id);

CREATE UNIQUE INDEX uniq_festival_name_doc
ON festivals (LOWER(name), document_id);

CREATE INDEX idx_heritages_document ON heritages(document_id);
CREATE INDEX idx_people_document ON people(document_id);
CREATE INDEX idx_festivals_document ON festivals(document_id);

CREATE INDEX idx_heritage_links_heritage ON heritage_links(heritage_id);
CREATE INDEX idx_people_links_person ON people_links(person_id);
CREATE INDEX idx_festival_links_festival ON festival_links(festival_id);
