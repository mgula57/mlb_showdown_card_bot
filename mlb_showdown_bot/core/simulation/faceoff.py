from enum import Enum
from typing import Optional

from pydantic import BaseModel

from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.team_builder.team import Team as BuilderTeam, TeamRosterSlot
from ..database.postgres_db import PostgresDB
from .live_game import LiveMatch, LiveSide
from .matchup import MatchupClub, MatchupError
from .models import GameResult, ManagerPreference, SimTeamIdentity
from .postseason import top_seed_is_home
from .team import SimTeam

# ONLY A SINGLE GAME IS OFFERED TODAY. THE SIMULATOR, STORAGE AND API ARE ALL SHAPED AROUND A SERIES,
# SO WIDENING THIS IS WHAT TURNS A LONGER ONE ON.
SUPPORTED_BEST_OF = (1,)

class FaceoffError(MatchupError):
    """A Faceoff that can't be played as requested. The message is safe to show the user."""


class FaceoffSide(str, Enum):
    CHALLENGER = 'challenger'
    OPPONENT = 'opponent'

    @property
    def other(self) -> 'FaceoffSide':
        return FaceoffSide.CHALLENGER if self == FaceoffSide.OPPONENT else FaceoffSide.OPPONENT

    @property
    def schedule_key(self) -> str:
        """The name each club runs under in the engine. Fixed per side rather than the team's own
        abbreviation, which two teams can share and which would then collide `builder_sim_id`s."""
        return self.value.upper()


# ONE SIDE OF A FACEOFF, AS REQUESTED: THE SAME CLUB ANY MATCHUP TAKES.
FaceoffEntrant = MatchupClub


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


def faceoff_snapshot(entrant: FaceoffEntrant) -> 'FaceoffTeamSnapshot':
    """A side as it stood when its Faceoff was played."""
    return FaceoffTeamSnapshot(
        team_id=entrant.team.team_id,
        identity=SimTeam.builder_team_identity(entrant.team),
        total_points=entrant.total_points,
        allowed_sets=entrant.team.allowed_sets or [],
        roster=entrant.team.roster,
        starter_card_id=entrant.starter_card_id,
        manager=entrant.manager,
    )


def live_seats(home_side: FaceoffSide) -> dict[FaceoffSide, LiveSide]:
    """Which live game seat each Faceoff side takes, given who's home."""
    return {home_side: LiveSide.HOME, home_side.other: LiveSide.AWAY}


class TeamMatchupSimulator:
    """Plays two clubs against each other, first to a majority of `best_of` games.

    A Faceoff is one user of live games: each of its games is a live game with the sim in both
    seats, so it plays out at once (and a Faceoff someone plays by hand is the same game with a person
    in a seat, recorded through `FaceoffLiveContext`). The challenged team has home field. Each game
    is fielded fresh, so nothing (bullpen workload, rotation rest) carries from one game of a series
    to the next.
    """

    def __init__(self, challenger: FaceoffEntrant, opponent: FaceoffEntrant, seed: int, best_of: int = 1) -> None:
        if best_of < 1 or best_of % 2 == 0:
            raise FaceoffError('A Faceoff series needs an odd number of games.')
        self.entrants = {FaceoffSide.CHALLENGER: challenger, FaceoffSide.OPPONENT: opponent}
        self.seed = seed
        self.best_of = best_of

    def simulate(self) -> FaceoffResult:
        cards = {side: self._load_cards(entrant.team) for side, entrant in self.entrants.items()}
        wins = {side: 0 for side in FaceoffSide}
        wins_needed = self.best_of // 2 + 1

        games: list[FaceoffGameResult] = []
        for game_number in range(1, self.best_of + 1):
            home_side = self._home_side(game_number)
            seats = live_seats(home_side)
            live = LiveMatch(
                clubs={seats[side]: self.entrants[side] for side in FaceoffSide},
                cards={seats[side]: cards[side] for side in FaceoffSide},
                # GAME 1 PLAYS FROM THE FACEOFF'S OWN SEED, EACH LATER GAME FROM THE NEXT ONE.
                seed=self.seed + game_number - 1,
                sim_sides=frozenset(LiveSide),
            )
            try:
                state = live.replay([])
            except FaceoffError:
                raise
            except MatchupError as exc:
                raise FaceoffError(str(exc)) from exc

            winner_side = home_side if state.winner_side == LiveSide.HOME else home_side.other
            wins[winner_side] += 1
            games.append(FaceoffGameResult(game_number=game_number, home_side=home_side, game=state.game))
            if wins[winner_side] >= wins_needed:
                break

        return FaceoffResult(
            best_of=self.best_of,
            seed=self.seed,
            challenger=faceoff_snapshot(self.entrants[FaceoffSide.CHALLENGER]),
            opponent=faceoff_snapshot(self.entrants[FaceoffSide.OPPONENT]),
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
