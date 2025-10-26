"""Commerce provider abstraction for submitting orders to external services."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

import requests

from app.models.schemas import OrderRecord, OrderRequest, OrderStatus


@dataclass
class CommerceConfig:
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    provider: str = "mock"
    timeout_seconds: int = 10


class CommerceProvider:
    """Simple commerce API wrapper with optional mock mode."""

    def __init__(self, config: CommerceConfig) -> None:
        self._config = config

    async def submit_order(self, request: OrderRequest) -> OrderRecord:
        created_at = self._now_ms()

        if self._config.provider == "mock" or not self._config.base_url:
            return OrderRecord(
                order_id=uuid.uuid4().hex[:12],
                intent_id=request.intent_id,
                product_id=request.product_id,
                variant_sku=request.variant_sku,
                quantity=request.quantity,
                status=OrderStatus.CONFIRMED,
                created_at_ms=created_at,
                updated_at_ms=created_at,
                provider="mock",
                provider_reference="offline-sim",
            )

        payload = {
            "intent_id": request.intent_id,
            "product_id": request.product_id,
            "variant_sku": request.variant_sku,
            "quantity": request.quantity,
            "destination": request.destination,
        }

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self._config.base_url}/order",
                json=payload,
                headers=headers,
                timeout=self._config.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            provider_ref = body.get("order_reference")
            return OrderRecord(
                order_id=body.get("order_id", uuid.uuid4().hex[:12]),
                intent_id=request.intent_id,
                product_id=request.product_id,
                variant_sku=request.variant_sku,
                quantity=request.quantity,
                status=OrderStatus(body.get("status", OrderStatus.SUBMITTED.value)),
                created_at_ms=created_at,
                updated_at_ms=self._now_ms(),
                provider=self._config.provider,
                provider_reference=provider_ref,
            )
        except requests.RequestException as exc:
            return OrderRecord(
                order_id=uuid.uuid4().hex[:12],
                intent_id=request.intent_id,
                product_id=request.product_id,
                variant_sku=request.variant_sku,
                quantity=request.quantity,
                status=OrderStatus.FAILED,
                created_at_ms=created_at,
                updated_at_ms=self._now_ms(),
                provider=self._config.provider,
                error=str(exc),
            )

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)
