from typing import Optional

from .team import (
    Team, TeamSource, CardSource, TeamRosterSlot, Lineup, LineupSlot, PitcherAssignment,
    PickSource, DEFAULT_LINEUP_NAME,
)
from .autofill import OFFENSE_POSITIONS
from .lineup import LineupBuilder, LineupCandidate
from ...database.postgres_db import ExploreDataRecord
from ...shared.player_position import Position, PositionSlot


class RosterToTeamConverter:
    """Convert a pool of ExploreDataRecord cards for a real MLB/WBC roster into a read-only Team.

    Used to present real rosters (sourced from the card archive) inside the team
    builder UI without going through the drafting flow. Unlike autofill
    (budget-driven and randomized), composition is deterministic and based on real
    playing time: lineup spots go to the eligible hitters with the most games
    played, the rotation is ordered by games started, and the closer role goes to
    the reliever with the most saves.
    """

    # The team builder UI only has SP1-SP5 role slots (ROTATION_ROLES is hardcoded
    # app-wide), so a starter beyond the 5th by games started is folded into the bullpen.
    MAX_ROTATION_SLOTS = 5

    def __init__(
        self,
        cards: list[ExploreDataRecord],
        team_id: str,
        name: str,
        abbreviation: str,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
    ) -> None:
        # A card can't be placed on the roster without an identifier the frontend can look up
        self.cards = [c for c in cards if c.card_id]
        self.team_id = team_id
        self.name = name
        self.abbreviation = abbreviation
        self.primary_color = primary_color
        self.secondary_color = secondary_color

    # ------------------------------------------------------------------
    # SORT KEYS
    # ------------------------------------------------------------------

    @staticmethod
    def _by_games_played(card: ExploreDataRecord) -> tuple:
        return (card.g or 0, card.points or 0)

    @staticmethod
    def _by_games_started(card: ExploreDataRecord) -> tuple:
        return (card.gs or 0, card.real_ip or 0.0, card.points or 0)

    @staticmethod
    def _by_saves(card: ExploreDataRecord) -> tuple:
        return (card.real_sv or 0, card.points or 0)

    @staticmethod
    def _card_source(card: ExploreDataRecord) -> CardSource:
        try:
            return CardSource((card.source or 'BOT').upper())
        except ValueError:
            return CardSource.BOT

    @staticmethod
    def _pos_matches(card: ExploreDataRecord, slot: PositionSlot) -> bool:
        """Check whether a hitter card can play the given field position (positions_list-based)."""
        pos_list = card.positions_list or []
        valid_in_game_positions = slot.valid_positions
        if slot == PositionSlot.DH:
            return card.player_type == 'HITTER'  # any hitter can DH
        return any(pos in pos_list for pos in valid_in_game_positions)

    # ------------------------------------------------------------------
    # COMPOSITION
    # ------------------------------------------------------------------

    @staticmethod
    def _preferred_position(card: ExploreDataRecord) -> Optional[str]:
        """The position a hitter played most, per Baseball Reference's position summary ordering.

        `primary_positions` is already ordered by games played at each position; falls back to
        `secondary_positions` for players with no primary position on record (e.g. limited playing time).
        """
        if card.primary_positions:
            return card.primary_positions[0]
        if card.secondary_positions:
            return card.secondary_positions[0]
        return None

    def _assign_lineup(self, hitters: list[ExploreDataRecord]) -> dict[str, ExploreDataRecord]:
        """Assign the 9 lineup positions to hitters.

        Pass 1 prefers each hitter's most-played position (primary/secondary_positions).
        Pass 2 falls back to the broader positions_list-based eligibility (the pre-existing
        logic, which folds LF/RF together and allows any hitter at DH) for any position that
        pass 1 couldn't fill. Both passes fill the scarcest position first so a player who is
        the only option at a position isn't consumed by a deeper one.
        """
        assignment: dict[str, ExploreDataRecord] = {}
        used_ids: set[str] = set()

        preferred_candidates: dict[str, list[ExploreDataRecord]] = {pos: [] for pos in OFFENSE_POSITIONS}
        for card in hitters:
            pos = self._preferred_position(card)
            if pos in preferred_candidates:
                preferred_candidates[pos].append(card)

        for position in sorted(OFFENSE_POSITIONS, key=lambda p: len(preferred_candidates[p])):
            candidates = [c for c in preferred_candidates[position] if c.card_id not in used_ids]
            if not candidates:
                continue
            picked = max(candidates, key=self._by_games_played)
            assignment[position] = picked
            used_ids.add(picked.card_id)

        remaining_positions = [p for p in OFFENSE_POSITIONS if p not in assignment]
        if remaining_positions:
            eligible = {
                pos: [c for c in hitters if c.card_id not in used_ids and self._pos_matches(c, PositionSlot(pos))]
                for pos in remaining_positions
            }
            for position in sorted(remaining_positions, key=lambda p: len(eligible[p])):
                candidates = [c for c in eligible[position] if c.card_id not in used_ids]
                if not candidates:
                    continue
                picked = max(candidates, key=self._by_games_played)
                assignment[position] = picked
                used_ids.add(picked.card_id)

        return assignment

    def build(self) -> Team:
        hitters = [c for c in self.cards if c.player_type != 'PITCHER']
        pitchers = [c for c in self.cards if c.player_type == 'PITCHER']
        starters = [c for c in pitchers if Position.SP in (c.positions_list or [])]
        relievers = [c for c in pitchers if Position.SP not in (c.positions_list or [])]

        roster_slots: list[TeamRosterSlot] = []
        lineup_slots: list[LineupSlot] = []
        rotation: list[PitcherAssignment] = []

        # LINEUP: one hitter per field position, batting order from the shared builder
        lineup_assignment = self._assign_lineup(hitters)
        batting_orders = {
            slot['card_id']: slot['batting_order']
            for slot in LineupBuilder([
                LineupCandidate(
                    card_id=card.card_id,
                    card_source=self._card_source(card),
                    field_position=position,
                    command=card.command,
                    outs=card.outs,
                    speed=card.speed,
                    points=card.points,
                )
                for position, card in lineup_assignment.items()
            ]).build()
        }
        for position in OFFENSE_POSITIONS:
            card = lineup_assignment.get(position)
            if card is None:
                continue
            src = self._card_source(card)
            roster_slots.append(TeamRosterSlot(
                card_id=card.card_id, card_source=src, roster_position=position,
                pick_source=PickSource.IMPORTED,
            ))
            lineup_slots.append(LineupSlot(
                card_id=card.card_id, card_source=src,
                field_position=position, batting_order=batting_orders[card.card_id],
            ))

        # BENCH: remaining hitters by games played
        lineup_ids = {c.card_id for c in lineup_assignment.values()}
        bench = sorted([c for c in hitters if c.card_id not in lineup_ids], key=self._by_games_played, reverse=True)
        for card in bench:
            roster_slots.append(TeamRosterSlot(
                card_id=card.card_id, card_source=self._card_source(card), roster_position='BE',
                pick_source=PickSource.IMPORTED,
            ))

        # ROTATION: starters by games started -> SP1..SPn, sized to however many the
        # pool actually has (capped by the number of role slots the UI supports)
        rotation_cards = sorted(starters, key=self._by_games_started, reverse=True)[:self.MAX_ROTATION_SLOTS]
        for i, card in enumerate(rotation_cards, start=1):
            role = f'SP{i}'
            src = self._card_source(card)
            roster_slots.append(TeamRosterSlot(
                card_id=card.card_id, card_source=src, roster_position=role,
                pick_source=PickSource.IMPORTED,
            ))
            rotation.append(PitcherAssignment(card_id=card.card_id, card_source=src, role=role))

        # BULLPEN: reliever with the most saves closes, the rest by appearances
        bullpen_pool = relievers + [c for c in starters if c not in rotation_cards]
        closer = max(bullpen_pool, key=self._by_saves) if bullpen_pool else None
        bullpen = [closer] if closer else []
        bullpen += sorted([c for c in bullpen_pool if c is not closer], key=self._by_games_played, reverse=True)
        for card in bullpen:
            role = 'CL' if card is closer else 'RP'
            src = self._card_source(card)
            roster_slots.append(TeamRosterSlot(
                card_id=card.card_id, card_source=src, roster_position=role,
                pick_source=PickSource.IMPORTED,
            ))
            rotation.append(PitcherAssignment(card_id=card.card_id, card_source=src, role=role))

        num_bench = len(bench)
        num_bullpen = len(bullpen)
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
            source=TeamSource.MLB,
            pts_limit=None,
            roster_size=len(roster_slots),
            min_bench=num_bench,
            min_bullpen=num_bullpen,
            num_starters=len(rotation_cards),
            roster=roster_slots,
            lineups=[Lineup(name=DEFAULT_LINEUP_NAME, index=0, slots=lineup_slots)],
            rotation=rotation,
            **team_kwargs,
        )

    def build_api_dict(self) -> dict:
        """Serialize the composed team to the same shape as the /user/teams endpoints."""
        team = self.build()
        data = team.model_dump(mode='json')
        total_points = sum(card.points or 0 for card in self.cards)
        data['total_points'] = total_points
        return data
