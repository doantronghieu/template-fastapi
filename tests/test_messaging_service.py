"""Unit tests for MessagingService.

Tests auto-provisioning, race condition handling, ownership validation,
and all CRUD operations for users, conversations, and messages.
"""

from uuid import uuid4

from fastapi import HTTPException
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ChannelType,
    Conversation,
    Message,
    MessageSenderRole,
    User,
    UserChannel,
    UserRole,
)
from app.services.messaging_service import MessagingService


@pytest.fixture
async def messaging_service(db_session: AsyncSession) -> MessagingService:
    """Provide MessagingService instance with test session."""
    return MessagingService(db_session)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user with email."""
    user = User(
        email="test@example.com",
        name="Test User",
        role=UserRole.CLIENT.value,
        profile={},
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGetOrCreateUserByChannel:
    """Test user auto-provisioning by channel."""

    async def test_creates_new_user_and_channel(
        self, messaging_service: MessagingService, db_session: AsyncSession
    ):
        """Auto-provision new user when channel doesn't exist."""
        user = await messaging_service.get_or_create_user_by_channel(
            channel_id="12345678", channel_type=ChannelType.TELEGRAM
        )

        assert user.id is not None
        assert user.email is None
        assert user.name == "Telegram User 5678"
        assert user.role == UserRole.CLIENT.value

        # Verify UserChannel was created
        result = await db_session.execute(
            select(UserChannel).where(UserChannel.user_id == user.id)
        )
        user_channel = result.scalar_one()
        assert user_channel.channel_id == "12345678"
        assert user_channel.channel_type == ChannelType.TELEGRAM
        assert user_channel.is_primary is True

    async def test_returns_existing_user(
        self, messaging_service: MessagingService, db_session: AsyncSession
    ):
        """Return existing user for known channel."""
        # Create user + channel
        user1 = await messaging_service.get_or_create_user_by_channel(
            channel_id="telegram_123", channel_type=ChannelType.TELEGRAM
        )

        # Retrieve again
        user2 = await messaging_service.get_or_create_user_by_channel(
            channel_id="telegram_123", channel_type=ChannelType.TELEGRAM
        )

        assert user1.id == user2.id

    async def test_different_channel_types_same_id(
        self, messaging_service: MessagingService, db_session: AsyncSession
    ):
        """Different channel types with same ID create separate users."""
        telegram_user = await messaging_service.get_or_create_user_by_channel(
            channel_id="123", channel_type=ChannelType.TELEGRAM
        )
        whatsapp_user = await messaging_service.get_or_create_user_by_channel(
            channel_id="123", channel_type=ChannelType.WHATSAPP
        )

        assert telegram_user.id != whatsapp_user.id

    async def test_channel_id_last_4_chars(self, messaging_service: MessagingService):
        """User name uses last 4 characters of channel_id."""
        user = await messaging_service.get_or_create_user_by_channel(
            channel_id="abc", channel_type=ChannelType.WHATSAPP
        )
        assert user.name == "Whatsapp User abc"

        user2 = await messaging_service.get_or_create_user_by_channel(
            channel_id="xyz123", channel_type=ChannelType.MESSENGER
        )
        assert user2.name == "Messenger User z123"


class TestGetOrCreateConversation:
    """Test conversation auto-provisioning with multiple lookup strategies."""

    async def test_lookup_by_conversation_id(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Find existing conversation by UUID."""
        conversation = Conversation(user_id=test_user.id, title="Existing Conversation")
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        found = await messaging_service.get_or_create_conversation(
            user_id=test_user.id, conversation_id=conversation.id
        )

        assert found.id == conversation.id
        assert found.title == "Existing Conversation"

    async def test_lookup_by_channel_conversation_id(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Find existing conversation by channel ID."""
        conversation = Conversation(
            user_id=test_user.id,
            title="Channel Chat",
            channel_conversation_id="telegram_chat_456",
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        found = await messaging_service.get_or_create_conversation(
            user_id=test_user.id, channel_conversation_id="telegram_chat_456"
        )

        assert found.id == conversation.id
        assert found.channel_conversation_id == "telegram_chat_456"

    async def test_auto_create_with_channel_id(
        self, messaging_service: MessagingService, test_user: User
    ):
        """Auto-create conversation with channel-based title."""
        conversation = await messaging_service.get_or_create_conversation(
            user_id=test_user.id,
            channel_conversation_id="whatsapp_789",
            channel_type=ChannelType.WHATSAPP,
        )

        assert conversation.id is not None
        assert conversation.title == "Chat via Whatsapp"
        assert conversation.channel_conversation_id == "whatsapp_789"

    async def test_auto_create_without_channel_id(
        self, messaging_service: MessagingService, test_user: User
    ):
        """Auto-create conversation with timestamp-based title."""
        conversation = await messaging_service.get_or_create_conversation(
            user_id=test_user.id
        )

        assert conversation.id is not None
        assert conversation.title.startswith("Conversation ")
        assert conversation.channel_conversation_id is None

    async def test_auto_create_false_raises_404(
        self, messaging_service: MessagingService, test_user: User
    ):
        """Raise HTTPException when conversation not found and auto_create=False."""
        with pytest.raises(HTTPException) as exc_info:
            await messaging_service.get_or_create_conversation(
                user_id=test_user.id,
                conversation_id=uuid4(),
                auto_create=False,
            )
        assert exc_info.value.status_code == 404

    async def test_explicit_title_override(
        self, messaging_service: MessagingService, test_user: User
    ):
        """Explicit title overrides auto-generated titles."""
        conversation = await messaging_service.get_or_create_conversation(
            user_id=test_user.id,
            channel_conversation_id="telegram_123",
            channel_type=ChannelType.TELEGRAM,
            title="Custom Title",
        )

        assert conversation.title == "Custom Title"


class TestCreateMessage:
    """Test message creation in both channel and internal modes."""

    async def test_channel_mode_auto_provisions_user_and_conversation(
        self, messaging_service: MessagingService, db_session: AsyncSession
    ):
        """Channel mode auto-creates user and conversation."""
        message = await messaging_service.create_message(
            content="Hello from Telegram",
            sender_role=MessageSenderRole.CLIENT,
            channel_id="telegram_user_123",
            channel_type=ChannelType.TELEGRAM,
            channel_conversation_id="telegram_chat_456",
        )

        assert message.id is not None
        assert message.content == "Hello from Telegram"
        assert message.sender_role == MessageSenderRole.CLIENT

        # Verify user was created
        result = await db_session.execute(
            select(User).where(User.id == message.user_id)
        )
        user = result.scalar_one()
        assert user.name == "Telegram User _123"

        # Verify conversation was created
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == message.conversation_id)
        )
        conversation = result.scalar_one()
        assert conversation.channel_conversation_id == "telegram_chat_456"

    async def test_internal_mode_with_existing_conversation(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Internal mode uses existing user and conversation."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        message = await messaging_service.create_message(
            content="Internal message",
            sender_role=MessageSenderRole.AI,
            user_id=test_user.id,
            conversation_id=conversation.id,
        )

        assert message.user_id == test_user.id
        assert message.conversation_id == conversation.id
        assert message.sender_role == MessageSenderRole.AI

    async def test_internal_mode_validates_ownership(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Internal mode rejects conversation access for wrong user."""
        # Create conversation for test_user
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        # Try to create message with wrong user_id
        wrong_user_id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await messaging_service.create_message(
                content="Unauthorized message",
                sender_role=MessageSenderRole.CLIENT,
                user_id=wrong_user_id,
                conversation_id=conversation.id,
            )
        assert exc_info.value.status_code == 404
        assert "not found or access denied" in str(exc_info.value.detail)

    async def test_invalid_parameters_raises_404(
        self, messaging_service: MessagingService
    ):
        """Missing required parameters raises HTTPException 404 when bypassing schema validation."""
        # When calling service directly without schema validation, it tries to look up
        # conversation with None values and returns 404
        with pytest.raises(HTTPException) as exc_info:
            await messaging_service.create_message(
                content="Invalid",
                sender_role=MessageSenderRole.CLIENT,
            )
        assert exc_info.value.status_code == 404

    async def test_different_sender_roles(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Support all sender role types."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        for role in [
            MessageSenderRole.CLIENT,
            MessageSenderRole.AI,
            MessageSenderRole.ADMIN,
        ]:
            message = await messaging_service.create_message(
                content=f"Message from {role.value}",
                sender_role=role,
                user_id=test_user.id,
                conversation_id=conversation.id,
            )
            assert message.sender_role == role


class TestGetConversationMessages:
    """Test message retrieval with sorting and filtering."""

    async def test_lookup_by_conversation_id(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Retrieve messages by conversation UUID."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.flush()

        for i in range(3):
            msg = Message(
                conversation_id=conversation.id,
                user_id=test_user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=f"Message {i}",
            )
            db_session.add(msg)
        await db_session.commit()

        conv, messages = await messaging_service.get_conversation_messages(
            conversation_id=conversation.id
        )

        assert conv.id == conversation.id
        assert len(messages) == 3

    async def test_lookup_by_channel_conversation_id(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Retrieve messages by channel conversation ID."""
        conversation = Conversation(
            user_id=test_user.id,
            title="Channel Chat",
            channel_conversation_id="telegram_123",
        )
        db_session.add(conversation)
        await db_session.flush()

        msg = Message(
            conversation_id=conversation.id,
            user_id=test_user.id,
            sender_role=MessageSenderRole.CLIENT,
            content="Test",
        )
        db_session.add(msg)
        await db_session.commit()

        conv, messages = await messaging_service.get_conversation_messages(
            channel_conversation_id="telegram_123"
        )

        assert conv.channel_conversation_id == "telegram_123"
        assert len(messages) == 1

    async def test_conversation_not_found_raises_404(
        self, messaging_service: MessagingService
    ):
        """Raise HTTPException 404 when conversation doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            await messaging_service.get_conversation_messages(conversation_id=uuid4())
        assert exc_info.value.status_code == 404

    async def test_order_ascending(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Order messages by created_at ascending."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.flush()

        messages_data = ["First", "Second", "Third"]
        for content in messages_data:
            msg = Message(
                conversation_id=conversation.id,
                user_id=test_user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=content,
            )
            db_session.add(msg)
        await db_session.commit()

        conv, messages = await messaging_service.get_conversation_messages(
            conversation_id=conversation.id, order="created_at.asc"
        )

        assert [m.content for m in messages] == ["First", "Second", "Third"]

    async def test_order_descending(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Order messages by created_at descending."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.flush()

        messages_data = ["First", "Second", "Third"]
        for content in messages_data:
            msg = Message(
                conversation_id=conversation.id,
                user_id=test_user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=content,
            )
            db_session.add(msg)
        await db_session.commit()

        conv, messages = await messaging_service.get_conversation_messages(
            conversation_id=conversation.id, order="created_at.desc"
        )

        assert [m.content for m in messages] == ["Third", "Second", "First"]

    async def test_reverse_option(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Reverse final result order."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.flush()

        messages_data = ["First", "Second", "Third"]
        for content in messages_data:
            msg = Message(
                conversation_id=conversation.id,
                user_id=test_user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=content,
            )
            db_session.add(msg)
        await db_session.commit()

        conv, messages = await messaging_service.get_conversation_messages(
            conversation_id=conversation.id, order="created_at.desc", reverse=True
        )

        assert [m.content for m in messages] == ["First", "Second", "Third"]

    async def test_limit_parameter(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Limit number of returned messages."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.flush()

        for i in range(10):
            msg = Message(
                conversation_id=conversation.id,
                user_id=test_user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=f"Message {i}",
            )
            db_session.add(msg)
        await db_session.commit()

        conv, messages = await messaging_service.get_conversation_messages(
            conversation_id=conversation.id, limit=3
        )

        assert len(messages) == 3

    async def test_invalid_order_format_raises_400(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Invalid order format raises HTTPException 400."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await messaging_service.get_conversation_messages(
                conversation_id=conversation.id, order="invalid"
            )
        assert exc_info.value.status_code == 400

    async def test_invalid_order_field_raises_400(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Invalid order field raises HTTPException 400."""
        conversation = Conversation(user_id=test_user.id, title="Test Chat")
        db_session.add(conversation)
        await db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await messaging_service.get_conversation_messages(
                conversation_id=conversation.id, order="nonexistent.desc"
            )
        assert exc_info.value.status_code == 400


class TestGetUserConversations:
    """Test conversation list retrieval with message counts."""

    async def test_returns_empty_list_for_new_user(
        self, messaging_service: MessagingService, test_user: User
    ):
        """Return empty list when user has no conversations."""
        conversations = await messaging_service.get_user_conversations(test_user.id)
        assert conversations == []

    async def test_returns_conversations_with_message_counts(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Return conversations with accurate message counts."""
        # Create 2 conversations
        conv1 = Conversation(user_id=test_user.id, title="Chat 1")
        conv2 = Conversation(user_id=test_user.id, title="Chat 2")
        db_session.add_all([conv1, conv2])
        await db_session.flush()

        # Add 3 messages to conv1
        for i in range(3):
            msg = Message(
                conversation_id=conv1.id,
                user_id=test_user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=f"Message {i}",
            )
            db_session.add(msg)

        # Add 1 message to conv2
        msg = Message(
            conversation_id=conv2.id,
            user_id=test_user.id,
            sender_role=MessageSenderRole.AI,
            content="AI Response",
        )
        db_session.add(msg)
        await db_session.commit()

        conversations = await messaging_service.get_user_conversations(test_user.id)

        assert len(conversations) == 2
        # Find conversations by title
        chat1 = next(c for c in conversations if c["title"] == "Chat 1")
        chat2 = next(c for c in conversations if c["title"] == "Chat 2")

        assert chat1["message_count"] == 3
        assert chat2["message_count"] == 1

    async def test_includes_all_conversation_fields(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Return all conversation fields including channel_conversation_id."""
        conversation = Conversation(
            user_id=test_user.id,
            title="Test Chat",
            channel_conversation_id="telegram_123",
        )
        db_session.add(conversation)
        await db_session.commit()

        conversations = await messaging_service.get_user_conversations(test_user.id)

        assert len(conversations) == 1
        conv = conversations[0]
        assert conv["id"] == conversation.id
        assert conv["title"] == "Test Chat"
        assert conv["channel_conversation_id"] == "telegram_123"
        assert conv["message_count"] == 0
        assert "created_at" in conv
        assert "updated_at" in conv

    async def test_ordered_by_updated_at_desc(
        self,
        messaging_service: MessagingService,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Conversations ordered by most recently updated first."""
        conv1 = Conversation(user_id=test_user.id, title="Older Chat")
        db_session.add(conv1)
        await db_session.commit()

        conv2 = Conversation(user_id=test_user.id, title="Newer Chat")
        db_session.add(conv2)
        await db_session.commit()

        conversations = await messaging_service.get_user_conversations(test_user.id)

        assert len(conversations) == 2
        assert conversations[0]["title"] == "Newer Chat"
        assert conversations[1]["title"] == "Older Chat"
