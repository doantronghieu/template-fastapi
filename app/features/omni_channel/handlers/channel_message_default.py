"""Default channel message handler using ChatService.

Provides fallback AI response generation for channel messages when no extension provides a handler.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.llm.base import LLMProvider

from ..models import ChannelType
from ..services.chat_service import ChatService

logger = logging.getLogger(__name__)


class DefaultChannelMessageHandler:
    """Default channel message handler using core ChatService.

    Used automatically when no extension registers a channel message handler.
    Provides standard AI response using configured LLM provider.
    """

    def __init__(self, llm_provider: LLMProvider):
        """Initialize with LLM provider for service instantiation."""
        self.llm_provider = llm_provider

    async def handle_message(
        self,
        sender_id: str,  # Channel-specific user identifier
        message_content: str,
        channel_type: ChannelType,
        channel_conversation_id: str,
        session: AsyncSession,
    ) -> str:
        """Process message using default ChatService."""
        chat_service = ChatService(session, self.llm_provider)

        return await chat_service.process_message_and_respond(
            sender_id=sender_id,
            message_content=message_content,
            channel_type=channel_type,
            channel_conversation_id=channel_conversation_id,
        )
