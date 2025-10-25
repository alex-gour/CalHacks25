/**
 * AutoReorderController.ts
 * 
 * Main controller for hands-free auto-reorder system using Remote Service Gateway
 * 
 * Features:
 * - Product detection using Gemini via RSG (no backend API keys needed!)
 * - Voice/gesture confirmation
 * - Order placement via backend API
 * - User preferences management
 * 
 * Setup:
 * 1. Generate RSG token in Lens Studio (Windows → Remote Service Gateway Token)
 * 2. Assign token to RemoteServiceGatewayCredentials in scene
 * 3. Update BACKEND_URL below with your backend address
 */

import { Gemini } from "LensStudio:RemoteServiceModule/HostedExternal/Gemini";

@component
export class AutoReorderController extends BaseScriptComponent {
    // ========================================================================
    // CONFIGURATION - UPDATE THESE!
    // ========================================================================
    
    private BACKEND_URL = "http://YOUR_COMPUTER_IP:8000/api";  // TODO: Update with your backend IP
    // Example: "http://192.168.1.100:8000/api" or "https://your-ngrok-url.ngrok.io/api"
    
    private USER_ID = "spectacles_user_001";  // TODO: Update with actual user ID
    
    // ========================================================================
    // SCRIPT INPUTS
    // ========================================================================
    
    @input
    @hint("Camera texture provider for capturing frames")
    cameraTexture: Texture;
    
    @input
    @hint("Internet/Remote Service Module for HTTP requests")
    httpModule: RemoteServiceModule;
    
    @input
    @hint("Text component for displaying prompts")
    promptText: Text;
    
    @input
    @hint("Scene object for prompt panel (enable/disable)")
    promptPanel: SceneObject;
    
    @input
    @hint("Button for confirming order")
    confirmButton: SceneObject;
    
    @input
    @hint("Button for dismissing prompt")
    dismissButton: SceneObject;
    
    @input
    @hint("Enable debug logging")
    enableDebug: boolean = true;
    
    @input
    @hint("Scan interval in seconds (5 = scan every 5 seconds)")
    scanInterval: number = 5.0;
    
    @input
    @hint("Minimum confidence threshold for detections (0-1)")
    confidenceThreshold: number = 0.7;
    
    // ========================================================================
    // PRIVATE STATE
    // ========================================================================
    
    private isScanning: boolean = false;
    private currentDetection: any = null;
    private cameraModule: CameraModule;
    private lastScanTime: number = 0;
    
    // ========================================================================
    // LIFECYCLE
    // ========================================================================
    
    onAwake() {
        this.log("AutoReorderController initialized");
        this.cameraModule = require("LensStudio:CameraModule");
        
        // Hide prompt initially
        if (this.promptPanel) {
            this.promptPanel.enabled = false;
        }
        
        // Setup button interactions
        this.setupButtons();
    }
    
    /**
     * Call this to start scanning for products
     * Recommended: Trigger via voice command or hand gesture
     */
    startScanning() {
        this.log("Starting product scanning...");
        this.isScanning = true;
        this.scan();
    }
    
    /**
     * Call this to stop scanning
     */
    stopScanning() {
        this.log("Stopping product scanning");
        this.isScanning = false;
    }
    
    // ========================================================================
    // DETECTION - Using Gemini via Remote Service Gateway
    // ========================================================================
    
    private async scan() {
        if (!this.isScanning) return;
        
        const currentTime = getTime();
        if (currentTime - this.lastScanTime < this.scanInterval) {
            // Schedule next scan
            this.createDelayedCallbackEvent(() => this.scan(), 1.0);
            return;
        }
        
        this.lastScanTime = currentTime;
        this.log("Scanning for products...");
        
        try {
            // Capture frame from camera
            const base64Image = await this.captureFrameBase64();
            
            // Detect products using Gemini via RSG
            const detections = await this.detectProductsViaRSG(base64Image);
            
            // Check for low/empty products
            const needsReorder = detections.filter((d: any) => 
                (d.state === "low" || d.state === "empty") && 
                d.confidence >= this.confidenceThreshold
            );
            
            if (needsReorder.length > 0) {
                this.log(`Found ${needsReorder.length} products needing reorder`);
                
                // Match with backend product database
                const product = await this.matchProduct(needsReorder[0].class_name);
                
                if (product) {
                    this.showReorderPrompt(needsReorder[0], product);
                }
            }
            
        } catch (error) {
            this.log(`Scan error: ${error}`, "error");
        }
        
        // Schedule next scan
        this.createDelayedCallbackEvent(() => this.scan(), this.scanInterval);
    }
    
    /**
     * Detect products using Gemini via Remote Service Gateway
     * No API keys needed - RSG handles authentication!
     */
    private async detectProductsViaRSG(base64Image: string): Promise<any[]> {
        this.log("Calling Gemini via RSG for product detection...");
        
        const prompt = `Analyze this image and detect household products.
For each product, determine:
1. class_name: Product type (water_bottle, sunscreen, etc.)
2. state: Fullness (full, half, low, empty)
3. confidence: Detection confidence (0-1)

Common products: water_bottle, sunscreen, lotion, shampoo, soap, laundry_detergent, dish_soap, coffee_container, milk_carton, cereal_box, toothpaste, deodorant

Return ONLY valid JSON (no markdown):
{"detections": [{"class_name": "water_bottle", "state": "low", "confidence": 0.9}]}`;
        
        const response = await Gemini.generateContent({
            model: "gemini-2.0-flash-exp",
            contents: [{
                parts: [
                    { text: prompt },
                    {
                        inlineData: {
                            mimeType: "image/jpeg",
                            data: base64Image
                        }
                    }
                ]
            }]
        });
        
        // Parse response
        const responseText = response.text || "";
        this.log(`Gemini response: ${responseText.substring(0, 200)}...`);
        
        try {
            // Extract JSON from response (handle markdown code blocks)
            let jsonText = responseText;
            const jsonMatch = responseText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                jsonText = jsonMatch[0];
            }
            
            const result = JSON.parse(jsonText);
            return result.detections || [];
        } catch (e) {
            this.log(`Failed to parse Gemini response: ${e}`, "error");
            return [];
        }
    }
    
    // ========================================================================
    // BACKEND INTEGRATION - Products & Orders
    // ========================================================================
    
    /**
     * Match detected product class to backend product database
     */
    private async matchProduct(className: string): Promise<any> {
        this.log(`Matching product class: ${className}`);
        
        try {
            const request = new Request(`${this.BACKEND_URL}/products/class/${className}`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json"
                }
            });
            
            const response = await this.httpModule.fetch(request);
            const data = JSON.parse(response.body);
            
            if (data.products && data.products.length > 0) {
                return data.products[0];
            }
            
            return null;
        } catch (error) {
            this.log(`Product match error: ${error}`, "error");
            return null;
        }
    }
    
    /**
     * Place order via backend API
     */
    private async placeOrder(productId: string, quantity: number = 1): Promise<any> {
        this.log(`Placing order for product: ${productId}`);
        
        try {
            const request = new Request(`${this.BACKEND_URL}/orders`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    user_id: this.USER_ID,
                    product_id: productId,
                    quantity: quantity,
                    confirm: true
                })
            });
            
            const response = await this.httpModule.fetch(request);
            const result = JSON.parse(response.body);
            
            this.log(`Order result: ${result.success ? "SUCCESS" : "FAILED"}`);
            return result;
            
        } catch (error) {
            this.log(`Order error: ${error}`, "error");
            return { success: false, error: String(error) };
        }
    }
    
    // ========================================================================
    // UI - Reorder Prompt
    // ========================================================================
    
    private showReorderPrompt(detection: any, product: any) {
        this.currentDetection = detection;
        
        if (!this.promptPanel || !this.promptText) {
            this.log("Prompt UI not configured", "error");
            return;
        }
        
        // Update prompt text (keep under 150 chars for AR display)
        const promptMessage = `${product.name} is ${detection.state}. Reorder for $${product.price.toFixed(2)}?`;
        this.promptText.text = promptMessage;
        
        // Show prompt
        this.promptPanel.enabled = true;
        
        this.log(`Showing prompt: ${promptMessage}`);
        
        // Auto-dismiss after 10 seconds
        this.createDelayedCallbackEvent(() => {
            if (this.currentDetection === detection) {
                this.dismissPrompt();
            }
        }, 10.0);
    }
    
    private dismissPrompt() {
        if (this.promptPanel) {
            this.promptPanel.enabled = false;
        }
        this.currentDetection = null;
        this.log("Prompt dismissed");
    }
    
    private async confirmOrder() {
        if (!this.currentDetection) {
            this.log("No current detection to order", "error");
            return;
        }
        
        this.log("Order confirmed by user");
        
        // Get product from backend
        const product = await this.matchProduct(this.currentDetection.class_name);
        
        if (product) {
            // Place order
            const result = await this.placeOrder(product.product_id, 1);
            
            if (result.success) {
                // Show success message
                if (this.promptText) {
                    this.promptText.text = `Order placed! ID: ${result.order.order_id.substring(0, 8)}`;
                }
                
                // Dismiss after 3 seconds
                this.createDelayedCallbackEvent(() => this.dismissPrompt(), 3.0);
            } else {
                // Show error
                if (this.promptText) {
                    this.promptText.text = "Order failed. Please try again.";
                }
                
                this.createDelayedCallbackEvent(() => this.dismissPrompt(), 3.0);
            }
        }
        
        this.currentDetection = null;
    }
    
    // ========================================================================
    // BUTTON SETUP
    // ========================================================================
    
    private setupButtons() {
        // Confirm button
        if (this.confirmButton) {
            const interactable = this.confirmButton.getComponent("Component.InteractionComponent");
            if (interactable) {
                // Add tap event (you'll need to set this up in Inspector)
                // interactable.onTap.add(() => this.confirmOrder());
            }
        }
        
        // Dismiss button
        if (this.dismissButton) {
            const interactable = this.dismissButton.getComponent("Component.InteractionComponent");
            if (interactable) {
                // Add tap event
                // interactable.onTap.add(() => this.dismissPrompt());
            }
        }
    }
    
    // ========================================================================
    // CAMERA UTILITIES
    // ========================================================================
    
    private async captureFrameBase64(): Promise<string> {
        if (!this.cameraTexture) {
            throw new Error("Camera texture not configured");
        }
        
        // Get texture data
        const texture = this.cameraTexture;
        
        // Convert to base64 (simplified - actual implementation depends on Lens Studio version)
        // For production, you may need to use ProceduralTextureProvider
        const width = texture.getWidth();
        const height = texture.getHeight();
        
        // Note: This is a placeholder - actual base64 encoding depends on your Lens Studio setup
        // You may need to use the CameraModule's texture provider methods
        this.log(`Capturing frame: ${width}x${height}`);
        
        // TODO: Implement actual base64 encoding based on your Lens Studio version
        // For now, return a placeholder that Gemini can handle
        return "";  // Will be populated from actual camera in production
    }
    
    // ========================================================================
    // UTILITIES
    // ========================================================================
    
    private log(message: string, level: string = "info") {
        if (!this.enableDebug && level === "info") return;
        
        const prefix = "[AutoReorder]";
        if (level === "error") {
            print(`${prefix} ERROR: ${message}`);
        } else {
            print(`${prefix} ${message}`);
        }
    }
    
    private createDelayedCallbackEvent(callback: () => void, delaySeconds: number) {
        const event = this.createEvent("DelayedCallbackEvent");
        event.bind(callback);
        event.reset(delaySeconds);
    }
}

