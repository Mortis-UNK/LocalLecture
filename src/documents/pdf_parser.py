from pathlib import Path

from src.generation.schemas import Slide


def parse_pdf(path: str) -> list[Slide]:
    import pymupdf
    import pymupdf4llm

    with pymupdf.open(str(path)) as document:
        pages = pymupdf4llm.to_markdown(document, page_chunks=True)
    return [Slide(id=f"slide:{i}", source_file=Path(path).name, page=i, text=p["text"])
            for i, p in enumerate(pages, start=1)]
