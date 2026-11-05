from typing import Optional

from .draft import SnakeOrder
from .settings import LeagueSettings


class LeagueListItem:
    """Turns a `PostgresDB.list_user_leagues` row into the payload a Leagues list tile draws: the
    current season's teams, in standings order once games are played, each with its record and
    whether it's on the clock or holds the title, plus how far the draft and the season have got."""

    def __init__(self, row: dict) -> None:
        self.row = dict(row)
        self.settings = LeagueSettings(**(self.row.get('settings') or {}))
        self.status = self.row.get('current_season_status')
        self.champion_team_id = self.row.pop('champion_team_id', None)
        self.picks_made = int(self.row.pop('picks_made', None) or 0)
        self.records = self._records_by_abbreviation(self.row.pop('standing_divisions', None))

    @staticmethod
    def _records_by_abbreviation(divisions: Optional[dict]) -> dict[str, dict]:
        """Standings key teams by abbreviation, which is unique within a league season."""
        records = [record for division in (divisions or {}).values() for record in division]
        return {(record.get('identity') or {}).get('abbreviation') or record.get('name'): record for record in records}

    @property
    def draft_order(self) -> Optional[SnakeOrder]:
        """The running draft's order, or None once it's over or before it starts."""
        team_count = len(self.row.get('teams') or [])
        if self.status != 'drafting' or team_count == 0:
            return None
        order = SnakeOrder(team_count, self.settings.roster_size)
        return order if self.picks_made < order.total_picks else None

    def _teams(self) -> list[dict]:
        order = self.draft_order
        on_the_clock_slot = order.slot_for_pick(self.picks_made + 1) if order else None
        teams = []
        for slot, team in enumerate(self.row.get('teams') or []):
            record = self.records.get(team['abbreviation']) or {}
            teams.append({
                **team,
                'wins': int(record.get('wins') or 0),
                'losses': int(record.get('losses') or 0),
                'win_pct': float(record.get('win_pct') or 0),
                'is_champion': self.champion_team_id is not None and team['team_id'] == self.champion_team_id,
                'is_on_the_clock': slot == on_the_clock_slot,
            })
        # SORTED IS STABLE: TIED AND UNPLAYED TEAMS STAY IN DRAFT-SLOT ORDER
        return sorted(teams, key=lambda team: (not team['is_champion'], -team['win_pct'], -team['wins']))

    def payload(self) -> dict:
        teams = self._teams()
        order = self.draft_order
        games_per_team = self.row.pop('games_per_team', None)
        return {
            **self.row,
            'teams': teams,
            'draft_pick': self.picks_made + 1 if order else None,
            'draft_total_picks': order.total_picks if order else None,
            'games_played': max((team['wins'] + team['losses'] for team in teams), default=0),
            'games_per_team': int(games_per_team) if games_per_team is not None else None,
        }
