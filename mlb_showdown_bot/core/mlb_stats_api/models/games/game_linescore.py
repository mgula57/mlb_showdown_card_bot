from pydantic import BaseModel, Field
from typing import Optional, List

class GameLinescoreStatLine(BaseModel):
	"""Runs/hits/errors/LOB for a team segment in linescore payload."""

	runs: Optional[int] = None
	hits: Optional[int] = None
	errors: Optional[int] = None
	left_on_base: Optional[int] = Field(None, alias='leftOnBase')


class GameLinescoreInning(BaseModel):
	"""Single inning details in game linescore payload."""

	num: Optional[int] = None
	ordinal_num: Optional[str] = Field(None, alias='ordinalNum')
	home: Optional[GameLinescoreStatLine] = None
	away: Optional[GameLinescoreStatLine] = None


class GameLinescoreTeams(BaseModel):
	"""Aggregate team totals in linescore payload."""

	home: Optional[GameLinescoreStatLine] = None
	away: Optional[GameLinescoreStatLine] = None


class GameLinescorePerson(BaseModel):
	"""Person reference used in offense/defense lineups."""

	id: Optional[int] = None
	full_name: Optional[str] = Field(None, alias='fullName')
	link: Optional[str] = None


class GameLinescoreTeamRef(BaseModel):
	"""Team reference used in offense/defense lineups."""

	id: Optional[int] = None
	name: Optional[str] = None
	link: Optional[str] = None


class GameLinescoreAlignment(BaseModel):
	"""Offensive/defensive alignment details in linescore payload."""

	pitcher: Optional[GameLinescorePerson] = None
	catcher: Optional[GameLinescorePerson] = None
	first: Optional[GameLinescorePerson] = None
	second: Optional[GameLinescorePerson] = None
	third: Optional[GameLinescorePerson] = None
	shortstop: Optional[GameLinescorePerson] = None
	left: Optional[GameLinescorePerson] = None
	center: Optional[GameLinescorePerson] = None
	right: Optional[GameLinescorePerson] = None
	batter: Optional[GameLinescorePerson] = None
	on_deck: Optional[GameLinescorePerson] = Field(None, alias='onDeck')
	in_hole: Optional[GameLinescorePerson] = Field(None, alias='inHole')
	batting_order: Optional[int] = Field(None, alias='battingOrder')
	team: Optional[GameLinescoreTeamRef] = None


class GameLinescore(BaseModel):
	"""Linescore details for scheduled/live game payloads."""

	current_inning: Optional[int] = Field(None, alias='currentInning')
	current_inning_ordinal: Optional[str] = Field(None, alias='currentInningOrdinal')
	inning_state: Optional[str] = Field(None, alias='inningState')
	inning_half: Optional[str] = Field(None, alias='inningHalf')
	is_top_inning: Optional[bool] = Field(None, alias='isTopInning')
	scheduled_innings: Optional[int] = Field(None, alias='scheduledInnings')

	innings: Optional[List[GameLinescoreInning]] = None
	teams: Optional[GameLinescoreTeams] = None
	defense: Optional[GameLinescoreAlignment] = None
	offense: Optional[GameLinescoreAlignment] = None

	balls: Optional[int] = None
	strikes: Optional[int] = None
	outs: Optional[int] = None

	class Config:
		populate_by_name = True