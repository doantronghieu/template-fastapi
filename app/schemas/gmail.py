"""Pydantic schemas for Gmail API endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class EmailSearchRequest(BaseModel):
    """Request schema for email search with hybrid filters.

    Supports common filters for ease-of-use and raw IMAP criteria for power users.
    If raw_criteria is provided, it overrides other filter parameters.
    """

    # Common filters
    since_date: datetime | None = Field(
        default=None,
        description="Filter emails since this date (inclusive, entire day included)",
    )
    before_date: datetime | None = Field(
        default=None,
        description="Filter emails before this date (inclusive, entire day included)",
    )
    from_email: str | None = Field(
        default=None, description="Filter by sender email address"
    )
    subject_contains: str | None = Field(
        default=None, description="Filter by subject text (case-insensitive)"
    )
    unread_only: bool = Field(default=False, description="Only return unread emails")

    # Advanced filter
    raw_criteria: str | None = Field(
        default=None,
        description="Raw IMAP search criteria string (overrides other filters if provided)",
        examples=[
            "UNSEEN",
            '(FROM "john@example.com" SINCE 01-Oct-2024)',
            "(LARGER 1000000 FLAGGED)",
        ],
    )

    limit: int = Field(default=50, ge=1, le=100, description="Maximum emails to return")


class EmailAddressResponse(BaseModel):
    """Email address with optional display name."""

    name: str | None = Field(default=None, description="Display name")
    email: str = Field(description="Email address")


class EmailResponse(BaseModel):
    """Parsed email message response."""

    message_id: str = Field(description="Unique message identifier")
    subject: str = Field(description="Email subject")
    from_: EmailAddressResponse = Field(alias="from", description="Sender address")
    to: list[EmailAddressResponse] = Field(description="Recipient addresses")
    date: str = Field(description="Email date header")
    body_text: str | None = Field(default=None, description="Plain text body content")
    body_html: str | None = Field(default=None, description="HTML body content")
    is_unread: bool = Field(description="Whether email is unread")

    class Config:
        populate_by_name = True


class EmailListResponse(BaseModel):
    """Response schema for email list endpoints with count."""

    items: list[EmailResponse] = Field(description="List of email messages")
    count: int = Field(description="Number of emails returned in this response")
