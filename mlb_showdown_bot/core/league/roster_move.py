"""Moving a drafted player to another roster position on a league team: into an open spot, or
swapping with the player who holds it.

Picks are final but positions aren't - a drafter can slide their SS to 2B to open short for a
better glove, reorder the rotation, or bench a starter. During the draft a move must still leave
the roster fillable (and under the points cap) with the picks left, so it can't strand the team.
"""

from collections import Counter
from typing import Optional

from ..card.team_builder.autofill import OFFENSE_POSITIONS
from ..card.team_builder.team import ROTATION_ROLES
from .draft import DraftCard, DraftConflict, DraftError, DraftRoster
from .settings import LeagueSettings

_BULLPEN_POSITIONS = ('RP', 'CL')


class LeagueRosterMove:
    """Validates and applies one move on a member's league team."""

    # Drafting plus everything the team builder may edit (`LeagueTeamGuard.EDITABLE_SEASON_STATUSES`)
    MOVABLE_SEASON_STATUSES = frozenset({'drafting', 'setup', 'regular', 'postseason'})

    def __init__(self, db, league: dict, season: dict, team: dict) -> None:
        self.db = db
        self.league = league
        self.season = season
        self.team = team
        self.settings = LeagueSettings(**(league.get('settings') or {}))

    @staticmethod
    def bucket(position: str) -> str:
        """Bench and bullpen spots are interchangeable, so a move within one goes nowhere."""
        return 'RP' if position in _BULLPEN_POSITIONS else position

    def can_hold(self, card: DraftCard, position: str) -> bool:
        """Whether `card` may sit in `position` - the same spots the draft lets it be picked into."""
        if card.is_pitcher:
            if card.is_starter:
                return position in ROTATION_ROLES[:self.settings.num_starters]
            return position in _BULLPEN_POSITIONS
        if position in ('DH', 'BE'):
            return True
        return position in OFFENSE_POSITIONS and card.can_play(position)

    def move(self, release_card_id: str, to_position: str, swap_with_card_id: Optional[str] = None) -> None:
        """Move `release_card_id` into `to_position`, or swap it with `swap_with_card_id` (taking
        that card's spot). Raises DraftError for a move the rules don't allow and DraftConflict
        if the roster changed since it was read."""
        status = self.season.get('status')
        if status not in self.MOVABLE_SEASON_STATUSES:
            raise DraftError("This team's season is over.")
        if self.season.get('job_status') == 'running':
            raise DraftError("Games are being simulated right now - try again when they finish.")

        my_slots = [slot for slot in self.db.get_league_roster_slots(self.season['season_id']) if slot['member_id'] == self.team['member_id']]
        slots = {slot['card_id']: slot['roster_position'] for slot in my_slots}
        cards = {pick['release_card_id']: DraftCard.from_row(pick)
                 for pick in self.db.get_league_draft_picks(self.season['season_id'])
                 if pick['member_id'] == self.team['member_id']}
        mover = cards.get(release_card_id)
        from_position = slots.get(release_card_id)
        if mover is None or from_position is None:
            raise DraftError("That player isn't on your team.")

        moves: list[tuple[str, str, str]] = []  # (card_id, from, to)
        if swap_with_card_id:
            other = cards.get(swap_with_card_id)
            other_position = slots.get(swap_with_card_id)
            if other is None or other_position is None:
                raise DraftError("That player isn't on your team.")
            if self.bucket(from_position) == self.bucket(other_position):
                raise DraftError(f"{mover.name} and {other.name} are already in the same spot.")
            if not self.can_hold(other, from_position):
                raise DraftError(f"{other.name} can't play {from_position}.")
            to_position = other_position
            moves.append((swap_with_card_id, other_position, from_position))
        else:
            if self.bucket(from_position) == self.bucket(to_position):
                raise DraftError(f"{mover.name} is already at {from_position}.")
            if to_position not in ('BE', 'RP') and to_position in slots.values():
                raise DraftConflict(f"{to_position} is already filled. Refresh your team and try again.")
        if not self.can_hold(mover, to_position):
            raise DraftError(f"{mover.name} can't play {to_position}.")
        moves.append((release_card_id, from_position, to_position))

        positions_before = list(slots.values())
        positions_after = list(positions_before)
        for _, old, new in moves:
            positions_after[positions_after.index(old)] = new
        if Counter(positions_before) != Counter(positions_after):
            self._check_still_fillable(positions_before, positions_after, sum(slot.get('points') or 0 for slot in my_slots))

        if not self.db.move_league_roster_slots(self.season['season_id'], self.team['team_id'], positions_before, moves):
            raise DraftConflict("Your team changed while you were moving players. Refresh and try again.")

    def _check_still_fillable(self, before: list[str], after: list[str], points: float) -> None:
        """A move into an open spot reshapes what the roster still needs. Reject it if it leaves
        more needs than picks (or, under a cap, too few points to fill them) - unless the roster
        was already in that state, so a team drafted out of position can still shuffle."""
        old = DraftRoster(settings=self.settings, positions=before, points=points)
        new = DraftRoster(settings=self.settings, positions=after, points=points)
        if new.slack < 0 and new.slack < old.slack:
            raise DraftError("That would open a spot you don't have picks left to fill.")
        if self.season.get('status') == 'drafting' and self.settings.pts_cap:
            pool = [DraftCard.from_row(row) for row in self.db.fetch_league_card_pool(self.season['season_id'], self.league['edition_ids'])]
            cap = self.settings.pts_cap
            new_total = new.points + new.cheapest_fill(pool)[0]
            if new_total > cap and new_total > old.points + old.cheapest_fill(pool)[0]:
                raise DraftError(f"That would open a spot you can't afford to fill under the {cap}-point cap.")
