"""
API Routes for Auto-Reorder System

This module provides REST API endpoints for:
- Object detection and product state analysis
- Product catalog management
- Order placement and tracking
- User profile and preferences
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.schemas import (
    # Detection models
    DetectionRequest,
    DetectionResponse,
    Detection,
    # Product models
    Product,
    ProductList,
    ProductCategory,
    # Order models
    PlaceOrderRequest,
    PlaceOrderResponse,
    Order,
    OrderStatus,
    # User models
    UserProfile,
    UserPreferences,
    ProductState,
    # General models
    HealthCheckResponse,
    ErrorResponse,
)

from app.services.vision_ai import (
    detect_objects_from_image,
    should_prompt_reorder,
    analyze_product_state,
)
from app.services.product_service import (
    get_product_by_id,
    get_all_products,
    search_products,
    get_product_by_detection_class,
    get_products_by_detection_class,
    get_recommended_products,
    get_product_alternatives,
)
from app.services.order_service import (
    place_order,
    get_order_by_id,
    get_user_orders,
    get_order_history,
    track_order,
    cancel_order,
    get_user_spending_summary,
    get_frequently_ordered_products,
)
from app.services.user_service import (
    create_user,
    get_user,
    get_or_create_user,
    get_user_preferences,
    update_user_preferences,
    set_auto_reorder,
    set_notification_threshold,
    set_preferred_vendor,
    update_delivery_address,
    get_delivery_address,
    block_product,
    unblock_product,
    is_product_blocked,
    add_favorite_product,
    remove_favorite_product,
    get_favorite_products,
    update_user_profile,
)

router = APIRouter(prefix="/api", tags=["api"])


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/", response_model=HealthCheckResponse)
async def root():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Detailed health check"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
    )


# ============================================================================
# OBJECT DETECTION ENDPOINTS
# ============================================================================

@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(request: DetectionRequest):
    """
    Detect objects and their states from an image
    
    This endpoint:
    1. Analyzes image for household products
    2. Determines product state (full/empty/low)
    3. Matches detected objects to product database
    4. Returns list of detections with confidence scores
    
    Example:
        POST /api/detect
        {
            "image": "base64_encoded_image_here",
            "user_id": "user_123",
            "confidence_threshold": 0.7
        }
    """
    try:
        # Perform detection
        response = await detect_objects_from_image(
            request.image,
            confidence_threshold=request.confidence_threshold,
        )
        
        # Match products if requested
        if request.return_matches:
            for detection in response.detections:
                product = get_product_by_detection_class(detection.class_name)
                if product:
                    detection.matched_product = product
        
        # Check if any products should trigger reorder
        if request.user_id:
            user = get_or_create_user(request.user_id)
            reorder_candidates = await should_prompt_reorder(
                response.detections,
                user.preferences.notification_threshold,
            )
            
            # Filter out blocked products
            reorder_candidates = [
                d for d in reorder_candidates
                if d.matched_product and not is_product_blocked(
                    request.user_id,
                    d.matched_product.product_id
                )
            ]
            
            # Add reorder flag to response (custom field)
            response_dict = response.model_dump()
            response_dict["reorder_candidates"] = len(reorder_candidates)
            return JSONResponse(content=response_dict)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/analyze-state")
async def analyze_state(
    image: str,
    product_class: str,
):
    """
    Analyze the state of a specific product in an image
    
    Args:
        image: Base64 encoded image
        product_class: Product class name (e.g., "water_bottle")
        
    Returns:
        State and confidence score
    """
    try:
        state, confidence = await analyze_product_state(image, product_class)
        
        return {
            "product_class": product_class,
            "state": state,
            "confidence": confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PRODUCT ENDPOINTS
# ============================================================================

@router.get("/products", response_model=ProductList)
async def list_products(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[ProductCategory] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
):
    """
    List and search products
    
    Supports filtering by:
    - Text search (name, description)
    - Category
    - Price range
    """
    try:
        if query or category or min_price or max_price:
            return search_products(
                query=query,
                category=category,
                min_price=min_price,
                max_price=max_price,
            )
        else:
            return get_all_products()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get product by ID"""
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products/class/{detection_class}")
async def get_products_by_class(detection_class: str):
    """
    Get products matching a detection class
    
    Args:
        detection_class: CV model class name (e.g., "water_bottle")
        
    Returns:
        List of matching products
    """
    products = get_products_by_detection_class(detection_class)
    return {"detection_class": detection_class, "products": products}


@router.get("/products/{product_id}/alternatives")
async def get_alternatives(product_id: str, limit: int = Query(3, ge=1, le=10)):
    """Get alternative products (same category, similar price)"""
    alternatives = get_product_alternatives(product_id, limit=limit)
    return {"product_id": product_id, "alternatives": alternatives}


@router.get("/products/recommendations/{user_id}")
async def get_recommendations(
    user_id: str,
    category: Optional[ProductCategory] = None,
    limit: int = Query(5, ge=1, le=20),
):
    """Get recommended products for user"""
    recommendations = get_recommended_products(user_id, category=category, limit=limit)
    return {"user_id": user_id, "recommendations": recommendations}


# ============================================================================
# ORDER ENDPOINTS
# ============================================================================

@router.post("/orders", response_model=PlaceOrderResponse)
async def create_order(request: PlaceOrderRequest):
    """
    Place a new order
    
    Example:
        POST /api/orders
        {
            "user_id": "user_123",
            "product_id": "prod_water_001",
            "quantity": 1,
            "confirm": true,
            "delivery_address": {
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94102"
            }
        }
    """
    try:
        # Get user's default address if not provided
        if not request.delivery_address and request.user_id:
            default_address = get_delivery_address(request.user_id)
            if default_address:
                request.delivery_address = default_address
        
        result = await place_order(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get order by ID"""
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/orders/user/{user_id}")
async def get_orders(
    user_id: str,
    status: Optional[OrderStatus] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """Get orders for a user"""
    orders = get_user_orders(user_id, status=status, limit=limit)
    return {"user_id": user_id, "orders": orders, "total": len(orders)}


@router.get("/orders/{order_id}/track")
async def track_order_status(order_id: str):
    """Get tracking information for an order"""
    tracking = await track_order(order_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Order not found")
    return tracking


@router.post("/orders/{order_id}/cancel")
async def cancel_order_endpoint(
    order_id: str,
    user_id: str,
    reason: Optional[str] = None,
):
    """Cancel an order"""
    result = await cancel_order(order_id, user_id, reason or "")
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    
    return result


@router.get("/orders/user/{user_id}/history")
async def order_history(user_id: str, limit: int = Query(10, ge=1, le=50)):
    """Get recent order history"""
    history = get_order_history(user_id, limit=limit)
    return {"user_id": user_id, "history": history}


@router.get("/orders/user/{user_id}/summary")
async def spending_summary(user_id: str):
    """Get spending summary for user"""
    summary = get_user_spending_summary(user_id)
    return summary


@router.get("/orders/user/{user_id}/frequent")
async def frequent_products(user_id: str, limit: int = Query(5, ge=1, le=20)):
    """Get frequently ordered products"""
    products = get_frequently_ordered_products(user_id, limit=limit)
    return {"user_id": user_id, "frequent_products": products}


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@router.post("/users", response_model=UserProfile)
async def create_user_endpoint(
    user_id: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
):
    """Create a new user"""
    try:
        user = create_user(user_id, email=email, name=name)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_endpoint(user_id: str):
    """Get user profile"""
    user = get_user(user_id)
    if not user:
        # Auto-create user if not exists
        user = create_user(user_id)
    return user


@router.put("/users/{user_id}")
async def update_user_endpoint(
    user_id: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
):
    """Update user profile"""
    user = update_user_profile(user_id, email=email, name=name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{user_id}/preferences", response_model=UserPreferences)
async def get_preferences(user_id: str):
    """Get user preferences"""
    prefs = get_user_preferences(user_id)
    if not prefs:
        raise HTTPException(status_code=404, detail="User not found")
    return prefs


@router.put("/users/{user_id}/preferences")
async def update_preferences(user_id: str, updates: Dict[str, Any]):
    """Update user preferences"""
    prefs = update_user_preferences(user_id, updates)
    if not prefs:
        raise HTTPException(status_code=404, detail="User not found")
    return prefs


@router.post("/users/{user_id}/preferences/auto-reorder")
async def toggle_auto_reorder(user_id: str, enabled: bool):
    """Enable/disable auto-reorder"""
    success = set_auto_reorder(user_id, enabled)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "auto_reorder_enabled": enabled}


@router.post("/users/{user_id}/preferences/threshold")
async def set_threshold(user_id: str, threshold: ProductState):
    """Set notification threshold"""
    success = set_notification_threshold(user_id, threshold)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "threshold": threshold}


@router.post("/users/{user_id}/preferences/vendor")
async def set_vendor(user_id: str, vendor: str):
    """Set preferred vendor"""
    success = set_preferred_vendor(user_id, vendor)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "preferred_vendor": vendor}


@router.post("/users/{user_id}/address")
async def set_address(user_id: str, address: Dict[str, str]):
    """Update delivery address"""
    success = update_delivery_address(user_id, address)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "address": address}


@router.get("/users/{user_id}/address")
async def get_address(user_id: str):
    """Get delivery address"""
    address = get_delivery_address(user_id)
    return {"user_id": user_id, "address": address}


@router.post("/users/{user_id}/blocked/{product_id}")
async def block_product_endpoint(user_id: str, product_id: str):
    """Block a product"""
    success = block_product(user_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "blocked_product": product_id}


@router.delete("/users/{user_id}/blocked/{product_id}")
async def unblock_product_endpoint(user_id: str, product_id: str):
    """Unblock a product"""
    success = unblock_product(user_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "unblocked_product": product_id}


@router.post("/users/{user_id}/favorites/{product_id}")
async def add_favorite_endpoint(user_id: str, product_id: str):
    """Add product to favorites"""
    success = add_favorite_product(user_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "favorited_product": product_id}


@router.delete("/users/{user_id}/favorites/{product_id}")
async def remove_favorite_endpoint(user_id: str, product_id: str):
    """Remove product from favorites"""
    success = remove_favorite_product(user_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "unfavorited_product": product_id}


@router.get("/users/{user_id}/favorites")
async def get_favorites(user_id: str):
    """Get favorite products"""
    favorites = get_favorite_products(user_id)
    return {"user_id": user_id, "favorites": favorites}


# ============================================================================
# LEGACY ENDPOINTS (kept for backward compatibility)
# ============================================================================

# You can keep the old endpoints here if needed for backward compatibility
# or remove them if you're doing a clean refactor
