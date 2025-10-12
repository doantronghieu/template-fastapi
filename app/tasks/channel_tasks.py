"""Celery tasks for processing channel messages (Messenger, WhatsApp, Telegram, etc.).

Background tasks handle async processing to meet webhook response time requirements:
- Facebook requires webhook responses < 20 seconds
- Processing includes: DB writes, LLM calls, API responses
- Celery decouples webhook receipt from message processing
"""

import asyncio
import logging

from app.core.celery import celery_app
from app.core.config import settings
from app.core.database import async_session_maker
from app.integrations.messenger import MessengerClient
from app.lib.llm.factory import get_llm_provider
from app.models import ChannelType
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.process_messenger_message")
def process_messenger_message(
    sender_id: str, message_content: str, conversation_id: str
):
    """
    Process Facebook Messenger message with AI response (async background task).

    This task is queued from webhook endpoint and executed by Celery worker.
    Handles complete message processing flow including database persistence,
    AI response generation, and sending reply via Facebook Send API.

    Args:
        sender_id: User's Page-Scoped ID (PSID) from Facebook
        message_content: User's message text (or attachment description)
        conversation_id: Conversation identifier (same as sender_id for Messenger)

    Flow:
        1. Initialize dependencies (DB session, LLM provider, Messenger client)
        2. Save user message → Generate AI response → Save AI response
        3. Send AI response via Facebook Send API
        4. Log success/failure

    Error Handling:
        Re-raises exceptions to mark Celery task as failed (visible in Flower UI).
        Logs full stack trace for debugging.

    Note:
        Uses asyncio.run() to execute async code within sync Celery task.
        Task name must match module path for Celery auto-discovery.
    """

    async def _process():
        """Inner async function to handle all async operations."""
        # Create new DB session for task (not shared with webhook handler)
        async with async_session_maker() as session:
            # Initialize dependencies (can't use FastAPI DI in Celery)
            llm_provider = get_llm_provider()
            llm_service = LLMService(session, llm_provider)
            messenger_client = MessengerClient(
                page_access_token=settings.FACEBOOK_PAGE_ACCESS_TOKEN,
                app_secret=settings.FACEBOOK_APP_SECRET,
                graph_api_version=settings.FACEBOOK_GRAPH_API_VERSION,
            )

            try:
                # Process: Save user msg → Generate AI response → Save AI msg
                ai_response = await llm_service.process_message_and_respond(
                    sender_id=sender_id,
                    message_content=message_content,
                    channel_type=ChannelType.MESSENGER,
                    channel_conversation_id=conversation_id,
                )

                # Send AI response back to user via Facebook Send API
                result = await messenger_client.send_text_message(
                    sender_id, ai_response
                )
                logger.info(
                    f"Message sent: sender={sender_id} msg_id={result.get('message_id')}"
                )

            except Exception:
                # Log full error trace for debugging
                logger.error(f"Task failed for sender {sender_id}", exc_info=True)
                # Re-raise to mark task as FAILED in Celery (don't hide errors)
                raise

    # Run async code within sync Celery task context
    asyncio.run(_process())
