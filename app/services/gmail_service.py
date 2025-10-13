"""Gmail service for email operations.

Business logic layer for Gmail IMAP operations, separating concerns from API layer.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.integrations.gmail import GmailClient


class GmailService:
    """Service for Gmail operations with business logic.

    Handles date calculations, timezone conversions, and email retrieval logic.
    """

    def __init__(self, client: GmailClient):
        self.client = client
        self.vietnam_tz = ZoneInfo("Asia/Ho_Chi_Minh")

    def get_today_emails(self, limit: int = 100) -> list:
        """Get all emails received today in Vietnam timezone.

        Args:
            limit: Maximum number of emails to return

        Returns:
            List of emails received since 00:00 today (Vietnam time)
        """
        now = datetime.now(self.vietnam_tz)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.client.search_emails(since_date=today_start, limit=limit)

    def get_yesterday_emails(self, limit: int = 100) -> list:
        """Get all emails received yesterday in Vietnam timezone.

        Args:
            limit: Maximum number of emails to return

        Returns:
            List of emails received yesterday (00:00 to 23:59:59 Vietnam time)

        Note:
            IMAP BEFORE/SINCE operate on dates, not datetime. To get yesterday's
            emails, we use SINCE yesterday and BEFORE today (which excludes today).
        """
        now = datetime.now(self.vietnam_tz)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        return self.client.search_emails(
            since_date=yesterday_start, before_date=today_start, limit=limit
        )

    def get_date_range_emails(
        self, start_date: datetime, end_date: datetime | None = None, limit: int = 100
    ) -> list:
        """Get emails within a specific date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (exclusive), defaults to now
            limit: Maximum number of emails to return

        Returns:
            List of emails within the date range
        """
        return self.client.search_emails(
            since_date=start_date, before_date=end_date, limit=limit
        )
