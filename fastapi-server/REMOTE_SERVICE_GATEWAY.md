# 🌐 Remote Service Gateway Integration

## Overview

**Remote Service Gateway (RSG)** is Snap's recommended way to connect Spectacles lenses to external APIs securely. Instead of calling your FastAPI backend directly, you can route requests through Snap's gateway for enhanced security and compliance.

## Architecture Options

### Option 1: Direct FastAPI Connection (Current Setup)
```
Spectacles → FastAPI Backend → AI APIs
```

**Pros:**
- Full control over backend logic
- Lower latency
- Easier debugging
- More flexible

**Cons:**
- Requires exposing your backend publicly
- You manage authentication and rate limiting
- API keys exposed to backend

### Option 2: Remote Service Gateway (Recommended by Snap)
```
Spectacles → Remote Service Gateway → AI APIs (OpenAI, Gemini, etc.)
```

**Pros:**
- Snap handles authentication and security
- No need to expose your backend
- Built-in rate limiting
- Compliant with Snap's security policies

**Cons:**
- Limited to supported APIs (OpenAI, Gemini, Snap3D, DeepSeek)
- Less flexibility
- Cannot use custom backend logic

### Option 3: Hybrid Approach (Best of Both Worlds)
```
Spectacles → {
  → Remote Service Gateway (for AI APIs)
  → FastAPI Backend (for custom logic, database, orders)
}
```

**Use RSG for:**
- OpenAI API calls (vision, chat)
- Gemini API calls
- Snap3D generation

**Use FastAPI Backend for:**
- Product database queries
- Order placement
- User preference management
- Custom business logic

---

## Setting Up Remote Service Gateway

### 1. Install the RSG Plugin

1. Open Lens Studio
2. Go to **Asset Library** → **Spectacles** section
3. Install **Remote Service Gateway Token Generator**
4. Restart Lens Studio if prompted

### 2. Generate API Token

1. Go to **Windows** → **Remote Service Gateway Token**
2. Click **Generate Token**
3. Copy the generated token
4. **Important:** Keep this token secure and don't commit to git

### 3. Configure in Your Lens

1. Create a Scene Object named `RemoteServiceGatewayCredentials`
2. Add a script component (or use existing RSG setup)
3. Paste your API token in the Inspector
4. The token enables access to:
   - OpenAI API (Chat, Vision, Realtime, Speech)
   - Gemini API (Model inference, Live API)
   - Snap3D API (Text-to-3D generation)
   - DeepSeek API (Advanced reasoning)

---

## Hybrid Integration Example

### Using RSG for Vision AI

```typescript
// lens-studio/Assets/Scripts/TS/RSGVisionDetection.ts

import { Gemini } from "RemoteServiceGateway.lspkg/HostedExternal/Gemini";

export class RSGVisionDetection {
    async detectProducts(imageTexture: Texture): Promise<DetectionResult> {
        // Use Gemini directly through RSG
        const base64Image = this.textureToBase64(imageTexture);
        
        const response = await Gemini.generateContent({
            model: 'gemini-2.0-flash-exp',
            contents: [{
                parts: [
                    { text: this.getDetectionPrompt() },
                    { 
                        inlineData: {
                            mimeType: "image/jpeg",
                            data: base64Image
                        }
                    }
                ]
            }]
        });
        
        return this.parseGeminiResponse(response);
    }
    
    private getDetectionPrompt(): string {
        return `Analyze this image and detect household products.
For each product, determine:
1. Product class (water_bottle, sunscreen, etc.)
2. State (full, half, low, empty)
3. Confidence (0-1)

Return JSON: {"detections": [{"class": "...", "state": "...", "confidence": 0.9}]}

CRITICAL: Response must be under 300 characters for AR display.`;
    }
}
```

### Using FastAPI Backend for Orders

```typescript
// lens-studio/Assets/Scripts/TS/OrderController.ts

import { HttpClient } from "./utils/HttpClient";

export class OrderController {
    private httpClient: HttpClient;
    private backendUrl = "https://your-backend.com/api";
    
    async placeOrder(
        userId: string,
        productId: string,
        quantity: number
    ): Promise<OrderResponse> {
        // Use direct FastAPI backend for custom logic
        const request = new Request(`${this.backendUrl}/orders`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: userId,
                product_id: productId,
                quantity: quantity,
                confirm: true
            })
        });
        
        const response = await this.httpClient.fetch(request);
        return await response.json();
    }
}
```

### Hybrid Controller

```typescript
// lens-studio/Assets/Scripts/TS/HybridAutoReorderController.ts

import { RSGVisionDetection } from "./RSGVisionDetection";
import { OrderController } from "./OrderController";
import { ProductService } from "./ProductService";

export class HybridAutoReorderController {
    private visionDetection: RSGVisionDetection;
    private orderController: OrderController;
    private productService: ProductService;
    
    async detectAndPromptReorder(userId: string) {
        // 1. Use RSG for vision detection
        const cameraTexture = this.captureFrame();
        const detections = await this.visionDetection.detectProducts(cameraTexture);
        
        // 2. Use FastAPI backend for product matching
        for (const detection of detections.detections) {
            const product = await this.productService.getProductByClass(
                detection.class
            );
            
            if (product && (detection.state === "low" || detection.state === "empty")) {
                // 3. Show prompt to user
                const confirmed = await this.showReorderPrompt(product);
                
                if (confirmed) {
                    // 4. Use FastAPI backend for order placement
                    await this.orderController.placeOrder(
                        userId,
                        product.product_id,
                        1
                    );
                }
            }
        }
    }
}
```

---

## Character Limit Best Practices

Based on Snap's sample projects, AR text displays have strict character limits:

### Display Constraints

| Context | Character Limit | Purpose |
|---------|----------------|---------|
| **Summary Cards** | 750-785 chars | Detailed educational content |
| **Card Titles** | 150-157 chars | Brief descriptive headers |
| **AR Responses** | 300 chars max | General conversation |
| **Concise Answers** | 150 chars max | Quick facts |

### Backend Response Optimization

Update your FastAPI endpoints to respect these limits:

```python
# fastapi-server/app/services/vision_ai.py

def optimize_for_ar_display(text: str, max_chars: int = 300) -> str:
    """
    Optimize response text for AR display constraints
    
    Args:
        text: Original response text
        max_chars: Maximum characters (default 300 for AR)
        
    Returns:
        Truncated and optimized text
    """
    if len(text) <= max_chars:
        return text
    
    # Truncate at sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')
    
    last_sentence = max(last_period, last_exclamation, last_question)
    
    if last_sentence > 0:
        return truncated[:last_sentence + 1]
    
    # Fallback: truncate at word boundary
    last_space = truncated.rfind(' ')
    return truncated[:last_space] + "..."


# Update detection response
async def detect_objects_from_image(...) -> DetectionResponse:
    # ... existing code ...
    
    # Add AR-optimized description
    for detection in detections:
        if detection.matched_product:
            product = detection.matched_product
            # Create concise description (under 150 chars)
            product.description = optimize_for_ar_display(
                product.description or product.name,
                max_chars=150
            )
    
    return response
```

---

## Environment Variables Update

Add RSG configuration to your `.env` file:

```env
# Backend Configuration
ANTHROPIC_API_KEY=your_anthropic_key_here
AMAZON_API_KEY=your_amazon_key_here

# Remote Service Gateway (Optional)
USE_REMOTE_SERVICE_GATEWAY=false  # Set to true if using hybrid approach
RSG_ENDPOINT=https://api.snapchat.com/rsg  # RSG endpoint if needed

# Response Optimization
MAX_AR_RESPONSE_LENGTH=300  # Character limit for AR display
ENABLE_RESPONSE_OPTIMIZATION=true  # Auto-truncate responses
```

---

## Security Considerations

### If Using Direct FastAPI Connection

1. **Use HTTPS only** - Never expose HTTP endpoints
2. **API Key Authentication** - Implement JWT tokens
3. **Rate Limiting** - Prevent abuse (e.g., 100 requests/minute per user)
4. **CORS Configuration** - Restrict to Spectacles domains
5. **Input Validation** - Sanitize all user inputs

```python
# fastapi-server/app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if not is_valid_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return token

@app.post("/api/detect")
@limiter.limit("10/minute")
async def detect_objects(
    request: DetectionRequest,
    token: str = Depends(verify_token)
):
    # Protected endpoint with rate limiting
    pass
```

### If Using Remote Service Gateway

RSG handles most security concerns automatically:
- ✅ Authentication managed by Snap
- ✅ Rate limiting built-in
- ✅ HTTPS enforced
- ✅ Token rotation handled
- ✅ Compliance with Snap policies

---

## Migration Guide: Direct to Hybrid

### Step 1: Keep FastAPI Backend

Your current backend remains valuable for:
- Product catalog management
- Order placement and tracking
- User preferences
- Custom business logic

### Step 2: Add RSG for AI

Offload AI vision to RSG:
- Less latency (Snap's infrastructure)
- Better security
- Automatic scaling

### Step 3: Update Frontend Integration

```typescript
// Old: Everything through FastAPI
const response = await httpClient.post("/api/detect", {...});

// New: Hybrid approach
// Use RSG for vision
const detections = await rsgVisionDetection.detectProducts(image);

// Use FastAPI for matching and orders
const products = await backendService.matchProducts(detections);
const order = await backendService.placeOrder(product);
```

---

## Testing RSG Integration

### 1. Test in Lens Studio Preview

```typescript
// Enable debug logging
print(`[RSG] Using Remote Service Gateway: ${useRSG}`);
print(`[RSG] Backend URL: ${backendUrl}`);

// Test both paths
const visionResult = await rsgVisionDetection.detectProducts(testImage);
print(`[RSG] Vision result: ${JSON.stringify(visionResult)}`);

const orderResult = await orderController.placeOrder(testUserId, productId, 1);
print(`[Backend] Order result: ${JSON.stringify(orderResult)}`);
```

### 2. Monitor Performance

| Metric | RSG (AI) | FastAPI (Orders) |
|--------|----------|------------------|
| Latency | ~1-2s | ~500ms |
| Cost | Snap covers | Your infra |
| Rate Limits | Automatic | Self-managed |
| Security | Snap managed | Self-managed |

---

## Best Practices Summary

✅ **DO:**
- Use RSG for AI/ML tasks (OpenAI, Gemini)
- Use FastAPI for custom business logic
- Optimize responses for 150-300 char limits
- Test both integration paths thoroughly
- Document which APIs use RSG vs direct backend

❌ **DON'T:**
- Expose API keys in Lens Studio scripts
- Exceed character limits (breaks AR display)
- Mix RSG and direct calls for the same API
- Forget to handle offline/network errors gracefully

---

## Support & Resources

- **RSG Documentation**: https://developers.snap.com/spectacles/about-spectacles-features/apis/remoteservice-gateway
- **Lens Studio API**: https://developers.snap.com/lens-studio/api/
- **Sample Projects**: Check `Context/Spectacles-Sample/` for working examples

---

**Need Help?** Check the sample projects in your `Context` folder:
- `AI Playground` - RSG with OpenAI/Gemini
- `Agentic Playground` - Advanced agent system with RSG

Your backend is now ready for both direct and RSG-based integrations! 🚀

