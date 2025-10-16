"""Default channel message handler using LLMService.

Provides fallback AI response generation for channel messages when no extension
provides a handler. Uses the existing LLMService for conversation-aware responses.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.llm.base import LLMProvider
from app.models import ChannelType
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class DefaultChannelMessageHandler:
    """Default channel message handler using core LLMService.

    Used automatically when no extension registers a channel message handler.
    Provides standard AI response using configured LLM provider.
    """

    def __init__(self, llm_provider: LLMProvider):
        """Initialize with LLM provider for service instantiation.

        Args:
            llm_provider: LLM provider instance (from factory)
        """
        self.llm_provider = llm_provider

    async def handle_message(
        self,
        sender_id: str,
        message_content: str,
        channel_type: ChannelType,
        channel_conversation_id: str,
        session: AsyncSession,
    ) -> str:
        """Process message using default LLMService.

        Args:
            sender_id: Channel-specific user identifier
            message_content: User's message text
            channel_type: Source channel (MESSENGER, WHATSAPP, etc.)
            channel_conversation_id: Channel's conversation identifier
            session: Database session for persistence

        Returns:
            Generated AI response text
        """
        llm_service = LLMService(session, self.llm_provider)

        return await llm_service.process_message_and_respond(
            sender_id=sender_id,
            message_content=message_content,
            channel_type=channel_type,
            channel_conversation_id=channel_conversation_id,
        )
