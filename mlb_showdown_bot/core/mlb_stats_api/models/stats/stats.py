from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

from ..teams.team import Team
from .enums import GameTypeEnum
from ..generic import DisplayNameGeneric


class StatGroup(BaseModel):
    type: DisplayNameGeneric
    group: Optional[DisplayNameGeneric] = None
    exemptions: Optional[List] = None
    splits: Optional[List['StatSplit']] = None


class StatSplit(BaseModel):
    season: Optional[str] = None
    stat: Optional[Dict[str, Any]] = None
    team: Optional[Team] = None
    game_type: Optional[GameTypeEnum] = Field(None, alias='gameType')