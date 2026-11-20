import re
import time
from collections import defaultdict
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup, Tag

from ..shared.hand import Hand
from ..shared.team import Team
from ..card.utils.shared_functions import total_innings_pitched
from .models import NPBLeague, NPBName, NPBPlayerTeamSeason


class NPBRegisterScraper:
    """Scrapes NPB player stats from Baseball Reference's register (minor/foreign league) pages.

    Each season is two league pages (Central + Pacific) and one page per club. A club page lists every player's
    batting, pitching and per-position fielding for that club, with handedness markers on the name
    (batting: '*' left, '#' switch; pitching: '*' left).

    The register leaves GS blank for NPB from 2018 on, so starts are backfilled from Fangraphs' NPB pitching
    leaderboard (matched by name), falling back to an estimate from innings per appearance.
    """

    BASE_URL = "https://www.baseball-reference.com"
    REQUEST_DELAY_SECONDS = 3.5  # BREF ALLOWS ~20 REQUESTS / MINUTE
    MAX_RETRIES = 4

    # COLUMNS STORED AS-IS. EVERYTHING ELSE ON THE PAGE (RATES, NOTES) IS RECOMPUTED FROM THESE.
    BATTING_COLUMNS = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'SO', 'TB', 'GIDP', 'HBP', 'SH', 'SF', 'IBB']
    PITCHING_COLUMNS = ['W', 'L', 'G', 'GS', 'GF', 'CG', 'SHO', 'SV', 'IP', 'H', 'R', 'ER', 'HR', 'BB', 'IBB', 'SO', 'HBP', 'BK', 'WP', 'batters_faced']
    FIELDING_COLUMNS = {'G': 'G', 'PO': 'PO', 'A': 'A', 'E_def': 'E', 'DP_def': 'DP', 'fielding_perc': 'fielding_perc', 'PB': 'PB', 'SB': 'SB', 'CS': 'CS'}
    FIELDING_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'OF', 'P']

    # USED WHEN NO FANGRAPHS MATCH EXISTS FOR A PITCHER
    STARTER_IP_PER_GAME_ESTIMATE = 3.5

    def __init__(self, session: Optional[requests.Session] = None, verbose: bool = True):
        self.session = session or requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; ShowdownBot/1.0)'})
        self.verbose = verbose
        self._last_request_time: float = 0.0
        self._league_season_ids: dict[NPBLeague, dict[int, str]] = {}

    # -------------------------
    # PUBLIC
    # -------------------------

    def fetch_season(self, season: int) -> list[NPBPlayerTeamSeason]:
        """All player-team rows for both leagues in a season, with GS backfilled."""
        rows: list[NPBPlayerTeamSeason] = []
        for league in NPBLeague:
            league_season_id = self.league_season_ids(league).get(season)
            if not league_season_id:
                self._log(f"No {league.abbreviation} season page found for {season}")
                continue
            for team_id, team_name in self.team_ids(league_season_id):
                self._log(f"  {season} {league.abbreviation}: {team_name}")
                soup = self._soup(f"/register/team.cgi?id={team_id}")
                rows.extend(self.parse_team_page(soup, season=season, league=league, team_name=team_name))

        self.backfill_games_started(rows, season=season)
        return rows

    def league_season_ids(self, league: NPBLeague) -> dict[int, str]:
        """{season: register league-season id} for every season of a league."""
        if league not in self._league_season_ids:
            soup = self._soup(f"/register/league.cgi?code={league.value}&class=Fgn")
            ids: dict[int, str] = {}
            for link in soup.find_all('a', href=re.compile(r'/register/league\.cgi\?id=[0-9a-f]+$')):
                text = link.get_text(strip=True)
                if text.isdigit():
                    ids.setdefault(int(text), link['href'].split('id=')[1])
            self._league_season_ids[league] = ids
        return self._league_season_ids[league]

    def team_ids(self, league_season_id: str) -> list[tuple[str, str]]:
        """[(register team id, club name)] for a league season."""
        soup = self._soup(f"/register/league.cgi?id={league_season_id}")
        teams: dict[str, str] = {}
        for link in soup.find_all('a', href=re.compile(r'/register/team\.cgi\?id=[0-9a-f]+$')):
            teams.setdefault(link['href'].split('id=')[1], link.get_text(strip=True))
        return list(teams.items())

    # -------------------------
    # PARSING
    # -------------------------

    def parse_team_page(self, soup: BeautifulSoup, season: int, league: NPBLeague, team_name: str) -> list[NPBPlayerTeamSeason]:
        team = Team.from_npb_team_name(team_name, year=season)
        team_value = team.value if team else team_name
        players: dict[str, NPBPlayerTeamSeason] = {}

        def player_for_row(row: Tag) -> Optional[NPBPlayerTeamSeason]:
            cell = row.find(attrs={'data-stat': 'player'})
            link = cell.find('a', href=True) if cell else None
            if not link or 'player.fcgi?id=' not in link['href']:
                return None
            register_id = link['href'].split('id=')[1]
            if register_id not in players:
                players[register_id] = NPBPlayerTeamSeason(
                    register_id=register_id, name=link.get_text(strip=True), season=season,
                    league=league, team=team_value, team_name=team_name,
                )
            return players[register_id]

        # BATTING
        for row in self._table_rows(soup, 'team_batting'):
            player = player_for_row(row)
            if player is None:
                continue
            player.age = self._int(self._cell_text(row, 'age')) or player.age
            player.batting = self._row_values(row, self.BATTING_COLUMNS)
            player.bats = self._hand_from_marker(row, is_batting=True)

        # PITCHING
        for row in self._table_rows(soup, 'team_pitching'):
            player = player_for_row(row)
            if player is None:
                continue
            player.age = player.age or self._int(self._cell_text(row, 'age'))
            player.pitching = self._row_values(row, self.PITCHING_COLUMNS)
            player.throws = self._hand_from_marker(row, is_batting=False)

        # FIELDING (ONE TABLE PER POSITION)
        for position in self.FIELDING_POSITIONS:
            for row in self._table_rows(soup, f'team_fielding_{position}'):
                player = player_for_row(row)
                if player is None:
                    continue
                values = {
                    key: self._number(self._cell_text(row, stat))
                    for stat, key in self.FIELDING_COLUMNS.items()
                    if row.find(attrs={'data-stat': stat}) is not None
                }
                player.fielding[position] = {k: v for k, v in values.items() if v is not None}

        return list(players.values())

    # -------------------------
    # GAMES STARTED BACKFILL
    # -------------------------

    def backfill_games_started(self, rows: list[NPBPlayerTeamSeason], season: int) -> None:
        """Fill blank GS from Fangraphs' NPB pitching leaderboard. Fangraphs lists one row per player-season,
        so a traded pitcher's starts are split across his team rows by games pitched."""
        pitcher_rows = [r for r in rows if r.pitching and r.pitching.get('G') and not r.pitching.get('GS')]
        if not pitcher_rows:
            return

        fangraphs_gs_by_name: dict[str, int] = {}
        try:
            from ..fangraphs.client import FangraphsAPIClient
            leaderboard = FangraphsAPIClient().fetch_leaderboard_stats(season_start=season, season_end=season, stat_type='pit', league='NPB')
            for fg_row in leaderboard or []:
                key = NPBName.key(fg_row.get('PlayerName', ''))
                if key and fg_row.get('GS') is not None:
                    fangraphs_gs_by_name[key] = fangraphs_gs_by_name.get(key, 0) + int(fg_row['GS'])
        except Exception as e:
            self._log(f"Fangraphs GS backfill unavailable for {season}: {e}")

        rows_by_player: dict[str, list[NPBPlayerTeamSeason]] = defaultdict(list)
        for row in pitcher_rows:
            rows_by_player[row.register_id].append(row)

        matched = 0
        for player_rows in rows_by_player.values():
            season_gs = fangraphs_gs_by_name.get(player_rows[0].name_key)
            if season_gs is None:
                for row in player_rows:
                    row.pitching['GS'] = self._estimate_games_started(row.pitching)
                    row.pitching['GS_estimated'] = True
                continue
            matched += 1
            total_games = sum(r.pitching.get('G', 0) for r in player_rows) or 1
            remaining = season_gs
            for index, row in enumerate(player_rows):
                is_last = index == len(player_rows) - 1
                share = remaining if is_last else round(season_gs * row.pitching.get('G', 0) / total_games)
                row.pitching['GS'] = min(share, row.pitching.get('G', 0))
                remaining -= row.pitching['GS']

        self._log(f"GS backfill {season}: {matched}/{len(rows_by_player)} pitchers matched to Fangraphs, rest estimated")

    @classmethod
    def _estimate_games_started(cls, pitching: dict[str, Any]) -> int:
        games = pitching.get('G', 0) or 0
        if games == 0:
            return 0
        ip_per_game = total_innings_pitched([pitching.get('IP', 0) or 0]) / games
        return games if ip_per_game >= cls.STARTER_IP_PER_GAME_ESTIMATE else 0

    # -------------------------
    # HELPERS
    # -------------------------

    def _soup(self, path: str) -> BeautifulSoup:
        html = self._get(f"{self.BASE_URL}{path}")
        # BREF HIDES MOST TABLES INSIDE HTML COMMENTS
        return BeautifulSoup(html.replace('<!--', '').replace('-->', ''), 'lxml')

    def _get(self, url: str) -> str:
        for attempt in range(self.MAX_RETRIES):
            wait = self.REQUEST_DELAY_SECONDS - (time.time() - self._last_request_time)
            if wait > 0:
                time.sleep(wait)
            self._last_request_time = time.time()
            response = self.session.get(url, timeout=30)
            if response.status_code == 429:
                backoff = 60 * (attempt + 1)
                self._log(f"Rate limited by BREF, waiting {backoff}s")
                time.sleep(backoff)
                continue
            response.raise_for_status()
            return response.text
        raise RuntimeError(f"Failed to fetch {url} after {self.MAX_RETRIES} attempts")

    @staticmethod
    def _table_rows(soup: BeautifulSoup, table_id: str) -> list[Tag]:
        table = soup.find('table', id=table_id)
        if table is None or table.tbody is None:
            return []
        return [row for row in table.tbody.find_all('tr') if 'thead' not in (row.get('class') or [])]

    @staticmethod
    def _cell_text(row: Tag, stat: str) -> str:
        cell = row.find(attrs={'data-stat': stat})
        return cell.get_text(strip=True) if cell else ''

    @classmethod
    def _row_values(cls, row: Tag, columns: list[str]) -> dict[str, Any]:
        values = {column: cls._number(cls._cell_text(row, column)) for column in columns}
        return {k: v for k, v in values.items() if v is not None}

    @staticmethod
    def _hand_from_marker(row: Tag, is_batting: bool) -> Hand:
        cell = row.find(attrs={'data-stat': 'player'})
        text = cell.get_text(strip=True) if cell else ''
        if text.endswith('#') and is_batting:
            return Hand.SWITCH
        if text.endswith('*'):
            return Hand.LEFT
        return Hand.RIGHT

    @staticmethod
    def _number(value: str) -> Optional[int | float]:
        value = (value or '').strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            return None

    @classmethod
    def _int(cls, value: str) -> Optional[int]:
        number = cls._number(value)
        return int(number) if number is not None else None

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)
