"""Domain schemas for the Spectacles reorder assistant backend.

We keep these lean and explicit to guard against API drift. Each request/response
model lines up with a public endpoint contract.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, conint, conlist, constr


# --- Enumerations -----------------------------------------------------------------


class DetectionConfidence(str, Enum):
    """Coarse confidence buckets from the on-device perception pipeline."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FillLevel(str, Enum):
    """Discrete fill-state classification reported by the CV model."""

    FULL = "FULL"
    MOSTLY_FULL = "MOSTLY_FULL"
    HALF = "HALF"
    NEARLY_EMPTY = "NEARLY_EMPTY"
    EMPTY = "EMPTY"


class ConfirmationChannel(str, Enum):
    """Supported confirmation modalities coming from Spectacles."""

    VOICE = "VOICE"
    GESTURE = "GESTURE"
    TAP = "TAP"


class OrderStatus(str, Enum):
    """High-level lifecycle for a reorder request."""

    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


# --- Product catalog models -------------------------------------------------------


class ProductVariant(BaseModel):
    sku: constr(strip_whitespace=True, min_length=2)  # type: ignore[valid-type]
    label: constr(strip_whitespace=True, min_length=2)
    size: Optional[str] = Field(default=None, description="Human readable size, e.g. 24-pack")
    unit_price_usd: Optional[float] = Field(default=None, ge=0)


class Product(BaseModel):
    id: constr(strip_whitespace=True, min_length=2)  # type: ignore[valid-type]
    object_class: constr(strip_whitespace=True, min_length=2)
    default_variant: ProductVariant
    variants: List[ProductVariant] = Field(default_factory=list)
    reorder_threshold: FillLevel = Field(
        default=FillLevel.NEARLY_EMPTY,
        description="Minimum fill level before we attempt a reorder prompt.",
    )
    metadata: Dict[str, str] = Field(default_factory=dict)


# --- Detection and intent payloads ------------------------------------------------


class DetectionEvent(BaseModel):
    """Single perception event emitted by Spectacles."""

    event_id: constr(strip_whitespace=True, min_length=8)  # type: ignore[valid-type]
    device_id: constr(strip_whitespace=True, min_length=4)
    object_class: constr(strip_whitespace=True, min_length=2)
    fill_level: FillLevel
    confidence: DetectionConfidence
    captured_at_ms: PositiveInt = Field(description="Client-side timestamp in epoch ms")
    frame_id: Optional[conint(ge=0)] = Field(default=None)
    location_hint: Optional[Dict[str, float]] = Field(
        default=None, description="Optional lat/lon or room coordinates"
    )


class DetectionIngestResponse(BaseModel):
    next_prompt_allowed_at_ms: Optional[PositiveInt]
    should_prompt: bool
    reason: Optional[str] = None
    pending_intent_id: Optional[str] = None


class PromptIntent(BaseModel):
    """Server-side record tying a detection to a prompt conversation."""

    intent_id: constr(strip_whitespace=True, min_length=8)  # type: ignore[valid-type]
    event_id: str
    product_id: str
    variant_sku: str
    created_at_ms: PositiveInt
    expires_at_ms: PositiveInt


class PromptDecisionRequest(BaseModel):
    intent_id: constr(strip_whitespace=True, min_length=8)  # type: ignore[valid-type]
    channel: ConfirmationChannel
    accepted: bool
    decided_at_ms: PositiveInt
    raw_payload: Optional[Dict[str, str]] = Field(
        default=None, description="Raw transcript or gesture metadata"
    )


class PromptDecisionResponse(BaseModel):
    order_id: Optional[str] = None
    status: OrderStatus
    message: str


# --- Order lifecycle --------------------------------------------------------------


class OrderRequest(BaseModel):
    intent_id: constr(strip_whitespace=True, min_length=8)  # type: ignore[valid-type]
    product_id: str
    variant_sku: str
    quantity: PositiveInt = Field(default=1, le=12)
    destination: Dict[str, str] = Field(
        description="Shipping destination info held on backend (e.g. address_id)"
    )


class OrderRecord(BaseModel):
    order_id: constr(strip_whitespace=True, min_length=8)  # type: ignore[valid-type]
    intent_id: str
    product_id: str
    variant_sku: str
    quantity: PositiveInt
    status: OrderStatus
    created_at_ms: PositiveInt
    updated_at_ms: PositiveInt
    provider: str
    provider_reference: Optional[str] = None
    error: Optional[str] = None


class OrderResponse(BaseModel):
    order_id: str
    status: OrderStatus
    estimated_arrival: Optional[str] = None
    provider: Optional[str] = None
    provider_reference: Optional[str] = None


class OrderStatusResponse(BaseModel):
    order: OrderRecord


# --- Bright Data Amazon scraper ---------------------------------------------------


class BrightDataDetectionPayload(BaseModel):
    """Single frame detection payload forwarded to Bright Data scraping."""

    box_2d: conlist(int, min_length=4, max_length=4)  # type: ignore[call-arg]
    mask: Optional[str] = Field(default=None, description="Optional segmentation mask as data URI")
    label: constr(strip_whitespace=True, min_length=2)
    percent_full: conint(ge=0, le=100)
    is_low: bool
    confidence: float = Field(ge=0.0, le=1.0)


class BrightDataScrapeRequest(BaseModel):
    """Keyword-based product discovery request for Bright Data."""

    input: conlist(
        BrightDataDetectionPayload,
        min_length=1,
        max_length=10,
    )  # type: ignore[call-arg]
    max_records_per_input: Optional[conint(ge=1, le=100)] = Field(
        default=None,
        description="Optional Bright Data record limit override",
    )


class BrightDataProduct(BaseModel):
    model_config = ConfigDict(extra="allow")

    asin: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
    price: Optional[str] = Field(default=None)
    image: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrightDataScrapeResponse(BaseModel):
    results: List[BrightDataProduct]
    raw_response: Optional[Dict[str, Any] | List[Any] | str] = Field(
        default=None,
        description="Raw Bright Data payload kept for debugging (dict, list, or str)",
    )
