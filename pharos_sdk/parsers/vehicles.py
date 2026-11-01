"""Parsers for vehicle lookup schemas."""

from __future__ import annotations

from pharos_sdk.models import VehicleMatch, VehicleMatchDeclaration
from pharos_sdk.parsers.customs import parse_customs_office
from pharos_sdk.parsers.importers import parse_importer_ref
from pharos_sdk.parsers.items import parse_vehicle
from pharos_sdk.parsers.primitives import (
    as_object,
    boolean,
    field_date,
    field_int,
    field_object,
    field_string,
    required,
)
from pharos_sdk.types import JSONObject, JSONValue


def parse_vehicle_match_value(value: JSONValue, path: str) -> VehicleMatch:
    """Parse a VehicleMatch value from a list envelope."""
    payload = as_object(value, path=path)
    return parse_vehicle_match(payload, path=path)


def parse_vehicle_match(payload: JSONObject, *, path: str = "$") -> VehicleMatch:
    """Parse a VehicleMatch object."""
    declaration_path = f"{path}.declaration"
    declaration = field_object(payload, key="declaration", path=path)
    vehicle = field_object(payload, key="vehicle", path=path)
    return VehicleMatch(
        object=field_string(payload, key="object", path=path),
        in_scope=boolean(required(payload, key="in_scope", path=path), path=f"{path}.in_scope"),
        declaration=parse_vehicle_match_declaration(declaration, path=declaration_path),
        item_number=field_int(payload, key="item_number", path=path),
        vehicle=parse_vehicle(vehicle, path=f"{path}.vehicle"),
    )


def parse_vehicle_match_declaration(payload: JSONObject, *, path: str) -> VehicleMatchDeclaration:
    """Parse the declaration block of a VehicleMatch."""
    office = field_object(payload, key="customs_office", path=path)
    importer = field_object(payload, key="importer", path=path)
    return VehicleMatchDeclaration(
        full_number=field_string(payload, key="full_number", path=path),
        numbering_date=field_date(payload, key="numbering_date", path=path),
        customs_office=parse_customs_office(office, path=f"{path}.customs_office"),
        importer=parse_importer_ref(importer, path=f"{path}.importer"),
    )
