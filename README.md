<!-- @format -->

# SnapAid - AI-Powered Homeless Support System

A comprehensive system that helps homeless individuals find essential resources
using AI-powered Snapchat lenses and a FastAPI backend.

## 🏗️ Project Structure

- **`fastapi-server/`** - Backend API server with AI orchestration
- **`lens-studio/`** - Snapchat Lens Studio project for AR interface

## 🚀 Quick Start

### 1. Backend Setup (FastAPI Server)

```bash
cd fastapi-server

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your Anthropic API key:
# ANTHROPIC_API_KEY=your-actual-api-key-here

# Start the server
python run.py
```

The server will start on `http://localhost:8000` with ngrok tunneling for
external access.

### 2. Frontend Setup (Lens Studio)

1. Open `lens-studio/AIAssistant.esproj` in Snapchat Lens Studio
2. In the VisionOpenAI component, set the `backendBaseUrl` to your ngrok URL
3. Assign the required components (Text inputs, Image, etc.)
4. Test the lens in the simulator or on device

## 🔧 API Endpoints

### Main Orchestration Endpoint

```
POST /api/orchestrate
```

Routes user requests to appropriate services based on AI classification.

**Request Body:**

```json
{
	"user_prompt": "I need help finding a shelter",
	"latitude": 34.0522,
	"longitude": -118.2437,
	"image_surroundings": "base64_encoded_image" // optional
}
```

### Individual Service Endpoints

- `POST /api/find_shelter` - Find homeless shelters
- `POST /api/find_restroom` - Find public restrooms
- `POST /api/find_healthcare_facilities` - Find medical centers
- `POST /api/find_pharmacy` - Find pharmacies with appointments
- `POST /api/summarize` - Generate AI summaries

## 🤖 AI Workflow Classification

The system automatically routes requests based on keywords:

- **A** - Physical injury (requires image)
- **B** - Internal medical problems
- **C** - Shelter/housing needs
- **D** - Pharmacy/medication needs
- **E** - Medical center/hospital needs
- **F** - Restroom/bathroom needs
- **G** - General physical resources

## 🔑 Required API Keys

### Anthropic Claude API

1. Get your API key from [console.anthropic.com](https://console.anthropic.com/)
2. Add it to `.env` file: `ANTHROPIC_API_KEY=your-key-here`

### PositionStack (Optional)

- Used for geocoding (has free tier)
- Default key is included, but you can add your own

## 🛠️ Features

### Backend Features

- ✅ AI-powered request routing
- ✅ Location-based resource finding
- ✅ Image analysis for physical injuries
- ✅ Real-time data from multiple APIs
- ✅ Error handling and fallbacks
- ✅ CORS enabled for web access

### Frontend Features (Lens Studio)

- ✅ Voice-to-text input
- ✅ Camera integration for image capture
- ✅ Text-to-speech output
- ✅ Chat history tracking
- ✅ Location services
- ✅ Real-time API communication

## 📱 Usage

1. **Voice Input**: Tap and speak your request
2. **Image Capture**: Take a photo if you have a physical injury
3. **AI Processing**: The system analyzes your request and location
4. **Resource Finding**: Get nearby resources with directions
5. **Voice Output**: Listen to the response

## 🔧 Troubleshooting

### Server Issues

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that your API key is set in `.env`
- Verify the server is running on port 8000

### Lens Studio Issues

- Ensure the `backendBaseUrl` is set to your ngrok URL
- Check that all required components are assigned
- Verify internet connectivity in the lens

### API Issues

- Check the server logs for error messages
- Verify your Anthropic API key is valid
- Test individual endpoints with curl or Postman

## 🌟 Key Improvements Made

1. **Fixed API Key Handling**: Added graceful fallbacks when API keys aren't
   configured
2. **Improved Error Handling**: Better error messages and fallback responses
3. **Added Missing Dependencies**: Included BeautifulSoup4 for web scraping
4. **Fixed Version Compatibility**: Updated Anthropic library version
5. **Enhanced Workflow Routing**: Added keyword-based fallback classification
6. **Better Environment Setup**: Clear instructions and example files

## 📞 Support

The system is now fully functional! If you encounter any issues:

1. Check the server logs for error messages
2. Verify your API keys are correctly set
3. Test individual endpoints to isolate problems
4. Ensure all dependencies are properly installed

## 🎯 Next Steps

1. Get your Anthropic API key and add it to `.env`
2. Test the system with the provided endpoints
3. Deploy the backend to a cloud service for production use
4. Publish your Snapchat lens for public use

The system is ready to help homeless individuals find essential resources
through an intuitive AR interface!
