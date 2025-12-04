"""Document processing API endpoints."""

import json
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.lib.document_processing.factory import get_text_extractor
from app.lib.document_processing.schemas import (
    DoclingOptions,
    MistralOptions,
    ProviderType,
    TextExtractionResult,
    TextSource,
)

router = APIRouter()


@router.post("/extract-text")
async def extract_text(
    file: Annotated[UploadFile | None, File()] = None,
    url: Annotated[str | None, Form(description="Document URL (Mistral only)")] = None,
    provider: Annotated[ProviderType, Form()] = ProviderType.DOCLING,
    options: Annotated[
        str | None,
        Form(description="JSON options string for provider-specific settings"),
    ] = None,
) -> TextExtractionResult:
    """Extract text from document."""
    # Validate input
    if file is None and url is None:
        raise HTTPException(400, "Provide either 'file' or 'url'")
    if file is not None and url is not None:
        raise HTTPException(400, "Provide either 'file' or 'url', not both")

    # Build source
    if url:
        source = TextSource.from_url(url)
    else:
        content = await file.read()
        source = TextSource.from_bytes(content, file.filename or "document")

    # Parse options
    parsed_options = None
    if options:
        try:
            options_dict = json.loads(options)
            if provider == ProviderType.DOCLING:
                parsed_options = DoclingOptions(**options_dict)
            else:
                parsed_options = MistralOptions(**options_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(400, f"Invalid options JSON: {e}")

    # Extract
    extractor = get_text_extractor(provider)
    return extractor.extract_text(source, parsed_options)
