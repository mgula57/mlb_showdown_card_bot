"""Roster snapshots for the sim result screen's field view (My Team tab).

Two sources fill the same `SimClubRoster` shape:
  - DRAFTED: a takeover/challenge club's builder team, exactly as it ran (`from_team`).
  - MOST_USED: a real club, whose lineup the engine rebuilds every game (rest days, injuries,
    deadline trades), so there is no single lineup to snapshot - instead the season's usage is
    read back off its statlines (`MostUsedRosterBuilder`).

Card ids only (~3 KB per club); the client resolves the cards itself.
"""
from enum import Enum
from typing import Callable, Optional

from pydantic import BaseModel, Field

from ..card.team_builder.lineup import LineupBuilder, LineupCandidate
from ..card.team_builder.team import (
    CardSource, DEFAULT_LINEUP_NAME, Lineup, LineupSlot, PickSource, PitcherAssignment, ROTATION_ROLES,
    Team as BuilderTeam, TeamRosterSlot,
)
from ..shared.player_position import PlayerSubType, PlayerType, PositionSlot
from .stats import StatCategory, Stats, real_card_id


class SimClubRosterSource(str, Enum):
    DRAFTED = 'drafted'
    MOST_USED = 'most_used'


class SimRosterSlot(TeamRosterSlot):
    """`TeamRosterSlot` minus its draft bookkeeping, which the result screen never shows."""
    draft_order: Optional[int] = Field(default=None, exclude=True)
    pick_source: PickSource = Field(default=PickSource.MANUAL, exclude=True)


class SimClubRoster(BaseModel):
    source: SimClubRosterSource = SimClubRosterSource.DRAFTED
    roster: list[SimRosterSlot] = []
    lineup: Optional[Lineup] = None             # THE DEFAULT (INDEX 0) LINEUP
    rotation: list[PitcherAssignment] = []      # STARTERS ONLY - THE BULLPEN IS READ OFF `roster`
    bench_pts_multiplier: float = 1.0
    bullpen_order_custom: bool = False
    min_bench: int = 0
    min_bullpen: int = 0
    num_starters: int = 5

    @classmethod
    def from_team(cls, team: BuilderTeam) -> 'SimClubRoster':
        default_lineup = next((ln for ln in team.lineups if ln.index == 0), team.lineups[0] if team.lineups else None)
        return cls(
            source=SimClubRosterSource.DRAFTED,
            roster=[SimRosterSlot(**slot.model_dump()) for slot in team.roster],
            lineup=default_lineup,
            rotation=[r for r in team.rotation if r.role in ROTATION_ROLES],
            bench_pts_multiplier=team.bench_pts_multiplier, bullpen_order_custom=team.bullpen_order_custom,
            min_bench=team.min_bench, min_bullpen=team.min_bullpen, num_starters=team.num_starters,
        )


class MostUsedRosterBuilder:
    """A real club's season as a depth chart, read back off its statlines.

      - Lineup: each position goes to whoever logged the most plate appearances there
        (`Stats.positions_played`), claimed greedily from the largest PA count down so a player
        holds at most one spot. Batting order comes from the team builder's own `LineupBuilder`,
        fed the sim season's OBP/SLG.
      - Rotation: the starters with the most innings (the engine doesn't track games started).
      - Bullpen: the relievers with the most innings, the saves leader pinned as closer.
      - Bench: the most-used remaining hitters.
    Bench and bullpen are capped to a 26-man active roster's shape, so a season's worth of
    call-ups and deadline arrivals doesn't bury the regulars.
    """

    _FIELD_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH']
    _ROTATION_SIZE = 5
    _BULLPEN_SIZE = 8
    _BENCH_SIZE = 4

    def __init__(self, stats: list[Stats], card_source_for: Callable[[str], str]) -> None:
        self.hitters = [s for s in stats if s.player_type == PlayerType.HITTER and s.stat(StatCategory.PA) > 0]
        self.pitchers = [s for s in stats if s.player_type == PlayerType.PITCHER and s.stat(StatCategory.IP) > 0]
        self.card_source_for = card_source_for

    @staticmethod
    def _pa_at(stats: Stats, position: str) -> int:
        # THE ENGINE RECORDS CATCHER AS PositionSlot.CA ('CA'); THE BUILDER LINEUP USES 'C'.
        key = PositionSlot.CA.value if position == 'C' else position
        return stats.positions_played.get(key, 0)

    def _slot(self, stats: Stats, roster_position: str) -> SimRosterSlot:
        card_id = real_card_id(stats.id)
        return SimRosterSlot(card_id=card_id, card_source=CardSource(self.card_source_for(card_id)), roster_position=roster_position)

    def _assign_positions(self) -> dict[str, Stats]:
        """The starting nine: the most-used hitters, each at the spot they played most among them.

        Solved as an exact assignment (a DP over which positions are filled - 2^9 states), not a
        greedy per-position claim. Greedy benches a regular whose PA are spread over several spots
        (a CF/LF/RF who never leads any single one) behind a part-timer who led the last open spot.
        The objective ranks the starters' season PA first and their PA at the assigned spot second.
        A player can only take a spot he logged PA at, except DH, which is open to any hitter when
        the club used a DH at all (a pre-2022 NL club has none, so the ace bats ninth instead).
        """
        uses_dh = any(self._pa_at(s, 'DH') > 0 for s in self.hitters)
        positions = [pos for pos in self._FIELD_POSITIONS if pos != 'DH' or uses_dh]
        # SEASON PA OUTWEIGHS ANY SINGLE POSITION'S PA, SO A REGULAR IS NEVER BENCHED FOR FIT.
        season_weight = 1 + max((int(s.stat(StatCategory.PA)) for s in self.hitters), default=0)

        def score(stats: Stats, pos: str) -> Optional[int]:
            pa_at = self._pa_at(stats, pos)
            if pa_at <= 0 and pos != 'DH':
                return None
            return int(stats.stat(StatCategory.PA)) * season_weight + pa_at

        # MASK OF FILLED POSITIONS -> (BEST SCORE, ASSIGNMENTS AS (POSITION INDEX, HITTER INDEX))
        best: dict[int, tuple[int, tuple[tuple[int, int], ...]]] = {0: (0, ())}
        for h_idx, stats in enumerate(self.hitters):
            step = dict(best)  # SKIPPING THIS HITTER KEEPS EVERY STATE AS-IS
            for mask, (total, picks) in best.items():
                for p_idx, pos in enumerate(positions):
                    if mask & (1 << p_idx) or (value := score(stats, pos)) is None:
                        continue
                    new_mask, new_total = mask | (1 << p_idx), total + value
                    if new_mask not in step or new_total > step[new_mask][0]:
                        step[new_mask] = (new_total, picks + ((p_idx, h_idx),))
            best = step

        _, picks = max(best.values(), key=lambda entry: entry[0])
        return {positions[p_idx]: self.hitters[h_idx] for p_idx, h_idx in sorted(picks)}

    def _candidate(self, stats: Stats, field_position: str) -> LineupCandidate:
        slot = self._slot(stats, field_position)
        return LineupCandidate(
            card_id=slot.card_id, card_source=slot.card_source.value, field_position=field_position,
            command=round(stats.command) if stats.command else None, speed=stats.speed or None, points=stats.points or None,
            onbase_perc=stats.obp, slugging_perc=stats.slg,
        )

    def build(self) -> SimClubRoster:
        by_ip = lambda s: s.stat(StatCategory.IP)
        starters = sorted((p for p in self.pitchers if p.player_sub_type == PlayerSubType.STARTING_PITCHER), key=by_ip, reverse=True)[:self._ROTATION_SIZE]
        starter_ids = {s.id for s in starters}
        relievers = sorted((p for p in self.pitchers if p.id not in starter_ids), key=by_ip, reverse=True)[:self._BULLPEN_SIZE]
        closer = max(relievers, key=lambda s: s.stat(StatCategory.SAVES), default=None)
        if closer is not None and closer.stat(StatCategory.SAVES) <= 0:
            closer = None

        by_position = self._assign_positions()
        starter_ids_by_pos = {s.id for s in by_position.values()}
        bench = sorted((h for h in self.hitters if h.id not in starter_ids_by_pos), key=lambda s: s.stat(StatCategory.PA), reverse=True)[:self._BENCH_SIZE]

        # NO DH IN THE LEAGUE (PRE-2022 NL) -> THE ACE BATS NINTH, AS IN THE TEAM BUILDER.
        pitcher_candidate = self._candidate(starters[0], 'SP') if 'DH' not in by_position and starters else None
        lineup_slots = LineupBuilder(
            [self._candidate(stats, pos) for pos, stats in by_position.items()], pitcher_candidate,
        ).build()

        rotation = [
            PitcherAssignment(card_id=real_card_id(s.id), card_source=CardSource(self.card_source_for(real_card_id(s.id))), role=ROTATION_ROLES[i])
            for i, s in enumerate(starters)
        ]
        roster = (
            [self._slot(stats, pos) for pos, stats in by_position.items()]
            + [self._slot(s, 'BE') for s in bench]
            + [self._slot(s, ROTATION_ROLES[i]) for i, s in enumerate(starters)]
            + [self._slot(s, 'CL' if s is closer else 'RP') for s in relievers]
        )
        return SimClubRoster(
            source=SimClubRosterSource.MOST_USED,
            roster=roster,
            lineup=Lineup(name=DEFAULT_LINEUP_NAME, index=0, slots=[LineupSlot(**slot) for slot in lineup_slots]),
            rotation=rotation,
            # BULLPEN SHOWS IN USAGE ORDER (MOST INNINGS FIRST), NOT CARD POINTS.
            bullpen_order_custom=True,
            num_starters=len(rotation),
        )
