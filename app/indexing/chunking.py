from app.domain.models import ParsedDocument


class Chunker:
    def __init__(self, chunk_size: int = 900, overlap: int = 120):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunks(self, parsed: ParsedDocument) -> list[dict]:
        output: list[dict] = []
        for page in parsed.pages:
            text = page.text.strip()
            if not text:
                continue
            start = 0
            chunk_number = 0
            while start < len(text):
                end = start + self.chunk_size
                output.append(
                    {
                        "text": text[start:end],
                        "page_start": page.number,
                        "page_end": page.number,
                        "chunk_number": chunk_number,
                    }
                )
                chunk_number += 1
                if end >= len(text):
                    break
                start = max(0, end - self.overlap)
        return output

