from __future__ import annotations

import asyncio
from typing import Dict

import httpx
import pytest

from pharos_sdk.config import ClientConfig
from pharos_sdk.exceptions import (
    APIError,
    AuthorizationError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
    ResponseDecodeError,
    ServerError,
    TransportError,
)
from pharos_sdk.transport import AsyncTransport, SyncTransport, decode_response
from pharos_sdk.transport.errors import parse_retry_after
from pharos_sdk.version import __version__


def test_sync_transport_sends_headers_and_params() -> None:
    seen: Dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers["authorization"]
        seen["user_agent"] = request.headers["user-agent"]
        seen["query"] = request.url.query.decode()
        return httpx.Response(status_code=200, json={"object": "ok"})

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    config = ClientConfig(
        api_key="phk_live_secret",
        headers={"User-Agent": "integration-test/1.0"},
    )
    transport = SyncTransport(config, http_client=http_client)

    path = "/importers"
    payload = transport.get(path=path, params={"limit": 10})

    assert payload == {"object": "ok"}
    assert seen == {
        "authorization": "Bearer phk_live_secret",
        "user_agent": "integration-test/1.0",
        "query": "limit=10",
    }
    assert not http_client.is_closed
    transport.close()
    assert not http_client.is_closed
    http_client.close()


def test_sync_transport_closes_owned_client() -> None:
    config = ClientConfig(api_key="phk_live_secret")
    transport = SyncTransport(config)

    assert not transport.client.is_closed
    transport.close()

    assert transport.client.is_closed


def test_sync_transport_wraps_httpx_transport_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network unavailable", request=request)

    http_client = httpx.Client(
        base_url="https://app.pharos.pe/api/v1",
        transport=httpx.MockTransport(handler),
    )
    transport = SyncTransport(ClientConfig(api_key="phk_live_secret"), http_client=http_client)

    path = "/importers"
    with pytest.raises(TransportError):
        transport.get(path=path)

    http_client.close()


def test_decode_response_rejects_malformed_json() -> None:
    response = httpx.Response(status_code=200, content=b"not json")

    with pytest.raises(ResponseDecodeError):
        decode_response(response)


def test_decode_response_rejects_json_arrays() -> None:
    response = httpx.Response(status_code=200, json=[])

    with pytest.raises(ResponseDecodeError, match="JSON object"):
        decode_response(response)


@pytest.mark.parametrize(
    ("status_code", "code", "expected_error"),
    [
        (403, "access_disabled", AuthorizationError),
        (404, "not_found", NotFoundError),
        (400, "invalid_parameter", InvalidRequestError),
        (500, "internal_error", ServerError),
        (418, "unexpected", APIError),
    ],
)
def test_decode_response_maps_documented_errors(
    status_code: int,
    code: str,
    expected_error: type,
) -> None:
    response = httpx.Response(
        status_code=status_code,
        json={"error": {"code": code, "message": "Request failed."}},
    )

    with pytest.raises(expected_error):
        decode_response(response)


def test_decode_response_maps_rate_limit_metadata() -> None:
    response = httpx.Response(
        status_code=429,
        json={"error": {"code": "rate_limited", "message": "Too many requests."}},
        headers={"Retry-After": "60"},
    )

    with pytest.raises(RateLimitError) as exc_info:
        decode_response(response)

    assert exc_info.value.retry_after == 60
    assert exc_info.value.code == "rate_limited"


def test_parse_retry_after_ignores_non_integer_values() -> None:
    assert parse_retry_after("60") == 60
    assert parse_retry_after("soon") is None


def test_async_transport_closes_owned_client() -> None:
    async def run() -> None:
        transport = AsyncTransport(ClientConfig(api_key="phk_live_secret"))

        assert not transport.client.is_closed
        await transport.close()

        assert transport.client.is_closed

    asyncio.run(run())


def test_async_transport_does_not_close_injected_client() -> None:
    async def run() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=200, json={"object": "ok"})

        http_client = httpx.AsyncClient(
            base_url="https://app.pharos.pe/api/v1",
            transport=httpx.MockTransport(handler),
        )
        transport = AsyncTransport(ClientConfig(api_key="phk_live_secret"), http_client=http_client)

        path = "/importers"
        payload = await transport.get(path=path)
        await transport.close()

        assert payload == {"object": "ok"}
        assert not http_client.is_closed
        await http_client.aclose()

    asyncio.run(run())


def test_async_transport_wraps_httpx_transport_errors() -> None:
    async def run() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("network unavailable", request=request)

        http_client = httpx.AsyncClient(
            base_url="https://app.pharos.pe/api/v1",
            transport=httpx.MockTransport(handler),
        )
        transport = AsyncTransport(ClientConfig(api_key="phk_live_secret"), http_client=http_client)

        path = "/importers"
        with pytest.raises(TransportError):
            await transport.get(path=path)

        await http_client.aclose()

    asyncio.run(run())


def test_gateway_error_page_is_still_an_api_error() -> None:
    # Cloudflare sits in front of the API, so 502s, 520s and bot challenges
    # arrive as HTML. They must reach the caller as APIError — the exception
    # everyone catches — and not as a decoding failure.
    response = httpx.Response(
        status_code=502,
        headers={"content-type": "text/html"},
        text="<html><body>502 Bad Gateway</body></html>",
    )

    with pytest.raises(ServerError) as raised:
        decode_response(response)

    assert raised.value.status_code == 502
    assert raised.value.code is None
    assert "502 Bad Gateway" in raised.value.message


def test_empty_error_body_is_still_an_api_error() -> None:
    response = httpx.Response(status_code=503, text="")

    with pytest.raises(ServerError) as raised:
        decode_response(response)

    assert raised.value.status_code == 503
    assert "empty body" in raised.value.message


def test_documented_error_body_still_wins_over_the_fallback() -> None:
    response = httpx.Response(
        status_code=404,
        json={"error": {"code": "not_found", "message": "Declaration was not found."}},
    )

    with pytest.raises(NotFoundError) as raised:
        decode_response(response)

    assert raised.value.message == "Declaration was not found."
    assert raised.value.code == "not_found"


def test_a_caller_supplied_client_needs_no_base_url() -> None:
    seen: Dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(status_code=200, json={"object": "ok"})

    # No base_url here: the transport addresses every request absolutely, so
    # bringing your own client does not mean repeating our base URL on it.
    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ClientConfig(api_key="phk_live_secret")
    transport = SyncTransport(config, http_client=http_client)

    payload = transport.get(path="/importers")

    assert payload == {"object": "ok"}
    assert seen["url"] == "https://app.pharos.pe/api/v1/importers"


def test_transport_identifies_itself() -> None:
    seen: Dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["user_agent"] = request.headers["user-agent"]
        return httpx.Response(status_code=200, json={"object": "ok"})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SyncTransport(ClientConfig(api_key="phk_live_secret"), http_client=http_client)

    transport.get(path="/importers")

    assert seen["user_agent"] == f"pharos-sdk/{__version__}"
