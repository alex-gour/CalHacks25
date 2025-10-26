from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DetectionEvent,
    DetectionIngestResponse,
    PromptIntent,
)
from app.services import catalog, intent_store, telemetry

router = APIRouter(prefix="/detections")


@router.post("", response_model=DetectionIngestResponse)
async def ingest_detection(event: DetectionEvent):
    product = catalog.get_by_object_class(event.object_class)
    if not product:
        telemetry.emit(
            "detection_unknown",
            device_id=event.device_id,
            object_class=event.object_class,
        )
        raise HTTPException(status_code=404, detail="object_class_not_supported")

    variant = catalog.resolve_variant(event.object_class, None)
    if not variant:
        raise HTTPException(status_code=500, detail="catalog_variant_missing")

    telemetry.emit(
        "detection",
        device_id=event.device_id,
        object_class=event.object_class,
        fill_level=event.fill_level.value,
        confidence=event.confidence.value,
    )
    response = await intent_store.register_detection(event, product, variant)
    return response


@router.get("/intents/{intent_id}", response_model=PromptIntent)
async def get_intent(intent_id: str):
    state = await intent_store.get_intent(intent_id)
    if not state:
        raise HTTPException(status_code=404, detail="intent_not_found")
    return state.intent
