"""Messenger API endpoints for sending messages."""

import logging

from fastapi import APIRouter

from .dependencies import MessengerClientDep
from .schemas.api import (
    SendGenericTemplateRequest,
    SendMessageRequest,
    SendMessageResponse,
    SendQuickRepliesRequest,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    messenger_client: MessengerClientDep,
):
    """
    Send a text message to a Messenger user.

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


@router.post("/send-quick-replies", response_model=SendMessageResponse)
async def send_quick_replies(
    request: SendQuickRepliesRequest,
    messenger_client: MessengerClientDep,
):
    """
    Send a text message with quick reply buttons.

    Quick replies are temporary buttons that appear above the composer.
    They disappear after the user taps one, making them ideal for
    context-specific choices.

    Note:
        - Max 13 quick replies per message
        - Button titles: 20 character limit
        - Automatically retries with exponential backoff on HTTP errors
    """
    # Convert Pydantic models to dicts for client
    quick_replies_dict = [
        qr.model_dump(exclude_none=True) for qr in request.quick_replies
    ]

    result = await messenger_client.send_quick_replies(
        request.recipient_id, request.text, quick_replies_dict
    )

    logger.info(
        f"Quick replies sent: recipient={request.recipient_id} msg_id={result['message_id']}"
    )

    return SendMessageResponse(
        recipient_id=request.recipient_id,
        message_id=result["message_id"],
    )


@router.post("/send-generic-template", response_model=SendMessageResponse)
async def send_generic_template(
    request: SendGenericTemplateRequest,
    messenger_client: MessengerClientDep,
):
    """
    Send a generic template (single card or carousel).

    Generic templates display rich cards with images, titles, subtitles, and buttons.
    Multiple elements create a horizontally scrollable carousel.

    Note:
        - 1-10 elements (single card or carousel)
        - Element titles: 80 character limit
        - Element subtitles: 80 character limit
        - Max 3 buttons per element
        - Button titles: 20 character limit
        - Automatically retries with exponential backoff on HTTP errors
    """
    # Convert Pydantic models to dicts for client
    elements_dict = [elem.model_dump(exclude_none=True) for elem in request.elements]

    result = await messenger_client.send_generic_template(
        request.recipient_id, elements_dict
    )

    logger.info(
        f"Generic template sent: recipient={request.recipient_id} elements={len(request.elements)} msg_id={result['message_id']}"
    )

    return SendMessageResponse(
        recipient_id=request.recipient_id,
        message_id=result["message_id"],
    )
