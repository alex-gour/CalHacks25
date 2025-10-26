from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import time
import signal

# Add timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Request timed out after 60 seconds")

load_dotenv()

print("Initializing Gemini client...")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Reading image file...")
with open('multiple_products.png', 'rb') as f:
    image_bytes = f.read()
print(f"Image loaded: {len(image_bytes)} bytes")

print("Sending request to Gemini API...")
print("(This request asks for segmentation masks which can take a long time)")
start_time = time.time()

try:
    # Set timeout for 60 seconds
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/png',
            ),
            """
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
        ],
        config={
            'temperature': 0.1,
            'max_output_tokens': 4000,
        }
    )
    
    signal.alarm(0)  # Cancel timeout
    elapsed = time.time() - start_time
    print(f"Response received in {elapsed:.2f} seconds")
    print("\n" + "="*60)
    print(response.text)
    print("="*60)
    
except TimeoutError as e:
    elapsed = time.time() - start_time
    print(f"\n{str(e)}")
    print("The API request took too long. This is likely because:")
    print("- The prompt asked for complex binary segmentation masks")
    print("- The API may be rate-limited or slow")
    print("\nTry: Run the script again, or simplify the prompt further")
except KeyboardInterrupt:
    print("\n\nScript interrupted by user")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"\nError after {elapsed:.2f} seconds: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

