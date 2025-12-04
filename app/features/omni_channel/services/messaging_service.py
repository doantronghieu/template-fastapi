"""Messaging service for conversation and message operations."""

from datetime import UTC, datetime
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
from app.utils import serialize_enum

from ..models import (
    ChannelType,
    Conversation,
    Message,
    MessageSenderRole,
    User,
    UserChannel,
    UserRole,
)


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
