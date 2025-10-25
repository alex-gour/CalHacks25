# 🔄 Migration Guide: From Old System to Auto-Reorder

## Quick Migration Checklist

- [x] Update `schemas.py` with new models
- [x] Create `vision_ai.py` for object detection
- [x] Create `product_service.py` for product catalog
- [x] Create `order_service.py` for commerce integration
- [x] Create `user_service.py` for user management
- [x] Refactor `routes.py` with new endpoints
- [x] Update `requirements.txt`
- [x] Move old services to `legacy/` folder
- [x] Create comprehensive documentation

## API Endpoint Migration

### Removed Endpoints
These endpoints are no longer available:

```
❌ POST /api/orchestrate
❌ POST /api/find_pharmacy
❌ POST /api/find_restroom
❌ POST /api/find_healthcare_facilities
❌ POST /api/find_shelter
❌ POST /api/summarize
```

### New Endpoints
Use these instead:

```
✅ POST /api/detect              → Detect products in images
✅ GET  /api/products            → Browse product catalog
✅ POST /api/orders              → Place orders
✅ GET  /api/users/{id}          → Get user profile
✅ PUT  /api/users/{id}/preferences → Update settings
```

## Code Migration Examples

### Before: Orchestration Request
```python
# OLD CODE - NO LONGER WORKS
response = requests.post("http://localhost:8000/api/orchestrate", json={
    "user_prompt": "I need help",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "image_surroundings": base64_image
})
```

### After: Detection Request
```python
# NEW CODE
response = requests.post("http://localhost:8000/api/detect", json={
    "image": base64_image,
    "user_id": "user_123",
    "confidence_threshold": 0.7,
    "return_matches": True
})

# Check for products needing reorder
detections = response.json()["detections"]
for detection in detections:
    if detection["state"] in ["low", "empty"]:
        product = detection["matched_product"]
        print(f"{product['name']} needs reordering!")
```

## Environment Variables

### Before
```env
ANTHROPIC_API_KEY=xxx
```

### After
```env
# Required
ANTHROPIC_API_KEY=xxx

# Optional (for production)
AMAZON_API_KEY=xxx
WALMART_API_KEY=xxx
INSTACART_API_KEY=xxx
```

## Database Schema

### Before: No Database
The old system had no persistent storage.

### After: Three In-Memory Databases

**Products**:
```python
PRODUCT_DATABASE: Dict[str, Product]
# Keys: "prod_water_001", "prod_sunscreen_001", etc.
```

**Orders**:
```python
ORDER_DATABASE: Dict[str, Order]
# Keys: "ord_xyz789", etc.
```

**Users**:
```python
USER_DATABASE: Dict[str, UserProfile]
# Keys: "user_123", "demo_user_001", etc.
```

## Testing Your Migration

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-25T12:00:00Z"
}
```

### 2. List Products
```bash
curl http://localhost:8000/api/products
```

Expected: 11 demo products

### 3. Create Test User
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "email": "test@example.com"}'
```

### 4. Test Detection (Mock)
Use the interactive docs at http://localhost:8000/docs

## Rollback Plan

If you need to rollback to the old system:

1. **Restore old services:**
   ```bash
   cd app/services
   cp legacy/*.py .
   ```

2. **Restore old routes.py:**
   ```bash
   git checkout HEAD~1 app/api/routes.py
   ```

3. **Restore old requirements.txt:**
   ```bash
   git checkout HEAD~1 requirements.txt
   pip install -r requirements.txt
   ```

## Breaking Changes

### 1. Request Format
**Before**: `OrchestrationRequest`
```json
{
  "user_prompt": "...",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "image_surroundings": "base64..."
}
```

**After**: `DetectionRequest`
```json
{
  "image": "base64...",
  "user_id": "user_123",
  "confidence_threshold": 0.7,
  "return_matches": true
}
```

### 2. Response Format
**Before**: Text response
```json
{
  "sessionId": "abc-123",
  "response": "Here is some advice..."
}
```

**After**: Structured detection
```json
{
  "session_id": "abc-123",
  "detections": [
    {
      "class_name": "water_bottle",
      "state": "empty",
      "confidence": 0.92,
      "matched_product": {...}
    }
  ],
  "processing_time_ms": 1250
}
```

### 3. No More Location Services
The new system doesn't use GPS coordinates. Instead, it uses:
- **Computer Vision**: Detect what user is looking at
- **User Preferences**: Saved delivery addresses
- **Product Database**: Catalog of items

## Feature Comparison

| Feature | Old System | New System |
|---------|------------|------------|
| **Primary Use Case** | Homeless assistance | Hands-free shopping |
| **Input** | Text + GPS | Camera + Voice |
| **AI Processing** | Claude text | Claude Vision |
| **Location Services** | ✅ (shelters, pharmacies) | ❌ (not needed) |
| **E-commerce** | ❌ | ✅ (orders, tracking) |
| **User Profiles** | ❌ | ✅ (preferences, history) |
| **Product Catalog** | ❌ | ✅ (11 demo products) |
| **State Detection** | ❌ | ✅ (full/empty analysis) |
| **Privacy Controls** | ❌ | ✅ (privacy mode, blocking) |

## Support

Need help with migration?
1. Check [README.md](README.md) for API documentation
2. See [SETUP.md](SETUP.md) for installation
3. Review [SPECTACLES_INTEGRATION.md](../SPECTACLES_INTEGRATION.md) for frontend
4. Check [REFACTOR_SUMMARY.md](../REFACTOR_SUMMARY.md) for complete changes

---

**Migration Complete! 🎉**

