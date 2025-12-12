"""WeasyPrint PDF converter implementation."""

from typing import Annotated

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

# Initialize library paths BEFORE importing weasyprint
# This handles macOS DYLD_LIBRARY_PATH for Homebrew
import app.lib.document_processing.pdf_conversion.providers._init_libs  # noqa: F401

from weasyprint import CSS, HTML

from app.lib.document_processing.pdf_conversion.base import PdfConverter
from app.lib.document_processing.pdf_conversion.config import DEFAULT_STYLE_CONFIG
from app.lib.document_processing.pdf_conversion.schemas.dto import (
    PdfConversionOptions,
    PdfConversionResult,
)


class WeasyPrintPdfConverter(PdfConverter):
    """PDF converter using WeasyPrint + markdown-it-py."""

    def __init__(self) -> None:
        self._md = (
            MarkdownIt("commonmark")
            .use(front_matter_plugin)
            .enable("table")
            .enable("strikethrough")
        )
        self._default_css = DEFAULT_STYLE_CONFIG.to_css()

    def _get_css(
        self,
        options: Annotated[PdfConversionOptions | None, "Conversion options"],
    ) -> str:
        """Get CSS for conversion, using custom or default."""
        if options and options.css:
            return options.css
        return self._default_css

    def _wrap_html(self, content: str) -> str:
        """Wrap markdown HTML in full document structure."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body>
{content}
</body>
</html>"""

    def convert_markdown(
        self,
        markdown: Annotated[str, "Markdown content to convert"],
        options: Annotated[
            PdfConversionOptions | None, "Conversion options"
        ] = None,
    ) -> PdfConversionResult:
        """Convert markdown string to PDF bytes."""
        try:
            # Convert markdown to HTML
            html_content = self._md.render(markdown)
            full_html = self._wrap_html(html_content)

            # Get CSS
            css_content = self._get_css(options)

            # Get base URL if provided
            base_url = options.base_url if options else None

            # Convert to PDF
            html = HTML(string=full_html, base_url=base_url)
            stylesheets = [CSS(string=css_content)] if css_content else None
            pdf_bytes = html.write_pdf(stylesheets=stylesheets)

            return PdfConversionResult(success=True, content=pdf_bytes)

        except Exception as e:
            return PdfConversionResult(success=False, message=str(e))
