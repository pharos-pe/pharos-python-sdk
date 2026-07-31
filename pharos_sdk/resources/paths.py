"""URL path helpers for Pharos Connect resources."""

from __future__ import annotations

from typing import Optional, Union
from urllib.parse import quote

from pharos_sdk.models import DeclarationNumber
from pharos_sdk.types import QueryParams

DeclarationNumberInput = Union[str, DeclarationNumber]


def latest_params(limit: Optional[int]) -> Optional[QueryParams]:
    """Build query parameters for the latest declarations endpoint."""
    if limit is None:
        return None
    else:
        return {"limit": limit}


def declaration_path(full_number: DeclarationNumberInput) -> str:
    """Build the declaration detail path."""
    formatted_declaration_number = format_declaration_number(full_number)
    path_part = url_path_part(formatted_declaration_number)
    return f"/declarations/{path_part}"


def declaration_items_path(full_number: DeclarationNumberInput) -> str:
    """Build the declaration items path."""
    path = declaration_path(full_number)
    return f"{path}/items"


def declaration_item_path(full_number: DeclarationNumberInput, item_number: int) -> str:
    """Build the declaration item detail path."""
    path = declaration_items_path(full_number)
    return f"{path}/{item_number}"


def format_declaration_number(full_number: DeclarationNumberInput) -> str:
    """Return a declaration number string accepted by the API."""
    if isinstance(full_number, DeclarationNumber):
        return full_number.format()
    else:
        return full_number


def url_path_part(value: str) -> str:
    """Escape a path segment for an API URL."""
    return quote(value, safe="")
