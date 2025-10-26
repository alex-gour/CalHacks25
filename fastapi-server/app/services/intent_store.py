"""Stateful in-memory store for prompt intents and order tracking.

This keeps us honest about zero-repeat prompts per session and gives the
backend a single source of truth for outstanding intents.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from app.models.schemas import (
    ConfirmationChannel,
    DetectionEvent,
    DetectionIngestResponse,
    FillLevel,
    OrderRecord,
    OrderStatus,
    Product,
    ProductVariant,
    PromptDecisionRequest,
    PromptDecisionResponse,
    PromptIntent,
)


@dataclass
class IntentState:
    intent: PromptIntent
    product: Product
    variant: ProductVariant
    last_prompted_at_ms: int
    accepted: Optional[bool] = None
    decision_channel: Optional[ConfirmationChannel] = None
    order_id: Optional[str] = None
    order_status: OrderStatus = OrderStatus.PENDING
    order_error: Optional[str] = None


class PromptIntentStore:
    """Tracks prompts + throttles duplicates for each device/object pair."""

    def __init__(
        self,
        prompt_cooldown_ms: int = 5 * 60 * 1000,
        intent_ttl_ms: int = 15 * 60 * 1000,
    ) -> None:
        self._prompt_cooldown_ms = prompt_cooldown_ms
        self._intent_ttl_ms = intent_ttl_ms
        self._state: Dict[str, IntentState] = {}
        self._orders: Dict[str, OrderRecord] = {}
        self._lock = asyncio.Lock()

    # ------------------------ Detection ingestion ---------------------------------

    async def register_detection(
        self,
        detection: DetectionEvent,
        product: Product,
        variant: ProductVariant,
    ) -> DetectionIngestResponse:
        async with self._lock:
            key = self._device_object_key(detection)
            now_ms = self._now_ms()
            stale_keys = [
                k
                for k, state in self._state.items()
                if state.intent.expires_at_ms < now_ms
            ]
            for stale in stale_keys:
                self._state.pop(stale, None)

            existing_state = self._state.get(key)
            if existing_state:
                elapsed = now_ms - existing_state.last_prompted_at_ms
                if elapsed < self._prompt_cooldown_ms:
                    return DetectionIngestResponse(
                        should_prompt=False,
                        reason="cooldown_active",
                        next_prompt_allowed_at_ms=existing_state.last_prompted_at_ms
                        + self._prompt_cooldown_ms,
                        pending_intent_id=existing_state.intent.intent_id,
                    )

            if not self._should_prompt(product, detection.fill_level):
                return DetectionIngestResponse(
                    should_prompt=False,
                    reason="above_threshold",
                    next_prompt_allowed_at_ms=None,
                )

            intent_id = uuid.uuid4().hex[:12]
            expires_at_ms = now_ms + self._intent_ttl_ms
            intent = PromptIntent(
                intent_id=intent_id,
                event_id=detection.event_id,
                product_id=product.id,
                variant_sku=variant.sku,
                created_at_ms=now_ms,
                expires_at_ms=expires_at_ms,
            )
            state = IntentState(
                intent=intent,
                product=product,
                variant=variant,
                last_prompted_at_ms=now_ms,
            )
            self._state[key] = state
            return DetectionIngestResponse(
                should_prompt=True,
                reason=None,
                next_prompt_allowed_at_ms=now_ms + self._prompt_cooldown_ms,
                pending_intent_id=intent_id,
            )

    # ---------------------------- Intent lookups ----------------------------------

    async def get_intent(self, intent_id: str) -> Optional[IntentState]:
        async with self._lock:
            for state in self._state.values():
                if state.intent.intent_id == intent_id:
                    if state.intent.expires_at_ms < self._now_ms():
                        return None
                    return state
            return None

    # ----------------------- Prompt decision handling -----------------------------

    async def record_decision(
        self, request: PromptDecisionRequest
    ) -> PromptDecisionResponse:
        async with self._lock:
            state_entry = self._find_state_by_intent(request.intent_id)
            if not state_entry:
                return PromptDecisionResponse(
                    status=OrderStatus.FAILED,
                    message="Intent expired or unknown.",
                )

            state_key, state = state_entry
            state.accepted = request.accepted
            state.decision_channel = request.channel

            if not request.accepted:
                self._state[state_key] = state
                return PromptDecisionResponse(
                    status=OrderStatus.FAILED,
                    message="User declined reorder.",
                )

            order_id = uuid.uuid4().hex[:12]
            state.order_id = order_id
            state.order_status = OrderStatus.PENDING
            self._state[state_key] = state
            return PromptDecisionResponse(
                order_id=order_id,
                status=OrderStatus.PENDING,
                message="Order request queued.",
            )

    # ---------------------------- Order lifecycle ---------------------------------

    async def mark_order_submitted(
        self,
        intent_id: str,
        order: OrderRecord,
    ) -> None:
        async with self._lock:
            entry = self._find_state_by_intent(intent_id)
            if entry:
                state_key, state = entry
                state.order_id = order.order_id
                state.order_status = order.status
                state.order_error = order.error
                self._orders[order.order_id] = order
                self._state[state_key] = state

    async def get_order(self, order_id: str) -> Optional[OrderRecord]:
        async with self._lock:
            return self._orders.get(order_id)

    # ----------------------------- Internals --------------------------------------

    def _device_object_key(self, detection: DetectionEvent) -> str:
        return f"{detection.device_id}:{detection.object_class.lower()}"

    def _should_prompt(self, product: Product, fill_level: FillLevel) -> bool:
        levels = list(FillLevel)
        return levels.index(fill_level) >= levels.index(product.reorder_threshold)

    def _find_state_by_intent(self, intent_id: str) -> Optional[Tuple[str, IntentState]]:
        for key, state in self._state.items():
            if state.intent.intent_id == intent_id:
                return key, state
        return None

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)
