"""PDF to Markdown converter with bookmark preservation and OCR support.

Converts PDF files to markdown while preserving PDF bookmarks/TOC as markdown headers.
Uses PyMuPDF4LLM with custom bookmark injection and automatic OCR for scanned pages.
"""

import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Annotated

# Configure Tesseract OCR before importing pymupdf
_TESSDATA_PATHS = [
    "/opt/homebrew/share/tessdata",
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/share/tesseract-ocr/5/tessdata",
    "/usr/share/tessdata",
]
if not os.environ.get("TESSDATA_PREFIX"):
    for p in _TESSDATA_PATHS:
        if Path(p).exists():
            os.environ["TESSDATA_PREFIX"] = p
            break

import pymupdf
import pymupdf4llm

logger = logging.getLogger(__name__)

# =============================================================================
# Patterns
# =============================================================================
_CLEANUP = {
    "strikethrough": (re.compile(r"~~([^~]+)~~"), r"\1"),
    "inline_code": (re.compile(r"`([^`]+)`"), r"\1"),
    "excess_newlines": (re.compile(r"\n{4,}"), "\n\n\n"),
}

# Garbage line patterns: (pattern, use_search)
_GARBAGE_LINE = [
    (re.compile(r"^[\s!I|.•\-\[\]r]*$"), False),  # Repeated punctuation
    (re.compile(r"^[^a-zA-Z0-9]*$"), False),  # No alphanumeric
    (re.compile(r"^([\w] ){2,}[\w]?$"), False),  # Spaced chars "N 1 XI"
    (re.compile(r"^\[.*\]$|^I I \["), False),  # Bracketed garbage
    (re.compile(r"^\s*[•·]\s*[A-Za-z]?$"), False),  # Bullet + single char
    (re.compile(r"^[~]?[a-zA-Z0-9]$"), False),  # Single char
    (re.compile(r"[^\w\s]{3,}"), True),  # 3+ consecutive symbols
    (re.compile(r"[\\;`\"\']{2,}|^\\"), True),  # Backslash garbage
    (re.compile(r"^[•·].*--"), True),  # Bullet + dashes
]

# Garbage heading patterns (pymupdf4llm converts bold/large text to headers)
_GARBAGE_HEADING = [
    re.compile(r"[■□▪▫●○◆◇★☆]"),  # Box/shape characters
    re.compile(r"^[=\-_*#]+$"),  # Only symbols
    re.compile(r"^\*\*[=\s■]+"),  # Bold with symbols
]

# Short words to preserve (not garbage)
_SHORT_WORDS = frozenset(
    "a an as at be by do go he i if in is it me my no of on or so to up us we am "
    "are can did for had has her him his how its may new not now old our out own "
    "see she the too two use was who why yes yet you and but "
    "dob ssn dds vr ed yr mo dr mr ms md pa rn aka etc inc ltd llc".split()
)


# =============================================================================
# Garbage filtering
# =============================================================================
def _is_garbage_line(line: str) -> bool:
    """Detect garbage lines from OCR/scanned PDFs."""
    s = line.strip()
    if not s or s.startswith("#") or s in ("---", "***", "___"):
        return False
    if s.startswith("**") and s.endswith("**"):
        return False

    # Pattern checks
    for pattern, use_search in _GARBAGE_LINE:
        if (use_search and pattern.search(s)) or (not use_search and pattern.match(s)):
            return True

    # Short word check (1-3 letters)
    if re.match(r"^[a-zA-Z]{1,3}$", s) and s.lower() not in _SHORT_WORDS:
        return True

    # High symbol ratio (>60% non-alphanumeric)
    if len(s) > 8 and sum(c.isalnum() for c in s) / len(s) < 0.4:
        return True

    # Short token sequences "a i", "n I"
    tokens = s.split()
    if 2 <= len(tokens) <= 3 and all(len(t) <= 2 for t in tokens):
        return True

    return False


def _filter_garbage(text: str) -> str:
    """Remove garbage lines."""
    return "\n".join(ln for ln in text.split("\n") if not _is_garbage_line(ln))


def _filter_garbage_headings(text: str) -> str:
    """Convert garbage headings to plain text."""
    lines = []
    for line in text.split("\n"):
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            if any(p.search(title) for p in _GARBAGE_HEADING):
                lines.append(title)  # Strip # prefix
                continue
        lines.append(line)
    return "\n".join(lines)


def _add_heading_context(text: str) -> str:
    """Add page/parent context to markdown headings."""
    result, page, stack = [], 1, {}

    for line in text.split("\n"):
        if line.startswith("**Page ") and " of " in line:
            try:
                page = int(line.split("**Page ")[1].split(" of ")[0])
            except (IndexError, ValueError):
                pass
            result.append(line)
            continue

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            stack = {k: v for k, v in stack.items() if k < level}
            parents = [stack[i] for i in range(1, level) if i in stack]
            stack[level] = title

            result.extend([
                line, "",
                "<context>",
                f"Page: {page}",
                f"Parent: {' > '.join(parents) if parents else '(none)'}",
                "</context>",
            ])
        else:
            result.append(line)

    return "\n".join(result)


# =============================================================================
# Bookmark extraction
# =============================================================================
def extract_bookmarks(doc: pymupdf.Document) -> dict[int, list[dict]]:
    """Extract bookmarks grouped by page number."""
    bookmarks: dict[int, list[dict]] = defaultdict(list)
    for level, title, page in doc.get_toc():
        if "(Page " in title and " of " in title:
            continue
        bookmarks[page].append({"level": level, "title": title})
    return dict(bookmarks)


def _bookmarks_to_markdown(bookmarks: list[dict]) -> str:
    """Convert bookmarks to markdown headers."""
    if not bookmarks:
        return ""
    return "\n\n".join("#" * b["level"] + " " + b["title"] for b in bookmarks) + "\n\n"


# =============================================================================
# Main conversion
# =============================================================================
def convert_pdf_to_markdown(
    pdf_path: Annotated[str | Path, "Path to input PDF file"],
    output_path: Annotated[str | Path | None, "Path to save output markdown"] = None,
) -> Annotated[str, "Markdown with bookmark headers"]:
    """Convert PDF to markdown with bookmark headers at page boundaries."""
    doc = pymupdf.open(str(pdf_path))

    bookmarks_by_page = extract_bookmarks(doc)
    logger.info(f"Extracted {sum(len(b) for b in bookmarks_by_page.values())} bookmarks from {doc.page_count} pages")

    page_chunks = pymupdf4llm.to_markdown(
        doc, page_chunks=True, write_images=False, table_strategy=None,
        ignore_graphics=True, ignore_images=True, ignore_code=True,
        fontsize_limit=3, graphics_limit=500, margins=0, force_text=True, use_glyphs=True,
    )

    # Build markdown
    parts = []
    if doc.metadata.get("title"):
        parts.append(f"# {doc.metadata['title']}\n\n")

    total = doc.page_count
    for i, chunk in enumerate(page_chunks):
        page_num = i + 1
        if page_num in bookmarks_by_page:
            parts.append(_bookmarks_to_markdown(bookmarks_by_page[page_num]))
        if page_text := chunk.get("text", "").strip():
            parts.append(f"---\n**Page {page_num} of {total}**\n\n")
            parts.append(page_text + "\n\n")

    doc.close()

    # Post-process
    md = "".join(parts)
    for pattern, replacement in _CLEANUP.values():
        md = pattern.sub(replacement, md)
    md = _filter_garbage(md)
    md = _filter_garbage_headings(md)
    md = _add_heading_context(md)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md, encoding="utf-8")
        logger.info(f"Saved markdown to: {output_path}")

    return md


def get_document_sections(
    pdf_path: Annotated[str | Path, "Path to PDF file"],
) -> Annotated[list[dict], "Section dicts with level, title, page"]:
    """Extract section structure from PDF bookmarks."""
    doc = pymupdf.open(str(pdf_path))
    toc = doc.get_toc()
    doc.close()
    return [
        {"level": level, "title": title, "page": page}
        for level, title, page in toc
        if not ("(Page " in title and " of " in title)
    ]
