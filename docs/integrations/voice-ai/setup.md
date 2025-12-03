# Voice AI Integration

Real-time voice AI using LiveKit, Deepgram (STT/TTS), and Telnyx (phone).

## Architecture

```
Web Client → LiveKit Room → Voice Agent → Deepgram STT → LLM → Deepgram TTS → Audio Response
Phone Call → Telnyx → SIP Transfer → LiveKit Room → Voice Agent → ...
```

## Setup

### 1. LiveKit (cloud.livekit.io)

1. Create project → Copy credentials to `envs/integrations/livekit.env`:
   ```
   LIVEKIT_API_KEY=APIxxxxxx
   LIVEKIT_API_SECRET=xxxxx
   LIVEKIT_URL=wss://your-project.livekit.cloud
   ```

2. For phone integration: Settings → SIP → Add Trunk (Provider: Telnyx)

### 2. Deepgram (console.deepgram.com)

1. Create API key → Copy to `envs/integrations/deepgram.env`:
   ```
   DEEPGRAM_API_KEY=xxxxx
   DEEPGRAM_STT_MODEL=nova-3
   DEEPGRAM_TTS_VOICE=aura-asteria-en
   ```

### 3. Telnyx - Phone Calls (portal.telnyx.com)

1. **API Key**: API Keys → Create → Copy to `TELNYX_API_KEY`

2. **Phone Number**: Numbers → Buy → Copy to `TELNYX_PHONE_NUMBER` (E.164: `+15551234567`)

3. **SIP Trunk**: SIP Trunking → Create → Set termination URI to LiveKit domain → Copy ID to `TELNYX_SIP_TRUNK_ID`

4. **Webhook**: Phone Numbers → Voice Settings → Set URL:
   ```
   https://your-domain.com/api/integrations/telnyx/webhooks/calls
   ```
   Copy signing secret to `TELNYX_WEBHOOK_SECRET`

5. Update `envs/integrations/telnyx.env`:
   ```
   TELNYX_API_KEY=KEYxxxxxxxx
   TELNYX_SIP_TRUNK_ID=trunk_id
   TELNYX_PHONE_NUMBER=+15551234567
   TELNYX_WEBHOOK_SECRET=secret
   ```

### 4. Enable Integrations

In `.env`:
```
ENABLED_INTEGRATIONS=livekit,telnyx,deepgram
```

## Running

```bash
# Terminal 1: FastAPI server
make dev

# Terminal 2: Voice agent worker
cd app/integrations/livekit/workers
python voice_agent.py dev
```

## Testing

**Web**: http://localhost:8000/api/integrations/livekit/test

**Phone**: Call your Telnyx number → Auto-transfers to LiveKit room → Agent joins

## Development (Local Webhook)

```bash
ngrok http 8000
# Update Telnyx webhook URL to ngrok URL
```

## Files

- `app/integrations/livekit/` - LiveKit integration, test UI
- `app/integrations/deepgram/` - STT/TTS services
- `app/integrations/telnyx/` - Phone call handling
- `app/integrations/livekit/workers/voice_agent.py` - Agent worker
- `app/features/voice/` - Voice session models, chat service
