# 👓 Spectacles Integration Guide

This guide shows how to connect your Snap Spectacles lens to the Auto-Reorder backend API.

## Architecture Overview

### Option 1: Direct Backend Integration (Current)
```
Spectacles Lens (TypeScript)
    │
    ├─> Camera API: Capture product images
    ├─> Speech-to-Text: Voice confirmation ("yes", "order")
    ├─> Text-to-Speech: Audio feedback
    └─> HTTP Client: Send requests to backend
            │
            └─> FastAPI Backend
                ├─> POST /api/detect (image analysis)
                ├─> POST /api/orders (place order)
                └─> GET /api/users/{id}/preferences
```

### Option 2: Remote Service Gateway (Recommended by Snap)
```
Spectacles Lens (TypeScript)
    │
    ├─> Remote Service Gateway → AI APIs (OpenAI/Gemini for vision)
    └─> HTTP Client → FastAPI Backend (for orders, database)
```

**Why RSG?** Snap's Remote Service Gateway provides:
- ✅ Built-in authentication and security
- ✅ Automatic rate limiting
- ✅ Access to OpenAI, Gemini, Snap3D without managing API keys
- ✅ Optimized for Spectacles platform

**See:** `fastapi-server/REMOTE_SERVICE_GATEWAY.md` for hybrid setup guide

---

## 🎯 Character Limit Best Practices

**CRITICAL:** Spectacles AR displays have strict character limits:

| Display Context | Max Characters | Usage |
|----------------|---------------|-------|
| **General Response** | 300 chars | AI conversational responses |
| **Concise Answer** | 150 chars | Quick facts, product descriptions |
| **Summary Title** | 157 chars | Card headers |
| **Summary Content** | 785 chars | Detailed content cards |

Our backend automatically optimizes responses for these limits. See `app/utils/ar_optimization.py`.

---

## Step 1: Set Up Backend Connection

In your Lens Studio project, update the backend URL:

```typescript
// lens-studio/Assets/Scripts/Config.ts

export const API_CONFIG = {
    BASE_URL: "http://YOUR_IP:8000/api",  // Replace with your backend IP
    TIMEOUT: 30000,  // 30 seconds
};

// For ngrok deployment (recommended for testing):
// BASE_URL: "https://your-ngrok-id.ngrok.io/api"
```

## Step 2: Image Capture & Detection

Use the existing `CameraAPI.ts` to capture images:

```typescript
// lens-studio/Assets/Scripts/TS/DetectionController.ts

import { API_CONFIG } from "./Config";
import { HttpClient } from "./utils/HttpClient";

export class DetectionController {
    private httpClient: HttpClient;
    
    constructor() {
        this.httpClient = new HttpClient(API_CONFIG.BASE_URL);
    }
    
    async detectProducts(userId: string): Promise<DetectionResponse> {
        // Capture image from camera
        const texture = this.captureFrame();
        const base64Image = this.textureToBase64(texture);
        
        // Send to backend
        const response = await this.httpClient.post("/detect", {
            image: base64Image,
            user_id: userId,
            confidence_threshold: 0.7,
            return_matches: true,
        });
        
        return response;
    }
    
    private captureFrame(): Texture {
        // Get camera component
        const camera = this.getSceneObject().getComponent("Component.Camera");
        return camera.renderTarget.getTexture();
    }
    
    private textureToBase64(texture: Texture): string {
        // Convert texture to base64
        // Implementation depends on Lens Studio version
        // See CameraAPI.ts for reference
        return "base64_encoded_image";
    }
}

interface DetectionResponse {
    session_id: string;
    detections: Detection[];
    processing_time_ms: number;
    reorder_candidates: number;
}

interface Detection {
    detection_id: string;
    class_name: string;
    confidence: number;
    bounding_box: BoundingBox;
    state: "full" | "half" | "low" | "empty" | "unknown";
    state_confidence: number;
    matched_product?: Product;
}
```

## Step 3: Reorder Prompt UI

Show non-invasive prompts for low products:

```typescript
// lens-studio/Assets/Scripts/TS/ReorderPromptController.ts

export class ReorderPromptController {
    // @input SceneObject promptPanel
    // @input Component.Text promptText
    // @input SceneObject confirmButton
    
    private currentDetection: Detection | null = null;
    
    showPrompt(detection: Detection) {
        if (!detection.matched_product) return;
        
        this.currentDetection = detection;
        const product = detection.matched_product;
        
        // Update prompt text
        script.promptText.text = 
            `${product.name} is running ${detection.state}.\n` +
            `Reorder for $${product.price}?`;
        
        // Show panel with fade-in animation
        this.animateIn();
        
        // Auto-dismiss after 10 seconds
        script.createDelayedCallback(() => {
            this.dismiss();
        }, 10.0);
    }
    
    private animateIn() {
        script.promptPanel.enabled = true;
        // Add fade-in animation here
    }
    
    private dismiss() {
        // Add fade-out animation
        script.promptPanel.enabled = false;
        this.currentDetection = null;
    }
}
```

## Step 4: Voice Confirmation

Integrate with existing `SpeechToText.ts`:

```typescript
// lens-studio/Assets/Scripts/TS/VoiceConfirmationController.ts

import { SpeechToText } from "./SpeechToText";

export class VoiceConfirmationController {
    private speechToText: SpeechToText;
    private orderController: OrderController;
    
    constructor() {
        this.speechToText = new SpeechToText();
        this.setupVoiceListeners();
    }
    
    private setupVoiceListeners() {
        this.speechToText.onTranscription.add((text: string) => {
            const command = text.toLowerCase().trim();
            
            if (command.includes("yes") || 
                command.includes("order") || 
                command.includes("reorder")) {
                this.confirmOrder();
            } else if (command.includes("no") || 
                       command.includes("cancel") || 
                       command.includes("dismiss")) {
                this.dismissPrompt();
            }
        });
    }
    
    private async confirmOrder() {
        if (!this.currentDetection?.matched_product) return;
        
        const product = this.currentDetection.matched_product;
        const result = await this.orderController.placeOrder(
            this.userId,
            product.product_id,
            1  // quantity
        );
        
        if (result.success) {
            this.showConfirmation(result.order);
        } else {
            this.showError(result.error);
        }
    }
}
```

## Step 5: Order Placement

```typescript
// lens-studio/Assets/Scripts/TS/OrderController.ts

import { HttpClient } from "./utils/HttpClient";

export class OrderController {
    private httpClient: HttpClient;
    
    async placeOrder(
        userId: string, 
        productId: string, 
        quantity: number
    ): Promise<OrderResponse> {
        // Get user's saved address
        const address = await this.getUserAddress(userId);
        
        // Place order
        const response = await this.httpClient.post("/orders", {
            user_id: userId,
            product_id: productId,
            quantity: quantity,
            confirm: true,
            delivery_address: address,
        });
        
        return response;
    }
    
    async getUserAddress(userId: string): Promise<Address> {
        const response = await this.httpClient.get(`/users/${userId}/address`);
        return response.address;
    }
}

interface OrderResponse {
    success: boolean;
    message: string;
    order?: Order;
    error?: string;
}
```

## Step 6: User Preferences

Allow users to configure settings:

```typescript
// lens-studio/Assets/Scripts/TS/SettingsController.ts

export class SettingsController {
    private httpClient: HttpClient;
    
    async setNotificationThreshold(
        userId: string, 
        threshold: "full" | "half" | "low" | "empty"
    ) {
        await this.httpClient.post(
            `/users/${userId}/preferences/threshold`,
            { threshold }
        );
    }
    
    async setPreferredVendor(userId: string, vendor: string) {
        await this.httpClient.post(
            `/users/${userId}/preferences/vendor`,
            { vendor }
        );
    }
    
    async blockProduct(userId: string, productId: string) {
        await this.httpClient.post(
            `/users/${userId}/blocked/${productId}`
        );
    }
}
```

## Step 7: Main Controller

Orchestrate everything:

```typescript
// lens-studio/Assets/Scripts/TS/AutoReorderController.ts

export class AutoReorderController {
    // @input string userId
    
    private detectionController: DetectionController;
    private promptController: ReorderPromptController;
    private voiceController: VoiceConfirmationController;
    private orderController: OrderController;
    
    private isScanning: boolean = false;
    private scanInterval: number = 5000;  // 5 seconds
    
    onStart() {
        this.detectionController = new DetectionController();
        this.promptController = new ReorderPromptController();
        this.voiceController = new VoiceConfirmationController();
        this.orderController = new OrderController();
        
        // Start periodic scanning
        this.startScanning();
    }
    
    startScanning() {
        this.isScanning = true;
        this.scan();
    }
    
    async scan() {
        if (!this.isScanning) return;
        
        try {
            // Detect products
            const result = await this.detectionController.detectProducts(
                script.userId
            );
            
            // Check for reorder candidates
            if (result.reorder_candidates > 0) {
                const lowProducts = result.detections.filter(d => 
                    d.state === "low" || d.state === "empty"
                );
                
                // Show prompt for first low product
                if (lowProducts.length > 0) {
                    this.promptController.showPrompt(lowProducts[0]);
                }
            }
        } catch (error) {
            print(`[AutoReorder] Scan error: ${error}`);
        }
        
        // Schedule next scan
        script.createDelayedCallback(() => {
            this.scan();
        }, this.scanInterval / 1000);
    }
    
    stopScanning() {
        this.isScanning = false;
    }
}
```

## Testing the Integration

### 1. Start Backend

```bash
cd fastapi-server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Use ngrok for Testing

```bash
# Install ngrok: https://ngrok.com
ngrok http 8000
```

This gives you a public URL like `https://abc123.ngrok.io`

### 3. Update Lens Studio Config

```typescript
export const API_CONFIG = {
    BASE_URL: "https://abc123.ngrok.io/api",
};
```

### 4. Deploy to Spectacles

1. Pair your Spectacles in Lens Studio
2. Send lens to device
3. Point camera at products
4. Check console logs for API responses

## Debugging Tips

### Check API Connectivity

```typescript
async testConnection() {
    try {
        const response = await this.httpClient.get("/health");
        print(`API Status: ${response.status}`);
    } catch (error) {
        print(`Connection failed: ${error}`);
    }
}
```

### Log Detection Results

```typescript
const result = await this.detectionController.detectProducts(userId);
print(`Detected ${result.detections.length} objects`);
result.detections.forEach(d => {
    print(`- ${d.class_name}: ${d.state} (${d.confidence})`);
});
```

### Monitor Network Requests

Use Lens Studio's Logger panel to view:
- HTTP request URLs
- Response status codes
- Error messages

## Performance Optimization

### 1. Debounce Detections

Don't send frames too frequently:

```typescript
private lastDetectionTime: number = 0;
private minDetectionInterval: number = 3000;  // 3 seconds

async detectIfNeeded() {
    const now = getTime() * 1000;
    if (now - this.lastDetectionTime < this.minDetectionInterval) {
        return;  // Skip detection
    }
    
    this.lastDetectionTime = now;
    await this.detectProducts();
}
```

### 2. Cache Results

Store detection results temporarily:

```typescript
private cachedDetections: Map<string, CachedResult> = new Map();

interface CachedResult {
    detection: Detection;
    timestamp: number;
}
```

### 3. Compress Images

Reduce image size before sending:

```typescript
private compressImage(texture: Texture, quality: number = 0.7): string {
    // Resize to max 1024x1024
    // Apply JPEG compression
    // Convert to base64
    return compressed_base64;
}
```

## Privacy Considerations

### 1. On-Device Mode

When privacy mode is enabled, only send product IDs (not images):

```typescript
if (userPreferences.privacy_mode) {
    // Use on-device ML model (future feature)
    // Only send detected class names to backend
    const response = await this.httpClient.post("/detect/by-class", {
        class_name: "water_bottle",
        user_id: userId,
    });
}
```

### 2. Secure Storage

Store user data securely:

```typescript
const storage = global.persistentStorageSystem.store;
storage.set("user_id", userId);
storage.set("api_key", encrypted_key);
```

## Next Steps

1. **Customize UI**: Design your own prompt panels and animations
2. **Add Analytics**: Track detection accuracy and order success rates
3. **Implement Feedback**: Let users report false detections
4. **Add Tutorials**: First-time user onboarding
5. **Multi-Product**: Support ordering multiple items at once

## Resources

- [Lens Studio API Docs](https://developers.snap.com/lens-studio/api/lens-scripting/)
- [Spectacles Interaction Kit](https://developers.snap.com/spectacles/spectacles-frameworks/spectacles-interaction-kit/)
- [Backend API Docs](http://localhost:8000/docs)

---

**Questions?** Check the main README or create an issue in the repository.

