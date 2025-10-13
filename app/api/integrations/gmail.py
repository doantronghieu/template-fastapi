"""Gmail integration API endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import verify_api_key
from app.integrations.gmail import GmailClientDep
from app.schemas.gmail import EmailListResponse, EmailResponse, EmailSearchRequest
from app.services.gmail_service import GmailServiceDep

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _to_email_list_response(emails: list) -> EmailListResponse:
    """Convert raw email list to EmailListResponse with count."""
    email_responses = [EmailResponse(**email) for email in emails]
    return EmailListResponse(count=len(email_responses), items=email_responses)


@router.post("/search", response_model=EmailListResponse)
async def search_emails(
    filters: EmailSearchRequest, client: GmailClientDep
) -> EmailListResponse:
    """Search Gmail inbox with flexible filters.

    Supports two modes:
    1. Common filters: Use date range, sender, subject, unread status
    2. Advanced: Provide raw IMAP search criteria

    Examples:
        # Simple search for unread emails
        {"unread_only": true, "limit": 10}

        # Search by date and sender
        {"since_date": "2024-10-01T00:00:00Z", "from_email": "john@example.com"}

        # Advanced: Raw IMAP criteria
        {"raw_criteria": ["LARGER", "1000000", "FLAGGED"], "limit": 20}
    """
    emails = client.search_emails(**filters.model_dump())
    return _to_email_list_response(emails)


@router.get("/today", response_model=EmailListResponse)
async def get_today_emails(
    service: GmailServiceDep, limit: int = Query(default=200, ge=1, le=200)
) -> EmailListResponse:
    """Get all emails received today in Vietnam timezone (UTC+7).

    Automatically calculates start of day in Vietnam time and fetches all emails
    since then. Useful for daily email monitoring and processing.

    Args:
        limit: Maximum number of emails to return (default: 200, max: 200)

    Returns:
        Email list with count of emails received today in Vietnam timezone
    """
    emails = service.get_today_emails(limit=limit)
    return _to_email_list_response(emails)


@router.get("/yesterday", response_model=EmailListResponse)
async def get_yesterday_emails(
    service: GmailServiceDep, limit: int = Query(default=200, ge=1, le=200)
) -> EmailListResponse:
    """Get all emails received yesterday in Vietnam timezone (UTC+7).

    Automatically calculates yesterday's date range (00:00 to 23:59:59) in Vietnam
    time and fetches all emails from that period. Useful for daily reports and
    retrospective analysis.

    Args:
        limit: Maximum number of emails to return (default: 200, max: 200)

    Returns:
        Email list with count of emails received yesterday in Vietnam timezone
    """
    emails = service.get_yesterday_emails(limit=limit)
    return _to_email_list_response(emails)
