"""Integration tests for messaging API endpoints.

Tests POST /api/messages, POST /api/conversations/messages,
and GET /api/users/{user_id}/conversations endpoints.
"""

from uuid import uuid4

from httpx import AsyncClient
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


class TestCreateMessageEndpoint:
    """Test POST /api/messages endpoint."""

    async def test_channel_mode_creates_message_user_conversation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Channel mode auto-provisions user and conversation."""
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": "telegram_user_999",
                "channel_type": "telegram",
                "channel_conversation_id": "telegram_chat_999",
                "sender_role": "client",
                "content": "Hello from Telegram integration test",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["content"] == "Hello from Telegram integration test"
        assert data["sender_role"] == "client"
        assert "id" in data
        assert "user_id" in data
        assert "conversation_id" in data

        # Verify user was created
        result = await db_session.execute(
            select(UserChannel).where(UserChannel.channel_id == "telegram_user_999")
        )
        user_channel = result.scalar_one()
        assert user_channel.channel_type == ChannelType.TELEGRAM

    async def test_internal_mode_creates_message(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Internal mode with existing user and conversation."""
        # Create user and conversation
        user = User(
            email="internal@test.com",
            name="Internal User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Internal Chat")
        db_session.add(conversation)
        await db_session.commit()

        response = await client.post(
            "/api/messages",
            json={
                "user_id": str(user.id),
                "conversation_id": str(conversation.id),
                "sender_role": "ai",
                "content": "AI response in internal mode",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["content"] == "AI response in internal mode"
        assert data["sender_role"] == "ai"
        assert data["user_id"] == str(user.id)
        assert data["conversation_id"] == str(conversation.id)

    async def test_missing_required_parameters_returns_422(self, client: AsyncClient):
        """Missing required parameters returns 422 (Pydantic validation error)."""
        response = await client.post(
            "/api/messages",
            json={
                "sender_role": "client",
                "content": "Invalid message",
            },
        )

        assert response.status_code == 422
        # Verify error message mentions the validation issue
        assert "Must provide either" in response.json()["detail"][0]["msg"]

    async def test_invalid_sender_role_returns_422(self, client: AsyncClient):
        """Invalid sender_role enum value returns 422."""
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": "test_123",
                "channel_type": "telegram",
                "sender_role": "invalid_role",
                "content": "Test",
            },
        )

        assert response.status_code == 422

    async def test_invalid_channel_type_returns_422(self, client: AsyncClient):
        """Invalid channel_type enum value returns 422."""
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": "test_123",
                "channel_type": "invalid_channel",
                "sender_role": "client",
                "content": "Test",
            },
        )

        assert response.status_code == 422

    async def test_empty_content_returns_422(self, client: AsyncClient):
        """Empty content fails validation (min_length=1)."""
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": "test_123",
                "channel_type": "telegram",
                "sender_role": "client",
                "content": "",
            },
        )

        assert response.status_code == 422

    async def test_whitespace_only_content_returns_422(self, client: AsyncClient):
        """Whitespace-only content fails validation."""
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": "test_123",
                "channel_type": "telegram",
                "sender_role": "client",
                "content": "   \n\t  ",
            },
        )

        assert response.status_code == 422
        assert "whitespace" in response.json()["detail"][0]["msg"].lower()

    async def test_content_too_long_returns_422(self, client: AsyncClient):
        """Content exceeding max_length=10000 fails validation."""
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": "test_123",
                "channel_type": "telegram",
                "sender_role": "client",
                "content": "x" * 10001,
            },
        )

        assert response.status_code == 422

    async def test_ownership_validation_in_internal_mode(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Internal mode rejects wrong user_id for conversation."""
        # Create user and conversation
        user = User(
            email="owner@test.com", name="Owner", role=UserRole.CLIENT.value, profile={}
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Owner's Chat")
        db_session.add(conversation)
        await db_session.commit()

        # Try with wrong user_id
        wrong_user_id = str(uuid4())
        response = await client.post(
            "/api/messages",
            json={
                "user_id": wrong_user_id,
                "conversation_id": str(conversation.id),
                "sender_role": "client",
                "content": "Unauthorized access attempt",
            },
        )

        assert response.status_code == 404

    async def test_all_sender_roles_accepted(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """All sender roles (client, ai, admin) work correctly."""
        user = User(
            email="roles@test.com",
            name="Roles User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Roles Chat")
        db_session.add(conversation)
        await db_session.commit()

        for role in ["client", "ai", "admin"]:
            response = await client.post(
                "/api/messages",
                json={
                    "user_id": str(user.id),
                    "conversation_id": str(conversation.id),
                    "sender_role": role,
                    "content": f"Message from {role}",
                },
            )

            assert response.status_code == 200
            assert response.json()["sender_role"] == role

    async def test_all_channel_types_accepted(self, client: AsyncClient):
        """All channel types (telegram, whatsapp, messenger, direct) work correctly."""
        for channel_type in ["telegram", "whatsapp", "messenger", "direct"]:
            response = await client.post(
                "/api/messages",
                json={
                    "channel_id": f"{channel_type}_test_id",
                    "channel_type": channel_type,
                    "sender_role": "client",
                    "content": f"Message via {channel_type}",
                },
            )

            assert response.status_code == 200


class TestGetConversationMessagesEndpoint:
    """Test POST /api/conversations/messages endpoint."""

    async def test_get_messages_by_conversation_id(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Retrieve messages by conversation UUID."""
        user = User(
            email="conv@test.com",
            name="Conv User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Test Conversation")
        db_session.add(conversation)
        await db_session.flush()

        # Create messages
        messages_data = [
            ("client", "Hello"),
            ("ai", "Hi there!"),
            ("client", "How are you?"),
        ]
        for sender_role, content in messages_data:
            msg = Message(
                conversation_id=conversation.id,
                user_id=user.id,
                sender_role=MessageSenderRole(sender_role),
                content=content,
            )
            db_session.add(msg)
        await db_session.commit()

        response = await client.post(
            "/api/conversations/messages",
            json={"conversation_id": str(conversation.id)},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["conversation_id"] == str(conversation.id)
        assert len(data["conversation_history"]) == 3

        # Verify conversation_history format
        for msg in data["conversation_history"]:
            assert "role" in msg
            assert "content" in msg
            assert "created_at" in msg

    async def test_get_messages_by_channel_conversation_id(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Retrieve messages by channel conversation ID."""
        user = User(
            email="channel@test.com",
            name="Channel User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(
            user_id=user.id,
            title="Channel Chat",
            channel_conversation_id="telegram_external_123",
        )
        db_session.add(conversation)
        await db_session.flush()

        msg = Message(
            conversation_id=conversation.id,
            user_id=user.id,
            sender_role=MessageSenderRole.CLIENT,
            content="Channel message",
        )
        db_session.add(msg)
        await db_session.commit()

        response = await client.post(
            "/api/conversations/messages",
            json={"channel_conversation_id": "telegram_external_123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["conversation_history"]) == 1
        assert data["conversation_history"][0]["content"] == "Channel message"

    async def test_missing_identifiers_returns_422(self, client: AsyncClient):
        """Missing both conversation_id and channel_conversation_id returns 422."""
        response = await client.post("/api/conversations/messages", json={})

        assert response.status_code == 422
        # Verify error message mentions validation issue (from schema validator)
        detail = response.json()["detail"]
        # Could be string or list depending on Pydantic format
        detail_str = (
            detail if isinstance(detail, str) else detail[0].get("msg", str(detail))
        )
        assert "Must provide" in detail_str

    async def test_nonexistent_conversation_returns_404(self, client: AsyncClient):
        """Non-existent conversation returns 404."""
        response = await client.post(
            "/api/conversations/messages",
            json={"conversation_id": str(uuid4())},
        )

        assert response.status_code == 404

    async def test_limit_parameter(self, client: AsyncClient, db_session: AsyncSession):
        """Limit parameter restricts number of returned messages."""
        user = User(
            email="limit@test.com",
            name="Limit User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Limit Chat")
        db_session.add(conversation)
        await db_session.flush()

        # Create 10 messages
        for i in range(10):
            msg = Message(
                conversation_id=conversation.id,
                user_id=user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=f"Message {i}",
            )
            db_session.add(msg)
        await db_session.commit()

        response = await client.post(
            "/api/conversations/messages",
            json={"conversation_id": str(conversation.id), "limit": 3},
        )

        assert response.status_code == 200
        assert len(response.json()["conversation_history"]) == 3

    async def test_order_descending(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Order messages by created_at descending."""
        user = User(
            email="order@test.com",
            name="Order User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Order Chat")
        db_session.add(conversation)
        await db_session.flush()

        messages_data = ["First", "Second", "Third"]
        for content in messages_data:
            msg = Message(
                conversation_id=conversation.id,
                user_id=user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=content,
            )
            db_session.add(msg)
        await db_session.commit()

        response = await client.post(
            "/api/conversations/messages",
            json={
                "conversation_id": str(conversation.id),
                "order": "created_at.desc",
            },
        )

        assert response.status_code == 200
        messages = response.json()["conversation_history"]
        contents = [m["content"] for m in messages]
        assert contents == ["Third", "Second", "First"]

    async def test_reverse_parameter(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Reverse parameter reverses final result order."""
        user = User(
            email="reverse@test.com",
            name="Reverse User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Reverse Chat")
        db_session.add(conversation)
        await db_session.flush()

        messages_data = ["First", "Second", "Third"]
        for content in messages_data:
            msg = Message(
                conversation_id=conversation.id,
                user_id=user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=content,
            )
            db_session.add(msg)
        await db_session.commit()

        response = await client.post(
            "/api/conversations/messages",
            json={
                "conversation_id": str(conversation.id),
                "order": "created_at.desc",
                "reverse": True,
            },
        )

        assert response.status_code == 200
        messages = response.json()["conversation_history"]
        contents = [m["content"] for m in messages]
        assert contents == ["First", "Second", "Third"]

    async def test_limit_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Limit must be between 1 and 100."""
        user = User(
            email="limitval@test.com",
            name="Limit Val User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Limit Validation")
        db_session.add(conversation)
        await db_session.commit()

        # Test limit < 1
        response = await client.post(
            "/api/conversations/messages",
            json={"conversation_id": str(conversation.id), "limit": 0},
        )
        assert response.status_code == 422

        # Test limit > 100
        response = await client.post(
            "/api/conversations/messages",
            json={"conversation_id": str(conversation.id), "limit": 101},
        )
        assert response.status_code == 422


class TestGetUserConversationsEndpoint:
    """Test GET /api/users/{user_id}/conversations endpoint."""

    async def test_get_conversations_for_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Retrieve all conversations for a user with message counts."""
        user = User(
            email="userconv@test.com",
            name="User Conv",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        # Create 2 conversations
        conv1 = Conversation(user_id=user.id, title="Conversation 1")
        conv2 = Conversation(user_id=user.id, title="Conversation 2")
        db_session.add_all([conv1, conv2])
        await db_session.flush()

        # Add messages to conv1
        for i in range(3):
            msg = Message(
                conversation_id=conv1.id,
                user_id=user.id,
                sender_role=MessageSenderRole.CLIENT,
                content=f"Message {i}",
            )
            db_session.add(msg)

        await db_session.commit()

        response = await client.get(f"/api/users/{user.id}/conversations")

        assert response.status_code == 200
        data = response.json()

        assert "conversations" in data
        assert len(data["conversations"]) == 2

        # Find conversations by title
        conversations = {c["title"]: c for c in data["conversations"]}
        assert conversations["Conversation 1"]["message_count"] == 3
        assert conversations["Conversation 2"]["message_count"] == 0

    async def test_empty_conversations_list(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Return empty list for user with no conversations."""
        user = User(
            email="noconv@test.com",
            name="No Conv User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.get(f"/api/users/{user.id}/conversations")

        assert response.status_code == 200
        data = response.json()

        assert data["conversations"] == []

    async def test_includes_channel_conversation_id(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Include channel_conversation_id in response."""
        user = User(
            email="chanconv@test.com",
            name="Chan Conv User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(
            user_id=user.id,
            title="Channel Conversation",
            channel_conversation_id="whatsapp_external_456",
        )
        db_session.add(conversation)
        await db_session.commit()

        response = await client.get(f"/api/users/{user.id}/conversations")

        assert response.status_code == 200
        data = response.json()

        assert len(data["conversations"]) == 1
        conv = data["conversations"][0]
        assert conv["channel_conversation_id"] == "whatsapp_external_456"
        assert conv["title"] == "Channel Conversation"

    async def test_conversation_fields_present(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """All required conversation fields are present in response."""
        user = User(
            email="fields@test.com",
            name="Fields User",
            role=UserRole.CLIENT.value,
            profile={},
        )
        db_session.add(user)
        await db_session.flush()

        conversation = Conversation(user_id=user.id, title="Fields Test")
        db_session.add(conversation)
        await db_session.commit()

        response = await client.get(f"/api/users/{user.id}/conversations")

        assert response.status_code == 200
        conv = response.json()["conversations"][0]

        required_fields = [
            "id",
            "created_at",
            "updated_at",
            "title",
            "channel_conversation_id",
            "message_count",
        ]
        for field in required_fields:
            assert field in conv

    async def test_invalid_user_id_format_returns_422(self, client: AsyncClient):
        """Invalid UUID format returns 422."""
        response = await client.get("/api/users/invalid-uuid/conversations")

        assert response.status_code == 422


class TestEndToEndWorkflow:
    """Test complete n8n integration workflow."""

    async def test_complete_channel_conversation_flow(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Simulate complete n8n workflow: create messages, retrieve history."""
        channel_id = "telegram_e2e_user"
        channel_conversation_id = "telegram_e2e_chat"

        # Step 1: Customer sends message via Telegram
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": channel_id,
                "channel_type": "telegram",
                "channel_conversation_id": channel_conversation_id,
                "sender_role": "client",
                "content": "Hello, I need help with my order",
            },
        )
        assert response.status_code == 200
        user_id = response.json()["user_id"]
        conversation_id = response.json()["conversation_id"]

        # Step 2: AI processes and sends response
        response = await client.post(
            "/api/messages",
            json={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "sender_role": "ai",
                "content": "I'd be happy to help! Can you provide your order number?",
            },
        )
        assert response.status_code == 200

        # Step 3: Customer replies
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": channel_id,
                "channel_type": "telegram",
                "channel_conversation_id": channel_conversation_id,
                "sender_role": "client",
                "content": "My order number is #12345",
            },
        )
        assert response.status_code == 200

        # Step 4: Retrieve conversation history
        response = await client.post(
            "/api/conversations/messages",
            json={
                "channel_conversation_id": channel_conversation_id,
                "order": "created_at.asc",
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["conversation_history"]) == 3
        messages = data["conversation_history"]

        assert messages[0]["role"] == "client"
        assert "help with my order" in messages[0]["content"]

        assert messages[1]["role"] == "ai"
        assert "order number" in messages[1]["content"]

        assert messages[2]["role"] == "client"
        assert "#12345" in messages[2]["content"]

        # Step 5: Get user's conversations
        response = await client.get(f"/api/users/{user_id}/conversations")
        assert response.status_code == 200
        data = response.json()

        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["message_count"] == 3
        assert data["conversations"][0]["title"] == "Chat via Telegram"

    async def test_multi_channel_same_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """User can have conversations across multiple channels."""
        # Create user with Telegram channel
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": "multi_user_123",
                "channel_type": "telegram",
                "channel_conversation_id": "telegram_conv",
                "sender_role": "client",
                "content": "Message via Telegram",
            },
        )
        assert response.status_code == 200
        telegram_user_id = response.json()["user_id"]

        # Verify user exists
        result = await db_session.execute(
            select(User).where(User.id == telegram_user_id)
        )
        user = result.scalar_one()

        # Add WhatsApp channel to same user
        whatsapp_channel = UserChannel(
            user_id=user.id,
            channel_id="whatsapp_multi_user",
            channel_type=ChannelType.WHATSAPP,
            is_primary=False,
        )
        db_session.add(whatsapp_channel)
        await db_session.commit()

        # Send message via WhatsApp
        response = await client.post(
            "/api/messages",
            json={
                "channel_id": "whatsapp_multi_user",
                "channel_type": "whatsapp",
                "channel_conversation_id": "whatsapp_conv",
                "sender_role": "client",
                "content": "Message via WhatsApp",
            },
        )
        assert response.status_code == 200
        whatsapp_user_id = response.json()["user_id"]

        # Same user ID for both channels
        assert telegram_user_id == whatsapp_user_id

        # User has 2 conversations
        response = await client.get(f"/api/users/{user.id}/conversations")
        assert response.status_code == 200
        assert len(response.json()["conversations"]) == 2
