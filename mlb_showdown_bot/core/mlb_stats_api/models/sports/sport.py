from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class Sport(BaseModel):
    
    id: int
    code: Optional[str] = None
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    link: Optional[str] = None
    sort_order: Optional[int] = Field(None, alias='sortOrder')
    active_status: Optional[bool] = Field(None, alias='activeStatus')

class SportEnum(int, Enum):
    MLB = 1
    INTERNATIONAL = 51
    NLB = 52
