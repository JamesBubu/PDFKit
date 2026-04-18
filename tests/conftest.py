"""Shared pytest fixtures: generates a small but realistic test PDF."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
import pytest


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory) -> Path:
    """Create a two-page PDF with styled text, headings, and a table."""
    pdf_path = tmp_path_factory.mktemp("pdfs") / "sample.pdf"

    doc = fitz.open()

    page1 = doc.new_page(width=612, height=792)
    page1.insert_text((72, 72), "PDFKit Sample Document",
                      fontname="helv", fontsize=20)
    page1.insert_text((72, 120), "Introduction",
                      fontname="helv", fontsize=14)
    page1.insert_text(
        (72, 150),
        "This PDF is generated for PDFKit's test suite. It exercises "
        "multi-page rendering, styled text, and table extraction.",
        fontname="helv", fontsize=11,
    )
    page1.insert_text((72, 210), "Bold emphasis here.",
                      fontname="hebo", fontsize=12)
    page1.insert_text((72, 240), "Italic aside here.",
                      fontname="heit", fontsize=12)

    # Simple ruled table for xlsx extraction.
    rows = [
        ["Name", "Score", "Grade"],
        ["Alice", "95", "A"],
        ["Bob", "82", "B"],
        ["Carol", "77", "C"],
    ]
    x0, y0, col_w, row_h = 72, 300, 90, 22
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            rect = fitz.Rect(
                x0 + c * col_w, y0 + r * row_h,
                x0 + (c + 1) * col_w, y0 + (r + 1) * row_h,
            )
            page1.draw_rect(rect, color=(0, 0, 0), width=0.8)
            page1.insert_text(
                (rect.x0 + 4, rect.y0 + 15),
                cell, fontname="helv", fontsize=10,
            )

    page2 = doc.new_page(width=612, height=792)
    page2.insert_text((72, 72), "Second Page",
                      fontname="helv", fontsize=18)
    page2.insert_text(
        (72, 110),
        "Content on the second page validates page-range handling.",
        fontname="helv", fontsize=11,
    )

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path
