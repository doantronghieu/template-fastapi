"""Facebook Messenger client for sending messages and verifying webhooks.

Provides secure communication with Facebook Messenger Platform:
- HMAC SHA256 signature verification for webhook security
- Async message sending with retry logic
- Configurable Graph API version support
"""

import hashlib
import hmac
import logging

import httpx

from app.lib.utils import async_retry

logger = logging.getLogger(__name__)


class MessengerClient:
    """Client for Facebook Messenger Send API.

    Handles bidirectional communication with Facebook Messenger Platform:
    - Incoming: Verify webhook signatures (HMAC SHA256)
    - Outgoing: Send text messages via Graph API

    Attributes:
        page_access_token: Page-specific token for API authentication
        app_secret: App secret for webhook signature verification
        graph_api_version: Graph API version (e.g., "v24.0")
        send_api_url: Constructed Send API endpoint URL

    Note:
        Rate limits (per Facebook documentation):
        - Text/links: 300 calls/sec
        - Audio/video: 10 calls/sec
    """

    def __init__(
        self, page_access_token: str, app_secret: str, graph_api_version: str = "v23.0"
    ):
        self.page_access_token = page_access_token
        self.app_secret = app_secret
        self.graph_api_version = graph_api_version
        self.send_api_url = (
            f"https://graph.facebook.com/{graph_api_version}/me/messages"
        )

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature from Facebook using HMAC SHA256.

        Facebook signs all webhook requests with app secret to prove authenticity.
        Uses constant-time comparison to prevent timing attacks.

        Args:
            payload: Raw request body bytes (pre-JSON parsing)
            signature: X-Hub-Signature-256 header value (format: "sha256=hash")

        Returns:
            bool: True if signature valid, False otherwise

        Security:
            - Prevents unauthorized webhook calls from non-Facebook sources
            - Uses hmac.compare_digest for timing-attack resistance
            - Rejects if signature missing, wrong format, or wrong hash method
        """
        if not signature:
            return False

        # Parse signature header (format: "sha256=hexdigest")
        try:
            method, provided_hash = signature.split("=", 1)
            if method != "sha256":
                return False
        except ValueError:
            return False

        # Compute expected HMAC using app secret
        expected_hash = hmac.new(
            self.app_secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        # Constant-time comparison prevents timing attacks
        return hmac.compare_digest(expected_hash, provided_hash)

    @async_retry(max_retries=3, exceptions=(httpx.HTTPError,))
    async def send_text_message(self, recipient_id: str, text: str) -> dict:
        """
        Send text message to recipient via Facebook Send API with automatic retry.

        Args:
            recipient_id: User's Page-Scoped ID (PSID) from webhook
            text: Message text to send (max 2000 characters)

        Returns:
            dict: Response with recipient_id and message_id

        Raises:
            httpx.HTTPError: If all retry attempts fail

        Note:
            Automatically retries with exponential backoff (1s, 2s, 4s) on HTTP errors.
            Uses access token in query params (Facebook's preferred method).
        """
        payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
        params = {"access_token": self.page_access_token}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self.send_api_url, json=payload, params=params)
            response.raise_for_status()
            return response.json()
