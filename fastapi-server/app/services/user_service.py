"""
User Service for User Management and Preferences

This service handles:
- User profile management
- User preferences and settings
- Privacy controls
- User authentication (basic)
"""

from datetime import datetime
from typing import Dict, Optional
from app.models.schemas import UserProfile, UserPreferences, ProductState


# ============================================================================
# IN-MEMORY USER DATABASE
# ============================================================================

# In production, replace with real database (PostgreSQL, MongoDB, etc.)
USER_DATABASE: Dict[str, UserProfile] = {}


# ============================================================================
# USER CREATION & RETRIEVAL
# ============================================================================

def create_user(
    user_id: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
) -> UserProfile:
    """
    Create a new user with default preferences
    
    Args:
        user_id: Unique user identifier
        email: User email (optional)
        name: User name (optional)
        
    Returns:
        Created UserProfile
    """
    if user_id in USER_DATABASE:
        raise ValueError(f"User {user_id} already exists")
    
    # Create default preferences
    preferences = UserPreferences(
        user_id=user_id,
        auto_reorder_enabled=True,
        preferred_vendor="amazon",
        notification_threshold=ProductState.LOW,
        privacy_mode=True,
        order_history_limit=50,
        blocked_products=[],
        favorite_products=[],
    )
    
    # Create user profile
    user = UserProfile(
        user_id=user_id,
        email=email,
        name=name,
        preferences=preferences,
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
    )
    
    USER_DATABASE[user_id] = user
    return user


def get_user(user_id: str) -> Optional[UserProfile]:
    """
    Get user profile by ID
    
    Args:
        user_id: User ID
        
    Returns:
        UserProfile or None if not found
    """
    user = USER_DATABASE.get(user_id)
    
    # Update last_active timestamp
    if user:
        user.last_active = datetime.utcnow()
        USER_DATABASE[user_id] = user
    
    return user


def get_or_create_user(user_id: str) -> UserProfile:
    """
    Get user or create if doesn't exist
    
    Args:
        user_id: User ID
        
    Returns:
        UserProfile
    """
    user = get_user(user_id)
    if user:
        return user
    
    return create_user(user_id)


def user_exists(user_id: str) -> bool:
    """Check if user exists"""
    return user_id in USER_DATABASE


# ============================================================================
# USER PREFERENCES MANAGEMENT
# ============================================================================

def get_user_preferences(user_id: str) -> Optional[UserPreferences]:
    """
    Get user preferences
    
    Args:
        user_id: User ID
        
    Returns:
        UserPreferences or None
    """
    user = get_user(user_id)
    return user.preferences if user else None


def update_user_preferences(
    user_id: str,
    updates: Dict,
) -> Optional[UserPreferences]:
    """
    Update user preferences
    
    Args:
        user_id: User ID
        updates: Dictionary of preference fields to update
        
    Returns:
        Updated UserPreferences or None
    """
    user = get_user(user_id)
    if not user:
        return None
    
    # Update preference fields
    for key, value in updates.items():
        if hasattr(user.preferences, key):
            setattr(user.preferences, key, value)
    
    USER_DATABASE[user_id] = user
    return user.preferences


def set_auto_reorder(user_id: str, enabled: bool) -> bool:
    """
    Enable or disable auto-reorder prompts
    
    Args:
        user_id: User ID
        enabled: Whether to enable auto-reorder
        
    Returns:
        Success status
    """
    prefs = update_user_preferences(user_id, {"auto_reorder_enabled": enabled})
    return prefs is not None


def set_notification_threshold(user_id: str, threshold: ProductState) -> bool:
    """
    Set the threshold for when to show reorder notifications
    
    Args:
        user_id: User ID
        threshold: ProductState threshold (FULL, HALF, LOW, EMPTY)
        
    Returns:
        Success status
    """
    prefs = update_user_preferences(user_id, {"notification_threshold": threshold})
    return prefs is not None


def set_preferred_vendor(user_id: str, vendor: str) -> bool:
    """
    Set user's preferred vendor
    
    Args:
        user_id: User ID
        vendor: Vendor name (amazon, walmart, instacart, etc.)
        
    Returns:
        Success status
    """
    prefs = update_user_preferences(user_id, {"preferred_vendor": vendor.lower()})
    return prefs is not None


def set_privacy_mode(user_id: str, enabled: bool) -> bool:
    """
    Enable or disable privacy mode (on-device processing)
    
    Args:
        user_id: User ID
        enabled: Whether to enable privacy mode
        
    Returns:
        Success status
    """
    prefs = update_user_preferences(user_id, {"privacy_mode": enabled})
    return prefs is not None


# ============================================================================
# DELIVERY ADDRESS MANAGEMENT
# ============================================================================

def update_delivery_address(
    user_id: str,
    address: Dict[str, str],
) -> bool:
    """
    Update user's default delivery address
    
    Args:
        user_id: User ID
        address: Address dict with keys like street, city, state, zip, country
        
    Returns:
        Success status
    """
    prefs = update_user_preferences(user_id, {"delivery_address": address})
    return prefs is not None


def get_delivery_address(user_id: str) -> Optional[Dict[str, str]]:
    """
    Get user's default delivery address
    
    Args:
        user_id: User ID
        
    Returns:
        Address dict or None
    """
    prefs = get_user_preferences(user_id)
    return prefs.delivery_address if prefs else None


# ============================================================================
# PRODUCT BLOCKING & FAVORITES
# ============================================================================

def block_product(user_id: str, product_id: str) -> bool:
    """
    Block a product from auto-reorder prompts
    
    Args:
        user_id: User ID
        product_id: Product to block
        
    Returns:
        Success status
    """
    user = get_user(user_id)
    if not user:
        return False
    
    if product_id not in user.preferences.blocked_products:
        user.preferences.blocked_products.append(product_id)
        USER_DATABASE[user_id] = user
    
    return True


def unblock_product(user_id: str, product_id: str) -> bool:
    """
    Unblock a product
    
    Args:
        user_id: User ID
        product_id: Product to unblock
        
    Returns:
        Success status
    """
    user = get_user(user_id)
    if not user:
        return False
    
    if product_id in user.preferences.blocked_products:
        user.preferences.blocked_products.remove(product_id)
        USER_DATABASE[user_id] = user
    
    return True


def is_product_blocked(user_id: str, product_id: str) -> bool:
    """
    Check if a product is blocked for user
    
    Args:
        user_id: User ID
        product_id: Product ID
        
    Returns:
        True if blocked, False otherwise
    """
    prefs = get_user_preferences(user_id)
    if not prefs:
        return False
    
    return product_id in prefs.blocked_products


def add_favorite_product(user_id: str, product_id: str) -> bool:
    """
    Add product to favorites
    
    Args:
        user_id: User ID
        product_id: Product to favorite
        
    Returns:
        Success status
    """
    user = get_user(user_id)
    if not user:
        return False
    
    if product_id not in user.preferences.favorite_products:
        user.preferences.favorite_products.append(product_id)
        USER_DATABASE[user_id] = user
    
    return True


def remove_favorite_product(user_id: str, product_id: str) -> bool:
    """
    Remove product from favorites
    
    Args:
        user_id: User ID
        product_id: Product to remove
        
    Returns:
        Success status
    """
    user = get_user(user_id)
    if not user:
        return False
    
    if product_id in user.preferences.favorite_products:
        user.preferences.favorite_products.remove(product_id)
        USER_DATABASE[user_id] = user
    
    return True


def get_favorite_products(user_id: str) -> list:
    """
    Get user's favorite products
    
    Args:
        user_id: User ID
        
    Returns:
        List of product IDs
    """
    prefs = get_user_preferences(user_id)
    return prefs.favorite_products if prefs else []


# ============================================================================
# USER PROFILE UPDATES
# ============================================================================

def update_user_profile(
    user_id: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[UserProfile]:
    """
    Update user profile information
    
    Args:
        user_id: User ID
        email: New email (optional)
        name: New name (optional)
        
    Returns:
        Updated UserProfile or None
    """
    user = get_user(user_id)
    if not user:
        return None
    
    if email is not None:
        user.email = email
    
    if name is not None:
        user.name = name
    
    USER_DATABASE[user_id] = user
    return user


def delete_user(user_id: str) -> bool:
    """
    Delete a user and all their data
    
    Args:
        user_id: User ID
        
    Returns:
        True if deleted, False if not found
    """
    if user_id in USER_DATABASE:
        del USER_DATABASE[user_id]
        return True
    return False


# ============================================================================
# DEMO USERS
# ============================================================================

def create_demo_users():
    """Create demo users for testing"""
    demo_users = [
        {
            "user_id": "demo_user_001",
            "email": "alice@example.com",
            "name": "Alice Smith",
        },
        {
            "user_id": "demo_user_002",
            "email": "bob@example.com",
            "name": "Bob Johnson",
        },
    ]
    
    for user_data in demo_users:
        if user_data["user_id"] not in USER_DATABASE:
            create_user(**user_data)
    
    print(f"Created {len(demo_users)} demo users. Total: {len(USER_DATABASE)}")


# Initialize demo users on import
create_demo_users()

