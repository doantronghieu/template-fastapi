"""Voice chat service for processing conversations with LLM."""

from pathlib import Path
from typing import Annotated
from uuid import UUID

from app.features.voice.models import VoiceMessageRole
from app.features.voice.services.session_service import VoiceSessionService
from app.lib.llm.base import LLMProvider

# Project root for loading prompt files
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


def load_prompt(path: str) -> str | None:
    """Load prompt from file path relative to project root."""
    file_path = PROJECT_ROOT / path
    if file_path.exists():
        return file_path.read_text().strip()
    return None


class VoiceChatService:
    """Process voice chat with LLM and message persistence."""

    def __init__(
        self,
        session_service: Annotated[VoiceSessionService, "Voice session service"],
        llm_provider: Annotated[LLMProvider, "LLM provider for responses"],
        model: Annotated[str, "LLM model identifier for responses"],
        model_provider: Annotated[str, "Model provider"],
        system_prompt_path: Annotated[str | None, "Path to system prompt .md file"] = None,
    ) -> None:
        self.session_service = session_service
        self.llm_provider = llm_provider
        self.model = model
        self.model_provider = model_provider
        self.system_prompt = load_prompt(system_prompt_path) if system_prompt_path else None

    async def process_chat(
        self,
        session_id: Annotated[UUID, "Voice session UUID"],
        text: Annotated[str, "User's transcribed speech"],
    ) -> str:
        """Process user message and generate AI response."""
        # Save user message
        await self.session_service.add_message(
            session_id=session_id,
            role=VoiceMessageRole.USER,
            content=text,
        )

        # Build conversation history (exclude current message)
        messages = await self.session_service.get_messages(session_id)
        history = (
            [
                {
                    "role": m.role.value if hasattr(m.role, "value") else m.role,
                    "content": m.content,
                }
                for m in messages[:-1]
            ]
            if len(messages) > 1
            else None
        )

        # Format prompt with system message and history context
        formatted_prompt = self.llm_provider.format_prompt(text, history, self.system_prompt)

        # Generate LLM response
        response_text = await self.llm_provider.invoke_model(
            prompt=formatted_prompt,
            mode="invoke",
            model_name=self.model,
            model_provider=self.model_provider,
        )

        # Save assistant message
        await self.session_service.add_message(
            session_id=session_id,
            role=VoiceMessageRole.ASSISTANT,
            content=response_text,
        )

        return response_text
