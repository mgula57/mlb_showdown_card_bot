from dataclasses import dataclass, field
from typing import Callable, Optional

from .team import (
    Team, TeamSource, CardSource, TeamRosterSlot, Lineup, LineupSlot, PitcherAssignment,
    PickSource, DEFAULT_LINEUP_NAME, infer_allowed_sets_from_cards,
)
from .autofill import OFFENSE_POSITIONS
from .lineup import LineupBuilder, LineupCandidate
from ...database.postgres_db import ExploreDataRecord
from ...shared.player_position import Position, PositionSlot


@dataclass
class RosterBuildDiagnostics:
    """Why a composed roster holds fewer cards than its input pool (see RosterToTeamConverter.diagnose).

    Every input card ends up either on the roster or in exactly one of the dropped lists, each
    entry a human-readable "Name (reason)" string.
    """
    pool_size: int
    roster_size: int
    max_roster_size: Optional[int]
    no_card_id: list[str] = field(default_factory=list)
    below_playing_time: list[str] = field(default_factory=list)
    relaxed_playing_time: list[str] = field(default_factory=list)
    left_off: list[str] = field(default_factory=list)
    rotation_shortfall: Optional[str] = None
    unfilled_positions: list[str] = field(default_factory=list)

    @property
    def is_short(self) -> bool:
        return self.max_roster_size is not None and self.roster_size < self.max_roster_size

    def reasons(self) -> list[str]:
        """Explanations for every card that didn't make the roster, plus why a short roster is short."""
        lines = []
        if self.no_card_id:
            lines.append(f"{len(self.no_card_id)} card(s) without a card_id: {', '.join(self.no_card_id)}")
        if self.below_playing_time:
            lines.append(
                f"{len(self.below_playing_time)} card(s) under the {RosterToTeamConverter.MIN_PLAYING_TIME_FRACTION:.0%} "
                f"playing-time cutoff: {', '.join(self.below_playing_time)}"
            )
        if self.relaxed_playing_time:
            lines.append(
                f"{len(self.relaxed_playing_time)} card(s) under the playing-time cutoff added back to fill the roster: "
                f"{', '.join(self.relaxed_playing_time)}"
            )
        if self.left_off:
            lines.append(f"{len(self.left_off)} eligible card(s) left off: {', '.join(self.left_off)}")
        if self.rotation_shortfall:
            lines.append(self.rotation_shortfall)
        lines += self.unfilled_positions
        if self.is_short:
            eligible = self.pool_size - len(self.no_card_id) - len(self.below_playing_time)
            if eligible < self.max_roster_size:
                lines.append(
                    f"only {eligible} of {self.pool_size} pooled card(s) are eligible, below the "
                    f"{self.max_roster_size}-man roster limit even with the playing-time cutoff relaxed"
                )
        return lines


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

    # Once the rotation's starters are picked (by games started), SP1..SP5 are ordered by a
    # weighted blend of workload and quality -- each scaled against the best of the selected
    # starters -- so a high-volume back-end arm doesn't front the rotation over the ace.
    ROTATION_ORDER_GS_WEIGHT = 0.5
    ROTATION_ORDER_POINTS_WEIGHT = 0.5

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
        self.team_id = team_id
        self.name = name
        self.abbreviation = abbreviation
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.season = season
        self.source = source
        self.input_cards = cards
        identified = [c for c in cards if c.card_id]
        self.cards = self._filter_by_playing_time(identified, protected_ids=protected_ids)
        self.relaxed_cards = self._relax_playing_time(identified, kept=self.cards)
        self.cards += self.relaxed_cards

    @staticmethod
    def _playing_time_groups(
        cards: list[ExploreDataRecord],
    ) -> list[tuple[list[ExploreDataRecord], Callable[[ExploreDataRecord], float], str]]:
        """Split cards into (group, playing-time measure, unit label) per role for _filter_by_playing_time.

        Hitters are measured in PA (falling back to G for older data without PA on record),
        starters in IP, and relievers in G (appearances) -- each the natural unit for that role.
        """
        hitters = [c for c in cards if c.player_type != 'PITCHER']
        pitchers = [c for c in cards if c.player_type == 'PITCHER']
        starters = [c for c in pitchers if Position.SP in (c.positions_list or [])]
        relievers = [c for c in pitchers if Position.SP not in (c.positions_list or [])]
        return [
            (hitters, lambda c: c.pa if c.pa is not None else (c.g or 0), 'PA'),
            (starters, lambda c: c.real_ip or 0.0, 'IP'),
            (relievers, lambda c: c.g or 0, 'G'),
        ]

    @classmethod
    def _playing_time_threshold(cls, group: list[ExploreDataRecord], measure: Callable[[ExploreDataRecord], float]) -> float:
        return max((measure(c) for c in group), default=0.0) * cls.MIN_PLAYING_TIME_FRACTION

    @classmethod
    def _playing_time_measures(cls, cards: list[ExploreDataRecord]) -> list[tuple[ExploreDataRecord, float, float, str]]:
        """(card, playing time, its role's cutoff, unit) for every card -- see _playing_time_groups."""
        measures = []
        for group, measure, unit in cls._playing_time_groups(cards):
            threshold = cls._playing_time_threshold(group, measure)
            measures += [(c, measure(c), threshold, unit) for c in group]
        return measures

    @classmethod
    def _filter_by_playing_time(
        cls, cards: list[ExploreDataRecord], protected_ids: set[str],
    ) -> list[ExploreDataRecord]:
        """Drop cameo-sample cards relative to the team's own most-used player at each role.

        A card survives if it clears MIN_PLAYING_TIME_FRACTION of the team's max for its role
        (see _playing_time_groups), so the cutoff scales down automatically for a team assembled
        mid-season or one with thin, injury-riddled depth, rather than excluding everyone (or no
        one) against a fixed number.
        """
        return [
            c for c, measure, threshold, _ in cls._playing_time_measures(cards)
            if c.card_id in protected_ids or measure >= threshold
        ]

    def _relax_playing_time(self, cards: list[ExploreDataRecord], kept: list[ExploreDataRecord]) -> list[ExploreDataRecord]:
        """Cameo cards to add back when the filtered pool can't fill the season's roster limit.

        Every kept card is rostered up to the cap (lineup + bench take all hitters, rotation +
        bullpen all pitchers), so the shortfall is simply the cap minus the kept count. It's made
        up with the cameos closest to their role's cutoff first; a full pool adds nothing.
        """
        max_roster_size = self._max_roster_size(self.season)
        shortfall = (max_roster_size or 0) - len(kept)
        if shortfall <= 0:
            return []
        kept_ids = {c.card_id for c in kept}
        cameos = [(c, measure / threshold) for c, measure, threshold, _ in self._playing_time_measures(cards)
                  if c.card_id not in kept_ids and threshold > 0]
        cameos.sort(key=lambda pair: pair[1], reverse=True)
        return [c for c, _ in cameos[:shortfall]]

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

    def _order_rotation(self, rotation_cards: list[ExploreDataRecord]) -> list[ExploreDataRecord]:
        """Order the already-selected starters SP1..SPn by weighted, max-normalized GS and points."""
        max_gs = max((c.gs or 0 for c in rotation_cards), default=0) or 1
        max_points = max((c.points or 0 for c in rotation_cards), default=0) or 1

        def _score(card: ExploreDataRecord) -> tuple:
            weighted = (
                self.ROTATION_ORDER_GS_WEIGHT * (card.gs or 0) / max_gs
                + self.ROTATION_ORDER_POINTS_WEIGHT * (card.points or 0) / max_points
            )
            return (weighted, *self._by_games_started(card))

        return sorted(rotation_cards, key=_score, reverse=True)

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

    @staticmethod
    def _bullpen_pool(
        starters: list[ExploreDataRecord], relievers: list[ExploreDataRecord], rotation_ids: set[str],
    ) -> list[ExploreDataRecord]:
        """Pitchers eligible for the bullpen/closer roles.

        A real single-season roster's extra starter (didn't make the 5-man rotation) becomes a
        long reliever in real life -- a normal, common bullpen role -- so both leftover starters
        and true relievers are eligible here by default. Overridden by EraRosterDrafter, where a
        career-bests pool makes that comparison meaningless: an elite starter's off-year should
        drop off the roster entirely rather than "become" a reliever.
        """
        return [c for c in relievers if c.card_id not in rotation_ids] + [c for c in starters if c.card_id not in rotation_ids]

    def _compose_depth(
        self, bench: list[ExploreDataRecord], bullpen: list[ExploreDataRecord], closer: Optional[ExploreDataRecord],
        core_count: int, max_roster_size: int,
    ) -> tuple[list[ExploreDataRecord], list[ExploreDataRecord]]:
        """Trim bench/bullpen depth (beyond lineup + rotation + closer) down to the roster cap.

        Pools the bench and non-closer bullpen together and keeps the highest-value players
        regardless of hitter/pitcher split -- appropriate for a real single season, where uneven
        bench/bullpen depth (e.g. a thin bench on a pitching-heavy roster) is a real fact of that
        specific roster. Overridden by EraRosterDrafter, where pooling a career-bests candidate
        list this way would starve the bench of picks entirely (see its own _compose_depth).
        """
        depth_pool = bench + [c for c in bullpen if c is not closer]
        depth = sorted(depth_pool, key=self._by_games_played, reverse=True)[:max(0, max_roster_size - core_count)]
        depth_ids = {c.card_id for c in depth}
        bench_out = [c for c in bench if c.card_id in depth_ids]
        bullpen_out = [c for c in bullpen if c is closer or c.card_id in depth_ids]
        return bench_out, bullpen_out

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
                    if c.card_id not in used_ids and self._pos_matches(c, self._slot(pos))
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

        for position in [p for p in OFFENSE_POSITIONS if p not in assignment]:
            self._fill_by_shifting(position, assignment, hitters, used_ids)

        return assignment

    @staticmethod
    def _slot(position: str) -> PositionSlot:
        return PositionSlot('CA' if position == 'C' else position)

    def _fill_by_shifting(
        self, position: str, assignment: dict[str, ExploreDataRecord], hitters: list[ExploreDataRecord], used_ids: set[str],
    ) -> None:
        """Fill an empty lineup position by shifting already-placed hitters along a chain.

        Passes 1-2 are greedy, so a versatile player can be locked into his most-played position
        while the only other hole he could cover goes empty (e.g. 2025 PIT: Triolo at SS leaves
        3B open, though Gonzales can play SS and Valdez 2B). Breadth-first search finds the
        shortest chain of moves -- a placed hitter slides into the open position, his old spot
        becomes the new opening -- ending with an unused hitter; the best one by games played wins
        among those at the shortest depth. Forced (All-Star) positions are never moved.
        """
        forced_ids = set(self.forced_positions)
        # came_from[opening] = (position the mover fills, mover) -- mover vacates `opening`.
        came_from: dict[str, Optional[tuple[str, ExploreDataRecord]]] = {position: None}
        frontier = [position]
        while frontier:
            fillers = [
                (opening, c) for opening in frontier for c in hitters
                if c.card_id not in used_ids and self._pos_matches(c, self._slot(opening))
            ]
            if fillers:
                opening, filler = max(fillers, key=lambda pair: self._by_games_played(pair[1]))
                assignment[opening] = filler
                used_ids.add(filler.card_id)
                while came_from[opening] is not None:
                    target, mover = came_from[opening]
                    assignment[target] = mover
                    opening = target
                return
            next_frontier = []
            for opening in frontier:
                for held, card in assignment.items():
                    if held in came_from or card.card_id in forced_ids or not self._pos_matches(card, self._slot(opening)):
                        continue
                    came_from[held] = (opening, card)
                    next_frontier.append(held)
            frontier = next_frontier

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
        rotation_cards = self._order_rotation(rotation_cards)

        # If the real starting pitcher is known (All-Star game), pin them to SP1 regardless of
        # season role — even a reliever-by-season who got the ASG start belongs at the front.
        if self.forced_starting_pitcher_id:
            forced_sp = next((c for c in pitchers if c.card_id == self.forced_starting_pitcher_id), None)
            if forced_sp is not None:
                rotation_cards = [forced_sp] + [c for c in rotation_cards if c.card_id != forced_sp.card_id]
                rotation_cards = rotation_cards[:self.MAX_ROTATION_SLOTS]

        # BULLPEN: reliever with the most saves closes, the rest by appearances
        rotation_ids = {c.card_id for c in rotation_cards}
        bullpen_pool = self._bullpen_pool(starters=starters, relievers=relievers, rotation_ids=rotation_ids)
        closer = max(bullpen_pool, key=self._by_saves) if bullpen_pool else None
        bullpen = [closer] if closer else []
        bullpen += sorted([c for c in bullpen_pool if c is not closer], key=self._by_games_played, reverse=True)

        # Cap total roster size to the historical limit for the season: trim the
        # weakest bench/relief depth (lineup, rotation, and the closer are kept intact)
        max_roster_size = self._max_roster_size(self.season)
        if max_roster_size is not None:
            core_count = len(lineup_slots) + len(rotation_cards) + (1 if closer else 0)
            bench, bullpen = self._compose_depth(
                bench=bench, bullpen=bullpen, closer=closer,
                core_count=core_count, max_roster_size=max_roster_size,
            )

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

        # Scope a fork of this synthesized roster to the sources/sets it's actually built from.
        rostered_ids = {s.card_id for s in roster_slots}
        team_kwargs.update(infer_allowed_sets_from_cards(
            [c for c in self.cards if c.card_id in rostered_ids]
        ))

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

    def diagnose(self, team: Optional[Team] = None) -> RosterBuildDiagnostics:
        """Account for every input card that didn't make the composed roster, and why.

        Pass an already-built `team` to avoid composing it twice.
        """
        team = team or self.build()
        rostered_ids = {s.card_id for s in team.roster}
        kept_ids = {c.card_id for c in self.cards}

        # Thresholds are recomputed over the same card_id'd pool _filter_by_playing_time saw.
        relaxed_ids = {c.card_id for c in self.relaxed_cards}
        below_playing_time, relaxed_playing_time = [], []
        for c, measure, threshold, unit in self._playing_time_measures([c for c in self.input_cards if c.card_id]):
            label = f"{c.name} ({measure:g} {unit} < {threshold:.1f})"
            if c.card_id in relaxed_ids:
                relaxed_playing_time.append(label)
            elif c.card_id not in kept_ids:
                below_playing_time.append(label)

        # Rotation slots only go to SP-tagged cards, so a short rotation is a pool fact, not a trim.
        starters = [c for c in self.cards if c.player_type == 'PITCHER' and Position.SP in (c.positions_list or [])]
        rotation_shortfall = None
        if len(starters) < self.MAX_ROTATION_SLOTS:
            filtered_sp = [c.name for c in self.input_cards if c.card_id and c.card_id not in kept_ids
                           and c.player_type == 'PITCHER' and Position.SP in (c.positions_list or [])]
            rotation_shortfall = (
                f"only {len(starters)} SP-eligible pitcher(s) after filtering (rotation needs {self.MAX_ROTATION_SLOTS}); "
                f"the rest are tagged RP/CL" + (f"; filtered SP cameo(s): {', '.join(filtered_sp)}" if filtered_sp else "")
            )

        # Lineup positions nobody could fill, plus any filtered cameo who was eligible there.
        filled = {s.field_position for lineup in team.lineups for s in lineup.slots}
        unfilled_positions = []
        for position in OFFENSE_POSITIONS:
            if position in filled:
                continue
            slot = PositionSlot('CA' if position == 'C' else position)
            cameos = [c.name for c in self.input_cards if c.card_id and c.card_id not in kept_ids
                      and c.player_type != 'PITCHER' and self._pos_matches(c, slot)]
            unfilled_positions.append(
                f"no eligible hitter left for {position}"
                + (f"; filtered cameo(s) who could play it: {', '.join(cameos)}" if cameos else "")
            )

        return RosterBuildDiagnostics(
            relaxed_playing_time=relaxed_playing_time,
            rotation_shortfall=rotation_shortfall,
            unfilled_positions=unfilled_positions,
            pool_size=len(self.input_cards),
            roster_size=len(team.roster),
            max_roster_size=self._max_roster_size(self.season),
            no_card_id=[c.name or '?' for c in self.input_cards if not c.card_id],
            below_playing_time=below_playing_time,
            left_off=[
                f"{c.name} ({'P' if c.player_type == 'PITCHER' else 'H'}, {c.g or 0} G)"
                for c in self.cards if c.card_id not in rostered_ids
            ],
        )

    def build_api_dict(self) -> dict:
        """Serialize the composed team to the same shape as the /user/teams endpoints."""
        team = self.build()
        data = team.model_dump(mode='json')
        total_points = sum(card.points or 0 for card in self.cards)
        data['total_points'] = total_points
        return data
