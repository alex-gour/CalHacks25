"""
Product Service for Product Database Management

This service handles:
- Product database (in-memory for now, can be replaced with real DB)
- Product matching from detection classes
- Product search and filtering
- Product CRUD operations
"""

from typing import List, Optional, Dict
from app.models.schemas import Product, ProductCategory, ProductList
from app.utils.ar_optimization import optimize_product_description


# ============================================================================
# IN-MEMORY PRODUCT DATABASE
# ============================================================================

# This is a simple in-memory database for demo purposes
# In production, replace with PostgreSQL, MongoDB, or similar
PRODUCT_DATABASE: Dict[str, Product] = {
    "prod_water_001": Product(
        product_id="prod_water_001",
        name="Spring Water 24-Pack (16.9 oz bottles)",
        category=ProductCategory.BEVERAGES,
        detection_class="water_bottle",
        asin="B07HNBV23M",
        upc="012000638602",
        price=12.99,
        image_url="https://example.com/images/water_24pack.jpg",
        description="Pure spring water, 24 bottles per pack",
        vendor="amazon",
        metadata={"pack_size": 24, "bottle_size_oz": 16.9},
    ),
    "prod_sunscreen_001": Product(
        product_id="prod_sunscreen_001",
        name="Coppertone Sport SPF 50 Sunscreen Lotion",
        category=ProductCategory.PERSONAL_CARE,
        detection_class="sunscreen",
        asin="B004D2C5GQ",
        upc="041100582805",
        price=15.49,
        image_url="https://example.com/images/coppertone_spf50.jpg",
        description="Water-resistant sunscreen, SPF 50, 8 fl oz",
        vendor="amazon",
        metadata={"spf": 50, "size_oz": 8, "water_resistant": True},
    ),
    "prod_detergent_001": Product(
        product_id="prod_detergent_001",
        name="Tide Liquid Laundry Detergent, Original Scent",
        category=ProductCategory.HOUSEHOLD,
        detection_class="laundry_detergent",
        asin="B00JSZ0E5C",
        upc="037000740759",
        price=18.99,
        image_url="https://example.com/images/tide_original.jpg",
        description="HE compatible, 64 loads, 92 fl oz",
        vendor="amazon",
        metadata={"loads": 64, "size_oz": 92, "scent": "original"},
    ),
    "prod_shampoo_001": Product(
        product_id="prod_shampoo_001",
        name="Pantene Pro-V Daily Moisture Renewal Shampoo",
        category=ProductCategory.PERSONAL_CARE,
        detection_class="shampoo",
        asin="B00CKCNV9W",
        upc="080878042418",
        price=7.99,
        image_url="https://example.com/images/pantene_shampoo.jpg",
        description="Hydrating shampoo for dry hair, 12.6 oz",
        vendor="amazon",
        metadata={"size_oz": 12.6, "hair_type": "dry"},
    ),
    "prod_soap_001": Product(
        product_id="prod_soap_001",
        name="Dove Beauty Bar Gentle Skin Cleanser",
        category=ProductCategory.PERSONAL_CARE,
        detection_class="soap",
        asin="B00L6F5D8O",
        upc="011111670891",
        price=9.49,
        image_url="https://example.com/images/dove_beauty_bar.jpg",
        description="Moisturizing beauty bar, 4 oz bars, 4-pack",
        vendor="amazon",
        metadata={"pack_size": 4, "bar_size_oz": 4},
    ),
    "prod_toothpaste_001": Product(
        product_id="prod_toothpaste_001",
        name="Colgate Total Whitening Toothpaste",
        category=ProductCategory.PERSONAL_CARE,
        detection_class="toothpaste",
        asin="B00N92Y5YG",
        upc="035000762351",
        price=5.99,
        image_url="https://example.com/images/colgate_whitening.jpg",
        description="Whitening toothpaste with fluoride, 4.8 oz",
        vendor="amazon",
        metadata={"size_oz": 4.8, "whitening": True, "fluoride": True},
    ),
    "prod_deodorant_001": Product(
        product_id="prod_deodorant_001",
        name="Degree Men Cool Rush Antiperspirant Deodorant",
        category=ProductCategory.PERSONAL_CARE,
        detection_class="deodorant",
        asin="B00EZXF8GU",
        upc="079400527387",
        price=6.49,
        image_url="https://example.com/images/degree_cool_rush.jpg",
        description="48-hour protection, 2.7 oz",
        vendor="amazon",
        metadata={"size_oz": 2.7, "protection_hours": 48, "gender": "men"},
    ),
    "prod_dish_soap_001": Product(
        product_id="prod_dish_soap_001",
        name="Dawn Ultra Dishwashing Liquid, Original Scent",
        category=ProductCategory.HOUSEHOLD,
        detection_class="dish_soap",
        asin="B00CQOK8M8",
        upc="037000302902",
        price=4.99,
        image_url="https://example.com/images/dawn_ultra.jpg",
        description="Cuts grease, 21.6 oz",
        vendor="amazon",
        metadata={"size_oz": 21.6, "scent": "original"},
    ),
}


# ============================================================================
# PRODUCT RETRIEVAL FUNCTIONS
# ============================================================================

def get_product_by_id(product_id: str, optimize_for_ar: bool = True) -> Optional[Product]:
    """
    Get product by ID
    
    Args:
        product_id: Product ID
        optimize_for_ar: Whether to optimize description for AR display (150 chars)
        
    Returns:
        Product with optimized description if requested
    """
    product = PRODUCT_DATABASE.get(product_id)
    if product and optimize_for_ar and product.description:
        product = product.model_copy()
        product.description = optimize_product_description(product.description)
    return product


def get_all_products() -> ProductList:
    """Get all products"""
    products = list(PRODUCT_DATABASE.values())
    return ProductList(products=products, total=len(products))


def search_products(
    query: Optional[str] = None,
    category: Optional[ProductCategory] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> ProductList:
    """
    Search products with filters
    
    Args:
        query: Text search in name/description
        category: Filter by category
        min_price: Minimum price filter
        max_price: Maximum price filter
        
    Returns:
        ProductList with matching products
    """
    products = list(PRODUCT_DATABASE.values())
    
    # Apply filters
    if query:
        query_lower = query.lower()
        products = [
            p for p in products
            if query_lower in p.name.lower() or query_lower in (p.description or "").lower()
        ]
    
    if category:
        products = [p for p in products if p.category == category]
    
    if min_price is not None:
        products = [p for p in products if p.price >= min_price]
    
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]
    
    return ProductList(products=products, total=len(products))


def get_product_by_detection_class(detection_class: str) -> Optional[Product]:
    """
    Get the best matching product for a detection class
    
    Args:
        detection_class: Class name from CV model (e.g., "water_bottle")
        
    Returns:
        Matching Product or None
    """
    # Simple matching: return first product with matching detection_class
    # In production, this could use more sophisticated matching logic
    for product in PRODUCT_DATABASE.values():
        if product.detection_class == detection_class:
            return product
    
    return None


def get_products_by_detection_class(detection_class: str) -> List[Product]:
    """
    Get all products matching a detection class
    
    Args:
        detection_class: Class name from CV model
        
    Returns:
        List of matching products
    """
    return [
        product
        for product in PRODUCT_DATABASE.values()
        if product.detection_class == detection_class
    ]


# ============================================================================
# PRODUCT CRUD OPERATIONS
# ============================================================================

def add_product(product: Product) -> Product:
    """
    Add a new product to the database
    
    Args:
        product: Product to add
        
    Returns:
        Added product
    """
    if product.product_id in PRODUCT_DATABASE:
        raise ValueError(f"Product with ID {product.product_id} already exists")
    
    PRODUCT_DATABASE[product.product_id] = product
    return product


def update_product(product_id: str, updates: Dict) -> Optional[Product]:
    """
    Update an existing product
    
    Args:
        product_id: ID of product to update
        updates: Dictionary of fields to update
        
    Returns:
        Updated product or None if not found
    """
    if product_id not in PRODUCT_DATABASE:
        return None
    
    product = PRODUCT_DATABASE[product_id]
    
    # Update fields
    for key, value in updates.items():
        if hasattr(product, key):
            setattr(product, key, value)
    
    PRODUCT_DATABASE[product_id] = product
    return product


def delete_product(product_id: str) -> bool:
    """
    Delete a product from the database
    
    Args:
        product_id: ID of product to delete
        
    Returns:
        True if deleted, False if not found
    """
    if product_id in PRODUCT_DATABASE:
        del PRODUCT_DATABASE[product_id]
        return True
    return False


# ============================================================================
# PRODUCT RECOMMENDATION
# ============================================================================

def get_recommended_products(
    user_id: str,
    category: Optional[ProductCategory] = None,
    limit: int = 5,
) -> List[Product]:
    """
    Get recommended products for a user
    
    In production, this would use:
    - User purchase history
    - Collaborative filtering
    - Product popularity
    - Seasonal trends
    
    For now, returns random popular products
    
    Args:
        user_id: User ID for personalization
        category: Optional category filter
        limit: Maximum number of recommendations
        
    Returns:
        List of recommended products
    """
    products = list(PRODUCT_DATABASE.values())
    
    if category:
        products = [p for p in products if p.category == category]
    
    # Sort by price (simple heuristic for "popular")
    products.sort(key=lambda p: p.price, reverse=True)
    
    return products[:limit]


def get_product_alternatives(product_id: str, limit: int = 3) -> List[Product]:
    """
    Get alternative products (same category, similar price)
    
    Args:
        product_id: Product to find alternatives for
        limit: Maximum number of alternatives
        
    Returns:
        List of alternative products
    """
    product = get_product_by_id(product_id)
    if not product:
        return []
    
    alternatives = []
    for p in PRODUCT_DATABASE.values():
        if p.product_id == product_id:
            continue
        
        # Same detection class or category
        if p.detection_class == product.detection_class or p.category == product.category:
            # Similar price (within 30%)
            price_diff = abs(p.price - product.price) / product.price
            if price_diff <= 0.3:
                alternatives.append((p, price_diff))
    
    # Sort by price similarity
    alternatives.sort(key=lambda x: x[1])
    
    return [alt[0] for alt in alternatives[:limit]]


# ============================================================================
# DEMO: ADD MORE PRODUCTS
# ============================================================================

def populate_demo_products():
    """Add more products for demo purposes"""
    demo_products = [
        Product(
            product_id="prod_coffee_001",
            name="Folgers Classic Roast Ground Coffee",
            category=ProductCategory.FOOD,
            detection_class="coffee_container",
            asin="B00TUXVBGU",
            price=11.99,
            description="Medium roast coffee, 30.5 oz canister",
            vendor="amazon",
            metadata={"size_oz": 30.5, "roast": "medium"},
        ),
        Product(
            product_id="prod_milk_001",
            name="Horizon Organic Whole Milk",
            category=ProductCategory.FOOD,
            detection_class="milk_carton",
            asin="B000X8X2QS",
            price=6.99,
            description="Organic whole milk, half gallon",
            vendor="amazon",
            metadata={"size_oz": 64, "organic": True},
        ),
        Product(
            product_id="prod_cereal_001",
            name="Cheerios Whole Grain Oat Cereal",
            category=ProductCategory.FOOD,
            detection_class="cereal_box",
            asin="B00CQOK8M8",
            price=5.49,
            description="Heart healthy cereal, 18 oz box",
            vendor="amazon",
            metadata={"size_oz": 18, "whole_grain": True},
        ),
    ]
    
    for product in demo_products:
        if product.product_id not in PRODUCT_DATABASE:
            PRODUCT_DATABASE[product.product_id] = product
    
    print(f"Added {len(demo_products)} demo products. Total: {len(PRODUCT_DATABASE)}")


# Initialize demo products on import
populate_demo_products()

