"""Document conversion API endpoints."""

from fastapi import APIRouter, File, UploadFile

from app.lib.docling import ConversionMode, ConversionResult, DoclingConverterDep

router = APIRouter()


@router.post("/documents/convert", response_model=ConversionResult)
async def convert_document(
    converter: DoclingConverterDep,
    file: UploadFile = File(...),
    mode: ConversionMode = ConversionMode.LOCAL,
    enable_ocr: bool = False,
) -> ConversionResult:
    """Convert uploaded document to markdown.

    Supports PDF, DOCX, PPTX, XLSX, HTML, and Markdown files.

    Args:
        file: Document file to convert
        mode: LOCAL (Tesseract, free) or REMOTE (VLM API, paid)
        enable_ocr: Enable OCR for scanned PDFs (only for LOCAL mode)
    """
    content = await file.read()
    return converter.convert_from_bytes(
        content,
        file.filename or "document",
        mode=mode,
        enable_ocr=enable_ocr,
    )
