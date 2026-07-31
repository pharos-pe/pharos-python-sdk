from __future__ import annotations

from pharos_sdk.models import DeclarationNumber
from pharos_sdk.resources.paths import (
    declaration_item_path,
    declaration_path,
    format_declaration_number,
    latest_params,
)


def test_declaration_number_formats_with_control_number() -> None:
    number = DeclarationNumber(
        customs_office="118",
        year=2026,
        regime="10",
        number=1234,
        control_number="00",
    )

    assert number.format() == "118-2026-10-001234-00"
    assert str(number) == "118-2026-10-001234-00"
    assert declaration_path(number) == "/declarations/118-2026-10-001234-00"


def test_declaration_number_formats_without_control_number() -> None:
    number = DeclarationNumber(
        customs_office="118",
        year=2026,
        regime="20",
        number=1234,
    )

    path = declaration_item_path(number, item_number=3)

    assert path == "/declarations/118-2026-20-001234/items/3"


def test_latest_params_omits_absent_limit() -> None:
    assert latest_params(limit=None) is None
    assert latest_params(limit=10) == {"limit": 10}


def test_format_declaration_number_accepts_plain_string() -> None:
    assert format_declaration_number("118-2026-10-001234") == "118-2026-10-001234"
