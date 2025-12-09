#!/usr/bin/env python
"""CLI tool for testing text extraction.

Usage:
    uv run python -m app.lib.document_processing.cli <file_path> [options]

Examples:
    # Docling (local)
    uv run python -m app.lib.document_processing.cli tmp/data/document.pdf
    uv run python -m app.lib.document_processing.cli tmp/data/document.pdf --mode remote
    uv run python -m app.lib.document_processing.cli tmp/data/scanned.pdf --ocr

    # Mistral OCR
    uv run python -m app.lib.document_processing.cli tmp/data/document.pdf --provider mistral
    uv run python -m app.lib.document_processing.cli --url https://example.com/doc.pdf --provider mistral
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from app.lib.document_processing.factory import get_text_extractor
from app.lib.document_processing.schemas.dto import (
    DoclingOptions,
    DoclingTextExtractionMode,
    MistralOptions,
    ProviderType,
    TextSource,
)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Test text extraction")
    parser.add_argument("file_path", nargs="?", help="Path to document file")
    parser.add_argument(
        "--url",
        help="URL of document (Mistral only)",
    )
    parser.add_argument(
        "--provider",
        choices=["docling", "mistral"],
        default="docling",
        help="Extraction provider (default: docling)",
    )
    parser.add_argument(
        "--mode",
        choices=["local", "remote"],
        default="local",
        help="Docling mode (default: local)",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Enable OCR for scanned documents (Docling only)",
    )
    args = parser.parse_args()

    if not args.file_path and not args.url:
        parser.error("Either file_path or --url is required")

    provider = ProviderType(args.provider)

    # Build source
    if args.url:
        source = TextSource.from_url(args.url)
        output_name = args.url.split("/")[-1].split("?")[0] or "document"
    else:
        path = Path(args.file_path)
        source = TextSource.from_path(path)
        output_name = path.stem

    # Build options
    if provider == ProviderType.DOCLING:
        options = DoclingOptions(
            mode=DoclingTextExtractionMode(args.mode),
            enable_ocr=args.ocr,
        )
    else:
        options = MistralOptions()

    output_path = Path(f"{output_name}.{provider.value}.md")

    print(f"Source:   {args.url or args.file_path}")
    print(f"Provider: {provider.value.upper()}")
    if provider == ProviderType.DOCLING:
        print(f"Mode:     {args.mode.upper()}")
        print(f"OCR:      {args.ocr}")

    extractor = get_text_extractor(provider)
    result = extractor.extract_text(source, options)

    if result.success:
        output_path.write_text(result.result or "")
        print(f"Output:   {output_path}")
        print(f"Length:   {len(result.result or '')} chars")
        preview = (result.result or "")[:500]
        print(f"\n--- Preview ---\n{preview}...")
    else:
        print(f"Error:    {result.message}")
        exit(1)


if __name__ == "__main__":
    main()
