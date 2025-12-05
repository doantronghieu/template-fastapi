"""NetDocuments utility functions."""

from fnmatch import fnmatch
from typing import Annotated


def matches_document_name(
    doc_name: Annotated[str, "Document name without extension"],
    doc_ext: Annotated[str, "Document extension (e.g., 'pdf')"],
    pattern: Annotated[str, "Search pattern (supports * and ? wildcards)"],
    exact: Annotated[
        bool, "If True, require exact match; if False, allow partial/wildcard"
    ],
) -> bool:
    """Check if document name matches pattern.

    Matching modes:
    - exact=True: doc_name or full_name must equal pattern exactly
    - Wildcards (* or ?): uses fnmatch for glob-style matching
    - Partial: case-insensitive substring match
    """
    full_name = f"{doc_name}.{doc_ext}" if doc_ext else doc_name
    if exact:
        return doc_name == pattern or full_name == pattern
    if "*" in pattern or "?" in pattern:
        return fnmatch(doc_name, pattern) or fnmatch(full_name, pattern)
    return pattern.lower() in doc_name.lower() or pattern.lower() in full_name.lower()
