"""API router for omni-channel feature.

Combines users and messaging endpoints into single router.
See docs/patterns/vertical-slice-architecture.md for structure guidelines.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import PaginationParams
from app.services import PaginatedResponse, PaginationType
from app.utils import serialize_enum

from .schemas.api import (
    ConversationHistoryResponse,
    ConversationListResponse,
    ConversationMessagesQuery,
    MessageCreate,
    MessageHistoryItem,
    MessageResponse,
    UserCreate,
    UserDetailResponse,
    UserFullResponse,
    UserUpdate,
)
from .service import MessagingServiceDep, UserServiceDep

router = APIRouter()

# =============================================================================
# Users Endpoints
# =============================================================================


@router.post(
    "/users", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_in: UserCreate,
    service: UserServiceDep,
):
    """Create a new user."""
    user = await service.create(user_in)
    return user


@router.get("/users", response_model=PaginatedResponse)
async def list_users(
    service: UserServiceDep,
    pagination: Annotated[PaginationParams, Depends()],
    role: str | None = Query(None, description="Filter by role"),
    email_like: str | None = Query(None, description="Filter by email pattern"),
):
    """List users with pagination and filtering."""
    filters = {}
    if role:
        filters["role"] = role
    if email_like:
        filters["email__ilike"] = f"%{email_like}%"

    result = await service.get_multi(
        limit=pagination.limit or 10,
        offset=pagination.offset or 0,
        cursor=pagination.cursor,
        pagination_type=pagination.pagination_type or PaginationType.OFFSET,
        order_by=pagination.order_by,
        filters=filters if filters else None,
    )
    return result


@router.get("/users/{user_id}", response_model=UserFullResponse)
async def get_user_details(
    user_id: UUID,
    service: UserServiceDep,
):
    """Get full user details including profile and all channels."""
    user = await service.get_user_details(user_id)

    if not user:
        raise HTTPException(404, f"User {user_id} not found")

    return user


@router.get("/users/{user_id}/simple", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    service: UserServiceDep,
):
    """Get user by ID without eager-loading relationships."""
    user = await service.get_by_id(user_id)
    return user


@router.patch("/users/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    service: UserServiceDep,
):
    """Update user (partial update)."""
    user = await service.update(user_id, user_in)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: UserServiceDep,
):
    """Delete user by ID."""
    await service.delete(user_id)
    return None


@router.get("/users/{user_id}/conversations", response_model=ConversationListResponse)
async def get_user_conversations(
    user_id: UUID,
    service: MessagingServiceDep,
):
    """Get all conversations for a user with message counts."""
    conversations = await service.get_user_conversations(user_id)
    return ConversationListResponse(
        conversations=conversations,
        next_cursor=None,
        has_more=False,
    )


# =============================================================================
# Messaging Endpoints
# =============================================================================


@router.post("/messaging/messages", response_model=MessageResponse)
async def create_message(
    data: MessageCreate,
    service: MessagingServiceDep,
):
    """Create a message with auto-provisioning of user and conversation.

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


@router.get("/messaging/conversations", response_model=ConversationListResponse)
async def get_all_conversations(
    service: MessagingServiceDep,
    limit: int = Query(50, ge=1, le=100),
    cursor: UUID | None = Query(None),
):
    """Get all conversations across all users (admin endpoint).

    Returns conversations with user info, channel type, and last message preview.
    Supports cursor-based pagination for infinite scroll.
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


@router.post(
    "/messaging/conversations/messages", response_model=ConversationHistoryResponse
)
async def get_conversation_messages(
    query: ConversationMessagesQuery,
    service: MessagingServiceDep,
):
    """Get messages for a conversation with formatted history.

    Returns messages in conversation_history format with role, content, and timestamp.
    Supports pagination via before_message_id for loading older messages.
    """
    conversation, messages, next_cursor = await service.get_conversation_messages(
        conversation_id=query.conversation_id,
        channel_conversation_id=query.channel_conversation_id,
        limit=query.limit,
        before_message_id=query.before_message_id,
        order=query.order,
        reverse=query.reverse,
    )

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
