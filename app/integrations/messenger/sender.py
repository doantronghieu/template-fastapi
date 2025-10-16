"""Service for sending multi-message responses to Messenger.

Generic sender service that works with any response object following
the MultiMessageResponse protocol.
"""

import asyncio
import logging
from datetime import datetime
from typing import Annotated, Any, Protocol

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import SessionDep
from app.integrations.messenger.client import MessengerClient
from app.integrations.messenger.dependencies import get_messenger_client
from app.integrations.messenger.formatters import (
    format_quick_replies,
    format_template_elements,
)
from app.integrations.messenger.types import MessageType
from app.models import MessageSenderRole
from app.services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

MESSAGE_DELAY_MS = 500  # Delay between messages


class MessageProtocol(Protocol):
    """Protocol for individual message in response."""

    type: MessageType
    text: str | None
    quick_replies: list[Any] | None
    template_elements: list[Any] | None


class MultiMessageResponseProtocol(Protocol):
    """Protocol for multi-message response.

    Any response object with .messages attribute satisfies this protocol.
    Enables type-safe duck typing without inheritance coupling.
    """

    messages: list[MessageProtocol]


class MessageSenderService:
    """Send structured responses to Messenger with interruption handling.

    Generic service that works with any response following MultiMessageResponseProtocol.
    Handles:
    - Multi-message sequencing with delays
    - User interruption detection
    - Pydantic schema → Messenger API conversion
    """

    def __init__(
        self,
        session: AsyncSession,
        messenger_client: MessengerClient,
        messaging_service: MessagingService | None = None,
    ):
        self.session = session
        self.messenger_client = messenger_client
        self.messaging_service = messaging_service or MessagingService(session)

    async def send_response(
        self,
        recipient_id: str,
        response: MultiMessageResponseProtocol,
        channel_conversation_id: str,
        response_start_time: datetime,
    ) -> dict[str, any]:
        """Send multi-message response with interruption detection.

        Args:
            recipient_id: Messenger PSID
            response: Structured response (any type with .messages)
            channel_conversation_id: External channel conversation ID (e.g., Facebook PSID)
            response_start_time: When response generation started

        Returns:
            dict with success/failure stats
        """
        sent_count = 0
        failed_count = 0
        interrupted = False

        for i, message in enumerate(response.messages):
            # Check for user interruption before each send
            if await self.messaging_service.has_new_messages_since(
                channel_conversation_id=channel_conversation_id,
                since=response_start_time,
                sender_role=MessageSenderRole.CLIENT,
            ):
                logger.info(
                    f"User interrupted, stopping message sequence. "
                    f"Sent {sent_count}/{len(response.messages)}"
                )
                interrupted = True
                break

            # Send message based on type
            try:
                if message.type == MessageType.TEXT:
                    await self.messenger_client.send_text_message(
                        recipient_id, message.text
                    )

                elif message.type == MessageType.QUICK_REPLY:
                    quick_replies = format_quick_replies(message.quick_replies)
                    await self.messenger_client.send_quick_replies(
                        recipient_id, message.text, quick_replies
                    )

                elif message.type == MessageType.TEMPLATE:
                    elements = format_template_elements(message.template_elements)
                    await self.messenger_client.send_generic_template(
                        recipient_id, elements
                    )

                sent_count += 1
                logger.info(
                    f"Sent message {i + 1}/{len(response.messages)}: {message.type}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to send message {i + 1}: {message.type} - {e}",
                    exc_info=True,
                )
                failed_count += 1
                # Best-effort: Continue to next message

            # Add delay before next message (unless it's the last one)
            if i < len(response.messages) - 1:
                await asyncio.sleep(MESSAGE_DELAY_MS / 1000)

        return {
            "sent": sent_count,
            "failed": failed_count,
            "interrupted": interrupted,
            "total": len(response.messages),
        }


# Dependency injection


def get_message_sender_service(
    session: SessionDep,
    messenger_client: Annotated[MessengerClient, Depends(get_messenger_client)],
) -> MessageSenderService:
    """Provide MessageSenderService instance.

    Args:
        session: Database session
        messenger_client: Messenger API client

    Returns:
        Configured MessageSenderService instance
    """
    return MessageSenderService(session=session, messenger_client=messenger_client)


# Type alias for clean dependency injection
MessageSenderServiceDep = Annotated[
    MessageSenderService, Depends(get_message_sender_service)
]
