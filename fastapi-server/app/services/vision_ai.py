"""
Vision AI Service - DEPRECATED

⚠️ IMPORTANT: This file is now DEPRECATED.
Use Remote Service Gateway (RSG) in Lens Studio instead!

WHY?
- No API keys needed (Snap handles authentication)
- Better performance (optimized for Spectacles)
- Built-in rate limiting and security
- Lower latency

HOW TO USE RSG:
1. Generate RSG token in Lens Studio (Windows → Remote Service Gateway Token)
2. Use Gemini via RSG in your Lens Studio script:

   import { Gemini } from "LensStudio:RemoteServiceModule/HostedExternal/Gemini";
   
   const response = await Gemini.generateContent({
       model: "gemini-2.0-flash-exp",
       contents: [{
           parts: [
               { text: "Detect products..." },
               { inlineData: { mimeType: "image/jpeg", data: base64Image } }
           ]
       }]
   });

This backend now only handles:
- Product database queries
- Order placement
- User preferences
- Business logic

Vision detection happens in Lens Studio via RSG.

---

LEGACY CODE BELOW (for reference only)
This code is kept for documentation purposes but is not used in production.
"""

# Legacy imports (not needed anymore)
import asyncio
import base64
import os
import time
import uuid
from typing import List, Optional, Tuple

# These imports are now optional
try:
    from dotenv import load_dotenv
    from anthropic import AsyncAnthropic
    from PIL import Image
    import io
except ImportError:
    print("⚠️ Vision AI dependencies not installed. Use RSG in Lens Studio instead!")
    AsyncAnthropic = None

from app.models.schemas import (
    Detection,
    BoundingBox,
    ProductState,
    DetectionResponse,
)
from app.utils.ar_optimization import optimize_product_description, optimize_ai_response

# Legacy configuration (not needed with RSG)
if AsyncAnthropic:
    load_dotenv()
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    if ANTHROPIC_API_KEY:
        anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    else:
        anthropic_client = None
        print("ℹ️ No ANTHROPIC_API_KEY found. Using Remote Service Gateway is recommended.")
else:
    anthropic_client = None


# ============================================================================
# MOCK DETECTION (for testing without API)
# ============================================================================

async def mock_detect_objects(
    image_base64: str,
    confidence_threshold: float = 0.7,
) -> DetectionResponse:
    """
    Mock detection function for testing without API calls
    
    Returns fake detections for development/testing.
    In production, use Remote Service Gateway in Lens Studio.
    """
    session_id = str(uuid.uuid4())
    
    # Simulate processing time
    await asyncio.sleep(0.5)
    
    mock_detections = [
        Detection(
            detection_id=f"{session_id}_0",
            class_name="water_bottle",
            confidence=0.92,
            bounding_box=BoundingBox(x=0.3, y=0.4, width=0.15, height=0.3),
            state=ProductState.EMPTY,
            state_confidence=0.88,
            matched_product=None,
        ),
        Detection(
            detection_id=f"{session_id}_1",
            class_name="sunscreen",
            confidence=0.85,
            bounding_box=BoundingBox(x=0.6, y=0.3, width=0.12, height=0.25),
            state=ProductState.LOW,
            state_confidence=0.79,
            matched_product=None,
        ),
    ]
    
    return DetectionResponse(
        session_id=session_id,
        detections=mock_detections,
        processing_time_ms=500,
        image_dimensions={"width": 1920, "height": 1080},
    )


# ============================================================================
# LEGACY DETECTION CODE (for reference only)
# ============================================================================

# This code is kept for reference but is not recommended for production.
# Use Remote Service Gateway in Lens Studio instead for better performance.

OBJECT_DETECTION_SYSTEM_PROMPT = """You are an expert computer vision system specialized in detecting household products and their states.

Your task is to:
1. Identify products in images (water bottles, sunscreen, household items, etc.)
2. Classify each product's state: FULL, HALF, LOW, or EMPTY
3. Provide bounding box coordinates (normalized 0-1) for each detected object
4. Rate your confidence (0-1) for both detection and state classification

CRITICAL: Keep reasoning under 150 characters for AR display optimization.

Return your response in this exact JSON format:
{
    "detections": [
        {
            "class_name": "water_bottle",
            "confidence": 0.95,
            "bounding_box": {"x": 0.3, "y": 0.4, "width": 0.15, "height": 0.3},
            "state": "low",
            "state_confidence": 0.87,
            "reasoning": "Container 30% full, below half mark"
        }
    ]
}

Common product classes:
- water_bottle, soda_can, juice_box
- sunscreen, lotion, shampoo, conditioner, soap
- laundry_detergent, dish_soap, cleaning_spray
- milk_carton, cereal_box, snack_bag
- coffee_container, tea_box
- toothpaste, deodorant

State classification guidelines:
- FULL: 80-100% filled, unopened or barely used
- HALF: 40-79% filled
- LOW: 10-39% filled, clearly needs replacement soon
- EMPTY: 0-9% filled or visibly empty
- UNKNOWN: Cannot determine state clearly

Be precise with bounding boxes and honest about confidence levels.
Keep reasoning concise for AR display (max 150 chars)."""


async def detect_objects_from_image_LEGACY(
    image_base64: str,
    confidence_threshold: float = 0.7,
    max_detections: int = 10,
) -> DetectionResponse:
    """
    LEGACY: Detect objects using Claude Vision API
    
    ⚠️ DEPRECATED: Use Remote Service Gateway in Lens Studio instead!
    
    This function is kept for backward compatibility only.
    For new implementations, use Gemini via RSG in Lens Studio.
    """
    if not anthropic_client:
        print("⚠️ Anthropic client not configured. Returning mock data.")
        return await mock_detect_objects(image_base64, confidence_threshold)
    
    # Legacy implementation would go here
    # But we recommend using RSG instead
    return await mock_detect_objects(image_base64, confidence_threshold)


# For backward compatibility, keep the original function name
detect_objects_from_image = detect_objects_from_image_LEGACY
