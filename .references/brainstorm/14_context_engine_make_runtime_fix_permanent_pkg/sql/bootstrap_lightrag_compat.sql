-- Legacy compatibility bootstrap.
-- This is NOT the preferred long-term path for new managed domains.
-- Use it only to support old LightRAG containers still using POSTGRES_USER=lightrag.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lightrag') THEN
    CREATE ROLE lightrag LOGIN PASSWORD 'lightrag';
  ELSE
    ALTER ROLE lightrag LOGIN PASSWORD 'lightrag';
  END IF;
END
$$;

SELECT 'CREATE DATABASE lightrag OWNER lightrag'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lightrag')\gexec

GRANT CONNECT ON DATABASE lightrag TO lightrag;

\connect lightrag

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age CASCADE;

GRANT USAGE, CREATE ON SCHEMA public TO lightrag;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lightrag;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO lightrag;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lightrag;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO lightrag;
