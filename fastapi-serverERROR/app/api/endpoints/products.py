from typing import Iterable

from fastapi import APIRouter, HTTPException

from app.models.schemas import Product
from app.services import catalog

router = APIRouter(prefix="/products")


def _serialize_products(products: Iterable[Product]):
    return [product for product in products]


@router.get("", response_model=list[Product])
async def list_products():
    return _serialize_products(catalog.list_products())


@router.get("/{object_class}", response_model=Product)
async def get_product(object_class: str):
    product = catalog.get_by_object_class(object_class)
    if not product:
        raise HTTPException(status_code=404, detail="product_not_found")
    return product
