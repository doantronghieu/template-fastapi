"""Omni-channel services for messaging, chat, and user operations.

Handles conversation flow, message persistence, user management,
and AI-powered responses across multiple channels.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

if TYPE_CHECKING:
    from sqlmodel import SQLModel

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import SessionDep
from app.lib.llm import InvocationMode, LLMProviderDep
from app.lib.llm.base import LLMProvider
from app.lib.llm.config import Model, ModelProvider
from app.lib.utils import async_retry
from app.services.base_crud import BaseCRUDService
from app.utils import serialize_enum

from .models import (
    ChannelType,
    Conversation,
    Message,
    MessageSenderRole,
    User,
    UserChannel,
    UserRole,
)

logger = logging.getLogger(__name__)


def load_prompt(filename: str) -> str | None:
    """Load prompt from resources/prompts directory."""
    file_path = Path(__file__).parent / "resources" / "prompts" / filename
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


# =============================================================================
# Messaging Service
# =============================================================================


class MessagingService:
    """Service for messaging operations with auto-provisioning."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _paginate_results(
        self, items: list, limit: int
    ) -> tuple[list, UUID | None, bool]:
        """Apply pagination logic to results list."""
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        next_cursor = items[-1].id if items and has_more else None
        return items, next_cursor, has_more

    def _parse_order(self, order: str, model: type["SQLModel"]) -> tuple[Any, str]:
        """Parse order string and return column with direction."""
        try:
            field, direction = order.split(".")
            if direction not in ["asc", "desc"]:
                raise ValueError("Direction must be 'asc' or 'desc'")
        except ValueError:
            raise HTTPException(
                400,
                "Invalid order format. Use 'field.direction' (e.g., 'created_at.desc')",
            )

        order_column = getattr(model, field, None)
        if order_column is None:
            raise HTTPException(400, f"Invalid order field: {field}")

        return order_column, direction

    async def _find_conversation(
        self,
        conversation_id: UUID | None = None,
        channel_conversation_id: str | None = None,
    ) -> Conversation | None:
        """Find conversation by Internal UUID or External channel conversation ID."""
        if not conversation_id and not channel_conversation_id:
            return None

        conditions = []
        if conversation_id:
            conditions.append(Conversation.id == conversation_id)
        if channel_conversation_id:
            conditions.append(
                Conversation.channel_conversation_id == channel_conversation_id
            )

        result = await self.session.execute(select(Conversation).where(*conditions))
        return result.scalar_one_or_none()

    async def _find_user_channel(
        self, channel_id: str, channel_type: ChannelType
    ) -> UserChannel | None:
        """Find UserChannel by External channel_id and channel_type."""
        result = await self.session.execute(
            select(UserChannel)
            .where(UserChannel.channel_id == channel_id)
            .where(UserChannel.channel_type == channel_type)
        )
        return result.scalar_one_or_none()

    async def has_new_messages_since(
        self,
        channel_conversation_id: str,  # External
        since: datetime,
        sender_role: MessageSenderRole | None = None,
    ) -> bool:
        """Check if new messages exist after a given timestamp."""
        stmt = (
            select(Message)
            .join(Conversation)
            .where(Conversation.channel_conversation_id == channel_conversation_id)
            .where(Message.created_at > since)
        )

        if sender_role:
            stmt = stmt.where(Message.sender_role == sender_role)

        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _create_user_with_channel(
        self, channel_id: str, channel_type: ChannelType
    ) -> User:
        """Create new user with associated External channel."""
        user = User(
            email=None,
            name=f"{channel_type.value.capitalize()} User {channel_id[-4:]}",
            role=UserRole.CLIENT.value,
            profile={},
        )
        self.session.add(user)
        await self.session.flush()

        user_channel = UserChannel(
            user_id=user.id,
            channel_id=channel_id,
            channel_type=channel_type,
            is_primary=True,
        )
        self.session.add(user_channel)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create_user_by_channel(
        self,
        channel_id: str,
        channel_type: ChannelType,
    ) -> User:
        """Find or create user by External channel ID with race condition handling."""
        user_channel = await self._find_user_channel(channel_id, channel_type)
        if user_channel:
            await self.session.refresh(user_channel, ["user"])
            return user_channel.user

        try:
            return await self._create_user_with_channel(channel_id, channel_type)
        except IntegrityError:
            await self.session.rollback()
            user_channel = await self._find_user_channel(channel_id, channel_type)
            if user_channel:
                await self.session.refresh(user_channel, ["user"])
                return user_channel.user
            raise

    def _generate_conversation_title(
        self,
        channel_conversation_id: str | None,
        channel_type: ChannelType | None,
    ) -> str:
        """Generate conversation title based on channel type."""
        if channel_conversation_id and channel_type:
            return f"Chat via {channel_type.value.capitalize()}"
        return f"Conversation {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"

    async def get_or_create_conversation(
        self,
        user_id: UUID,
        conversation_id: UUID | None = None,
        channel_conversation_id: str | None = None,
        channel_type: ChannelType | None = None,
        title: str | None = None,
        auto_create: bool = True,
    ) -> Conversation:
        """Find or create conversation with multiple lookup strategies."""
        conversation = await self._find_conversation(
            conversation_id=conversation_id,
            channel_conversation_id=channel_conversation_id,
        )

        if conversation and conversation.user_id == user_id:
            return conversation

        if not auto_create:
            raise HTTPException(404, "Conversation not found")

        if title is None:
            title = self._generate_conversation_title(
                channel_conversation_id, channel_type
            )

        conversation = Conversation(
            user_id=user_id,
            title=title,
            channel_conversation_id=channel_conversation_id,
        )
        self.session.add(conversation)

        try:
            await self.session.commit()
            await self.session.refresh(conversation)
        except IntegrityError:
            await self.session.rollback()
            if channel_conversation_id:
                result = await self.session.execute(
                    select(Conversation)
                    .where(
                        Conversation.channel_conversation_id == channel_conversation_id
                    )
                    .where(Conversation.user_id == user_id)
                )
                return result.scalar_one()
            raise

        return conversation

    async def create_message(
        self,
        content: str,
        sender_role: MessageSenderRole,
        channel_id: str | None = None,
        channel_type: ChannelType | None = None,
        channel_conversation_id: str | None = None,
        user_id: UUID | None = None,
        conversation_id: UUID | None = None,
    ) -> Message:
        """
        Create message - supports both channel and internal modes.

        Channel mode:
            Provide: channel_id, channel_type, channel_conversation_id, sender_role, content
            Auto-resolves: user_id, conversation_id

        Internal mode (API):
            Provide: user_id, conversation_id, sender_role, content
            Skip channel resolution
        """
        is_channel_mode = channel_id is not None and channel_type is not None

        if is_channel_mode:
            user = await self.get_or_create_user_by_channel(channel_id, channel_type)
            conversation = await self.get_or_create_conversation(
                user_id=user.id,
                channel_conversation_id=channel_conversation_id,
                channel_type=channel_type,
            )
            resolved_user_id = user.id
            resolved_conversation_id = conversation.id
        else:
            result = await self.session.execute(
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .where(Conversation.user_id == user_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(404, "Conversation not found or access denied")

            resolved_user_id = user_id
            resolved_conversation_id = conversation_id

        message = Message(
            conversation_id=resolved_conversation_id,
            user_id=resolved_user_id,
            sender_role=sender_role,
            content=content,
        )
        self.session.add(message)

        conversation.updated_at = datetime.now(UTC)
        self.session.add(conversation)

        await self.session.commit()
        await self.session.refresh(message)

        return message

    async def get_conversation_messages(
        self,
        conversation_id: UUID | None = None,
        channel_conversation_id: str | None = None,
        limit: int = 50,
        before_message_id: UUID | None = None,
        order: str = "created_at.desc",
        reverse: bool = True,
    ) -> tuple[Conversation, list[Message], UUID | None]:
        """Get messages for a conversation with pagination support."""
        conversation = await self._find_conversation(
            conversation_id=conversation_id,
            channel_conversation_id=channel_conversation_id,
        )
        if not conversation:
            raise HTTPException(404, "Conversation not found")

        order_column, direction = self._parse_order(order, Message)

        query = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .limit(limit + 1)
        )

        if before_message_id:
            before_msg_result = await self.session.execute(
                select(Message).where(Message.id == before_message_id)
            )
            before_msg = before_msg_result.scalar_one_or_none()
            if before_msg:
                query = query.where(Message.created_at < before_msg.created_at)

        if direction == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        result = await self.session.execute(query)
        messages: list[Message] = list(result.scalars().all())

        messages, next_cursor, _ = self._paginate_results(messages, limit)

        if reverse:
            messages.reverse()

        return conversation, messages, next_cursor

    async def get_all_conversations(
        self,
        limit: int = 50,
        cursor: UUID | None = None,
    ) -> tuple[list[dict], UUID | None, bool]:
        """Get all conversations across all users for admin view."""
        query = (
            select(Conversation)
            .options(
                selectinload(Conversation.user).selectinload(User.channels),
                selectinload(Conversation.messages).load_only(
                    Message.content,
                    Message.created_at,
                    Message.sender_role,
                ),
            )
            .order_by(Conversation.updated_at.desc())
            .limit(limit + 1)
        )

        if cursor:
            cursor_conv_result = await self.session.execute(
                select(Conversation).where(Conversation.id == cursor)
            )
            cursor_conv = cursor_conv_result.scalar_one_or_none()
            if cursor_conv:
                query = query.where(Conversation.updated_at < cursor_conv.updated_at)

        result = await self.session.execute(query)
        conversations: list[Conversation] = list(result.scalars().all())

        conversations, next_cursor, has_more = self._paginate_results(
            conversations, limit
        )

        formatted_conversations = []
        for conv in conversations:
            last_message = (
                max(conv.messages, key=lambda m: m.created_at)
                if conv.messages
                else None
            )

            user_channels = sorted(
                conv.user.channels, key=lambda c: c.is_primary, reverse=True
            )
            user_channel = user_channels[0] if user_channels else None

            formatted_conversations.append(
                {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "ai_summary": conv.ai_summary,
                    "ai_summary_updated_at": conv.ai_summary_updated_at,
                    "user": {
                        "id": conv.user.id,
                        "name": conv.user.name,
                        "role": conv.user.role,
                    },
                    "channel_type": user_channel.channel_type if user_channel else None,
                    "last_message": (
                        {
                            "content": last_message.content,
                            "created_at": last_message.created_at,
                            "sender_role": serialize_enum(last_message.sender_role),
                        }
                        if last_message
                        else None
                    ),
                }
            )

        return formatted_conversations, next_cursor, has_more

    async def get_user_conversations(
        self,
        user_id: UUID,
    ) -> list[dict]:
        """Get all conversations for a user with full details."""
        query = (
            select(Conversation)
            .options(
                selectinload(Conversation.user).selectinload(User.channels),
                selectinload(Conversation.messages).load_only(
                    Message.content,
                    Message.created_at,
                    Message.sender_role,
                ),
            )
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )

        result = await self.session.execute(query)
        conversations: list[Conversation] = list(result.scalars().all())

        formatted_conversations = []
        for conv in conversations:
            last_message = (
                max(conv.messages, key=lambda m: m.created_at)
                if conv.messages
                else None
            )

            user_channels = sorted(
                conv.user.channels, key=lambda c: c.is_primary, reverse=True
            )
            user_channel = user_channels[0] if user_channels else None

            formatted_conversations.append(
                {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "ai_summary": conv.ai_summary,
                    "ai_summary_updated_at": conv.ai_summary_updated_at,
                    "user": {
                        "id": conv.user.id,
                        "name": conv.user.name,
                        "role": conv.user.role,
                    },
                    "channel_type": user_channel.channel_type if user_channel else None,
                    "last_message": (
                        {
                            "content": last_message.content,
                            "created_at": last_message.created_at,
                            "sender_role": serialize_enum(last_message.sender_role),
                        }
                        if last_message
                        else None
                    ),
                }
            )

        return formatted_conversations


async def get_messaging_service(session: SessionDep) -> MessagingService:
    """Provide MessagingService instance."""
    return MessagingService(session)


MessagingServiceDep = Annotated[MessagingService, Depends(get_messaging_service)]


# =============================================================================
# Chat Service
# =============================================================================


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


# =============================================================================
# User Service
# =============================================================================


class UserService(BaseCRUDService[User]):
    """Service for user-related operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_user_details(self, user_id: UUID) -> User:
        """Get full user details with channels eagerly loaded. Raises 404 if not found."""
        result = await self.session.execute(
            select(User).options(selectinload(User.channels)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address. Returns None if not found."""
        return await self.get_by_field({"email": email})


async def get_user_service(session: SessionDep) -> UserService:
    """Provide UserService instance."""
    return UserService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


__all__ = [
    "MessagingService",
    "MessagingServiceDep",
    "get_messaging_service",
    "ChatService",
    "ChatServiceDep",
    "get_chat_service",
    "UserService",
    "UserServiceDep",
    "get_user_service",
    "load_prompt",
    "DEFAULT_SYSTEM_PROMPT",
]
