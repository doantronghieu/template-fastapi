"""Gmail IMAP client for searching and retrieving emails.

Provides secure IMAP connection with flexible search capabilities:
- Common filters (date range, sender, subject, unread status)
- Raw IMAP criteria for advanced queries
"""

import imaplib
import logging
from datetime import datetime, timedelta

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
        since_date_str: str | None,
        before_date_str: str | None,
        from_email: str | None,
        subject_contains: str | None,
        unread_only: bool,
    ) -> str:
        """Build IMAP search criteria string from common filters.

        Returns single formatted string using IMAP parentheses syntax for reliability.
        Example: '(UNSEEN SINCE 01-Jan-2025 FROM "test@example.com")'

        Note: IMAP SINCE is inclusive, BEFORE is exclusive (both disregard time).
        """
        criteria_parts = []

        if unread_only:
            criteria_parts.append("UNSEEN")
        if since_date_str:
            criteria_parts.append(f"SINCE {since_date_str}")
        if before_date_str:
            criteria_parts.append(f"BEFORE {before_date_str}")
        if from_email:
            criteria_parts.append(f'FROM "{from_email}"')
        if subject_contains:
            # Escape double quotes in subject by doubling them
            escaped_subject = subject_contains.replace('"', '""')
            criteria_parts.append(f'SUBJECT "{escaped_subject}"')

        if not criteria_parts:
            return "ALL"

        # Return single string with proper IMAP format
        return "(" + " ".join(criteria_parts) + ")"

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
        raw_criteria: str | None = None,
        limit: int = 50,
    ) -> list[EmailMessage]:
        """Search Gmail inbox with filters.

        Args:
            since_date: Filter emails since this date (inclusive, entire day included)
            before_date: Filter emails before this date (inclusive, entire day included)
            from_email: Filter by sender email address
            subject_contains: Filter by subject text (case-insensitive)
            unread_only: Only return unread emails
            raw_criteria: Raw IMAP search string (overrides other filters)
            limit: Maximum number of emails to return

        Returns:
            List of parsed email messages

        Note:
            IMAP SINCE is inclusive, BEFORE is exclusive (RFC 3501).
            This method automatically adjusts before_date by adding 1 day
            to make it behave as inclusive from the user's perspective.

        Example:
            # Common filters
            emails = client.search_emails(unread_only=True, limit=10)

            # Search emails on Oct 13, 2025
            emails = client.search_emails(
                since_date=datetime(2025, 10, 13),
                before_date=datetime(2025, 10, 13),
                limit=50
            )

            # Advanced query with raw criteria
            emails = client.search_emails(
                raw_criteria='(LARGER 1000000 FLAGGED)',
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
                # Note: IMAP BEFORE is exclusive, so add 1 day to include the before_date day
                since_str = self._format_date(since_date) if since_date else None
                before_str = None
                if before_date:
                    # Add 1 day to make BEFORE exclusive of the next day (includes before_date)
                    before_date_adjusted = before_date + timedelta(days=1)
                    before_str = self._format_date(before_date_adjusted)

                criteria = self._build_criteria(
                    since_str, before_str, from_email, subject_contains, unread_only
                )

            # Execute search with single criteria string
            logger.debug(f"IMAP search criteria: {criteria}")
            status, messages = mail.search(None, criteria)
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
