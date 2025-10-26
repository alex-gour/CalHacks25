"""Service singletons for the reorder assistant backend.

This is intentionally tiny; in a larger system you would wire these up with a
proper dependency injection container.
"""

from app.models.schemas import OrderRequest
from app.services.brightdata import configure_brightdata_scraper
from app.services.commerce import CommerceConfig, CommerceProvider
from app.services.intent_store import PromptIntentStore
from app.services.product_catalog import ProductCatalogService, default_catalog
from app.services.telemetry import TelemetryClient

catalog: ProductCatalogService = default_catalog()
intent_store = PromptIntentStore()
telemetry = TelemetryClient()
commerce_provider = CommerceProvider(CommerceConfig(provider="mock"))
brightdata_scraper = configure_brightdata_scraper()


async def submit_order(request: OrderRequest):
    order = await commerce_provider.submit_order(request)
    await intent_store.mark_order_submitted(request.intent_id, order)
    return order
