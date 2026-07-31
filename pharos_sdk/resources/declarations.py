"""Declaration resources."""

from __future__ import annotations

from typing import Optional, overload

from pharos_sdk.models import Declaration, DeclarationNumber, DeclarationSummary, Item, ListEnvelope
from pharos_sdk.parsers import (
    parse_declaration,
    parse_declaration_summary_value,
    parse_item,
    parse_item_value,
    parse_list_envelope,
)
from pharos_sdk.resources.paths import (
    DeclarationNumberInput,
    declaration_item_path,
    declaration_items_path,
    declaration_path,
    latest_params,
)
from pharos_sdk.transport import AsyncTransport, SyncTransport


class DeclarationsResource:
    """Synchronous declaration operations."""

    def __init__(self, transport: SyncTransport) -> None:
        self.transport = transport

    def latest(self, *, limit: Optional[int] = None) -> ListEnvelope[DeclarationSummary]:
        """Return latest declaration summaries visible to the credential."""
        params = latest_params(limit)
        payload = self.transport.get(path="/declarations/latest", params=params)
        return parse_list_envelope(payload, item_parser=parse_declaration_summary_value)

    @overload
    def get(self, full_number: str) -> Declaration: ...

    @overload
    def get(self, full_number: DeclarationNumber) -> Declaration: ...

    def get(self, full_number: DeclarationNumberInput) -> Declaration:
        """Return the full declaration for a DUA number."""
        path = declaration_path(full_number)
        payload = self.transport.get(path=path)
        return parse_declaration(payload)

    @overload
    def items(self, full_number: str) -> ListEnvelope[Item]: ...

    @overload
    def items(self, full_number: DeclarationNumber) -> ListEnvelope[Item]: ...

    def items(self, full_number: DeclarationNumberInput) -> ListEnvelope[Item]:
        """Return declaration items without repeating the declaration header."""
        path = declaration_items_path(full_number)
        payload = self.transport.get(path=path)
        return parse_list_envelope(payload, item_parser=parse_item_value)

    @overload
    def item(self, full_number: str, item_number: int) -> Item: ...

    @overload
    def item(self, full_number: DeclarationNumber, item_number: int) -> Item: ...

    def item(self, full_number: DeclarationNumberInput, item_number: int) -> Item:
        """Return one item from a declaration."""
        path = declaration_item_path(full_number, item_number)
        payload = self.transport.get(path=path)
        return parse_item(payload)


class AsyncDeclarationsResource:
    """Asynchronous declaration operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self.transport = transport

    async def latest(self, *, limit: Optional[int] = None) -> ListEnvelope[DeclarationSummary]:
        """Return latest declaration summaries visible to the credential."""
        params = latest_params(limit)
        payload = await self.transport.get(path="/declarations/latest", params=params)
        return parse_list_envelope(payload, item_parser=parse_declaration_summary_value)

    @overload
    async def get(self, full_number: str) -> Declaration: ...

    @overload
    async def get(self, full_number: DeclarationNumber) -> Declaration: ...

    async def get(self, full_number: DeclarationNumberInput) -> Declaration:
        """Return the full declaration for a DUA number."""
        path = declaration_path(full_number)
        payload = await self.transport.get(path=path)
        return parse_declaration(payload)

    @overload
    async def items(self, full_number: str) -> ListEnvelope[Item]: ...

    @overload
    async def items(self, full_number: DeclarationNumber) -> ListEnvelope[Item]: ...

    async def items(self, full_number: DeclarationNumberInput) -> ListEnvelope[Item]:
        """Return declaration items without repeating the declaration header."""
        path = declaration_items_path(full_number)
        payload = await self.transport.get(path=path)
        return parse_list_envelope(payload, item_parser=parse_item_value)

    @overload
    async def item(self, full_number: str, item_number: int) -> Item: ...

    @overload
    async def item(self, full_number: DeclarationNumber, item_number: int) -> Item: ...

    async def item(self, full_number: DeclarationNumberInput, item_number: int) -> Item:
        """Return one item from a declaration."""
        path = declaration_item_path(full_number, item_number)
        payload = await self.transport.get(path=path)
        return parse_item(payload)
