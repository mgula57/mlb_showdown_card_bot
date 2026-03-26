from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

from ..teams.team import Team
from ..sports.sport import Sport
from .enums import GameTypeEnum
from ..generic import DisplayNameGeneric


class StatGroup(BaseModel):
    type: DisplayNameGeneric
    group: Optional[DisplayNameGeneric] = None
    exemptions: Optional[List] = None
    splits: Optional[List['StatSplit']] = None


class StatSplit(BaseModel):
    model_config = {"populate_by_name": True}

    season: Optional[str] = None
    stat: Optional[Dict[str, Any]] = None
    team: Optional[Team] = None
    sport: Optional[Sport] = None
    split: Optional['Split'] = None
    game_type: Optional[GameTypeEnum] = Field(None, alias='gameType')
    date: Optional[str] = None

    # TODO: EXPAND THIS
    game: Optional[Dict[str, Any]] = None
    

class Split(BaseModel):
    """Split metadata for stats splits"""
    code: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, alias='sortOrder')


StatSplit.model_rebuild()