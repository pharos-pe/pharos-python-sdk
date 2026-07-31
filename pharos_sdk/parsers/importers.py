"""Parsers for importer schemas."""

from __future__ import annotations

from pharos_sdk.models import Importer, ImporterRef
from pharos_sdk.parsers.primitives import as_object, field_optional_string, field_string
from pharos_sdk.types import JSONObject, JSONValue


def parse_importer_value(value: JSONValue, path: str) -> Importer:
    """Parse an Importer value from a list envelope."""
    payload = as_object(value, path=path)
    return parse_importer(payload, path=path)


def parse_importer(payload: JSONObject, *, path: str = "$") -> Importer:
    """Parse an Importer object."""
    return Importer(
        object=field_string(payload, key="object", path=path),
        ruc=field_string(payload, key="ruc", path=path),
        name=field_string(payload, key="name", path=path),
        address=field_string(payload, key="address", path=path),
        department=field_optional_string(payload, key="department", path=path),
        province=field_optional_string(payload, key="province", path=path),
        district=field_optional_string(payload, key="district", path=path),
    )


def parse_importer_ref(payload: JSONObject, *, path: str) -> ImporterRef:
    """Parse an ImporterRef object."""
    return ImporterRef(
        ruc=field_string(payload, key="ruc", path=path),
        name=field_string(payload, key="name", path=path),
    )
