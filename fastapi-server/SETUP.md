# Setup Guide

## Environment Variables

Create a `.env` file in the `fastapi-server` directory with the following variables:

```env
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional (for production)
AMAZON_API_KEY=your_amazon_api_key_here
WALMART_API_KEY=your_walmart_api_key_here
INSTACART_API_KEY=your_instacart_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## Getting API Keys

### Anthropic API Key (Required)

1. Go to https://console.anthropic.com
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

### Commerce API Keys (Optional)

These are only needed if you want to integrate with real commerce platforms:

- **Amazon**: https://developer.amazon.com
- **Walmart**: https://developer.walmart.com
- **Instacart**: https://www.instacart.com/company/developer-platform

For demo purposes, the system will work without these keys (using mock order placement).

## Installation Steps

1. **Create virtual environment:**
   ```bash
   cd fastapi-server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file:**
   ```bash
   # Copy the template above and fill in your API keys
   nano .env
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Test the API:**
   - Open http://localhost:8000/docs in your browser
   - Try the `/api/health` endpoint

## Verification

Test that everything is working:

```bash
# Health check
curl http://localhost:8000/api/health

# List products (should return ~11 demo products)
curl http://localhost:8000/api/products
```

You should see a JSON response with product listings.

## Next Steps

1. Read the main [README.md](README.md) for API documentation
2. Explore the interactive API docs at http://localhost:8000/docs
3. Test the detection endpoint with a sample image
4. Integrate with your Spectacles lens

## Troubleshooting

**Issue: Import errors**
```bash
# Solution: Reinstall dependencies
pip install --upgrade -r requirements.txt
```

**Issue: ANTHROPIC_API_KEY not found**
```bash
# Solution: Check .env file exists and has correct format
cat .env
```

**Issue: Port 8000 already in use**
```bash
# Solution: Use a different port
uvicorn app.main:app --reload --port 8080
```

**Issue: CORS errors from Spectacles**
- The API is already configured to allow all origins in development
- Check that your Spectacles app is making requests to the correct URL

