"""Docling document converter."""

import logging
import warnings
from io import BytesIO
from pathlib import Path
from typing import Annotated, Callable

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import DocumentStream
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    TesseractOcrOptions,
    VlmPipelineOptions,
)
from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions, ResponseFormat
from docling.datamodel.settings import settings
from docling.document_converter import (
    ConversionResult as DoclingConversionResult,
    DocumentConverter,
    PdfFormatOption,
)
from docling.pipeline.vlm_pipeline import VlmPipeline
from requests.exceptions import ConnectionError, HTTPError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.lib.docling.config import docling_settings
from app.lib.docling.schemas import ConversionMode, ConversionResult

# Suppress Docling markdown correction warnings (cosmetic, not errors)
warnings.filterwarnings("ignore", message="Detected potentially incorrect Markdown")

logger = logging.getLogger(__name__)

# Set page batch size to match concurrency for optimal parallel processing
settings.perf.page_batch_size = docling_settings.DL_VLM_CONCURRENCY


def _is_transient_error(exception: BaseException) -> bool:
    """Check if exception is a transient error that should be retried."""
    if isinstance(exception, HTTPError):
        status_code = exception.response.status_code if exception.response else 0
        return status_code in (429, 502, 503, 504)

    if isinstance(exception, ConnectionError):
        return True

    # Docling wraps HTTP errors in RuntimeError
    if isinstance(exception, RuntimeError):
        error_msg = str(exception).lower()
        return any(
            code in error_msg
            for code in (
                "502",
                "503",
                "504",
                "429",
                "bad gateway",
                "service unavailable",
            )
        )

    return False


def _create_retry_decorator() -> Callable:
    """Create retry decorator with settings from config."""
    return retry(
        retry=retry_if_exception(_is_transient_error),
        stop=stop_after_attempt(docling_settings.DL_VLM_RETRY_ATTEMPTS),
        wait=wait_exponential(
            min=docling_settings.DL_VLM_RETRY_MIN_WAIT,
            max=docling_settings.DL_VLM_RETRY_MAX_WAIT,
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


class DoclingConverter:
    """Document converter using Docling.

    Supports two modes:
    - LOCAL: Tesseract OCR (free, local processing)
    - REMOTE: VLM API (paid, higher accuracy) - any OpenAI-compatible endpoint

    Remote mode includes automatic retry for transient API errors (502, 503, 504).
    """

    def __init__(self):
        self._local_converters: dict[bool, DocumentConverter] = {}
        self._remote_converter: DocumentConverter | None = None

    def _get_local_converter(self, enable_ocr: bool) -> DocumentConverter:
        """Get or create local converter with specified OCR setting."""
        if enable_ocr not in self._local_converters:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = enable_ocr
            pipeline_options.do_table_structure = True
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            pipeline_options.table_structure_options.do_cell_matching = True
            pipeline_options.accelerator_options = AcceleratorOptions(
                num_threads=4,
                device=AcceleratorDevice.CPU,
            )

            if enable_ocr:
                pipeline_options.images_scale = 2.0
                pipeline_options.ocr_options = TesseractOcrOptions(
                    force_full_page_ocr=True,
                    lang=["eng"],
                )

            self._local_converters[enable_ocr] = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
        return self._local_converters[enable_ocr]

    def _get_remote_converter(self) -> DocumentConverter:
        """Get or create remote VLM converter (OpenAI-compatible API)."""
        if self._remote_converter is None:
            if not docling_settings.vlm_api_key:
                raise ValueError(
                    "DL_VLM_API_KEY or OPENAI_API_KEY environment variable is required"
                )

            pipeline_options = VlmPipelineOptions(
                enable_remote_services=True,
                vlm_options=ApiVlmOptions(
                    url=docling_settings.DL_VLM_API_URL,
                    headers={"Authorization": f"Bearer {docling_settings.vlm_api_key}"},
                    params={"model": docling_settings.DL_VLM_MODEL},
                    prompt=(
                        "Convert this document page to markdown format. "
                        "Preserve all text, tables, and structure accurately. "
                        "Do not add any commentary, only output the markdown."
                    ),
                    response_format=ResponseFormat.MARKDOWN,
                    timeout=docling_settings.DL_VLM_TIMEOUT,
                    scale=docling_settings.DL_VLM_SCALE,
                    temperature=docling_settings.DL_VLM_TEMPERATURE,
                    concurrency=docling_settings.DL_VLM_CONCURRENCY,
                ),
            )

            self._remote_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_cls=VlmPipeline,
                        pipeline_options=pipeline_options,
                    ),
                }
            )
        return self._remote_converter

    def _execute_conversion(
        self,
        source: Annotated[str | DocumentStream, "File path or document stream"],
        filename: str,
        mode: ConversionMode,
        enable_ocr: Annotated[bool, "OCR for scanned docs (LOCAL mode only)"],
    ) -> ConversionResult:
        """Execute document conversion with appropriate converter."""
        try:
            if mode == ConversionMode.REMOTE:
                converter = self._get_remote_converter()
                result = self._convert_with_retry(converter, source)
            else:
                converter = self._get_local_converter(enable_ocr)
                result = converter.convert(source)

            return ConversionResult(
                success=True,
                markdown=result.document.export_to_markdown(),
                filename=filename,
                mode=mode,
            )
        except Exception as e:
            logger.exception(f"Conversion failed for {filename}")
            return ConversionResult(
                success=False,
                error=str(e),
                filename=filename,
                mode=mode,
            )

    def _convert_with_retry(
        self, converter: DocumentConverter, source: str | DocumentStream
    ) -> DoclingConversionResult:
        """Execute conversion with retry for transient errors."""
        retry_decorator = _create_retry_decorator()

        @retry_decorator
        def _do_convert() -> DoclingConversionResult:
            return converter.convert(source)

        return _do_convert()

    def convert_from_path(
        self,
        file_path: str | Path,
        mode: ConversionMode = ConversionMode.LOCAL,
        enable_ocr: Annotated[bool, "OCR for scanned docs (LOCAL mode only)"] = False,
    ) -> ConversionResult:
        """Convert document from file path to markdown."""
        path = Path(file_path)
        if not path.exists():
            return ConversionResult(
                success=False,
                error=f"File not found: {file_path}",
                filename=path.name,
                mode=mode,
            )

        return self._execute_conversion(str(path), path.name, mode, enable_ocr)

    def convert_from_bytes(
        self,
        content: bytes,
        filename: str,
        mode: ConversionMode = ConversionMode.LOCAL,
        enable_ocr: Annotated[bool, "OCR for scanned docs (LOCAL mode only)"] = False,
    ) -> ConversionResult:
        """Convert document from bytes to markdown."""
        source = DocumentStream(name=filename, stream=BytesIO(content))
        return self._execute_conversion(source, filename, mode, enable_ocr)
