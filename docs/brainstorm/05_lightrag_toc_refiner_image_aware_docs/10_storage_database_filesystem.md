# 10 — Storage, Database, and Filesystem

## Storage Rule

Use Postgres for metadata. Use filesystem for files.

Do not store image bytes in Postgres.

## Filesystem Layout

```text
.data/
  documents/
    {document_id}/
      original/
        source.pdf
      manifest/
        document_structure.json
        docling_raw.json
        toc_refinement_report.json
      assets/
        asset_001.png
        asset_001_thumb.png
        asset_002.png
        asset_002_thumb.png
```

## Tables

### documents

```text
id
filename
storage_path
domain_id
status
created_by
created_at
updated_at
```

### document_sections

```text
id
document_id
parent_section_id
title
level
page_start
page_end
source
confidence
```

### document_blocks

```text
id
document_id
section_id
type
text
page_start
page_end
bbox_json
reading_order
```

### document_chunks

```text
id
document_id
section_id
text
page_start
page_end
lightrag_status
lightrag_external_id
metadata_json
```

### document_assets

```text
id
document_id
section_id
block_id
chunk_id
asset_type
storage_path
thumbnail_path
mime_type
content_hash
page_number
caption
nearby_text
bbox_json
generated_description
ocr_text
```

### ingestion_jobs

```text
id
document_id
domain_id
status
stage
error_message
started_at
completed_at
metadata_json
```

### toc_refinement_reports

```text
id
document_id
enabled
accepted
reason
validation_accuracy
logical_to_physical_offset
llm_call_count
warnings_json
created_at
```

## JSON Manifest

Even with DB tables, save a manifest for debugging/reproducibility.

```text
.data/documents/{document_id}/manifest/document_structure.json
```

This makes it easy to inspect ingestion output outside the database.

## Deletion Policy

Soft delete first:

```text
documents.status = deleted
```

Physical deletion should require explicit admin action:

```text
--delete-permanently
```

Permanent delete removes:

```text
original file
manifest files
asset files
DB metadata
LightRAG domain document data if supported
```
