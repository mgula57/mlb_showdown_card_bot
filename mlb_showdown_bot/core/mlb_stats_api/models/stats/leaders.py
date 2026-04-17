
from pydantic import BaseModel, Field
from typing import Optional, List
from ..generic import EnumGeneric

# ----------------------------------------------------------------
# MARK: - Leaders (/api/v1/stats/leaders)
# ----------------------------------------------------------------

class LeaderPerson(BaseModel):
    """Minimal person object as returned in leader entries."""
    model_config = {"populate_by_name": True}

    id: int
    full_name: Optional[str] = Field(None, alias='fullName')
    first_name: Optional[str] = Field(None, alias='firstName')
    last_name: Optional[str] = Field(None, alias='lastName')
    link: Optional[str] = None


class LeaderTeam(BaseModel):
    """Minimal team object as returned in leader entries."""
    id: Optional[int] = None
    name: Optional[str] = None
    link: Optional[str] = None
    abbreviation: Optional[str] = None


class LeaderLeague(BaseModel):
    """Minimal league object as returned in leader entries."""
    id: Optional[int] = None
    name: Optional[str] = None
    link: Optional[str] = None
    abbreviation: Optional[str] = None


class LeaderSport(BaseModel):
    """Minimal sport object as returned in leader entries."""
    id: Optional[int] = None
    link: Optional[str] = None
    abbreviation: Optional[str] = None


class PlayerLeader(BaseModel):
    """A single entry in a stat leaders list (PlayerLeaderRestObject)."""
    model_config = {"populate_by_name": True}

    rank: Optional[int] = None
    value: Optional[str] = None
    season: Optional[str] = None
    num_teams: Optional[int] = Field(None, alias='numTeams')
    person: Optional[LeaderPerson] = None
    team: Optional[LeaderTeam] = None
    league: Optional[LeaderLeague] = None
    sport: Optional[LeaderSport] = None


class LeaderLimits(BaseModel):
    """Limit criteria applied to a leaders query."""
    amount: Optional[str] = None
    type: Optional[str] = None
    compare_type: Optional[str] = Field(None, alias='compareType')


class LeaderLimitMetadata(BaseModel):
    """Pagination metadata for a leaders response."""
    model_config = {"populate_by_name": True}

    limit: Optional[int] = None
    offset: Optional[int] = None
    additional_ties: Optional[int] = Field(None, alias='additionalTies')

class LeadersGameType(BaseModel):
    """Game type criteria applied to a leaders query."""
    id: Optional[str] = None
    description: Optional[str] = None


class LeadersGroup(BaseModel):
    """A single stat-category block within the leaders response (LeadersRestObject)."""
    model_config = {"populate_by_name": True}

    leader_category: Optional[str] = Field(None, alias='leaderCategory')
    stat_group: Optional[str] = Field(None, alias='statGroup')
    season: Optional[str] = None
    game_type: Optional[LeadersGameType] = Field(None, alias='gameType')
    total_splits: Optional[int] = Field(None, alias='totalSplits')
    limits: Optional[LeaderLimits] = None
    limit_metadata: Optional[LeaderLimitMetadata] = Field(None, alias='limitMetadata')
    leaders: Optional[List[PlayerLeader]] = None
    team: Optional[LeaderTeam] = None
    league: Optional[LeaderLeague] = None


class LeagueLeadersResponse(BaseModel):
    """Top-level response from GET /api/v1/stats/leaders (LeagueLeaderContainerRestObject)."""
    copyright: Optional[str] = None
    league_leaders: Optional[List[LeadersGroup]] = Field(None, alias='leagueLeaders')