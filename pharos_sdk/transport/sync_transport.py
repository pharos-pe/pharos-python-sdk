"""Synchronous httpx transport."""

from __future__ import annotations

from typing import Dict, Optional

import httpx

from pharos_sdk.config import ClientConfig
from pharos_sdk.exceptions import TransportError
from pharos_sdk.transport.base import USER_AGENT, BaseTransport, build_url
from pharos_sdk.transport.response import decode_response
from pharos_sdk.types import JSONObject, QueryParams


class SyncTransport(BaseTransport):
    """Synchronous httpx transport wrapper."""

    def __init__(self, config: ClientConfig, http_client: Optional[httpx.Client] = None) -> None:
        self.config = config
        self.owns_client = http_client is None
        self.client = http_client or httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
        )

    def close(self) -> None:
        """Close the underlying client if the SDK created it."""
        if self.owns_client:
            self.client.close()

    def get(self, path: str, *, params: Optional[QueryParams] = None) -> JSONObject:
        """Execute a GET request and return the decoded JSON object."""
        try:
            headers = self.headers()
            url = build_url(base_url=self.config.base_url, path=path)
            response = self.client.get(url, params=params, headers=headers)
        except httpx.TransportError as e:
            raise TransportError("Pharos API request failed before receiving a response.") from e
        else:
            return decode_response(response)

    def headers(self) -> Dict[str, str]:
        """Return request headers including authentication."""
        defaults = {"Accept": "application/json", "User-Agent": USER_AGENT}
        headers = {**defaults, **self.config.headers}
        auth_headers = self.config.auth_headers()
        headers.update(auth_headers)
        return headers
