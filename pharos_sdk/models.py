"""Dataclass models for the Pharos Connect OpenAPI contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Generic, Optional, Tuple, TypeVar, Union
from uuid import UUID

T = TypeVar("T")


@dataclass(frozen=True)
class ListEnvelope(Generic[T]):
    """Common list response envelope returned by Pharos Connect."""

    object: str
    count: int
    retrieved_at: datetime
    data: Tuple[T, ...]
    limit: Optional[int] = None


@dataclass(frozen=True)
class Importer:
    """Company included in the integration scope."""

    object: str
    ruc: str
    name: str
    address: str
    department: Optional[str]
    province: Optional[str]
    district: Optional[str]


@dataclass(frozen=True)
class ImporterRef:
    """Minimal importer identity used in summaries and webhooks."""

    ruc: str
    name: str


@dataclass(frozen=True)
class CustomsOffice:
    """Customs office identity."""

    code: str
    name: str


@dataclass(frozen=True)
class CustomsBroker:
    """Customs broker identity."""

    code: str
    name: str


@dataclass(frozen=True)
class Vehicle:
    """Vehicle detail block for a vehicle item."""

    category: str
    vehicle_class: str
    brand: str
    model: str
    version: str
    model_year: Optional[int]
    vin_number: str
    chassis_number: str
    engine_number: str
    fuel_type: str
    engine_cylinders_count: Optional[int]
    engine_displacement_cc: Optional[Decimal]
    engine_power: str
    drivetrain: str
    transmission_type: str
    axles_count: int
    wheels_count: Optional[Decimal]
    seats_count: Optional[int]
    passengers_count: int
    color_1: str
    color_2: Optional[str]
    gross_weight: Optional[Decimal]
    net_weight: Optional[Decimal]
    load_capacity: Optional[Decimal]
    length_mm: Optional[Decimal]
    width_mm: Optional[Decimal]
    height_mm: Optional[Decimal]
    fob_usd: Optional[Decimal]
    freight_usd: Optional[Decimal]
    insurance_usd: Optional[Decimal]
    additional_notes: str


@dataclass(frozen=True)
class Product:
    """Product detail block for a product item."""

    commercial_description: str
    product_category: str
    brand: str
    model: str
    quantity: Decimal


@dataclass(frozen=True)
class ItemBase:
    """Fields shared by VehicleItem and ProductItem.

    `retrieved_at` is set only when the item was fetched on its own, through
    `declarations.item(...)`. Pharos puts it at the top level of every response,
    which for a list is the envelope: read `ListEnvelope.retrieved_at` there, or
    `Declaration.retrieved_at` for the items inside a declaration. It says when
    Pharos built the response, not when the declaration was read from customs —
    that is `created_at` and `updated_at`.
    """

    object: str
    item_number: int
    item_type: str
    nandina_code: str
    tariff_description: str
    commercial_description: str
    commercial_units: Decimal
    commercial_unit_type: str
    physical_units: Decimal
    package_quantity: Decimal
    package_class: str
    net_weight_kg: Decimal
    gross_weight_kg: Decimal
    fob_usd: Decimal
    freight_usd: Decimal
    insurance_usd: Decimal
    advalorem_usd: Decimal
    igv_usd: Decimal
    ipm_usd: Decimal
    isc_usd: Decimal
    origin_country: str
    acquisition_country: str
    port_of_loading: str
    bill_of_lading: str
    shipment_date: Optional[date]
    invoice_numbers: Tuple[str, ...]
    status: str
    retrieved_at: Optional[datetime]


@dataclass(frozen=True)
class VehicleItem(ItemBase):
    """Declaration item with a vehicle block."""

    vehicle: Vehicle


@dataclass(frozen=True)
class ProductItem(ItemBase):
    """Declaration item with a product block."""

    product: Product


Item = Union[VehicleItem, ProductItem]


@dataclass(frozen=True)
class DeclarationNumber:
    """Structured DUA number accepted by declaration resource methods."""

    customs_office: str
    year: int
    regime: str
    number: int
    control_number: Optional[str] = None

    def format(self) -> str:
        """Return the DUA number in the API path format."""
        base = f"{self.customs_office}-{self.year}-{self.regime}-{self.number:06d}"
        if self.control_number is None:
            return base
        else:
            return f"{base}-{self.control_number}"

    def __str__(self) -> str:
        return self.format()


@dataclass(frozen=True)
class DeclarationHeader:
    """Fields shared by Declaration and DeclarationSummary."""

    full_number: str
    customs_office: CustomsOffice
    year: int
    number: int
    revision: int
    numbering_date: date
    channel: str
    customs_broker: CustomsBroker
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TotalsBase:
    """Value totals present on every declaration representation."""

    items: int
    fob_usd: Decimal
    freight_usd: Decimal
    insurance_usd: Decimal
    cif_usd: Decimal


@dataclass(frozen=True)
class DeclarationSummary(DeclarationHeader):
    """Header-only declaration returned by the latest endpoint."""

    object: str
    importer: ImporterRef
    totals: TotalsBase


@dataclass(frozen=True)
class Transport:
    """Transport block of a full declaration."""

    mode: str
    company: Optional[str]
    terminal: str
    manifest_number: str


@dataclass(frozen=True)
class DeclarationTotals(TotalsBase):
    """Full declaration totals."""

    net_weight_kg: Decimal
    gross_weight_kg: Decimal
    packages: Decimal
    commercial_units: Decimal
    physical_units: Decimal
    liquidation: Decimal


@dataclass(frozen=True)
class Transaction:
    """Transaction block of a full declaration."""

    currency: str
    payment_method: str
    payment_term_days: Optional[int]


@dataclass(frozen=True)
class Declaration(DeclarationHeader):
    """Full declaration with items, vehicles and products."""

    object: str
    arrival_date: Optional[date]
    last_payment_date: date
    importer: Importer
    transport: Transport
    totals: DeclarationTotals
    transaction: Transaction
    items: Tuple[Item, ...]
    retrieved_at: datetime


@dataclass(frozen=True)
class WebhookDeclarationRef:
    """Declaration reference carried by webhook events."""

    full_number: str
    customs_office_code: str
    year: int
    number: int
    numbering_date: date
    items_count: int


@dataclass(frozen=True)
class WebhookEvent:
    """Base webhook event payload.

    `extra` holds whatever the endpoint was configured to send on top of the
    documented keys. The contract allows them — `additionalProperties: true` —
    and a typed event has to give them one named home or drop them, so anything
    that is not a field above arrives here. Values keep their JSON type, except
    on a form-encoded endpoint, where a form carried no types and they are text.
    """

    event_id: UUID
    event: str
    occurred_at: datetime
    revision: int
    declaration: WebhookDeclarationRef
    importer: ImporterRef
    resource_url: str
    extra: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DeclarationIngestedEvent(WebhookEvent):
    """Webhook event emitted when a declaration first enters Pharos."""


@dataclass(frozen=True)
class DeclarationCorrectedEvent(WebhookEvent):
    """Webhook event emitted when a declaration is reprocessed."""


@dataclass(frozen=True)
class DeclarationDeletedEvent(WebhookEvent):
    """Webhook event emitted before a declaration is removed."""


@dataclass(frozen=True)
class SeverityCounts:
    """Findings of each severity, with the zeros included."""

    critical: int
    high: int
    medium: int
    low: int


@dataclass(frozen=True)
class ValidationOccurrence:
    """Another declaration carrying the same identifier.

    Only a match inside your own companies is named; outside them the contract
    carries the date and the customs office alone. Read `match_scope` first.
    """

    match_scope: str
    numbering_date: date
    declaration_full_number: Optional[str] = None
    item_number: Optional[int] = None
    customs_office_code: Optional[str] = None


@dataclass(frozen=True)
class ValidationEvidence:
    """The values that triggered a finding, as they were at that moment.

    Which keys appear depends on the rule; those this version does not document
    arrive in `extra`, as they do on `WebhookEvent`.
    """

    identifier_type: Optional[str] = None
    identifier_value: Optional[str] = None
    match_scope: Optional[str] = None
    occurrence_count: Optional[int] = None
    item_numbers: Tuple[int, ...] = ()
    item_numbers_truncated: Optional[bool] = None
    occurrences: Tuple[ValidationOccurrence, ...] = ()
    occurrences_truncated: Optional[bool] = None
    extra: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationFinding:
    """One thing a rule observed about a series of the declaration."""

    rule_code: str
    rule_version: int
    category: str
    severity: str
    scope: str
    item_number: Optional[int]
    message: str
    evidence: ValidationEvidence


@dataclass(frozen=True)
class ValidationResult:
    """The aggregated outcome of validating one declaration revision.

    `status` is `issues_detected` or `passed`; a run where a rule did not
    execute is never reported at all.
    """

    status: str
    rules_evaluated_count: int
    findings_count: int
    severity_counts: SeverityCounts
    findings: Tuple[ValidationFinding, ...]
    evaluated_at: Optional[datetime]


@dataclass(frozen=True)
class DeclarationValidationCompletedEvent(WebhookEvent):
    """Webhook event emitted when Pharos finished reviewing a declaration.

    `validation` is always present on a delivered event; it is typed `Optional`
    only because a dataclass on Python 3.8 cannot follow a defaulted field with
    a required one.
    """

    validation: Optional[ValidationResult] = None
