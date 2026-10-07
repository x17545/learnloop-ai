from pathlib import Path

import pymupdf


def extract_pdf_text(file_path: str) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    pages = []

    with pymupdf.open(path) as document:
        for page_index, page in enumerate(document):
            text = page.get_text("text").strip()

            pages.append(
                {
                    "page": page_index + 1,
                    "text": text,
                }
            )

    return pages