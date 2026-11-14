"""One game between two clubs built from builder-shaped teams, outside any season.

The pieces every such game shares, whatever it's for: a Faceoff (`faceoff.py`), a live game two
people play (`live_game.py`), or anything later built on either. A club can be any team the Team
Builder can show (a user's team, an official one, a historical MLB club, an Era Roster), since all
of them come as the same `Team`.
"""

from datetime import date
from random import Random
from typing import Optional

from pydantic import BaseModel

from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.team_builder.team import Team as BuilderTeam
from .controller import GameController
from .game import Game
from .models import ManagerPreference
from .stats import builder_sim_id
from .team import SimTeam

# A YEAR WITH NO LEAGUE-AVERAGE DATA, SO `league_steal_factor` IS A NO-OP: TWO CLUBS OUTSIDE A SEASON
# HAVE NO RUNNING ENVIRONMENT TO INHERIT. PLAYERS NEVER SEE THIS DATE - RESULTS CARRY THE DAY PLAYED.
MATCHUP_START_DATE = date(1800, 4, 1)


class MatchupError(ValueError):
    """A matchup that can't be played as requested. The message is safe to show the user."""


class MatchupClub(BaseModel):
    """One side of a matchup, as requested."""

    team: BuilderTeam
    total_points: int = 0
    starter_card_id: Optional[str] = None  # NONE = THE ROTATION'S FIRST STARTER
    manager: Optional[ManagerPreference] = None


def build_club(club: MatchupClub, cards: dict[str, ShowdownPlayerCard], schedule_key: str) -> SimTeam:
    """Field a club under `schedule_key`, the name it plays under in the engine. Fixed per side
    rather than the team's own abbreviation, which two clubs can share and which would then collide
    `builder_sim_id`s."""
    if any(slot.card_id not in cards for slot in club.team.roster):
        raise MatchupError(f"{club.team.name} has a card that can no longer be loaded.")
    sim_team = SimTeam.from_builder_team(
        team=club.team, cards=cards, year=MATCHUP_START_DATE.year, name_override=schedule_key, manager=club.manager,
    )
    if club.starter_card_id and not sim_team.rotation.move_to_front(builder_sim_id(schedule_key, club.starter_card_id)):
        raise MatchupError(f"That starter isn't in the {club.team.name} rotation.")
    return sim_team


def setup_game(home: SimTeam, away: SimTeam, game_number: int = 1, game_date: date = MATCHUP_START_DATE) -> Game:
    """A game between two fielded clubs, starters picked by rest as in a postseason series."""
    game = Game(
        index=game_number, date=game_date,
        home_team_name=home.name, away_team_name=away.name,
        home_team_game_number=game_number, away_team_game_number=game_number,
    )
    game.setup(home_team=home, away_team=away, postseason=True)
    return game


def play_game(game: Game, rng: Random, controller: Optional[GameController] = None) -> None:
    # NO RANDOM +/- ROLL NUDGES: THESE GAMES SHOW THEIR DICE, SO THEY SHOULD BE THE RAW D20S.
    game.simulate(rng=rng, collect_log=True, collect_box_score=True, random_roll_adjustments=False, controller=controller)
