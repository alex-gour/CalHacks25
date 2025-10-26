from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    OrderRequest,
    OrderStatus,
    OrderStatusResponse,
    PromptDecisionRequest,
    PromptDecisionResponse,
)
from app.services import intent_store, submit_order, telemetry

router = APIRouter(prefix="/orders")


@router.post("/decisions", response_model=PromptDecisionResponse)
async def decide_prompt(request: PromptDecisionRequest):
    response = await intent_store.record_decision(request)
    if not response.order_id or response.status != OrderStatus.PENDING:
        telemetry.emit(
            "prompt_decision",
            intent_id=request.intent_id,
            channel=request.channel.value,
            accepted=str(request.accepted),
        )
        return response

    # Only reach here when accepted and order queued
    state = await intent_store.get_intent(request.intent_id)
    if not state:
        raise HTTPException(status_code=404, detail="intent_expired")

    order_request = OrderRequest(
        intent_id=request.intent_id,
        product_id=state.product.id,
        variant_sku=state.variant.sku,
        quantity=1,
        destination={"address_id": "default"},
    )
    order = await submit_order(order_request)
    telemetry.emit(
        "order_submitted",
        order_id=order.order_id,
        status=order.status.value,
        provider=order.provider,
    )
    if order.status == OrderStatus.FAILED:
        telemetry.emit(
            "order_failed",
            order_id=order.order_id,
            provider=order.provider,
        )
        return PromptDecisionResponse(
            order_id=order.order_id,
            status=order.status,
            message=order.error or "order_failed",
        )

    return PromptDecisionResponse(
        order_id=order.order_id,
        status=order.status,
        message="Order submitted successfully.",
    )


@router.get("/{order_id}", response_model=OrderStatusResponse)
async def get_order(order_id: str):
    order = await intent_store.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")

    return OrderStatusResponse(order=order)
