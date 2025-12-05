"""NetDocuments API client with OAuth authentication.

Uses client_credentials OAuth flow for service account access.
Auth format: CLIENT_ID|REPOSITORY_ID:CLIENT_SECRET (base64 encoded)
"""

import base64
import logging
import time
from typing import Annotated

import requests

from .config import netdocuments_settings

logger = logging.getLogger(__name__)


class NetDocumentsClient:
    """NetDocuments API client with OAuth token management."""

    def __init__(
        self,
        client_id: Annotated[
            str | None, "OAuth Client ID (from Developer Portal)"
        ] = None,
        client_secret: Annotated[str | None, "OAuth Client Secret"] = None,
        repository_id: Annotated[
            str | None, "Repository ID (format: CA-XXXXXXXX)"
        ] = None,
        cabinet_id: Annotated[str | None, "Cabinet ID (format: NG-XXXXXXXX)"] = None,
    ):
        """Initialize client with credentials from settings or parameters."""
        self.client_id = client_id or netdocuments_settings.NETDOC_CLIENT_ID
        self.client_secret = client_secret or netdocuments_settings.NETDOC_CLIENT_SECRET
        self.repository_id = repository_id or netdocuments_settings.NETDOC_REPOSITORY_ID
        self.cabinet_id = cabinet_id or netdocuments_settings.NETDOC_CABINET_ID
        self.token_url = netdocuments_settings.NETDOC_TOKEN_URL
        self.endpoint = "https://api.vault.netvoyage.com/v1"
        self.scope = netdocuments_settings.NETDOC_SCOPE
        self._access_token: str | None = None
        self._token_expiry: float = 0

    def _get_access_token(self) -> str | None:
        """Get OAuth access token using client_credentials flow.

        Token is cached until 60 seconds before expiry.
        """
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        try:
            # NetDocuments requires special auth format: CLIENT_ID|REPOSITORY_ID:CLIENT_SECRET
            auth_string = base64.b64encode(
                f"{self.client_id}|{self.repository_id}:{self.client_secret}".encode()
            ).decode()

            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "scope": self.scope,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {auth_string}",
                    "Accept": "application/json",
                },
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(f"Token failed: {response.status_code} - {response.text}")
                return None

            token_data = response.json()
            self._access_token = token_data.get("access_token")
            self._token_expiry = (
                time.time() + int(token_data.get("expires_in", 3600)) - 60
            )
            return self._access_token

        except requests.RequestException as e:
            logger.error(f"Token exception: {e}")
            return None

    def _get_headers(self, accept: str = "application/json") -> dict[str, str]:
        """Build request headers with Bearer auth token."""
        token = self._get_access_token()
        if not token:
            raise RuntimeError("Failed to obtain NetDocuments access token")
        return {"Authorization": f"Bearer {token}", "Accept": accept}

    def search(
        self,
        query: Annotated[str, "Search query (e.g., 'contract', 'invoice AND 2024')"],
    ) -> list[dict]:
        """Search for documents in cabinet.

        Supports NetDocuments query syntax with AND, OR, NOT operators.
        Returns list of dicts with: id, name, extension
        """
        logger.info(f"Search query: {query}")

        url = f"{self.endpoint}/Search/{self.cabinet_id}"
        try:
            response = requests.get(
                url, params={"q": query}, headers=self._get_headers(), timeout=60
            )
            if response.status_code != 200:
                logger.error(f"Search failed: {response.status_code}")
                return []
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Search exception: {e}")
            return []

        # Enrich search results with document metadata
        items = data.get("list", data.get("standardList", []))
        results = []
        for item in items[:20]:  # Limit to first 20 results
            if env_id := item.get("envId"):
                if doc_info := self.get_document_info(env_id):
                    attrs = doc_info.get("standardAttributes", {})
                    results.append(
                        {
                            "id": attrs.get("id"),
                            "name": attrs.get("name"),
                            "extension": attrs.get("extension"),
                        }
                    )
        return results

    def get_document_info(
        self,
        doc_id: Annotated[str, "NetDocuments document ID (e.g., '4933-5950-1396')"],
    ) -> dict | None:
        """Get document metadata by ID.

        Returns standardAttributes dict with: id, name, extension, created, modified, etc.
        """
        url = f"{self.endpoint}/Document/{doc_id}/info"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=60)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException as e:
            logger.error(f"Get info exception: {e}")
        return None

    def download_document(
        self,
        doc_id: Annotated[str, "NetDocuments document ID (e.g., '4933-5950-1396')"],
    ) -> tuple[bytes, str] | None:
        """Download document content by ID.

        Returns (content_bytes, filename) tuple or None on failure.
        Retries with exponential backoff.
        """
        url = f"{self.endpoint}/Document/{doc_id}"
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Downloading {doc_id} (attempt {attempt})")
                response = requests.get(
                    url,
                    headers=self._get_headers(accept="application/octet-stream"),
                    stream=True,
                    timeout=300,
                )

                if response.status_code == 200:
                    # Extract filename from Content-Disposition header
                    content_disp = response.headers.get("Content-Disposition", "")
                    filename = (
                        content_disp.split("filename=")[-1].strip('"')
                        if "filename=" in content_disp
                        else f"document_{doc_id}.bin"
                    )
                    content = response.content
                    logger.info(f"Downloaded {filename} ({len(content)} bytes)")
                    return content, filename

                logger.warning(f"Attempt {attempt} failed: {response.status_code}")

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt} exception: {e}")

            if attempt < max_retries:
                time.sleep(2**attempt)  # Exponential backoff

        logger.error(f"Failed to download {doc_id} after {max_retries} attempts")
        return None
