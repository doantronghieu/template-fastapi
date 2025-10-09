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
    # AI Bot user
    {"id": uid(10), "name": "AI Assistant Bot", "role": UserRole.AI},
    # Channel users - one for each platform
    {"id": uid(4), "name": "Telegram User 5678", "role": UserRole.CLIENT},
    {"id": uid(5), "name": "WhatsApp User 1234", "role": UserRole.CLIENT},
    {"id": uid(6), "name": "Messenger User 9012", "role": UserRole.CLIENT},
    {"id": uid(7), "name": "Zalo User 3456", "role": UserRole.CLIENT},
    {"id": uid(8), "name": "Instagram User 7890", "role": UserRole.CLIENT},
    {"id": uid(9), "name": "TikTok User 2468", "role": UserRole.CLIENT},
]

# Channel associations
CHANNELS = [
    # Alice has BOTH email (direct) AND Telegram channel - demonstrates multi-channel user
    {
        "user_id": uid(2),
        "channel_id": "telegram_alice_smith",
        "channel_type": ChannelType.TELEGRAM,
        "is_primary": True,
    },
    {
        "user_id": uid(4),
        "channel_id": "telegram_5678",
        "channel_type": ChannelType.TELEGRAM,
        "is_primary": True,
    },
    {
        "user_id": uid(5),
        "channel_id": "whatsapp_1234",
        "channel_type": ChannelType.WHATSAPP,
        "is_primary": True,
    },
    {
        "user_id": uid(6),
        "channel_id": "messenger_9012",
        "channel_type": ChannelType.MESSENGER,
        "is_primary": True,
    },
    {
        "user_id": uid(7),
        "channel_id": "zalo_3456",
        "channel_type": ChannelType.ZALO,
        "is_primary": True,
    },
    {
        "user_id": uid(8),
        "channel_id": "instagram_7890",
        "channel_type": ChannelType.INSTAGRAM,
        "is_primary": True,
    },
    {
        "user_id": uid(9),
        "channel_id": "tiktok_2468",
        "channel_type": ChannelType.TIKTOK,
        "is_primary": True,
    },
]

# Conversations
CONVERSATIONS = [
    # Alice's conversations - demonstrates user with BOTH direct AND channel conversations
    {"id": cid(1), "user_id": uid(2), "title": "Alice Direct Support Chat"},
    {
        "id": cid(9),
        "user_id": uid(2),
        "title": "Alice via Telegram",
        "channel_conversation_id": "tg_alice_001",
    },
    # Bob's direct conversation
    {"id": cid(2), "user_id": uid(3), "title": "Bob Technical Issue"},
    # Channel-only user conversations
    {
        "id": cid(3),
        "user_id": uid(4),
        "title": "Chat via Telegram",
        "channel_conversation_id": "tg_chat_001",
    },
    {
        "id": cid(4),
        "user_id": uid(5),
        "title": "Chat via WhatsApp",
        "channel_conversation_id": "wa_chat_001",
    },
    {
        "id": cid(5),
        "user_id": uid(6),
        "title": "Chat via Messenger",
        "channel_conversation_id": "msg_chat_001",
    },
    {
        "id": cid(6),
        "user_id": uid(7),
        "title": "Chat via Zalo",
        "channel_conversation_id": "zalo_chat_001",
    },
    {
        "id": cid(7),
        "user_id": uid(8),
        "title": "Chat via Instagram",
        "channel_conversation_id": "ig_chat_001",
    },
    {
        "id": cid(8),
        "user_id": uid(9),
        "title": "Chat via TikTok",
        "channel_conversation_id": "tt_chat_001",
    },
]

# Messages
MESSAGES = [
    # Alice's direct conversation
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
    # Alice's Telegram conversation - demonstrates SAME user via DIFFERENT channel
    (
        mid(81),
        cid(9),
        uid(2),
        MessageSenderRole.CLIENT,
        "Hi! Quick question via Telegram - where's my order?",
    ),
    (
        mid(82),
        cid(9),
        uid(10),
        MessageSenderRole.AI,
        "Hi Alice! Let me check your order status for you.",
    ),
    (
        mid(83),
        cid(9),
        uid(2),
        MessageSenderRole.CLIENT,
        "Thanks! Order #12345",
    ),
    (
        mid(84),
        cid(9),
        uid(1),
        MessageSenderRole.ADMIN,
        "Your order shipped yesterday! Tracking: TRK123456789",
    ),
    # Bob's conversation (regular user)
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
    (mid(22), cid(3), uid(10), MessageSenderRole.AI, "Hi! How can I assist you today?"),
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
        uid(10),
        MessageSenderRole.AI,
        "We're available 24/7 to help you!",
    ),
    (
        mid(25),
        cid(3),
        uid(4),
        MessageSenderRole.CLIENT,
        "Great! I need help with order tracking",
    ),
    (
        mid(26),
        cid(3),
        uid(1),
        MessageSenderRole.ADMIN,
        "I'll help you track your order. Please provide your order number.",
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
        uid(10),
        MessageSenderRole.AI,
        "I'd be happy to help! What would you like to know?",
    ),
    (
        mid(33),
        cid(4),
        uid(5),
        MessageSenderRole.CLIENT,
        "Do you offer bulk discounts?",
    ),
    (
        mid(34),
        cid(4),
        uid(10),
        MessageSenderRole.AI,
        "Yes! We offer discounts for orders over 100 units. Would you like more details?",
    ),
    (
        mid(35),
        cid(4),
        uid(5),
        MessageSenderRole.CLIENT,
        "Yes please, send me the pricing tiers",
    ),
    # Messenger channel conversation
    (
        mid(41),
        cid(5),
        uid(6),
        MessageSenderRole.CLIENT,
        "Hey! I saw your ad on Facebook",
    ),
    (
        mid(42),
        cid(5),
        uid(10),
        MessageSenderRole.AI,
        "Welcome! Thanks for reaching out. How can I help you today?",
    ),
    (
        mid(43),
        cid(5),
        uid(6),
        MessageSenderRole.CLIENT,
        "I'm interested in the new product launch",
    ),
    (
        mid(44),
        cid(5),
        uid(10),
        MessageSenderRole.AI,
        "Excellent! Our new product launches next week. Would you like to pre-order?",
    ),
    (mid(45), cid(5), uid(6), MessageSenderRole.CLIENT, "What's the delivery time?"),
    (
        mid(46),
        cid(5),
        uid(1),
        MessageSenderRole.ADMIN,
        "Delivery takes 3-5 business days for domestic orders.",
    ),
    # Zalo channel conversation
    (mid(51), cid(6), uid(7), MessageSenderRole.CLIENT, "Xin chào! Tôi cần hỗ trợ"),
    (
        mid(52),
        cid(6),
        uid(10),
        MessageSenderRole.AI,
        "Xin chào! Tôi có thể giúp gì cho bạn?",
    ),
    (
        mid(53),
        cid(6),
        uid(7),
        MessageSenderRole.CLIENT,
        "Tôi muốn biết thông tin về sản phẩm",
    ),
    (
        mid(54),
        cid(6),
        uid(10),
        MessageSenderRole.AI,
        "Chúng tôi có nhiều sản phẩm. Bạn quan tâm đến loại nào?",
    ),
    (mid(55), cid(6), uid(7), MessageSenderRole.CLIENT, "Sản phẩm mới nhất"),
    (
        mid(56),
        cid(6),
        uid(1),
        MessageSenderRole.ADMIN,
        "Let me show you our latest products with detailed specifications.",
    ),
    # Instagram channel conversation
    (
        mid(61),
        cid(7),
        uid(8),
        MessageSenderRole.CLIENT,
        "Love your Instagram posts! 💕",
    ),
    (
        mid(62),
        cid(7),
        uid(10),
        MessageSenderRole.AI,
        "Thank you so much! How can we help you today?",
    ),
    (
        mid(63),
        cid(7),
        uid(8),
        MessageSenderRole.CLIENT,
        "Is the item from your latest post still available?",
    ),
    (
        mid(64),
        cid(7),
        uid(10),
        MessageSenderRole.AI,
        "Yes! We still have stock. Would you like to place an order?",
    ),
    (mid(65), cid(7), uid(8), MessageSenderRole.CLIENT, "What colors do you have?"),
    (
        mid(66),
        cid(7),
        uid(1),
        MessageSenderRole.ADMIN,
        "We have black, white, blue, and pink. All colors are in stock!",
    ),
    # TikTok channel conversation
    (mid(71), cid(8), uid(9), MessageSenderRole.CLIENT, "Saw your TikTok video! 🔥"),
    (
        mid(72),
        cid(8),
        uid(10),
        MessageSenderRole.AI,
        "Thanks for watching! What caught your interest?",
    ),
    (
        mid(73),
        cid(8),
        uid(9),
        MessageSenderRole.CLIENT,
        "The product demo was amazing. How much is it?",
    ),
    (
        mid(74),
        cid(8),
        uid(10),
        MessageSenderRole.AI,
        "Great question! The price is $49.99 with free shipping.",
    ),
    (mid(75), cid(8), uid(9), MessageSenderRole.CLIENT, "Do you ship internationally?"),
    (
        mid(76),
        cid(8),
        uid(1),
        MessageSenderRole.ADMIN,
        "Yes! We ship worldwide. Shipping costs vary by location.",
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
        users_with_email = sum(1 for u in USERS if u.get("email"))
        channel_convs = sum(1 for c in CONVERSATIONS if "channel_conversation_id" in c)

        print("✓ Seeded database with test data:")
        print(f"  Users: {len(USERS)} total")
        print(f"    - {users_with_email} with email (Admin, Alice, Bob)")
        print("    - 1 AI bot")
        print(f"    - {len(USERS) - users_with_email - 1} channel-only")
        print(f"  Channels: {len(CHANNELS)} associations")
        print("    - Alice has BOTH email AND Telegram (multi-channel user)")
        print(
            f"  Conversations: {len(CONVERSATIONS)} ({channel_convs} channel, {len(CONVERSATIONS) - channel_convs} direct)"
        )
        print(f"  Messages: {len(MESSAGES)}")
        print("\n  Fixed UUIDs for easy testing:")
        print(f"    Admin User:      {uid(1)}")
        print(f"    Alice Smith:     {uid(2)} (has 2 conversations: direct + Telegram)")
        print(f"    Bob Johnson:     {uid(3)}")
        print(f"    AI Bot:          {uid(10)}")
        print(f"    Telegram User:   {uid(4)}")
        print(f"    WhatsApp User:   {uid(5)}")
        print(f"    Messenger User:  {uid(6)}")
        print(f"    Zalo User:       {uid(7)}")
        print(f"    Instagram User:  {uid(8)}")
        print(f"    TikTok User:     {uid(9)}")


if __name__ == "__main__":
    asyncio.run(seed_data())
