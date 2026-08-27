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

    # Real rosters are presented with a fixed 5-man rotation: a starter beyond the 5th by
    # games started is folded into the bullpen. (User-built teams can carry more — see
    # ROTATION_ROLES / num_starters — but a synthesized real roster deliberately caps here.)
    MAX_ROTATION_SLOTS = 5

    # A cameo appearance (e.g. a September call-up's lone start) shouldn't be eligible to win a
    # roster spot just because nobody else is available at that position. Cutoff is relative to
    # the team's own busiest player at each role rather than a fixed number, since a fixed floor
    # either excludes everyone on a rebuilding/injury-riddled roster or (mid-season) a team that
    # simply hasn't played many games yet.
    MIN_PLAYING_TIME_FRACTION = 0.15

    def __init__(
        self,
        cards: list[ExploreDataRecord],
        team_id: str,
        name: str,
        abbreviation: str,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        season: Optional[int] = None,
        source: TeamSource = TeamSource.MLB,
        forced_positions: Optional[dict[str, str]] = None,
        forced_batting_order: Optional[dict[str, int]] = None,
        forced_starting_pitcher_id: Optional[str] = None,
    ) -> None:
        # Optional real-roster overrides (used for All-Star teams, where the actual starting
        # lineup positions, batting order, and starting pitcher are known rather than derived
        # from playing time). All keyed by card_id.
        self.forced_positions = forced_positions or {}
        self.forced_batting_order = forced_batting_order or {}
        self.forced_starting_pitcher_id = forced_starting_pitcher_id

        # A card can't be placed on the roster without an identifier the frontend can look up.
        # Cameo-sample cards are dropped too, except any card a forced override depends on --
        # those reflect a verified real-life role (e.g. an actual All-Star starter) and should
        # never be silently excluded by a playing-time heuristic.
        protected_ids = set(self.forced_positions) | set(self.forced_batting_order)
        if self.forced_starting_pitcher_id:
            protected_ids.add(self.forced_starting_pitcher_id)
        self.cards = self._filter_by_playing_time([c for c in cards if c.card_id], protected_ids=protected_ids)
        self.team_id = team_id
        self.name = name
        self.abbreviation = abbreviation
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.season = season
        self.source = source

    @classmethod
    def _filter_by_playing_time(
        cls, cards: list[ExploreDataRecord], protected_ids: set[str],
    ) -> list[ExploreDataRecord]:
        """Drop cameo-sample cards relative to the team's own most-used player at each role.

        Hitters are indexed off the team's max PA (falling back to G for older data without PA
        on record), starters off the team's max IP, and relievers off the team's max G
        (appearances) -- each the natural playing-time unit for that role. A card survives if it
        clears MIN_PLAYING_TIME_FRACTION of that team-specific max, so the cutoff scales down
        automatically for a team assembled mid-season or one with thin, injury-riddled depth,
        rather than excluding everyone (or no one) against a fixed number.
        """
        hitters = [c for c in cards if c.player_type != 'PITCHER']
        pitchers = [c for c in cards if c.player_type == 'PITCHER']
        starters = [c for c in pitchers if Position.SP in (c.positions_list or [])]
        relievers = [c for c in pitchers if Position.SP not in (c.positions_list or [])]

        def _hitter_measure(card: ExploreDataRecord) -> float:
            return card.pa if card.pa is not None else (card.g or 0)

        def _starter_measure(card: ExploreDataRecord) -> float:
            return card.real_ip or 0.0

        def _reliever_measure(card: ExploreDataRecord) -> float:
            return card.g or 0

        def _keep(group: list[ExploreDataRecord], measure) -> list[ExploreDataRecord]:
            threshold = max((measure(c) for c in group), default=0.0) * cls.MIN_PLAYING_TIME_FRACTION
            return [c for c in group if c.card_id in protected_ids or measure(c) >= threshold]

        return (
            _keep(hitters, _hitter_measure)
            + _keep(starters, _starter_measure)
            + _keep(relievers, _reliever_measure)
        )

    @staticmethod
    def _max_roster_size(season: Optional[int]) -> Optional[int]:
        """Historical roster-size limit for the season, used to cap bench/bullpen depth.

        Active rosters expanded over time: 21 pre-1920, 25 through the 20th century,
        26 starting in 2020 (Opening Day rosters permanently grew from 25 to 26).
        """
        if season is None:
            return None
        if season >= 2020:
            return 26
        if season >= 1920:
            return 25
        return 21

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

        Deliberately does NOT fall back to `secondary_positions` for players with no primary
        position on record. That case means BREF saw too little playing time to name a primary
        position at all (e.g. a September call-up who DH'd once) — trusting it as "preferred"
        let a near-unplayed cameo win a lineup slot outright whenever he happened to be the only
        candidate in an otherwise-empty preferred pool (most often DH, since few regulars carry
        DH as their primary position). Returning None here routes those players to pass 2 instead,
        where they compete for the position on games played like everyone else.
        """
        return card.primary_positions[0] if card.primary_positions else None

    def _assign_lineup(self, hitters: list[ExploreDataRecord]) -> dict[str, ExploreDataRecord]:
        """Assign the 9 lineup positions to hitters.

        Pass 1 prefers each hitter's most-played position (primary_positions).
        Pass 2 falls back to the broader positions_list-based eligibility (the pre-existing
        logic, which folds LF/RF together and allows any hitter at DH) for any position that
        pass 1 couldn't fill. Both passes fill the scarcest position first so a player who is
        the only option at a position isn't consumed by a deeper one.
        """
        assignment: dict[str, ExploreDataRecord] = {}
        used_ids: set[str] = set()

        # Pass 0: honor explicit position assignments (e.g. All-Star starters) before any heuristic.
        if self.forced_positions:
            for card in hitters:
                pos = self.forced_positions.get(card.card_id)
                if pos in OFFENSE_POSITIONS and pos not in assignment and card.card_id not in used_ids:
                    assignment[pos] = card
                    used_ids.add(card.card_id)

        preferred_candidates: dict[str, list[ExploreDataRecord]] = {pos: [] for pos in OFFENSE_POSITIONS}
        for card in hitters:
            if card.card_id in used_ids:
                continue
            pos = self._preferred_position(card)
            if pos in preferred_candidates:
                preferred_candidates[pos].append(card)

        for position in sorted([p for p in OFFENSE_POSITIONS if p not in assignment], key=lambda p: len(preferred_candidates[p])):
            candidates = [c for c in preferred_candidates[position] if c.card_id not in used_ids]
            if not candidates:
                continue
            picked = max(candidates, key=self._by_games_played)
            assignment[position] = picked
            used_ids.add(picked.card_id)

        remaining_positions = [p for p in OFFENSE_POSITIONS if p not in assignment]
        if remaining_positions:
            eligible = {
                pos: [
                    c for c in hitters
                    if c.card_id not in used_ids and self._pos_matches(c, PositionSlot('CA' if pos == 'C' else pos))
                ]
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
        # Honor a known batting order (All-Star lineups carry the real 1-9) over the derived one.
        for card_id, order in self.forced_batting_order.items():
            if card_id in batting_orders:
                batting_orders[card_id] = order
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

        # ROTATION: starters by games started -> SP1..SPn, sized to however many the
        # pool actually has (capped by the number of role slots the UI supports)
        rotation_cards = sorted(starters, key=self._by_games_started, reverse=True)[:self.MAX_ROTATION_SLOTS]

        # If the real starting pitcher is known (All-Star game), pin them to SP1 regardless of
        # season role — even a reliever-by-season who got the ASG start belongs at the front.
        if self.forced_starting_pitcher_id:
            forced_sp = next((c for c in pitchers if c.card_id == self.forced_starting_pitcher_id), None)
            if forced_sp is not None:
                rotation_cards = [forced_sp] + [c for c in rotation_cards if c.card_id != forced_sp.card_id]
                rotation_cards = rotation_cards[:self.MAX_ROTATION_SLOTS]

        # BULLPEN: reliever with the most saves closes, the rest by appearances
        rotation_ids = {c.card_id for c in rotation_cards}
        bullpen_pool = [c for c in relievers if c.card_id not in rotation_ids] + [c for c in starters if c.card_id not in rotation_ids]
        closer = max(bullpen_pool, key=self._by_saves) if bullpen_pool else None
        bullpen = [closer] if closer else []
        bullpen += sorted([c for c in bullpen_pool if c is not closer], key=self._by_games_played, reverse=True)

        # Cap total roster size to the historical limit for the season: trim the
        # weakest bench/relief depth (lineup, rotation, and the closer are kept intact)
        max_roster_size = self._max_roster_size(self.season)
        if max_roster_size is not None:
            core_count = len(lineup_slots) + len(rotation_cards) + (1 if closer else 0)
            depth_pool = bench + [c for c in bullpen if c is not closer]
            depth = sorted(depth_pool, key=self._by_games_played, reverse=True)[:max(0, max_roster_size - core_count)]
            depth_ids = {c.card_id for c in depth}
            bench = [c for c in bench if c.card_id in depth_ids]
            bullpen = [c for c in bullpen if c is closer or c.card_id in depth_ids]

        for card in bench:
            roster_slots.append(TeamRosterSlot(
                card_id=card.card_id, card_source=self._card_source(card), roster_position='BE',
                pick_source=PickSource.IMPORTED,
            ))

        for i, card in enumerate(rotation_cards, start=1):
            role = f'SP{i}'
            src = self._card_source(card)
            roster_slots.append(TeamRosterSlot(
                card_id=card.card_id, card_source=src, roster_position=role,
                pick_source=PickSource.IMPORTED,
            ))
            rotation.append(PitcherAssignment(card_id=card.card_id, card_source=src, role=role))

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
            source=self.source,
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
