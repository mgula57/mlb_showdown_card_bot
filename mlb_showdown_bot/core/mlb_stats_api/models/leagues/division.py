from pydantic import BaseModel, Field
from typing import Optional

class Division(BaseModel):
    id: int
    name: str
    abbreviation: Optional[str] = None
    name_short: Optional[str] = Field(None, alias='nameShort')
