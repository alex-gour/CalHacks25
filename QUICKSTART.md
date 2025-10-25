# 🚀 Quick Start Guide - Auto-Reorder System

Get your Spectacles Auto-Reorder backend running in 5 minutes!

## ⚡ Super Quick Start

```bash
# 1. Navigate to backend
cd fastapi-server

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API key
echo 'ANTHROPIC_API_KEY=your_key_here' > .env

# 4. Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Test it!
curl http://localhost:8000/api/health
```

Done! API is running at http://localhost:8000

## 📖 Documentation Quick Links

| What You Need | Document | Time |
|---------------|----------|------|
| **Install & Setup** | [SETUP.md](fastapi-server/SETUP.md) | 5 min |
| **API Reference** | [README.md](fastapi-server/README.md) | 15 min |
| **Spectacles Integration** | [SPECTACLES_INTEGRATION.md](SPECTACLES_INTEGRATION.md) | 30 min |
| **What Changed** | [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md) | 10 min |
| **Migration from Old System** | [fastapi-server/MIGRATION_GUIDE.md](fastapi-server/MIGRATION_GUIDE.md) | 10 min |

## 🎯 Test the API

### 1. Interactive Docs
Open in browser: **http://localhost:8000/docs**

Try these endpoints:
- `GET /api/health` - Health check
- `GET /api/products` - List products
- `POST /api/users` - Create test user

### 2. Quick Test Script

Save as `test_api.py`:
```python
import requests

BASE_URL = "http://localhost:8000/api"

# Test health
response = requests.get(f"{BASE_URL}/health")
print(f"✅ Health: {response.json()['status']}")

# List products
response = requests.get(f"{BASE_URL}/products")
products = response.json()
print(f"✅ Products: {products['total']} items")

# Create user
response = requests.post(f"{BASE_URL}/users", params={
    "user_id": "test_user_001",
    "email": "test@example.com",
    "name": "Test User"
})
print(f"✅ User created: {response.json()['user_id']}")

print("\n🎉 All tests passed!")
```

Run it:
```bash
python test_api.py
```

## 🔑 Key Endpoints

```bash
# Detect products in image
POST /api/detect
Body: {"image": "base64...", "user_id": "user_123"}

# List products
GET /api/products

# Get specific product
GET /api/products/prod_water_001

# Place order
POST /api/orders
Body: {"user_id": "...", "product_id": "...", "quantity": 1, "confirm": true}

# Get user preferences
GET /api/users/{user_id}/preferences

# Update notification threshold
POST /api/users/{user_id}/preferences/threshold
Body: {"threshold": "low"}
```

## 📁 Project Structure

```
fastapi-server/
├── app/
│   ├── main.py                 ← FastAPI app entry point
│   ├── api/
│   │   └── routes.py           ← 40+ API endpoints
│   ├── models/
│   │   └── schemas.py          ← Pydantic models
│   └── services/
│       ├── vision_ai.py        ← Object detection (Claude Vision)
│       ├── product_service.py  ← Product catalog (11 demo products)
│       ├── order_service.py    ← Order placement & tracking
│       ├── user_service.py     ← User management
│       └── legacy/             ← Old services (archived)
├── requirements.txt            ← Dependencies
├── README.md                   ← Full documentation
└── SETUP.md                    ← Setup instructions
```

## 🎨 What This System Does

```
┌─────────────────────────────────────────────────────────┐
│ 1. USER points Spectacles camera at products           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 2. VISION AI detects:                                   │
│    • Water bottle (empty) ← needs reorder!              │
│    • Sunscreen (low) ← needs reorder!                   │
│    • Coffee (full) ← no action                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 3. SYSTEM shows prompt:                                 │
│    "Water bottle is empty. Reorder for $12.99?"         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 4. USER confirms via:                                   │
│    • Voice: "Yes, order"                                │
│    • Gesture: Pinch button                              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│ 5. ORDER placed with Amazon/Walmart/Instacart           │
│    Order #AMZ-A1B2C3 confirmed! Arriving in 2-3 days.   │
└─────────────────────────────────────────────────────────┘
```

## 🔥 Cool Features

✨ **Smart Detection**: Knows difference between full, half, low, and empty

🎯 **Non-Invasive**: Only prompts when products are actually running low

🔒 **Privacy First**: User controls what gets detected and ordered

🛒 **Multi-Vendor**: Works with Amazon, Walmart, Instacart

📊 **Analytics**: Track spending, frequent products, order history

🎙️ **Voice & Gesture**: Hands-free confirmation

🚫 **Block Products**: Never show prompts for specific items

⭐ **Favorites**: Quick reorder frequently purchased items

## 🎓 Learn More

### For Backend Development
- [Full API Docs](fastapi-server/README.md)
- [Setup Instructions](fastapi-server/SETUP.md)
- [Service Architecture](REFACTOR_SUMMARY.md)

### For Frontend (Spectacles) Development
- [Integration Guide](SPECTACLES_INTEGRATION.md)
- [Spectacles Dev Guide](https://developers.snap.com/spectacles)
- Example TypeScript code included!

### For Understanding Changes
- [What Changed](REFACTOR_SUMMARY.md)
- [Migration from Old System](fastapi-server/MIGRATION_GUIDE.md)

## 💡 Next Steps

1. ✅ **Backend Running**: You're here!
2. 📱 **Integrate Spectacles**: Follow [SPECTACLES_INTEGRATION.md](SPECTACLES_INTEGRATION.md)
3. 🧪 **Test Detection**: Upload test images via `/api/detect`
4. 🎨 **Customize Products**: Add your own to `product_service.py`
5. 🚀 **Deploy**: Use Docker or cloud hosting
6. 🔐 **Add Auth**: Implement JWT tokens
7. 💾 **Add Database**: Migrate to PostgreSQL

## 🆘 Troubleshooting

**API not starting?**
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Try a different port
uvicorn app.main:app --reload --port 8080
```

**Import errors?**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Anthropic API errors?**
```bash
# Check your .env file
cat .env

# Verify API key at https://console.anthropic.com
```

## 🎉 You're Ready!

Your backend is now ready to power hands-free shopping with Spectacles!

**Next**: Open http://localhost:8000/docs and explore the API!

---

**Questions?** Check the full [README.md](fastapi-server/README.md) or the other guides in this repo.

