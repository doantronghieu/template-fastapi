"""LLM service for AI-powered conversation responses.

Orchestrates conversation flow:
1. Retrieves conversation history from database
2. Formats context for LLM (system prompt + history + current query)
3. Generates AI response with retry logic
4. Saves messages to database

Supports multiple messaging channels (Messenger, WhatsApp, Telegram, etc.)
through channel-agnostic message handling.
"""

import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import SessionDep
from app.lib.llm import InvocationMode, LLMProviderDep
from app.lib.llm.base import LLMProvider
from app.lib.llm.config import Model, ModelProvider
from app.lib.utils import async_retry
from app.models import ChannelType, MessageSenderRole
from app.services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

# System prompt defining AI assistant behavior and constraints
SYSTEM_PROMPT = """You are a helpful AI assistant having a text conversation with a user.
Keep your responses conversational, friendly, and concise (under 2000 characters).
Do not use markdown formatting - write naturally as you would in a text message.
If you need to list things, use simple bullet points with hyphens.
Always be helpful, respectful, and aim to provide clear answers to user questions.

Important context notes:
- When you see "[User sent an image]", acknowledge that you cannot view images and ask the user to describe what they need help with.
- When you see "[User sent a file: filename]", let the user know you cannot process attachments and ask them to send their question as text."""


class LLMService:
    """
    Service for generating AI responses to user messages.

    Handles complete conversation flow including:
    - Message persistence (save user/AI messages)
    - Context retrieval (conversation history)
    - LLM invocation (generate responses)
    - Retry logic (handle transient failures)

    Works with any LLM provider through abstraction layer.
    """

    def __init__(self, session: AsyncSession, llm_provider: LLMProvider):
        self.session = session
        self.llm_provider = llm_provider
        self.messaging_service = MessagingService(session)

    async def _get_conversation_history(
        self, conversation_id, limit: int = 50
    ) -> list[dict]:
        """
        Retrieve latest N messages from conversation history formatted for LLM.

        Args:
            conversation_id: Conversation UUID
            limit: Maximum number of messages to retrieve (default: 50)

        Returns:
            List of messages in chronological order (oldest to newest)
            Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Implementation Detail:
            Fetches LATEST 50 messages using DESC order (newest first from DB),
            then reverses to chronological ASC (oldest first for LLM context).
            This ensures LLM receives most recent conversation context.

        Why Latest 50:
            Provides sufficient context while staying within LLM token limits.
            Older messages beyond 50 are excluded to prevent context overflow.
        """
        _, messages, _ = await self.messaging_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            order="created_at.desc",  # Get latest messages first
            reverse=True,  # Then reverse to chronological order (oldest → newest)
        )

        # Format messages with roles recognized by LLM
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
    async def generate_response(self, conversation_id) -> str:
        """
        Generate AI response based on conversation history with automatic retry.

        Args:
            conversation_id: Conversation UUID for context

        Returns:
            str: Generated AI response text

        Raises:
            Exception: Re-raised on final retry failure with full stack trace

        Flow:
            1. Fetch conversation history (includes latest user message)
            2. Format as plain string with XML-like sections
            3. Invoke LLM with exponential backoff retry
            4. Return generated response

        Prompt Format:
            Uses plain string (not message list) with sections:
            - <SYSTEM>: AI behavior instructions
            - <HISTORY>: Previous conversation (excluding current query)
            - <CURRENT_USER_QUERY>: Latest user message

        Note:
            Automatically retries with exponential backoff on any exception.
            Plain string format used instead of message list for model compatibility.
        """
        # Get conversation history (includes latest user message from DB)
        history = await self._get_conversation_history(conversation_id)

        # Extract current query and build history text
        current_query = history[-1]["content"] if history else ""
        history_text = "\n".join(
            f"<{msg['role'].upper()}>\n{msg['content']}\n</{msg['role'].upper()}>"
            for msg in history[:-1]
        )

        # Format complete prompt with XML-like structure
        prompt_text = f"""<SYSTEM>
{SYSTEM_PROMPT}
</SYSTEM>

<HISTORY>
{history_text or "(No previous conversation)"}
</HISTORY>

<CURRENT_USER_QUERY>
{current_query}
</CURRENT_USER_QUERY>

Please respond to the user's current query based on the conversation history and system instructions."""

        # Invoke LLM (retry handled by decorator)
        return await self.llm_provider.invoke_model(
            prompt=prompt_text,
            mode=InvocationMode.INVOKE.value,
            model_name=Model.GPT_OSS_120B,
            model_provider=ModelProvider.GROQ,
            temperature=0.0,  # Deterministic responses
        )

    async def process_message_and_respond(
        self,
        sender_id: str,
        message_content: str,
        channel_type: ChannelType,
        channel_conversation_id: str,
    ) -> str:
        """
        Process incoming message, save to DB, generate and save AI response.

        Complete message processing flow:
            1. Save user message to database
               - Auto-creates user if first message
               - Auto-creates conversation if needed
            2. Generate AI response using conversation history
            3. Save AI response to database
            4. Return AI response text (for sending via channel)

        Args:
            sender_id: Channel-specific user ID (e.g., PSID for Messenger)
            message_content: User's message text
            channel_type: Source channel (MESSENGER, WHATSAPP, etc.)
            channel_conversation_id: Channel's conversation identifier

        Returns:
            str: Generated AI response text ready for sending

        Note:
            This is the main entry point for message processing.
            All persistence and AI generation happens here before
            response is sent back via channel client.
        """
        # Save user message (auto-creates user/conversation if first interaction)
        user_message = await self.messaging_service.create_message(
            content=message_content,
            sender_role=MessageSenderRole.CLIENT,
            channel_id=sender_id,
            channel_type=channel_type,
            channel_conversation_id=channel_conversation_id,
        )

        # Generate AI response based on full conversation history
        ai_response_text = await self.generate_response(
            conversation_id=user_message.conversation_id,
        )

        # Persist AI response to database for history tracking
        await self.messaging_service.create_message(
            content=ai_response_text,
            sender_role=MessageSenderRole.AI,
            user_id=user_message.user_id,
            conversation_id=user_message.conversation_id,
        )

        return ai_response_text


# Dependency provider
async def get_llm_service(
    session: SessionDep, llm_provider: LLMProviderDep
) -> LLMService:
    """
    Provide LLMService instance with database and LLM provider dependencies.

    Args:
        session: Async database session for message persistence
        llm_provider: LLM provider (e.g., LangChain, LiteLLM)

    Returns:
        LLMService: Initialized service instance
    """
    return LLMService(session, llm_provider)


# Type alias for cleaner endpoint signatures
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
