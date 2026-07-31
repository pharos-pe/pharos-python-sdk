"""API error mapping for HTTP responses."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Optional, Type

from pharos_sdk.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from pharos_sdk.types import JSONObject, JSONValue


def api_error_from_response(
    status_code: int,
    payload: JSONObject,
    headers: Mapping[str, str],
    *,
    fallback_message: Optional[str] = None,
) -> APIError:
    """Map an error response into the SDK exception hierarchy.

    `fallback_message` describes a body the API did not write — a gateway error
    page, an empty response — so the raised error still says what happened.
    """
    error_value = payload.get("error")
    error = error_value if isinstance(error_value, dict) else {}
    code_value: JSONValue = error.get("code")
    message_value: JSONValue = error.get("message")
    code = code_value if isinstance(code_value, str) else None
    default_message = fallback_message or "Pharos API request failed."
    message = message_value if isinstance(message_value, str) else default_message
    retry_after_header = headers.get("retry-after")
    error_class = error_class_for(status_code, code)
    return error_class(
        message=message,
        status_code=status_code,
        code=code,
        retry_after=parse_retry_after(retry_after_header),
        headers=dict(headers),
    )


def error_class_for(status_code: int, code: Optional[str]) -> Type[APIError]:
    """Pick the exception class for a status code and documented error code."""
    if status_code == 401 or code == "unauthorized":
        return AuthenticationError
    elif status_code == 403 or code in {"access_disabled", "ip_not_allowed"}:
        return AuthorizationError
    elif status_code == 404 or code == "not_found":
        return NotFoundError
    elif status_code == 429 or code == "rate_limited":
        return RateLimitError
    elif status_code == 400 or code in {"invalid_parameter", "method_not_allowed"}:
        return InvalidRequestError
    elif status_code >= 500 or code == "internal_error":
        return ServerError
    else:
        return APIError


def parse_retry_after(value: Optional[str]) -> Optional[int]:
    """Parse Retry-After when it is an integer number of seconds."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
