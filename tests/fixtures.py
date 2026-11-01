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


def vehicle_match_payload() -> Dict[str, object]:
    return {
        "object": "vehicle_match",
        "in_scope": False,
        "declaration": {
            "full_number": "118-2026-10-001234-00",
            "numbering_date": "2026-03-04",
            "customs_office": {"code": "118", "name": "MARITIMA DEL CALLAO"},
            "importer": {"ruc": "20100000003", "name": "GREENLINE TRES S.A.C."},
        },
        "item_number": 1,
        "vehicle": vehicle_payload(),
    }


def vehicle_lookup_payload() -> Dict[str, object]:
    return {
        "object": "list",
        "scope": "global",
        "count": 1,
        "retrieved_at": "2026-03-04T12:00:00+00:00",
        "data": [vehicle_match_payload()],
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


def validation_webhook_payload() -> Dict[str, object]:
    return {
        "event_id": "c4f1a9d2-77b3-4e1a-9c05-1d8e2f6a4b70",
        "event": "declaration.validation_completed",
        "occurred_at": "2026-07-30T15:04:11.882014+00:00",
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
        "validation": {
            "status": "issues_detected",
            "rules_evaluated_count": 3,
            "findings_count": 2,
            "severity_counts": {"critical": 0, "high": 2, "medium": 0, "low": 0},
            "findings": [
                {
                    "rule_code": "duplicate_vin_in_declaration",
                    "rule_version": 1,
                    "category": "identifier_conflict",
                    "severity": "high",
                    "scope": "declaration",
                    "item_number": 3,
                    "message": "The vin LZPAERLMXRB000946 appears on 2 items.",
                    "evidence": {
                        "identifier_type": "vin",
                        "identifier_value": "LZPAERLMXRB000946",
                        "match_scope": "same_declaration",
                        "occurrence_count": 2,
                        "item_numbers": [3, 7],
                        "item_numbers_truncated": False,
                    },
                },
                {
                    "rule_code": "duplicate_engine_number",
                    "rule_version": 1,
                    "category": "identifier_conflict",
                    "severity": "high",
                    "scope": "account_history",
                    "item_number": 4,
                    "message": "The engine_number 120YC6040403NA250516 is already recorded.",
                    "evidence": {
                        "identifier_type": "engine_number",
                        "identifier_value": "120YC6040403NA250516",
                        "occurrence_count": 2,
                        "occurrences_truncated": False,
                        "occurrences": [
                            {
                                "match_scope": "authorized_importers",
                                "declaration_full_number": "118-2025-10-009876-00",
                                "item_number": 4,
                                "numbering_date": "2025-11-14",
                            },
                            {
                                "match_scope": "external_importer",
                                "numbering_date": "2026-02-03",
                                "customs_office_code": "235",
                            },
                        ],
                    },
                },
            ],
            "evaluated_at": "2026-07-30T15:04:11.640922+00:00",
        },
    }
