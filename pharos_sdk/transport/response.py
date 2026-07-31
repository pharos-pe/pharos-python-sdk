"""HTTP response decoding."""

from __future__ import annotations

from typing import Optional, cast

import httpx

from pharos_sdk.exceptions import ResponseDecodeError
from pharos_sdk.transport.errors import api_error_from_response
from pharos_sdk.types import JSONObject, JSONValue

BODY_SNIPPET_LIMIT = 200


def decode_response(response: httpx.Response) -> JSONObject:
    """Decode a Pharos API response and raise mapped errors when needed."""
    headers = {key.lower(): value for key, value in response.headers.items()}
    if response.status_code >= 400:
        # Status first, body second. A failure that never reached the
        # application — a gateway 502, a bot challenge, a proxy error page —
        # arrives as HTML, and it still has to surface as an APIError, which is
        # what callers catch.
        payload = error_payload(response)
        fallback_message = None if payload else non_json_message(response)
        raise api_error_from_response(
            response.status_code,
            payload,
            headers,
            fallback_message=fallback_message,
        )
    else:
        return success_payload(response)


def success_payload(response: httpx.Response) -> JSONObject:
    """Decode a successful response body, which must be a JSON object."""
    try:
        response_value = response.json()
        value = cast(JSONValue, response_value)
    except ValueError as e:
        raise ResponseDecodeError("Pharos API response was not valid JSON.") from e
    if not isinstance(value, dict):
        raise ResponseDecodeError("Pharos API response was not a JSON object.")
    else:
        return value


def error_payload(response: httpx.Response) -> JSONObject:
    """Decode an error response body, or an empty object when it is not JSON."""
    try:
        response_value = response.json()
        value = cast(JSONValue, response_value)
    except ValueError:
        return {}
    else:
        return value if isinstance(value, dict) else {}


def non_json_message(response: httpx.Response) -> Optional[str]:
    """Describe an error body that did not come from the API itself."""
    snippet = " ".join(response.text.split())[:BODY_SNIPPET_LIMIT]
    if snippet:
        return f"Pharos API returned {response.status_code} with a non-JSON body: {snippet}"
    else:
        return f"Pharos API returned {response.status_code} with an empty body."
