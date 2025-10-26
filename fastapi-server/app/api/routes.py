from fastapi import APIRouter

from app.api.endpoints import brightdata, detection, orders, products, system

router = APIRouter(prefix="/api")
router.include_router(system.router, tags=["system"])
router.include_router(products.router, tags=["products"])
router.include_router(detection.router, tags=["detection"])
router.include_router(orders.router, tags=["orders"])
router.include_router(brightdata.router, tags=["scrapers"])
