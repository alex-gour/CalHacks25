"""Gemini-based product detection service."""

from google import genai
from google.genai import types
import os
from typing import List, Optional
import json
from pydantic import BaseModel


class DetectedProduct(BaseModel):
    """Represents a product detected by Gemini."""
    box_2d: List[int]  # [y0, x0, y1, x1]
    label: str
    percent_full: int
    is_low: bool
    confidence: float


class GeminiDetectionService:
    """Service for detecting products in images using Gemini."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-flash'

    async def detect_products(self, image_bytes: bytes, mime_type: str = 'image/png') -> List[DetectedProduct]:
        """
        Detect products in an image using Gemini.

        Args:
            image_bytes: Image data as bytes
            mime_type: MIME type of the image (default: image/png)

        Returns:
            List of detected products
        """
        prompt = """
You are a container detection engine. ONLY detect objects that are FILLABLE CONTAINERS (bottles, tubes, jars, vials, canisters, dispensers, spray bottles, etc.) that can hold liquids, gels, or contents that deplete over time.

CRITICAL: IGNORE completely:
- Solid objects (phones, books, mugs, plates, utensils)
- Electronic devices
- Clothing, fabric, paper
- Food items that are not in containers
- Any object that cannot be "filled" or "emptied"
- Cosmetic products without visible containers (like solid bars, powders without containers)

ONLY OUTPUT objects that meet ALL criteria:
1. Is a CONTAINER (bottles, tubes, jars, canisters, spray bottles, dispensers, vials)
2. Has an INTERIOR that can hold contents
3. Has an "emptiness" level (can be full, partially full, or empty)
4. Can be used up over time (contents can deplete)

For each detected fillable container, output EXACTLY one JSON object:

[
  {
    "box_2d": [y0, x0, y1, x1],
    "label": "<container type + description>",
    "percent_full": N,
    "is_low": true|false,
    "confidence": C
  },
  ...
]

STRICT RULES:
- OUTPUT FORMAT: Respond ONLY with Markdown JSON code block. First line MUST be ```json, last line MUST be ```. No prose, no explanations.
- JSON: Strict JSON; no trailing commas; double-quoted keys/strings; numbers only for percent_full/confidence; booleans are true/false (lowercase).
- SORTING: Sort by top-left corner (ascending x0, then ascending y0).
- LABELING: Use generic names. Include container type (bottle, tube, jar, spray bottle, dispenser, etc.).
- FILTERING: If you are uncertain an object is a fillable container, DO NOT include it. Better to return empty array than wrong objects.

- PERCENT FULL ESTIMATION (CRITICAL - read carefully):
  1) Transparent/Translucent containers: Measure liquid level from bottom to top. 0-25% = near empty, 25-50% = half full, 50-75% = mostly full, 75-90% = very full, 90%+ = almost completely full.
  2) Opaque containers with sight window: Only use the visible window. If you see product in window, it's 50-70% full. If window is empty, bottle is 10-40% full.
  3) Fully opaque containers (lotion bottles, opaque sprays): USE THIS RULE - estimate 45-65% for opaque bottles unless there's obvious deformation indicating they're nearly empty (10-30%). DO NOT estimate 90%+ for opaque bottles without strong visual evidence. A normal opaque lotion bottle should be estimated at 50-65% full on average.
  4) Spray bottles: If you can see product level, use that. If opaque, estimate 50-65% unless clearly empty or full.
  5) Dropper bottles: If transparent, estimate actual liquid level. If opaque or tinted, estimate 40-60% as baseline.
  6) SQUEEZABLE TUBES: Deep creases throughout = 10-25%, some creases = 30-50%, minimal creases = 60-80%, smooth and plump = 80-95%.
  7) DEFAULT RULE FOR UNCERTAINTY: Most containers in real homes are 45-70% full. Only estimate above 80% if you have strong visual evidence.
  
  Clip all values to [0,100] and round to nearest integer.

- CONFIDENCE SCORING:
  0.9: Clear fill line in transparent container or obvious physical deformation
  0.7: Visible but somewhat ambiguous fill level or partial sight window
  0.5: Inferred from subtle cues like container shape changes
  0.3: Highly uncertain, mostly guessing
  
- CALIBRATION REMINDER: 
  Most real-world containers in homes are NOT nearly full! People use products daily. 
  When you see an opaque bottle, ask: "Would someone actually have a 95% full product?" 

- BOX_2D: Use [y0, x0, y1, x1] normalized to 0–1000 (integers). Ensure y0<y1 and x0<x1. Tightly enclose only the container, not surrounding objects.

IF NO FILLABLE CONTAINERS ARE DETECTED: Return an empty JSON array [] in the required code block.
"""

        try:
            print(f"[DEBUG] Sending image to Gemini: {len(image_bytes)} bytes, mime_type={mime_type}")

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    ),
                    prompt
                ],
                config={
                    'temperature': 0.1,
                    'max_output_tokens': 4000,
                }
            )

            # Parse the response - extract JSON from markdown code block
            text = response.text.strip()
            print(f"[DEBUG] Gemini raw response: {text[:500]}...")  # First 500 chars

            if text.startswith('```json'):
                text = text[7:]  # Remove ```json
            if text.endswith('```'):
                text = text[:-3]  # Remove ```
            text = text.strip()

            print(f"[DEBUG] Gemini cleaned JSON: {text}")

            # Parse JSON
            products_data = json.loads(text)
            print(f"[DEBUG] Parsed {len(products_data)} products from Gemini")

            # Convert to DetectedProduct objects
            products = [DetectedProduct(**p) for p in products_data]
            return products

        except Exception as e:
            print(f"[ERROR] Error detecting products with Gemini: {e}")
            import traceback
            traceback.print_exc()
            raise


# Singleton instance
_gemini_service: Optional[GeminiDetectionService] = None


def get_gemini_service() -> GeminiDetectionService:
    """Get or create the Gemini detection service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiDetectionService()
    return _gemini_service
