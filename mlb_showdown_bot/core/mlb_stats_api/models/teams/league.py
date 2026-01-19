from pydantic import BaseModel
from typing import Optional

class League(BaseModel):
    id: int
    name: str
    abbreviation: Optional[str] = None
