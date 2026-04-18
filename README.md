# PDFKit

Convert PDF files into editable formats while preserving the original layout,
fonts, tables, and images as closely as the target format allows.

## Supported output formats

| Format | Extension | Preserves |
|--------|-----------|-----------|
| Microsoft Word | `.docx` | columns, paragraphs, tables, images, fonts, bold/italic, colors |
| HTML | `.html` | exact positioning, font family, size, weight, color |
| Markdown | `.md` | headings, lists, emphasis, links |
| Plain text | `.txt` | reading order |
| Excel | `.xlsx` | one sheet per detected table |

## Install

```bash
pip install -r requirements.txt
```

## Command-line usage

```bash
# Default: convert to .docx in the current directory
python -m pdfkit input.pdf

# Pick specific formats
python -m pdfkit input.pdf -f docx -f html -f md

# Convert to every supported format at once
python -m pdfkit input.pdf --all -o ./out

# Limit to a page range (1-indexed, inclusive)
python -m pdfkit input.pdf -f docx --pages 1-5
python -m pdfkit input.pdf -f txt  --pages 3
python -m pdfkit input.pdf -f html --pages 2-
```

After `pip install .` the same commands are available as the `pdfkit` script.

## Python API

```python
from pdfkit import PDFConverter

converter = PDFConverter("report.pdf")
outputs = converter.convert(
    output_dir="out",
    formats=["docx", "html", "xlsx"],
    pages=(0, 10),  # 0-indexed, end exclusive
)
for fmt, path in outputs.items():
    print(fmt, path)
```

## Running the tests

```bash
pip install -r requirements.txt pytest
pytest
```

The suite generates its own sample PDF in a temp directory and exercises every
supported output format plus the CLI. CI runs the same suite on Python 3.9 –
3.12 via GitHub Actions (`.github/workflows/ci.yml`).

## How layout and styling are preserved

- **DOCX** - uses `pdf2docx`, which reconstructs paragraphs, columns, tables,
  images, and character-level styles (font family, size, weight, color). The
  result opens directly in Word or LibreOffice with the original look intact.
- **HTML** - uses PyMuPDF's `get_text("html")` output, which positions every
  text span absolutely and attaches inline CSS for font, size, style, and
  color.
- **Markdown** - the HTML above is run through `markdownify` so that semantic
  structure (headings, lists, bold/italic, links) survives.
- **XLSX** - tables are detected with `pdfplumber` and each one is placed on
  its own worksheet.
