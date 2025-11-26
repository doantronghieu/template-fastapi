"""Email parsing utilities for IMAP messages."""

import email
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr

import html2text

from ..types import EmailAddress, EmailMessage


def _decode_header_value(header_value: str | None) -> str:
    """Decode email header handling various encodings."""
    if not header_value:
        return ""

    decoded_parts = decode_header(header_value)
    result = []
    for content, encoding in decoded_parts:
        if isinstance(content, bytes):
            result.append(content.decode(encoding or "utf-8", errors="ignore"))
        else:
            result.append(content)
    return "".join(result)


def _parse_email_address(address_str: str) -> EmailAddress:
    """Parse email address string into structured format."""
    name, email_addr = parseaddr(address_str)
    return EmailAddress(
        name=_decode_header_value(name) if name else None, email=email_addr
    )


def _parse_email_addresses(address_str: str | None) -> list[EmailAddress]:
    """Parse comma-separated email addresses."""
    if not address_str:
        return []
    return [_parse_email_address(addr.strip()) for addr in address_str.split(",")]


def _get_email_body(msg: Message) -> tuple[str | None, str | None]:
    """Extract text and HTML body from email message."""
    text_body = None
    html_body = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and not text_body:
                payload = part.get_payload(decode=True)
                if payload:
                    text_body = payload.decode(errors="ignore")
            elif content_type == "text/html" and not html_body:
                payload = part.get_payload(decode=True)
                if payload:
                    html_body = payload.decode(errors="ignore")
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            decoded_payload = payload.decode(errors="ignore")
            if content_type == "text/plain":
                text_body = decoded_payload
            elif content_type == "text/html":
                html_body = decoded_payload

    return text_body, html_body


def parse_email_message(raw_email: bytes, is_unread: bool = False) -> EmailMessage:
    """Parse raw email bytes into structured EmailMessage.

    Args:
        raw_email: Raw email bytes from IMAP
        is_unread: Whether email is marked as unread

    Returns:
        Structured EmailMessage dict
    """
    msg = email.message_from_bytes(raw_email)

    text_body, html_body = _get_email_body(msg)

    # Convert HTML to text if text body is not available
    if not text_body and html_body:
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        text_body = h.handle(html_body)

    return EmailMessage(
        message_id=msg.get("Message-ID", ""),
        subject=_decode_header_value(msg.get("Subject", "")),
        from_=_parse_email_address(msg.get("From", "")),
        to=_parse_email_addresses(msg.get("To")),
        date=msg.get("Date", ""),
        body_text=text_body,
        body_html=html_body,
        is_unread=is_unread,
    )
