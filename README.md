# Homeless Assistance AI Application

This is a comprehensive AI-powered application designed to help homeless individuals find essential resources like shelter, medical care, restrooms, and pharmacies.

## Project Structure

### Backend (FastAPI Server)
- **Location**: `fastapi-server/`
- **Purpose**: Provides REST API endpoints for finding resources
- **Features**:
  - Medical facilities lookup
  - Shelter/homeless resource finder
  - Public restroom locator
  - Pharmacy/vaccination centers
  - Smart orchestration based on user requests

### Frontend (Lens Studio AR)
- **Location**: `lens-studio/`
- **Purpose**: Snapchat Lens that provides AI assistance through AR
- **Features**:
  - Tap-to-get-help interface
  - Real-time resource location
  - Voice-activated assistance

## Setup Instructions

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd fastapi-server
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure environment variables** (optional for demo):
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys if you have them
   ```

4. **Run the server**:
   ```bash
   python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Test the server**:
   ```bash
   python3 test_simple.py
   ```

### Lens Studio Setup

1. **Open Lens Studio** (Snapchat's AR development tool)

2. **Import the project**:
   - Open `lens-studio/AIAssistant.esproj` in Lens Studio

3. **Configure the script**:
   - The main script is in `Assets/AIAssistant.js`
   - Update the `apiUrl` variable if your server is running on a different address

4. **Test the lens**:
   - Use the preview feature in Lens Studio
   - Tap the screen to trigger the AI assistant

## API Endpoints

### Core Endpoints

- `GET /api/` - Welcome message
- `POST /api/orchestrate` - Smart routing based on user request
- `POST /api/find_shelter` - Find nearest homeless shelters
- `POST /api/find_healthcare_facilities` - Find medical facilities
- `POST /api/find_restroom` - Find public restrooms
- `POST /api/find_pharmacy` - Find pharmacies/vaccination centers

### Example API Usage

```bash
# Find shelter
curl -X POST http://127.0.0.1:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "I need shelter", "latitude": 34.0522, "longitude": -118.2437}'

# Find medical help
curl -X POST http://127.0.0.1:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "I need medical help", "latitude": 34.0522, "longitude": -118.2437}'
```

## How It Works

### Backend Intelligence
1. **User Request Processing**: The `/orchestrate` endpoint analyzes user prompts using keyword matching
2. **Resource Location**: Queries various APIs and databases for nearby resources
3. **Distance Calculation**: Uses Haversine formula to find closest resources
4. **Response Formatting**: Returns structured data with distances and contact info

### AR Lens Interface
1. **User Interaction**: Tap the screen to request help
2. **API Communication**: Sends location and request to backend
3. **Response Display**: Shows nearest resources with distances
4. **Auto-reset**: Returns to ready state after 8 seconds

## Data Sources

- **Medical Facilities**: Los Angeles County Health Department
- **Restrooms**: LA Open Data Portal
- **Shelters**: Los Angeles Public Library Homeless Resources
- **Pharmacies**: EasyVax API

## Features

### Smart Routing
The system automatically determines what type of help is needed based on keywords:
- "shelter", "homeless", "sleep" → Shelter finder
- "medical", "doctor", "hospital" → Medical facilities
- "bathroom", "restroom" → Public restrooms
- "pharmacy", "medicine" → Pharmacy locations

### Real-time Data
- Live data from government APIs
- Distance calculations in real-time
- Up-to-date facility information

### Accessibility
- Simple tap interface
- Clear text responses
- No complex navigation required

## Troubleshooting

### Backend Issues
- **Import errors**: Make sure all dependencies are installed
- **API errors**: Check if external APIs are accessible
- **Port conflicts**: Change port in uvicorn command if 8000 is busy

### Lens Studio Issues
- **Script errors**: Check console for JavaScript errors
- **Network issues**: Verify API URL is correct
- **Preview not working**: Ensure server is running and accessible

## Development Notes

- The application works without API keys for demo purposes
- Real production use would require Anthropic and Google API keys
- The Lens Studio script is designed for Snapchat's AR platform
- All coordinates are currently set to Los Angeles for testing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is designed for social good and helping homeless individuals access essential resources.
