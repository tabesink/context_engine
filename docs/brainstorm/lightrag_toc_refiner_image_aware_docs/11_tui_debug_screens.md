# 11 — TUI Debug Screens

The TUI is for backend/API debugging, not a final user-facing app. Keep it monochrome, compact, and information-rich.

## Main Screens

```text
Dashboard
Domains
Documents
Document Detail
Structure Tree
Chunks
Assets
TOC Refinement Report
Query Tester
Retrieved Sources
Graph
Jobs
```

## Document Detail Screen

Show:

```text
document id
filename
domain
status
page count
section count
block count
chunk count
asset count
ingestion stage
LightRAG status
```

## Structure Quality Screen

Show:

```text
heading_count
section_count
asset_count
has_toc
has_page_ranges
unsectioned_block_ratio
invalid_page_range_count
score
should_run_toc_refiner
reasons
```

## TOC Refinement Report Screen

Show:

```text
enabled / disabled
reason it ran
TOC pages detected
LLM call count
accepted / rejected
validation accuracy
logical-to-physical page offset
warnings
```

Example:

```text
+------------------------------------------------------------+
| TOC Refinement                                             |
+--------------------------+---------------------------------+
| Enabled                  | auto                            |
| Ran                      | yes                             |
| Reason                   | Docling section_count < 3       |
| TOC pages                | 3, 4                            |
| Offset                   | +8                              |
| Validation accuracy      | 0.83                            |
| Accepted                 | yes                             |
| LLM calls                | 6 / 8                           |
+--------------------------+---------------------------------+
```

## Assets Screen

Show:

```text
asset_id
type
page
section
block
chunk
caption
thumbnail_path
```

## Query Tester Screen

When testing a query, show:

```text
answer
source chunks
section path
page range
asset ids
thumbnail URLs
LightRAG raw metadata if debug mode enabled
```

## Minimal UI Rule

Do not show everything by default. Use expandable views:

```text
[summary]
[structure]
[chunks]
[assets]
[raw json]
```
