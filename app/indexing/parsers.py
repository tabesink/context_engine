from pathlib import Path
from uuid import UUID

from pypdf import PdfReader

from app.domain.models import Page, ParsedDocument


class DocumentParser:
    def parse(self, *, document_id: UUID, filename: str, path: Path, content_type: str) -> ParsedDocument:
        suffix = path.suffix.lower()
        if suffix == ".pdf" or content_type == "application/pdf":
            return self._parse_pdf(document_id=document_id, filename=filename, path=path)
        if suffix in {".md", ".markdown"}:
            return self._parse_markdown(document_id=document_id, filename=filename, path=path)
        return self._parse_text(document_id=document_id, filename=filename, path=path)

    def _parse_text(self, *, document_id: UUID, filename: str, path: Path) -> ParsedDocument:
        text = path.read_text(encoding="utf-8", errors="ignore")
        page = Page(number=1, text=text, metadata={"kind": "text"})
        return ParsedDocument(document_id=document_id, title=filename, pages=[page], full_text=text)

    def _parse_markdown(self, *, document_id: UUID, filename: str, path: Path) -> ParsedDocument:
        text = path.read_text(encoding="utf-8", errors="ignore")
        pages: list[Page] = []
        current: list[str] = []
        current_title = filename
        page_number = 1
        for line in text.splitlines():
            if line.startswith("#") and current:
                pages.append(
                    Page(
                        number=page_number,
                        text="\n".join(current).strip(),
                        metadata={"section_title": current_title},
                    )
                )
                page_number += 1
                current = []
            if line.startswith("#"):
                current_title = line.lstrip("#").strip() or filename
            current.append(line)
        if current:
            pages.append(
                Page(
                    number=page_number,
                    text="\n".join(current).strip(),
                    metadata={"section_title": current_title},
                )
            )
        return ParsedDocument(document_id=document_id, title=filename, pages=pages, full_text=text)

    def _parse_pdf(self, *, document_id: UUID, filename: str, path: Path) -> ParsedDocument:
        reader = PdfReader(str(path))
        pages = [
            Page(number=index + 1, text=page.extract_text() or "", metadata={"kind": "pdf"})
            for index, page in enumerate(reader.pages)
        ]
        full_text = "\n\n".join(page.text for page in pages)
        return ParsedDocument(document_id=document_id, title=filename, pages=pages, full_text=full_text)

