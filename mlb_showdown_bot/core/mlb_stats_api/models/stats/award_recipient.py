from pydantic import BaseModel, Field
from typing import Optional

from ..teams.team import Team


class AwardRecipientPosition(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    abbreviation: Optional[str] = None


class AwardRecipientPlayer(BaseModel):
    id: int
    name_first_last: Optional[str] = Field(None, alias='nameFirstLast')
    primary_position: Optional[AwardRecipientPosition] = Field(None, alias='primaryPosition')

    model_config = {'populate_by_name': True}


class AwardRecipient(BaseModel):
    """A single award winner, as returned by GET /awards/{awardId}/recipients"""

    id: str
    name: str
    date: Optional[str] = None
    season: Optional[str] = None
    team: Optional[Team] = None
    player: AwardRecipientPlayer
