"""WeasyPrint markdown to PDF converter implementation."""

# Initialize library paths BEFORE importing weasyprint
# This handles macOS DYLD_LIBRARY_PATH for Homebrew
import app.lib.document_processing.markdown_to_pdf.providers._init_libs  # noqa: F401, I001

from typing import Annotated

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from weasyprint import CSS, HTML

from app.lib.document_processing.markdown_to_pdf.base import MarkdownToPdfConverter
from app.lib.document_processing.markdown_to_pdf.config import DEFAULT_STYLE_CONFIG
from app.lib.document_processing.markdown_to_pdf.schemas.dto import (
    MarkdownToPdfOptions,
    MarkdownToPdfResult,
)


class WeasyPrintMarkdownToPdfConverter(MarkdownToPdfConverter):
    """Markdown to PDF converter using WeasyPrint + markdown-it-py."""

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
        options: Annotated[MarkdownToPdfOptions | None, "Conversion options"],
    ) -> str:
        """Get CSS for conversion, merging default with custom if provided."""
        if options and options.css:
            # Merge default CSS with custom CSS
            return f"{self._default_css}\n\n/* Custom styles */\n{options.css}"
        return self._default_css

    def _wrap_html(
        self,
        content: str,
        template: Annotated[str | None, "Custom HTML template"] = None,
    ) -> str:
        """Wrap markdown HTML in full document structure."""
        if template:
            return template.format(content=content)
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body>
{content}
</body>
</html>"""

    def convert(
        self,
        markdown: Annotated[str, "Markdown content to convert"],
        options: Annotated[MarkdownToPdfOptions | None, "Conversion options"] = None,
    ) -> MarkdownToPdfResult:
        """Convert markdown string to PDF bytes."""
        try:
            # Convert markdown to HTML
            html_content = self._md.render(markdown)
            template = options.html_template if options else None
            full_html = self._wrap_html(html_content, template)

            # Get CSS
            css_content = self._get_css(options)

            # Get base URL if provided
            base_url = options.base_url if options else None

            # Convert to PDF
            html = HTML(string=full_html, base_url=base_url)
            stylesheets = [CSS(string=css_content)] if css_content else None
            pdf_bytes = html.write_pdf(stylesheets=stylesheets)

            return MarkdownToPdfResult(success=True, content=pdf_bytes)

        except Exception as e:
            return MarkdownToPdfResult(success=False, message=str(e))
