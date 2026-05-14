import hashlib

from app.domain.models import ParsedDocument
from app.indexing.chunking import Chunker
from app.integrations.lightrag_adapter import LightRAGAdapter
from app.storage.tables import SemanticChunkRow


class SemanticIndexBuilder:
    def __init__(self, adapter: LightRAGAdapter | None = None, chunker: Chunker | None = None):
        self.adapter = adapter or LightRAGAdapter()
        self.chunker = chunker or Chunker()

    def build(self, parsed: ParsedDocument) -> list[SemanticChunkRow]:
        rows: list[SemanticChunkRow] = []
        for index, chunk in enumerate(self.chunker.chunks(parsed)):
            stable = hashlib.sha1(
                f"{parsed.document_id}:{index}:{chunk['text']}".encode("utf-8")
            ).hexdigest()
            rows.append(
                SemanticChunkRow(
                    id=stable,
                    document_id=str(parsed.document_id),
                    chunk_index=index,
                    text=chunk["text"],
                    embedding=self.adapter.embed(chunk["text"]),
                    page_start=chunk["page_start"],
                    page_end=chunk["page_end"],
                    meta={"chunk_number": chunk["chunk_number"]},
                )
            )
        return rows

