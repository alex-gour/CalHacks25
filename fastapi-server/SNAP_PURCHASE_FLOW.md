# Snap & Purchase Flow

This document describes the new snap-and-purchase flow that integrates image detection, product search, and automated Shopify purchasing.

## Overview

The flow consists of three main steps:

1. **Image Detection** (Gemini): Detect products in an image and identify low-stock items
2. **Product Matching/Search**:
   - **Database Mode** (`database=true`): Match against prepopulated product catalog
   - **Search Mode** (`database=false`): Find Shopify URLs using Google Search API
3. **Automated Purchase** (Selenium): Purchase the product from Shopify

## Architecture

### Services

- **`app/services/gemini_detection.py`**: Gemini-based product detection service
- **`app/services/google_search.py`**: Google Custom Search API integration
- **`app/services/product_matcher.py`**: Product catalog matching service
- **`app/services/shopify_purchase.py`**: Shopify purchase automation service

### Endpoints

#### Snap & Purchase
All endpoints are available under `/api/snap-purchase`:

1. **`POST /api/snap-purchase/detect`**: Detect products in an image
2. **`POST /api/snap-purchase/search`**: Search for Shopify URLs by product label
3. **`POST /api/snap-purchase/purchase`**: Purchase a product from a Shopify URL
4. **`POST /api/snap-purchase/snap-and-buy`**: Complete flow (detect → match/search → purchase)

#### Product Catalog Management
All endpoints are available under `/api/catalog`:

1. **`GET /api/catalog/products`**: List all products in catalog
2. **`GET /api/catalog/products/{id}`**: Get a specific product
3. **`POST /api/catalog/products`**: Add a new product to catalog
4. **`PUT /api/catalog/products/{id}`**: Update an existing product
5. **`DELETE /api/catalog/products/{id}`**: Delete a product from catalog
6. **`POST /api/catalog/match`**: Test matching a label against catalog

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required variables:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GOOGLE_SEARCH_API_KEY`: Your Google Custom Search API key
- `GOOGLE_SEARCH_ENGINE_ID`: Your Google Custom Search Engine ID

Optional Shopify purchase defaults (can be overridden per request):
- Customer info: `SHOPIFY_EMAIL`, `SHOPIFY_FIRST_NAME`, etc.
- Payment info: `SHOPIFY_CARD_NUMBER`, `SHOPIFY_EXP_MONTH`, etc.

### 3. Set Up Google Custom Search

1. Go to [Google Custom Search](https://programmablesearchengine.google.com/)
2. Create a new search engine
3. **Important**: Configure it to "Search the entire web" (not just specific sites)
4. Enable "Image search" and "SafeSearch" if desired
5. Get your Search Engine ID from the setup page (looks like: `012345678901234567890:abcdefghijk`)
6. Get an API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Enable the "Custom Search API" for your project
   - Create credentials → API key
7. Add both values to your `.env` file

**Search Quality Tips:**
- The search uses `inurl:products` to specifically target product pages (not collection pages)
- Results are filtered to exclude `/collections/` URLs
- If you're getting poor results, the product label from Gemini might be too generic
- Consider using more specific keywords when searching manually via the `/search` endpoint

### 4. Install ChromeDriver

For automated purchasing, you need ChromeDriver installed:

```bash
# macOS
brew install chromedriver

# Or download from: https://chromedriver.chromium.org/
```

## Usage

### Option 1: Complete Flow with Database Mode (Recommended)

Use the prepopulated product catalog for faster, more reliable matching:

```bash
curl -X POST "http://localhost:8000/api/snap-purchase/snap-and-buy?database=true&auto_purchase=true&quantity=1" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@/path/to/image.png"
```

**Response:**
```json
{
  "detected_products": [
    {
      "box_2d": [100, 200, 300, 400],
      "label": "water bottle, white, blue cap",
      "percent_full": 15,
      "is_low": true,
      "confidence": 0.9
    }
  ],
  "search_results": [],
  "catalog_match": {
    "detected_label": "water bottle, white, blue cap",
    "matched_product": {
      "id": "lifestraw-1l",
      "name": "LifeStraw Go Series Stainless Steel 1L",
      "category": "water bottle",
      "shopify_url": "https://lifestraw-store.myshopify.com/products/lifestraw-go-series-stainless-steel-1l"
    },
    "confidence": 0.85,
    "match_reason": "Matched on: category 'water bottle'; keyword 'bottle'; name words: water, bottle"
  },
  "purchase_url": "https://lifestraw-store.myshopify.com/products/lifestraw-go-series-stainless-steel-1l",
  "purchase_result": {
    "success": true,
    "message": "Purchase initiated"
  }
}
```

### Option 2: Complete Flow with Google Search

Use Google Search to find products (requires API keys):

```bash
curl -X POST "http://localhost:8000/api/snap-purchase/snap-and-buy?database=false&auto_purchase=true&quantity=1" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@/path/to/image.png"
```

**Response:**
```json
{
  "detected_products": [
    {
      "box_2d": [100, 200, 300, 400],
      "label": "shampoo bottle, white, pump",
      "percent_full": 15,
      "is_low": true,
      "confidence": 0.9
    }
  ],
  "search_results": [
    {
      "title": "Premium Shampoo - ACME Store",
      "url": "https://acmestore.myshopify.com/products/premium-shampoo",
      "snippet": "High-quality shampoo for all hair types..."
    }
  ],
  "purchase_url": "https://acmestore.myshopify.com/products/premium-shampoo",
  "purchase_result": {
    "success": true,
    "message": "Purchase initiated",
    "cart_url": "https://acmestore.myshopify.com/cart/..."
  }
}
```

## Managing the Product Catalog

### View Catalog Products

```bash
curl -X GET "http://localhost:8000/api/catalog/products"
```

### Add a Product to Catalog

```bash
curl -X POST "http://localhost:8000/api/catalog/products" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "new-product-1",
    "name": "Premium Water Bottle",
    "category": "water bottle",
    "keywords": ["water", "bottle", "hydration", "sports"],
    "shopify_url": "https://store.myshopify.com/products/water-bottle",
    "description": "Insulated water bottle for sports",
    "attributes": {
      "material": "stainless steel",
      "capacity": "750ml",
      "color": "blue"
    }
  }'
```

### Update a Product

```bash
curl -X PUT "http://localhost:8000/api/catalog/products/new-product-1" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "new-product-1",
    "name": "Premium Water Bottle - Updated",
    "category": "water bottle",
    "keywords": ["water", "bottle", "hydration", "sports", "insulated"],
    "shopify_url": "https://store.myshopify.com/products/water-bottle",
    "description": "Insulated water bottle for sports and outdoor activities"
  }'
```

### Delete a Product

```bash
curl -X DELETE "http://localhost:8000/api/catalog/products/new-product-1"
```

### Test Catalog Matching

Test how a product label would match against the catalog:

```bash
curl -X POST "http://localhost:8000/api/catalog/match?label=blue%20water%20bottle%20stainless%20steel"
```

**Response:**
```json
{
  "detected_label": "blue water bottle stainless steel",
  "matched_product": {
    "id": "lifestraw-1l",
    "name": "LifeStraw Go Series Stainless Steel 1L",
    "category": "water bottle",
    "shopify_url": "https://lifestraw-store.myshopify.com/products/lifestraw-go-series-stainless-steel-1l"
  },
  "confidence": 0.75,
  "match_reason": "Matched on: category 'water bottle'; keyword 'stainless steel'; name words: water, bottle"
}
```

### Option 3: Step-by-Step

#### Step 1: Detect Products

```bash
curl -X POST "http://localhost:8000/api/snap-purchase/detect" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@/path/to/image.png"
```

**Response:**
```json
{
  "detected_products": [
    {
      "box_2d": [100, 200, 300, 400],
      "label": "shampoo bottle, white, pump",
      "percent_full": 15,
      "is_low": true,
      "confidence": 0.9
    }
  ],
  "count": 1
}
```

#### Step 2: Search for Product

```bash
curl -X POST "http://localhost:8000/api/snap-purchase/search?product_label=shampoo%20bottle%2C%20white%2C%20pump&max_results=5"
```

**Response:**
```json
{
  "product_label": "shampoo bottle, white, pump",
  "search_results": [
    {
      "title": "Premium Shampoo - ACME Store",
      "url": "https://acmestore.myshopify.com/products/premium-shampoo",
      "snippet": "High-quality shampoo..."
    }
  ],
  "best_url": "https://acmestore.myshopify.com/products/premium-shampoo"
}
```

#### Step 3: Purchase Product

```bash
curl -X POST "http://localhost:8000/api/snap-purchase/purchase?product_url=https://acmestore.myshopify.com/products/premium-shampoo&quantity=1"
```

**Response:**
```json
{
  "success": true,
  "message": "Purchase initiated",
  "product_url": "https://acmestore.myshopify.com/products/premium-shampoo",
  "product_info": {
    "name": "Premium Shampoo",
    "url": "https://acmestore.myshopify.com/products/premium-shampoo",
    "variants": [...],
    "total_stock": 100
  },
  "cart_url": "https://acmestore.myshopify.com/cart/123456:1"
}
```

## Flow Diagram

### Database Mode (database=true)
```
┌─────────────┐
│   Upload    │
│    Image    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  Gemini Detection API   │
│  (detect_features.py)   │
└──────┬──────────────────┘
       │
       │ Detected Products
       ▼
┌─────────────────────────┐
│  Product Catalog        │
│  Matcher                │
│  (product_matcher.py)   │
└──────┬──────────────────┘
       │
       │ Matched Product URL
       ▼
┌─────────────────────────┐
│  Shopify Purchase Bot   │
│  (shopify_purchase.py)  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────┐
│  Purchase   │
│  Complete   │
└─────────────┘
```

### Search Mode (database=false)
```
┌─────────────┐
│   Upload    │
│    Image    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  Gemini Detection API   │
│  (detect_features.py)   │
└──────┬──────────────────┘
       │
       │ Detected Products
       ▼
┌─────────────────────────┐
│  Google Search API      │
│  (google_search.py)     │
└──────┬──────────────────┘
       │
       │ Shopify URLs
       ▼
┌─────────────────────────┐
│  Shopify Purchase Bot   │
│  (shopify_purchase.py)  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────┐
│  Purchase   │
│  Complete   │
└─────────────┘
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

You can test with the included test image:

```bash
# If you have a test image
curl -X POST "http://localhost:8000/api/snap-purchase/snap-and-buy?auto_purchase=false" \
  -F "image=@multiple_products.png"
```

Set `auto_purchase=false` to only detect and search without purchasing.

## Notes

- **Database vs Search Mode**:
  - **Database Mode** is faster and more reliable, but requires prepopulating the catalog
  - **Search Mode** is more flexible but requires Google API keys and has usage limits
  - Use Database Mode for known/recurring products, Search Mode for discovery
- **Selenium Browser**: The purchase automation will open a Chrome browser window. This is intentional for debugging and monitoring.
- **Test Cards**: Use Stripe test card `4242424242424242` for testing Shopify stores in test mode.
- **Low Stock Detection**: The flow prioritizes products marked as `is_low: true` (< 25% full).
- **Google Search Limits**: The Google Custom Search API has usage limits. See [pricing](https://developers.google.com/custom-search/v1/overview#pricing).
- **Catalog Storage**: The product catalog is stored in `app/data/product_catalog.json` and persists across server restarts.
- **Matching Algorithm**: The matcher uses category, keywords, and attributes to score matches. Confidence threshold is 0.3 (30%).

## Troubleshooting

### "GEMINI_API_KEY environment variable not set"
Make sure you've created a `.env` file with your API keys.

### "ChromeDriver not found"
Install ChromeDriver using `brew install chromedriver` or download it manually.

### "Product search failed"
Check your Google Custom Search API key and Search Engine ID configuration.

### "Product is sold out"
The Shopify product has no stock available. Try a different product URL.
