from pathlib import Path
from uuid import UUID

from app.document_processing.pipeline import ParsedDocumentFromStructureAdapter, TextDoclingParser


def test_text_docling_parser_builds_structure_that_adapts_to_parsed_document(tmp_path: Path) -> None:
    source = tmp_path / "manual.txt"
    source.write_text("# Safety\nWear eye protection.\n\n# Service\nDisconnect power.", encoding="utf-8")
    parser = TextDoclingParser()

    structure = parser.parse(document_id="11111111-1111-4111-8111-111111111111", source_path=source)
    parsed = ParsedDocumentFromStructureAdapter().to_parsed_document(structure)

    assert [section.title for section in structure.sections] == ["Safety", "Service"]
    assert structure.source_chunks[0].section_id == structure.sections[0].section_id
    assert parsed.document_id == UUID("11111111-1111-4111-8111-111111111111")
    assert parsed.pages[0].text.startswith("Safety")
    assert "Disconnect power." in parsed.full_text
