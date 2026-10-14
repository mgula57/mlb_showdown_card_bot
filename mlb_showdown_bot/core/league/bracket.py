"""A league's postseason: a fixed, seeded bracket that's saved between sim chunks.

The MLB `Postseason` plays a whole bracket in one go and assumes real leagues and divisions. A
league needs neither, and needs to stop after a day or a round and pick up later, so its bracket
is plain data (`LeagueBracket.to_state` / `from_state`) the season runner advances game by game.
"""

import uuid
from dataclasses import dataclass, field
from typing import ClassVar, Optional

from pydantic import BaseModel, Field, model_validator

from ..simulation.models import PostseasonFormat, PostseasonResult, PostseasonRound, SeriesResult


class BracketConfig(BaseModel):
    """How many teams make the postseason, and how long each round's series is."""

    teams: int = Field(default=4)
    # ONE PER ROUND, FIRST ROUND FIRST - EACH ODD SO A SERIES ALWAYS HAS A WINNER
    series_lengths: list[int] = Field(default_factory=lambda: [5, 7])

    # (seed, seed) PAIRINGS FOR EACH SIZE'S FIRST ROUND, IN BRACKET ORDER - ADJACENT SERIES FEED THE
    # SAME NEXT-ROUND SERIES. A `None` SLOT IS A BYE: THAT SEED WAITS FOR THE NEXT ROUND.
    FIRST_ROUNDS: ClassVar[dict[int, list[tuple[int, Optional[int]]]]] = {
        2: [(1, 2)],
        4: [(1, 4), (2, 3)],
        6: [(1, None), (4, 5), (2, None), (3, 6)],
        8: [(1, 8), (4, 5), (2, 7), (3, 6)],
    }

    @property
    def round_count(self) -> int:
        return {0: 0, 2: 1, 4: 2, 6: 3, 8: 3}[self.teams]

    @model_validator(mode='after')
    def _valid_shape(self) -> 'BracketConfig':
        if self.teams not in (0, 2, 4, 6, 8):
            raise ValueError("Postseason teams must be 0, 2, 4, 6 or 8")
        if len(self.series_lengths) != self.round_count:
            raise ValueError(f"A {self.teams}-team postseason has {self.round_count} round(s) - give one series length per round")
        if any(length < 1 or length % 2 == 0 or length > 9 for length in self.series_lengths):
            raise ValueError("Series lengths must be odd: 1, 3, 5, 7 or 9")
        return self

    @staticmethod
    def round_labels(round_count: int) -> list[PostseasonRound]:
        """Rounds named from the final backwards, so the last two are always the Championship
        Series and World Series - the rounds that award series MVPs."""
        named_from_final = [PostseasonRound.WORLD_SERIES, PostseasonRound.CHAMPIONSHIP, PostseasonRound.DIVISIONAL, PostseasonRound.WILDCARD]
        return list(reversed(named_from_final[:round_count]))


@dataclass
class BracketSeries:
    series_id: str
    round_index: int
    length: int
    high_seed: Optional[int] = None    # HOME-FIELD ADVANTAGE
    low_seed: Optional[int] = None
    high_wins: int = 0
    low_wins: int = 0
    next_series_id: Optional[str] = None
    game_indexes: list[int] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.high_seed is not None and self.low_seed is not None

    @property
    def is_bye(self) -> bool:
        """A first-round slot with no opponent - its seed goes straight to round 2."""
        return self.round_index == 0 and self.low_seed is None

    @property
    def winner_seed(self) -> Optional[int]:
        needed = self.length // 2 + 1
        if self.high_wins >= needed:
            return self.high_seed
        if self.low_wins >= needed:
            return self.low_seed
        return None

    @property
    def games_played(self) -> int:
        return self.high_wins + self.low_wins

    def high_seed_hosts(self, game_number: int) -> bool:
        """Home field for game `game_number` (1-based): 2-3-2 for a best-of-7, 2-2-1 otherwise,
        and every game at the higher seed's park for a one- or three-game series."""
        if self.length <= 3:
            return True
        if self.length == 7:
            return game_number not in (3, 4, 5)
        return game_number not in (3, 4)


class LeagueBracket:
    """A seeded postseason bracket for a league, advanced one game at a time."""

    def __init__(self, config: BracketConfig, seeds: dict[int, str], series: list[BracketSeries]) -> None:
        self.config = config
        self.seeds = seeds          # SEED -> SCHEDULE KEY
        self.series = series

    @classmethod
    def create(cls, config: BracketConfig, seeded_keys: list[str]) -> 'LeagueBracket':
        """Build the bracket for teams ranked best first. Byes advance straight to round 2."""
        seeds = {seed: key for seed, key in enumerate(seeded_keys[:config.teams], start=1)}
        series: list[BracketSeries] = []
        previous: list[BracketSeries] = []
        for round_index in range(config.round_count):
            length = config.series_lengths[round_index]
            if round_index == 0:
                current = [
                    BracketSeries(series_id=str(uuid.uuid4()), round_index=0, length=length, high_seed=a, low_seed=b)
                    for a, b in config.FIRST_ROUNDS[config.teams]
                ]
            else:
                current = [
                    BracketSeries(series_id=str(uuid.uuid4()), round_index=round_index, length=length)
                    for _ in range(len(previous) // 2)
                ]
                for i, feeder in enumerate(previous):
                    feeder.next_series_id = current[i // 2].series_id
            series += current
            previous = current
        bracket = cls(config=config, seeds=seeds, series=series)
        for bye in [s for s in series if s.is_bye]:
            bracket._advance(bye, bye.high_seed)
        return bracket

    # MARK: State

    def to_state(self) -> dict:
        return {
            'config': self.config.model_dump(),
            'seeds': {str(seed): key for seed, key in self.seeds.items()},
            'series': [s.__dict__ for s in self.series],
        }

    @classmethod
    def from_state(cls, state: dict) -> 'LeagueBracket':
        return cls(
            config=BracketConfig(**state['config']),
            seeds={int(seed): key for seed, key in state['seeds'].items()},
            series=[BracketSeries(**s) for s in state['series']],
        )

    # MARK: Play

    def _by_id(self, series_id: str) -> BracketSeries:
        return next(s for s in self.series if s.series_id == series_id)

    @property
    def current_round(self) -> Optional[int]:
        """The earliest round with a series still to decide (a bye never counts), or None when
        the bracket is finished."""
        undecided = [s.round_index for s in self.series if not s.is_bye and s.winner_seed is None]
        return min(undecided) if undecided else None

    def todays_games(self) -> list[tuple[BracketSeries, str, str, int]]:
        """`(series, home_key, away_key, game_number)` for the next game of every undecided,
        ready series in the current round - one postseason day."""
        round_index = self.current_round
        if round_index is None:
            return []
        games = []
        for s in self.series:
            if s.round_index != round_index or not s.is_ready or s.winner_seed is not None:
                continue
            game_number = s.games_played + 1
            high, low = self.seeds[s.high_seed], self.seeds[s.low_seed]
            games.append((s, high, low, game_number) if s.high_seed_hosts(game_number) else (s, low, high, game_number))
        return games

    def record_game(self, series_id: str, winner_key: str, game_index: int) -> None:
        s = self._by_id(series_id)
        s.game_indexes.append(game_index)
        if self.seeds[s.high_seed] == winner_key:
            s.high_wins += 1
        else:
            s.low_wins += 1
        if s.winner_seed is not None:
            self._advance(s, s.winner_seed)

    def _advance(self, s: BracketSeries, seed: int) -> None:
        if s.next_series_id is None:
            return
        nxt = self._by_id(s.next_series_id)
        if nxt.high_seed is None:
            nxt.high_seed = seed
        else:
            nxt.low_seed = seed
        if nxt.is_ready and nxt.high_seed > nxt.low_seed:  # BETTER SEED HOSTS
            nxt.high_seed, nxt.low_seed = nxt.low_seed, nxt.high_seed

    @property
    def is_complete(self) -> bool:
        return self.current_round is None

    @property
    def champion_key(self) -> Optional[str]:
        final = next((s for s in self.series if s.next_series_id is None), None)
        return self.seeds[final.winner_seed] if final and final.winner_seed is not None else None

    # MARK: Results

    def round_label(self, round_index: int) -> PostseasonRound:
        return BracketConfig.round_labels(self.config.round_count)[round_index]

    def as_result(self, games_by_index: dict, series_player_stats: dict[str, list]) -> PostseasonResult:
        """The bracket as the sim's `PostseasonResult`, so the season summary and awards (series
        MVPs come from the last two rounds' `player_stats`) read it like any other postseason.
        Byes aren't series, so they're left out."""
        rounds: dict[str, list[SeriesResult]] = {}
        for s in self.series:
            if s.is_bye:
                continue
            winner = s.winner_seed
            rounds.setdefault(self.round_label(s.round_index).value, []).append(SeriesResult(
                round=self.round_label(s.round_index),
                league=None,
                home_team=self.seeds[s.high_seed] if s.high_seed else 'TBD',
                away_team=self.seeds[s.low_seed] if s.low_seed else 'TBD',
                home_team_seed=s.high_seed,
                away_team_seed=s.low_seed,
                home_team_wins=s.high_wins,
                away_team_wins=s.low_wins,
                winner=self.seeds[winner] if winner else None,
                games=[games_by_index[i] for i in s.game_indexes if i in games_by_index],
                player_stats=series_player_stats.get(s.series_id, []) if winner else [],
            ))
        return PostseasonResult(format=PostseasonFormat.WORLD_SERIES, rounds=rounds, world_series_winner=self.champion_key)
