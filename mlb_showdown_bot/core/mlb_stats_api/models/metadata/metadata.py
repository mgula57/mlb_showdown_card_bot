from pydantic import BaseModel, Field
from typing import Optional

class SituationCode(BaseModel):
    code: str = Field(..., alias='code')
    description: str = Field(..., alias='description')
    navigation_menu: Optional[str] = Field(None, alias='navigationMenu')
    team: Optional[bool] = Field(None, alias='team')
    batting: Optional[bool] = Field(None, alias='batting')
    fielding: Optional[bool] = Field(None, alias='fielding')
    pitching: Optional[bool] = Field(None, alias='pitching')
    sort_order: Optional[int] = Field(None, alias='sortOrder')
