CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE knowledge_chunks (
  tenant_id text NOT NULL,
  chunk_id text NOT NULL,
  source_id text NOT NULL,
  content text NOT NULL,
  embedding vector(512) NOT NULL,
  PRIMARY KEY (tenant_id, chunk_id)
);
