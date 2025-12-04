"""LiveKit Voice Agent implementation.

This agent runs as a separate process and handles real-time voice
conversations using LiveKit Agents framework.

Flow:
1. Agent joins LiveKit room when participant joins
2. Receives audio from user via LiveKit
3. Transcribes speech using DeepGram STT
4. Processes via VoiceChatService (direct import, no HTTP)
5. Synthesizes speech using DeepGram TTS
6. Sends audio response back to user via LiveKit
"""

import logging
from uuid import UUID

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)
from livekit.plugins import deepgram, langchain, silero
from typing_extensions import Annotated, TypedDict

# Import config first - it loads env files into os.environ via python-dotenv
from app.integrations.livekit.workers.config import agent_settings

# Suppress noisy logs from external libraries
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

for lib in ("openai", "httpcore", "httpx", "asyncio"):
    logging.getLogger(lib).setLevel(logging.WARNING)


class VoiceChatBackend:
    """Backend using direct VoiceChatService import (no HTTP calls).

    Creates fresh DB session per operation to avoid connection timeouts.
    """

    def __init__(self, room_name: str) -> None:
        self.room_name = room_name
        self.session_id: UUID | None = None

    async def _get_or_create_voice_session(self) -> UUID:
        """Get or create voice session with fresh DB connection."""
        if self.session_id:
            return self.session_id

        from sqlalchemy.exc import IntegrityError

        from app.core.database import async_session_maker
        from app.features.voice.models import VoiceSessionType
        from app.features.voice.services.session_service import VoiceSessionService

        async with async_session_maker() as db:
            session_service = VoiceSessionService(db)
            session = await session_service.get_session_by_external_id(self.room_name)

            if not session:
                try:
                    session = await session_service.create_session(
                        session_type=VoiceSessionType.WEB,
                        provider_type="livekit",
                        external_session_id=self.room_name,
                    )
                except IntegrityError:
                    # Race condition: another process created it first, fetch it
                    await db.rollback()
                    session = await session_service.get_session_by_external_id(
                        self.room_name
                    )

            self.session_id = session.id
            return self.session_id

    async def chat(self, text: str) -> str:
        """Process message using fresh DB connection per call."""
        from app.core.database import async_session_maker
        from app.features.voice.services.chat_service import VoiceChatService
        from app.features.voice.services.session_service import VoiceSessionService
        from app.lib.llm.factory import get_llm_provider

        try:
            session_id = await self._get_or_create_voice_session()
            # Fresh DB session for each chat to avoid connection timeout
            async with async_session_maker() as db:
                session_service = VoiceSessionService(db)
                chat_service = VoiceChatService(
                    session_service,
                    get_llm_provider(),
                    model=agent_settings.LLM_MODEL,
                    model_provider=agent_settings.LLM_MODEL_PROVIDER,
                    system_prompt_path=agent_settings.SYSTEM_PROMPT_PATH,
                )
                return await chat_service.process_chat(session_id, text)
        except Exception as e:
            logger.error(f"Error processing chat: {e}")
            return "I'm sorry, I couldn't process your request."


class AgentState(TypedDict):
    """State for the voice agent workflow.

    Uses add_messages reducer to automatically append new messages.
    """

    messages: Annotated[list[AnyMessage], add_messages]


def create_voice_workflow(backend: VoiceChatBackend) -> CompiledStateGraph:
    """Create LangGraph workflow for voice conversation."""

    async def process_message(state: AgentState) -> dict:
        """Process user message through VoiceChatService.

        Returns only new messages - add_messages reducer handles appending.
        """
        messages = state.get("messages", [])
        if not messages:
            return {"messages": []}

        last_message = messages[-1]

        # Handle HumanMessage - user's spoken input
        if isinstance(last_message, HumanMessage):
            response_text = await backend.chat(last_message.content)
            return {"messages": [AIMessage(content=response_text)]}

        # Handle SystemMessage - initial greeting
        # When generate_reply(instructions=...) is called, only SystemMessage is passed
        if isinstance(last_message, SystemMessage) and len(messages) == 1:
            response_text = await backend.chat(
                "The user just connected. Generate a brief, friendly greeting."
            )
            return {"messages": [AIMessage(content=response_text)]}
        return {"messages": []}

    workflow = StateGraph(AgentState)
    workflow.add_node("process", process_message)
    workflow.add_edge(START, "process")
    workflow.add_edge("process", END)

    return workflow.compile()


def prewarm(proc: JobProcess) -> None:
    """Prewarm function - load VAD model."""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext) -> None:
    """Voice agent entrypoint - called for each room connection."""
    logger.info(f"Agent connecting to room: {ctx.room.name}")
    await ctx.connect()

    backend = VoiceChatBackend(ctx.room.name)
    workflow = create_voice_workflow(backend)

    agent = Agent(
        instructions="You are a helpful voice assistant. Respond concisely and naturally.",
        llm=langchain.LLMAdapter(workflow),
    )

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(
            model=agent_settings.DEEPGRAM_STT_MODEL,
            language="en",
            api_key=agent_settings.DEEPGRAM_API_KEY,
        ),
        tts=deepgram.TTS(
            model=agent_settings.DEEPGRAM_TTS_VOICE,
            api_key=agent_settings.DEEPGRAM_API_KEY,
        ),
    )

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(
        instructions="Greet the user and ask how you can help them today."
    )


def main() -> None:
    """Run the LiveKit agent."""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            api_key=agent_settings.LIVEKIT_API_KEY,
            api_secret=agent_settings.LIVEKIT_API_SECRET,
            ws_url=agent_settings.LIVEKIT_URL,
        )
    )


if __name__ == "__main__":
    main()
