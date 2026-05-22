# 12 — Testing Strategy

## Unit Tests

### Structure Quality

Test:

```text
good Docling structure does not trigger refiner
flat structure triggers refiner
invalid page ranges trigger refiner
TOC detected triggers refiner
```

### TOC Refiner

Use fixtures with mocked LLM responses.

Test:

```text
TOC with printed page numbers
TOC without page numbers
PDF physical page offset
invalid LLM JSON
out-of-bounds page numbers
low validation accuracy rejection
bounded max_llm_calls
```

### Asset Extraction

Test:

```text
assets saved to expected path
thumbnails created
content hash calculated
duplicate assets detected
assets linked to blocks
assets inherited by chunks
```

### Chunk Builder

Test:

```text
chunks stay inside section boundaries when possible
chunk inherits asset_ids from blocks
chunk metadata includes page range
large sections split correctly
```

### Retrieval Asset Resolver

Test:

```text
retrieved chunks resolve assets
max_assets limit enforced
duplicate assets removed
caption-overlap ranking works
```

## Integration Tests

### Ingestion Without TOC Refiner

```text
upload document
Docling parse succeeds
structure score good
TOC refiner skipped
chunks sent to LightRAG
assets saved
```

### Ingestion With TOC Refiner

```text
upload messy manual
Docling parse succeeds but weak structure
TOC refiner runs
refined sections accepted
chunks sent to LightRAG with asset_ids
```

### Query With Images

```text
query mentions diagram
LightRAG returns relevant chunk
Context Engine resolves asset_ids
response includes thumbnail and full asset URL
```

## Golden Fixture Types

Keep a small test corpus:

```text
1. Clean Markdown document
2. PDF with reliable headings
3. PDF with TOC and page offset
4. PDF with weak headings but good TOC
5. PDF with figures and captions
6. PDF with tables
7. PDF with images but no captions
```

## Non-goals for v1 Tests

Do not test:

```text
CLIP embeddings
image semantic search
full multimodal answer generation
S3/MinIO storage
browser rendering
```
