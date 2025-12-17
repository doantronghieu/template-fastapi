"""CLI for PDF to Markdown conversion with bookmark preservation.

Usage: uv run python -m app.lib.document_processing.pdf_to_markdown input.pdf
Output: input.md (same directory, .pdf → .md)
"""

import sys
from pathlib import Path

from app.lib.document_processing.pdf_to_markdown.service import convert_pdf_to_markdown


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if "-h" in sys.argv or "--help" in sys.argv else 1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    output_path = pdf_path.with_suffix(".md")
    convert_pdf_to_markdown(pdf_path=pdf_path, output_path=output_path)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
