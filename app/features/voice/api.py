"""
Voice feature API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.features.voice.models import VoiceSessionStatus
from app.features.voice.schemas import (
    VoiceMessageCreate,
    VoiceMessageResponse,
    VoiceSessionCreate,
    VoiceSessionResponse,
    VoiceSessionStatusUpdate,
)
from app.features.voice.services.session_service import VoiceSessionServiceDep

router = APIRouter()


# === Session Management API ===


@router.post("/sessions", response_model=VoiceSessionResponse)
async def create_session(
    request: VoiceSessionCreate,
    session_service: VoiceSessionServiceDep,
) -> VoiceSessionResponse:
    """Create a new voice session."""
    session = await session_service.create_session(
        session_type=request.session_type,
        provider_type=request.provider_type,
        external_session_id=request.external_session_id,
        from_number=request.from_number,
        to_number=request.to_number,
    )
    return VoiceSessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[VoiceSessionResponse])
async def list_sessions(
    session_service: VoiceSessionServiceDep,
    limit: int = 10,
    status: VoiceSessionStatus | None = None,
) -> list[VoiceSessionResponse]:
    """List recent voice sessions."""
    sessions = await session_service.get_recent_sessions(
        limit=limit,
        status=status,
    )
    return [VoiceSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=VoiceSessionResponse)
async def get_session(
    session_id: UUID,
    session_service: VoiceSessionServiceDep,
) -> VoiceSessionResponse:
    """Get a specific voice session."""
    session = await session_service.get_by_id(session_id)
    return VoiceSessionResponse.model_validate(session)


@router.get(
    "/sessions/external/{external_id}",
    response_model=VoiceSessionResponse,
)
async def get_session_by_external_id(
    external_id: str,
    session_service: VoiceSessionServiceDep,
) -> VoiceSessionResponse:
    """Get a voice session by its external ID."""
    session = await session_service.get_session_by_external_id(external_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return VoiceSessionResponse.model_validate(session)


@router.patch("/sessions/{session_id}/status", response_model=VoiceSessionResponse)
async def update_session_status(
    session_id: UUID,
    request: VoiceSessionStatusUpdate,
    session_service: VoiceSessionServiceDep,
) -> VoiceSessionResponse:
    """Update voice session status."""
    session = await session_service.update_status(session_id, request.status)
    return VoiceSessionResponse.model_validate(session)


# === Message Management API ===


@router.post(
    "/sessions/{session_id}/messages",
    response_model=VoiceMessageResponse,
)
async def add_message(
    session_id: UUID,
    request: VoiceMessageCreate,
    session_service: VoiceSessionServiceDep,
) -> VoiceMessageResponse:
    """Add a message to a voice session."""
    message = await session_service.add_message(
        session_id=session_id,
        role=request.role,
        content=request.content,
    )
    return VoiceMessageResponse.model_validate(message)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[VoiceMessageResponse],
)
async def get_messages(
    session_id: UUID,
    session_service: VoiceSessionServiceDep,
    limit: int | None = None,
) -> list[VoiceMessageResponse]:
    """Get all messages for a voice session."""
    messages = await session_service.get_messages(session_id, limit=limit)
    return [VoiceMessageResponse.model_validate(m) for m in messages]
