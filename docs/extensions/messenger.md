# Facebook Messenger Integration

AI-powered chatbot integration with Facebook Messenger using FastAPI, Celery, and Groq LLM.

---

## Architecture

```
User Message → Facebook → Webhook → FastAPI → Celery → LLM → Database
                            ↓                    ↓
                      200 OK (fast)        Send Response
```

### Flow

1. **Webhook Receive** (FastAPI)
   - Verify HMAC signature
   - Parse message payload
   - Check rate limit (Redis)
   - Queue Celery task
   - Return 200 OK immediately (<20s requirement)

2. **Background Processing** (Celery)
   - Save user message to database
   - Fetch conversation history (last 50 messages)
   - Format as structured prompt
   - Call Groq LLM (GPT-OSS-120B)
   - Save AI response to database
   - Send via Facebook Send API

3. **LLM Context**
   ```
   <SYSTEM>[instructions]</SYSTEM>
   <HISTORY>[previous conversation]</HISTORY>
   <CURRENT_USER_QUERY>[latest message]</CURRENT_USER_QUERY>
   ```

### Components

**API Layer**
- `app/api/webhooks/messenger.py` - Receive webhooks (GET verification, POST receive)
- `app/api/webhooks/router.py` - Webhook aggregator for multiple services
- `app/api/integrations/messenger.py` - Send messages to Messenger users
- `app/api/pages.py` - Privacy policy endpoint

**Integration Layer**
- `app/integrations/messenger/client.py` - MessengerClient (Send API, signature verification)
- `app/integrations/messenger/webhook.py` - Webhook payload parsing
- `app/integrations/messenger/types.py` - TypedDict for Facebook payload structure
- `app/integrations/messenger/dependencies.py` - DI providers

**Services**
- `app/features/omni_channel/services/chat_service.py` - AI response generation with retry logic
- `app/features/omni_channel/services/messaging_service.py` - User/conversation/message management
- `app/services/rate_limiter/redis_rate_limiter.py` - Redis sliding window

**Utilities**
- `app/lib/utils/retry.py` - Async retry decorator with exponential backoff

**Tasks**
- `app/features/omni_channel/tasks/channel_tasks.py` - Celery message processing

**Database** (existing tables)
- `users` - Auto-created from channel interactions
- `conversations` - Per-user conversation threads
- `messages` - All messages with sender_role (CLIENT/AI)
- `user_channels` - Links users to external channel IDs

---

## API Endpoints

### Webhook Endpoints (Incoming from Facebook)

```
GET  /api/webhooks/messenger   # Webhook verification
POST /api/webhooks/messenger   # Receive messages
```

### Integration Endpoints (Outgoing to Facebook)

```
POST /api/integrations/messenger/send
```

**Request:**
```json
{
  "recipient_id": "1234567890",
  "text": "Hello from API"
}
```

**Response:**
```json
{
  "recipient_id": "1234567890",
  "message_id": "m_abc123xyz"
}
```

**Use cases:**
- Send proactive messages to users
- Broadcast announcements
- Test message sending manually
- Integration with other systems

---

## Quick Setup

### 1. Prerequisites

```bash
# Start services
make dev          # Terminal 1: FastAPI
make infra-up     # Terminal 2: Celery + Redis
make ngrok        # Terminal 3: Expose localhost

# Get ngrok URL
curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*' | head -1
# Output: https://abc123.ngrok-free.app
```

### 2. Configure Environment

```bash
# .env
FACEBOOK_PAGE_ACCESS_TOKEN=EAA...      # From Page settings
FACEBOOK_VERIFY_TOKEN=your_secure_token # Custom (your choice)
FACEBOOK_APP_SECRET=abc123...          # From App settings
FACEBOOK_GRAPH_API_VERSION=v24.0       # Current version
GROQ_API_KEY=gsk_...                   # From console.groq.com
CONTACT_EMAIL=your@email.com           # For privacy policy
```

**Get credentials:**
- **Page Token:** App Dashboard → Messenger → Settings → Access Tokens → Generate Token
- **App Secret:** App Dashboard → Settings → Basic → App Secret (Show)
- **Verify Token:** Any secure string (you choose)

### 3. Facebook App Setup

**Create App:**
1. https://developers.facebook.com/apps → Create App
2. Choose "Business" type
3. Add Messenger product

**Configure Webhook:**
1. Messenger → Settings → Webhooks → Add Callback URL
2. Enter:
   - URL: `https://abc123.ngrok-free.app/api/webhooks/messenger`
   - Token: `your_secure_token` (must match .env)
3. Click "Verify and Save" → Should show ✅
4. Click "Add Subscriptions" → Check ✅ `messages` → Save
   - Webhook → Subscribe to "messages" event
   - Access Tokens → Page shows "Subscribed"

**Connect Page:**
1. Messenger → Settings → Access Tokens
2. Click "Add or Remove Pages" → Select Page → Grant permissions
3. Click "Generate Token" → Copy to .env
4. Click "Subscribe" button next to your Page

### 4. Test

```bash
# Watch logs
Terminal 1: make dev
Terminal 2: make infra-logs

# Send message to your Page (as admin, works in Development Mode)
# Expected logs:
INFO: Queued task: sender=123 task_id=abc-123
INFO: Message sent: sender=123 msg_id=m_123

# Should receive AI response in Messenger within 3-5 seconds
```

---

## Configuration

### Required Variables

```bash
FACEBOOK_PAGE_ACCESS_TOKEN=    # Page-specific access token
FACEBOOK_VERIFY_TOKEN=         # Custom webhook verification token
FACEBOOK_APP_SECRET=           # App secret for signature verification
GROQ_API_KEY=                  # Groq API key for LLM
CONTACT_EMAIL=                 # Email for privacy policy
```

### Optional Variables

```bash
FACEBOOK_GRAPH_API_VERSION=v24.0                    # Default: v24.0
FACEBOOK_RATE_LIMIT_MESSAGES_PER_MINUTE=10         # Default: 10
```

---

## Security

- **HMAC SHA256 signature verification** on all webhook requests
- **Constant-time comparison** to prevent timing attacks
- **Rate limiting** via Redis (10 msg/min per user, configurable)
- **Environment variables** for all secrets (never hardcoded)
- **URL-encoded database credentials** (handles special characters)

---

## Production Deployment

### Facebook App Review

**Testing without review:**
- Development Mode allows admin/developer accounts to test
- No app review needed for testing

**Production (real users):**
- Publish app requires App Review approval
- Requirements:
  - App icon (1024x1024 PNG)
  - Privacy policy URL (auto-configured: `/privacy`)
  - Screencast (60-90 seconds showing bot interaction)
  - Description of use case

**Submit for review:**
1. App Dashboard → App Review
2. Request `pages_messaging` permission
3. Upload screencast and icon
4. Wait 1-3 days for approval

### Deployment Checklist

- [ ] Replace ngrok with permanent domain
- [ ] Update privacy policy URL in Facebook settings
- [ ] Configure monitoring/alerting for errors
- [ ] Scale Celery workers based on message volume
- [ ] Set up log aggregation (optional, for structured logging)
- [ ] Adjust rate limits based on usage patterns

---

## Troubleshooting

### No webhook logs

```bash
# Check services
ps aux | grep -E "uvicorn|celery|ngrok"

# Check ngrok URL (changes on restart)
curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*'

# Verify in Facebook:
# - Webhook → Callback URL matches ngrok URL
# - Webhook → Subscribed to "messages" event
# - Access Tokens → Page shows "Subscribed"
```

### Invalid signature errors

```bash
# Get correct App Secret
# Dashboard → Settings → Basic → App Secret (Show)

# Update .env
FACEBOOK_APP_SECRET=correct_secret_here

# Restart
make dev
docker-compose restart celery-worker
```

### LLM errors

```bash
# Check Groq API key
cat .env | grep GROQ_API_KEY

# Should be real key (not placeholder)
GROQ_API_KEY=gsk_...

# Check Celery logs for full error
make infra-logs
```

### Rate limit issues

```bash
# Check Redis connection
docker logs celery-worker | grep -i redis

# Adjust limit if needed
# .env: FACEBOOK_RATE_LIMIT_MESSAGES_PER_MINUTE=20
```

---

## Key Implementation Details

### Webhook Signature Verification

```python
# HMAC SHA256 with app secret
expected = hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()
is_valid = hmac.compare_digest(expected, provided_hash)
```

### Rate Limiting (Redis Sliding Window)

```python
# Add timestamp to sorted set
await redis.zadd(key, {str(now): now})

# Remove old timestamps outside window
await redis.zremrangebyscore(key, "-inf", cutoff)

# Count requests in window
count = await redis.zcard(key)
return count <= max_per_minute
```

### Conversation History

```python
# Fetch last 50 messages (DESC) then reverse to chronological (ASC)
messages = get_messages(conversation_id, limit=50, order="created_at.desc", reverse=True)

# Format as structured prompt with sections
<SYSTEM>...</SYSTEM>
<HISTORY>...</HISTORY>
<CURRENT_USER_QUERY>...</CURRENT_USER_QUERY>
```

### Error Handling

```python
# Show full errors (exc_info=True) instead of hiding with friendly messages
try:
    result = await llm.invoke(...)
except Exception as e:
    logger.error("LLM failed", exc_info=True)
    raise  # Don't hide error for debugging
```

---

## Testing

### Local Testing

```bash
# Verification endpoint
curl "http://localhost:8000/api/webhooks/messenger?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test"
# Expected: "test"

# Health check
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}
```

### Test Webhook Button

Facebook Dashboard → Messenger → Webhooks → Click "Test" next to `messages` field

Sends sample payload to your webhook (but won't send real response back to user)

### Direct Messaging

Send message to your Facebook Page (as admin/developer account)

Works in Development Mode without app review.

---

## Logging

**Success logs (minimal):**
```
INFO: Queued task: sender=123 task_id=abc-123
INFO: Message sent: sender=123 msg_id=m_123
```

**Error logs (full trace):**
```
ERROR: Task failed for sender 123
Traceback (most recent call last):
  File "...", line X
    [Full stack trace showing exact error]
```

**Third-party logs:**
```
INFO: HTTP Request: POST https://api.groq.com/... "HTTP/1.1 200 OK"
INFO: HTTP Request: POST https://graph.facebook.com/... "HTTP/1.1 200 OK"
```

---

## Development Commands

```bash
# Start services
make dev                        # FastAPI
make infra-up                   # Celery + Redis
make ngrok                      # Expose localhost

# Logs
make infra-logs                 # Celery logs
# FastAPI logs in terminal where `make dev` runs

# Restart after .env changes
Ctrl+C → make dev               # FastAPI
docker-compose restart celery-worker  # Celery

# Monitoring
open http://localhost:5555      # Flower (Celery monitoring)
open http://localhost:8000/admin  # Database admin
open http://localhost:8000/scalar  # API documentation

# Testing
curl -X POST http://localhost:8000/api/integrations/messenger/send \
  -H "Content-Type: application/json" \
  -d '{"recipient_id": "123456", "text": "Test message"}'
```

---

## Architecture Decisions

### Why Celery?

Facebook requires webhook response <20s. Celery allows:
- Immediate 200 OK response
- Background processing (LLM can take 3-5 seconds)
- Retry logic for failed messages
- Monitoring via Flower

### Why Redis Rate Limiting?

- Distributed (works across multiple FastAPI instances)
- Sliding window (accurate, no burst issues)
- Fail-open (allows requests if Redis fails)

### Why Plain String Prompts?

Initial implementation used message list format `[{role, content}]` but caused errors with LangChain's ChatGroq. Plain string with XML-like sections (`<SYSTEM>`, `<HISTORY>`, etc.) works reliably.

### Why Re-raise Errors?

Development priority: Full error visibility for debugging.
Production alternative: Catch errors and send friendly message to user.

### Why `app/integrations/` vs `app/lib/`?

**`app/integrations/`** - External service clients (Messenger, Stripe, Twilio)
- Service-specific business logic
- API integration code
- Not reusable utilities

**`app/lib/`** - Reusable utilities and abstractions (retry, LLM providers)
- Generic, framework-agnostic
- Multi-provider abstractions
- Pure utility functions

### Why Separate API Directories?

**`app/api/integrations/`** - Endpoints that **call** external services (outgoing)
**`app/api/webhooks/`** - Endpoints that **receive** from external services (incoming)

Mirrors backend structure and makes intent clear.

---

## Future Enhancements

- Multi-language support
- Rich media responses (cards, buttons, quick replies)
- User preferences/settings storage
- Conversation branching/flows
- Analytics and metrics
- WhatsApp/Telegram integration (same architecture)
- Streaming responses (for longer AI outputs)

---

## References

- Facebook Messenger Platform: https://developers.facebook.com/docs/messenger-platform
- Groq Documentation: https://console.groq.com/docs
- Celery Documentation: https://docs.celeryq.dev/
