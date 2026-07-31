from __future__ import annotations

from typing import Dict


def importer_payload() -> Dict[str, object]:
    return {
        "object": "importer",
        "ruc": "20100000001",
        "name": "EMPRESA DEMO S.A.C.",
        "address": "AV TEST 123",
        "department": None,
        "province": "LIMA",
        "district": "MIRAFLORES",
    }


def importer_list_payload() -> Dict[str, object]:
    return {
        "object": "list",
        "count": 1,
        "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
        "data": [importer_payload()],
    }


def vehicle_payload() -> Dict[str, object]:
    return {
        "category": "L1",
        "vehicle_class": "MOTOCICLETA",
        "brand": "MARCA DEMO",
        "model": "G5",
        "version": "",
        "model_year": 2026,
        "vin_number": "LXYTBK",
        "chassis_number": "LXYTBK",
        "engine_number": "TDT",
        "fuel_type": "ELECTRIC",
        "engine_cylinders_count": None,
        "engine_displacement_cc": None,
        "engine_power": "1.00@500",
        "drivetrain": "ELECTRIC",
        "transmission_type": "AUTOMATIC",
        "axles_count": 2,
        "wheels_count": "2",
        "seats_count": 2,
        "passengers_count": 2,
        "color_1": "NEGRO",
        "color_2": None,
        "gross_weight": "120.50",
        "net_weight": "100.00",
        "load_capacity": None,
        "length_mm": "1800",
        "width_mm": "700",
        "height_mm": "1100",
        "fob_usd": "588.00",
        "freight_usd": None,
        "insurance_usd": None,
        "additional_notes": "",
    }


def vehicle_item_payload() -> Dict[str, object]:
    return {
        "object": "declaration_item",
        "item_number": 1,
        "item_type": "VEHICLE",
        "nandina_code": "87.11.60.00.00",
        "tariff_description": "MOTOCICLETA ELECTRICA",
        "commercial_description": "MOTOCICLETA ELECTRICA MARCA DEMO",
        "commercial_units": "1.00",
        "commercial_unit_type": "U",
        "physical_units": "1.00",
        "package_quantity": "1.00",
        "package_class": "CAJA",
        "net_weight_kg": "100.00",
        "gross_weight_kg": "120.00",
        "fob_usd": "588.00",
        "freight_usd": "30.00",
        "insurance_usd": "5.00",
        "advalorem_usd": "0.00",
        "igv_usd": "112.14",
        "ipm_usd": "12.46",
        "isc_usd": "0.00",
        "origin_country": "PAIS DEMO",
        "acquisition_country": "PAIS DEMO",
        "port_of_loading": "PUERTO DEMO",
        "bill_of_lading": "BL123",
        "shipment_date": "2026-05-20",
        "invoice_numbers": ["F001-1"],
        "status": "ACTIVE",
        "vehicle": vehicle_payload(),
    }


def product_item_payload() -> Dict[str, object]:
    item = vehicle_item_payload()
    item.pop("vehicle")
    item["item_number"] = 2
    item["item_type"] = "PRODUCT"
    item["product"] = {
        "commercial_description": "CARGADOR",
        "product_category": "PARTS",
        "brand": "MARCA GENERICA",
        "model": "MODELO GENERICO",
        "quantity": "2.00",
    }
    return item


def summary_payload() -> Dict[str, object]:
    return {
        "object": "declaration_summary",
        "full_number": "118-2026-10-001234-00",
        "customs_office": {"code": "118", "name": "MARITIMA DEL CALLAO"},
        "year": 2026,
        "number": 1234,
        "revision": 2,
        "numbering_date": "2026-06-01",
        "channel": "VERDE",
        "importer": {"ruc": "20100000001", "name": "EMPRESA DEMO S.A.C."},
        "customs_broker": {"code": "0001", "name": "AGENCIA DEMO"},
        "totals": {
            "items": 12,
            "fob_usd": "48250.00",
            "freight_usd": "3860.00",
            "insurance_usd": "965.00",
            "cif_usd": "53075.00",
        },
        "created_at": "2026-06-02T09:14:22.104512+00:00",
        "updated_at": "2026-07-30T14:22:05.113291+00:00",
    }


def declaration_payload() -> Dict[str, object]:
    payload = summary_payload()
    payload.update(
        {
            "object": "declaration",
            "arrival_date": None,
            "last_payment_date": "2026-06-10",
            "importer": importer_payload(),
            "transport": {
                "mode": "MARITIMO",
                "company": None,
                "terminal": "TERMINAL DEMO",
                "manifest_number": "MAN123",
            },
            "totals": {
                "items": 12,
                "fob_usd": "48250.00",
                "freight_usd": "3860.00",
                "insurance_usd": "965.00",
                "cif_usd": "53075.00",
                "net_weight_kg": "100.00",
                "gross_weight_kg": "120.00",
                "packages": "1.00",
                "commercial_units": "1.00",
                "physical_units": "1.00",
                "liquidation": "124.60",
            },
            "transaction": {
                "currency": "USD",
                "payment_method": "CONTADO",
                "payment_term_days": None,
            },
            "items": [vehicle_item_payload(), product_item_payload()],
            "retrieved_at": "2026-07-30T14:25:01.882913+00:00",
        }
    )
    return payload


def webhook_payload() -> Dict[str, object]:
    return {
        "event_id": "2cda6cfd-ef58-437f-a60f-169c9fa59ed9",
        "event": "declaration.ingested",
        "occurred_at": "2026-07-30T14:25:01.882913+00:00",
        "revision": 1,
        "declaration": {
            "full_number": "118-2026-10-001234-00",
            "customs_office_code": "118",
            "year": 2026,
            "number": 1234,
            "numbering_date": "2026-06-01",
            "items_count": 12,
        },
        "importer": {"ruc": "20100000001", "name": "EMPRESA DEMO S.A.C."},
        "resource_url": "https://app.pharos.pe/api/v1/declarations/118-2026-10-001234-00",
        "client_reference": "abc",
    }
