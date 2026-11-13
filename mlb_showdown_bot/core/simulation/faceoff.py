from datetime import date, timedelta
from enum import Enum
from random import Random
from typing import Optional

from pydantic import BaseModel

from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.team_builder.team import Team as BuilderTeam, TeamRosterSlot
from ..database.postgres_db import PostgresDB
from .game import Game
from .models import GameResult, ManagerPreference, SimTeamIdentity
from .postseason import top_seed_is_home
from .stats import builder_sim_id
from .team import SimTeam

# ONLY A SINGLE GAME IS OFFERED TODAY. THE SIMULATOR, STORAGE AND API ARE ALL SHAPED AROUND A SERIES,
# SO WIDENING THIS IS WHAT TURNS A LONGER ONE ON.
SUPPORTED_BEST_OF = (1,)

# A YEAR WITH NO LEAGUE-AVERAGE DATA, SO `league_steal_factor` IS A NO-OP: TWO BUILDER TEAMS HAVE NO
# SEASON, AND THEIR GAME SHOULDN'T INHERIT ONE'S RUNNING ENVIRONMENT. PLAYERS NEVER SEE THIS DATE -
# THE RESULT CARRIES THE DAY IT WAS PLAYED.
_SERIES_START_DATE = date(1800, 4, 1)


class FaceoffError(ValueError):
    """A Faceoff that can't be played as requested. The message is safe to show the user."""


class FaceoffSide(str, Enum):
    CHALLENGER = 'challenger'
    OPPONENT = 'opponent'

    @property
    def schedule_key(self) -> str:
        """The name each club runs under in the engine. Fixed per side rather than the team's own
        abbreviation, which two teams can share and which would then collide `builder_sim_id`s."""
        return self.value.upper()


class FaceoffEntrant(BaseModel):
    """One side of a Faceoff, as requested."""

    team: BuilderTeam
    total_points: int = 0
    starter_card_id: Optional[str] = None  # NONE = THE ROTATION'S FIRST STARTER
    manager: Optional[ManagerPreference] = None


class FaceoffTeamSnapshot(BaseModel):
    """A side as it stood when the Faceoff was played, so replays outlive edits to the team."""

    team_id: Optional[str] = None
    identity: SimTeamIdentity
    total_points: int = 0
    allowed_sets: list[str] = []
    roster: list[TeamRosterSlot] = []
    starter_card_id: Optional[str] = None
    manager: Optional[ManagerPreference] = None


class FaceoffGameResult(BaseModel):
    game_number: int
    home_side: FaceoffSide
    game: GameResult


class FaceoffResult(BaseModel):
    best_of: int
    seed: int
    challenger: FaceoffTeamSnapshot
    opponent: FaceoffTeamSnapshot
    challenger_wins: int = 0
    opponent_wins: int = 0
    winner_side: Optional[FaceoffSide] = None
    games: list[FaceoffGameResult] = []


class TeamMatchupSimulator:
    """Plays two builder teams against each other, first to a majority of `best_of` games.

    Both clubs stay the same objects from game to game, so bullpen workload carries through a
    series, and starters come from the postseason's rest-based selection. The challenged team has
    home field.
    """

    def __init__(self, challenger: FaceoffEntrant, opponent: FaceoffEntrant, seed: int, best_of: int = 1) -> None:
        if best_of < 1 or best_of % 2 == 0:
            raise FaceoffError('A Faceoff series needs an odd number of games.')
        self.entrants = {FaceoffSide.CHALLENGER: challenger, FaceoffSide.OPPONENT: opponent}
        self.seed = seed
        self.best_of = best_of

    def simulate(self) -> FaceoffResult:
        clubs = {side: self._build_club(side) for side in FaceoffSide}
        rng = Random(self.seed)
        wins = {side: 0 for side in FaceoffSide}
        wins_needed = self.best_of // 2 + 1

        games: list[FaceoffGameResult] = []
        game_date = _SERIES_START_DATE
        previous_home: Optional[FaceoffSide] = None
        for game_number in range(1, self.best_of + 1):
            home_side = self._home_side(game_number)
            away_side = FaceoffSide.CHALLENGER if home_side == FaceoffSide.OPPONENT else FaceoffSide.OPPONENT
            # ONE DAY BETWEEN GAMES, PLUS A TRAVEL DAY WHEN THE SERIES CHANGES PARKS.
            if previous_home is not None:
                game_date += timedelta(days=2 if home_side != previous_home else 1)
            previous_home = home_side

            game = Game(
                index=game_number, date=game_date,
                home_team_name=clubs[home_side].name, away_team_name=clubs[away_side].name,
                home_team_game_number=game_number, away_team_game_number=game_number,
            )
            game.setup(home_team=clubs[home_side], away_team=clubs[away_side], postseason=True)
            # NO RANDOM +/- ROLL NUDGES: THE REPLAY SHOWS ITS DICE, SO THEY SHOULD BE THE RAW D20S.
            game.simulate(rng=rng, collect_log=True, collect_box_score=True, random_roll_adjustments=False)

            winner_side = home_side if game.winning_team is clubs[home_side] else away_side
            wins[winner_side] += 1
            games.append(FaceoffGameResult(
                game_number=game_number, home_side=home_side,
                game=game.as_result().model_copy(update={'date': date.today()}),
            ))
            if wins[winner_side] >= wins_needed:
                break

        return FaceoffResult(
            best_of=self.best_of,
            seed=self.seed,
            challenger=self._snapshot(FaceoffSide.CHALLENGER, clubs),
            opponent=self._snapshot(FaceoffSide.OPPONENT, clubs),
            challenger_wins=wins[FaceoffSide.CHALLENGER],
            opponent_wins=wins[FaceoffSide.OPPONENT],
            winner_side=next((side for side, count in wins.items() if count >= wins_needed), None),
            games=games,
        )

    def _home_side(self, game_number: int) -> FaceoffSide:
        return FaceoffSide.OPPONENT if top_seed_is_home(game_number, self.best_of) else FaceoffSide.CHALLENGER

    def _load_cards(self, team: BuilderTeam) -> dict[str, ShowdownPlayerCard]:
        """Hydrate a roster, refusing one with a missing card: a hole in the lineup would otherwise
        surface as a confusing failure partway through the game."""
        with PostgresDB() as db:
            cards = db.fetch_cards_for_roster_slots(slots=team.roster, strip_diagnostics=True)
        if any(slot.card_id not in cards for slot in team.roster):
            raise FaceoffError(f"{team.name} has a card that can no longer be loaded.")
        return cards

    def _build_club(self, side: FaceoffSide) -> SimTeam:
        entrant = self.entrants[side]
        club = SimTeam.from_builder_team(
            team=entrant.team, cards=self._load_cards(entrant.team), year=_SERIES_START_DATE.year,
            name_override=side.schedule_key, manager=entrant.manager,
        )
        if entrant.starter_card_id:
            starter_id = builder_sim_id(side.schedule_key, entrant.starter_card_id)
            if not club.rotation.move_to_front(starter_id):
                raise FaceoffError(f"That starter isn't in the {entrant.team.name} rotation.")
        return club

    def _snapshot(self, side: FaceoffSide, clubs: dict[FaceoffSide, SimTeam]) -> FaceoffTeamSnapshot:
        entrant = self.entrants[side]
        return FaceoffTeamSnapshot(
            team_id=entrant.team.team_id,
            identity=clubs[side].identity,
            total_points=entrant.total_points,
            allowed_sets=entrant.team.allowed_sets or [],
            roster=entrant.team.roster,
            starter_card_id=entrant.starter_card_id,
            manager=entrant.manager,
        )
