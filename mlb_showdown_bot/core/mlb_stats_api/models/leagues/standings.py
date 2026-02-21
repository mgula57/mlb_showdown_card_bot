from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from .league import League
from .division import Division
from ..teams.team import Team


class StandingsType(str, Enum):
    REGULAR_SEASON = "regularSeason"
    WILD_CARD = "wildCard"
    DIVISION_LEADERS = "divisionLeaders"
    WILD_CARD_WITH_LEADERS = "wildCardWithLeaders"
    FIRST_HALF = "firstHalf"
    SECOND_HALF = "secondHalf"
    SPRING_TRAINING = "springTraining"
    POSTSEASON = "postseason"
    BY_DIVISION = "byDivision"
    BY_CONFERENCE = "byConference"
    BY_LEAGUE = "byLeague"
    BY_ORGANIZATION = "byOrganization"
    CURRENT_HALF = "currentHalf"


class Record(BaseModel):
    wins: int
    losses: int
    ties: Optional[int] = None
    percentage: Optional[str] = None


class TeamRecords(BaseModel):
    team: Team
    season: Optional[int] = None

    league_record: Optional[Record] = Field(None, alias='leagueRecord')


class Standings(BaseModel):
    """Model for standings data returned by the MLB Stats API"""

    standings_type: StandingsType = Field(..., alias='standingsType')
    league: Optional[League] = None
    division: Optional[Division] = None
    team_records: Optional[List[TeamRecords]] = Field(None, alias='teamRecords')