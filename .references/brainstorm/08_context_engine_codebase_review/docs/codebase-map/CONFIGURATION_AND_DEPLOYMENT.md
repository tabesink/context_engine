# Configuration and Deployment

## Runtime Components

Expected runtime stack:

```text
API container
PostgreSQL container/service
Redis container/service
RQ worker container
status-poller container
migration service
LightRAG domain containers/services
file storage volumes
```

## Startup Flow

Recommended startup flow:

```text
docker compose up
  → PostgreSQL starts
  → Redis starts
  → migration service runs alembic upgrade head
  → API starts after migrations complete
  → worker starts after migrations complete
  → status poller starts after migrations complete
  → API health/readiness becomes available
```

## Environment Variable Categories

### Core App

```text
ENVIRONMENT
APP_NAME
API_HOST
API_PORT
```

### Security

```text
SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES
SEED_ADMIN_EMAIL
SEED_ADMIN_PASSWORD
```

Production guardrails should reject:

- default/weak `SECRET_KEY`
- weak seed admin password
- insecure production values

### CORS

```text
ALLOWED_ORIGINS
```

Production should reject wildcard origins.

Recommended examples:

```text
http://localhost:3000
https://your-frontend.example.com
```

### Database

```text
DATABASE_URL
```

Production should use PostgreSQL, not SQLite.

SQLite should be allowed only for isolated tests.

### Redis / Queue

```text
REDIS_URL
RQ_QUEUE_NAME
```

### Storage

```text
DATA_DIR
UPLOADS_DIR
ASSETS_DIR
```

Keep all storage paths centralized.

### LightRAG Runtime

```text
LIGHTRAG_ENABLED
LIGHTRAG_BASE_URL
LIGHTRAG_DOMAIN
```

Recommended product posture:

- `LIGHTRAG_ENABLED=true` for normal runtime
- no local semantic fallback
- retrieval fails clearly if LightRAG/domain is unavailable

### LightRAG Domain Deployment

```text
LIGHTRAG_DEPLOY_ENABLED
LIGHTRAG_IMAGE
LIGHTRAG_DOMAIN_ROOT
LIGHTRAG_PORT_BASE
```

Important production rule:

Do not use `:latest` image tags in staging or production.

### Provider/API Keys

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
EMBEDDING_MODEL
```

For OpenAI-compatible Bedrock endpoints, prefer provider profile settings rather than scattering provider-specific logic across services.

## Production Guardrails

Recommended validations:

```text
Reject weak/default SECRET_KEY in production
Reject wildcard CORS in production
Reject SQLite in production
Reject weak seed admin password in production
Reject LIGHTRAG_IMAGE=:latest in production
Require intentional LIGHTRAG_DEPLOY_ENABLED posture
Require explicit external origins
```

## Docker Compose Notes

Good Compose design should include:

- isolated services
- named volumes
- explicit health checks
- migration service
- API depends on migrations
- worker depends on migrations
- Redis and Postgres health checks
- clear port mappings
- persistent volumes for database and file data

## Deployment Risks

### Risk: Image drift

Using `latest` LightRAG image can silently change behavior.

Mitigation:

```text
Pin image tags in staging/production.
Document upgrade steps.
Run retrieval smoke tests after bumping LightRAG version.
```

### Risk: Mixed frontend/backend URL configuration

If frontend is HTTPS but backend URL is HTTP, browsers will block requests.

Mitigation:

```text
Use HTTPS backend URL in frontend config.
Configure CORS with exact frontend origin.
```

### Risk: Migrations not applied before API start

Mitigation:

```text
Keep migration service or deploy pre-command.
Block API start until migrations succeed.
```

### Risk: Secrets checked into `.env.example`

Mitigation:

```text
Keep `.env.example` placeholder-only.
Never commit real API keys.
Use deployment secret manager.
```

## Recommended Deployment Checklist

Before production:

- [ ] PostgreSQL database configured
- [ ] Redis configured
- [ ] migrations run successfully
- [ ] admin seed user configured with strong password
- [ ] `SECRET_KEY` strong and unique
- [ ] CORS origins exact, not wildcard
- [ ] LightRAG image pinned
- [ ] LightRAG domain storage backed by persistent volume
- [ ] uploaded file storage backed by persistent volume
- [ ] health/readiness endpoints pass
- [ ] worker is running
- [ ] status poller is running
- [ ] `/retrieve` smoke test passes
- [ ] admin upload smoke test passes
- [ ] domain lifecycle smoke test passes, if deployment management is enabled
