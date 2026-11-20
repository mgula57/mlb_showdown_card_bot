import re
from typing import Any, Optional

from thefuzz import process as fuzzy_process

from ..shared.hand import Hand
from ..shared.player_position import PlayerType
from ..card.stats.datasource import Datasource
from ..card.stats.stats_period import StatsPeriod
from ..card.stats.normalized_player_stats import NormalizedPlayerStats, PlayerStatsNormalizer
from ..card.utils.shared_functions import fill_empty_stat_categories, total_innings_pitched
from .models import NPBName, NPBPlayerTeamSeason


class NPBPlayerNotFoundError(Exception):
    pass


class NPBPlayerStatsBuilder:
    """Builds NormalizedPlayerStats for an NPB player from the register rows stored in Postgres
    (see NPBRegisterScraper / `showdown_bot database store_npb_stats`).

    One stat line is built per season (summing a traded player's team rows), and multi-year periods reuse
    PlayerStatsNormalizer.combine_multi_year_stats like every other datasource.
    """

    FIRST_SEASON = 2018             # FIRST SEASON LOADED INTO THE DATABASE (PHASE 2 EXTENDS THIS TO 1950)
    DH_MIN_GAMES = 10               # BATTING GAMES NOT COVERED BY A FIELDING POSITION THAT EARN A DH LISTING
    FUZZY_NAME_MIN_SCORE = 88
    REGISTER_ID_PATTERN = re.compile(r'^[a-z\-]{6}\d{3}[a-z\-]{3}$')

    # -------------------------
    # LOOKUP
    # -------------------------

    @classmethod
    def from_database(cls, name: str, stats_period: StatsPeriod) -> NormalizedPlayerStats:
        """Find the player by register id or name and build their stats for the period."""
        from ..database.postgres_db import PostgresDB

        search = (name or '').split('(')[0].strip()
        seasons = cls._seasons_for_period(stats_period)
        with PostgresDB(is_archive=True) as db:
            if cls.REGISTER_ID_PATTERN.match(search.lower()):
                rows = db.fetch_npb_player_team_seasons(seasons=seasons, register_id=search.lower())
            else:
                rows = db.fetch_npb_player_team_seasons(seasons=seasons, name_key=NPBName.key(search))
                if not rows:
                    rows = cls._fuzzy_match_rows(db, search=search, seasons=seasons)

        if not rows:
            years = stats_period.year or ', '.join(str(s) for s in seasons)
            raise NPBPlayerNotFoundError(
                f"No NPB player found named '{search}' for {years}. NPB cards are available for {cls.FIRST_SEASON}+ seasons. "
                "Check the spelling (Baseball Reference romanization, ex: 'Kensuke Kondoh') or use the player's Baseball Reference register ID."
            )

        player_rows = cls._single_player_rows(rows)
        stats_period.year_list = sorted({row.season for row in player_rows}) # RESOLVES CAREER INTO THE SEASONS PLAYED
        stats = cls.build(rows=player_rows, stats_period=stats_period)
        if stats is None:
            raise NPBPlayerNotFoundError(f"No {'pitching' if stats_period.is_pitcher_override else 'batting'} stats found for {search} in {stats_period.year}.")
        stats.years_played = [str(season) for season in stats_period.year_list]
        return stats

    @classmethod
    def _seasons_for_period(cls, stats_period: StatsPeriod) -> list[int]:
        if stats_period.is_full_career or not stats_period.year_list:
            from datetime import datetime
            return list(range(cls.FIRST_SEASON, datetime.now().year + 1))
        return [int(y) for y in stats_period.year_list]

    @classmethod
    def _fuzzy_match_rows(cls, db, search: str, seasons: list[int]) -> list[NPBPlayerTeamSeason]:
        """Fall back to the closest name that played in the seasons (handles small spelling differences)."""
        candidates = {row.name_key: row.register_id for row in db.fetch_npb_player_team_seasons(seasons=seasons)}
        if not candidates:
            return []
        match = fuzzy_process.extractOne(NPBName.key(search), list(candidates.keys()))
        if not match or match[1] < cls.FUZZY_NAME_MIN_SCORE:
            return []
        return db.fetch_npb_player_team_seasons(seasons=seasons, register_id=candidates[match[0]])

    @staticmethod
    def _single_player_rows(rows: list[NPBPlayerTeamSeason]) -> list[NPBPlayerTeamSeason]:
        """When a name matches more than one player, keep the one with the most playing time."""
        playing_time: dict[str, float] = {}
        for row in rows:
            playing_time[row.register_id] = playing_time.get(row.register_id, 0) \
                + (row.batting.get('PA', 0) or 0) + (row.pitching.get('batters_faced', 0) or 0)
        register_id = max(playing_time, key=playing_time.get)
        return [row for row in rows if row.register_id == register_id]

    # -------------------------
    # BUILD
    # -------------------------

    @classmethod
    def build(cls, rows: list[NPBPlayerTeamSeason], stats_period: StatsPeriod) -> Optional[NormalizedPlayerStats]:
        player_type = stats_period.player_type_override or cls._player_type(rows)
        yearly_stats = [
            stats for season in sorted({row.season for row in rows})
            if (stats := cls._season_stats([row for row in rows if row.season == season], player_type)) is not None
        ]
        if not yearly_stats:
            return None
        if len(yearly_stats) == 1:
            return yearly_stats[0]
        return PlayerStatsNormalizer.combine_multi_year_stats(yearly_stats, stats_period=stats_period)

    @staticmethod
    def _player_type(rows: list[NPBPlayerTeamSeason]) -> PlayerType:
        plate_appearances = sum(row.batting.get('PA', 0) or 0 for row in rows)
        batters_faced = sum(row.pitching.get('batters_faced', 0) or 0 for row in rows)
        return PlayerType.PITCHER if batters_faced > plate_appearances else PlayerType.HITTER

    @classmethod
    def _season_stats(cls, season_rows: list[NPBPlayerTeamSeason], player_type: PlayerType) -> Optional[NormalizedPlayerStats]:
        is_pitcher = player_type.is_pitcher
        section = 'pitching' if is_pitcher else 'batting'
        rows = [row for row in season_rows if getattr(row, section)]
        if not rows:
            return None

        first = rows[0]
        team_games = {row.team: getattr(row, section).get('G', 0) or 0 for row in rows}
        warnings: list[str] = []

        data: dict[str, Any] = {
            'primary_datasource': Datasource.BREF_REGISTER,
            'name': first.name,
            'bref_id': first.register_id, # REGISTER ID KEYS PLAYER IMAGES, EX: '(muraka000mun)' IN THE FILE NAME
            'bref_url': first.register_url,
            'year_ID': first.season,
            'age': first.age,
            'type': player_type.value,
            'team_ID': max(team_games, key=team_games.get),
            'team_games_played_dict': team_games,
            'team_id_list': list(team_games.keys()),
            'lg_ID': 'NPB',
            'hand': (first.bats or Hand.RIGHT).value,
            'hand_throw': (next((r.throws for r in season_rows if r.throws), None) or Hand.RIGHT).value,
            **cls._summed_stats([getattr(row, section) for row in rows]),
            'positions': cls._positions(season_rows, is_pitcher=is_pitcher),
            'accolades': {},
            'award_summary': '',
            'is_rookie': False,
        }

        if is_pitcher and any(row.pitching.get('GS_estimated') for row in rows):
            warnings.append("Games started aren't published for this NPB season and couldn't be matched, so starter/reliever role was estimated from innings per appearance.")
        if warnings:
            data['warnings'] = warnings

        data = fill_empty_stat_categories(stats_data=data, is_pitcher=is_pitcher, is_game_logs=False)
        return NormalizedPlayerStats(**data)

    @staticmethod
    def _summed_stats(stat_lines: list[dict[str, Any]]) -> dict[str, Any]:
        summed: dict[str, Any] = {}
        for line in stat_lines:
            for key, value in line.items():
                if key in ('IP', 'GS_estimated') or not isinstance(value, (int, float)):
                    continue
                summed[key] = summed.get(key, 0) + value
        innings = [line['IP'] for line in stat_lines if line.get('IP')]
        if innings:
            summed['IP'] = total_innings_pitched(innings)
        return summed

    @classmethod
    def _positions(cls, season_rows: list[NPBPlayerTeamSeason], is_pitcher: bool) -> dict[str, dict[str, Any]]:
        if is_pitcher:
            games = sum(row.pitching.get('G', 0) or 0 for row in season_rows)
            return {'P': {'g': games}}

        positions: dict[str, dict[str, Any]] = {}
        for row in season_rows:
            for position, line in row.fielding.items():
                if position == 'P':
                    continue
                combined = positions.setdefault(position, {'g': 0, 'rf_fld': 0.0})
                combined['g'] += line.get('G', 0) or 0
                combined['rf_fld'] = round(combined['rf_fld'] + (line.get('rf_fld', 0) or 0), 2)

        batting_games = sum(row.batting.get('G', 0) or 0 for row in season_rows)
        most_fielding_games = max((p['g'] for p in positions.values()), default=0)
        if batting_games - most_fielding_games >= cls.DH_MIN_GAMES:
            positions['DH'] = {'g': batting_games - most_fielding_games}
        return positions
