"""PDF conversion configuration with CSS styling."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PageConfig:
    """Page layout configuration."""

    size: str = "A4"
    margin: str = "1cm 1cm 1cm 1.5cm"  # top right bottom left


@dataclass(frozen=True)
class TypographyConfig:
    """Typography configuration."""

    font_family: str = (
        '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
        '"Helvetica Neue", Arial, sans-serif'
    )
    font_size: str = "9pt"
    line_height: float = 1.25
    color: str = "#333"


@dataclass(frozen=True)
class SpacingConfig:
    """Spacing configuration."""

    paragraph_margin: str = "0.4em"
    heading_margin_top: str = "0.7em"
    heading_margin_bottom: str = "0.25em"
    code_block_padding: str = "0.4em 0.6em"
    list_margin: str = "0.3em"


@dataclass(frozen=True)
class PdfStyleConfig:
    """Complete PDF styling configuration."""

    page: PageConfig = None
    typography: TypographyConfig = None
    spacing: SpacingConfig = None

    def __post_init__(self):
        # Use object.__setattr__ for frozen dataclass
        if self.page is None:
            object.__setattr__(self, "page", PageConfig())
        if self.typography is None:
            object.__setattr__(self, "typography", TypographyConfig())
        if self.spacing is None:
            object.__setattr__(self, "spacing", SpacingConfig())

    def to_css(self) -> str:
        """Generate CSS from configuration."""
        return f"""/* Auto-generated PDF styling */

@page {{
    size: {self.page.size};
    margin: {self.page.margin};
}}

body {{
    font-family: {self.typography.font_family};
    font-size: {self.typography.font_size};
    line-height: {self.typography.line_height};
    color: {self.typography.color};
}}

h1, h2, h3, h4, h5, h6 {{
    margin-top: {self.spacing.heading_margin_top};
    margin-bottom: {self.spacing.heading_margin_bottom};
    font-weight: 600;
    line-height: 1.2;
}}

h1 {{ font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
h3 {{ font-size: 1.25em; }}
h4 {{ font-size: 1em; }}

p {{
    margin: {self.spacing.paragraph_margin} 0;
}}

a {{
    color: #0366d6;
    text-decoration: none;
}}

code {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.9em;
    background-color: #f6f8fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
}}

pre {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.85em;
    background-color: #f6f8fa;
    padding: {self.spacing.code_block_padding};
    border-radius: 4px;
    overflow-x: auto;
    line-height: 1.35;
    margin: {self.spacing.paragraph_margin} 0;
}}

pre code {{
    background-color: transparent;
    padding: 0;
}}

blockquote {{
    margin: {self.spacing.paragraph_margin} 0;
    padding: 0 0.8em;
    border-left: 3px solid #ddd;
    color: #666;
}}

ul, ol {{
    margin: {self.spacing.list_margin} 0;
    padding-left: 1.8em;
}}

li {{
    margin: 0.15em 0;
}}

table {{
    border-collapse: collapse;
    width: 100%;
    margin: {self.spacing.paragraph_margin} 0;
}}

th, td {{
    border: 1px solid #ddd;
    padding: 0.35em 0.6em;
    text-align: left;
}}

th {{
    background-color: #f6f8fa;
    font-weight: 600;
}}

hr {{
    border: none;
    border-top: 1px solid #eee;
    margin: 1em 0;
}}

del, s {{
    text-decoration: line-through;
    color: #666;
}}

img {{
    max-width: 100%;
    height: auto;
}}
"""


# Default configuration instance
DEFAULT_STYLE_CONFIG = PdfStyleConfig()
