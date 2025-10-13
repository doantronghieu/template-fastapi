"""Gmail IMAP integration."""

from .client import GmailClient
from .dependencies import GmailClientDep, get_gmail_client
from .types import EmailAddress, EmailMessage

__all__ = [
    "EmailAddress",
    "EmailMessage",
    "GmailClient",
    "GmailClientDep",
    "get_gmail_client",
]
