"""Docling dependency injection."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.lib.docling.converter import DoclingConverter


@lru_cache
def get_docling_converter() -> DoclingConverter:
    """Provide singleton DoclingConverter instance."""
    return DoclingConverter()


DoclingConverterDep = Annotated[DoclingConverter, Depends(get_docling_converter)]
