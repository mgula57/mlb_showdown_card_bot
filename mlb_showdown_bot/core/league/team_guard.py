from collections import Counter
from typing import Optional


class LeagueTeamGuard:
    """What an owner may still change on a league team through the ordinary team routes.

    A league team is a normal `user_teams` row, so the team builder can edit its lineups and
    defensive alignment. What it can't touch is anything the league decides: which cards are on
    the roster (the draft), the roster rules, visibility, or the team's existence. And nothing is
    editable mid-draft, since a roster save rewrites every slot and could drop a pick that landed
    after the client last read the team.
    """

    # Identity and presentation only - roster rules, visibility and provenance belong to the league
    EDITABLE_FIELDS = frozenset({'name', 'abbreviation', 'primary_color', 'secondary_color', 'logo_url'})
    EDITABLE_SEASON_STATUSES = frozenset({'setup', 'regular', 'postseason'})
    MANAGED_BY_LEAGUE_ERROR = "League teams are managed by their league."

    def __init__(self, db, context: dict) -> None:
        self.db = db
        self.context = context

    @classmethod
    def for_team(cls, db, team_id: str) -> Optional['LeagueTeamGuard']:
        """The guard for a league team, or None for an ordinary team (no restrictions)."""
        context = db.get_league_team_context(team_id)
        return cls(db, context) if context else None

    def update_error(self, team_id: str, payload: dict) -> Optional[str]:
        """Why this update can't be applied, or None. Strips fields the owner may not change
        from `payload` in place, so a team builder that saves the whole team still works."""
        if self.context['season_status'] not in self.EDITABLE_SEASON_STATUSES:
            return "This team can't be edited right now." if self.context['season_status'] != 'drafting' \
                else "Your team can be edited once the draft is complete."
        for key in [k for k in payload if k not in self.EDITABLE_FIELDS and k not in ('roster', 'lineups')]:
            payload.pop(key)
        roster = payload.get('roster')
        if roster is not None:
            current = Counter(self.db.get_team_roster_cards(team_id))
            proposed = Counter((str(slot.get('card_source', 'BOT')), str(slot.get('card_id'))) for slot in roster)
            if proposed != current:
                return "A league team's cards come from the draft - you can move players between positions, but not add or remove them."
        return None
