from pydantic import BaseModel, Field
from typing import Optional

from .enums import GameType
from .game_linescore import GameLinescore

from ..teams.team import Team
from ....database.classes import ShowdownBotCardCompact


class GameStatus(BaseModel):
    """Game status metadata."""

    abstract_game_state: Optional[str] = Field(None, alias='abstractGameState')
    coded_game_state: Optional[str] = Field(None, alias='codedGameState')
    detailed_state: Optional[str] = Field(None, alias='detailedState')
    status_code: Optional[str] = Field(None, alias='statusCode')
    start_time_tbd: Optional[bool] = Field(None, alias='startTimeTBD')
    abstract_game_code: Optional[str] = Field(None, alias='abstractGameCode')


class LeagueRecord(BaseModel):
    """Team record shown in schedule game response."""

    wins: Optional[int] = None
    losses: Optional[int] = None
    pct: Optional[str] = None

class GameProbablePitcher(BaseModel):
    """Probable pitcher information for a scheduled game."""

    id: Optional[int] = None
    full_name: Optional[str] = Field(None, alias='fullName')
    link: Optional[str] = None

    # OPTIONAL: Showdown Card Data
    card: Optional[ShowdownBotCardCompact] = Field(None, alias='showdownCard')

class GameTeamLine(BaseModel):
    """Away/home game team information."""

    team: Optional[Team] = None
    league_record: Optional[LeagueRecord] = Field(None, alias='leagueRecord')
    score: Optional[int] = None
    is_winner: Optional[bool] = Field(None, alias='isWinner')
    split_squad: Optional[bool] = Field(None, alias='splitSquad')
    series_number: Optional[int] = Field(None, alias='seriesNumber')

    probable_pitcher: Optional[GameProbablePitcher] = Field(None, alias='probablePitcher')


class GameTeams(BaseModel):
    """Container for away/home team data."""

    away: Optional[GameTeamLine] = None
    home: Optional[GameTeamLine] = None


class GameVenue(BaseModel):
    """Venue information for a game."""

    id: int
    name: Optional[str] = None
    link: Optional[str] = None


class GameContent(BaseModel):
    """Game content endpoint reference."""

    link: Optional[str] = None


class GameDecisionPitcher(BaseModel):
    """Pitcher information for game decisions (winner/loser/save)."""

    id: Optional[int] = None
    full_name: Optional[str] = Field(None, alias='fullName')
    link: Optional[str] = None


class GameDecisions(BaseModel):
    """Winning/losing/save pitcher details for a completed game."""

    winner: Optional[GameDecisionPitcher] = None
    loser: Optional[GameDecisionPitcher] = None
    save: Optional[GameDecisionPitcher] = None

class GameScheduled(BaseModel):
    """Model for top level game scheduled information from MLB Stats API"""

    game_pk: int = Field(..., alias='gamePk')
    game_guid: Optional[str] = Field(None, alias='gameGuid')
    link: Optional[str] = None
    game_type: Optional[GameType] = Field(None, alias='gameType')
    season: Optional[str] = None
    game_date: Optional[str] = Field(None, alias='gameDate')
    official_date: Optional[str] = Field(None, alias='officialDate')

    status: Optional[GameStatus] = None
    teams: Optional[GameTeams] = None
    venue: Optional[GameVenue] = None
    content: Optional[GameContent] = None
    linescore: Optional[GameLinescore] = None
    decisions: Optional[GameDecisions] = None

    is_tie: Optional[bool] = Field(None, alias='isTie')
    game_number: Optional[int] = Field(None, alias='gameNumber')
    public_facing: Optional[bool] = Field(None, alias='publicFacing')
    double_header: Optional[str] = Field(None, alias='doubleHeader')
    gameday_type: Optional[str] = Field(None, alias='gamedayType')
    tiebreaker: Optional[str] = None
    calendar_event_id: Optional[str] = Field(None, alias='calendarEventID')
    season_display: Optional[str] = Field(None, alias='seasonDisplay')
    day_night: Optional[str] = Field(None, alias='dayNight')
    description: Optional[str] = None
    scheduled_innings: Optional[int] = Field(None, alias='scheduledInnings')
    reverse_home_away_status: Optional[bool] = Field(None, alias='reverseHomeAwayStatus')
    inning_break_length: Optional[int] = Field(None, alias='inningBreakLength')
    games_in_series: Optional[int] = Field(None, alias='gamesInSeries')
    series_game_number: Optional[int] = Field(None, alias='seriesGameNumber')
    series_description: Optional[str] = Field(None, alias='seriesDescription')
    record_source: Optional[str] = Field(None, alias='recordSource')
    if_necessary: Optional[str] = Field(None, alias='ifNecessary')
    if_necessary_description: Optional[str] = Field(None, alias='ifNecessaryDescription')

    class Config:
        populate_by_name = True


