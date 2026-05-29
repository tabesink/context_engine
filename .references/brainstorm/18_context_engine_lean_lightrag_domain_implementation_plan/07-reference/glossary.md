# Glossary

## Create

Configure a LightRAG domain. Does not start container.

## Start

The only runtime boot path. Prepares artifacts, writes env/compose, provisions Postgres, starts Docker, checks health.

## Stop

Stops the domain container.

## Delete

Safe archive/remove from active use. Preserves documents.

## Retrieval defaults

LightRAG runtime tuning values. Not product settings. Written to `domain.env` from backend/deployment config.

## Provider secret

Encrypted API key stored in DB. Decrypted only when needed to write runtime env or test a profile. Never returned to UI.

## Embedding snapshot

Domain-level record of selected embedding provider/model/dimensions/fingerprint. Treat as immutable after ingestion.
