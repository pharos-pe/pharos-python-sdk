"""Vehicle lookup resources."""

from __future__ import annotations

from typing import Optional

from pharos_sdk.models import ListEnvelope, VehicleMatch
from pharos_sdk.parsers import parse_list_envelope, parse_vehicle_match_value
from pharos_sdk.resources.paths import vehicle_lookup_params
from pharos_sdk.transport import AsyncTransport, SyncTransport


class VehiclesResource:
    """Synchronous vehicle lookup. Needs a key Pharos has enabled for it."""

    def __init__(self, transport: SyncTransport) -> None:
        self.transport = transport

    def find(
        self,
        *,
        vin: Optional[str] = None,
        engine_number: Optional[str] = None,
    ) -> ListEnvelope[VehicleMatch]:
        """Look a vehicle up by exact VIN or exact engine number, one of the two."""
        params = vehicle_lookup_params(vin=vin, engine_number=engine_number)
        payload = self.transport.get(path="/vehicles", params=params)
        return parse_list_envelope(payload, item_parser=parse_vehicle_match_value)


class AsyncVehiclesResource:
    """Asynchronous vehicle lookup. Needs a key Pharos has enabled for it."""

    def __init__(self, transport: AsyncTransport) -> None:
        self.transport = transport

    async def find(
        self,
        *,
        vin: Optional[str] = None,
        engine_number: Optional[str] = None,
    ) -> ListEnvelope[VehicleMatch]:
        """Look a vehicle up by exact VIN or exact engine number, one of the two."""
        params = vehicle_lookup_params(vin=vin, engine_number=engine_number)
        payload = await self.transport.get(path="/vehicles", params=params)
        return parse_list_envelope(payload, item_parser=parse_vehicle_match_value)
