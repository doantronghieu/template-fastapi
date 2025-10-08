"""Seed database with test data for messaging system."""

import asyncio
from functools import partial
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import async_session_maker
from app.models import (
    ChannelType,
    Conversation,
    Message,
    MessageSenderRole,
    User,
    UserChannel,
    UserRole,
)


# UUID helpers for readable, predictable test data
def _test_uuid(prefix: int, n: int) -> UUID:
    """Generate test UUID: {prefix}0000000-0000-0000-0000-{n:012d}"""
    return UUID(f"{prefix}0000000-0000-0000-0000-{n:012d}")


uid = partial(_test_uuid, 0)  # User ID
cid = partial(_test_uuid, 1)  # Conversation ID
mid = partial(_test_uuid, 2)  # Message ID


# Test users
USERS = [
    # Regular users (no channel)
    {
        "id": uid(1),
        "email": "admin@example.com",
        "name": "Admin User",
        "role": UserRole.ADMIN,
        "profile": {"department": "Support"},
    },
    {
        "id": uid(2),
        "email": "alice@example.com",
        "name": "Alice Smith",
        "role": UserRole.CLIENT,
        "profile": {"company": "Acme Corp"},
    },
    {
        "id": uid(3),
        "email": "bob@example.com",
        "name": "Bob Johnson",
        "role": UserRole.CLIENT,
        "profile": {"company": "TechStart Inc"},
    },
    # Channel users
    {"id": uid(4), "name": "Telegram User 5678", "role": UserRole.CLIENT},
    {"id": uid(5), "name": "WhatsApp User 1234", "role": UserRole.CLIENT},
]

# Channel associations
CHANNELS = [
    {
        "user_id": uid(4),
        "channel_id": "telegram_5678",
        "channel_type": ChannelType.TELEGRAM,
    },
    {
        "user_id": uid(5),
        "channel_id": "whatsapp_1234",
        "channel_type": ChannelType.WHATSAPP,
    },
]

# Conversations
CONVERSATIONS = [
    {"id": cid(1), "user_id": uid(2), "title": "Alice Support Chat"},
    {"id": cid(2), "user_id": uid(3), "title": "Bob Technical Issue"},
    {
        "id": cid(3),
        "user_id": uid(4),
        "title": "Chat via Telegram",
        "channel_conversation_id": "tg_chat_001",
    },
    {
        "id": cid(4),
        "user_id": uid(5),
        "title": "Chat via Whatsapp",
        "channel_conversation_id": "wa_chat_002",
    },
    {"id": cid(5), "user_id": uid(4), "title": "Direct Support (Telegram User)"},
]

# Messages
MESSAGES = [
    # Alice's conversation
    (
        mid(1),
        cid(1),
        uid(2),
        MessageSenderRole.CLIENT,
        "I need help with my account settings",
    ),
    (
        mid(2),
        cid(1),
        uid(1),
        MessageSenderRole.ADMIN,
        "Hi Alice! I can help you with that. What specific settings?",
    ),
    (
        mid(3),
        cid(1),
        uid(2),
        MessageSenderRole.CLIENT,
        "How do I update my email address?",
    ),
    # Bob's conversation
    (
        mid(11),
        cid(2),
        uid(3),
        MessageSenderRole.CLIENT,
        "Getting an error when uploading files",
    ),
    (
        mid(12),
        cid(2),
        uid(1),
        MessageSenderRole.ADMIN,
        "Let me look into that. Can you share the error message?",
    ),
    # Telegram channel conversation
    (mid(21), cid(3), uid(4), MessageSenderRole.CLIENT, "Hello from Telegram!"),
    (mid(22), cid(3), uid(4), MessageSenderRole.AI, "Hi! How can I assist you today?"),
    (
        mid(23),
        cid(3),
        uid(4),
        MessageSenderRole.CLIENT,
        "What are your business hours?",
    ),
    (
        mid(24),
        cid(3),
        uid(4),
        MessageSenderRole.AI,
        "We're available 24/7 to help you!",
    ),
    # WhatsApp channel conversation
    (
        mid(31),
        cid(4),
        uid(5),
        MessageSenderRole.CLIENT,
        "Hi, I have a question about pricing",
    ),
    (
        mid(32),
        cid(4),
        uid(5),
        MessageSenderRole.AI,
        "I'd be happy to help! What would you like to know?",
    ),
    # Telegram direct conversation
    (
        mid(41),
        cid(5),
        uid(4),
        MessageSenderRole.ADMIN,
        "This is a direct support message outside of Telegram",
    ),
]


async def seed_data() -> None:
    """Create test users, conversations, and messages with fixed UUIDs."""
    async with async_session_maker() as session:
        session: AsyncSession

        # Check if data already exists
        result = await session.execute(select(User))
        if result.scalars().first():
            print("✓ Test data already exists")
            return

        # Create all users
        users = [User(**user_data) for user_data in USERS]
        session.add_all(users)
        await session.commit()

        # Create channel associations
        channels = [UserChannel(**channel_data) for channel_data in CHANNELS]
        session.add_all(channels)
        await session.commit()

        # Create conversations
        conversations = [Conversation(**conv_data) for conv_data in CONVERSATIONS]
        session.add_all(conversations)
        await session.commit()

        # Create messages
        messages = [
            Message(
                id=msg_id,
                conversation_id=conv_id,
                user_id=user_id,
                sender_role=role,
                content=content,
            )
            for msg_id, conv_id, user_id, role, content in MESSAGES
        ]
        session.add_all(messages)
        await session.commit()

        # Summary
        regular_users = len(USERS) - len(CHANNELS)
        channel_convs = sum(1 for c in CONVERSATIONS if "channel_conversation_id" in c)

        print("✓ Seeded database with test data:")
        print(
            f"  Users: {len(USERS)} ({regular_users} regular, {len(CHANNELS)} channel)"
        )
        print(
            f"  Conversations: {len(CONVERSATIONS)} ({channel_convs} channel, {len(CONVERSATIONS) - channel_convs} direct)"
        )
        print(f"  Messages: {len(MESSAGES)}")
        print("\n  Fixed UUIDs for easy testing:")
        print(f"    Admin User:    {uid(1)}")
        print(f"    Alice Smith:   {uid(2)}")
        print(f"    Bob Johnson:   {uid(3)}")
        print(f"    Telegram User: {uid(4)}")
        print(f"    WhatsApp User: {uid(5)}")


if __name__ == "__main__":
    asyncio.run(seed_data())
