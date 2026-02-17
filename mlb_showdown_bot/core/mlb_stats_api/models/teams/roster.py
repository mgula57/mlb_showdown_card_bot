from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from enum import Enum

from ..leagues.division import Division
from ..leagues.league import League
from ..person import Person
from ..position import Position
from ..generic import EnumGeneric

class RosterTypeEnum(str, Enum):
    MAN_40 = "40Man"
    FULL_SEASON = "fullSeason"
    FULL_ROSTER = "fullRoster"
    NON_ROSTER_INVITEES = "nonRosterInvitees"
    ACTIVE = "active"
    ALL_TIME = "allTime"
    DEPTH_CHART = "depthChart"
    GAMEDAY = "gameday"
    COACH = "coach"

class RosterSlot(BaseModel):
    person: Person = Field(..., alias='person')
    position: Position = Field(..., alias='position')
    status: Optional[EnumGeneric] = Field(None, alias='status')
    jersey_number: Optional[str] = Field(None, alias='jerseyNumber')
    parentTeamId: Optional[int] = Field(None, alias='parentTeamId')


class Roster(BaseModel):

    roster_type: RosterTypeEnum = Field(..., alias='rosterType')
    team_id: int = Field(..., alias='teamId')
    roster: list[RosterSlot] = Field(..., alias='roster')