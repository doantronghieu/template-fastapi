"""Seed database with test data for admin interface."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import async_session_maker
from app.models import Conversation, Message, User, UserRole

# Test data constants
TEST_USERS = [
    {
        "email": "admin@example.com",
        "name": "Admin User",
        "role": UserRole.ADMIN,
        "profile": {"department": "Engineering"},
    },
    {
        "email": "client@example.com",
        "name": "Client User",
        "role": UserRole.CLIENT,
        "profile": {"company": "Acme Corp"},
    },
    {
        "email": "ai@example.com",
        "name": "AI Assistant",
        "role": UserRole.AI,
        "profile": {"model": "gpt-4"},
    },
]

TEST_CONVERSATIONS = [
    {"title": "Welcome Conversation"},
    {"title": "Support Request"},
]

TEST_MESSAGES = [
    {"conv_idx": 0, "user_idx": 1, "content": "Hello! I need help getting started."},
    {
        "conv_idx": 0,
        "user_idx": 2,
        "content": "Welcome! I'm here to help. What would you like to know?",
    },
    {"conv_idx": 0, "user_idx": 1, "content": "How do I create a new project?"},
    {"conv_idx": 1, "user_idx": 1, "content": "I'm having an issue with my account."},
    {
        "conv_idx": 1,
        "user_idx": 0,
        "content": "I can help with that. What seems to be the problem?",
    },
]


async def seed_data() -> None:
    """Create test users, conversations, and messages."""
    async with async_session_maker() as session:
        session: AsyncSession
        # Check if data already exists
        result = await session.execute(select(User))
        if result.scalars().first():
            print("✓ Test data already exists")
            return

        # Create users
        users = [User(**user_data) for user_data in TEST_USERS]
        session.add_all(users)
        await session.commit()
        for user in users:
            await session.refresh(user)

        # Create conversations (assigned to client user)
        client_user = users[1]
        conversations = [
            Conversation(user_id=client_user.id, **conv_data)
            for conv_data in TEST_CONVERSATIONS
        ]
        session.add_all(conversations)
        await session.commit()
        for conv in conversations:
            await session.refresh(conv)

        # Create messages
        messages = [
            Message(
                conversation_id=conversations[msg_data["conv_idx"]].id,
                user_id=users[msg_data["user_idx"]].id,
                content=msg_data["content"],
            )
            for msg_data in TEST_MESSAGES
        ]
        session.add_all(messages)
        await session.commit()

        print(
            f"✓ Created {len(messages)} messages in {len(conversations)} "
            f"conversations for {len(users)} users"
        )
        for user in users:
            print(f"  - {user.name}: {user.email}")


if __name__ == "__main__":
    asyncio.run(seed_data())
