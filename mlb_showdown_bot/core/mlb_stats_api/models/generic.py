from pydantic import BaseModel, Field
from typing import Optional

class EnumGeneric(BaseModel):
    """Generic model for MLB Stats API enumerations with code and description"""
    
    code: str
    description: str

class DisplayNameGeneric(BaseModel):
    """Generic model for MLB Stats API display names"""
    
    display_name: str = Field(..., alias='displayName')

class XRefIdData(BaseModel):
    """Model for cross-reference ID data from MLB Stats API"""
    
    xref_id: str = Field(..., alias='xrefId')
    xref_type: str = Field(..., alias='xrefType')
    season: Optional[str] = Field(None, alias='season')