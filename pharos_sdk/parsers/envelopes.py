"""Parsers for list envelopes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional, TypeVar

from pharos_sdk.models import ListEnvelope
from pharos_sdk.parsers.primitives import (
    field_datetime,
    field_int,
    field_string,
    integer,
    parse_tuple,
    required,
    string,
)
from pharos_sdk.types import JSONObject, JSONValue

T = TypeVar("T")


def parse_list_envelope(
    payload: JSONObject,
    item_parser: Callable[[JSONValue, str], T],
) -> ListEnvelope[T]:
    """Parse the OpenAPI ListEnvelope schema and endpoint-specific data."""
    limit_value = payload.get("limit")
    limit = _make_limit(limit_value)
    scope = _make_scope(payload.get("scope"))
    data_value = required(payload, key="data", path="$")
    data = parse_tuple(data_value, parser=item_parser, path="$.data")
    return ListEnvelope(
        object=field_string(payload, key="object", path="$"),
        count=field_int(payload, key="count", path="$"),
        retrieved_at=field_datetime(payload, key="retrieved_at", path="$"),
        data=data,
        limit=limit,
        scope=scope,
    )


def _make_limit(limit_value: JSONValue) -> Optional[int]:
    if limit_value is not None:
        return integer(limit_value, path="$.limit")
    else:
        return None


def _make_scope(scope_value: JSONValue) -> Optional[str]:
    if scope_value is not None:
        return string(scope_value, path="$.scope")
    else:
        return None
