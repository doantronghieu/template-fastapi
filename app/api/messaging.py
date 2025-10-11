"""API endpoints for messaging operations."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.schemas.messaging import (
    ConversationHistoryResponse,
    ConversationListResponse,
    ConversationMessagesQuery,
    MessageCreate,
    MessageHistoryItem,
    MessageResponse,
)
from app.services.messaging_service import MessagingServiceDep
from app.utils import serialize_enum

router = APIRouter()


@router.post("/messages", response_model=MessageResponse)
async def create_message(
    data: MessageCreate,
    service: MessagingServiceDep,
):
    """
    Create a message with auto-provisioning of user and conversation.

    Supports two modes:
    - Channel mode: Provide channel_id, channel_type, channel_conversation_id
    - Internal mode: Provide user_id, conversation_id
    """
    message = await service.create_message(
        content=data.content,
        sender_role=data.sender_role,
        channel_id=data.channel_id,
        channel_type=data.channel_type,
        channel_conversation_id=data.channel_conversation_id,
        user_id=data.user_id,
        conversation_id=data.conversation_id,
    )
    return message


@router.get("/conversations", response_model=ConversationListResponse)
async def get_all_conversations(
    service: MessagingServiceDep,
    limit: int = Query(50, ge=1, le=100),
    cursor: UUID | None = Query(None),
):
    """
    Get all conversations across all users (admin endpoint).

    Returns conversations with user info, channel type, and last message preview.
    Supports cursor-based pagination for infinite scroll.

    Args:
        limit: Maximum number of conversations to return (1-100, default 50)
        cursor: Conversation UUID to start after (for pagination)
    """
    conversations, next_cursor, has_more = await service.get_all_conversations(
        limit=limit,
        cursor=cursor,
    )

    return ConversationListResponse(
        conversations=conversations,
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.post("/conversations/messages", response_model=ConversationHistoryResponse)
async def get_conversation_messages(
    query: ConversationMessagesQuery,
    service: MessagingServiceDep,
):
    """
    Get messages for a conversation with formatted history.

    Returns messages in conversation_history format with role, content, and timestamp.
    Supports pagination via before_message_id for loading older messages.

    Note: POST method used (instead of GET) to support request body for complex
    query parameters and enable schema-level validation.
    """
    conversation, messages, next_cursor = await service.get_conversation_messages(
        conversation_id=query.conversation_id,
        channel_conversation_id=query.channel_conversation_id,
        limit=query.limit,
        before_message_id=query.before_message_id,
        order=query.order,
        reverse=query.reverse,
    )

    # Format as typed conversation history
    conversation_history = [
        MessageHistoryItem(
            role=serialize_enum(msg.sender_role),
            content=msg.content,
            created_at=msg.created_at.isoformat(),
        )
        for msg in messages
    ]

    return ConversationHistoryResponse(
        conversation_id=conversation.id,
        conversation_history=conversation_history,
        next_cursor=next_cursor,
    )


@router.get("/users/{user_id}/conversations", response_model=ConversationListResponse)
async def get_user_conversations(
    user_id: UUID,
    service: MessagingServiceDep,
):
    """Get all conversations for a user with message counts."""
    conversations = await service.get_user_conversations(user_id)
    return {"conversations": conversations}
