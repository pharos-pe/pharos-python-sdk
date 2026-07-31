"""Parsers for customs identity schemas."""

from __future__ import annotations

from pharos_sdk.models import CustomsBroker, CustomsOffice
from pharos_sdk.parsers.primitives import field_string
from pharos_sdk.types import JSONObject


def parse_customs_office(payload: JSONObject, *, path: str) -> CustomsOffice:
    """Parse a CustomsOffice object."""
    return CustomsOffice(
        code=field_string(payload, key="code", path=path),
        name=field_string(payload, key="name", path=path),
    )


def parse_customs_broker(payload: JSONObject, *, path: str) -> CustomsBroker:
    """Parse a CustomsBroker object."""
    return CustomsBroker(
        code=field_string(payload, key="code", path=path),
        name=field_string(payload, key="name", path=path),
    )
