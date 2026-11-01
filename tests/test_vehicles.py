from __future__ import annotations

import asyncio
from typing import Callable, Dict

import httpx
import pytest

from pharos_sdk import AsyncPharosClient, PharosClient
from pharos_sdk.exceptions import AuthorizationError, ConfigurationError
from tests.fixtures import vehicle_lookup_payload


def _sync_client(handler: Callable[[httpx.Request], httpx.Response]) -> PharosClient:
    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    return PharosClient(api_key="phk_live_secret", http_client=http_client)


def test_find_by_vin_sends_the_identifier_and_parses_the_matches() -> None:
    seen: Dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        assert request.url.path == "/api/v1/vehicles"
        return httpx.Response(status_code=200, json=vehicle_lookup_payload())

    with _sync_client(handler) as client:
        result = client.vehicles.find(vin="LSJA24U98RG000001")

    assert seen == {"vin": "LSJA24U98RG000001"}
    assert result.scope == "global"
    match = result.data[0]
    assert match.in_scope is False
    assert match.item_number == 1
    assert match.declaration.full_number == "118-2026-10-001234-00"
    assert match.declaration.customs_office.code == "118"
    assert match.declaration.importer.ruc == "20100000003"
    assert match.vehicle.brand == "MARCA DEMO"


def test_find_by_engine_number_sends_only_that_parameter() -> None:
    seen: Dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(status_code=200, json=vehicle_lookup_payload())

    with _sync_client(handler) as client:
        client.vehicles.find(engine_number="TZ220XS0001")

    assert seen == {"engine_number": "TZ220XS0001"}


@pytest.mark.parametrize(
    "identifiers",
    [{}, {"vin": "A", "engine_number": "B"}],
)
def test_find_takes_exactly_one_identifier_before_any_request(identifiers: Dict[str, str]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request expected")

    with _sync_client(handler) as client, pytest.raises(ConfigurationError):
        client.vehicles.find(**identifiers)


def test_a_key_without_the_lookup_raises_authorization_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=403,
            json={"error": {"code": "access_disabled", "message": "Not enabled."}},
        )

    with _sync_client(handler) as client, pytest.raises(AuthorizationError):
        client.vehicles.find(vin="X")


def test_async_find_parses_the_matches() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json=vehicle_lookup_payload())

    async def run() -> None:
        http_client = httpx.AsyncClient(
            base_url="https://app.pharos.pe/api/v1",
            transport=httpx.MockTransport(handler),
        )
        client = AsyncPharosClient(api_key="phk_live_secret", http_client=http_client)
        result = await client.vehicles.find(vin="LSJA24U98RG000001")
        assert result.scope == "global"
        assert result.data[0].vehicle.vin_number
        await http_client.aclose()

    asyncio.run(run())
