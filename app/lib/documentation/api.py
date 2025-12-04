"""Document conversion API endpoints."""

from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.lib.documentation.dependencies import DocumentConverterDep
from app.lib.documentation.schemas import ConversionMode, ConversionResult

router = APIRouter()


@router.post("/convert", response_model=ConversionResult)
async def convert_document(
    converter: DocumentConverterDep,
    file: Annotated[UploadFile, File(description="Document to convert")],
    mode: Annotated[
        ConversionMode, "LOCAL (Tesseract, free) or REMOTE (VLM API, paid)"
    ] = ConversionMode.LOCAL,
    enable_ocr: Annotated[
        bool, "Enable OCR for scanned PDFs (LOCAL mode only)"
    ] = False,
) -> ConversionResult:
    """Convert uploaded document to markdown. Supports PDF, DOCX, PPTX, XLSX, HTML, Markdown."""
    content = await file.read()
    return converter.convert_from_bytes(
        content,
        file.filename or "document",
        mode=mode,
        enable_ocr=enable_ocr,
    )
