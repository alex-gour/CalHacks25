# Spectacles Reorder Assistant Backend

Hands-free replenishment server that pairs with Snap Spectacles to identify when everyday consumables are running low and reorder them with a single gesture or voice confirmation.

## What This Does

- Accepts real-time detection events from Spectacles vision models (object class + fill level).
- Maps detections to a curated product catalog and throttles duplicate prompts per session.
- Captures pinch/voice confirmations and submits a commerce order via a provider abstraction (mocked by default).
- Exposes lightweight telemetry so you can verify latency targets, prompt frequency, and order flow during demos.

## Quickstart

```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger UI lives at `http://localhost:8000/docs`.

## Environment Variables

No keys are required for the mock commerce mode. To point at a real commerce API set:

- `COMMERCE_BASE_URL`
- `COMMERCE_API_KEY`

(You would then update `app/services/__init__.py` to load from `os.getenv`).

To enable the Bright Data Amazon scraper endpoint set:

- `BRIGHTDATA_API_KEY`
- `BRIGHTDATA_DATASET_ID`

Without these the `/api/scrapers/amazon/discover` route returns `503` so we never leak secrets or surprise-call third-party APIs.

## Bright Data Amazon Scraper

Once the two Bright Data env vars are set and the server is running, drop your detection payloads directly into the body of a `POST /api/scrapers/amazon/discover` call.

Example `curl` once the env vars are loaded:

```bash
curl -X POST "http://localhost:8000/api/scrapers/amazon/discover" \
  -H "Content-Type: application/json" \
  -d '{
        "input": [
          {
            "box_2d": [124, 357, 888, 622],
            "mask": "data:image/png;base64,...",
            "label": "Nestle Pure Life water bottle, plastic",
            "percent_full": 27,
            "is_low": false,
            "confidence": 0.9
          },
          { "box_2d": [0, 0, 640, 480], "label": "dog toys", "percent_full": 15, "is_low": true, "confidence": 0.85 }
        ],
        "max_records_per_input": 3
      }'
```

That request body is exactly where you slam the Bright Data query: pass each detection in the `input` array and we fan those labels into keyword searches upstream. The response comes back shaped like `BrightDataScrapeResponse` so you can grab ASIN, titles, URLs, and any extra metadata Bright Data sneaks in.

## Core Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/detections` | Ingest on-device detection events and learn whether to prompt the user |
| `GET` | `/api/detections/intents/{intent_id}` | Fetch metadata for a pending prompt |
| `POST` | `/api/orders/decisions` | Submit gesture/voice confirmation or dismissal |
| `GET` | `/api/orders/{order_id}` | Poll order status |
| `GET` | `/api/products` | List supported object classes + catalog metadata |
| `GET` | `/api/system/telemetry` | Recent event counts for debugging |

## Flow Summary

1. **Detection** – Device posts `DetectionEvent` once the CV stack flags `NEARLY_EMPTY`/`EMPTY` with high confidence.
2. **Policy & Throttle** – `PromptIntentStore` enforces a per-device/object cooldown and records the new `PromptIntent`.
3. **Confirmation** – Spectacles sends user confirmation via `/orders/decisions` with the channel (`VOICE`, `GESTURE`, etc.).
4. **Commerce** – Accepted prompts translate into an `OrderRequest` and are handed to `CommerceProvider` (mock by default).
5. **Telemetry** – Every step emits in-memory telemetry so you can hit `/api/system/telemetry` to validate zero double-prompts and end-to-end latency.

## Extending

- Update `app/services/product_catalog.py` to add new object classes or variants.
- Swap the mock commerce provider by changing `CommerceConfig` in `app/services/__init__.py`.
- Persist prompt/order state by replacing `PromptIntentStore` with a database-backed implementation (keep the interface intact).

## Testing Ideas

- Unit test `PromptIntentStore` to harden cooldown + intent expiry logic.
- Contract-test `/api/orders/decisions` to ensure rejected confirmations never attempt to order.
- Load-test `/api/detections` with high-frequency events to confirm we maintain the 300ms target end-to-end.

Have fun turning XR eyewear into the most loyal auto-replenishment buddy. 🐶
