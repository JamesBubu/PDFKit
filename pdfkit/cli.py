"""Command-line entry point for PDFKit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import PDFConverter, SUPPORTED_FORMATS


def _parse_pages(value: str) -> tuple[int, int]:
    """Parse "START-END" (1-indexed, inclusive) into 0-indexed (start, end)."""
    if "-" not in value:
        page = int(value)
        return page - 1, page
    start_s, end_s = value.split("-", 1)
    start = int(start_s) - 1 if start_s else 0
    end = int(end_s) if end_s else None
    if end is not None and end <= start:
        raise argparse.ArgumentTypeError(f"Invalid page range: {value}")
    return start, end  # type: ignore[return-value]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdfkit",
        description="Convert PDF files into editable formats (Word, HTML, Markdown, text, Excel).",
    )
    p.add_argument("pdf", help="Path to the source PDF file.")
    p.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Directory to write outputs to (default: current directory).",
    )
    p.add_argument(
        "-f",
        "--format",
        dest="formats",
        action="append",
        choices=SUPPORTED_FORMATS,
        help=(
            "Output format; pass multiple times for several formats. "
            f"Choices: {', '.join(SUPPORTED_FORMATS)}. Default: docx."
        ),
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="Convert to every supported format.",
    )
    p.add_argument(
        "--pages",
        type=_parse_pages,
        help="Page range to convert, 1-indexed inclusive (e.g. '1-5', '3', '2-').",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.all:
        formats = list(SUPPORTED_FORMATS)
    else:
        formats = args.formats or ["docx"]

    try:
        converter = PDFConverter(args.pdf)
        outputs = converter.convert(
            output_dir=args.output_dir,
            formats=formats,
            pages=args.pages,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface library errors cleanly
        print(f"conversion failed: {exc}", file=sys.stderr)
        return 1

    for fmt, path in outputs.items():
        print(f"{fmt:<5} -> {Path(path).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
