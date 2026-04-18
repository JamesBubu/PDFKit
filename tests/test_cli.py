"""Tests for the pdfkit CLI (argument parsing + end-to-end conversion)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdfkit.cli import _parse_pages, main


def test_parse_pages_single():
    assert _parse_pages("3") == (2, 3)


def test_parse_pages_range():
    assert _parse_pages("1-5") == (0, 5)


def test_parse_pages_open_end():
    assert _parse_pages("2-") == (1, None)


def test_parse_pages_invalid():
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        _parse_pages("5-2")


def test_cli_missing_file_exits_2(tmp_path, capsys):
    code = main([str(tmp_path / "missing.pdf"), "-o", str(tmp_path)])
    assert code == 2
    assert "error" in capsys.readouterr().err.lower()


def test_cli_default_is_docx(sample_pdf, tmp_path):
    code = main([str(sample_pdf), "-o", str(tmp_path)])
    assert code == 0
    assert (tmp_path / f"{sample_pdf.stem}.docx").is_file()


def test_cli_multi_format(sample_pdf, tmp_path):
    code = main([
        str(sample_pdf),
        "-o", str(tmp_path),
        "-f", "txt",
        "-f", "md",
    ])
    assert code == 0
    assert (tmp_path / f"{sample_pdf.stem}.txt").is_file()
    assert (tmp_path / f"{sample_pdf.stem}.md").is_file()


def test_cli_all_flag(sample_pdf, tmp_path):
    from pdfkit import SUPPORTED_FORMATS

    code = main([str(sample_pdf), "-o", str(tmp_path), "--all"])
    assert code == 0
    for fmt in SUPPORTED_FORMATS:
        assert (tmp_path / f"{sample_pdf.stem}.{fmt}").is_file()


def test_cli_page_range(sample_pdf, tmp_path):
    code = main([
        str(sample_pdf),
        "-o", str(tmp_path),
        "-f", "txt",
        "--pages", "1",
    ])
    assert code == 0
    text = (tmp_path / f"{sample_pdf.stem}.txt").read_text(encoding="utf-8")
    assert "PDFKit Sample Document" in text
    assert "Second Page" not in text
