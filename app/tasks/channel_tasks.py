"""Celery tasks for processing channel messages (Messenger, WhatsApp, Telegram, etc.).

Background tasks handle async processing via async_to_sync bridge:
- Facebook requires webhook responses < 20 seconds
- Processing includes: DB writes, LLM calls, API responses
- Celery decouples webhook receipt from message processing
- Uses asgiref.sync.async_to_sync with fresh engine per task
- Uses channel message handler registry for extensible AI response generation
"""

import logging
from datetime import datetime, timezone

from asgiref.sync import async_to_sync
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.celery import celery_app
from app.core.config import settings
from app.integrations.messenger import MessengerClient
from app.models import ChannelType
from app.services.handlers import channel_message_handler_registry

logger = logging.getLogger(__name__)


@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.process_messenger_message")
def process_messenger_message(
    sender_id: str, message_content: str, conversation_id: str
):
    """
    Process Facebook Messenger message with AI response (background task).

    This task is queued from webhook endpoint and executed by Celery worker.
    Handles complete message processing flow including database persistence,
    AI response generation, and sending reply via Facebook Send API.

    Args:
        sender_id: User's Page-Scoped ID (PSID) from Facebook
        message_content: User's message text (or attachment description)
        conversation_id: Conversation identifier (same as sender_id for Messenger)

    Flow:
        1. Save user message → Generate AI response → Save AI response
        2. Send AI response via Facebook Send API

    Error Handling:
        Re-raises exceptions to mark Celery task as failed (visible in Flower UI).
        Logs full stack trace for debugging.

    Note:
        Uses async_to_sync to bridge async services into sync Celery context.
        Task name must match module path for Celery auto-discovery.
    """

    @async_to_sync
    async def _process_async():
        """Async implementation called via async_to_sync bridge."""
        # Create fresh engine for this task's event loop
        # Minimal pool settings to conserve connections (Supabase free tier limit)
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            future=True,
            pool_size=1,  # Only 1 connection per task
            max_overflow=0,  # No additional connections
            connect_args={"statement_cache_size": 0},
        )
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        try:
            async with async_session_maker() as session:
                # Initialize messenger client
                messenger_client = MessengerClient(
                    page_access_token=settings.FACEBOOK_PAGE_ACCESS_TOKEN,
                    app_secret=settings.FACEBOOK_APP_SECRET,
                    graph_api_version=settings.FACEBOOK_GRAPH_API_VERSION,
                )

                try:
                    # Get appropriate channel message handler (extension or default)
                    handler = channel_message_handler_registry.get_handler()

                    # Process: Save user msg → Generate AI response → Save AI msg
                    # Handler now returns AIResponse (structured) instead of str
                    ai_response = await handler.handle_message(
                        sender_id=sender_id,
                        message_content=message_content,
                        channel_type=ChannelType.MESSENGER,
                        channel_conversation_id=conversation_id,
                        session=session,
                    )

                    # Capture timestamp AFTER message processing completes
                    # This ensures user's triggering message is already saved to DB
                    # Only messages created AFTER this point are interruptions
                    response_start_time = datetime.now(timezone.utc)

                    # Send structured multi-message response
                    from app.integrations.messenger import MessageSenderService

                    # Check if response has .messages attribute (duck typing)
                    if hasattr(ai_response, "messages"):
                        # Use MessageSenderService for multi-message sending
                        sender_service = MessageSenderService(session, messenger_client)
                        send_stats = await sender_service.send_response(
                            recipient_id=sender_id,
                            response=ai_response,
                            channel_conversation_id=conversation_id,
                            response_start_time=response_start_time,
                        )

                        logger.info(
                            f"Sent response: {send_stats['sent']}/{send_stats['total']} "
                            f"(failed: {send_stats['failed']}, interrupted: {send_stats['interrupted']})"
                        )
                    else:
                        # Fallback for string responses (backwards compatibility)
                        result = await messenger_client.send_text_message(
                            sender_id, ai_response
                        )
                        logger.info(
                            f"Message sent: sender={sender_id} msg_id={result.get('message_id')}"
                        )

                except Exception:
                    logger.error(f"Task failed for sender {sender_id}", exc_info=True)
                    raise
        finally:
            await engine.dispose()

    # Execute async code in sync context
    _process_async()


@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.send_messenger_special_message")
def send_messenger_special_message(
    sender_id: str,
    conversation_id: str,
    message_type: str,
    text: str | None = None,
    quick_replies: list[dict] | None = None,
    elements: list[dict] | None = None,
):
    """
    Send special Messenger message (quick_replies, generic_template) and save to DB.

    Formats rich message data into human-readable text for database storage,
    sends via Messenger API, and persists formatted message to conversation history.

    Args:
        sender_id: User's Page-Scoped ID (PSID)
        conversation_id: Conversation identifier
        message_type: "quick_replies" or "generic_template"
        text: Message text (for quick_replies)
        quick_replies: Quick reply buttons
        elements: Generic template elements

    Note:
        Uses format_messenger_message() to convert rich messages to readable text
        for LLM context and conversation history.
    """
    from app.integrations.messenger import format_messenger_message
    from app.models import MessageSenderRole
    from app.services.messaging_service import MessagingService

    @async_to_sync
    async def _send_special_message():
        """Async implementation for sending special messages."""
        # Create fresh engine for this task's event loop
        # Minimal pool settings to conserve connections (Supabase free tier limit)
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            future=True,
            pool_size=1,  # Only 1 connection per task
            max_overflow=0,  # No additional connections
            connect_args={"statement_cache_size": 0},
        )
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        try:
            async with async_session_maker() as session:
                messenger_client = MessengerClient(
                    page_access_token=settings.FACEBOOK_PAGE_ACCESS_TOKEN,
                    app_secret=settings.FACEBOOK_APP_SECRET,
                    graph_api_version=settings.FACEBOOK_GRAPH_API_VERSION,
                )
                messaging_service = MessagingService(session)

                try:
                    # Send message via Messenger API
                    if message_type == "quick_replies":
                        result = await messenger_client.send_quick_replies(
                            sender_id, text, quick_replies
                        )
                    elif message_type == "generic_template":
                        result = await messenger_client.send_generic_template(
                            sender_id, elements
                        )
                    else:
                        raise ValueError(f"Unsupported message_type: {message_type}")

                    logger.info(
                        f"Special message sent: sender={sender_id} type={message_type} msg_id={result.get('message_id')}"
                    )

                    # Format message for database storage
                    formatted_content = format_messenger_message(
                        message_type=message_type,
                        text=text,
                        quick_replies=quick_replies,
                        elements=elements,
                    )

                    # Save formatted message to conversation history
                    await messaging_service.create_message(
                        content=formatted_content,
                        sender_role=MessageSenderRole.AI,
                        channel_id=sender_id,
                        channel_type=ChannelType.MESSENGER,
                        channel_conversation_id=conversation_id,
                    )

                except Exception:
                    logger.error(
                        f"Failed to send special message: sender={sender_id} type={message_type}",
                        exc_info=True,
                    )
                    raise
        finally:
            await engine.dispose()

    _send_special_message()
