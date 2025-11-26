"""Facebook Messenger webhook endpoints.

Handles webhook verification and incoming message events from Facebook Messenger.
Implements security verification, rate limiting, and asynchronous message processing.
"""

import logging

from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.services.rate_limiter import RateLimiterDep
from app.tasks.channel_tasks import process_messenger_message

from .config import messenger_settings
from .dependencies import MessengerClientDep
from .utils.webhook_parser import format_messenger_message, parse_webhook_payload

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", include_in_schema=False)
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
):
    """
    Webhook verification endpoint for Facebook Messenger.

    Facebook calls this during webhook setup to verify ownership.
    Must echo back the challenge parameter if verification token matches.

    Flow:
        1. Facebook sends GET request with mode, token, challenge
        2. Verify token matches configured FACEBOOK_VERIFY_TOKEN
        3. Return challenge as integer to confirm ownership

    Returns:
        challenge (int): Numeric challenge to confirm webhook ownership

    Raises:
        HTTPException: 403 if verification token doesn't match
    """
    if mode == "subscribe" and token == messenger_settings.FACEBOOK_VERIFY_TOKEN:
        return int(challenge)

    logger.warning(f"Webhook verify failed: mode={mode}")
    raise HTTPException(403, "Verification token mismatch")


@router.post("/")
async def receive_webhook(
    request: Request,
    messenger_client: MessengerClientDep,
    rate_limiter: RateLimiterDep,
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
):
    """
    Receive and process incoming messages from Facebook Messenger.

    Flow:
        1. Verify HMAC SHA256 signature (prevents unauthorized requests)
        2. Parse JSON payload into message events
        3. Check rate limit per user (prevents spam/abuse)
        4. Queue Celery task for async processing
        5. Return 200 OK immediately (Facebook requires <20s response)

    Background processing (via Celery):
        - Save user message to database
        - Generate response
        - Send response back via Facebook Send API

    Returns:
        dict: Status confirmation with number of events processed

    Raises:
        HTTPException: 403 if signature invalid, 400 if JSON malformed
    """
    body = await request.body()

    # Security: Verify HMAC SHA256 signature using app secret
    if not messenger_client.verify_webhook_signature(body, x_hub_signature_256 or ""):
        logger.warning("Invalid signature")
        raise HTTPException(403, "Invalid signature")

    # Parse JSON payload (validated against TypedDict structure)
    try:
        data = await request.json()
    except Exception:
        logger.error("Invalid JSON payload", exc_info=True)
        raise HTTPException(400, "Invalid JSON payload")

    # Extract normalized message events from nested Facebook structure
    events = parse_webhook_payload(data)
    if not events:
        return {"status": "ok"}

    # Process each event (message or postback)
    for event in events:
        sender_id = event["sender_id"]
        conversation_id = event["conversation_id"]
        event_type = event["event_type"]

        # Rate limiting: Prevent spam/abuse (sliding window via Redis)
        within_limit = await rate_limiter.check_rate_limit(
            sender_id, messenger_settings.FACEBOOK_RATE_LIMIT_MESSAGES_PER_MINUTE
        )

        if not within_limit:
            logger.warning(f"Rate limited: sender={sender_id}")
            # Send immediate response (not queued) to inform user
            await messenger_client.send_text_message(
                sender_id,
                "You're sending messages too quickly. Please wait a moment.",
            )
            continue

        # Process based on event type
        if event_type == "message":
            message_text = event["message_text"]
            # Queue background task for text message processing
            task_result = process_messenger_message.delay(
                sender_id, message_text, conversation_id
            )
            logger.info(
                f"Queued message task: sender={sender_id} task_id={task_result.id}"
            )

        elif event_type == "postback":
            # Format postback event for database storage
            formatted_text = format_messenger_message(
                message_type="postback",
                title=event.get("title", ""),
                payload=event.get("payload", ""),
            )
            # Queue background task with formatted postback text
            task_result = process_messenger_message.delay(
                sender_id, formatted_text, conversation_id
            )
            logger.info(
                f"Queued postback task: sender={sender_id} payload={event.get('payload')} task_id={task_result.id}"
            )

    return {"status": "ok", "events_processed": len(events)}
