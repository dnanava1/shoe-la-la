from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ShoeConstraints(BaseModel):
    shoe_fit: Optional[str] = None
    shoe_color: Optional[str] = None
    shoe_size: Optional[float] = None
    price_cap: Optional[float] = None
    gender: Optional[str] = None
    collection_name: Optional[str] = None

class ParsedIntent(BaseModel):
    intent: str = Field(..., description="search|recommend|view_details")
    shoe_name: Optional[str] = None
    constraints: ShoeConstraints = ShoeConstraints()

def as_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": ["search", "recommend", "view_details","add_to_watchlist","remove_from_watchlist"]},
            "shoe_name": {"type": "string"},
            "constraints": {
                "type": "object",
                "properties": {
                    "shoe_fit": {"type": "string"},
                    "shoe_color": {"type": "string"},
                    "shoe_size": {"type": "number"},
                    "price_cap": {"type": "number"},
                    "gender": {"type": "string"},
                    "collection_name": {"type": "string"}
                },
                "additionalProperties": False  # Prevent empty strings for missing fields
            }
        },
        "required": ["intent"],
        "additionalProperties": False
    }