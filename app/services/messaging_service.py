"""Messaging service for conversation and message operations."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

if TYPE_CHECKING:
    from sqlmodel import SQLModel

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import SessionDep
from app.models import (
    ChannelType,
    Conversation,
    Message,
    MessageSenderRole,
    User,
    UserChannel,
    UserRole,
)
from app.utils import serialize_enum


class MessagingService:
    """Service for messaging operations with auto-provisioning."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _paginate_results(
        self, items: list, limit: int
    ) -> tuple[list, UUID | None, bool]:
        """
        Apply pagination logic to results list.

        Args:
            items: List of items (must have .id attribute for cursor)
            limit: Maximum number of items per page

        Returns:
            Tuple of (paginated_items, next_cursor, has_more)
        """
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        next_cursor = items[-1].id if items and has_more else None
        return items, next_cursor, has_more

    def _parse_order(self, order: str, model: type["SQLModel"]) -> tuple[Any, str]:
        """
        Parse order string and return column with direction.

        Args:
            order: Order string in format "field.direction" (e.g., "created_at.desc")
            model: SQLModel class to get column from

        Returns:
            Tuple of (column, direction)

        Raises:
            HTTPException: 400 if invalid format or field
        """
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
        """
        Find conversation by UUID or channel ID.

        Args:
            conversation_id: Internal conversation UUID
            channel_conversation_id: External conversation identifier

        Returns:
            Conversation if found, None otherwise
        """
        if not conversation_id and not channel_conversation_id:
            return None

        # Build query with OR conditions
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

    async def has_new_messages_since(
        self,
        channel_conversation_id: str,
        since: datetime,
        sender_role: MessageSenderRole | None = None,
    ) -> bool:
        """Check if new messages exist after a given timestamp.

        Generic helper to detect message activity patterns:
        - Interruption detection
        - Activity monitoring
        - Notification triggers

        Args:
            channel_conversation_id: External channel conversation ID (e.g., Facebook PSID)
            since: Timestamp to check for messages after
            sender_role: Optional filter by message sender (CLIENT, AI, ADMIN)

        Returns:
            True if at least one message exists after the timestamp

        Example:
            >>> # Check if user sent any message in last 5 minutes
            >>> five_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
            >>> has_activity = await messaging_service.has_new_messages_since(
            ...     channel_conversation_id="123456",
            ...     since=five_mins_ago,
            ...     sender_role=MessageSenderRole.CLIENT
            ... )
        """
        stmt = (
            select(Message)
            .join(Conversation)
            .where(Conversation.channel_conversation_id == channel_conversation_id)
            .where(Message.created_at > since)
        )

        # Optional filter by sender role
        if sender_role:
            stmt = stmt.where(Message.sender_role == sender_role)

        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

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
        """
        Get messages for a conversation with pagination support.

        Args:
            conversation_id: Internal conversation UUID
            channel_conversation_id: External conversation identifier
            limit: Maximum number of messages to return
            before_message_id: Message UUID to fetch messages before (for pagination)
            order: Sort order in format "field.direction" (e.g., "created_at.desc")
            reverse: Whether to reverse the final result order

        Returns:
            Tuple of (conversation, messages_list, next_cursor)

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

        # Parse order parameter using helper
        order_column, direction = self._parse_order(order, Message)

        # Build query with ordering
        query = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .limit(limit + 1)  # Fetch one extra to check has_more
        )

        # Add pagination filter
        if before_message_id:
            before_msg_result = await self.session.execute(
                select(Message).where(Message.id == before_message_id)
            )
            before_msg = before_msg_result.scalar_one_or_none()
            if before_msg:
                # Assuming descending order by created_at for pagination
                query = query.where(Message.created_at < before_msg.created_at)

        if direction == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        result = await self.session.execute(query)
        messages: list[Message] = list(result.scalars().all())

        # Apply pagination using helper
        messages, next_cursor, _ = self._paginate_results(messages, limit)

        # Apply reverse if requested
        if reverse:
            messages.reverse()

        return conversation, messages, next_cursor

    async def get_all_conversations(
        self,
        limit: int = 50,
        cursor: UUID | None = None,
    ) -> tuple[list[dict], UUID | None, bool]:
        """
        Get all conversations across all users for admin view.

        Args:
            limit: Maximum number of conversations to return
            cursor: Conversation UUID to start after (for pagination)

        Returns:
            Tuple of (conversations_list, next_cursor, has_more)
        """
        # Base query with eager loading for user and messages
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
            .limit(limit + 1)  # Fetch one extra to check has_more
        )

        # Apply cursor pagination
        if cursor:
            cursor_conv_result = await self.session.execute(
                select(Conversation).where(Conversation.id == cursor)
            )
            cursor_conv = cursor_conv_result.scalar_one_or_none()
            if cursor_conv:
                query = query.where(Conversation.updated_at < cursor_conv.updated_at)

        result = await self.session.execute(query)
        conversations: list[Conversation] = list(result.scalars().all())

        # Apply pagination using helper
        conversations, next_cursor, has_more = self._paginate_results(
            conversations, limit
        )

        # Format response with eagerly loaded data
        formatted_conversations = []
        for conv in conversations:
            # Get last message from eagerly loaded messages
            last_message = (
                max(conv.messages, key=lambda m: m.created_at)
                if conv.messages
                else None
            )

            # Get primary channel from eagerly loaded user channels
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
