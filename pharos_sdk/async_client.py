"""Asynchronous Pharos Connect client."""

from __future__ import annotations

from typing import Dict, Optional

import httpx

from pharos_sdk.base import BaseClient
from pharos_sdk.config import BASE_URL, AuthScheme, AuthSchemeInput, make_config
from pharos_sdk.resources import (
    AsyncDeclarationsResource,
    AsyncImportersResource,
    AsyncVehiclesResource,
)
from pharos_sdk.transport import AsyncTransport


class AsyncPharosClient(BaseClient):
    """Asynchronous client for the Pharos Connect API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None,
        auth_scheme: AuthSchemeInput = AuthScheme.BEARER,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """Create an asynchronous Pharos Connect client."""
        config = make_config(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            auth_scheme=auth_scheme,
        )
        self.transport = AsyncTransport(config, http_client=http_client)
        self.importers = AsyncImportersResource(self.transport)
        self.vehicles = AsyncVehiclesResource(self.transport)
        self.declarations = AsyncDeclarationsResource(self.transport)

    async def close(self) -> None:
        """Close the underlying HTTP client if this SDK instance owns it."""
        await self.transport.close()

    def is_closed(self) -> bool:
        """Return whether the underlying HTTP client is closed."""
        return bool(self.transport.client.is_closed)

    async def __aenter__(self) -> AsyncPharosClient:
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.close()
