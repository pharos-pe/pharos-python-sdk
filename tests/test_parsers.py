from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from pharos_sdk.exceptions import ResponseDecodeError, UnsupportedWebhookEvent
from pharos_sdk.models import (
    DeclarationCorrectedEvent,
    DeclarationDeletedEvent,
    Importer,
    ProductItem,
    VehicleItem,
    WebhookEvent,
)
from pharos_sdk.parsers import parse_declaration, parse_item, parse_webhook_event
from pharos_sdk.parsers.declarations import parse_declaration_summary
from pharos_sdk.parsers.envelopes import parse_list_envelope
from pharos_sdk.parsers.importers import parse_importer_value
from pharos_sdk.parsers.primitives import (
    as_object,
    decimal_value,
    integer,
    nullable_decimal,
    optional_string,
    parse_date,
    parse_datetime,
    parse_tuple,
    parse_uuid,
    string,
)
from pharos_sdk.parsers.webhook_events import BASE_WEBHOOK_KEYS
from tests.fixtures import (
    declaration_payload,
    product_item_payload,
    summary_payload,
    vehicle_item_payload,
    webhook_payload,
)


def test_parse_list_envelope_with_importers() -> None:
    payload = {
        "object": "list",
        "count": 1,
        "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
        "data": [
            {
                "object": "importer",
                "ruc": "20100000001",
                "name": "EMPRESA DEMO S.A.C.",
                "address": "AV TEST 123",
                "department": None,
                "province": "LIMA",
                "district": "MIRAFLORES",
            }
        ],
    }

    envelope = parse_list_envelope(
        payload,
        item_parser=parse_importer_value,
    )

    assert envelope.object == "list"
    assert envelope.count == 1
    assert envelope.limit is None
    assert isinstance(envelope.data[0], Importer)
    assert envelope.data[0].department is None


def test_parse_list_envelope_preserves_limit() -> None:
    payload = {
        "object": "list",
        "count": 0,
        "limit": 20,
        "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
        "data": [],
    }

    envelope = parse_list_envelope(
        payload,
        item_parser=parse_importer_value,
    )

    assert envelope.limit == 20
    assert envelope.data == ()


def test_parse_declaration_summary() -> None:
    summary = parse_declaration_summary(summary_payload())

    assert summary.object == "declaration_summary"
    assert summary.customs_office.name == "MARITIMA DEL CALLAO"
    assert summary.importer.ruc == "20100000001"
    assert summary.totals.cif_usd == Decimal("53075.00")


def test_parse_vehicle_item_converts_money_dates_and_oneof() -> None:
    payload = vehicle_item_payload()
    payload["retrieved_at"] = "2026-07-30T14:25:01.882913+00:00"

    item = parse_item(payload)

    assert isinstance(item, VehicleItem)
    assert item.object == "declaration_item"
    assert item.fob_usd == Decimal("588.00")
    assert item.vehicle.gross_weight == Decimal("120.50")
    assert item.vehicle.wheels_count == Decimal("2")
    assert item.shipment_date is not None
    assert item.retrieved_at is not None
    assert item.retrieved_at.tzinfo is not None


def test_parse_product_item() -> None:
    item = parse_item(product_item_payload())

    assert isinstance(item, ProductItem)
    assert item.product.quantity == Decimal("2.00")


def test_parse_item_rejects_unknown_item_type() -> None:
    payload = vehicle_item_payload()
    payload["item_type"] = "SERVICE"

    with pytest.raises(ResponseDecodeError, match="Unsupported item_type"):
        parse_item(payload)


def test_parse_item_rejects_a_null_where_the_contract_promises_a_value() -> None:
    # The spec declares these non-nullable because the columns behind them are.
    # Accepting a null would put an Optional back into every caller's code for
    # a case Pharos cannot produce; if one ever arrives, it is a broken payload
    # and should say so here rather than three layers up.
    payload = vehicle_item_payload()
    payload["port_of_loading"] = None

    with pytest.raises(ResponseDecodeError, match=r"Expected string at \$\.port_of_loading"):
        parse_item(payload)


def test_parse_item_rejects_missing_matching_block() -> None:
    payload = vehicle_item_payload()
    payload.pop("vehicle")

    with pytest.raises(ResponseDecodeError, match="vehicle"):
        parse_item(payload)


def test_parse_declaration() -> None:
    declaration = parse_declaration(declaration_payload())

    assert declaration.full_number == "118-2026-10-001234-00"
    assert declaration.totals.liquidation == Decimal("124.60")
    assert declaration.created_at.tzinfo is not None
    assert declaration.importer.name == "EMPRESA DEMO S.A.C."
    assert len(declaration.items) == 2


def test_parse_webhook_corrected_event() -> None:
    payload = webhook_payload()
    payload["event"] = "declaration.corrected"

    event = parse_webhook_event(payload)

    assert isinstance(event, DeclarationCorrectedEvent)
    assert event.event == "declaration.corrected"
    assert event.extra == {"client_reference": "abc"}


def test_parse_webhook_deleted_event() -> None:
    payload = webhook_payload()
    payload["event"] = "declaration.deleted"

    event = parse_webhook_event(payload)

    assert isinstance(event, DeclarationDeletedEvent)
    assert event.declaration.full_number == "118-2026-10-001234-00"


def test_the_known_webhook_keys_are_exactly_the_event_fields() -> None:
    """What is not a field of the event is what lands in `extra`.

    The contract declares `additionalProperties: true`, so a typed event needs
    somewhere to put whatever an endpoint has configured on top of the
    documented keys. `BASE_WEBHOOK_KEYS` is what decides the boundary, and it is
    a second list of the same names: add a field here and forget it there, and
    the value arrives twice — once typed and once inside `extra`.
    """
    fields = {field.name for field in dataclasses.fields(WebhookEvent)}

    assert fields - {"extra"} == BASE_WEBHOOK_KEYS


def test_parse_webhook_flags_an_unknown_event_on_its_own() -> None:
    # Not a decoding error: the payload is fine, the type is simply newer than
    # this SDK. A handler catches this one specifically and acknowledges it.
    payload = webhook_payload()
    payload["event"] = "declaration.unknown"

    with pytest.raises(UnsupportedWebhookEvent) as raised:
        parse_webhook_event(payload)

    assert raised.value.event == "declaration.unknown"
    assert not isinstance(raised.value, ResponseDecodeError)


def test_parser_rejects_missing_required_field() -> None:
    payload = vehicle_item_payload()
    payload.pop("fob_usd")

    with pytest.raises(ResponseDecodeError, match="fob_usd"):
        parse_item(payload)


def test_parser_rejects_naive_datetime() -> None:
    payload = declaration_payload()
    payload["created_at"] = "2026-07-30T14:25:01"

    with pytest.raises(ResponseDecodeError, match="timezone-aware"):
        parse_declaration(payload)


def test_primitives_reject_invalid_values() -> None:
    with pytest.raises(ResponseDecodeError, match="decimal"):
        decimal_value("not-a-decimal", path="$.amount")

    with pytest.raises(ResponseDecodeError, match="UUID"):
        parse_uuid("not-a-uuid", path="$.event_id")

    with pytest.raises(ResponseDecodeError, match="datetime"):
        parse_datetime("not-a-datetime", path="$.occurred_at")


def test_nullable_decimal_accepts_json_numbers_without_float_precision_loss() -> None:
    assert nullable_decimal(2, path="$.amount") == Decimal("2")
    assert nullable_decimal(2.5, path="$.amount") == Decimal("2.5")
    assert nullable_decimal(None, path="$.amount") is None


def test_parse_tuple_rejects_non_array() -> None:
    def parser(value: object, path: str) -> object:
        return value

    with pytest.raises(ResponseDecodeError, match="array"):
        parse_tuple(
            {},
            parser=parser,
            path="$.data",
        )


def test_primitives_reject_invalid_json_shapes() -> None:
    with pytest.raises(ResponseDecodeError, match="object"):
        as_object([], path="$")

    with pytest.raises(ResponseDecodeError, match="string"):
        string(1, path="$.name")

    with pytest.raises(ResponseDecodeError, match="string or null"):
        optional_string(1, path="$.name")

    with pytest.raises(ResponseDecodeError, match="integer"):
        integer(True, path="$.count")

    with pytest.raises(ResponseDecodeError, match="decimal string"):
        decimal_value(1, path="$.amount")

    with pytest.raises(ResponseDecodeError, match="decimal string, number, or null"):
        nullable_decimal({}, path="$.amount")

    with pytest.raises(ResponseDecodeError, match="date string"):
        parse_date(1, path="$.numbering_date")

    with pytest.raises(ResponseDecodeError, match="Invalid date"):
        parse_date("not-a-date", path="$.numbering_date")

    with pytest.raises(ResponseDecodeError, match="datetime string"):
        parse_datetime(1, path="$.occurred_at")

    with pytest.raises(ResponseDecodeError, match="UUID string"):
        parse_uuid(1, path="$.event_id")
