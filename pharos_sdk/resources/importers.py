"""Importer resources."""

from __future__ import annotations

from pharos_sdk.models import Importer, ListEnvelope
from pharos_sdk.parsers import parse_importer_value, parse_list_envelope
from pharos_sdk.transport import AsyncTransport, SyncTransport


class ImportersResource:
    """Synchronous importer operations."""

    def __init__(self, transport: SyncTransport) -> None:
        self.transport = transport

    def list(self) -> ListEnvelope[Importer]:
        """List companies included in the integration scope."""
        payload = self.transport.get(path="/importers")
        return parse_list_envelope(payload, item_parser=parse_importer_value)


class AsyncImportersResource:
    """Asynchronous importer operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self.transport = transport

    async def list(self) -> ListEnvelope[Importer]:
        """List companies included in the integration scope."""
        payload = await self.transport.get(path="/importers")
        return parse_list_envelope(payload, item_parser=parse_importer_value)
