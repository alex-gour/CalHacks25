"""Snap and purchase endpoint - orchestrates image detection, search, and purchase."""

import base64
import binascii

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Request
from typing import List, Optional
from pydantic import BaseModel, ValidationError

from app.services.gemini_detection import get_gemini_service, DetectedProduct
from app.services.google_search import get_search_service, SearchResult
from app.services.shopify_purchase import get_purchase_service, PurchaseConfig
from app.services.product_matcher import get_product_matcher, ProductMatchResult, CatalogProduct


router = APIRouter(prefix="/snap-purchase")


class DetectionResponse(BaseModel):
    """Response from product detection."""
    detected_products: List[DetectedProduct]
    count: int


class SearchResponse(BaseModel):
    """Response from product search."""
    product_label: str
    search_results: List[SearchResult]
    best_url: Optional[str]


class PurchaseResponse(BaseModel):
    """Response from purchase attempt."""
    success: bool
    message: str
    product_url: str
    product_info: Optional[dict] = None
    selected_variant: Optional[dict] = None
    cart_url: Optional[str] = None


class SnapPurchaseResponse(BaseModel):
    """Complete response from snap and purchase flow."""
    detected_products: List[DetectedProduct]
    search_results: List[SearchResult] = []
    catalog_match: Optional[dict] = None  # When using database mode
    purchase_url: Optional[str]
    purchase_result: Optional[dict]


class SnapAndBuyPayload(BaseModel):
    """JSON payload variant for snap and buy flow."""
    image_surroundings: str
    user_prompt: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    chat_history: Optional[str] = None
    auto_purchase: bool = False
    quantity: str = "1"
    database: bool = False


@router.post("/detect", response_model=DetectionResponse)
async def detect_products_in_image(
    image: UploadFile = File(..., description="Image file to detect products in")
):
    """
    Step 1: Detect products in an uploaded image using Gemini.

    This endpoint accepts an image and returns all detected products with their
    bounding boxes, labels, and fill levels.
    """
    # Read image bytes
    image_bytes = await image.read()

    # Determine MIME type
    mime_type = image.content_type or 'image/png'

    # Detect products using Gemini
    gemini_service = get_gemini_service()
    try:
        products = await gemini_service.detect_products(image_bytes, mime_type)

        return DetectionResponse(
            detected_products=products,
            count=len(products)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product detection failed: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_for_product(
    product_label: str = Query(..., description="Product label from detection (e.g., 'shampoo bottle, white, pump')"),
    max_results: int = Query(5, ge=1, le=10, description="Maximum number of search results")
):
    """
    Step 2: Search for Shopify URLs based on a product label.

    This endpoint takes a product label (from detection) and searches Google
    for matching Shopify product URLs.
    """
    search_service = get_search_service()

    try:
        # Get search results
        results = await search_service.search_shopify_product(product_label, max_results)

        # Find best Shopify URL
        best_url = await search_service.find_best_shopify_url(product_label)

        return SearchResponse(
            product_label=product_label,
            search_results=results,
            best_url=best_url
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product search failed: {str(e)}")


@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_shopify_product(
    product_url: str = Query(..., description="Shopify product URL to purchase"),
    size: Optional[str] = Query(None, description="Specific size to purchase (optional)"),
    quantity: str = Query("1", description="Quantity to purchase")
):
    """
    Step 3: Purchase a product from a Shopify URL.

    This endpoint initiates an automated purchase of a Shopify product.
    It will open a browser window and fill in the checkout form.
    """
    purchase_service = get_purchase_service()

    try:
        # Create purchase config
        config = PurchaseConfig(
            product_url=product_url,
            size=size,
            quantity=quantity,
            **purchase_service.default_config
        )

        # Purchase product
        result = await purchase_service.purchase_product(product_url, config)

        return PurchaseResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            product_url=product_url,
            product_info=result.get("product"),
            selected_variant=result.get("selected_variant"),
            cart_url=result.get("cart_url")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Purchase failed: {str(e)}")


@router.post("/snap-and-buy", response_model=SnapPurchaseResponse)
async def snap_and_buy(request: Request):
    """
    Complete flow: Detect products in image, search for Shopify URLs, and optionally purchase.

    Supports both multipart/form-data uploads and JSON payloads containing
    a base64 encoded image (for clients that cannot send multipart requests).
    """

    # Step 0: Normalise request input (multipart vs JSON)
    image_bytes: Optional[bytes] = None
    mime_type: str = "image/png"
    auto_purchase = False
    quantity = "1"
    database = False

    content_type = request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        try:
            form = await request.form()
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse multipart form data: {exc}",
            )

        upload = form.get("image")
        if isinstance(upload, UploadFile):
            mime_type = upload.content_type or mime_type
            image_bytes = await upload.read()
        else:
            raise HTTPException(
                status_code=400,
                detail="Multipart request must include an 'image' file field",
            )

        auto_purchase = form.get("auto_purchase", "false") in {"true", "1", True}
        if form.get("quantity"):
            quantity = str(form.get("quantity"))
        database = form.get("database", "false") in {"true", "1", True}

    else:
        try:
            payload_dict = await request.json()
            payload = SnapAndBuyPayload(**payload_dict)
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON payload. {exc}",
            )

        if not payload.image_surroundings:
            raise HTTPException(
                status_code=400,
                detail="image_surroundings is required in JSON payload",
            )

        try:
            image_bytes = base64.b64decode(payload.image_surroundings)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 image data: {exc}",
            )

        auto_purchase = payload.auto_purchase
        quantity = payload.quantity
        database = payload.database

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="No image provided. Upload an image file or include image_surroundings in the JSON body.",
        )

    # Step 1: Detect products
    gemini_service = get_gemini_service()
    try:
        products = await gemini_service.detect_products(image_bytes, mime_type)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Product detection failed: {str(e)}"
        )

    if not products:
        return SnapPurchaseResponse(
            detected_products=[],
            search_results=[],
            purchase_url=None,
            purchase_result=None,
        )

    # Step 2: Find a low-stock product to search for
    target_product = next((product for product in products if product.is_low), None)
    if not target_product:
        target_product = products[0]

    # Step 2a: Either match against database or search Google
    search_results: List[SearchResult] = []
    catalog_match = None
    best_url = None

    if database:
        matcher = get_product_matcher()
        try:
            match_result = matcher.match_product(target_product.label)

            if match_result.matched_product:
                best_url = match_result.matched_product.shopify_url
                catalog_match = {
                    "detected_label": match_result.detected_label,
                    "matched_product": match_result.matched_product.dict(),
                    "confidence": match_result.confidence,
                    "match_reason": match_result.match_reason,
                }
            else:
                return SnapPurchaseResponse(
                    detected_products=products,
                    search_results=[],
                    catalog_match={
                        "detected_label": match_result.detected_label,
                        "matched_product": None,
                        "confidence": match_result.confidence,
                        "match_reason": match_result.match_reason,
                    },
                    purchase_url=None,
                    purchase_result={
                        "success": False,
                        "message": "No matching product found in catalog.",
                        "catalog_attempted": True,
                    },
                )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Catalog matching failed: {str(e)}"
            )
    else:
        search_service = get_search_service()
        try:
            search_results = await search_service.search_shopify_product(
                target_product.label, max_results=10
            )
            best_url = await search_service.find_best_shopify_url(target_product.label)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Product search failed: {str(e)}"
            )

        if not best_url or "/products/" not in best_url:
            return SnapPurchaseResponse(
                detected_products=products,
                search_results=search_results,
                catalog_match=None,
                purchase_url=best_url,
                purchase_result={
                    "success": False,
                    "message": "No valid product URL found.",
                    "search_attempted": True,
                }
                if best_url
                else {
                    "success": False,
                    "message": "No search results found for the product.",
                    "search_attempted": True,
                },
            )

    # Step 3: Optionally purchase
    purchase_result = None
    if auto_purchase and best_url:
        purchase_service = get_purchase_service()
        try:
            config = PurchaseConfig(
                product_url=best_url,
                quantity=quantity,
                **purchase_service.default_config,
            )
            purchase_result = await purchase_service.purchase_product(best_url, config)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Purchase failed: {str(e)}")

    return SnapPurchaseResponse(
        detected_products=products,
        search_results=search_results,
        catalog_match=catalog_match,
        purchase_url=best_url,
        purchase_result=purchase_result,
    )
