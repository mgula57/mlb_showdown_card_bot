from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ..card.team_builder.team import CardSource
from ..shared.player_position import PlayerSubType, PlayerType
from .awards import AwardsBuilder, SeasonAwards
from .models import ManagerPreference, SeasonSimulationResult, SimTeamIdentity, StandingsResult, TeamRecord
from .reporting import HITTER_CATEGORIES, PITCHER_CATEGORIES
from .stats import SimStatLine, StatCategory, Stats, builder_sim_id, real_card_id

# LEADERBOARD DEPTH. SMALL ON PURPOSE - THE FULL 1100-PLAYER `player_stats` LIST IS ~390 KB AND
# THE RESULT SCREEN ONLY EVER SHOWS A TOP TEN.
_LEADERBOARD_LIMIT = 10

# (STAT, IS_DESC) PER LEADERBOARD - KEYS PlayerSubType.value IN THE BUILT `top_players` DICT.
_LEADERBOARD_STATS: dict[PlayerSubType, tuple[str, bool]] = {
    PlayerSubType.POSITION_PLAYER: ('ops', True),
    PlayerSubType.STARTING_PITCHER: ('era', False),
    PlayerSubType.RELIEF_PITCHER: ('era', False),
}


class SimGameLine(BaseModel):
    """One of the team's games, trimmed to what a schedule/streak view needs.

    Linescores and box scores are dropped - they are 3.2 MB of the 6.1 MB result and nothing on
    the season screen reads them.
    """

    date: str
    opponent: str
    opponent_identity: Optional[SimTeamIdentity] = None
    is_home: bool
    runs_scored: int
    runs_allowed: int
    is_win: bool
    wins: int      # RUNNING RECORD AFTER THIS GAME - BACKS THE 162-0 STREAK CHART
    losses: int


class SimPostseasonGameLine(BaseModel):
    """One game within a postseason series, trimmed the same way `SimGameLine` trims the regular
    season - no linescore/log/box score, just enough for a per-game results table."""

    date: str
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0
    winner: Optional[str] = None


class SimSeriesLine(BaseModel):
    """A postseason series, with its games trimmed down for a results breakdown."""

    round: str
    league: Optional[str] = None
    home_team: str
    away_team: str
    home_team_wins: int = 0
    away_team_wins: int = 0
    winner: Optional[str] = None
    games: list[SimPostseasonGameLine] = []


class SimSeasonGameLine(BaseModel):
    """One game of the season, trimmed the same way `SimGameLine` trims a single team's games -
    no linescore/log/box score. Populated only in open-sim mode (`team_abbr` is None), where it
    backs every club's schedule/streak view instead of just one team's `SimGameLine` list."""

    date: str
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0


class SimTeamSeason(BaseModel):
    """How the user's team finished."""

    identity: Optional[SimTeamIdentity] = None
    replaced_abbr: Optional[str] = None
    wins: int = 0
    losses: int = 0
    win_pct: float = 0.0
    points: int = 0
    division: Optional[str] = None
    division_rank: Optional[int] = None
    division_size: Optional[int] = None
    games_back: Optional[float] = None
    playoff_seeding: Optional[int] = None
    made_playoffs: bool = False
    is_champion: bool = False
    longest_win_streak: int = 0
    longest_losing_streak: int = 0


class SeasonSimSummary(BaseModel):
    """Everything the season result screen renders, and nothing else.

    Built in the worker straight after `simulate()` so the full ~6 MB `SeasonSimulationResult`
    can be freed and only this (~100 KB) is ever persisted.
    """

    # META
    year: int
    set: str
    seed: Optional[int] = None
    runtime_seconds: float = 0.0
    schedule_length: int = 0
    original_schedule_length: int = 0
    generated_at: datetime

    # NONE IN OPEN-SIM MODE (`team_abbr` UNSET) - THERE IS NO SINGLE FOCUS TEAM, SO THE CLIENT
    # PICKS ONE VIA `useClubSeason` INSTEAD. SET FOR A TAKEOVER/CHALLENGE RUN, AS BEFORE.
    team: Optional[SimTeamSeason] = None
    games: list[SimGameLine] = []
    players: list[SimStatLine] = []

    # EVERY GAME OF THE SEASON, ONCE - ONLY POPULATED IN OPEN-SIM MODE. BACKS THE CLUB BROWSER
    # (`useClubSeason`) SO SWITCHING FOCUS CLUB NEVER NEEDS A REFETCH. EMPTY FOR A TAKEOVER RUN,
    # WHICH ALREADY HAS ITS OWN TEAM-SCOPED `games` LIST ABOVE.
    season_games: list[SimSeasonGameLine] = []

    # SCHEDULE KEY -> (WINS, LOSSES) EACH CLUB STARTED THE SIM WITH - POPULATED ONLY FOR A
    # REST-OF-SEASON PROJECTION. EMPTY (EVERY CLUB STARTED 0-0) FOR A FULL-SEASON SIM.
    seeded_records: dict[str, tuple[int, int]] = {}

    # LEAST-STALE stats_modified_date ACROSS EVERY PLAYER WHOSE REAL STATS WERE MERGED IN. NONE
    # UNLESS THE RUN USED `config.merge_real_stats` - THE ARCHIVE HOLDS ONE CURRENT SNAPSHOT PER
    # PLAYER-YEAR, NOT A HISTORY, SO THIS MAY LAG THE RUN'S OWN resume_as_of_date. SHOW THIS DATE,
    # NOT THAT ONE, WHEN DESCRIBING WHAT THE MERGED STATS COVER.
    real_stats_as_of: Optional[datetime] = None

    # SCHEDULE KEYS OF EVERY CLUB REPLACED BY A BUILDER TEAM THIS RUN, FOR BADGING THEM IN A
    # CLUB PICKER. EMPTY FOR A PLAIN SIM.
    takeover_abbrs: list[str] = []

    # SCHEDULE KEY -> THE CUSTOM MANAGER TENDENCIES THAT CLUB PLAYED WITH THIS RUN. ONLY NON-NEUTRAL
    # PROFILES ARE RECORDED (EMPTY FOR A PLAIN SIM), SO THE RESULT/LEADERBOARD SCREENS CAN SHOW
    # WHAT STRATEGY A RUN USED.
    manager_preferences: dict[str, ManagerPreference] = {}

    standings: StandingsResult
    postseason: list[SimSeriesLine] = []
    champion: Optional[str] = None

    # SCHEDULE KEY -> BRANDING, FOR EVERY TEAM IN THE LEAGUE. STANDINGS ROWS, GAME OPPONENTS AND
    # POSTSEASON SERIES ALL REFER TO TEAMS BY SCHEDULE KEY, WHICH FOR THE TAKEOVER TEAM IS THE
    # CLUB IT REPLACED - THIS IS HOW THE UI RESOLVES ANY OF THEM BACK TO A NAME AND COLORS.
    identities: dict[str, SimTeamIdentity] = {}

    # KEYED BY PlayerSubType.value ('position_player' / 'starting_pitcher' / 'relief_pitcher').
    top_players: dict[str, list[SimStatLine]] = {}

    # SIM vs REAL LEAGUE AVERAGES. EMPTY WHEN THE SEASON HAS NO REAL BASELINE.
    league_totals: dict[str, SimStatLine] = {}
    real_league_averages: dict[str, SimStatLine] = {}

    awards: SeasonAwards = SeasonAwards()


class SeasonSummaryBuilder:
    """Projects a `SeasonSimulationResult` down to the fields the result screen needs.

    The parallel of `SeasonReport`, which can only print. Column sets are shared with it so the
    web tables and the CLI tables never drift.
    """

    def __init__(self, result: SeasonSimulationResult, team_abbr: Optional[str] = None) -> None:
        self.result = result
        # SCHEDULE KEY OF THE TEAM THE SUMMARY IS CENTERED ON. NONE MEANS OPEN-SIM MODE - THE
        # SUMMARY COVERS EVERY CLUB AND THE CLIENT PICKS A FOCUS CLUB ITSELF.
        self.team_abbr = team_abbr

    @property
    def roster_player_ids(self) -> dict[str, set[str]]:
        """Schedule key -> stat-engine player ids on that club's takeover roster, for every
        takeover this run (see `SeasonSimulationConfig.all_takeovers`).

        Statlines report the builder team's own abbreviation, which is deliberately not the
        schedule key the takeover runs under, so matching on team would find nothing here.
        `from_builder_team` keys each drafted player under `builder_sim_id(schedule_key, card_id)`
        (the schedule key being the replaced club's abbr), so membership is the exact filter.
        Empty when there is no takeover.
        """
        return {
            abbr: {builder_sim_id(abbr, slot.card_id) for slot in team.roster}
            for abbr, team in self.result.config.all_takeovers.items()
        }

    def build(self) -> SeasonSimSummary:
        result = self.result
        is_open_sim = self.team_abbr is None
        record, division, rank, size = (None, None, None, None) if is_open_sim else self._find_record()
        games = [] if is_open_sim else self._build_games()
        season_games = self._build_season_games() if is_open_sim else []
        postseason = self._build_postseason()

        return SeasonSimSummary(
            year=result.config.year,
            set=result.config.set.value,
            seed=result.config.seed,
            runtime_seconds=round(result.runtime_seconds, 1),
            schedule_length=result.schedule_length,
            original_schedule_length=result.original_schedule_length,
            generated_at=result.ended_at,
            team=None if is_open_sim else self._build_team_season(record, division, rank, size, games, postseason),
            games=games,
            season_games=season_games,
            players=self._build_players(),
            standings=result.standings,
            postseason=postseason,
            identities=self._build_identities(),
            champion=result.postseason.world_series_winner if result.postseason else None,
            top_players={sub_type.value: self._leaderboard(sub_type) for sub_type in PlayerSubType},
            league_totals=self._league_lines(result.league_totals),
            real_league_averages=self._league_lines(result.real_league_averages),
            awards=AwardsBuilder(result=result).build(),
            takeover_abbrs=list(self.roster_player_ids.keys()),
            manager_preferences={
                abbr: pref for abbr, pref in result.config.all_manager_preferences.items()
                if not pref.is_neutral
            },
            seeded_records=result.seeded_records,
            real_stats_as_of=result.real_stats_as_of,
        )

    # ------------------------------------------------------------------
    # TEAM
    # ------------------------------------------------------------------

    def _build_identities(self) -> dict[str, SimTeamIdentity]:
        """Schedule key -> branding, plus an alias for a takeover roster's own abbreviation.

        Standings/schedule/postseason all key off the schedule key, which for a takeover team is
        the replaced club's abbreviation (see `SimTeam.from_builder_team`). Player statlines,
        though, report the builder team's own abbreviation - so without the alias, resolving a
        takeover player's team colors by `SimStatLine.team` would miss every entry here.
        """
        identities = {
            record.name: record.identity
            for records in self.result.standings.divisions.values()
            for record in records
            if record.identity is not None
        }
        for replaces_abbr, takeover_team in self.result.config.all_takeovers.items():
            replaced_identity = identities.get(replaces_abbr)
            if replaced_identity is not None:
                identities[takeover_team.abbreviation] = replaced_identity
        return identities

    def _find_record(self) -> tuple[Optional[TeamRecord], Optional[str], Optional[int], Optional[int]]:
        """The team's standings row plus where it finished in its division."""
        for division, records in self.result.standings.divisions.items():
            for index, record in enumerate(records):
                if record.name == self.team_abbr:
                    return record, division, index + 1, len(records)
        return None, None, None, None

    def _build_team_season(self, record: Optional[TeamRecord], division: Optional[str], rank: Optional[int], size: Optional[int], games: list[SimGameLine], postseason: list[SimSeriesLine]) -> SimTeamSeason:
        postseason_teams = {
            team
            for series in postseason
            for team in (series.home_team, series.away_team)
        }
        champion = self.result.postseason.world_series_winner if self.result.postseason else None
        wins, losses = self._longest_streaks(games)

        if record is None:
            return SimTeamSeason(replaced_abbr=self.team_abbr, longest_win_streak=wins, longest_losing_streak=losses)

        return SimTeamSeason(
            identity=record.identity,
            replaced_abbr=self.team_abbr,
            wins=record.wins,
            losses=record.losses,
            win_pct=record.win_pct,
            points=record.points,
            division=division,
            division_rank=rank,
            division_size=size,
            games_back=record.games_back,
            playoff_seeding=record.playoff_seeding,
            made_playoffs=self.team_abbr in postseason_teams,
            is_champion=champion == self.team_abbr,
            longest_win_streak=wins,
            longest_losing_streak=losses,
        )

    @staticmethod
    def _longest_streaks(games: list[SimGameLine]) -> tuple[int, int]:
        best_win = best_loss = run = 0
        last: Optional[bool] = None
        for game in games:
            run = run + 1 if game.is_win == last else 1
            last = game.is_win
            if game.is_win:
                best_win = max(best_win, run)
            else:
                best_loss = max(best_loss, run)
        return best_win, best_loss

    # ------------------------------------------------------------------
    # GAMES
    # ------------------------------------------------------------------

    def _build_games(self) -> list[SimGameLine]:
        lines: list[SimGameLine] = []
        # 0-0 UNLESS THIS IS A REST-OF-SEASON PROJECTION, IN WHICH CASE THE RUNNING RECORD PICKS
        # UP FROM WHERE THE REAL SEASON LEFT OFF - SEE `SeasonSimulationConfig.resume_from_real_season`.
        wins, losses = self.result.seeded_records.get(self.team_abbr, (0, 0))
        for game in self.result.games:
            is_home = game.home_team == self.team_abbr
            if not is_home and game.away_team != self.team_abbr:
                continue
            scored = game.home_score if is_home else game.away_score
            allowed = game.away_score if is_home else game.home_score
            is_win = scored > allowed
            wins, losses = (wins + 1, losses) if is_win else (wins, losses + 1)
            lines.append(SimGameLine(
                date=str(game.date),
                opponent=game.away_team if is_home else game.home_team,
                opponent_identity=game.away_team_identity if is_home else game.home_team_identity,
                is_home=is_home,
                runs_scored=scored,
                runs_allowed=allowed,
                is_win=is_win,
                wins=wins,
                losses=losses,
            ))
        return lines

    def _build_season_games(self) -> list[SimSeasonGameLine]:
        """Every game of the season, once - the club browser (`useClubSeason` on the frontend)
        derives each club's own schedule/streaks from this instead of a `SimGameLine` list per
        club, which would duplicate every game 30x over."""
        return [
            SimSeasonGameLine(
                date=str(game.date),
                home_team=game.home_team,
                away_team=game.away_team,
                home_score=game.home_score,
                away_score=game.away_score,
            )
            for game in self.result.games
        ]

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------

    def _categories(self, player_type: PlayerType) -> list[StatCategory]:
        return HITTER_CATEGORIES if player_type == PlayerType.HITTER else PITCHER_CATEGORIES

    def _line(self, stats: Stats, player_type: PlayerType) -> SimStatLine:
        """Every player-facing statline carries a `(id, card_source)` pair `useCardMap` on the
        frontend can resolve straight to a real card - not just the user's own roster. Builder-
        drafted players (tournament teams, a takeover roster) resolve via `config.card_sources`;
        every other player is a real-season card from the bot archive (`CardSource.BOT`).
        """
        return SimStatLine.build(
            stats=stats,
            categories=self._categories(player_type),
            league_stats=self.result.league_totals.get(player_type.value),
            woba_weights=self.result.woba_weights,
            card_source=self.result.config.card_sources.get(real_card_id(stats.id), CardSource.BOT.value),
        )

    def _build_players(self) -> list[SimStatLine]:
        """In open-sim mode (`team_abbr` is None), every player in the season - and every
        takeover roster's statlines get their `team` rewritten from the builder team's own
        abbreviation to the schedule key it actually plays under, so the club browser can filter
        on `team` the same way for a takeover club as for a real one (see `roster_player_ids`).

        Otherwise, unchanged: only the focus team's own players, `team` left as reported.
        """
        is_open_sim = self.team_abbr is None
        if is_open_sim:
            selected = [stats for stats in self.result.player_stats if stats.player_type is not None]
            card_id_to_abbr = {
                card_id: abbr
                for abbr, card_ids in self.roster_player_ids.items()
                for card_id in card_ids
            }
        else:
            roster_ids = self.roster_player_ids.get(self.team_abbr)
            on_team = (
                (lambda stats: stats.id in roster_ids) if roster_ids is not None
                else (lambda stats: stats.team == self.team_abbr)
            )
            selected = [stats for stats in self.result.player_stats if stats.player_type is not None and on_team(stats)]
            card_id_to_abbr = {}

        lines: list[SimStatLine] = []
        for stats in selected:
            line = self._line(stats, stats.player_type)
            resolved_abbr = card_id_to_abbr.get(stats.id)
            if resolved_abbr is not None and resolved_abbr != line.team:
                line = line.model_copy(update={'team': resolved_abbr})
            lines.append(line)
        return sorted(lines, key=lambda line: (line.player_type or '', -line.points))

    def _leaderboard(self, player_sub_type: PlayerSubType) -> list[SimStatLine]:
        player_type = player_sub_type.parent_type
        stat, is_desc = _LEADERBOARD_STATS[player_sub_type]
        min_ip = 0
        if player_type == PlayerType.PITCHER:
            min_ip = self.result.stats_min_ip_rp if player_sub_type == PlayerSubType.RELIEF_PITCHER else self.result.stats_min_ip
        leaders = self.result.top_players(
            player_type=player_type.value, stat=stat, limit=_LEADERBOARD_LIMIT, is_desc=is_desc,
            min_pa=self.result.stats_min_pa if player_type == PlayerType.HITTER else 0,
            min_ip=min_ip, player_sub_type=player_sub_type,
        )
        return [self._line(stats, player_type) for stats in leaders]

    def _league_lines(self, totals: dict[str, Stats]) -> dict[str, SimStatLine]:
        lines: dict[str, SimStatLine] = {}
        for type_value, stats in totals.items():
            try:
                player_type = PlayerType(type_value)
            except ValueError:
                continue
            lines[type_value] = self._line(stats, player_type)
        return lines

    # ------------------------------------------------------------------
    # POSTSEASON
    # ------------------------------------------------------------------

    def _build_postseason(self) -> list[SimSeriesLine]:
        if self.result.postseason is None:
            return []
        return [
            SimSeriesLine(
                round=round_value,
                league=series.league,
                home_team=series.home_team,
                away_team=series.away_team,
                home_team_wins=series.home_team_wins,
                away_team_wins=series.away_team_wins,
                winner=series.winner,
                games=[
                    SimPostseasonGameLine(
                        date=str(game.date), home_team=game.home_team, away_team=game.away_team,
                        home_score=game.home_score, away_score=game.away_score, winner=game.winner,
                    )
                    for game in series.games
                ],
            )
            for round_value, series_list in self.result.postseason.rounds.items()
            for series in series_list
        ]
