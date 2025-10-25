from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class ProductState(str, Enum):
    """State of a detected product"""
    FULL = "full"
    HALF = "half"
    LOW = "low"
    EMPTY = "empty"
    UNKNOWN = "unknown"


class OrderStatus(str, Enum):
    """Status of an order"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ProductCategory(str, Enum):
    """Product categories for classification"""
    BEVERAGES = "beverages"
    PERSONAL_CARE = "personal_care"
    HOUSEHOLD = "household"
    FOOD = "food"
    HEALTH = "health"
    OTHER = "other"


# ============================================================================
# PRODUCT MODELS
# ============================================================================

class Product(BaseModel):
    """Product information from database"""
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product display name")
    category: ProductCategory = Field(..., description="Product category")
    detection_class: str = Field(..., description="CV model class name (e.g., 'water_bottle')")
    asin: Optional[str] = Field(None, description="Amazon ASIN")
    upc: Optional[str] = Field(None, description="Universal Product Code")
    price: float = Field(..., description="Price in USD")
    image_url: Optional[str] = Field(None, description="Product image URL")
    description: Optional[str] = Field(None, description="Product description")
    vendor: str = Field(default="amazon", description="Vendor/retailer")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional product data")


class ProductList(BaseModel):
    """List of products"""
    products: List[Product]
    total: int


# ============================================================================
# DETECTION MODELS
# ============================================================================

class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x: float = Field(..., description="X coordinate (normalized 0-1)")
    y: float = Field(..., description="Y coordinate (normalized 0-1)")
    width: float = Field(..., description="Width (normalized 0-1)")
    height: float = Field(..., description="Height (normalized 0-1)")


class Detection(BaseModel):
    """Single object detection result"""
    detection_id: str = Field(..., description="Unique detection ID")
    class_name: str = Field(..., description="Detected object class")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bounding_box: BoundingBox = Field(..., description="Object bounding box")
    state: ProductState = Field(..., description="Detected product state")
    state_confidence: float = Field(..., ge=0.0, le=1.0, description="State classification confidence")
    matched_product: Optional[Product] = Field(None, description="Matched product from database")


class DetectionRequest(BaseModel):
    """Request for object detection"""
    image: str = Field(..., description="Base64 encoded image")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    return_matches: bool = Field(default=True, description="Whether to match products from database")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")


class DetectionResponse(BaseModel):
    """Response from object detection"""
    session_id: str = Field(..., description="Session identifier")
    detections: List[Detection] = Field(..., description="List of detected objects")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    image_dimensions: Dict[str, int] = Field(..., description="Original image dimensions")


# ============================================================================
# ORDER MODELS
# ============================================================================

class OrderItem(BaseModel):
    """Item in an order"""
    product_id: str
    product_name: str
    quantity: int = Field(default=1, ge=1)
    price: float
    total: float


class Order(BaseModel):
    """Order record"""
    order_id: str = Field(..., description="Unique order identifier")
    user_id: str = Field(..., description="User who placed the order")
    items: List[OrderItem] = Field(..., description="Ordered items")
    subtotal: float = Field(..., description="Subtotal before tax/shipping")
    tax: float = Field(default=0.0, description="Tax amount")
    shipping: float = Field(default=0.0, description="Shipping cost")
    total: float = Field(..., description="Total order amount")
    status: OrderStatus = Field(..., description="Current order status")
    vendor: str = Field(..., description="Vendor/retailer")
    vendor_order_id: Optional[str] = Field(None, description="Vendor's order ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    delivery_address: Optional[Dict[str, str]] = Field(None, description="Delivery address")
    tracking_number: Optional[str] = Field(None, description="Shipping tracking number")


class PlaceOrderRequest(BaseModel):
    """Request to place an order"""
    user_id: str = Field(..., description="User ID")
    product_id: str = Field(..., description="Product to order")
    quantity: int = Field(default=1, ge=1, description="Quantity to order")
    delivery_address: Optional[Dict[str, str]] = Field(None, description="Delivery address")
    confirm: bool = Field(default=False, description="Whether user has confirmed the order")


class PlaceOrderResponse(BaseModel):
    """Response from order placement"""
    success: bool
    order: Optional[Order] = None
    error: Optional[str] = None
    message: str


# ============================================================================
# USER MODELS
# ============================================================================

class UserPreferences(BaseModel):
    """User preferences and settings"""
    user_id: str
    auto_reorder_enabled: bool = Field(default=True, description="Enable automatic reorder prompts")
    preferred_vendor: str = Field(default="amazon", description="Preferred retailer")
    notification_threshold: ProductState = Field(default=ProductState.LOW, description="When to show reorder prompt")
    delivery_address: Optional[Dict[str, str]] = Field(None, description="Default delivery address")
    privacy_mode: bool = Field(default=True, description="Process CV on-device when possible")
    order_history_limit: int = Field(default=50, description="Number of orders to keep in history")
    blocked_products: List[str] = Field(default_factory=list, description="Product IDs to never auto-reorder")
    favorite_products: List[str] = Field(default_factory=list, description="Frequently ordered products")


class UserProfile(BaseModel):
    """User profile"""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    preferences: UserPreferences
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# GENERAL REQUEST/RESPONSE MODELS
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    details: Optional[str] = None
    session_id: Optional[str] = None


# ============================================================================
# LEGACY MODELS (for backward compatibility - can be removed later)
# ============================================================================

class LocationRequest(BaseModel):
    latitude: float
    longitude: float 

class HealthcareFacility(BaseModel):
    name: str
    type: str
    distance: float

class Shelter(BaseModel):
    name: str
    address: str
    phone: str
    distance: float
    latitude: float
    longitude: float

class OrchestrationRequest(BaseModel):
    user_prompt: str
    latitude: float
    longitude: float
    image_surroundings: str = None  # Base64 encoded image

class SummaryRequest(BaseModel):
    summaryPrompt: str