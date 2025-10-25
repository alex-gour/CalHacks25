# 🛒 Auto-Reorder System Backend

FastAPI backend for the **Snap Spectacles Auto-Reorder System** - a hands-free shopping assistant using AR glasses, computer vision, and commerce APIs.

## 🎯 Overview

This backend powers a Spectacles lens that:
1. **Detects products** via computer vision (water bottles, sunscreen, household items, etc.)
2. **Analyzes product state** (full, half, low, empty)
3. **Prompts reorders** when products are running low
4. **Places orders** with commerce APIs (Amazon, Walmart, Instacart)
5. **Tracks orders** and maintains user preferences

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│ Spectacles Lens (Frontend)                          │
│ - Camera feed capture                                │
│ - Hand gesture / voice confirmation                  │
│ - UI prompts and notifications                       │
└─────────────────────────────────────────────────────┘
           │
           ▼ HTTP/REST API
┌─────────────────────────────────────────────────────┐
│ FastAPI Backend (This Repository)                   │
├─────────────────────────────────────────────────────┤
│ Services:                                            │
│  - vision_ai.py      : Object detection + state      │
│  - product_service.py: Product database              │
│  - order_service.py  : Order placement + tracking    │
│  - user_service.py   : User preferences + privacy    │
└─────────────────────────────────────────────────────┘
           │
           ▼ External APIs
┌─────────────────────────────────────────────────────┐
│ External Services                                    │
│ - Anthropic Claude (Vision AI)                       │
│ - Amazon Product API                                 │
│ - Walmart API                                        │
│ - Instacart API                                      │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Anthropic API key (for Claude Vision)
- Optional: Amazon/Walmart/Instacart API credentials

### Installation

```bash
cd fastapi-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Environment Variables

Create a `.env` file:

```env
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional (for production)
AMAZON_API_KEY=your_amazon_api_key
WALMART_API_KEY=your_walmart_api_key
INSTACART_API_KEY=your_instacart_api_key
```

### Run the Server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the run script
python run.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Key Endpoints

### Object Detection

```bash
# Detect objects and their states
POST /api/detect
Content-Type: application/json

{
  "image": "base64_encoded_image_here",
  "user_id": "user_123",
  "confidence_threshold": 0.7,
  "return_matches": true
}
```

**Response:**
```json
{
  "session_id": "abc-123",
  "detections": [
    {
      "detection_id": "abc-123_0",
      "class_name": "water_bottle",
      "confidence": 0.92,
      "bounding_box": {"x": 0.3, "y": 0.4, "width": 0.15, "height": 0.3},
      "state": "empty",
      "state_confidence": 0.88,
      "matched_product": {
        "product_id": "prod_water_001",
        "name": "Spring Water 24-Pack",
        "price": 12.99,
        "asin": "B07HNBV23M"
      }
    }
  ],
  "processing_time_ms": 1250,
  "reorder_candidates": 1
}
```

### Place Order

```bash
POST /api/orders
Content-Type: application/json

{
  "user_id": "user_123",
  "product_id": "prod_water_001",
  "quantity": 1,
  "confirm": true,
  "delivery_address": {
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Order placed successfully with amazon!",
  "order": {
    "order_id": "ord_xyz789",
    "user_id": "user_123",
    "items": [
      {
        "product_id": "prod_water_001",
        "product_name": "Spring Water 24-Pack",
        "quantity": 1,
        "price": 12.99,
        "total": 12.99
      }
    ],
    "subtotal": 12.99,
    "tax": 0.94,
    "shipping": 0.00,
    "total": 13.93,
    "status": "confirmed",
    "vendor": "amazon",
    "vendor_order_id": "AMZ-A1B2C3D4E5F6"
  }
}
```

### User Preferences

```bash
# Get user preferences
GET /api/users/user_123/preferences

# Update notification threshold
POST /api/users/user_123/preferences/threshold
{
  "threshold": "low"  # Options: full, half, low, empty
}

# Block a product from auto-reorder
POST /api/users/user_123/blocked/prod_sunscreen_001

# Set preferred vendor
POST /api/users/user_123/preferences/vendor
{
  "vendor": "amazon"  # Options: amazon, walmart, instacart
}
```

## 📦 Data Models

### Product

```python
{
  "product_id": "prod_water_001",
  "name": "Spring Water 24-Pack",
  "category": "beverages",
  "detection_class": "water_bottle",
  "asin": "B07HNBV23M",
  "upc": "012000638602",
  "price": 12.99,
  "vendor": "amazon"
}
```

### Detection

```python
{
  "detection_id": "session_0",
  "class_name": "water_bottle",
  "confidence": 0.92,
  "bounding_box": {"x": 0.3, "y": 0.4, "width": 0.15, "height": 0.3},
  "state": "empty",  # full, half, low, empty, unknown
  "state_confidence": 0.88,
  "matched_product": {...}
}
```

### Order

```python
{
  "order_id": "ord_xyz789",
  "user_id": "user_123",
  "items": [...],
  "subtotal": 12.99,
  "tax": 0.94,
  "shipping": 0.00,
  "total": 13.93,
  "status": "confirmed",  # pending, confirmed, shipped, delivered, cancelled
  "vendor": "amazon",
  "vendor_order_id": "AMZ-A1B2C3D4E5F6",
  "created_at": "2025-10-25T12:00:00Z",
  "tracking_number": null
}
```

### User Preferences

```python
{
  "user_id": "user_123",
  "auto_reorder_enabled": true,
  "preferred_vendor": "amazon",
  "notification_threshold": "low",  # When to show reorder prompt
  "privacy_mode": true,  # Process CV on-device when possible
  "delivery_address": {...},
  "blocked_products": [],
  "favorite_products": []
}
```

## 🔧 Services

### 1. Vision AI Service (`vision_ai.py`)

Handles computer vision tasks:
- Object detection using Claude Vision API
- Product state classification (full/empty/low)
- Bounding box generation
- Confidence scoring

**Key Functions:**
- `detect_objects_from_image()` - Main detection function
- `analyze_product_state()` - Determine product fullness
- `should_prompt_reorder()` - Filter products needing reorder

### 2. Product Service (`product_service.py`)

Manages product catalog:
- Product database (in-memory for demo)
- Product search and filtering
- Detection class → Product matching
- Product recommendations

**Key Functions:**
- `get_product_by_id()`
- `search_products()`
- `get_product_by_detection_class()`
- `get_recommended_products()`

### 3. Order Service (`order_service.py`)

Handles order placement and tracking:
- Order placement with commerce APIs
- Tax and shipping calculations
- Order status tracking
- Order history and analytics

**Key Functions:**
- `place_order()` - Place order with vendor
- `track_order()` - Get tracking info
- `cancel_order()` - Cancel order
- `get_user_spending_summary()` - Analytics

### 4. User Service (`user_service.py`)

Manages user data:
- User profiles and preferences
- Privacy settings
- Blocked/favorite products
- Delivery addresses

**Key Functions:**
- `get_or_create_user()`
- `update_user_preferences()`
- `block_product()` / `add_favorite_product()`
- `set_notification_threshold()`

## 🧪 Testing

### Manual Testing with cURL

```bash
# Health check
curl http://localhost:8000/api/health

# List products
curl http://localhost:8000/api/products

# Get specific product
curl http://localhost:8000/api/products/prod_water_001

# Create user
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "email": "test@example.com", "name": "Test User"}'

# Get user preferences
curl http://localhost:8000/api/users/test_user/preferences
```

### Testing with Python

```python
import requests
import base64

# Encode image
with open("test_image.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

# Detect objects
response = requests.post(
    "http://localhost:8000/api/detect",
    json={
        "image": image_b64,
        "user_id": "test_user",
        "confidence_threshold": 0.7,
    }
)

print(response.json())
```

## 🔐 Privacy & Security

### Privacy Features

1. **On-Device Processing**: `privacy_mode` allows users to opt for on-device CV when possible
2. **No Image Storage**: Images are processed in-memory and discarded immediately
3. **User Control**: Users can block products and disable auto-reorder
4. **Minimal Data**: Only product identifiers sent to backend (not video frames when privacy_mode enabled)

### Security Best Practices

- Use HTTPS in production
- Implement authentication (JWT, OAuth2)
- Rate limiting on detection endpoints
- Validate and sanitize all inputs
- Use environment variables for API keys
- Never commit `.env` files to git

## 🚀 Deployment

### Production Setup

1. **Use a production ASGI server**:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```

2. **Set up a reverse proxy** (nginx):
   ```nginx
   server {
       listen 80;
       server_name api.yourapp.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Use a real database** (PostgreSQL):
   - Replace in-memory dictionaries with SQLAlchemy models
   - Set up database migrations with Alembic

4. **Add monitoring**:
   - Sentry for error tracking
   - Prometheus for metrics
   - CloudWatch/DataDog for logs

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t auto-reorder-backend .
docker run -p 8000:8000 --env-file .env auto-reorder-backend
```

## 📊 Future Enhancements

### Planned Features

- [ ] **Real Database**: PostgreSQL/MongoDB integration
- [ ] **Authentication**: JWT-based user auth
- [ ] **Real Commerce APIs**: Integrate actual Amazon/Walmart APIs
- [ ] **ML Model Server**: Dedicated CV inference server
- [ ] **Webhooks**: Order status updates from vendors
- [ ] **Analytics Dashboard**: User spending insights
- [ ] **Subscription Orders**: Auto-reorder on schedule
- [ ] **Price Alerts**: Notify when prices drop
- [ ] **Barcode Scanning**: UPC/EAN lookup
- [ ] **Recipe Integration**: Suggest products based on recipes

### Scalability

- Redis caching for frequently accessed products
- Background task queue (Celery) for order processing
- CDN for product images
- Load balancing for multiple API instances
- Rate limiting and throttling

## 🐛 Troubleshooting

### Common Issues

**Import errors:**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**Anthropic API errors:**
- Check that `ANTHROPIC_API_KEY` is set in `.env`
- Verify API key is valid at https://console.anthropic.com
- Check API rate limits

**CORS errors from Spectacles:**
- CORS is configured to allow all origins in development
- In production, restrict to your Spectacles app domain

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact

For questions or support, reach out to the development team.

---

**Built with ❤️ for Snap Spectacles**
