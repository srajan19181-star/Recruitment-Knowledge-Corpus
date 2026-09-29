from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class PageText:
    doc_id: str
    page: int
    text: str


def load_pdf(path: Path) -> list[PageText]:
    """Extract text page by page. Multi-column layouts and tables extract
    as jumbled text with pypdf's default extraction — that's a known
    limitation worth calling out rather than hiding; a production system
    would add layout-aware extraction (e.g. pdfplumber or a vision model)
    as a follow-up for documents where this matters."""
    reader = PdfReader(str(path))
    doc_id = path.stem
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(PageText(doc_id=doc_id, page=i + 1, text=text))
    return pages
