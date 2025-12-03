"""LiveKit token service for generating access tokens."""

from datetime import timedelta
from functools import lru_cache
from typing import Annotated

from livekit import api

from app.integrations.livekit.config import livekit_settings


class TokenService:
    """Generate LiveKit access tokens for participants.

    Tokens are JWTs signed with the API secret that grant
    specific permissions for room access.
    """

    def create_token(
        self,
        room_name: Annotated[str, "Name of the room to join"],
        participant_name: Annotated[str, "Identity for the participant"],
        can_publish: Annotated[bool, "Allow publishing audio/video"] = True,
        can_subscribe: Annotated[bool, "Allow subscribing to others"] = True,
        is_agent: Annotated[bool, "Mark as agent participant (server-side)"] = False,
        ttl_seconds: Annotated[int, "Token validity duration in seconds"] = 3600,
    ) -> str:
        """Generate JWT access token for room."""
        token = api.AccessToken(
            livekit_settings.LIVEKIT_API_KEY,
            livekit_settings.LIVEKIT_API_SECRET,
        )

        # Set identity and display name
        token.with_identity(participant_name)
        token.with_name(participant_name)
        token.with_ttl(timedelta(seconds=ttl_seconds))

        # Configure grants
        grants = api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=can_publish,
            can_subscribe=can_subscribe,
        )

        if is_agent:
            grants.agent = True

        token.with_grants(grants)

        return token.to_jwt()


@lru_cache(maxsize=1)
def get_token_service() -> TokenService:
    """Cached singleton."""
    return TokenService()
