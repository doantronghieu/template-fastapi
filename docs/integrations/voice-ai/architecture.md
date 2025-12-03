# Voice AI Architecture

## Overview

```
+------------------------------------------------------------------------+
|                              ENTRY POINTS                              |
+------------------------------------------------------------------------+
|  Web Client                              Phone Call                    |
|  (LiveKit JS)                            (PSTN)                        |
|       |                                      |                         |
|       v                                      v                         |
|  LiveKit Room  <-- (transfer) -->  Telnyx SIP                          |
|       |                                      |                         |
|       +---------------+----------------------+                         |
|                       |                                                |
|                       v                                                |
|               Voice Agent Worker                                       |
|               (LiveKit Agents)                                         |
|                       |                                                |
|          +------------+------------+                                   |
|          |            |            |                                   |
|          v            v            v                                   |
|     Deepgram     LangGraph    Deepgram                                 |
|       STT        Workflow       TTS                                    |
|          |            |            |                                   |
|          +------------+------------+                                   |
|                       |                                                |
|                       v                                                |
|             VoiceChatService                                           |
|             (DB persistence)                                           |
+------------------------------------------------------------------------+
```

## Layer Structure

### 1. Libraries (`app/lib/`) - Provider Abstractions

| Library | Purpose | Protocols |
|---------|---------|-----------|
| `lib/voice/` | STT/TTS abstraction | `STTProvider`, `TTSProvider` |
| `lib/telephony/` | Phone call abstraction | `TelephonyProvider` |
| `lib/llm/` | LLM abstraction | `LLMProvider` |

Each library defines:
- `base.py` - Protocol definitions
- `config.py` - Provider type enums
- `factory.py` - Provider instantiation
- `dependencies.py` - FastAPI dependencies

### 2. Integrations (`app/integrations/`) - Provider Implementations

| Integration | Implements | Services |
|-------------|------------|----------|
| `livekit/` | Real-time audio | TokenService, RoomService, VoiceAgentWorker |
| `deepgram/` | STTProvider, TTSProvider | DeepgramSTT, DeepgramTTS |
| `telnyx/` | TelephonyProvider | CallService, Webhooks |

### 3. Features (`app/features/voice/`) - Business Logic

| Component | Purpose |
|-----------|---------|
| `models.py` | VoiceSession, VoiceMessage (SQLModel) |
| `services/session_service.py` | Session CRUD, message persistence |
| `services/chat_service.py` | LLM conversation with system prompt |
| `prompts/system.md` | Configurable system instructions |

## Data Flow

### Web Voice Chat

```
1. Client connects to LiveKit room
2. Voice Agent Worker joins room (auto-dispatch)
3. User speaks -> Deepgram STT -> text
4. Text -> VoiceChatService -> LLM -> response
5. Response -> Deepgram TTS -> audio -> user
```

### Phone Call (Inbound)

```
1. Call arrives at Telnyx number
2. Webhook: call.initiated -> CallService
3. Create VoiceSession, LiveKit room
4. Answer call, transfer to SIP URI
5. Voice Agent joins -> same flow as web
```

## Key Files

```
app/
+-- lib/
|   +-- voice/
|   |   +-- base.py          # STTProvider, TTSProvider protocols
|   |   +-- factory.py       # get_stt_provider(), get_tts_provider()
|   +-- telephony/
|   |   +-- base.py          # TelephonyProvider protocol
|   |   +-- factory.py       # get_telephony_provider()
|   +-- llm/
|       +-- base.py          # LLMProvider with format_prompt()
|       +-- factory.py       # get_llm_provider()
+-- integrations/
|   +-- livekit/
|   |   +-- api.py           # Token, room, test endpoints
|   |   +-- services/        # TokenService, RoomService
|   |   +-- workers/
|   |       +-- voice_agent.py   # LangGraph workflow, VoiceChatBackend
|   |       +-- config.py        # AgentSettings (STT, TTS, LLM, prompt path)
|   +-- deepgram/
|   |   +-- stt.py           # DeepgramSTT (STTProvider)
|   |   +-- tts.py           # DeepgramTTS (TTSProvider)
|   +-- telnyx/
|       +-- webhooks.py      # Call event handlers
|       +-- services/call_service.py  # Inbound call -> LiveKit transfer
+-- features/voice/
    +-- models.py            # VoiceSession, VoiceMessage
    +-- services/
    |   +-- session_service.py   # Session/message CRUD
    |   +-- chat_service.py      # LLM chat with system prompt
    +-- prompts/system.md        # Default system instructions
```

## Configuration

| Env File | Variables |
|----------|-----------|
| `envs/integrations/livekit.env` | LIVEKIT_URL, API_KEY, API_SECRET, BACKEND_URL |
| `envs/integrations/deepgram.env` | API_KEY, STT_MODEL, TTS_VOICE |
| `envs/integrations/telnyx.env` | API_KEY, SIP_TRUNK_ID, PHONE_NUMBER |
| `envs/workers/voice-agent.env` | LLM_MODEL, LLM_MODEL_PROVIDER, SYSTEM_PROMPT_PATH |

## Database Models

```sql
voice_sessions
+-- id (UUID)
+-- external_session_id (room name / call ID)
+-- provider_type (livekit / telnyx)
+-- session_type (web / phone_inbound / phone_outbound)
+-- status (initiated / active / completed / failed)
+-- from_number, to_number (phone only)
+-- started_at, ended_at

voice_messages
+-- id (UUID)
+-- session_id (FK)
+-- role (user / assistant)
+-- content (text)
```

## Adding New Providers

### New STT/TTS Provider

1. Implement `STTProvider` or `TTSProvider` protocol in `app/integrations/{provider}/`
2. Add provider type to `app/lib/voice/config.py`
3. Register in `app/lib/voice/factory.py`

### New Telephony Provider

1. Implement `TelephonyProvider` protocol
2. Add provider type to `app/lib/telephony/config.py`
3. Register in `app/lib/telephony/factory.py`
4. Add webhook handlers
