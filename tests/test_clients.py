from __future__ import annotations

import asyncio
from typing import Dict, List, cast

import httpx
import pytest

from pharos_sdk import AsyncPharosClient, AuthScheme, PharosClient
from pharos_sdk.config import ClientConfig
from pharos_sdk.exceptions import AuthenticationError, ConfigurationError, ResponseDecodeError
from pharos_sdk.models import DeclarationNumber, VehicleItem
from tests.fixtures import (
    declaration_payload,
    importer_list_payload,
    summary_payload,
    vehicle_item_payload,
)


def test_sync_client_uses_bearer_auth_and_parses_resource() -> None:
    seen: Dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers["authorization"]
        assert request.url.path == "/api/v1/importers"
        return httpx.Response(status_code=200, json=importer_list_payload())

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    with PharosClient(api_key="phk_live_secret", http_client=http_client) as client:
        result = client.importers.list()

    assert seen["authorization"] == "Bearer phk_live_secret"
    assert result.data[0].ruc == "20100000001"
    assert not http_client.is_closed
    http_client.close()


def test_sync_client_can_use_x_pharos_key() -> None:
    seen: Dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers["x-pharos-key"]
        return httpx.Response(status_code=200, json=importer_list_payload())

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    client = PharosClient(
        api_key="phk_live_secret",
        auth_scheme="api_key",
        http_client=http_client,
    )
    client.importers.list()
    client.close()

    assert seen["key"] == "phk_live_secret"
    assert not http_client.is_closed
    http_client.close()


def test_sync_client_accepts_positional_api_key_and_auth_scheme_enum() -> None:
    seen: Dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers["x-pharos-key"]
        return httpx.Response(status_code=200, json=importer_list_payload())

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    client = PharosClient(
        "phk_live_secret",
        auth_scheme=AuthScheme.API_KEY,
        http_client=http_client,
    )

    result = client.importers.list()
    client.close()

    assert result.count == 1
    assert seen["key"] == "phk_live_secret"
    assert not http_client.is_closed
    http_client.close()


def test_client_rejects_invalid_configuration() -> None:
    with pytest.raises(ConfigurationError, match="api_key"):
        PharosClient("")

    with pytest.raises(ConfigurationError, match="auth_scheme"):
        PharosClient("phk_live_secret", auth_scheme="basic")


def test_declaration_resource_methods() -> None:
    paths: List[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path.endswith("/latest"):
            return httpx.Response(
                status_code=200,
                json={
                    "object": "list",
                    "count": 1,
                    "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
                    "limit": 10,
                    "data": [summary_payload()],
                },
            )
        if request.url.path.endswith("/items/1"):
            item = vehicle_item_payload()
            item["retrieved_at"] = "2026-07-30T14:25:01.882913+00:00"
            return httpx.Response(status_code=200, json=item)
        if request.url.path.endswith("/items"):
            return httpx.Response(
                status_code=200,
                json={
                    "object": "list",
                    "count": 1,
                    "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
                    "data": [vehicle_item_payload()],
                },
            )
        return httpx.Response(status_code=200, json=declaration_payload())

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    client = PharosClient(api_key="phk_live_secret", http_client=http_client)

    latest = client.declarations.latest(limit=10)
    number = DeclarationNumber(
        customs_office="118",
        year=2026,
        regime="10",
        number=1234,
        control_number="00",
    )
    declaration = client.declarations.get(number)
    items = client.declarations.items(number)
    item = client.declarations.item(number, item_number=1)

    assert latest.limit == 10
    assert declaration.items
    assert isinstance(items.data[0], VehicleItem)
    assert isinstance(item, VehicleItem)
    assert paths == [
        "/api/v1/declarations/latest",
        "/api/v1/declarations/118-2026-10-001234-00",
        "/api/v1/declarations/118-2026-10-001234-00/items",
        "/api/v1/declarations/118-2026-10-001234-00/items/1",
    ]
    client.close()
    http_client.close()


def test_declaration_resource_methods_accept_string_full_number() -> None:
    paths: List[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path.endswith("/items/1"):
            item = vehicle_item_payload()
            item["retrieved_at"] = "2026-07-30T14:25:01.882913+00:00"
            return httpx.Response(status_code=200, json=item)
        elif request.url.path.endswith("/items"):
            return httpx.Response(
                status_code=200,
                json={
                    "object": "list",
                    "count": 1,
                    "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
                    "data": [vehicle_item_payload()],
                },
            )
        else:
            return httpx.Response(status_code=200, json=declaration_payload())

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    client = PharosClient(api_key="phk_live_secret", http_client=http_client)

    declaration = client.declarations.get("118-2026-10-001234")
    items = client.declarations.items("118-2026-10-001234")
    item = client.declarations.item(
        "118-2026-10-001234-00",
        item_number=1,
    )

    assert declaration.full_number == "118-2026-10-001234-00"
    assert isinstance(items.data[0], VehicleItem)
    assert isinstance(item, VehicleItem)
    assert paths == [
        "/api/v1/declarations/118-2026-10-001234",
        "/api/v1/declarations/118-2026-10-001234/items",
        "/api/v1/declarations/118-2026-10-001234-00/items/1",
    ]
    client.close()
    http_client.close()


def test_error_mapping() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            json={"error": {"code": "unauthorized", "message": "Invalid API key."}},
        )

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    client = PharosClient(api_key="phk_live_secret", http_client=http_client)

    with pytest.raises(AuthenticationError) as exc_info:
        client.importers.list()

    assert "phk_live_secret" not in str(exc_info.value)
    client.close()
    http_client.close()


def test_malformed_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, content=b"not json")

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    client = PharosClient(api_key="phk_live_secret", http_client=http_client)

    with pytest.raises(ResponseDecodeError):
        client.importers.list()

    client.close()
    http_client.close()


def test_async_client_has_matching_resource_behavior() -> None:
    async def run() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=200, json=importer_list_payload())

        http_client = httpx.AsyncClient(
            base_url="https://app.pharos.pe/api/v1",
            transport=httpx.MockTransport(handler),
        )
        async with AsyncPharosClient(
            api_key="phk_live_secret",
            http_client=http_client,
        ) as client:
            result = await client.importers.list()
        assert result.data[0].name == "EMPRESA DEMO S.A.C."
        assert not http_client.is_closed
        await http_client.aclose()

    asyncio.run(run())


def test_async_client_can_be_used_without_context_manager() -> None:
    async def run() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=200, json=importer_list_payload())

        http_client = httpx.AsyncClient(
            base_url="https://app.pharos.pe/api/v1",
            transport=httpx.MockTransport(handler),
        )
        client = AsyncPharosClient(api_key="phk_live_secret", http_client=http_client)
        try:
            result = await client.importers.list()
        finally:
            await client.close()

        assert result.data[0].name == "EMPRESA DEMO S.A.C."
        assert not http_client.is_closed
        await http_client.aclose()

    asyncio.run(run())


def test_async_declaration_resource_methods() -> None:
    async def run() -> None:
        paths: List[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            if request.url.path.endswith("/latest"):
                return httpx.Response(
                    200,
                    json={
                        "object": "list",
                        "count": 1,
                        "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
                        "limit": 10,
                        "data": [summary_payload()],
                    },
                )
            if request.url.path.endswith("/items/1"):
                item_payload = vehicle_item_payload()
                item_payload["retrieved_at"] = "2026-07-30T14:25:01.882913+00:00"
                return httpx.Response(status_code=200, json=item_payload)
            if request.url.path.endswith("/items"):
                return httpx.Response(
                    200,
                    json={
                        "object": "list",
                        "count": 1,
                        "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
                        "data": [vehicle_item_payload()],
                    },
                )
            return httpx.Response(status_code=200, json=declaration_payload())

        http_client = httpx.AsyncClient(
            base_url="https://app.pharos.pe/api/v1",
            transport=httpx.MockTransport(handler),
        )
        client = AsyncPharosClient("phk_live_secret", http_client=http_client)
        number = DeclarationNumber(
            customs_office="118",
            year=2026,
            regime="10",
            number=1234,
            control_number="00",
        )

        latest = await client.declarations.latest(limit=10)
        declaration = await client.declarations.get(number)
        items = await client.declarations.items(number)
        item = await client.declarations.item(number, item_number=1)
        await client.close()

        assert latest.limit == 10
        assert declaration.items
        assert isinstance(items.data[0], VehicleItem)
        assert isinstance(item, VehicleItem)
        assert paths == [
            "/api/v1/declarations/latest",
            "/api/v1/declarations/118-2026-10-001234-00",
            "/api/v1/declarations/118-2026-10-001234-00/items",
            "/api/v1/declarations/118-2026-10-001234-00/items/1",
        ]
        assert not http_client.is_closed
        await http_client.aclose()

    asyncio.run(run())


def test_sync_client_reports_closed_state() -> None:
    client = PharosClient("phk_live_secret")

    assert not client.is_closed()

    client.close()

    assert client.is_closed()


def test_async_client_reports_closed_state() -> None:
    async def run() -> None:
        client = AsyncPharosClient("phk_live_secret")

        assert not client.is_closed()

        await client.close()

        assert client.is_closed()

    asyncio.run(run())


def test_client_config_rejects_unreachable_invalid_auth_scheme() -> None:
    config = ClientConfig(
        api_key="phk_live_secret",
        auth_scheme=cast(AuthScheme, "invalid"),
    )

    with pytest.raises(ValueError, match="Unsupported auth scheme"):
        config.auth_headers()


def test_async_declaration_resource_methods_accept_string_full_number() -> None:
    async def run() -> None:
        paths: List[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            if request.url.path.endswith("/items/1"):
                item_payload = vehicle_item_payload()
                item_payload["retrieved_at"] = "2026-07-30T14:25:01.882913+00:00"
                return httpx.Response(status_code=200, json=item_payload)
            elif request.url.path.endswith("/items"):
                return httpx.Response(
                    200,
                    json={
                        "object": "list",
                        "count": 1,
                        "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
                        "data": [vehicle_item_payload()],
                    },
                )
            else:
                return httpx.Response(status_code=200, json=declaration_payload())

        http_client = httpx.AsyncClient(
            base_url="https://app.pharos.pe/api/v1",
            transport=httpx.MockTransport(handler),
        )
        client = AsyncPharosClient("phk_live_secret", http_client=http_client)

        declaration = await client.declarations.get("118-2026-10-001234")
        items = await client.declarations.items("118-2026-10-001234")
        item = await client.declarations.item(
            "118-2026-10-001234-00",
            item_number=1,
        )
        await client.close()

        assert declaration.full_number == "118-2026-10-001234-00"
        assert isinstance(items.data[0], VehicleItem)
        assert isinstance(item, VehicleItem)
        assert paths == [
            "/api/v1/declarations/118-2026-10-001234",
            "/api/v1/declarations/118-2026-10-001234/items",
            "/api/v1/declarations/118-2026-10-001234-00/items/1",
        ]
        assert not http_client.is_closed
        await http_client.aclose()

    asyncio.run(run())
