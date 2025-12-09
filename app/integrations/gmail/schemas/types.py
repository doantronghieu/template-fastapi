"""Type definitions for email structures.

Provides runtime type hints for IMAP email data without validation overhead.
"""

from typing import TypedDict


class EmailAddress(TypedDict, total=False):
    """Email address with optional display name."""

    name: str | None
    email: str


class EmailMessage(TypedDict, total=False):
    """Parsed email message structure."""

    message_id: str
    subject: str
    from_: EmailAddress
    to: list[EmailAddress]
    date: str
    body_text: str | None
    body_html: str | None
    is_unread: bool
