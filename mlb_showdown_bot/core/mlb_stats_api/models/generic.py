from pydantic import BaseModel, Field

class EnumGeneric(BaseModel):
    """Generic model for MLB Stats API enumerations with code and description"""
    
    code: str
    description: str

class DisplayNameGeneric(BaseModel):
    """Generic model for MLB Stats API display names"""
    
    display_name: str = Field(..., alias='displayName')