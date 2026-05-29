# Phase 3 Coding Agent Prompt

Implement Phase 3 only: remove duplicate document relationship state safely.

Tasks:

1. Find all reads/writes for:
   - `document_sections.block_ids`
   - `document_sections.child_section_ids`
   - `document_blocks.asset_ids`
   - `document_source_chunks.asset_ids`

2. Add repository helpers that derive:
   - child sections from `parent_section_id`
   - blocks from `section_id`
   - assets from `block_id`
   - assets from `chunk_id`

3. Update API response builders to preserve response shape if frontend expects arrays.

4. Stop ingestion from writing these duplicate reverse arrays.

5. Add tests proving response shape is stable.

6. Only after the above is stable, add a migration to drop the duplicate columns.

Important:

Do not drop `document_source_chunks.block_ids` unless you add a join table. Chunk-to-block may be many-to-many.
