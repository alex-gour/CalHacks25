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

if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY environment variable must be set")

anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

WorkflowType = Literal["A", "B", "C", "D", "E", "F", "G"]


class WorkflowPrompt(Enum):
    PHYSICAL = (
        "You are helping a homeless person with a visible physical injury captured in the provided image."
        " Offer urgent but practical guidance, keep the tone calm, limit to 100 tokens,"
        " and speak conversationally."
    )
    NONPHYSICAL = (
        "You are helping a homeless person with a non-physical medical concern."
        " Offer practical advice, keep the response under 100 tokens,"
        " avoid lists or parentheses, and speak conversationally."
    )


async def determine_workflow(user_prompt: str) -> WorkflowType:
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
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_output_tokens=300,
        system=workflow_prompt.value,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()


async def send_vision_prompt(prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg"):
    session_id = str(uuid.uuid4())
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


async def web_search(user_prompt: str, latitude: float, longitude: float) -> str:
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
