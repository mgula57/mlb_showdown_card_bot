"""Playing a league season in chunks.

`core/simulation`'s `Season` plays a whole season in one in-memory pass. A league season is
played a day, a week, or a round at a time, with owners free to change lineups in between, so
this runner rebuilds every team from its saved roster before each chunk and restores what the
engine carries from one game to the next from `league_season.state`:

  - each team's record, runs for/against, rotation position, recent bullpen workload,
    consecutive starts, and (postseason) starters' rest
  - every player's running regular-season and postseason stat totals
  - the postseason bracket, once there is one

Games themselves go through the same `Game.setup` / `Game.simulate` path every other sim mode
uses. After each chunk the runner builds an ordinary `SeasonSimulationResult` from that state, so
standings, leaders, awards and the summary come from the existing builders unchanged.

Known simplification: a reliever's fatigue only looks back `PITCHING_LOG_DAYS` days, which is all
the engine reads anyway; nothing else about fatigue persists between games.
"""

from collections import Counter
from datetime import date, datetime, timedelta
from enum import Enum
from random import Random
from typing import Callable, Optional

from pydantic import BaseModel, Field

from ..card.sets import Set
from ..card.showdown_player_card import ShowdownPlayerCard
from ..card.team_builder.autofill import OFFENSE_POSITIONS
from ..card.team_builder.team import ROTATION_ROLES, Team as BuilderTeam
from ..shared.player_position import PlayerType
from ..simulation.game import Game
from ..simulation.models import GameResult, PostseasonRound, SeasonSimulationConfig, SeasonSimulationResult
from ..simulation.standings import Standings
from ..simulation.stats import PitchingLog, PlayerStatsGroup, StatCategory, Stats, load_woba_weights
from ..simulation.summary import SeasonSummaryBuilder
from ..simulation.team import SimTeam
from .bracket import BracketConfig, LeagueBracket
from .schedule import LeagueSchedule


class SeasonConfig(BaseModel):
    """What the commissioner sets for a season before it starts. Stored as `league_season.config`."""

    games_per_team: int = Field(default=162, ge=2, le=162)
    postseason: BracketConfig = Field(default_factory=BracketConfig)


class SimTarget(str, Enum):
    """How far one chunk plays."""
    DAY = 'day'
    WEEK = 'week'
    REGULAR_END = 'regular_end'          # THROUGH THE LAST REGULAR-SEASON DAY (THE BRACKET IS THEN SET)
    ROUND = 'round'                      # THROUGH THE END OF THE CURRENT POSTSEASON ROUND
    POSTSEASON_END = 'postseason_end'    # TO A CHAMPION


class LeagueSeasonError(Exception):
    """A season action the current state doesn't allow. The message is safe to show."""


class LeagueSeasonRunner:

    POSTSEASON_GAP_DAYS = 2
    POSTSEASON_GAME_INDEX_BASE = 100_000
    PITCHING_LOG_DAYS = 5            # THE ENGINE ONLY LOOKS BACK 2 DAYS FOR BULLPEN AVAILABILITY
    MVP_ROUNDS = (PostseasonRound.CHAMPIONSHIP, PostseasonRound.WORLD_SERIES)
    # QUALIFYING THRESHOLDS OVER A 162-GAME SEASON, SCALED TO GAMES PLAYED - SAME BASES AS `Season`
    FULL_SEASON_MIN_PA, FULL_SEASON_MIN_IP, FULL_SEASON_MIN_IP_RP = 250, 60, 30

    def __init__(self, db, league: dict, season: dict) -> None:
        self.db = db
        self.league = league
        self.season = season
        self.config = SeasonConfig(**(season.get('config') or {}))

    @property
    def season_id(self) -> str:
        return self.season['season_id']

    # ------------------------------------------------------------------
    # MARK: - TEAMS
    # ------------------------------------------------------------------

    def _builder_teams(self) -> dict[str, BuilderTeam]:
        """team_id -> each league team as the team builder last saved it."""
        teams = {}
        for row in self.db.get_league_teams(self.season_id):
            stored = self.db.get_team(row['team_id'], row.get('user_id'))
            if stored is not None:
                teams[row['team_id']] = BuilderTeam.from_db_row(stored)
        return teams

    @staticmethod
    def roster_problems(team: BuilderTeam) -> list[str]:
        """Holes that would keep a team from taking the field."""
        positions = {slot.roster_position.upper() for slot in team.roster}
        missing = [pos for pos in OFFENSE_POSITIONS if pos not in positions]
        missing += [role for role in ROTATION_ROLES[:team.num_starters] if role not in positions]
        return [f"{team.name} has no {', '.join(missing)}"] if missing else []

    def validate_rosters(self, teams: Optional[dict[str, BuilderTeam]] = None) -> None:
        teams = teams if teams is not None else self._builder_teams()
        problems = [problem for team in teams.values() for problem in self.roster_problems(team)]
        if problems:
            raise LeagueSeasonError("Fix these lineups first: " + "; ".join(problems) + ".")

    def _sim_teams(self, state: dict, builder_teams: dict[str, BuilderTeam]) -> dict[str, SimTeam]:
        cards = {release_card_id: ShowdownPlayerCard(**data) for release_card_id, data in self.db.get_league_draft_cards(self.season_id).items()}
        teams: dict[str, SimTeam] = {}
        for key, team_id in state['team_keys'].items():
            builder_team = builder_teams[team_id]
            teams[key] = SimTeam.from_builder_team(
                team=builder_team,
                cards={slot.card_id: cards[slot.card_id] for slot in builder_team.roster if slot.card_id in cards},
                year=state['year'],
                league=self.league['name'],
                name_override=key,
            )
            self._restore_team(teams[key], state['teams'][key])
        return teams

    # ------------------------------------------------------------------
    # MARK: - START
    # ------------------------------------------------------------------

    def start(self) -> None:
        """`setup` -> `regular`: lock in the schedule and the opening state."""
        if self.season['status'] != 'setup':
            raise LeagueSeasonError("This season has already started.")
        teams = self.db.get_league_teams(self.season_id)
        abbreviations = Counter(team['abbreviation'] for team in teams)
        repeated = [abbr for abbr, count in abbreviations.items() if count > 1]
        if repeated:
            raise LeagueSeasonError(f"Every team needs its own abbreviation - {', '.join(repeated)} is used more than once.")
        self.validate_rosters()

        keys = [team['abbreviation'] for team in teams]
        games = LeagueSchedule(keys, self.config.games_per_team).games()
        state = {
            'year': self._season_year(),
            'team_keys': {team['abbreviation']: team['team_id'] for team in teams},
            'teams': {key: {} for key in keys},
            'regular_days': max(game.day for game in games),
            'last_day': 0,
            'player_totals': {},
            'postseason_player_totals': {},
            'series_player_totals': {},
            'bracket': None,
        }
        started = self.db.start_league_regular_season(
            self.season_id, [game.__dict__ for game in games], state,
        )
        if not started:
            raise LeagueSeasonError("This season has already started.")
        self.season['status'] = 'regular'

    def _season_year(self) -> int:
        """The year whose league context (wOBA weights) the stats use: the most common year among
        the drafted cards, or the nearest earlier year that has weights."""
        years = Counter(int(data.get('year')) for data in self.db.get_league_draft_cards(self.season_id).values()
                        if str(data.get('year') or '').isdigit())
        year = years.most_common(1)[0][0] if years else date.today().year
        for candidate in range(year, year - 30, -1):
            if load_woba_weights(candidate):
                return candidate
        return year

    # ------------------------------------------------------------------
    # MARK: - PLAY
    # ------------------------------------------------------------------

    def games_remaining(self, target: SimTarget) -> int:
        """Rough game count a chunk will play, for its progress bar."""
        scheduled = self.db.get_league_games(self.season_id, status='scheduled')
        days = sorted({g['day'] for g in scheduled})
        match target:
            case SimTarget.DAY:
                return sum(1 for g in scheduled if days and g['day'] == days[0]) or len(self.db.get_league_teams(self.season_id)) // 2
            case SimTarget.WEEK:
                return sum(1 for g in scheduled if g['day'] in days[:7]) or len(self.db.get_league_teams(self.season_id))
            case _:
                return len(scheduled) + sum(self.config.postseason.series_lengths) * max(1, self.config.postseason.teams // 2)

    def run(self, target: SimTarget, progress_callback: Optional[Callable[[int], None]] = None) -> None:
        """Play one chunk and save everything it produced in one write."""
        if self.season['status'] not in ('regular', 'postseason'):
            raise LeagueSeasonError("This season isn't being played.")
        state = self.db.get_league_season_state(self.season_id)
        builder_teams = self._builder_teams()
        self.validate_rosters(builder_teams)
        teams = self._sim_teams(state, builder_teams)
        standings = Standings(
            year=state['year'], tournament=self.league['name'],
            team_leagues={key: self.league['name'] for key in teams}, teams=teams,
        )
        regular_stats = self._stats_group(standings, state['player_totals'], 'LEAGUE')
        postseason_stats = self._stats_group(standings, state['postseason_player_totals'], 'POSTSEASON')
        series_stats = {
            series_id: self._stats_group(standings, totals, series_id)
            for series_id, totals in state['series_player_totals'].items()
        }
        bracket = LeagueBracket.from_state(state['bracket']) if state.get('bracket') else None
        for seed, key in (bracket.seeds.items() if bracket else ()):
            teams[key].playoff_seeding = seed

        status = self.season['status']
        played: list[dict] = []
        days_budget = {SimTarget.DAY: 1, SimTarget.WEEK: 7}.get(target)
        days_played = 0
        start_round: Optional[int] = None
        scheduled = sorted(self.db.get_league_games(self.season_id, status='scheduled'), key=lambda g: g['game_index'])

        def play(index: int, day: int, home_key: str, away_key: str, postseason: bool) -> Game:
            home, away = teams[home_key], teams[away_key]
            game = Game(
                index=index, date=self._date(state, day), home_team_name=home_key, away_team_name=away_key,
                home_team_game_number=home.games + 1, away_team_game_number=away.games + 1,
            )
            game.setup(home_team=home, away_team=away, postseason=postseason)
            game.simulate(rng=Random((self.season.get('seed') or 0) + index), collect_box_score=True, keep_innings=False)
            for team, scored, allowed in ((home, game.home_team_final_score, game.away_team_final_score),
                                          (away, game.away_team_final_score, game.home_team_final_score)):
                if not postseason:
                    team_state = state['teams'][team.name]
                    team_state['runs_scored'] = team_state.get('runs_scored', 0) + int(scored)
                    team_state['runs_allowed'] = team_state.get('runs_allowed', 0) + int(allowed)
            (postseason_stats if postseason else regular_stats).merge(home.stats)
            (postseason_stats if postseason else regular_stats).merge(away.stats)
            state['last_day'] = day
            if progress_callback:
                progress_callback(len(played) + 1)
            return game

        while True:
            if status == 'regular':
                if not scheduled:
                    bracket = self._close_regular_season(state, teams)
                    status = 'postseason' if bracket else 'complete'
                    if target == SimTarget.REGULAR_END or status == 'complete':
                        break
                    continue
                if days_budget is not None and days_played >= days_budget:
                    break
                day = scheduled[0]['day']
                todays = [g for g in scheduled if g['day'] == day]
                scheduled = scheduled[len(todays):]
                for row in todays:
                    game = play(row['game_index'], day, row['home_key'], row['away_key'], postseason=False)
                    played.append(self._played_row(game, day, 'REG', None))
                days_played += 1

            elif status == 'postseason':
                if target == SimTarget.REGULAR_END or (days_budget is not None and days_played >= days_budget):
                    break
                if start_round is None:
                    start_round = bracket.current_round
                elif target == SimTarget.ROUND and bracket.current_round != start_round:
                    break
                day = max(state['last_day'], state['regular_days'] + self.POSTSEASON_GAP_DAYS - 1) + 1
                for series, home_key, away_key, _ in bracket.todays_games():
                    index = self.POSTSEASON_GAME_INDEX_BASE + 1 + sum(s.games_played for s in bracket.series)
                    game = play(index, day, home_key, away_key, postseason=True)
                    round_label = bracket.round_label(series.round_index)
                    if round_label in self.MVP_ROUNDS:
                        group = series_stats.setdefault(series.series_id, self._stats_group(standings, {}, series.series_id))
                        group.merge(teams[home_key].stats)
                        group.merge(teams[away_key].stats)
                    bracket.record_game(series.series_id, game.winning_team.name, index)
                    played.append(self._played_row(game, day, round_label.value, series.series_id))
                days_played += 1
                if bracket.is_complete:
                    status = 'complete'
                    break
            else:
                break

        self._save(state, teams, standings, regular_stats, postseason_stats, series_stats, bracket, status, played)

    def _close_regular_season(self, state: dict, teams: dict[str, SimTeam]) -> Optional[LeagueBracket]:
        """Seed the postseason from the final standings (win %, wins, run differential, then a
        seeded coin flip) and build the bracket. None when the league has no postseason."""
        if self.config.postseason.teams == 0:
            return None
        tiebreak = Random(self.season.get('seed') or 0)
        ranked = sorted(
            teams,
            key=lambda key: (
                teams[key].win_pct, teams[key].wins,
                state['teams'][key].get('runs_scored', 0) - state['teams'][key].get('runs_allowed', 0),
                tiebreak.random(),
            ),
            reverse=True,
        )
        for team in teams.values():  # FREEZE REGULAR-SEASON RECORDS BEFORE POSTSEASON GAMES ADD TO THEM
            state['teams'][team.name]['wins'], state['teams'][team.name]['losses'] = team.wins, team.losses
        state['regular_records_final'] = True
        bracket = LeagueBracket.create(self.config.postseason, ranked)
        for seed, key in bracket.seeds.items():
            teams[key].playoff_seeding = seed
        return bracket

    @staticmethod
    def _played_row(game: Game, day: int, round: str, series_id: Optional[str]) -> dict:
        return {
            'game_index': game.index,
            'day': day,
            'round': round,
            'series_id': series_id,
            'home_key': game.home_team_name,
            'away_key': game.away_team_name,
            'home_score': int(game.home_team_final_score),
            'away_score': int(game.away_team_final_score),
            'result': game.as_result().model_dump(mode='json', exclude={'log'}),
        }

    @staticmethod
    def _date(state: dict, day: int) -> date:
        return date(int(state['year']), 4, 1) + timedelta(days=day - 1)

    # ------------------------------------------------------------------
    # MARK: - STATE
    # ------------------------------------------------------------------

    @staticmethod
    def _stats_group(standings: Standings, saved: dict[str, dict], name: str) -> PlayerStatsGroup:
        """Every player's identity statline (from today's rosters) plus their saved totals."""
        group = PlayerStatsGroup(players=standings.all_players, year=standings.year, name=name)
        for player_id, dump in saved.items():
            if player_id in group.stats:
                group.stats[player_id].merge_totals(dump.get('totals') or {})
                group.stats[player_id].merge_positions_played(dump.get('positions_played') or {})
            else:
                group.stats[player_id] = Stats(**dump)
        return group

    @staticmethod
    def _dump_stats(group: PlayerStatsGroup) -> dict[str, dict]:
        """Only players who've appeared - an untouched identity line is rebuilt from the roster."""
        return {
            player_id: stats.model_dump(mode='json')
            for player_id, stats in group.stats.items()
            if stats.totals
        }

    def _restore_team(self, team: SimTeam, saved: dict) -> None:
        team.wins, team.losses = saved.get('wins', 0), saved.get('losses', 0)
        if team.rotation.players:
            team.rotation.pitcher_index = saved.get('rotation_index', 0) % len(team.rotation.players)
        team.consecutive_starts = dict(saved.get('consecutive_starts') or {})
        log = saved.get('pitching_log') or {}
        team.bullpen.pitching_log = PitchingLog(
            daily_appearances={date.fromisoformat(day): ip for day, ip in (log.get('daily_appearances') or {}).items()},
            season_appearances=log.get('season_appearances') or {},
        )
        rest = saved.get('starter_rest') or {}
        for pitcher in team.rotation.players:
            last_start, starts = rest.get(pitcher.id, (None, 0))
            pitcher.last_start_date = date.fromisoformat(last_start) if last_start else None
            pitcher.postseason_starts = starts

    def _snapshot_team(self, team: SimTeam, saved: dict, freeze_record: bool) -> dict:
        log = team.bullpen.pitching_log
        latest = max(log.daily_appearances, default=None)
        keep_from = latest - timedelta(days=self.PITCHING_LOG_DAYS) if latest else None
        return {
            **saved,
            'wins': saved.get('wins', 0) if freeze_record else team.wins,
            'losses': saved.get('losses', 0) if freeze_record else team.losses,
            'rotation_index': team.rotation.pitcher_index,
            'consecutive_starts': team.consecutive_starts,
            'pitching_log': {
                'daily_appearances': {day.isoformat(): ip for day, ip in log.daily_appearances.items() if keep_from is None or day >= keep_from},
                'season_appearances': log.season_appearances,
            },
            'starter_rest': {
                p.id: [p.last_start_date.isoformat() if p.last_start_date else None, p.postseason_starts]
                for p in team.rotation.players
            },
        }

    # ------------------------------------------------------------------
    # MARK: - RESULTS
    # ------------------------------------------------------------------

    def _save(self, state: dict, teams: dict[str, SimTeam], standings: Standings, regular_stats: PlayerStatsGroup,
              postseason_stats: PlayerStatsGroup, series_stats: dict[str, PlayerStatsGroup],
              bracket: Optional[LeagueBracket], status: str, played: list[dict]) -> None:
        freeze_record = bool(state.get('regular_records_final'))
        state['teams'] = {key: self._snapshot_team(team, state['teams'][key], freeze_record) for key, team in teams.items()}
        state['player_totals'] = self._dump_stats(regular_stats)
        state['postseason_player_totals'] = self._dump_stats(postseason_stats)
        state['series_player_totals'] = {sid: self._dump_stats(group) for sid, group in series_stats.items()}
        state['bracket'] = bracket.to_state() if bracket else None

        # STANDINGS SHOW THE REGULAR SEASON ONLY - POSTSEASON GAMES ALSO ADD TO A SimTeam'S W/L
        for key, team in teams.items():
            team.wins, team.losses = state['teams'][key]['wins'], state['teams'][key]['losses']

        result = self._season_result(state, teams, standings, regular_stats, postseason_stats, series_stats, bracket, played)
        summary = SeasonSummaryBuilder(result=result).build()
        champion_key = bracket.champion_key if bracket else None
        if status == 'complete' and champion_key is None:  # NO POSTSEASON: BEST RECORD WINS
            champion_key = max(teams, key=lambda key: (teams[key].win_pct, teams[key].wins))
        self.db.save_league_chunk(
            season_id=self.season_id,
            played=played,
            status=status,
            state=state,
            summary=summary.model_dump(mode='json'),
            champion_team_id=state['team_keys'][champion_key] if status == 'complete' and champion_key else None,
            awards=summary.awards.model_dump(mode='json') if status == 'complete' else None,
        )
        self.season['status'] = status

    def _season_result(self, state: dict, teams: dict[str, SimTeam], standings: Standings, regular_stats: PlayerStatsGroup,
                       postseason_stats: PlayerStatsGroup, series_stats: dict[str, PlayerStatsGroup],
                       bracket: Optional[LeagueBracket], played: list[dict]) -> SeasonSimulationResult:
        """The season so far as the sim's own result model, for `SeasonSummaryBuilder`/awards."""
        rows = {row['game_index']: row for row in self.db.get_league_games(self.season_id, status='final')}
        rows.update({row['game_index']: row for row in played})
        games = {index: self._light_game_result(state, row, teams) for index, row in rows.items()}

        games_played = max((team.games for team in teams.values()), default=0)
        scale = games_played / 162
        now = datetime.now()
        year = int(state['year'])
        return SeasonSimulationResult(
            config=SeasonSimulationConfig(
                year=year, set=Set(self.league['showdown_set']), seed=self.season.get('seed'),
                custom_teams=[], tournament_name=self.league['name'], include_box_scores=True,
            ),
            started_at=now,
            ended_at=now,
            schedule_length=self.config.games_per_team,
            original_schedule_length=self.config.games_per_team,
            stats_min_pa=int(self.FULL_SEASON_MIN_PA * scale),
            stats_min_ip=int(self.FULL_SEASON_MIN_IP * scale),
            stats_min_ip_rp=int(self.FULL_SEASON_MIN_IP_RP * scale),
            standings=standings.as_result(),
            player_stats=list(regular_stats.stats.values()),
            league_totals={pt.value: regular_stats.aggregated_stats(type=pt) for pt in (PlayerType.HITTER, PlayerType.PITCHER)},
            woba_weights=load_woba_weights(year),
            games=[game for index, game in sorted(games.items()) if index < self.POSTSEASON_GAME_INDEX_BASE],
            postseason=bracket.as_result(games, self._series_mvp_pools(series_stats, teams, bracket)) if bracket else None,
        )

    def _light_game_result(self, state: dict, row: dict, teams: dict[str, SimTeam]) -> GameResult:
        winner = row['home_key'] if (row['home_score'] or 0) > (row['away_score'] or 0) else row['away_key']
        return GameResult(
            index=row['game_index'], date=self._date(state, row['day']),
            home_team=row['home_key'], away_team=row['away_key'],
            home_score=row['home_score'] or 0, away_score=row['away_score'] or 0, winner=winner,
            home_team_identity=teams[row['home_key']].identity if row['home_key'] in teams else None,
            away_team_identity=teams[row['away_key']].identity if row['away_key'] in teams else None,
        )

    @staticmethod
    def _series_mvp_pools(series_stats: dict[str, PlayerStatsGroup], teams: dict[str, SimTeam], bracket: LeagueBracket) -> dict[str, list[Stats]]:
        """Each decided MVP-round series' winning club's contributors - the pool its MVP is
        picked from, same as `PostseasonSeries._winner_series_stats`."""
        pools = {}
        for series in bracket.series:
            group = series_stats.get(series.series_id)
            if group is None or series.winner_seed is None:
                continue
            winner_ids = {p.id for p in teams[bracket.seeds[series.winner_seed]].all_players}
            pools[series.series_id] = [
                s for s in group.stats.values()
                if s.id in winner_ids and (s.stat(StatCategory.PA) > 0 or s.stat(StatCategory.IP) > 0)
            ]
        return pools
