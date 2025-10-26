"""Summarization endpoint using Gemini."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from google import genai

router = APIRouter()


class SummarizeRequest(BaseModel):
    """Request body for summarization."""
    summaryPrompt: str


class SummarizeResponse(BaseModel):
    """Response from summarization."""
    summary: str


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """
    Summarize text using Gemini.

    This endpoint accepts a prompt and uses Gemini to generate a concise summary.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not configured"
        )

    try:
        client = genai.Client(api_key=api_key)

        print(f"[DEBUG] Summarize request: {request.summaryPrompt[:200]}...")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[request.summaryPrompt],
            config={
                'temperature': 0.3,
                'max_output_tokens': 500,
            }
        )

        summary = response.text
        print(f"[DEBUG] Summarize response: {summary}")

        return SummarizeResponse(summary=summary)

    except Exception as e:
        print(f"[ERROR] Summarization failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )
