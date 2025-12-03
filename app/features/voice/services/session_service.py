"""Voice session service for managing sessions and messages."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.core import SessionDep
from app.features.voice.models import (
    VoiceMessage,
    VoiceMessageRole,
    VoiceSession,
    VoiceSessionStatus,
    VoiceSessionType,
)
from app.services.base_crud import BaseCRUDService


class VoiceSessionService(BaseCRUDService[VoiceSession]):
    """Manage voice sessions and messages."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VoiceSession, session)

    async def create_session(
        self,
        session_type: Annotated[VoiceSessionType, "Type of voice session"],
        provider_type: Annotated[str, "Provider identifier"] = "livekit",
        from_number: Annotated[str | None, "Caller phone number (E.164)"] = None,
        to_number: Annotated[str | None, "Called phone number (E.164)"] = None,
        external_session_id: Annotated[
            str | None, "External ID (auto-generated if None)"
        ] = None,
    ) -> VoiceSession:
        """Create a new voice session."""
        voice_session = VoiceSession(
            external_session_id=external_session_id or f"voice-{uuid4().hex[:12]}",
            provider_type=provider_type,
            session_type=session_type,
            status=VoiceSessionStatus.INITIATED,
            from_number=from_number,
            to_number=to_number,
        )
        self.session.add(voice_session)
        await self.session.commit()
        await self.session.refresh(voice_session)
        return voice_session

    async def get_session_by_external_id(
        self,
        external_id: Annotated[str, "External session identifier"],
    ) -> VoiceSession | None:
        """Get session by external session ID."""
        result = await self.session.execute(
            select(VoiceSession).where(VoiceSession.external_session_id == external_id)
        )
        return result.scalar_one_or_none()

    async def _apply_status_change(
        self,
        voice_session: VoiceSession,
        status: VoiceSessionStatus,
    ) -> VoiceSession:
        """Apply status change with automatic timing. Internal helper."""
        voice_session.status = status

        if status == VoiceSessionStatus.ACTIVE:
            voice_session.started_at = datetime.now(UTC)
        elif status in (VoiceSessionStatus.COMPLETED, VoiceSessionStatus.FAILED):
            voice_session.ended_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(voice_session)
        return voice_session

    async def update_status(
        self,
        session_id: Annotated[UUID, "Session UUID"],
        status: Annotated[VoiceSessionStatus, "New status to set"],
    ) -> VoiceSession:
        """Update session status by UUID."""
        voice_session = await self.get_by_id(session_id)
        return await self._apply_status_change(voice_session, status)

    async def update_status_by_external_id(
        self,
        external_id: Annotated[str, "External session identifier"],
        status: Annotated[VoiceSessionStatus, "New status to set"],
    ) -> VoiceSession | None:
        """Update session status by external ID. Returns None if not found."""
        voice_session = await self.get_session_by_external_id(external_id)
        if not voice_session:
            return None
        return await self._apply_status_change(voice_session, status)

    async def add_message(
        self,
        session_id: Annotated[UUID, "Session UUID"],
        role: Annotated[VoiceMessageRole, "Message sender role"],
        content: Annotated[str, "Message text content"],
    ) -> VoiceMessage:
        """Add a message to a session."""
        message = VoiceMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_messages(
        self,
        session_id: Annotated[UUID, "Session UUID"],
        limit: Annotated[int | None, "Max messages to return"] = None,
    ) -> list[VoiceMessage]:
        """Get all messages for a session ordered by creation time."""
        query = (
            select(VoiceMessage)
            .where(VoiceMessage.session_id == session_id)
            .order_by(VoiceMessage.created_at)
        )

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_sessions(
        self,
        limit: Annotated[int, "Max sessions to return"] = 10,
        status: Annotated[VoiceSessionStatus | None, "Status filter"] = None,
        session_type: Annotated[VoiceSessionType | None, "Session type filter"] = None,
    ) -> list[VoiceSession]:
        """Get recent voice sessions with optional filtering."""
        query = select(VoiceSession).order_by(VoiceSession.created_at.desc())

        if status:
            query = query.where(VoiceSession.status == status)
        if session_type:
            query = query.where(VoiceSession.session_type == session_type)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())


async def get_voice_session_service(session: SessionDep) -> VoiceSessionService:
    """Dependency to get VoiceSessionService instance."""
    return VoiceSessionService(session)


VoiceSessionServiceDep = Annotated[
    VoiceSessionService,
    Depends(get_voice_session_service),
]
