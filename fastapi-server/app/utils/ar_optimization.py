"""
AR Display Optimization Utilities

Based on Snap Spectacles sample projects, AR text displays have strict character limits.
This module provides utilities to optimize responses for AR display constraints.

Character Limits (from Snap's sample projects):
- Summary Cards: 750-785 chars (detailed content)
- Card Titles: 150-157 chars (descriptive headers)
- General Responses: 300 chars max (conversational AI)
- Concise Answers: 150 chars max (quick facts)
"""

import re
from typing import Optional


# Character limit constants based on Spectacles samples
AR_LIMITS = {
    "summary_content": 785,  # Detailed summary cards
    "summary_title": 157,    # Summary card titles
    "general_response": 300, # General AI responses
    "concise_answer": 150,   # Quick factual responses
    "product_description": 150,  # Product descriptions
}


def optimize_for_ar(
    text: str,
    max_chars: int = 300,
    truncation_style: str = "sentence"
) -> str:
    """
    Optimize text for AR display with character limits
    
    Args:
        text: Original text
        max_chars: Maximum character count
        truncation_style: How to truncate ("sentence", "word", "hard")
        
    Returns:
        Optimized text within character limit
    """
    if len(text) <= max_chars:
        return text
    
    if truncation_style == "sentence":
        return _truncate_at_sentence(text, max_chars)
    elif truncation_style == "word":
        return _truncate_at_word(text, max_chars)
    else:  # hard
        return text[:max_chars]


def _truncate_at_sentence(text: str, max_chars: int) -> str:
    """Truncate at last complete sentence"""
    if len(text) <= max_chars:
        return text
    
    truncated = text[:max_chars]
    
    # Find last sentence boundary
    sentence_endings = ['.', '!', '?']
    last_boundary = -1
    
    for ending in sentence_endings:
        pos = truncated.rfind(ending)
        if pos > last_boundary:
            last_boundary = pos
    
    if last_boundary > 0:
        return truncated[:last_boundary + 1].strip()
    
    # Fallback to word truncation
    return _truncate_at_word(text, max_chars)


def _truncate_at_word(text: str, max_chars: int) -> str:
    """Truncate at last complete word"""
    if len(text) <= max_chars:
        return text
    
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        return truncated[:last_space].strip() + "..."
    
    return truncated


def optimize_product_description(description: str) -> str:
    """
    Optimize product description for AR display (150 chars max)
    
    Example:
        Input: "Pure spring water sourced from natural mountain springs, 
                filtered and bottled for maximum freshness and purity"
        Output: "Pure spring water from natural mountain springs, 
                 filtered & bottled for maximum freshness"
    """
    if not description:
        return ""
    
    max_chars = AR_LIMITS["product_description"]
    
    if len(description) <= max_chars:
        return description
    
    # Apply aggressive optimization
    optimized = description
    
    # Remove filler words
    fillers = [
        "very ", "really ", "quite ", "just ", "actually ", 
        "basically ", "literally ", "essentially "
    ]
    for filler in fillers:
        optimized = optimized.replace(filler, "")
    
    # Abbreviate common words
    abbreviations = {
        " and ": " & ",
        "maximum": "max",
        "minimum": "min",
        "approximate": "approx",
        "with": "w/",
        "without": "w/o",
    }
    for full, abbrev in abbreviations.items():
        optimized = optimized.replace(full, abbrev)
    
    # Remove extra spaces
    optimized = re.sub(r'\s+', ' ', optimized).strip()
    
    # If still too long, truncate at sentence
    if len(optimized) > max_chars:
        optimized = _truncate_at_sentence(optimized, max_chars)
    
    return optimized


def optimize_ai_response(
    response: str,
    response_type: str = "general"
) -> str:
    """
    Optimize AI response for AR display based on context
    
    Args:
        response: AI generated text
        response_type: Type of response (general, concise, summary_title, summary_content)
        
    Returns:
        Optimized response within appropriate character limit
    """
    # Determine character limit based on type
    if response_type == "concise":
        max_chars = AR_LIMITS["concise_answer"]
    elif response_type == "summary_title":
        max_chars = AR_LIMITS["summary_title"]
    elif response_type == "summary_content":
        max_chars = AR_LIMITS["summary_content"]
    else:  # general
        max_chars = AR_LIMITS["general_response"]
    
    # Apply optimization
    return optimize_for_ar(response, max_chars, truncation_style="sentence")


def validate_ar_constraints(
    text: str,
    max_chars: int,
    field_name: str = "text"
) -> tuple[bool, Optional[str]]:
    """
    Validate that text meets AR display constraints
    
    Args:
        text: Text to validate
        max_chars: Maximum allowed characters
        field_name: Name of field (for error message)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(text) <= max_chars:
        return True, None
    
    return False, (
        f"{field_name} exceeds AR display limit: "
        f"{len(text)} chars (max {max_chars})"
    )


def format_for_ar_display(
    text: str,
    max_lines: Optional[int] = None,
    max_chars_per_line: Optional[int] = 50
) -> str:
    """
    Format text for optimal AR display readability
    
    Args:
        text: Text to format
        max_lines: Maximum number of lines (None for no limit)
        max_chars_per_line: Maximum characters per line
        
    Returns:
        Formatted text with appropriate line breaks
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + (1 if current_line else 0)  # +1 for space
        
        if current_length + word_length <= max_chars_per_line:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
            
            # Check line limit
            if max_lines and len(lines) >= max_lines:
                break
    
    # Add remaining words
    if current_line and (not max_lines or len(lines) < max_lines):
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)


def create_concise_summary(text: str, max_chars: int = 150) -> str:
    """
    Create an ultra-concise summary for AR display
    
    Follows pattern from Snap's SummaryTool:
    - Use short phrases, not full sentences when possible
    - Focus on key facts only
    - Omit pleasantries and filler words
    - Use bullet-style format
    
    Example:
        Input: "Neural networks are computational systems that are inspired by 
                biological neural networks and are used to estimate functions 
                based on a large number of inputs."
        Output: "Neural networks: computational systems that learn from many inputs 
                 to estimate functions"
    """
    if len(text) <= max_chars:
        return text
    
    # Extract key concepts (simplified approach)
    # Remove common filler phrases
    concise = text
    
    remove_phrases = [
        "it is important to note that",
        "it should be noted that",
        "in other words",
        "as a matter of fact",
        "for example",
        "such as",
        "including",
    ]
    
    for phrase in remove_phrases:
        concise = concise.replace(phrase, "")
    
    # Simplify structure
    concise = re.sub(r'\s+', ' ', concise).strip()
    
    # Extract first sentence if still too long
    if len(concise) > max_chars:
        first_sentence = re.split(r'[.!?]', concise)[0]
        if len(first_sentence) <= max_chars:
            return first_sentence.strip()
    
    # Final truncation
    return _truncate_at_word(concise, max_chars)


def add_ar_metadata(data: dict) -> dict:
    """
    Add AR optimization metadata to response
    
    Adds information about character counts and optimization status
    useful for debugging and frontend optimization
    """
    metadata = {
        "ar_optimized": True,
        "character_limits": AR_LIMITS,
    }
    
    # Add character counts for text fields
    text_fields = ["description", "title", "content", "response", "message"]
    for field in text_fields:
        if field in data and isinstance(data[field], str):
            metadata[f"{field}_length"] = len(data[field])
    
    data["_ar_metadata"] = metadata
    return data

