# 08 — Retrieval With Images

## Query Flow

```text
User query
  -> Context Engine receives query
  -> Context Engine calls LightRAG domain query
  -> LightRAG returns answer + source chunk metadata
  -> Context Engine loads local chunk records
  -> Context Engine resolves section/page/source info
  -> Context Engine resolves asset_ids
  -> Context Engine returns answer + sources + images
```

## Response Shape

```json
{
  "answer": "The controller wiring diagram shows the emergency stop circuit and sensor harness connections.",
  "sources": [
    {
      "document_id": "doc_123",
      "document_name": "Service Manual.pdf",
      "section_id": "sec_007",
      "section_title": "Electrical Wiring",
      "page_start": 18,
      "page_end": 20,
      "chunk_id": "chunk_007_002"
    }
  ],
  "assets": [
    {
      "asset_id": "asset_044",
      "asset_type": "figure",
      "caption": "Figure 6. Main controller wiring diagram",
      "page_number": 19,
      "thumbnail_url": "/api/documents/doc_123/assets/asset_044/thumbnail",
      "url": "/api/documents/doc_123/assets/asset_044"
    }
  ]
}
```

## Asset Resolver

```python
def resolve_assets_for_retrieved_chunks(
    chunks: list[DocumentChunk],
    max_assets: int = 5,
) -> list[DocumentAsset]:
    asset_ids: list[str] = []
    for chunk in chunks:
        for asset_id in chunk.asset_ids:
            if asset_id not in asset_ids:
                asset_ids.append(asset_id)
    return asset_repo.get_many(asset_ids[:max_assets])
```

## Ranking Assets

When there are too many assets, rank simply:

```text
1. asset directly linked to retrieved chunk
2. asset linked to a block inside retrieved chunk
3. asset caption overlaps user query
4. asset is on same page as retrieved chunk
5. asset is in same section
6. asset is near retrieved page range
```

## Defaults

```text
include_assets: true
include_thumbnails: true
max_assets: 5
return_full_image_bytes: false
```

Return URLs, not bytes, in JSON responses.

## Frontend/TUI Behavior

In a full frontend:

```text
show answer
show source sections/pages
show image thumbnails inline
allow click to open full image
```

In TUI:

```text
show asset metadata
show thumbnail URL / file path
optionally open image externally if supported
```

## No Multimodal Retrieval in v1

Do not search directly over images in v1.

Retrieval path is:

```text
text query -> text chunk -> linked image
```

This is lightweight and predictable.
