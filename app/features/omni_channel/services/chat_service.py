"""Chat service for AI-powered conversation responses.

Orchestrates conversation flow:
1. Retrieves conversation history from database
2. Formats context for LLM (system prompt + history + current query)
3. Generates AI response with retry logic
4. Saves messages to database
"""

import logging
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import SessionDep
from app.lib.llm import InvocationMode, LLMProviderDep
from app.lib.llm.base import LLMProvider
from app.lib.llm.config import Model, ModelProvider
from app.lib.utils import async_retry

from ..models import ChannelType, MessageSenderRole
from .messaging_service import MessagingService

logger = logging.getLogger(__name__)


def load_prompt(filename: str) -> str | None:
    """Load prompt from prompts directory."""
    file_path = Path(__file__).parent.parent / "prompts" / filename
    if file_path.exists():
        return file_path.read_text().strip()
    return None


# Default system prompt if file not found
DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant having a text conversation with a user.
Keep your responses conversational, friendly, and concise (under 2000 characters).
Do not use markdown formatting - write naturally as you would in a text message.
If you need to list things, use simple bullet points with hyphens.
Always be helpful, respectful, and aim to provide clear answers to user questions.

Important context notes:
- When you see "[User sent an image]", acknowledge that you cannot view images and ask the user to describe what they need help with.
- When you see "[User sent a file: filename]", let the user know you cannot process attachments and ask them to send their question as text."""


class ChatService:
    """Service for generating AI responses to user messages.

    Handles complete conversation flow including message persistence,
    context retrieval, LLM invocation, and retry logic.
    """

    def __init__(self, session: AsyncSession, llm_provider: LLMProvider):
        self.session = session
        self.llm_provider = llm_provider
        self.messaging_service = MessagingService(session)
        self._system_prompt = load_prompt("system.md") or DEFAULT_SYSTEM_PROMPT

    async def _get_conversation_history(
        self, conversation_id: UUID, limit: int = 50
    ) -> list[dict]:
        """Retrieve latest N messages from conversation history formatted for LLM."""
        _, messages, _ = await self.messaging_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            order="created_at.desc",  # Get latest messages first
            reverse=True,  # Reverse to chronological order (oldest → newest)
        )

        return [
            {
                "role": "assistant"
                if msg.sender_role == MessageSenderRole.AI
                else "user",
                "content": msg.content,
            }
            for msg in messages
        ]

    @async_retry(max_retries=3, exceptions=(Exception,))
    async def generate_response(self, conversation_id: UUID) -> str:
        """Generate AI response based on conversation history with automatic retry."""
        history = await self._get_conversation_history(conversation_id)

        current_query = history[-1]["content"] if history else ""
        history_text = "\n".join(
            f"<{msg['role'].upper()}>\n{msg['content']}\n</{msg['role'].upper()}>"
            for msg in history[:-1]
        )

        prompt_text = f"""<SYSTEM>
{self._system_prompt}
</SYSTEM>

<HISTORY>
{history_text or "(No previous conversation)"}
</HISTORY>

<CURRENT_USER_QUERY>
{current_query}
</CURRENT_USER_QUERY>

Please respond to the user's current query based on the conversation history and system instructions."""

        return await self.llm_provider.invoke_model(
            prompt=prompt_text,
            mode=InvocationMode.INVOKE.value,
            model_name=Model.GPT_OSS_120B,
            model_provider=ModelProvider.GROQ,
            temperature=0.0,
        )

    async def process_message_and_respond(
        self,
        sender_id: Annotated[
            str, "Channel-specific user ID (e.g., PSID for Messenger)"
        ],
        message_content: str,
        channel_type: ChannelType,
        channel_conversation_id: Annotated[str, "Channel's conversation identifier"],
    ) -> str:
        """Process incoming message, save to DB, generate and save AI response."""
        # Save user message (auto-creates user/conversation if first interaction)
        user_message = await self.messaging_service.create_message(
            content=message_content,
            sender_role=MessageSenderRole.CLIENT,
            channel_id=sender_id,
            channel_type=channel_type,
            channel_conversation_id=channel_conversation_id,
        )

        ai_response_text = await self.generate_response(
            conversation_id=user_message.conversation_id,
        )

        await self.messaging_service.create_message(
            content=ai_response_text,
            sender_role=MessageSenderRole.AI,
            user_id=user_message.user_id,
            conversation_id=user_message.conversation_id,
        )

        return ai_response_text


async def get_chat_service(
    session: SessionDep, llm_provider: LLMProviderDep
) -> ChatService:
    """Provide ChatService instance with injected dependencies."""
    return ChatService(session, llm_provider)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
