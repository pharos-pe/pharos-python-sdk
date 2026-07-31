"""Synchronous Pharos Connect client."""

from __future__ import annotations

from typing import Dict, Optional

import httpx

from pharos_sdk.base import BaseClient
from pharos_sdk.config import BASE_URL, AuthScheme, AuthSchemeInput, make_config
from pharos_sdk.resources import DeclarationsResource, ImportersResource
from pharos_sdk.transport import SyncTransport


class PharosClient(BaseClient):
    """Synchronous client for the Pharos Connect API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None,
        auth_scheme: AuthSchemeInput = AuthScheme.BEARER,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        """Create a synchronous Pharos Connect client."""
        config = make_config(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            auth_scheme=auth_scheme,
        )
        self.transport = SyncTransport(config, http_client=http_client)
        self.importers = ImportersResource(self.transport)
        self.declarations = DeclarationsResource(self.transport)

    def close(self) -> None:
        """Close the underlying HTTP client if this SDK instance owns it."""
        self.transport.close()

    def is_closed(self) -> bool:
        """Return whether the underlying HTTP client is closed."""
        return bool(self.transport.client.is_closed)

    def __enter__(self) -> PharosClient:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
