"""Segmentation service with enhanced JSON parsing and validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from PIL import Image
import io
import json
import copy

from google import genai
from google.genai import types
import os


class DetectedProduct(BaseModel):
    """Represents a product detected by segmentation."""
    box_2d: List[int]  # [y0, x0, y1, x1]
    label: str
    percent_full: int
    is_low: bool
    confidence: float


def _parse_json_robust(json_output: str) -> str:
    """
    Extract JSON from markdown code blocks or find JSON directly.
    Includes fallback logic for incomplete JSON.

    Args:
        json_output: Raw output from Gemini API

    Returns:
        Extracted JSON string
    """
    lines = json_output.splitlines()
    json_start = -1
    json_end = -1

    # Try to find markdown JSON block
    for i, line in enumerate(lines):
        if line.strip() == "```json":
            json_start = i + 1
        elif line.strip() == "```" and json_start != -1:
            json_end = i
            break

    if json_start != -1 and json_end != -1:
        json_content = "\n".join(lines[json_start:json_end])
        print(f"[SEGMENTATION] Extracted JSON from markdown blocks: {len(json_content)} characters")
        return json_content.strip()

    print("[SEGMENTATION] No markdown blocks found, searching for JSON directly")

    # Fallback: Find JSON array by bracket matching
    start_idx = json_output.find('[')
    if start_idx != -1:
        print(f"[SEGMENTATION] Found '[' at position {start_idx}")
        bracket_count = 0
        end_idx = start_idx

        for i in range(start_idx, len(json_output)):
            if json_output[i] == '[':
                bracket_count += 1
            elif json_output[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i
                    break

        if bracket_count == 0:
            json_content = json_output[start_idx:end_idx + 1]
            print(f"[SEGMENTATION] Found complete JSON: {len(json_content)} characters")
            return json_content
        else:
            print(f"[SEGMENTATION] JSON appears incomplete, bracket count: {bracket_count}")
            return json_output[start_idx:]

    print("[SEGMENTATION] No JSON found, returning original string")
    return json_output


def _normalize_box_2d(box: List) -> List[int]:
    """
    Normalize bounding box coordinates to [y0, x0, y1, x1] format in 0-1000 range.

    Args:
        box: List of 4 coordinates in various formats

    Returns:
        Normalized [y0, x0, y1, x1] list
    """
    vals = [float(v) for v in box]
    m = max(vals)

    # Scale to 0-1000 range
    if m <= 1.5:
        vals = [v * 1000.0 for v in vals]
    elif 1000 < m <= 1024 + 20:
        scale = 1000.0 / 1024.0
        vals = [v * scale for v in vals]

    y0, x0, y1, x1 = vals

    # Auto-detect if coordinates are swapped
    if abs((y1 - y0)) < abs((x1 - x0)) and (y0 > x0 or y1 > x1):
        x0, y0, x1, y1 = vals

    # Ensure correct ordering
    if y0 > y1:
        y0, y1 = y1, y0
    if x0 > x1:
        x0, x1 = x1, x0

    # Clamp to valid range
    y0 = int(max(0, min(1000, round(y0))))
    x0 = int(max(0, min(1000, round(x0))))
    y1 = int(max(0, min(1000, round(y1))))
    x1 = int(max(0, min(1000, round(x1))))

    return [y0, x0, y1, x1]


def _is_valid_container(item: Dict[str, Any]) -> bool:
    """
    Filter out non-container objects based on label keywords.

    Args:
        item: Detected item dictionary

    Returns:
        True if item appears to be a valid fillable container
    """
    label = item.get('label', '').lower()

    container_keywords = [
        'bottle', 'container', 'tube', 'jar', 'vial', 'canister',
        'dispenser', 'pump', 'spray', 'dropper', 'flask',
        'can', 'cartridge', 'syringe'
    ]

    non_container_keywords = [
        'phone', 'book', 'paper', 'card', 'electronics', 'cable', 'charger',
        'mug', 'cup', 'plate', 'bowl', 'utensil', 'fork', 'spoon', 'knife',
        'clothing', 'fabric', 'textile', 'bag', 'backpack', 'shirt', 'shoe',
        'food', 'fruit', 'vegetable', 'apple', 'banana', 'orange',
        'soap bar', 'bar', 'solid', 'brick', 'block', 'tile', 'stone'
    ]

    has_container_keyword = any(keyword in label for keyword in container_keywords)
    has_non_container_keyword = any(keyword in label for keyword in non_container_keywords)

    if has_non_container_keyword and not has_container_keyword:
        print(f"[SEGMENTATION] Filtered out non-container: {item.get('label', 'unknown')}")
        return False

    if has_container_keyword:
        return True

    print(f"[SEGMENTATION] Warning: Uncertain if container: {item.get('label', 'unknown')}")
    return True


class SegmentationService:
    """Service for detecting products using enhanced Gemini detection with robust parsing."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-flash'

    async def detect_products(self, image_bytes: bytes, mime_type: str = 'image/png') -> List[DetectedProduct]:
        """
        Detect products in an image using Gemini with enhanced JSON parsing.

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
            print(f"[SEGMENTATION DEBUG] Receiving image: {len(image_bytes)} bytes, mime_type={mime_type}")

            # Convert bytes to PIL Image for preprocessing
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            print(f"[SEGMENTATION DEBUG] Image loaded: {image.size}, mode={image.mode}")

            # Call Gemini API
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

            # Parse response with robust JSON extraction
            text = response.text.strip()
            print(f"[SEGMENTATION DEBUG] Gemini raw response length: {len(text)} characters")
            print(f"[SEGMENTATION DEBUG] First 500 chars: {text[:500]}...")

            # Extract JSON using robust parser
            parsed_json = _parse_json_robust(text)

            # Additional cleanup: ensure JSON starts and ends correctly
            if not parsed_json.strip().startswith('['):
                print("[SEGMENTATION] JSON doesn't start with '[' - trying to find array start")
                start_idx = parsed_json.find('[')
                if start_idx != -1:
                    parsed_json = parsed_json[start_idx:]

            if not parsed_json.strip().endswith(']'):
                print("[SEGMENTATION] JSON doesn't end with ']' - trying to complete it")
                last_brace = parsed_json.rfind('}')
                if last_brace != -1:
                    end_pos = last_brace + 1
                    parsed_json = parsed_json[:end_pos] + ']'
                    print("[SEGMENTATION] Attempted to complete JSON by adding ']'")

            print(f"[SEGMENTATION DEBUG] Cleaned JSON: {parsed_json}")

            # Parse JSON
            items = json.loads(parsed_json)
            print(f"[SEGMENTATION DEBUG] Successfully parsed {len(items)} items")

            # Validate containers
            filtered_items = [item for item in items if _is_valid_container(item)]
            if len(filtered_items) < len(items):
                print(f"[SEGMENTATION] Filtered {len(items) - len(filtered_items)} non-container objects")

            # Normalize boxes and convert to DetectedProduct objects
            products = []
            for item in filtered_items:
                try:
                    # Normalize bounding box
                    normalized_box = _normalize_box_2d(item['box_2d'])

                    product = DetectedProduct(
                        box_2d=normalized_box,
                        label=item['label'],
                        percent_full=item['percent_full'],
                        is_low=item['is_low'],
                        confidence=item['confidence']
                    )
                    products.append(product)
                    print(f"[SEGMENTATION DEBUG] Product: {product.label}, {product.percent_full}% full, low={product.is_low}, box={product.box_2d}")
                except Exception as e:
                    print(f"[SEGMENTATION ERROR] Failed to parse item: {item}, error: {e}")
                    continue

            print(f"[SEGMENTATION DEBUG] Returning {len(products)} validated products")
            return products

        except json.JSONDecodeError as e:
            print(f"[SEGMENTATION ERROR] JSON parsing error: {e}")
            print(f"[SEGMENTATION ERROR] Attempted JSON: {parsed_json[:500]}...")

            # Try one more fallback: parse partial JSON
            try:
                last_brace = parsed_json.rfind('}')
                if last_brace != -1:
                    partial_json = parsed_json[:last_brace + 1] + ']'
                    print(f"[SEGMENTATION] Attempting partial JSON parse")
                    items = json.loads(partial_json)
                    print(f"[SEGMENTATION] Partial parse succeeded with {len(items)} items")

                    # Process partial results
                    filtered_items = [item for item in items if _is_valid_container(item)]
                    products = []
                    for item in filtered_items:
                        try:
                            normalized_box = _normalize_box_2d(item['box_2d'])
                            product = DetectedProduct(
                                box_2d=normalized_box,
                                label=item['label'],
                                percent_full=item['percent_full'],
                                is_low=item['is_low'],
                                confidence=item['confidence']
                            )
                            products.append(product)
                        except Exception:
                            continue

                    if products:
                        print(f"[SEGMENTATION] Returning {len(products)} products from partial parse")
                        return products
            except Exception as fallback_error:
                print(f"[SEGMENTATION ERROR] Fallback parsing also failed: {fallback_error}")

            # If all parsing fails, return empty list
            print("[SEGMENTATION] All parsing attempts failed, returning empty list")
            return []

        except Exception as e:
            print(f"[SEGMENTATION ERROR] Error detecting products: {e}")
            import traceback
            traceback.print_exc()
            raise


# Singleton instance
_segmentation_service: Optional[SegmentationService] = None


def get_segmentation_service() -> SegmentationService:
    """Get or create the segmentation service singleton."""
    global _segmentation_service
    if _segmentation_service is None:
        _segmentation_service = SegmentationService()
    return _segmentation_service
