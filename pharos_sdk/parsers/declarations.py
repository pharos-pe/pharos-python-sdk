"""Parsers for declaration schemas."""

from __future__ import annotations

from pharos_sdk.models import (
    Declaration,
    DeclarationHeader,
    DeclarationSummary,
    DeclarationTotals,
    TotalsBase,
    Transaction,
    Transport,
)
from pharos_sdk.parsers.customs import parse_customs_broker, parse_customs_office
from pharos_sdk.parsers.importers import parse_importer, parse_importer_ref
from pharos_sdk.parsers.items import parse_item_value
from pharos_sdk.parsers.primitives import (
    as_object,
    field_date,
    field_datetime,
    field_decimal,
    field_int,
    field_object,
    field_optional_date,
    field_optional_int,
    field_optional_string,
    field_string,
    parse_tuple,
    required,
)
from pharos_sdk.types import JSONObject, JSONValue


def parse_declaration_summary_value(value: JSONValue, path: str) -> DeclarationSummary:
    """Parse a DeclarationSummary value from a list envelope."""
    payload = as_object(value, path=path)
    return parse_declaration_summary(payload, path=path)


def parse_declaration_summary(payload: JSONObject, *, path: str = "$") -> DeclarationSummary:
    """Parse a DeclarationSummary object."""
    header = parse_declaration_header(payload, path=path)
    importer_payload = field_object(payload, key="importer", path=path)
    importer_path = f"{path}.importer"
    importer = parse_importer_ref(importer_payload, path=importer_path)
    totals_payload = field_object(payload, key="totals", path=path)
    totals_path = f"{path}.totals"
    totals = parse_totals_base(totals_payload, path=totals_path)
    return DeclarationSummary(
        full_number=header.full_number,
        customs_office=header.customs_office,
        year=header.year,
        number=header.number,
        revision=header.revision,
        numbering_date=header.numbering_date,
        channel=header.channel,
        customs_broker=header.customs_broker,
        created_at=header.created_at,
        updated_at=header.updated_at,
        object=field_string(payload, key="object", path=path),
        importer=importer,
        totals=totals,
    )


def parse_declaration(payload: JSONObject, *, path: str = "$") -> Declaration:
    """Parse a full Declaration object."""
    header = parse_declaration_header(payload, path=path)
    importer_payload = field_object(payload, key="importer", path=path)
    importer_path = f"{path}.importer"
    importer = parse_importer(importer_payload, path=importer_path)
    transport_payload = field_object(payload, key="transport", path=path)
    transport_path = f"{path}.transport"
    transport = parse_transport(transport_payload, path=transport_path)
    totals_payload = field_object(payload, key="totals", path=path)
    totals_path = f"{path}.totals"
    totals = parse_declaration_totals(totals_payload, path=totals_path)
    transaction_payload = field_object(payload, key="transaction", path=path)
    transaction_path = f"{path}.transaction"
    transaction = parse_transaction(transaction_payload, path=transaction_path)
    items_value = required(payload, key="items", path=path)
    items_path = f"{path}.items"
    items = parse_tuple(items_value, parser=parse_item_value, path=items_path)
    return Declaration(
        full_number=header.full_number,
        customs_office=header.customs_office,
        year=header.year,
        number=header.number,
        revision=header.revision,
        numbering_date=header.numbering_date,
        channel=header.channel,
        customs_broker=header.customs_broker,
        created_at=header.created_at,
        updated_at=header.updated_at,
        object=field_string(payload, key="object", path=path),
        arrival_date=field_optional_date(payload, key="arrival_date", path=path),
        last_payment_date=field_date(payload, key="last_payment_date", path=path),
        importer=importer,
        transport=transport,
        totals=totals,
        transaction=transaction,
        items=items,
        retrieved_at=field_datetime(payload, key="retrieved_at", path=path),
    )


def parse_declaration_header(payload: JSONObject, *, path: str) -> DeclarationHeader:
    """Parse fields shared by Declaration and DeclarationSummary."""
    office_payload = field_object(payload, key="customs_office", path=path)
    office_path = f"{path}.customs_office"
    customs_office = parse_customs_office(office_payload, path=office_path)
    broker_payload = field_object(payload, key="customs_broker", path=path)
    broker_path = f"{path}.customs_broker"
    customs_broker = parse_customs_broker(broker_payload, path=broker_path)
    return DeclarationHeader(
        full_number=field_string(payload, key="full_number", path=path),
        customs_office=customs_office,
        year=field_int(payload, key="year", path=path),
        number=field_int(payload, key="number", path=path),
        revision=field_int(payload, key="revision", path=path),
        numbering_date=field_date(payload, key="numbering_date", path=path),
        channel=field_string(payload, key="channel", path=path),
        customs_broker=customs_broker,
        created_at=field_datetime(payload, key="created_at", path=path),
        updated_at=field_datetime(payload, key="updated_at", path=path),
    )


def parse_declaration_totals(payload: JSONObject, *, path: str) -> DeclarationTotals:
    """Parse full declaration totals."""
    base = parse_totals_base(payload, path=path)
    return DeclarationTotals(
        items=base.items,
        fob_usd=base.fob_usd,
        freight_usd=base.freight_usd,
        insurance_usd=base.insurance_usd,
        cif_usd=base.cif_usd,
        net_weight_kg=field_decimal(payload, key="net_weight_kg", path=path),
        gross_weight_kg=field_decimal(payload, key="gross_weight_kg", path=path),
        packages=field_decimal(payload, key="packages", path=path),
        commercial_units=field_decimal(payload, key="commercial_units", path=path),
        physical_units=field_decimal(payload, key="physical_units", path=path),
        liquidation=field_decimal(payload, key="liquidation", path=path),
    )


def parse_totals_base(payload: JSONObject, *, path: str) -> TotalsBase:
    """Parse a TotalsBase object."""
    return TotalsBase(
        items=field_int(payload, key="items", path=path),
        fob_usd=field_decimal(payload, key="fob_usd", path=path),
        freight_usd=field_decimal(payload, key="freight_usd", path=path),
        insurance_usd=field_decimal(payload, key="insurance_usd", path=path),
        cif_usd=field_decimal(payload, key="cif_usd", path=path),
    )


def parse_transport(payload: JSONObject, *, path: str) -> Transport:
    """Parse a Transport object."""
    return Transport(
        mode=field_string(payload, key="mode", path=path),
        company=field_optional_string(payload, key="company", path=path),
        terminal=field_string(payload, key="terminal", path=path),
        manifest_number=field_string(payload, key="manifest_number", path=path),
    )


def parse_transaction(payload: JSONObject, *, path: str) -> Transaction:
    """Parse a Transaction object."""
    return Transaction(
        currency=field_string(payload, key="currency", path=path),
        payment_method=field_string(payload, key="payment_method", path=path),
        payment_term_days=field_optional_int(payload, key="payment_term_days", path=path),
    )
