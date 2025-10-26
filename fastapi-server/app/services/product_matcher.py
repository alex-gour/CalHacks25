"""Product matching service for catalog-based product discovery."""

import json
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from pathlib import Path


class CatalogProduct(BaseModel):
    """Represents a product in our catalog."""
    id: str
    name: str
    category: str  # e.g., "water bottle", "shampoo", "toothpaste"
    keywords: List[str]  # Keywords for matching
    shopify_url: str
    description: Optional[str] = None
    attributes: Dict[str, Any] = {}  # e.g., {"color": "blue", "size": "1L"}


class ProductMatchResult(BaseModel):
    """Result of matching a detected product to catalog."""
    detected_label: str
    matched_product: Optional[CatalogProduct]
    confidence: float  # 0.0 to 1.0
    match_reason: str


class ProductMatcher:
    """Service for matching detected products to catalog."""

    def __init__(self, catalog_path: Optional[str] = None):
        if catalog_path is None:
            # Default catalog path
            catalog_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "product_catalog.json"
            )

        self.catalog_path = catalog_path
        self.catalog: List[CatalogProduct] = []
        self._load_catalog()

    def _load_catalog(self):
        """Load product catalog from JSON file."""
        catalog_file = Path(self.catalog_path)

        if not catalog_file.exists():
            # Create empty catalog if it doesn't exist
            catalog_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_catalog([])
            return

        try:
            with open(catalog_file, 'r') as f:
                data = json.load(f)
                self.catalog = [CatalogProduct(**item) for item in data]
        except Exception as e:
            print(f"Error loading catalog: {e}")
            self.catalog = []

    def _save_catalog(self, products: List[CatalogProduct]):
        """Save catalog to JSON file."""
        catalog_file = Path(self.catalog_path)
        catalog_file.parent.mkdir(parents=True, exist_ok=True)

        with open(catalog_file, 'w') as f:
            data = [p.dict() for p in products]
            json.dump(data, f, indent=2)

    def add_product(self, product: CatalogProduct) -> bool:
        """Add a product to the catalog."""
        # Check if product with same ID exists
        existing_ids = [p.id for p in self.catalog]
        if product.id in existing_ids:
            return False

        self.catalog.append(product)
        self._save_catalog(self.catalog)
        return True

    def update_product(self, product_id: str, product: CatalogProduct) -> bool:
        """Update an existing product in the catalog."""
        for i, p in enumerate(self.catalog):
            if p.id == product_id:
                self.catalog[i] = product
                self._save_catalog(self.catalog)
                return True
        return False

    def delete_product(self, product_id: str) -> bool:
        """Delete a product from the catalog."""
        original_len = len(self.catalog)
        self.catalog = [p for p in self.catalog if p.id != product_id]

        if len(self.catalog) < original_len:
            self._save_catalog(self.catalog)
            return True
        return False

    def get_all_products(self) -> List[CatalogProduct]:
        """Get all products in the catalog."""
        return self.catalog

    def get_product(self, product_id: str) -> Optional[CatalogProduct]:
        """Get a specific product by ID."""
        for p in self.catalog:
            if p.id == product_id:
                return p
        return None

    def match_product(self, detected_label: str) -> ProductMatchResult:
        """
        Match a detected product label to a catalog product.

        Args:
            detected_label: Label from Gemini (e.g., "water bottle, white, blue cap")

        Returns:
            ProductMatchResult with best match
        """
        if not self.catalog:
            return ProductMatchResult(
                detected_label=detected_label,
                matched_product=None,
                confidence=0.0,
                match_reason="Catalog is empty"
            )

        # Normalize detected label
        label_lower = detected_label.lower()
        label_words = set(label_lower.split(", "))

        best_match = None
        best_score = 0.0
        best_reason = "No match found"

        for product in self.catalog:
            score = 0.0
            matches = []

            # Check category match (high weight)
            if product.category.lower() in label_lower:
                score += 0.4
                matches.append(f"category '{product.category}'")

            # Check keyword matches
            keyword_matches = 0
            for keyword in product.keywords:
                if keyword.lower() in label_lower:
                    keyword_matches += 1
                    matches.append(f"keyword '{keyword}'")

            # Weight keyword matches
            if keyword_matches > 0:
                score += min(0.4, keyword_matches * 0.1)

            # Check attribute matches (e.g., color, material)
            for attr_key, attr_value in product.attributes.items():
                if isinstance(attr_value, str):
                    if attr_value.lower() in label_lower:
                        score += 0.05
                        matches.append(f"attribute {attr_key}='{attr_value}'")

            # Check if product name words are in detected label
            name_words = set(product.name.lower().split())
            common_words = label_words.intersection(name_words)
            if common_words:
                score += min(0.2, len(common_words) * 0.05)
                matches.append(f"name words: {', '.join(common_words)}")

            # Update best match if this is better
            if score > best_score:
                best_score = score
                best_match = product
                best_reason = "Matched on: " + "; ".join(matches) if matches else "Partial match"

        # Consider it a match if score is above threshold
        confidence = min(1.0, best_score)

        if confidence < 0.3:
            # Too low confidence, return no match
            return ProductMatchResult(
                detected_label=detected_label,
                matched_product=None,
                confidence=confidence,
                match_reason=f"Low confidence match ({confidence:.2f})"
            )

        return ProductMatchResult(
            detected_label=detected_label,
            matched_product=best_match,
            confidence=confidence,
            match_reason=best_reason
        )


# Singleton instance
_matcher: Optional[ProductMatcher] = None


def get_product_matcher() -> ProductMatcher:
    """Get or create the product matcher singleton."""
    global _matcher
    if _matcher is None:
        _matcher = ProductMatcher()
    return _matcher
