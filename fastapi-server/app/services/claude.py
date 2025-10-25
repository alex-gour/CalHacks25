import base64
import os
import uuid
from enum import Enum
from typing import Literal, Optional

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your-claude-api-key-here":
    print("WARNING: ANTHROPIC_API_KEY not set or using placeholder value")
    print("Please set your actual Anthropic API key in the .env file")
    # Create a mock client for testing
    anthropic_client = None
else:
    anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

WorkflowType = Literal["A", "B", "C", "D", "E", "F", "G"]


class WorkflowPrompt(Enum):
    PHYSICAL = (
        "You are helping a homeless person with a physical injury or medical issue."
        " Offer urgent but practical guidance, keep the tone calm, limit to 100 tokens,"
        " and speak conversationally."
    )
    NONPHYSICAL = (
        "You are helping a homeless person with a non-physical medical concern."
        " Offer practical advice, keep the response under 100 tokens,"
        " avoid lists or parentheses, and speak conversationally."
    )


async def determine_workflow(user_prompt: str) -> WorkflowType:
    if not anthropic_client:
        # Fallback to simple keyword matching when API key is not available
        prompt_lower = user_prompt.lower()
        print(f"DEBUG: Analyzing prompt: '{user_prompt}' -> '{prompt_lower}'")
        
        if any(word in prompt_lower for word in ['hurt', 'injury', 'wound', 'cut', 'bleeding', 'pain', 'bleed', 'blood', 'injured']):
            print("DEBUG: Matched physical injury keywords")
            return "A"  # Physical injury
        elif any(word in prompt_lower for word in ['sick', 'ill', 'fever', 'headache', 'stomach', 'depressed', 'suicidal', 'mental', 'crisis', 'anxious']):
            print("DEBUG: Matched internal medical keywords")
            return "B"  # Internal medical
        elif any(word in prompt_lower for word in ['shelter', 'homeless', 'sleep', 'bed']):
            print("DEBUG: Matched shelter keywords")
            return "C"  # Shelter
        elif any(word in prompt_lower for word in ['pharmacy', 'medicine', 'medication', 'drug']):
            print("DEBUG: Matched pharmacy keywords")
            return "D"  # Pharmacy
        elif any(word in prompt_lower for word in ['doctor', 'hospital', 'clinic', 'medical']):
            print("DEBUG: Matched medical center keywords")
            return "E"  # Medical center
        elif any(word in prompt_lower for word in ['bathroom', 'restroom', 'toilet', 'washroom']):
            print("DEBUG: Matched restroom keywords")
            return "F"  # Washroom
        else:
            print("DEBUG: No specific keywords matched, defaulting to physical resources")
            return "G"  # Physical resource (default)
    
    system = (
        "You route support requests from unhoused individuals."
        " Return only a single uppercase letter A-G based on the category that best fits:"
        " A Physical injury; B Internal medical problem; C Shelter; D Pharmacy;"
        " E Medical center; F Washroom; G Physical resource."
    )
    message: MessageParam = {
        "role": "user",
        "content": f"Classify this request with a single letter A-G: {user_prompt}",
    }
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_output_tokens=5,
        system=system,
        messages=[message],
    )

    choice = response.content[0].text.strip().upper()
    if choice not in {"A", "B", "C", "D", "E", "F", "G"}:
        raise ValueError(f"Invalid workflow classification returned: {choice}")
    return choice  # type: ignore[return-value]


async def get_general_claude_response(user_prompt: str, workflow_prompt: WorkflowPrompt) -> str:
    if not anthropic_client:
        # Provide comprehensive help without API key
        return get_comprehensive_homeless_help(user_prompt, workflow_prompt)
    
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_output_tokens=300,
        system=workflow_prompt.value,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()

def get_comprehensive_homeless_help(user_prompt: str, workflow_prompt: WorkflowPrompt) -> str:
    """Provide comprehensive help for homeless individuals without requiring API key."""
    
    prompt_lower = user_prompt.lower()
    
    if workflow_prompt == WorkflowPrompt.NONPHYSICAL:
        # Medical help
        if any(word in prompt_lower for word in ['sick', 'ill', 'fever', 'headache', 'stomach', 'pain', 'hurt']):
            return """I understand you're not feeling well. Here's what you can do right now:

• Call 911 if it's a medical emergency
• Visit the nearest emergency room - they cannot turn you away
• Call 211 for free medical clinics in your area
• Go to a local library - they often have information about free health services
• Ask at a nearby shelter about medical assistance programs

Stay hydrated and try to rest. Your health matters and help is available."""
        
        elif any(word in prompt_lower for word in ['mental', 'depressed', 'anxious', 'suicidal', 'crisis', 'suicide', 'kill', 'end', 'thoughts']):
            return """I hear you're going through a tough time. You're not alone:

• Call 988 for the Suicide & Crisis Lifeline (24/7)
• Text HOME to 741741 for crisis text support
• Call 211 for mental health resources
• Visit a local library for information about free counseling
• Talk to someone at a nearby shelter - they understand

Your life has value. Please reach out for help - people care about you."""
        
        else:
            return """I understand you need help. Here are immediate resources:

• Call 211 for 24/7 crisis support and resource referrals
• Visit your local library for information and computer access
• Check with nearby churches - many offer assistance programs
• Look for community centers in your area
• Ask at local shelters about available services

You're not alone - help is available and people want to support you."""
    
    else:
        # Check for physical injury keywords in the general case
        if any(word in prompt_lower for word in ['hurt', 'injury', 'wound', 'cut', 'bleeding', 'pain', 'bleed', 'blood', 'injured']):
            return """I can see you may have an injury. Here's what to do immediately:

• If bleeding heavily or severe pain: Call 911 right now
• For cuts: Clean with water if available, apply pressure to stop bleeding
• Visit the nearest emergency room - they cannot refuse treatment
• Call 211 for free medical clinics in your area
• Ask at a nearby shelter about medical assistance

Your safety is the priority. Don't hesitate to seek emergency care."""
        else:
            return """I'm here to help you find the resources you need. Here's what I can do:

• Find nearby shelters and emergency housing
• Locate free meals and food assistance
• Help you find medical care and mental health support
• Connect you with job training and employment services
• Provide information about benefits and assistance programs

What specific help do you need right now? I'll do my best to guide you to the right resources."""


async def send_vision_prompt(prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg"):
    session_id = str(uuid.uuid4())
    
    if not anthropic_client:
        # Provide helpful response even without API key
        return {
            "sessionId": session_id,
            "response": get_vision_help_response(prompt),
            "full_response": {"fallback": "API key not configured"},
        }
    
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_output_tokens=400,
        system="You are a vision assistant focused on safety support for homeless populations.",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": base64_image,
                        },
                    },
                ],
            }
        ],
    )

    text_response = response.content[0].text if response.content else ""
    return {
        "sessionId": session_id,
        "response": text_response,
        "full_response": response.model_dump(),
    }

def get_vision_help_response(prompt: str):
    """Provide helpful response for vision-based requests without API key."""
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ['hurt', 'injury', 'wound', 'cut', 'bleeding', 'pain']):
        return """I can see you may have an injury. Here's what to do immediately:

• If bleeding heavily or severe pain: Call 911 right now
• For cuts: Clean with water if available, apply pressure to stop bleeding
• Visit the nearest emergency room - they cannot refuse treatment
• Call 211 for free medical clinics in your area
• Ask at a nearby shelter about medical assistance

Your safety is the priority. Don't hesitate to seek emergency care."""
    
    elif any(word in prompt_lower for word in ['sick', 'ill', 'fever', 'headache']):
        return """I understand you're not feeling well. Here's immediate help:

• Call 911 if it's a medical emergency
• Visit the nearest emergency room
• Call 211 for free medical clinics
• Go to a local library for health information
• Ask at shelters about medical programs

Stay hydrated and rest. Your health matters and help is available."""
    
    else:
        return """I can see you need help. Here are immediate resources:

• Call 211 for 24/7 crisis support and resource referrals
• Visit your local library for information and assistance
• Check with nearby churches and community centers
• Look for local shelters and assistance programs
• Call 988 if you're in crisis

You're not alone - help is available and people want to support you."""


async def web_search(user_prompt: str, latitude: float, longitude: float) -> str:
    if not anthropic_client:
        return get_local_resource_help(user_prompt, latitude, longitude)
    
    system = (
        "You help unhoused folks locate nearby physical resources (food, clothing, supplies)."
        " Provide concise directions using the given coordinates."
    )
    user_content = (
        f"User is at latitude {latitude}, longitude {longitude}."
        f" Provide suggestions for this request: {user_prompt}."
        " Keep advice under 120 tokens and conversational."
    )

    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_output_tokens=350,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text.strip()

def get_local_resource_help(user_prompt: str, latitude: float, longitude: float) -> str:
    """Provide helpful local resource information without API key."""
    prompt_lower = user_prompt.lower()
    
    # Determine if this is LA area (roughly)
    is_la_area = 33.5 <= latitude <= 34.5 and -119.0 <= longitude <= -117.0
    
    if any(word in prompt_lower for word in ['food', 'eat', 'meal', 'hungry', 'starving']):
        if is_la_area:
            return f"""I understand you need food. Here are immediate options near you:

• Call 211 for free meal programs and food pantries
• Visit your local library - they often have information about free meals
• Check with nearby churches - many offer free meals
• Look for community centers in your area
• Ask at shelters about meal programs
• Visit LA Mission (303 E 5th St) for free meals

You're at {latitude}, {longitude}. Help is available - don't go hungry."""
        else:
            return f"""I understand you need food. Here are immediate options:

• Call 211 for free meal programs and food pantries
• Visit your local library for information about free meals
• Check with nearby churches and community centers
• Look for local food banks and soup kitchens
• Ask at shelters about meal programs

You're at {latitude}, {longitude}. Help is available - don't go hungry."""
    
    elif any(word in prompt_lower for word in ['clothes', 'clothing', 'shirt', 'pants', 'shoes']):
        return f"""I understand you need clothing. Here are options near you:

• Call 211 for clothing assistance programs
• Visit your local library for information about clothing banks
• Check with nearby churches - many have clothing programs
• Look for community centers with clothing assistance
• Ask at shelters about clothing programs
• Visit local thrift stores for affordable options

You're at {latitude}, {longitude}. Help is available."""
    
    elif any(word in prompt_lower for word in ['job', 'work', 'employment', 'money', 'income']):
        return f"""I understand you need work. Here are resources near you:

• Call 211 for job training and employment services
• Visit your local library for job search resources and computer access
• Check with nearby shelters about job programs
• Look for community centers with employment services
• Visit local workforce development centers
• Ask at churches about job assistance programs

You're at {latitude}, {longitude}. Employment help is available."""
    
    else:
        return f"""I understand you need help. Here are immediate resources near you:

• Call 211 for 24/7 crisis support and resource referrals
• Visit your local library for information and assistance
• Check with nearby churches and community centers
• Look for local shelters and assistance programs
• Call 988 if you're in crisis

You're at {latitude}, {longitude}. Help is available and people want to support you."""


def _summary_system_prompt() -> str:
    return (
        "Summarize inputs into 3-5 short bullet points."
        " Use the • character for bullets and keep each point succinct."
    )


async def summarize_text(prompt: str) -> str:
    if not anthropic_client:
        return get_helpful_summary_fallback(prompt)
    
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_output_tokens=200,
        system=_summary_system_prompt(),
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()

def get_helpful_summary_fallback(prompt: str) -> str:
    """Provide helpful summary fallback without API key."""
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ['shelter', 'homeless', 'housing', 'sleep']):
        return """• Call 211 for emergency shelter and housing assistance
• Visit local shelters for immediate help
• Check with churches and community centers
• Look for local housing programs and resources"""
    
    elif any(word in prompt_lower for word in ['medical', 'health', 'sick', 'doctor']):
        return """• Call 911 for medical emergencies
• Visit emergency rooms for immediate care
• Call 211 for free medical clinics
• Check with local health departments"""
    
    elif any(word in prompt_lower for word in ['food', 'hungry', 'meal', 'eat']):
        return """• Call 211 for free meal programs
• Visit local food banks and pantries
• Check with churches for free meals
• Look for community meal programs"""
    
    elif any(word in prompt_lower for word in ['mental', 'crisis', 'depressed', 'suicidal']):
        return """• Call 988 for crisis support (24/7)
• Text HOME to 741741 for crisis text support
• Call 211 for mental health resources
• Visit local crisis centers"""
    
    else:
        return """• Call 211 for 24/7 crisis support and resource referrals
• Visit your local library for information and assistance
• Check with nearby churches and community centers
• Look for local shelters and assistance programs"""


async def get_orchestrated_response(
    user_prompt: str,
    workflow_type: WorkflowType,
    image_surroundings: Optional[bytes],
) -> dict:
    if workflow_type == "A":
        if not image_surroundings:
            return {
                "sessionId": str(uuid.uuid4()),
                "error": "Image required for workflow A but none provided.",
            }
        return await send_vision_prompt(user_prompt, image_surroundings)
    if workflow_type == "B":
        response = await get_general_claude_response(user_prompt, WorkflowPrompt.NONPHYSICAL)
        return {"sessionId": str(uuid.uuid4()), "response": response}

    raise ValueError("Specialized workflow handling must be performed by the router")
