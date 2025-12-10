
from typing import Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

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
