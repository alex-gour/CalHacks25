"""
Order Service for Commerce API Integration

This service handles:
- Order placement with commerce providers (Amazon, Walmart, Instacart)
- Order tracking and status updates
- Order history management
- Tax and shipping calculations
"""

import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

from app.models.schemas import (
    Order,
    OrderItem,
    OrderStatus,
    PlaceOrderRequest,
    PlaceOrderResponse,
    Product,
)
from app.services.product_service import get_product_by_id

load_dotenv()

# ============================================================================
# COMMERCE API CONFIGURATION
# ============================================================================

# In production, these would be real API credentials
AMAZON_API_KEY = os.getenv("AMAZON_API_KEY", "demo_amazon_key")
WALMART_API_KEY = os.getenv("WALMART_API_KEY", "demo_walmart_key")
INSTACART_API_KEY = os.getenv("INSTACART_API_KEY", "demo_instacart_key")

# Tax rates by state (simplified)
STATE_TAX_RATES = {
    "CA": 0.0725,  # California
    "NY": 0.0800,  # New York
    "TX": 0.0625,  # Texas
    "FL": 0.0600,  # Florida
    "WA": 0.0650,  # Washington
    # Add more states as needed
}

DEFAULT_TAX_RATE = 0.07  # 7% default
SHIPPING_COST = 5.99  # Flat shipping rate
FREE_SHIPPING_THRESHOLD = 35.00  # Free shipping over this amount


# ============================================================================
# IN-MEMORY ORDER DATABASE
# ============================================================================

# In production, replace with real database
ORDER_DATABASE: Dict[str, Order] = {}


# ============================================================================
# ORDER PLACEMENT
# ============================================================================

async def place_order(request: PlaceOrderRequest) -> PlaceOrderResponse:
    """
    Place an order for a product
    
    Args:
        request: Order request with product, quantity, user info
        
    Returns:
        PlaceOrderResponse with order details or error
    """
    try:
        # Validate product exists
        product = get_product_by_id(request.product_id)
        if not product:
            return PlaceOrderResponse(
                success=False,
                error=f"Product {request.product_id} not found",
                message="Product not found in database",
            )
        
        # Check if user has confirmed (for safety)
        if not request.confirm:
            return PlaceOrderResponse(
                success=False,
                error="Order not confirmed",
                message="User must confirm order before placement",
            )
        
        # Create order item
        item_price = product.price
        item_total = item_price * request.quantity
        
        order_item = OrderItem(
            product_id=product.product_id,
            product_name=product.name,
            quantity=request.quantity,
            price=item_price,
            total=item_total,
        )
        
        # Calculate subtotal
        subtotal = item_total
        
        # Calculate tax
        state = request.delivery_address.get("state", "CA") if request.delivery_address else "CA"
        tax_rate = STATE_TAX_RATES.get(state, DEFAULT_TAX_RATE)
        tax = round(subtotal * tax_rate, 2)
        
        # Calculate shipping
        shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
        
        # Calculate total
        total = subtotal + tax + shipping
        
        # Create order
        order_id = str(uuid.uuid4())
        order = Order(
            order_id=order_id,
            user_id=request.user_id,
            items=[order_item],
            subtotal=subtotal,
            tax=tax,
            shipping=shipping,
            total=total,
            status=OrderStatus.PENDING,
            vendor=product.vendor,
            delivery_address=request.delivery_address,
        )
        
        # Place order with vendor
        vendor_result = await place_order_with_vendor(order, product)
        
        if vendor_result["success"]:
            order.vendor_order_id = vendor_result.get("vendor_order_id")
            order.status = OrderStatus.CONFIRMED
            order.updated_at = datetime.utcnow()
            
            # Save order
            ORDER_DATABASE[order_id] = order
            
            return PlaceOrderResponse(
                success=True,
                order=order,
                message=f"Order placed successfully with {product.vendor}!",
            )
        else:
            return PlaceOrderResponse(
                success=False,
                error=vendor_result.get("error", "Unknown vendor error"),
                message="Failed to place order with vendor",
            )
            
    except Exception as e:
        return PlaceOrderResponse(
            success=False,
            error=str(e),
            message="Internal error while placing order",
        )


async def place_order_with_vendor(order: Order, product: Product) -> Dict:
    """
    Place order with specific vendor API
    
    Args:
        order: Order to place
        product: Product being ordered
        
    Returns:
        Dict with success status and vendor_order_id
    """
    vendor = product.vendor.lower()
    
    if vendor == "amazon":
        return await place_amazon_order(order, product)
    elif vendor == "walmart":
        return await place_walmart_order(order, product)
    elif vendor == "instacart":
        return await place_instacart_order(order, product)
    else:
        return {"success": False, "error": f"Unsupported vendor: {vendor}"}


async def place_amazon_order(order: Order, product: Product) -> Dict:
    """
    Place order with Amazon API
    
    In production, this would use Amazon's Product Advertising API
    or Amazon SP-API
    
    For demo purposes, this simulates the API call
    """
    # Simulate API call
    print(f"[DEMO] Placing Amazon order for ASIN: {product.asin}")
    
    # In production, make actual API call:
    # response = requests.post(
    #     "https://api.amazon.com/orders",
    #     headers={"Authorization": f"Bearer {AMAZON_API_KEY}"},
    #     json={
    #         "asin": product.asin,
    #         "quantity": order.items[0].quantity,
    #         "address": order.delivery_address,
    #     }
    # )
    
    # Simulate success
    vendor_order_id = f"AMZ-{uuid.uuid4().hex[:12].upper()}"
    
    return {
        "success": True,
        "vendor_order_id": vendor_order_id,
        "estimated_delivery": "3-5 business days",
    }


async def place_walmart_order(order: Order, product: Product) -> Dict:
    """Place order with Walmart API"""
    print(f"[DEMO] Placing Walmart order for UPC: {product.upc}")
    
    vendor_order_id = f"WM-{uuid.uuid4().hex[:12].upper()}"
    
    return {
        "success": True,
        "vendor_order_id": vendor_order_id,
        "estimated_delivery": "2-4 business days",
    }


async def place_instacart_order(order: Order, product: Product) -> Dict:
    """Place order with Instacart API"""
    print(f"[DEMO] Placing Instacart order for: {product.name}")
    
    vendor_order_id = f"IC-{uuid.uuid4().hex[:12].upper()}"
    
    return {
        "success": True,
        "vendor_order_id": vendor_order_id,
        "estimated_delivery": "same day (2-4 hours)",
    }


# ============================================================================
# ORDER RETRIEVAL
# ============================================================================

def get_order_by_id(order_id: str) -> Optional[Order]:
    """Get order by ID"""
    return ORDER_DATABASE.get(order_id)


def get_user_orders(
    user_id: str,
    status: Optional[OrderStatus] = None,
    limit: int = 50,
) -> List[Order]:
    """
    Get orders for a specific user
    
    Args:
        user_id: User ID
        status: Optional status filter
        limit: Maximum number of orders to return
        
    Returns:
        List of orders
    """
    user_orders = [
        order for order in ORDER_DATABASE.values()
        if order.user_id == user_id
    ]
    
    if status:
        user_orders = [o for o in user_orders if o.status == status]
    
    # Sort by created_at descending (newest first)
    user_orders.sort(key=lambda o: o.created_at, reverse=True)
    
    return user_orders[:limit]


def get_order_history(user_id: str, limit: int = 10) -> List[Order]:
    """
    Get recent order history for user
    
    Args:
        user_id: User ID
        limit: Number of recent orders
        
    Returns:
        List of recent orders
    """
    return get_user_orders(user_id, limit=limit)


# ============================================================================
# ORDER STATUS UPDATES
# ============================================================================

def update_order_status(order_id: str, new_status: OrderStatus) -> Optional[Order]:
    """
    Update order status
    
    Args:
        order_id: Order ID
        new_status: New status
        
    Returns:
        Updated order or None
    """
    order = ORDER_DATABASE.get(order_id)
    if not order:
        return None
    
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    ORDER_DATABASE[order_id] = order
    return order


def add_tracking_number(order_id: str, tracking_number: str) -> Optional[Order]:
    """
    Add tracking number to order
    
    Args:
        order_id: Order ID
        tracking_number: Shipping tracking number
        
    Returns:
        Updated order or None
    """
    order = ORDER_DATABASE.get(order_id)
    if not order:
        return None
    
    order.tracking_number = tracking_number
    order.status = OrderStatus.SHIPPED
    order.updated_at = datetime.utcnow()
    
    ORDER_DATABASE[order_id] = order
    return order


async def track_order(order_id: str) -> Optional[Dict]:
    """
    Get tracking information for an order
    
    Args:
        order_id: Order ID
        
    Returns:
        Tracking info dict or None
    """
    order = ORDER_DATABASE.get(order_id)
    if not order:
        return None
    
    return {
        "order_id": order.order_id,
        "status": order.status,
        "vendor": order.vendor,
        "vendor_order_id": order.vendor_order_id,
        "tracking_number": order.tracking_number,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "estimated_delivery": "Check vendor website for details",
    }


# ============================================================================
# ORDER CANCELLATION
# ============================================================================

async def cancel_order(order_id: str, user_id: str, reason: str = "") -> Dict:
    """
    Cancel an order
    
    Args:
        order_id: Order ID
        user_id: User ID (for authorization)
        reason: Cancellation reason
        
    Returns:
        Dict with success status and message
    """
    order = ORDER_DATABASE.get(order_id)
    
    if not order:
        return {"success": False, "error": "Order not found"}
    
    if order.user_id != user_id:
        return {"success": False, "error": "Unauthorized"}
    
    if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
        return {"success": False, "error": "Cannot cancel shipped/delivered order"}
    
    # Cancel with vendor (in production)
    print(f"[DEMO] Cancelling order {order_id} with {order.vendor}")
    
    # Update status
    order.status = OrderStatus.CANCELLED
    order.updated_at = datetime.utcnow()
    ORDER_DATABASE[order_id] = order
    
    return {
        "success": True,
        "message": f"Order {order_id} cancelled successfully",
        "refund_amount": order.total,
    }


# ============================================================================
# ORDER ANALYTICS
# ============================================================================

def get_user_spending_summary(user_id: str) -> Dict:
    """
    Get spending summary for a user
    
    Args:
        user_id: User ID
        
    Returns:
        Dict with spending statistics
    """
    user_orders = get_user_orders(user_id)
    
    total_spent = sum(o.total for o in user_orders if o.status != OrderStatus.CANCELLED)
    total_orders = len([o for o in user_orders if o.status != OrderStatus.CANCELLED])
    
    return {
        "user_id": user_id,
        "total_orders": total_orders,
        "total_spent": round(total_spent, 2),
        "average_order_value": round(total_spent / total_orders, 2) if total_orders > 0 else 0.0,
        "orders_by_status": {
            status.value: len([o for o in user_orders if o.status == status])
            for status in OrderStatus
        },
    }


def get_frequently_ordered_products(user_id: str, limit: int = 5) -> List[Dict]:
    """
    Get most frequently ordered products for user
    
    Args:
        user_id: User ID
        limit: Number of products to return
        
    Returns:
        List of products with order counts
    """
    user_orders = get_user_orders(user_id)
    
    product_counts = {}
    for order in user_orders:
        if order.status == OrderStatus.CANCELLED:
            continue
        for item in order.items:
            if item.product_id not in product_counts:
                product_counts[item.product_id] = {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "order_count": 0,
                    "total_quantity": 0,
                }
            product_counts[item.product_id]["order_count"] += 1
            product_counts[item.product_id]["total_quantity"] += item.quantity
    
    # Sort by order count
    sorted_products = sorted(
        product_counts.values(),
        key=lambda x: x["order_count"],
        reverse=True
    )
    
    return sorted_products[:limit]

