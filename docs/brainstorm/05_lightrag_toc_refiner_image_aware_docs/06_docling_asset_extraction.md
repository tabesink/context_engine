# 06 — Docling Asset Extraction

## Goal

Images, figures, and table snapshots detected by Docling must be saved and returned to users when associated chunks are retrieved.

## Asset Principle

Store images once. Pass references everywhere else.

```text
Good:
chunk.asset_ids = ["asset_044"]

Bad:
chunk.metadata.image_base64 = "..."
```

## File Layout

```text
.data/
  documents/
    {document_id}/
      original/
        source.pdf
      manifest/
        document_structure.json
      assets/
        asset_001.png
        asset_001_thumb.png
        asset_002.png
        asset_002_thumb.png
```

## Asset Extraction Steps

```text
1. Docling detects figure/image/table region.
2. Extract or render image to PNG/JPEG.
3. Compute content hash.
4. Save full-resolution asset.
5. Generate thumbnail.
6. Create DocumentAsset metadata.
7. Link asset to block/page/section.
8. Later link asset to chunk.
```

## Link Rules

Use simple deterministic rules first.

```text
1. If image has a caption block, link image to caption block.
2. If image block exists, link image to that block.
3. If no caption exists, link to nearest text block on same page.
4. Link to containing section by page range.
5. During chunking, chunk inherits asset_ids from included blocks.
```

## Caption Handling

Prefer human-authored captions.

```text
Figure 4. Hydraulic circuit diagram
Table 2. Torque specifications
```

If no caption exists, leave `caption = null` in v1.

Optional v2:

```text
run vision captioning only for uncaptained images
store generated_description
inject generated_description into chunk text if useful
```

## No Image Embeddings in v1

Do not add:

```text
CLIP embeddings
image vector search
separate image retriever
vision model processing for every asset
MinIO/S3 unless deployment requires it
```

The v1 image retrieval rule is enough:

```text
retrieved chunk -> asset_ids -> return image URLs/thumbnails
```

## Asset Deduplication

Use content hash.

```python
def compute_asset_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

If the same asset appears twice, store one file but allow multiple metadata links if needed.

## Thumbnail Rule

Generate thumbnails on ingestion.

```text
max width: 512 px
preserve aspect ratio
same file stem + _thumb suffix
```

The query response should return thumbnail URLs by default. The frontend/TUI can open the full asset when requested.
