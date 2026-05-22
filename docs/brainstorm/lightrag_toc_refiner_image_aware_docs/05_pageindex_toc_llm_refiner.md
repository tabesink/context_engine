# 05 — PageIndex-Style LLM TOC Refiner

## Main Point

PageIndex's LLM-based TOC indexing is valuable and should be preserved as a design idea.

It is better than Docling for one specific job:

```text
Recovering a usable section tree and physical page ranges from messy PDF tables of contents.
```

It is not better as the whole parser.

## Why This Matters

Many manuals have a visible TOC, but the PDF's physical page numbers do not match the printed page numbers.

Example:

```text
Printed manual page 1 may be PDF physical page 9.
TOC says "Installation ........ 12".
Actual PDF page may be 20.
```

PageIndex-style logic is useful because it tries to solve:

```text
TOC page detection
TOC extraction
TOC to JSON conversion
logical page number -> physical PDF page mapping
page offset calculation
section start validation
missing page repair
fallback hierarchy generation
```

## Correct Role in This System

Use PageIndex logic as a conditional refinement pass.

```text
Docling parses everything first.
Then structure quality is scored.
If structure is weak or TOC recovery would help, run the TOC refiner.
The refiner returns section improvements.
The final output is still the canonical DocumentStructure.
```

## Do Not Run It for Every Document

LLM TOC indexing costs tokens, time, and introduces variability.

Run it only when:

```text
Docling produced too few sections
Docling found blocks but weak headings
TOC pages are likely present
section page ranges are missing
page ranges are invalid
admin explicitly requests rebuild with LLM TOC refinement
```

Skip it when:

```text
Markdown headings are reliable
Docling produced good section hierarchy
document is small
page ranges are valid
asset/block links are already good
```

## Refiner Interface

```python
class TocRefiner:
    async def refine(
        self,
        pages: list[DocumentPage],
        blocks: list[DocumentBlock],
        initial_sections: list[DocumentSection],
        options: "TocRefinerOptions",
    ) -> "TocRefinementResult":
        ...
```

```python
class TocRefinerOptions(BaseModel):
    enabled: bool = False
    max_llm_calls: int = 8
    model: str
    temperature: float = 0.0
    toc_scan_page_limit: int = 20
    validate_sample_count: int = 12
    min_acceptance_accuracy: float = 0.70
    allow_fallback_tree_generation: bool = True
```

```python
class TocRefinementResult(BaseModel):
    accepted: bool
    reason: str
    toc_pages: list[int] = []
    logical_to_physical_offset: int | None = None
    sections: list[DocumentSection] = []
    validation_accuracy: float | None = None
    warnings: list[str] = []
    llm_call_count: int = 0
```

## Refiner Algorithm

```text
1. Scan first N pages for TOC-like pages.
2. Extract TOC text.
3. Detect whether the TOC contains page numbers.
4. Convert the TOC text into flat section rows:
   - title
   - level or structure number
   - printed page number if present
5. If printed page numbers exist:
   - sample early content pages
   - find where known TOC titles start physically
   - calculate most common page offset
   - assign physical page_start
6. If printed page numbers do not exist:
   - use LLM to locate section starts in tagged page text
7. Validate section starts by checking whether title appears near that page.
8. Repair invalid rows with bounded retry.
9. Calculate page_end from next section start.
10. Return refined sections only if acceptance threshold is met.
```

## Prompt Discipline

All prompts must return JSON only.

Bad:

```text
Tell me what you think about this TOC.
```

Good:

```text
Return only JSON matching this schema:
[
  {
    "title": "string",
    "level": 1,
    "printed_page": 12
  }
]
```

## Acceptance Policy

Do not blindly trust LLM output.

Accept the result only if:

```text
sections are non-empty
section page_start values are in bounds
section hierarchy is valid enough
validation accuracy >= min_acceptance_accuracy
LLM call count <= max_llm_calls
```

If not accepted:

```text
return initial Docling structure
add warning
continue ingestion
```

## Merge Policy

The TOC refiner may override:

```text
section title
section level
section parent/child relationships
section page_start
section page_end
block-to-section mapping
```

The TOC refiner must not override:

```text
asset files
asset ids
image paths
table extraction
figure extraction
Docling block text
original file metadata
LightRAG chunk ids once ingestion is complete
```

## Section Range Calculation

Given sorted section starts:

```python
def assign_section_ends(sections: list[DocumentSection], page_count: int) -> list[DocumentSection]:
    ordered = sorted(sections, key=lambda s: (s.page_start or 10**9, s.level))
    for i, section in enumerate(ordered):
        next_start = None
        for nxt in ordered[i + 1:]:
            if nxt.page_start and nxt.page_start >= (section.page_start or 1):
                next_start = nxt.page_start
                break
        section.page_end = (next_start - 1) if next_start else page_count
    return ordered
```

## Lightweight Implementation Modules

```text
app/document_processing/refinement/
  toc_page_detector.py
  toc_json_extractor.py
  page_offset_resolver.py
  section_start_validator.py
  section_range_assigner.py
  toc_refiner.py
```

## What to Keep from PageIndex

Keep these concepts:

```text
TOC page detection
TOC-to-JSON transformation
page number detection
logical page to physical page offset correction
section start validation
missing page-number repair
fallback hierarchy generation
large-section recursive splitting
accuracy checks before accepting LLM structure
```

## What Not to Copy from PageIndex Wholesale

Avoid:

```text
separate PageIndex workspace
separate document registry
full parallel retrieval API
unbounded prompt chains
LLM-first parsing for every document
PyPDF2 as parser of record
image/table handling through PageIndex
second structure format
```

## Final Rule

PageIndex-style TOC indexing is a useful refinement tool.

It should be implemented as:

```text
small bounded optional service
```

not as:

```text
second document navigation platform
```
