-- Temporary local triage only.
-- This creates the plain `lightrag` role to match a currently broken generated domain.env.
-- The clean Option B implementation should instead provision per-domain roles/databases,
-- for example: lightrag_fatigue / lightrag_fatigue.

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lightrag') THEN
    CREATE ROLE lightrag LOGIN PASSWORD 'lightrag';
  ELSE
    ALTER ROLE lightrag WITH LOGIN PASSWORD 'lightrag';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE context_engine TO lightrag;
GRANT USAGE, CREATE ON SCHEMA public TO lightrag;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lightrag;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO lightrag;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lightrag;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO lightrag;
