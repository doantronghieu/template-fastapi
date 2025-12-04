#!/usr/bin/env python
"""CLI tool for testing document conversion.

Usage:
    uv run python -m app.lib.documentation.cli <file_path> [--mode local|remote] [--ocr]

Examples:
    uv run python -m app.lib.documentation.cli tmp/data/document.pdf
    uv run python -m app.lib.documentation.cli tmp/data/document.pdf --mode remote
    uv run python -m app.lib.documentation.cli tmp/data/scanned.pdf --mode local --ocr
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from app.lib.documentation import ConversionMode, get_document_converter


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Test document conversion")
    parser.add_argument("file_path", help="Path to document file")
    parser.add_argument(
        "--mode",
        choices=["local", "remote"],
        default="local",
        help="Conversion mode (default: local)",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Enable OCR for scanned documents (local mode only)",
    )
    args = parser.parse_args()

    path = Path(args.file_path)
    mode = ConversionMode(args.mode)
    output_path = path.with_suffix(f".{mode.value}.md")

    print(f"Input:  {path}")
    print(f"Mode:   {mode.value.upper()}")
    print(f"OCR:    {args.ocr}")

    converter = get_document_converter()
    result = converter.convert_from_path(path, mode=mode, enable_ocr=args.ocr)

    if result.success:
        output_path.write_text(result.markdown)
        print(f"Output: {output_path}")
        print(f"Length: {len(result.markdown)} chars")
        print(f"\n--- Preview ---\n{result.markdown[:500]}...")
    else:
        print(f"Error:  {result.error}")
        exit(1)


if __name__ == "__main__":
    main()
