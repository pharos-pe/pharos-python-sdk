"""Primitive JSON parsing helpers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, TypeVar
from uuid import UUID

from pharos_sdk.exceptions import ResponseDecodeError
from pharos_sdk.types import JSONObject, JSONValue

T = TypeVar("T")


def required(obj: JSONObject, key: str, *, path: str) -> JSONValue:
    """Read a required key from a JSON object."""
    try:
        return obj[key]
    except KeyError as e:
        raise ResponseDecodeError(f"Missing required field {path}.{key}.") from e


def as_object(value: JSONValue, *, path: str) -> JSONObject:
    """Parse a JSON object value."""
    if isinstance(value, dict):
        return value
    else:
        raise ResponseDecodeError(f"Expected object at {path}.")


def as_array(value: JSONValue, *, path: str) -> List[JSONValue]:
    """Parse a JSON array value."""
    if isinstance(value, list):
        return value
    else:
        raise ResponseDecodeError(f"Expected array at {path}.")


def field_object(payload: JSONObject, key: str, *, path: str) -> JSONObject:
    """Read and parse an object field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return as_object(value, path=field_path)


def field_string(payload: JSONObject, key: str, *, path: str) -> str:
    """Read and parse a string field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return string(value, path=field_path)


def field_optional_string(payload: JSONObject, key: str, *, path: str) -> Optional[str]:
    """Read and parse a nullable string field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return optional_string(value, path=field_path)


def field_int(payload: JSONObject, key: str, *, path: str) -> int:
    """Read and parse an integer field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return integer(value, path=field_path)


def field_optional_int(payload: JSONObject, key: str, *, path: str) -> Optional[int]:
    """Read and parse a nullable integer field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    if value is None:
        return None
    else:
        return integer(value, path=field_path)


def field_decimal(payload: JSONObject, key: str, *, path: str) -> Decimal:
    """Read and parse a decimal string field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return decimal_value(value, path=field_path)


def field_optional_decimal(payload: JSONObject, key: str, *, path: str) -> Optional[Decimal]:
    """Read and parse a nullable decimal field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return nullable_decimal(value, path=field_path)


def field_date(payload: JSONObject, key: str, *, path: str) -> date:
    """Read and parse a required ISO date field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return parse_date(value, path=field_path)


def field_optional_date(payload: JSONObject, key: str, *, path: str) -> Optional[date]:
    """Read and parse a nullable ISO date field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return nullable_date(value, path=field_path)


def field_datetime(payload: JSONObject, key: str, *, path: str) -> datetime:
    """Read and parse a timezone-aware ISO datetime field."""
    value = required(payload, key, path=path)
    field_path = f"{path}.{key}"
    return parse_datetime(value, path=field_path)


def string(value: JSONValue, *, path: str) -> str:
    """Parse a JSON string value."""
    if isinstance(value, str):
        return value
    else:
        raise ResponseDecodeError(f"Expected string at {path}.")


def optional_string(value: JSONValue, *, path: str) -> Optional[str]:
    """Parse a nullable JSON string value."""
    if value is None or isinstance(value, str):
        return value
    else:
        raise ResponseDecodeError(f"Expected string or null at {path}.")


def integer(value: JSONValue, *, path: str) -> int:
    """Parse a JSON integer value."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    else:
        raise ResponseDecodeError(f"Expected integer at {path}.")


def decimal_value(value: JSONValue, *, path: str) -> Decimal:
    """Parse a decimal string without losing precision."""
    if not isinstance(value, str):
        raise ResponseDecodeError(f"Expected decimal string at {path}.")
    try:
        return Decimal(value)
    except InvalidOperation as e:
        raise ResponseDecodeError(f"Invalid decimal at {path}.") from e


def nullable_decimal(value: JSONValue, *, path: str) -> Optional[Decimal]:
    """Parse a nullable decimal value."""
    if value is None:
        return None
    elif isinstance(value, str):
        return decimal_value(value, path=path)
    elif isinstance(value, int) and not isinstance(value, bool):
        return Decimal(value)
    elif isinstance(value, float):
        decimal_text = str(value)
        return Decimal(decimal_text)
    else:
        raise ResponseDecodeError(f"Expected decimal string, number, or null at {path}.")


def parse_date(value: JSONValue, *, path: str) -> date:
    """Parse an ISO date string."""
    if not isinstance(value, str):
        raise ResponseDecodeError(f"Expected date string at {path}.")
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise ResponseDecodeError(f"Invalid date at {path}.") from e


def nullable_date(value: JSONValue, *, path: str) -> Optional[date]:
    """Parse a nullable ISO date string."""
    if value is None:
        return None
    else:
        return parse_date(value, path=path)


def parse_datetime(value: JSONValue, *, path: str) -> datetime:
    """Parse a timezone-aware ISO datetime string."""
    if not isinstance(value, str):
        raise ResponseDecodeError(f"Expected datetime string at {path}.")
    try:
        normalized_value = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized_value)
    except ValueError as e:
        raise ResponseDecodeError(f"Invalid datetime at {path}.") from e
    else:
        if parsed.tzinfo is None:
            raise ResponseDecodeError(f"Expected timezone-aware datetime at {path}.")
        else:
            return parsed


def parse_uuid(value: JSONValue, *, path: str) -> UUID:
    """Parse a UUID string."""
    if not isinstance(value, str):
        raise ResponseDecodeError(f"Expected UUID string at {path}.")
    try:
        return UUID(value)
    except ValueError as e:
        raise ResponseDecodeError(f"Invalid UUID at {path}.") from e


def parse_tuple(
    value: JSONValue,
    parser: Callable[[JSONValue, str], T],
    *,
    path: str,
) -> Tuple[T, ...]:
    """Parse a JSON array into an immutable tuple."""
    items = as_array(value, path=path)
    parsed_items: List[T] = []
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        parsed_item = parser(item, item_path)
        parsed_items.append(parsed_item)
    return tuple(parsed_items)
