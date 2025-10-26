"""Product catalog utilities for mapping detections to purchasable goods.

The goal is to keep configuration centralized and testable. In production this
would likely talk to a database or feature flag service; for hackathon velocity
we keep an in-memory catalog with clean APIs around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from app.models.schemas import FillLevel, Product, ProductVariant


@dataclass(frozen=True)
class CatalogEntry:
    product: Product
    variants_by_sku: Dict[str, ProductVariant]


class ProductCatalogService:
    """Thin catalog façade with sane defaults and DRY lookups."""

    def __init__(self, products: Iterable[Product]):
        mapped: Dict[str, CatalogEntry] = {}
        for product in products:
            variants = {product.default_variant.sku: product.default_variant}
            for variant in product.variants:
                variants[variant.sku] = variant

            mapped[product.object_class.lower()] = CatalogEntry(
                product=product, variants_by_sku=variants
            )
        self._catalog = mapped

    # ------------------------------ Query helpers ---------------------------------

    def list_products(self) -> Iterable[Product]:
        return (entry.product for entry in self._catalog.values())

    def get_by_object_class(self, object_class: str) -> Optional[Product]:
        entry = self._catalog.get(object_class.lower())
        return entry.product if entry else None

    def resolve_variant(self, object_class: str, variant_sku: Optional[str]) -> Optional[ProductVariant]:
        entry = self._catalog.get(object_class.lower())
        if not entry:
            return None

        if not variant_sku:
            return entry.product.default_variant

        return entry.variants_by_sku.get(variant_sku)

    def should_prompt(self, object_class: str, fill_level: FillLevel) -> bool:
        entry = self._catalog.get(object_class.lower())
        if not entry:
            return False

        threshold = entry.product.reorder_threshold
        levels = list(FillLevel)
        return levels.index(fill_level) >= levels.index(threshold)


# ----------------------------------------------------------------------------
# Factory setup with default catalog. This can be swapped for DI later.
# ----------------------------------------------------------------------------


def default_catalog() -> ProductCatalogService:
    baseline_products = [
        Product(
            id="hydration_001",
            object_class="water_bottle",
            default_variant=ProductVariant(
                sku="WATER-24PK",
                label="Spring Water 24-pack",
                size="24 x 16.9 oz",
                unit_price_usd=12.99,
            ),
            variants=[
                ProductVariant(
                    sku="WATER-12PK",
                    label="Spring Water 12-pack",
                    size="12 x 16.9 oz",
                    unit_price_usd=7.49,
                )
            ],
            reorder_threshold=FillLevel.NEARLY_EMPTY,
            metadata={"provider": "amazon"},
        ),
        Product(
            id="sunscreen_001",
            object_class="sunscreen",
            default_variant=ProductVariant(
                sku="SUN-50SPF",
                label="SPF 50 Sunscreen",
                size="6 oz",
                unit_price_usd=15.49,
            ),
            variants=[],
            reorder_threshold=FillLevel.NEARLY_EMPTY,
            metadata={"provider": "instacart"},
        ),
        Product(
            id="soap_refill_001",
            object_class="soap_dispenser",
            default_variant=ProductVariant(
                sku="SOAP-REFILL",
                label="Foaming Soap Refill",
                size="1 L",
                unit_price_usd=9.99,
            ),
            variants=[],
            reorder_threshold=FillLevel.EMPTY,
            metadata={"provider": "amazon"},
        ),
    ]

    return ProductCatalogService(baseline_products)
