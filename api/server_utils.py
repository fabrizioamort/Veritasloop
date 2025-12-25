
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger(__name__)

def serialize_for_json(obj: Any) -> Any:
    """
    Helper to serialize objects for JSON.
    Handles Pydantic models, datetimes, UUIDs, etc.
    """
    if isinstance(obj, BaseModel):
        # Use model_dump with mode='json' to properly serialize all nested types
        return serialize_for_json(obj.model_dump(mode='json'))
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    return obj

def sanitize_error_message(error: Exception, default: str = "An unexpected error occurred. Please try again.") -> str:
    """
    Logs a detailed error and returns a user-safe, generic error message.
    """
    # Log the full exception for debugging purposes
    logger.error(f"Sanitizing error. Original exception: {error}", exc_info=True)

    # Map exception types to user-friendly messages
    safe_messages = {
        ValueError: "Invalid input provided. Please check your data and try again.",
        TimeoutError: "The request timed out. Please try again later.",
        ConnectionError: "Unable to connect to an external service. Please check your network connection.",
        # Add more specific exceptions as they are identified
    }

    # Return a specific message if the exception type is in our map, otherwise the default
    return safe_messages.get(type(error), default)

