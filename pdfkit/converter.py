"""Core PDF conversion logic.

Each output format is handled by a dedicated method that preserves as much of
the original layout, typography, and structure as the target format allows.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

SUPPORTED_FORMATS = ("docx", "html", "txt", "md", "xlsx")


class PDFConverter:
    """Convert a single PDF into one or more editable formats."""

    def __init__(self, pdf_path: str | os.PathLike):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        if self.pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {self.pdf_path}")

    def convert(
        self,
        output_dir: str | os.PathLike,
        formats: Iterable[str] = ("docx",),
        pages: Optional[tuple[int, int]] = None,
    ) -> dict[str, Path]:
        """Convert the PDF to every requested format.

        Args:
            output_dir: Directory where outputs are written.
            formats: Iterable of format names from SUPPORTED_FORMATS.
            pages: Optional (start, end) 0-indexed page range, end exclusive.

        Returns:
            Mapping of format -> written file path.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        results: dict[str, Path] = {}
        stem = self.pdf_path.stem

        for fmt in formats:
            fmt = fmt.lower().lstrip(".")
            if fmt not in SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
                )
            target = out_dir / f"{stem}.{fmt}"
            method = getattr(self, f"_to_{fmt}")
            method(target, pages=pages)
            results[fmt] = target
        return results

    # ----- Per-format implementations --------------------------------------

    def _to_docx(self, target: Path, pages: Optional[tuple[int, int]] = None) -> None:
        """Convert to Word, preserving layout, fonts, images, and tables.

        Uses pdf2docx, which reconstructs paragraphs, columns, tables, images,
        and character-level styling (font family, size, bold/italic, color).
        """
        from pdf2docx import Converter

        start, end = (pages or (0, None))
        cv = Converter(str(self.pdf_path))
        try:
            cv.convert(str(target), start=start, end=end)
        finally:
            cv.close()

    def _to_html(self, target: Path, pages: Optional[tuple[int, int]] = None) -> None:
        """Convert to styled HTML with absolute positioning.

        PyMuPDF emits HTML whose spans carry inline CSS for font family, size,
        weight, style, and color - so the output looks very close to the PDF.
        """
        import fitz  # PyMuPDF

        doc = fitz.open(self.pdf_path)
        start, end = self._resolve_range(pages, doc.page_count)
        parts = [
            "<!DOCTYPE html>",
            '<html><head><meta charset="utf-8">',
            f"<title>{self.pdf_path.stem}</title>",
            "<style>body{margin:0;background:#eee}"
            ".page{background:#fff;margin:16px auto;box-shadow:0 0 4px #aaa;position:relative}"
            "</style></head><body>",
        ]
        for i in range(start, end):
            page = doc.load_page(i)
            page_html = page.get_text("html")
            parts.append(f'<div class="page" data-page="{i + 1}">{page_html}</div>')
        parts.append("</body></html>")
        target.write_text("\n".join(parts), encoding="utf-8")
        doc.close()

    def _to_md(self, target: Path, pages: Optional[tuple[int, int]] = None) -> None:
        """Convert to Markdown by way of HTML (keeps headings, lists, bold, links)."""
        import fitz
        from markdownify import markdownify

        doc = fitz.open(self.pdf_path)
        start, end = self._resolve_range(pages, doc.page_count)
        chunks = []
        for i in range(start, end):
            page_html = doc.load_page(i).get_text("html")
            chunks.append(markdownify(page_html, heading_style="ATX"))
            chunks.append(f"\n\n---\n\n*page {i + 1}*\n\n")
        doc.close()
        target.write_text("".join(chunks).strip() + "\n", encoding="utf-8")

    def _to_txt(self, target: Path, pages: Optional[tuple[int, int]] = None) -> None:
        """Convert to plain text, preserving reading order and blank lines."""
        import fitz

        doc = fitz.open(self.pdf_path)
        start, end = self._resolve_range(pages, doc.page_count)
        buffer = []
        for i in range(start, end):
            buffer.append(doc.load_page(i).get_text("text"))
            buffer.append("\n")
        doc.close()
        target.write_text("".join(buffer), encoding="utf-8")

    def _to_xlsx(self, target: Path, pages: Optional[tuple[int, int]] = None) -> None:
        """Extract every detected table into its own worksheet.

        Uses pdfplumber, whose table detection handles both ruled and
        whitespace-delimited tables.
        """
        import pdfplumber
        from openpyxl import Workbook

        wb = Workbook()
        wb.remove(wb.active)

        with pdfplumber.open(self.pdf_path) as pdf:
            start, end = self._resolve_range(pages, len(pdf.pages))
            table_idx = 0
            for page_num in range(start, end):
                page = pdf.pages[page_num]
                for t_num, table in enumerate(page.extract_tables() or [], start=1):
                    table_idx += 1
                    sheet = wb.create_sheet(title=f"p{page_num + 1}_t{t_num}"[:31])
                    for row in table:
                        sheet.append([("" if cell is None else cell) for cell in row])

            if table_idx == 0:
                sheet = wb.create_sheet(title="text")
                for page_num in range(start, end):
                    for line in (pdf.pages[page_num].extract_text() or "").splitlines():
                        sheet.append([line])

        wb.save(target)

    # ----- Helpers ---------------------------------------------------------

    @staticmethod
    def _resolve_range(
        pages: Optional[tuple[int, int]], total: int
    ) -> tuple[int, int]:
        if pages is None:
            return 0, total
        start, end = pages
        end = total if end is None else min(end, total)
        start = max(0, start)
        if start >= end:
            raise ValueError(f"Empty page range: {pages}")
        return start, end
