"""Messenger API endpoints for sending messages."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.integrations.messenger import MessengerClientDep

router = APIRouter()
logger = logging.getLogger(__name__)


class SendMessageRequest(BaseModel):
    """Send a message to a Messenger user."""

    recipient_id: str = Field(..., description="Facebook Page-Scoped ID (PSID)")
    text: str = Field(..., max_length=2000, description="Message text to send")


class SendMessageResponse(BaseModel):
    """Response from sending a message."""

    recipient_id: str
    message_id: str


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    messenger_client: MessengerClientDep,
):
    """
    Send a text message to a Messenger user.

    Args:
        request: Message content and recipient
        messenger_client: Messenger client instance

    Returns:
        SendMessageResponse: Confirmation with recipient_id and message_id

    Raises:
        HTTPException: If message sending fails

    Note:
        Automatically retries with exponential backoff (1s, 2s, 4s) on HTTP errors.
    """
    result = await messenger_client.send_text_message(
        request.recipient_id, request.text
    )

    logger.info(
        f"Message sent: recipient={request.recipient_id} msg_id={result['message_id']}"
    )

    return SendMessageResponse(
        recipient_id=request.recipient_id,
        message_id=result["message_id"],
    )
