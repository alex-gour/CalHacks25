# ✅ Setup Checklist - Auto-Reorder System

**Use this checklist to ensure everything is configured correctly**

---

## 📋 Backend Setup

### Step 1: Install Dependencies
```bash
cd fastapi-server
pip install -r requirements.txt
```
- [ ] All dependencies installed without errors
- [ ] Python 3.10+ confirmed

### Step 2: Environment Configuration
```bash
# .env file is already created with correct settings!
# No AI API keys needed - using Remote Service Gateway
```
- [ ] `.env` file exists in `fastapi-server/` folder
- [ ] File shows "AI APIs - NOT NEEDED!"
- [ ] Commerce API keys blank (using demo mode)

### Step 3: Start Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- [ ] Server starts without errors
- [ ] Can access http://localhost:8000/docs
- [ ] Health check works: http://localhost:8000/api/health

### Step 4: Get Your IP Address
```bash
# macOS/Linux:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows:
ipconfig | findstr IPv4
```
- [ ] IP address noted: `________________` (example: 192.168.1.100)
- [ ] Can access from network: `http://YOUR_IP:8000/docs`

---

## 📱 Lens Studio Setup

### Step 5: Install RSG Token Generator
- [ ] Lens Studio 5.15+ installed
- [ ] Asset Library → Spectacles → RSG Token Generator installed
- [ ] Lens Studio restarted (if required)

### Step 6: Generate RSG Token
- [ ] Windows → Remote Service Gateway Token opened
- [ ] "Generate Token" button clicked
- [ ] Token copied (long string of characters)
- [ ] Token saved somewhere safe

### Step 7: Open Project
- [ ] Lens Studio project opened: `lens-studio/AIAssistant.esproj`
- [ ] Project loaded without errors
- [ ] Scene Hierarchy visible

### Step 8: Configure RSG
- [ ] `RemoteServiceGatewayCredentials` object found/created in scene
- [ ] RSG Token pasted in Inspector
- [ ] Project saved (Ctrl+S / Cmd+S)

### Step 9: Add Internet Module
- [ ] Internet Module added to scene (Add Component → Internet Module)
- [ ] Module visible in Scene Hierarchy

### Step 10: Add AutoReorderController
- [ ] New Scene Object created: `AutoReorderController`
- [ ] Script component added: `AutoReorderController.ts`
- [ ] All inputs assigned in Inspector:
  - [ ] Camera Texture
  - [ ] Http Module (Internet Module)
  - [ ] Prompt Text
  - [ ] Prompt Panel
  - [ ] Confirm Button
  - [ ] Dismiss Button

### Step 11: Update Script Configuration
Open `Assets/Scripts/TS/AutoReorderController.ts`:

- [ ] Line ~20: `BACKEND_URL` updated with your IP:
  ```typescript
  private BACKEND_URL = "http://YOUR_IP:8000/api";
  ```
  Replace `YOUR_IP` with: `________________`

- [ ] Line ~22: `USER_ID` set (optional):
  ```typescript
  private USER_ID = "spectacles_user_001";
  ```

- [ ] File saved (Ctrl+S / Cmd+S)

---

## 🧪 Testing

### Step 12: Test Backend Endpoints
```bash
# Health check
curl http://YOUR_IP:8000/api/health

# List products
curl http://YOUR_IP:8000/api/products

# Get specific product
curl http://YOUR_IP:8000/api/products/prod_water_001
```
- [ ] Health check returns `{"status":"healthy"}`
- [ ] Products list shows 11 items
- [ ] Product details load correctly

### Step 13: Test in Lens Studio Preview
- [ ] Preview panel open
- [ ] Device set to "Spectacles (2024)"
- [ ] Logger panel open (View → Panels → Logger)
- [ ] Preview started (no errors)

### Step 14: Check Logs
Look for these messages in Logger:
```
[AutoReorder] AutoReorderController initialized
[AutoReorder] Starting product scanning...
```
- [ ] Initialization message visible
- [ ] No error messages
- [ ] Script is running

### Step 15: Test Detection (Optional)
- [ ] Point camera at a product
- [ ] Wait 5+ seconds
- [ ] Logger shows: "Calling Gemini via RSG..."
- [ ] Detection attempt visible in logs

---

## 🎯 Final Verification

### Architecture Check
- [ ] ✅ Gemini Vision via RSG (no API key needed)
- [ ] ✅ Backend handles products/orders
- [ ] ✅ No ANTHROPIC_API_KEY required
- [ ] ✅ No GEMINI_API_KEY required
- [ ] ✅ Commerce keys optional (demo mode works)

### Files Check
- [ ] ✅ `.env` file configured correctly
- [ ] ✅ `AutoReorderController.ts` has correct backend URL
- [ ] ✅ RSG token configured in Lens Studio
- [ ] ✅ Internet Module added to scene
- [ ] ✅ Script inputs all assigned

### Functionality Check
- [ ] ✅ Backend API accessible
- [ ] ✅ Lens Studio preview works
- [ ] ✅ No errors in Logger
- [ ] ✅ RSG authentication successful
- [ ] ✅ Can detect products (or see attempt in logs)

---

## 🎉 Success!

If all boxes are checked, you're ready to go! 🚀

### What Works:
- ✅ **Vision AI**: Gemini via RSG (no API keys!)
- ✅ **Product Database**: 11 demo products
- ✅ **Order System**: Demo mode (no commerce keys needed)
- ✅ **User Management**: Full preferences system
- ✅ **AR Optimization**: Automatic character limits

### Next Steps:
1. Test on Spectacles hardware
2. Point at real products
3. Test voice/gesture confirmation
4. Review order history
5. Customize product catalog

---

## ⚠️ Troubleshooting

### If Backend Won't Start:
```bash
# Check port 8000 is available
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Try different port
uvicorn app.main:app --reload --port 8080
```

### If RSG Authentication Fails:
1. Regenerate token: Windows → RSG Token
2. Copy new token (entire string)
3. Paste in `RemoteServiceGatewayCredentials`
4. Save and restart preview

### If Backend Connection Fails:
1. Check IP address is correct
2. Verify backend is running
3. Test: `curl http://YOUR_IP:8000/api/health`
4. Check firewall settings (allow port 8000)
5. Try: `http://YOUR_IP:8000/api` not `http://localhost:8000/api`

### If No Detection Happens:
1. Check Logger for errors
2. Verify RSG token is valid
3. Ensure camera permissions enabled
4. Wait full 5 seconds between scans
5. Check lighting (good lighting helps detection)

---

## 📊 Completion Status

**My Status:**

- [ ] Backend fully configured
- [ ] Lens Studio fully configured
- [ ] All tests passing
- [ ] Ready for Spectacles testing
- [ ] **READY TO DEMO! 🎉**

**Date Completed:** _______________

**Notes:**
```
_____________________________________
_____________________________________
_____________________________________
```

---

**Remember:** No AI API keys needed! Everything works via Remote Service Gateway. 🎯

