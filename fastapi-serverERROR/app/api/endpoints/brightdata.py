from fastapi import APIRouter, HTTPException

from app.models.schemas import BrightDataScrapeRequest, BrightDataScrapeResponse
from app.services import brightdata_scraper
from app.services.brightdata import BrightDataError

router = APIRouter(prefix="/scrapers/amazon")


@router.post("/discover", response_model=BrightDataScrapeResponse)
async def discover_products(payload: BrightDataScrapeRequest):
    if not brightdata_scraper:
        raise HTTPException(status_code=503, detail="brightdata_not_configured")

    try:
        return await brightdata_scraper.discover_products(payload)
    except BrightDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
