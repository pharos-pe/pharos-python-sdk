"""Parsers for declaration item schemas."""

from __future__ import annotations

from pharos_sdk.exceptions import ResponseDecodeError
from pharos_sdk.models import Item, ItemBase, Product, ProductItem, Vehicle, VehicleItem
from pharos_sdk.parsers.primitives import (
    as_object,
    field_decimal,
    field_int,
    field_object,
    field_optional_date,
    field_optional_decimal,
    field_optional_int,
    field_optional_string,
    field_string,
    parse_datetime,
    parse_tuple,
    required,
    string,
)
from pharos_sdk.types import JSONObject, JSONValue


def parse_item_value(value: JSONValue, path: str) -> Item:
    """Parse an Item value from a list or declaration."""
    payload = as_object(value, path=path)
    return parse_item(payload, path=path)


def parse_item(payload: JSONObject, *, path: str = "$") -> Item:
    """Parse the Item oneOf schema into VehicleItem or ProductItem."""
    base = parse_item_base(payload, path=path)
    if base.item_type == "VEHICLE":
        vehicle_payload = field_object(payload, key="vehicle", path=path)
        vehicle_path = f"{path}.vehicle"
        vehicle = parse_vehicle(vehicle_payload, path=vehicle_path)
        return vehicle_item_from_base(base, vehicle)
    elif base.item_type == "PRODUCT":
        product_payload = field_object(payload, key="product", path=path)
        product_path = f"{path}.product"
        product = parse_product(product_payload, path=product_path)
        return product_item_from_base(base, product)
    else:
        raise ResponseDecodeError(f"Unsupported item_type at {path}.item_type.")


def parse_invoice_number(value: JSONValue, path: str) -> str:
    """Parse one invoice number from an item invoice list."""
    return string(value, path=path)


def parse_item_base(payload: JSONObject, *, path: str) -> ItemBase:
    """Parse fields shared by VehicleItem and ProductItem."""
    retrieved_value = payload.get("retrieved_at")
    invoice_numbers_value = required(payload, key="invoice_numbers", path=path)
    invoice_numbers_path = f"{path}.invoice_numbers"
    invoice_numbers = parse_tuple(
        invoice_numbers_value,
        parser=parse_invoice_number,
        path=invoice_numbers_path,
    )
    if retrieved_value is not None:
        retrieved_at_path = f"{path}.retrieved_at"
        retrieved_at = parse_datetime(retrieved_value, path=retrieved_at_path)
    else:
        retrieved_at = None
    return ItemBase(
        object=field_string(payload, key="object", path=path),
        item_number=field_int(payload, key="item_number", path=path),
        item_type=field_string(payload, key="item_type", path=path),
        nandina_code=field_string(payload, key="nandina_code", path=path),
        tariff_description=field_string(payload, key="tariff_description", path=path),
        commercial_description=field_string(payload, key="commercial_description", path=path),
        commercial_units=field_decimal(payload, key="commercial_units", path=path),
        commercial_unit_type=field_string(payload, key="commercial_unit_type", path=path),
        physical_units=field_decimal(payload, key="physical_units", path=path),
        package_quantity=field_decimal(payload, key="package_quantity", path=path),
        package_class=field_string(payload, key="package_class", path=path),
        net_weight_kg=field_decimal(payload, key="net_weight_kg", path=path),
        gross_weight_kg=field_decimal(payload, key="gross_weight_kg", path=path),
        fob_usd=field_decimal(payload, key="fob_usd", path=path),
        freight_usd=field_decimal(payload, key="freight_usd", path=path),
        insurance_usd=field_decimal(payload, key="insurance_usd", path=path),
        advalorem_usd=field_decimal(payload, key="advalorem_usd", path=path),
        igv_usd=field_decimal(payload, key="igv_usd", path=path),
        ipm_usd=field_decimal(payload, key="ipm_usd", path=path),
        isc_usd=field_decimal(payload, key="isc_usd", path=path),
        origin_country=field_string(payload, key="origin_country", path=path),
        acquisition_country=field_string(payload, key="acquisition_country", path=path),
        port_of_loading=field_string(payload, key="port_of_loading", path=path),
        bill_of_lading=field_string(payload, key="bill_of_lading", path=path),
        shipment_date=field_optional_date(payload, key="shipment_date", path=path),
        invoice_numbers=invoice_numbers,
        status=field_string(payload, key="status", path=path),
        retrieved_at=retrieved_at,
    )


def parse_vehicle(payload: JSONObject, *, path: str) -> Vehicle:
    """Parse a Vehicle object."""
    return Vehicle(
        category=field_string(payload, key="category", path=path),
        vehicle_class=field_string(payload, key="vehicle_class", path=path),
        brand=field_string(payload, key="brand", path=path),
        model=field_string(payload, key="model", path=path),
        version=field_string(payload, key="version", path=path),
        model_year=field_optional_int(payload, key="model_year", path=path),
        vin_number=field_string(payload, key="vin_number", path=path),
        chassis_number=field_string(payload, key="chassis_number", path=path),
        engine_number=field_string(payload, key="engine_number", path=path),
        fuel_type=field_string(payload, key="fuel_type", path=path),
        engine_cylinders_count=field_optional_int(payload, key="engine_cylinders_count", path=path),
        engine_displacement_cc=field_optional_decimal(
            payload,
            key="engine_displacement_cc",
            path=path,
        ),
        engine_power=field_string(payload, key="engine_power", path=path),
        drivetrain=field_string(payload, key="drivetrain", path=path),
        transmission_type=field_string(payload, key="transmission_type", path=path),
        axles_count=field_int(payload, key="axles_count", path=path),
        wheels_count=field_optional_decimal(payload, key="wheels_count", path=path),
        seats_count=field_optional_int(payload, key="seats_count", path=path),
        passengers_count=field_int(payload, key="passengers_count", path=path),
        color_1=field_string(payload, key="color_1", path=path),
        color_2=field_optional_string(payload, key="color_2", path=path),
        gross_weight=field_optional_decimal(payload, key="gross_weight", path=path),
        net_weight=field_optional_decimal(payload, key="net_weight", path=path),
        load_capacity=field_optional_decimal(payload, key="load_capacity", path=path),
        length_mm=field_optional_decimal(payload, key="length_mm", path=path),
        width_mm=field_optional_decimal(payload, key="width_mm", path=path),
        height_mm=field_optional_decimal(payload, key="height_mm", path=path),
        fob_usd=field_optional_decimal(payload, key="fob_usd", path=path),
        freight_usd=field_optional_decimal(payload, key="freight_usd", path=path),
        insurance_usd=field_optional_decimal(payload, key="insurance_usd", path=path),
        additional_notes=field_string(payload, key="additional_notes", path=path),
    )


def parse_product(payload: JSONObject, *, path: str) -> Product:
    """Parse a Product object."""
    return Product(
        commercial_description=field_string(payload, key="commercial_description", path=path),
        product_category=field_string(payload, key="product_category", path=path),
        brand=field_string(payload, key="brand", path=path),
        model=field_string(payload, key="model", path=path),
        quantity=field_decimal(payload, key="quantity", path=path),
    )


def vehicle_item_from_base(base: ItemBase, vehicle: Vehicle) -> VehicleItem:
    """Build a VehicleItem from common item fields and a Vehicle block."""
    return VehicleItem(
        object=base.object,
        item_number=base.item_number,
        item_type=base.item_type,
        nandina_code=base.nandina_code,
        tariff_description=base.tariff_description,
        commercial_description=base.commercial_description,
        commercial_units=base.commercial_units,
        commercial_unit_type=base.commercial_unit_type,
        physical_units=base.physical_units,
        package_quantity=base.package_quantity,
        package_class=base.package_class,
        net_weight_kg=base.net_weight_kg,
        gross_weight_kg=base.gross_weight_kg,
        fob_usd=base.fob_usd,
        freight_usd=base.freight_usd,
        insurance_usd=base.insurance_usd,
        advalorem_usd=base.advalorem_usd,
        igv_usd=base.igv_usd,
        ipm_usd=base.ipm_usd,
        isc_usd=base.isc_usd,
        origin_country=base.origin_country,
        acquisition_country=base.acquisition_country,
        port_of_loading=base.port_of_loading,
        bill_of_lading=base.bill_of_lading,
        shipment_date=base.shipment_date,
        invoice_numbers=base.invoice_numbers,
        status=base.status,
        retrieved_at=base.retrieved_at,
        vehicle=vehicle,
    )


def product_item_from_base(base: ItemBase, product: Product) -> ProductItem:
    """Build a ProductItem from common item fields and a Product block."""
    return ProductItem(
        object=base.object,
        item_number=base.item_number,
        item_type=base.item_type,
        nandina_code=base.nandina_code,
        tariff_description=base.tariff_description,
        commercial_description=base.commercial_description,
        commercial_units=base.commercial_units,
        commercial_unit_type=base.commercial_unit_type,
        physical_units=base.physical_units,
        package_quantity=base.package_quantity,
        package_class=base.package_class,
        net_weight_kg=base.net_weight_kg,
        gross_weight_kg=base.gross_weight_kg,
        fob_usd=base.fob_usd,
        freight_usd=base.freight_usd,
        insurance_usd=base.insurance_usd,
        advalorem_usd=base.advalorem_usd,
        igv_usd=base.igv_usd,
        ipm_usd=base.ipm_usd,
        isc_usd=base.isc_usd,
        origin_country=base.origin_country,
        acquisition_country=base.acquisition_country,
        port_of_loading=base.port_of_loading,
        bill_of_lading=base.bill_of_lading,
        shipment_date=base.shipment_date,
        invoice_numbers=base.invoice_numbers,
        status=base.status,
        retrieved_at=base.retrieved_at,
        product=product,
    )
