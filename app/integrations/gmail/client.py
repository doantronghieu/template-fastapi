"""Gmail IMAP client for searching and retrieving emails.

Provides secure IMAP connection with flexible search capabilities:
- Common filters (date range, sender, subject, unread status)
- Raw IMAP criteria for advanced queries
"""

import imaplib
import logging
from datetime import datetime

from .types import EmailMessage
from .utils import parse_email_message

logger = logging.getLogger(__name__)


class GmailClient:
    """Client for Gmail IMAP operations.

    Handles email search with hybrid approach:
    - User-friendly filters for common use cases
    - Raw IMAP criteria for advanced queries

    Attributes:
        email: Gmail account email address
        app_password: App-specific password from Google Account settings
    """

    def __init__(self, email: str, app_password: str):
        self.email = email
        self.app_password = app_password
        self.imap_host = "imap.gmail.com"

    def _build_criteria(
        self,
        since_date: str | None,
        before_date: str | None,
        from_email: str | None,
        subject_contains: str | None,
        unread_only: bool,
    ) -> list[str]:
        """Build IMAP search criteria from common filters."""
        criteria = []

        if unread_only:
            criteria.append("UNSEEN")
        if since_date:
            criteria.extend(["SINCE", since_date])
        if before_date:
            criteria.extend(["BEFORE", before_date])
        if from_email:
            criteria.extend(["FROM", from_email])
        if subject_contains:
            criteria.extend(["SUBJECT", subject_contains])

        return criteria if criteria else ["ALL"]

    def _format_date(self, dt: datetime) -> str:
        """Format datetime to IMAP date format (DD-Mon-YYYY)."""
        return dt.strftime("%d-%b-%Y")

    def search_emails(
        self,
        since_date: datetime | None = None,
        before_date: datetime | None = None,
        from_email: str | None = None,
        subject_contains: str | None = None,
        unread_only: bool = False,
        raw_criteria: list[str] | None = None,
        limit: int = 50,
    ) -> list[EmailMessage]:
        """Search Gmail inbox with filters.

        Args:
            since_date: Filter emails since this date (inclusive)
            before_date: Filter emails before this date (exclusive)
            from_email: Filter by sender email address
            subject_contains: Filter by subject text (case-insensitive)
            unread_only: Only return unread emails
            raw_criteria: Raw IMAP search terms (overrides other filters)
            limit: Maximum number of emails to return

        Returns:
            List of parsed email messages

        Example:
            # Common filters
            emails = client.search_emails(unread_only=True, limit=10)

            # Advanced query with raw criteria
            emails = client.search_emails(
                raw_criteria=["LARGER", "1000000", "FLAGGED"],
                limit=20
            )
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host)
            mail.login(self.email, self.app_password)
            mail.select("inbox")

            # Build search criteria
            if raw_criteria:
                criteria = raw_criteria
            else:
                # Convert datetime to IMAP date format
                since_str = self._format_date(since_date) if since_date else None
                before_str = self._format_date(before_date) if before_date else None
                criteria = self._build_criteria(
                    since_str, before_str, from_email, subject_contains, unread_only
                )

            # Execute search
            status, messages = mail.search(None, *criteria)
            if status != "OK":
                logger.error(f"IMAP search failed with status: {status}")
                return []

            email_ids = messages[0].split()
            if not email_ids:
                return []

            # Limit results and fetch most recent first
            email_ids = email_ids[-limit:][::-1]

            results = []
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822 FLAGS)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                flags = msg_data[1].decode() if len(msg_data) > 1 else ""
                is_unread = "\\Seen" not in flags

                parsed_email = parse_email_message(raw_email, is_unread)
                results.append(parsed_email)

            mail.close()
            mail.logout()

            logger.info(f"Retrieved {len(results)} emails from Gmail")
            return results

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Failed to search emails: {e}", exc_info=True)
            raise
