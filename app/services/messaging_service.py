"""Messaging service for conversation and message operations."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import SessionDep
from app.models import (
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

    async def _find_conversation(
        self,
        conversation_id: UUID | None = None,
        channel_conversation_id: str | None = None,
    ) -> Conversation | None:
        """
        Find conversation by UUID or channel ID.

        Args:
            conversation_id: Internal conversation UUID
            channel_conversation_id: External conversation identifier

        Returns:
            Conversation if found, None otherwise
        """
        if conversation_id:
            result = await self.session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            return result.scalar_one_or_none()

        if channel_conversation_id:
            result = await self.session.execute(
                select(Conversation).where(
                    Conversation.channel_conversation_id == channel_conversation_id
                )
            )
            return result.scalar_one_or_none()

        return None

    async def _find_user_channel(
        self, channel_id: str, channel_type: ChannelType
    ) -> UserChannel | None:
        """
        Find UserChannel by channel_id and channel_type.

        Args:
            channel_id: External channel identifier
            channel_type: Channel platform type

        Returns:
            UserChannel if found, None otherwise
        """
        result = await self.session.execute(
            select(UserChannel)
            .where(UserChannel.channel_id == channel_id)
            .where(UserChannel.channel_type == channel_type)
        )
        return result.scalar_one_or_none()

    async def _create_user_with_channel(
        self, channel_id: str, channel_type: ChannelType
    ) -> User:
        """
        Create new user with associated channel.

        Args:
            channel_id: External channel identifier
            channel_type: Channel platform type

        Returns:
            Newly created User

        Raises:
            IntegrityError: If race condition occurs (handled by caller)
        """
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
        """
        Find or create user by channel ID with race condition handling.

        Args:
            channel_id: External channel identifier
            channel_type: Channel platform type

        Returns:
            User linked to the channel
        """
        # Check if user channel exists
        user_channel = await self._find_user_channel(channel_id, channel_type)
        if user_channel:
            await self.session.refresh(user_channel, ["user"])
            return user_channel.user

        # Create new user with channel
        try:
            return await self._create_user_with_channel(channel_id, channel_type)
        except IntegrityError:
            # Race condition: user_channel created by another request
            await self.session.rollback()
            user_channel = await self._find_user_channel(channel_id, channel_type)
            if user_channel:
                await self.session.refresh(user_channel, ["user"])
                return user_channel.user
            raise  # Re-raise if still not found (unexpected)

    def _generate_conversation_title(
        self,
        channel_conversation_id: str | None,
        channel_type: ChannelType | None,
    ) -> str:
        """
        Generate conversation title based on channel type.

        Args:
            channel_conversation_id: External conversation identifier
            channel_type: Channel platform type

        Returns:
            Generated title string
        """
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
        """
        Find or create conversation with multiple lookup strategies.

        Priority:
        1. If conversation_id: lookup by UUID (internal conversation)
        2. If channel_conversation_id: lookup/create by channel ID
        3. If auto_create=True: create new conversation
        4. Else: raise HTTPException(404)

        Args:
            user_id: User who owns the conversation
            conversation_id: Internal UUID (for direct conversations)
            channel_conversation_id: External channel identifier
            channel_type: Channel type (for auto-generated title)
            title: Explicit title (overrides auto-generation)
            auto_create: Whether to create if not found

        Returns:
            Conversation instance

        Raises:
            HTTPException: 404 if not found and auto_create=False
        """
        # Try to find existing conversation
        conversation = await self._find_conversation(
            conversation_id=conversation_id,
            channel_conversation_id=channel_conversation_id,
        )

        # If found and belongs to user, return it
        if conversation and conversation.user_id == user_id:
            return conversation

        # If not found and auto_create is False, raise 404
        if not auto_create:
            raise HTTPException(404, "Conversation not found")

        # Generate title if not provided
        if title is None:
            title = self._generate_conversation_title(
                channel_conversation_id, channel_type
            )

        # Create new conversation
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
            # Race condition: conversation created by another request
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
        # Channel mode parameters
        channel_id: str | None = None,
        channel_type: ChannelType | None = None,
        channel_conversation_id: str | None = None,
        # Internal mode parameters
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

        Args:
            content: Message content
            sender_role: Who sent the message (client/ai/admin)
            channel_id: External channel identifier (Telegram chat ID, etc.)
            channel_type: Channel platform type
            channel_conversation_id: External conversation identifier
            user_id: User UUID (for internal mode)
            conversation_id: Conversation UUID (for internal mode)

        Returns:
            Created message

        Raises:
            HTTPException: 400 if required parameters missing, 404 if conversation not found
        """
        # Determine mode (validation already done at schema level)
        is_channel_mode = channel_id is not None and channel_type is not None

        # Channel mode: resolve user and conversation
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
            # Internal mode: validate ownership
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

        # Create message
        message = Message(
            conversation_id=resolved_conversation_id,
            user_id=resolved_user_id,
            sender_role=sender_role,
            content=content,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)

        return message

    async def get_conversation_messages(
        self,
        conversation_id: UUID | None = None,
        channel_conversation_id: str | None = None,
        limit: int = 20,
        order: str = "created_at.desc",
        reverse: bool = False,
    ) -> tuple[Conversation, list[Message]]:
        """
        Get messages for a conversation with sorting options.

        Args:
            conversation_id: Internal conversation UUID
            channel_conversation_id: External conversation identifier
            limit: Maximum number of messages to return
            order: Sort order in format "field.direction" (e.g., "created_at.desc")
            reverse: Whether to reverse the final result order

        Returns:
            Tuple of (conversation, messages_list)

        Raises:
            HTTPException: 404 if conversation not found, 400 if invalid order format
        """
        # Find conversation using extracted method
        conversation = await self._find_conversation(
            conversation_id=conversation_id,
            channel_conversation_id=channel_conversation_id,
        )
        if not conversation:
            raise HTTPException(404, "Conversation not found")

        # Parse order parameter
        try:
            field, direction = order.split(".")
            if direction not in ["asc", "desc"]:
                raise ValueError("Direction must be 'asc' or 'desc'")
        except ValueError:
            raise HTTPException(
                400,
                "Invalid order format. Use 'field.direction' (e.g., 'created_at.desc')",
            )

        # Build query with ordering
        order_column = getattr(Message, field, None)
        if order_column is None:
            raise HTTPException(400, f"Invalid order field: {field}")

        query = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .limit(limit)
        )

        if direction == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        result = await self.session.execute(query)
        messages = list(result.scalars().all())

        # Apply reverse if requested
        if reverse:
            messages.reverse()

        return conversation, messages

    async def get_user_conversations(
        self,
        user_id: UUID,
    ) -> list[dict]:
        """
        Get all conversations for a user with message counts.

        Args:
            user_id: User UUID

        Returns:
            List of conversation dicts with message_count field
        """
        # Query conversations with message count
        query = (
            select(
                Conversation,
                func.count(Message.id).label("message_count"),
            )
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
            .group_by(Conversation.id)
            .order_by(Conversation.updated_at.desc())
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Format response
        conversations = []
        for conversation, message_count in rows:
            conversations.append(
                {
                    "id": conversation.id,
                    "created_at": conversation.created_at,
                    "updated_at": conversation.updated_at,
                    "title": conversation.title,
                    "channel_conversation_id": conversation.channel_conversation_id,
                    "message_count": message_count,
                }
            )

        return conversations


# Dependency provider
async def get_messaging_service(session: SessionDep) -> MessagingService:
    """Provide MessagingService instance."""
    return MessagingService(session)


# Type alias for cleaner endpoint signatures
MessagingServiceDep = Annotated[MessagingService, Depends(get_messaging_service)]
