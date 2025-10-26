"""Product catalog management endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List

from app.services.product_matcher import get_product_matcher, CatalogProduct, ProductMatchResult


router = APIRouter(prefix="/catalog")


@router.get("/products", response_model=List[CatalogProduct])
async def list_catalog_products():
    """
    Get all products in the catalog.

    Returns:
        List of all catalog products
    """
    matcher = get_product_matcher()
    return matcher.get_all_products()


@router.get("/products/{product_id}", response_model=CatalogProduct)
async def get_catalog_product(product_id: str):
    """
    Get a specific product from the catalog.

    Args:
        product_id: Product ID

    Returns:
        Catalog product details
    """
    matcher = get_product_matcher()
    product = matcher.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found in catalog")

    return product


@router.post("/products", response_model=CatalogProduct)
async def add_catalog_product(product: CatalogProduct):
    """
    Add a new product to the catalog.

    Args:
        product: Product details to add

    Returns:
        The added product
    """
    matcher = get_product_matcher()

    if not matcher.add_product(product):
        raise HTTPException(
            status_code=400,
            detail=f"Product with ID '{product.id}' already exists in catalog"
        )

    return product


@router.put("/products/{product_id}", response_model=CatalogProduct)
async def update_catalog_product(product_id: str, product: CatalogProduct):
    """
    Update an existing product in the catalog.

    Args:
        product_id: ID of product to update
        product: Updated product details

    Returns:
        The updated product
    """
    matcher = get_product_matcher()

    # Ensure the product ID in the path matches the body
    if product.id != product_id:
        raise HTTPException(
            status_code=400,
            detail=f"Product ID in path '{product_id}' does not match ID in body '{product.id}'"
        )

    if not matcher.update_product(product_id, product):
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found in catalog")

    return product


@router.delete("/products/{product_id}")
async def delete_catalog_product(product_id: str):
    """
    Delete a product from the catalog.

    Args:
        product_id: Product ID to delete

    Returns:
        Success message
    """
    matcher = get_product_matcher()

    if not matcher.delete_product(product_id):
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found in catalog")

    return {"message": f"Product '{product_id}' deleted successfully"}


@router.post("/match", response_model=ProductMatchResult)
async def match_product_label(label: str):
    """
    Test matching a product label against the catalog.

    This is useful for testing how well a detected label would match
    against the catalog without actually running the full snap-and-buy flow.

    Args:
        label: Product label to match (e.g., "water bottle, white, blue cap")

    Returns:
        Match result with best matching product and confidence
    """
    matcher = get_product_matcher()
    return matcher.match_product(label)
