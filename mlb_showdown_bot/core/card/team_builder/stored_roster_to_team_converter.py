from typing import Optional

from .team import (
    Team, TeamSource, CardSource, TeamRosterSlot, Lineup, PitcherAssignment,
    PickSource, ROTATION_ROLES, BULLPEN_ROLES, derive_lineups_rotation,
)
from ...database.postgres_db import ExploreDataRecord


class StoredRosterToTeamConverter:
    """Rebuild a read-only Team from pre-computed roster slots in internal.dim_historical_roster.

    The counterpart to RosterToTeamConverter: that class *derives* the roster from playing
    time (an expensive, per-request composition), while this one just rehydrates slots that
    were already derived offline by the CLI backfill. Stored slots are keyed by mlb_id and
    are therefore set-agnostic — the caller supplies whichever set's cards it wants and the
    same alignment applies.

    A player with no card in the requested set is dropped, mirroring how the roster-derived
    converter skips records without a card_id.
    """

    def __init__(
        self,
        cards: list[ExploreDataRecord],
        meta_rows: list[dict],
        team_id: str,
        name: str,
        abbreviation: str,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        source: TeamSource = TeamSource.MLB,
    ) -> None:
        self.cards = [c for c in cards if c.card_id and c.mlb_id is not None]
        self.meta_rows = meta_rows
        self.team_id = team_id
        self.name = name
        self.abbreviation = abbreviation
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.source = source

    @staticmethod
    def _card_source(card: ExploreDataRecord) -> CardSource:
        try:
            return CardSource((card.source or 'BOT').upper())
        except ValueError:
            return CardSource.BOT

    def build(self) -> Team:
        card_by_mlb_id = {c.mlb_id: c for c in self.cards}

        # Roster dicts carry the stats derive_lineups_rotation needs to score the batting order.
        roster_rows: list[dict] = []
        stored_batting_order: dict[str, int] = {}
        for meta in sorted(self.meta_rows, key=lambda r: r.get('slot_order') or 0):
            card = card_by_mlb_id.get(meta.get('mlb_id'))
            if card is None:
                continue
            roster_rows.append({
                'card_id': card.card_id,
                'card_source': self._card_source(card).value,
                'roster_position': meta.get('roster_position'),
                'command': card.command,
                'outs': card.outs,
                'speed': card.speed,
                'points': card.points,
            })
            if meta.get('batting_order'):
                stored_batting_order[card.card_id] = meta['batting_order']

        # Rotation ordering and the Default batting order come from the shared derivation
        # used by saved user teams — nothing about that logic is re-implemented here.
        lineups, rotation = derive_lineups_rotation(roster_rows)

        # Prefer the batting order computed during the backfill so the lineup is stable
        # across sets, falling back to the freshly derived one for any slot without it.
        if stored_batting_order and lineups:
            for slot in lineups[0]['slots']:
                slot['batting_order'] = stored_batting_order.get(slot['card_id'], slot['batting_order'])
            lineups[0]['slots'].sort(key=lambda s: s['batting_order'])

        roster = [
            TeamRosterSlot(
                card_id=row['card_id'],
                card_source=CardSource(row['card_source']),
                roster_position=row['roster_position'],
                pick_source=PickSource.IMPORTED,
            )
            for row in roster_rows
        ]

        num_bench = sum(1 for r in roster if r.roster_position == 'BE')
        num_bullpen = sum(1 for r in roster if r.roster_position in BULLPEN_ROLES)
        num_starters = sum(1 for r in roster if r.roster_position in ROTATION_ROLES)

        team_kwargs = {}
        if self.primary_color:
            team_kwargs['primary_color'] = self.primary_color
        if self.secondary_color:
            team_kwargs['secondary_color'] = self.secondary_color

        return Team(
            team_id=self.team_id,
            user_id=None,
            name=self.name,
            abbreviation=self.abbreviation,
            is_public=True,
            source=self.source,
            pts_limit=None,
            roster_size=len(roster),
            min_bench=num_bench,
            min_bullpen=num_bullpen,
            num_starters=num_starters,
            roster=roster,
            lineups=[Lineup(**lineup) for lineup in lineups],
            rotation=[PitcherAssignment(**assignment) for assignment in rotation],
            **team_kwargs,
        )

    def build_api_dict(self) -> dict:
        """Serialize to the same shape as /user/teams and the on-the-fly MLB team endpoints.

        `total_points` sums the *rostered* cards only — the composed team is exactly what the
        detail view renders, so the tile and the roster always agree.
        """
        team = self.build()
        data = team.model_dump(mode='json')
        points_by_card_id = {c.card_id: (c.points or 0) for c in self.cards}
        data['total_points'] = sum(points_by_card_id.get(slot.card_id, 0) for slot in team.roster)
        return data
