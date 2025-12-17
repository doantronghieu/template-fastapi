"""NetDocuments API client with OAuth authentication.

Uses client_credentials OAuth flow for service account access.
"""

import base64
import json
import logging
import re
import time
from typing import Annotated

import requests

from app.lib.utils import retry

from .config import netdocuments_settings

logger = logging.getLogger(__name__)


def _ws_url_to_env_id(ws_url: str) -> str:
    """Convert workspace URL to envId format. Example: /Q24/o/9/m/6/^W... -> :Q24:o:9:m:6:^W..."""
    return ws_url.replace("/", ":") if ws_url.startswith("/") else ws_url


def _parse_xml_response(xml_text: str) -> dict:
    """Parse NetDocuments XML response to dict (handles multipart upload responses)."""
    patterns = {
        "id": r"<id>([^<]+)</id>",
        "name": r"<name>([^<]+)</name>",
        "extension": r"<extension>([^<]+)</extension>",
        "envId": r"<envId>([^<]+)</envId>",
        "newVer": r"<newVer>([^<]+)</newVer>",
        "latestVersionNumber": r"<latestVersionNumber>([^<]+)</latestVersionNumber>",
    }
    return {
        key: m.group(1)
        for key, pattern in patterns.items()
        if (m := re.search(pattern, xml_text))
    }


def _parse_response(response: requests.Response) -> dict:
    """Parse response as JSON, falling back to XML for multipart uploads."""
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        return _parse_xml_response(response.text)


def _split_filename(filename: str) -> tuple[str, str]:
    """Split filename into (base_name, extension)."""
    if "." in filename:
        parts = filename.rsplit(".", 1)
        return parts[0], parts[1]
    return filename, ""


class NetDocumentsClient:
    """NetDocuments API client with OAuth token management."""

    def __init__(
        self,
        client_id: Annotated[str | None, "OAuth Client ID"] = None,
        client_secret: Annotated[str | None, "OAuth Client Secret"] = None,
        repository_id: Annotated[str | None, "Repository ID (CA-XXXXXXXX)"] = None,
        cabinet_id: Annotated[str | None, "Cabinet ID (NG-XXXXXXXX)"] = None,
    ):
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
        """Get OAuth access token (cached until 60s before expiry)."""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        try:
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

    def _headers(self, accept: str = "application/json") -> dict[str, str]:
        """Build request headers with Bearer auth."""
        token = self._get_access_token()
        if not token:
            raise RuntimeError("Failed to obtain NetDocuments access token")
        return {"Authorization": f"Bearer {token}", "Accept": accept}

    def _get(
        self, url: str, params: dict | None = None, timeout: int = 60
    ) -> dict | None:
        """Make GET request with error handling."""
        try:
            response = requests.get(
                url, params=params, headers=self._headers(), timeout=timeout
            )
            if response.status_code != 200:
                logger.warning(f"GET {url} failed: {response.status_code}")
                return None
            return response.json()
        except requests.RequestException as e:
            logger.error(f"GET {url} exception: {e}")
            return None

    def _delete(self, url: str, timeout: int = 60) -> bool:
        """Make DELETE request with error handling."""
        try:
            response = requests.delete(url, headers=self._headers(), timeout=timeout)
            if response.status_code not in (200, 204):
                logger.warning(f"DELETE {url} failed: {response.status_code}")
                return False
            return True
        except requests.RequestException as e:
            logger.error(f"DELETE {url} exception: {e}")
            return False

    # === Document Operations ===

    def search(self, query: Annotated[str, "Search query"]) -> list[dict]:
        """Search for documents in cabinet. Returns list of {id, name, extension}.

        Note: Newly uploaded documents may not appear immediately due to indexing delay.
        """
        logger.info(f"Search query: {query}")
        data = self._get(f"{self.endpoint}/Search/{self.cabinet_id}", {"q": query})
        if not data:
            return []

        results = []
        for item in data.get("list", data.get("standardList", []))[:20]:
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

    def get_document_info(self, doc_id: Annotated[str, "Document ID"]) -> dict | None:
        """Get document metadata."""
        return self._get(f"{self.endpoint}/Document/{doc_id}/info")

    def get_document_locations(
        self, doc_id: Annotated[str, "Document ID"]
    ) -> dict | None:
        """Get document locations including workspace info."""
        return self._get(f"{self.endpoint}/Document/{doc_id}/locations")

    def download_document(
        self, doc_id: Annotated[str, "Document ID"]
    ) -> tuple[bytes, str] | None:
        """Download document content. Returns (content, filename) or None."""
        url = f"{self.endpoint}/Document/{doc_id}"

        @retry(max_retries=3, exceptions=(requests.RequestException,))
        def _download() -> tuple[bytes, str]:
            response = requests.get(
                url,
                headers=self._headers(accept="application/octet-stream"),
                stream=True,
                timeout=300,
            )
            response.raise_for_status()
            content_disp = response.headers.get("Content-Disposition", "")
            filename = (
                content_disp.split("filename=")[-1].strip('"')
                if "filename=" in content_disp
                else f"document_{doc_id}.bin"
            )
            return response.content, filename

        try:
            content, filename = _download()
            logger.info(f"Downloaded {filename} ({len(content)} bytes)")
            return content, filename
        except requests.RequestException:
            logger.error(f"Failed to download {doc_id}")
            return None

    def delete_document(self, doc_id: Annotated[str, "Document ID"]) -> bool:
        """Delete document by ID."""
        logger.info(f"Deleting document: {doc_id}")
        return self._delete(f"{self.endpoint}/Document/{doc_id}")

    def upload_document(
        self,
        file_content: Annotated[bytes, "File content"],
        filename: Annotated[str, "Filename"],
        destination: Annotated[str, "Folder/workspace ID"],
        profile: Annotated[dict | None, "Document metadata"] = None,
    ) -> dict | None:
        """Upload new document. Returns {id, name, extension} or None.

        Note: Document not immediately searchable due to indexing. Use returned ID for direct access.
        """
        logger.info(f"Uploading {filename} to {destination}")
        files = {"file": (filename, file_content, "application/octet-stream")}
        data = {"destination": destination}
        if profile:
            data["profile"] = json.dumps(profile)

        @retry(max_retries=3, exceptions=(requests.RequestException,))
        def _upload() -> dict:
            response = requests.post(
                f"{self.endpoint}/Document",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {self._get_access_token()}"},
                timeout=300,
            )
            response.raise_for_status()
            return _parse_response(response)

        try:
            result = _upload()
            logger.info(f"Uploaded: {filename} (ID: {result.get('id')})")
            return result
        except requests.RequestException:
            return None

    def create_version(
        self,
        doc_id: Annotated[str, "Document ID"],
        file_content: Annotated[bytes, "New version content"],
        filename: Annotated[str | None, "Filename"] = None,
        description: Annotated[str | None, "Version description"] = None,
    ) -> dict | None:
        """Create new version of existing document."""
        logger.info(f"Creating version for {doc_id}")
        url = f"{self.endpoint}/Document/{doc_id}/version"

        @retry(max_retries=3, exceptions=(requests.RequestException,))
        def _create() -> dict:
            headers = {"Authorization": f"Bearer {self._get_access_token()}"}
            if filename:
                files = {"file": (filename, file_content, "application/octet-stream")}
                data = {"version_description": description} if description else {}
                response = requests.post(
                    url, files=files, data=data, headers=headers, timeout=300
                )
            else:
                data = {
                    "body": base64.b64encode(file_content).decode(),
                    "base64": "true",
                }
                if description:
                    data["version_description"] = description
                headers["Content-Type"] = "application/json"
                response = requests.post(url, json=data, headers=headers, timeout=300)
            response.raise_for_status()
            return _parse_response(response)

        try:
            result = _create()
            logger.info(f"Created version {result.get('newVer')} for {doc_id}")
            return result
        except requests.RequestException:
            return None

    # === Workspace/Folder Operations ===

    def find_workspace_by_name(
        self, workspace_name: Annotated[str, "Workspace name pattern"]
    ) -> dict | None:
        """Find workspace by searching documents and checking their locations."""
        logger.info(f"Finding workspace: {workspace_name}")
        file_num = workspace_name.split(" - ", 1)[0].strip()

        data = self._get(f"{self.endpoint}/Search/{self.cabinet_id}", {"q": file_num})
        if not data or not data.get("list"):
            logger.warning(f"No documents found for workspace: {workspace_name}")
            return None

        doc_env_id = data["list"][0].get("envId")
        if not doc_env_id:
            return None

        locations = self.get_document_locations(doc_env_id)
        if not locations:
            return None

        # Check workspaceList
        for ws in locations.get("workspaceList", []):
            if ws.get("wsName", "").startswith(file_num):
                ws_id = _ws_url_to_env_id(ws.get("wsUrl", ""))
                logger.info(f"Found workspace: {ws.get('wsName')} ({ws_id})")
                return {"id": ws_id, "name": ws.get("wsName")}

        # Fallback: check WorkspaceName
        ws_name = locations.get("WorkspaceName", "")
        if ws_name.startswith(file_num):
            ws_id = _ws_url_to_env_id(locations.get("WorkspaceUrl", ""))
            logger.info(f"Found workspace: {ws_name} ({ws_id})")
            return {"id": ws_id, "name": ws_name}

        logger.warning(f"Workspace not found for: {workspace_name}")
        return None

    def list_workspace_contents(
        self, workspace_id: Annotated[str, "Workspace envId"]
    ) -> list[dict]:
        """List all documents in a workspace."""
        data = self._get(f"{self.endpoint}/Workspace/{workspace_id}")
        if not data:
            return []

        results = []
        for item in data.get("list", []):
            if item.get("type") == "doc" and (env_id := item.get("envId")):
                if doc_info := self.get_document_info(env_id):
                    attrs = doc_info.get("standardAttributes", {})
                    results.append(
                        {
                            "id": attrs.get("id"),
                            "name": attrs.get("name"),
                            "extension": attrs.get("extension"),
                            "envId": env_id,
                        }
                    )
        return results

    def find_document_in_workspace(
        self,
        workspace_id: Annotated[str, "Workspace envId"],
        filename: Annotated[str, "Document filename"],
        matter_number: Annotated[str | None, "Matter number for search filter"] = None,
    ) -> dict | None:
        """Find document by filename in workspace. Returns document info or None."""
        base_name, ext = _split_filename(filename)
        query = f"=1({matter_number}) AND {base_name}" if matter_number else base_name

        for doc in self.search(query):
            if doc.get("name", "").lower() == base_name.lower():
                if not ext or doc.get("extension", "").lower() == ext.lower():
                    if doc_id := doc.get("id"):
                        locations = self.get_document_locations(doc_id)
                        if (
                            locations
                            and _ws_url_to_env_id(locations.get("WorkspaceUrl", ""))
                            == workspace_id
                        ):
                            logger.info(
                                f"Found existing document: {doc.get('name')} ({doc_id})"
                            )
                            return doc
        return None
