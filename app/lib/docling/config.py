"""Docling configuration.

Pydantic settings for document conversion with Tesseract OCR and VLM API.
"""

import logging
import os
import re
import subprocess
from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class SupportedFormat(str, Enum):
    """Supported document formats for conversion."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    HTML = "html"
    MD = "md"


def _detect_tessdata_prefix() -> str | None:
    """Auto-detect Tesseract data directory (OS-agnostic).

    Returns detected path or None if already set or not found.
    """
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stderr or result.stdout
        # Parse: List of available languages in "/path/to/tessdata/" (N):
        match = re.search(r'in "([^"]+)"', output)
        if match:
            return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Could not auto-detect tessdata path: {e}")

    return None


class DoclingSettings(BaseSettings):
    """Docling document conversion settings.

    All settings prefixed with DL_ (Docling).
    VLM settings prefixed with DL_VLM_ for remote API mode.
    """

    # ==========================================================================
    # Tesseract OCR (LOCAL mode)
    # ==========================================================================
    DL_TESSDATA_PREFIX: str | None = Field(
        default=None,
        description="Tesseract data directory (auto-detected if not set)",
    )

    # ==========================================================================
    # VLM API (REMOTE mode) - Any OpenAI-compatible endpoint
    # Supports: OpenAI, Azure OpenAI, OpenRouter, vLLM, Ollama, LM Studio, etc.
    # ==========================================================================
    DL_VLM_API_URL: str = Field(
        default="https://api.openai.com/v1/chat/completions",
        description="OpenAI-compatible chat completions endpoint",
    )

    DL_VLM_API_KEY: str | None = Field(
        default=None,
        description="API key for VLM endpoint (falls back to OPENAI_API_KEY)",
    )

    DL_VLM_MODEL: str = Field(
        default="gpt-4o-mini",
        description="Vision model: gpt-4o-mini (cheapest), gpt-5-nano, gpt-5-mini, gpt-4o, gpt-5",
    )

    DL_VLM_CONCURRENCY: int = Field(
        default=8,
        description="Parallel page processing (4-8 for OpenAI, 32-64 for self-hosted)",
    )

    DL_VLM_TEMPERATURE: float = Field(
        default=1.0,
        description="Temperature (some models like gpt-5-mini only support 1.0)",
    )

    DL_VLM_TIMEOUT: int = Field(
        default=180,
        description="Timeout per page in seconds",
    )

    DL_VLM_SCALE: float = Field(
        default=2.0,
        description="Image scale for accuracy (1.0-3.0)",
    )

    # Retry settings for transient API errors (502, 503, 504, connection errors)
    DL_VLM_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="Number of retry attempts for transient API errors",
    )

    DL_VLM_RETRY_MIN_WAIT: float = Field(
        default=1.0,
        description="Minimum wait time between retries in seconds",
    )

    DL_VLM_RETRY_MAX_WAIT: float = Field(
        default=30.0,
        description="Maximum wait time between retries in seconds",
    )

    # Fallback for API key
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API key (used if DL_VLM_API_KEY not set)",
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )

    @property
    def vlm_api_key(self) -> str | None:
        """Get VLM API key with fallback to OPENAI_API_KEY."""
        return self.DL_VLM_API_KEY or self.OPENAI_API_KEY

    @property
    def tessdata_prefix(self) -> str | None:
        """Get Tesseract data path with auto-detection."""
        if self.DL_TESSDATA_PREFIX:
            return self.DL_TESSDATA_PREFIX
        return _detect_tessdata_prefix()


# Singleton instance
docling_settings = DoclingSettings()

# Configure Tesseract environment on import
if docling_settings.tessdata_prefix:
    os.environ["TESSDATA_PREFIX"] = docling_settings.tessdata_prefix
    logger.debug(f"TESSDATA_PREFIX set to: {docling_settings.tessdata_prefix}")
