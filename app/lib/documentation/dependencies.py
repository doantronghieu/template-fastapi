"""Document converter dependency injection.

No factory needed - single implementation (docling). Will add factory when needed.
"""

from functools import lru_cache
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

from app.integrations import require_integration

if TYPE_CHECKING:
    from app.lib.documentation.base import DocumentConverter


@lru_cache
@require_integration("docling")
def get_document_converter() -> "DocumentConverter":
    """Provide singleton DocumentConverter instance.

    Currently uses Docling implementation. Will add factory pattern
    when additional converter implementations are needed.
    """
    from app.integrations.docling.converter import DoclingConverter

    return DoclingConverter()


DocumentConverterDep = Annotated["DocumentConverter", Depends(get_document_converter)]
