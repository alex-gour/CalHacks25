from fastapi import APIRouter

from app.services import telemetry

router = APIRouter()


@router.get("/health")
async def healthcheck():
    return {
        "status": "ok",
        "message": "Spectacles reorder assistant backend ready",
    }


@router.get("/telemetry")
async def telemetry_summary():
    return telemetry.summary()
