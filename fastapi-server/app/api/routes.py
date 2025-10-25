import base64
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from app.models.schemas import (
    HealthcareFacility,
    LocationRequest,
    OrchestrationRequest,
    Shelter,
    SummaryRequest,
)
from app.services.claude import (
    WorkflowPrompt,
    determine_workflow,
    get_general_claude_response,
    send_vision_prompt,
    summarize_text,
    web_search,
)
from app.services.medical import get_medical_care_locations
from app.services.pharmacy import get_easyvax_locations
from app.services.restroom import get_restroom_data
from app.services.shelter import get_shelter_data
from app.utils.geo import get_zip_from_lat_long, haversine

router = APIRouter(prefix="/api", tags=["api"])

async def handle_physical_injury(user_prompt: str, image_surroundings: str) -> str:
    """Handle physical injury workflow with image"""
    session_id = str(uuid.uuid4())

    full_prompt = f"""
    You are to help homeless people get healthcare support. The current user has a physical medical issue. See the photo. 
    Help them solve it. Keep response under 100 tokens! and no formatting, lists, of parenthesis. response as if you're talking.
    
    User prompt: {user_prompt}
    """ 

    image_bytes = base64.b64decode(image_surroundings)

    try:
        response = await send_vision_prompt(full_prompt, image_bytes)
        return response
    except Exception as e:
        return {"sessionId": session_id, "error": str(e)}

async def handle_physical_injury_no_image(user_prompt: str) -> str:
    """Handle physical injury workflow without image"""
    session_id = str(uuid.uuid4())
    
    try:
        # Use the general Claude response for physical injury without image
        response = await get_general_claude_response(user_prompt, WorkflowPrompt.PHYSICAL)
        return {
            "sessionId": session_id,
            "response": response
        }
    except Exception as e:
        return {"sessionId": session_id, "error": str(e)}

async def handle_internal_medical(user_prompt: str) -> str:
    """Handle internal medical problem workflow"""
    session_id = str(uuid.uuid4())
    try:
        response = await get_general_claude_response(user_prompt, WorkflowPrompt.NONPHYSICAL)
        return {
            "sessionId": session_id,
            "response": response
        }
    except Exception as e:
        return {"sessionId": session_id, "error ": str(e)}

async def handle_pharmacy_request(latitude: float, longitude: float) -> Dict[str, Any]:
    """Handle pharmacy location request"""
    session_id = str(uuid.uuid4())
    try:
        zip_code = get_zip_from_lat_long(latitude, longitude)
        print(f"[handle_pharmacy_request] Zip code: {zip_code}")

        locations = get_easyvax_locations(zip_code, session_id)
        print(f"[handle_pharmacy_request] Locations raw: {locations}")

        if not isinstance(locations, list):
            return {"sessionId": session_id, "error": f"Expected list, got {type(locations).__name__}: {locations}"}

        for loc in locations:
            if loc.get('appointments'):
                has_appointments = any(day['times'] for day in loc['appointments'])
                if has_appointments:
                    pharmacy_info = {
                        "sessionId": session_id,
                        "locationName": loc.get('locationName', 'Unknown'),
                        "address": loc.get('address', 'Unknown'),
                        "city": loc.get('city', 'Unknown'),
                        "state": loc.get('state', 'Unknown'),
                        "zip": loc.get('zip', 'Unknown'),
                        "appointments": [],
                        "distance_miles": loc.get('distance', 0),
                    }
                    for appointment_day in loc['appointments']:
                        if appointment_day.get('times'):
                            day_info = {
                                "date": appointment_day.get('date', 'Unknown'),
                                "times": [slot.get('time', 'Unknown') for slot in appointment_day['times']]
                            }
                            pharmacy_info["appointments"].append(day_info)
                    
                    return pharmacy_info
        
        return {"sessionId": session_id, "message": "No pharmacies with available appointments found."}

    except Exception as e:
        return {"sessionId": session_id, "error": f"Internal error: {str(e)}"}
@router.post("/find_pharmacy")
async def find_pharmacy(req: LocationRequest):
    return await handle_pharmacy_request(req.latitude, req.longitude)

async def handle_restroom_request(latitude: float, longitude: float) -> Dict[str, Any]:
    """Handle restroom location request"""
    session_id = str(uuid.uuid4())

    try:
        user_lat = latitude
        user_lon = longitude
        
        restrooms = get_restroom_data()

        closest_restroom = None
        min_distance = float('inf')

        for restroom in restrooms:
            geom = restroom.get('the_geom')
            if geom and 'coordinates' in geom:
                try:
                    toilets = int(restroom.get('toilets', 0) or 0)
                    urinals = int(restroom.get('urinals', 0) or 0)
                    faucets = int(restroom.get('faucets', 0) or 0)
                except (ValueError, TypeError):
                    toilets = urinals = faucets = 0

                if toilets == 0 and urinals == 0 and faucets == 0:
                    continue

                lon, lat = geom['coordinates']
                distance = haversine(user_lon, user_lat, lon, lat)

                if distance < min_distance:
                    min_distance = distance
                    closest_restroom = {
                        "facility": restroom.get('facility', 'Unknown'),
                        "gender": restroom.get('gender', 'Unknown'),
                        "toilets": toilets,
                        "urinals": urinals,
                        "faucets": faucets,
                        "location": geom,
                        "distance_miles": round(distance, 2)
                    }

        if closest_restroom:
            return {
                "sessionId": session_id,
                "nearestRestroom": closest_restroom
            }
        else:
            return {
                "sessionId": session_id,
                "message": "No restrooms found."
            }

    except Exception as e:
        return {"sessionId": session_id, "error": str(e)}

@router.post("/find_restroom")
async def find_restroom(req: LocationRequest):
    return await handle_restroom_request(req.latitude, req.longitude)

@router.post("/find_healthcare_facilities")
async def find_healthcare_facilities(req: LocationRequest):
    return await handle_medical_center_request(req.latitude, req.longitude)

async def handle_medical_center_request(latitude: float, longitude: float, limit: int = 5) -> Dict[str, Any]:
    """Handle medical center location request"""
    session_id = str(uuid.uuid4())
    try:
        facilities = get_medical_care_locations(latitude, longitude, limit)
        
        if isinstance(facilities, dict) and "error" in facilities:
            return {"sessionId": session_id, "error": facilities["error"]}
        
        return {
            "sessionId": session_id,
            "facilities": facilities
        }
    except Exception as e:
        return {"sessionId": session_id, "error": str(e)}

async def handle_shelter_request(latitude: float, longitude: float) -> Dict[str, Any]:
    """Handle shelter location request"""
    session_id = str(uuid.uuid4())  # Generate fresh session UUID
    try:
        if not latitude or not longitude:
            return {"sessionId": session_id, "error": "Latitude and longitude are required."}
        
        print(f"Latitude: {latitude}, Longitude: {longitude}")
        zip_code = get_zip_from_lat_long(latitude, longitude)
                
        nearest_resource = get_shelter_data(latitude, longitude, zip_code)
        
        return {
            "sessionId": session_id,
            "zipCode": zip_code,
            "nearest_resource": nearest_resource,
            "message": "Found nearest homeless resource."
        }
    
    except Exception as e:
        return {"sessionId": session_id, "error": str(e)}

@router.post("/find_shelter")
async def find_shelter(req: LocationRequest):
    return await handle_shelter_request(req.latitude, req.longitude)

async def handle_physical_resource_request(latitude: float, longitude: float, user_prompt: str) -> Dict[str, Any]:
    """Handle physical resource location request"""
    session_id = str(uuid.uuid4())
    try:
        response = await web_search(user_prompt, latitude, longitude)
        return {
            "sessionId": session_id,
            "response": response,
            "location": {"latitude": latitude, "longitude": longitude}
        }
    except Exception as e:
        return {"sessionId": session_id, "error": str(e)}

@router.post("/summarize")
async def summarize(req: SummaryRequest):
    try:
        result = await summarize_text(req.summaryPrompt)
        return {"summary": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/orchestrate", response_model=Dict[str, Any])
async def orchestrate(req: OrchestrationRequest):
    """
    Orchestration endpoint that determines which service to call based on semantic similarity.
    
    Args:
        req: Request containing user prompt, location, and optional image
        
    Returns:
        Dictionary with response from the most appropriate service
    """
    print(f"DEBUG: Orchestrate called with prompt: '{req.user_prompt}' - VERSION 2")
    try:
        # Determine the workflow using Gemini
        workflow_type = await determine_workflow(req.user_prompt)
        print(f"DEBUG: Orchestrate detected workflow type: {workflow_type} for prompt: '{req.user_prompt}'")
        
        # Route to the appropriate service based on workflow type
        print(f"DEBUG: Routing to workflow {workflow_type}")
        if workflow_type == "A":
            print("DEBUG: Handling physical injury workflow")
            if req.image_surroundings:
                return await handle_physical_injury(req.user_prompt, req.image_surroundings)
            else:
                # Handle physical injury without image
                return await handle_physical_injury_no_image(req.user_prompt)
        elif workflow_type == "B":
            print("DEBUG: Handling internal medical workflow")
            return await handle_internal_medical(req.user_prompt)
        elif workflow_type == "C":
            print("DEBUG: Handling shelter workflow")
            return await handle_shelter_request(req.latitude, req.longitude)
        elif workflow_type == "D":
            print("DEBUG: Handling pharmacy workflow")
            return await handle_pharmacy_request(req.latitude, req.longitude)
        elif workflow_type == "E":
            print("DEBUG: Handling medical center workflow")
            return await handle_medical_center_request(req.latitude, req.longitude)
        elif workflow_type == "F":
            print("DEBUG: Handling restroom workflow")
            return await handle_restroom_request(req.latitude, req.longitude)
        elif workflow_type == "G":
            print("DEBUG: Handling physical resource workflow")
            return await handle_physical_resource_request(req.latitude, req.longitude, req.user_prompt)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
            
    except Exception as e:
        return {"sessionId": str(uuid.uuid4()), "error": str(e)} 
    
@router.get("/")
async def root():
    return {"message": "Welcome to the FastAPI server!"}

@router.post("/test_workflow")
async def test_workflow(request: dict):
    """Test endpoint to debug workflow detection"""
    user_prompt = request.get("user_prompt", "")
    workflow_type = await determine_workflow(user_prompt)
    return {"user_prompt": user_prompt, "workflow_type": workflow_type}