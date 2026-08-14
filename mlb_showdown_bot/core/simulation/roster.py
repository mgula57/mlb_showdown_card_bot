from dataclasses import dataclass, field
from datetime import date, timedelta
from random import Random
from typing import TYPE_CHECKING, Optional, Union

from pydantic import BaseModel

from ..card.showdown_player_card import ShowdownPlayerCard
from ..shared.player_position import PlayerSubType, PositionSlot, PositionSlotParent
from .models import Transaction, TransactionType
from .player import SimPitcher, SimPlayer
from .player_group import PositionEligibility

if TYPE_CHECKING:
    from .team import SimTeam

# ----------------------------------------------------------------------------------------------
# INJURY CALIBRATION CONSTANTS
# ----------------------------------------------------------------------------------------------

_MIN_IL_SHARE = 0.015          # EVERYONE CARRIES SOME RISK, EVEN IRON-MAN SEASONS
_MAX_IL_SHARE = 0.60
_MAX_HAZARD_PER_GAME = 0.25

_STINT_SHORT_RANGE = (3, 10)
_STINT_MEDIUM_RANGE = (11, 25)
_STINT_LONG_RANGE = (26, 75)
_STINT_SHORT_MEAN = 6.5
_STINT_MEDIUM_MEAN = 18.0
_STINT_LONG_MEAN = 50.0
_P_MEDIUM = 0.30
_P_LONG_BASE = 0.10
_P_LONG_MAX = 0.55

_RP_REFERENCE_APPEARANCE_RATE = 0.40   # A HEALTHY FULL-SEASON RP APPEARS IN ~40% OF TEAM GAMES
_RP_MISSED_DAMPENER = 0.60             # RP APPEARANCE COUNTS ARE USAGE-DRIVEN, NOT ONLY HEALTH

# CONFIDENCE REFERENCES: A LOW-PLAYING-TIME CARD (BENCH BAT, LONG RELIEVER, SEPTEMBER CALL-UP) IS
# USUALLY LOW BECAUSE OF HIS ROLE, NOT AN INJURY - THE GAP VS. THE "HEALTHY" BASELINE IS ONLY
# TRUSTWORTHY AS AN INJURY SIGNAL ONCE A PLAYER HAS ENOUGH REAL SAMPLE TO SHOW HE WAS ACTUALLY
# USED AS AN EVERYDAY PLAYER. BELOW THE REFERENCE, `missed_games` IS SCALED DOWN PROPORTIONALLY
# RATHER THAN TAKEN AT FACE VALUE - OTHERWISE EVERY RESERVE ON THE 40-MAN (WHICH THIS SYSTEM ALSO
# PROFILES, SINCE THEY CAN BE CALLED UP) READS AS SEVERELY INJURED PURELY BECAUSE HE'S A RESERVE.
_ROLE_CONFIDENCE_PA_REFERENCE = 400.0
_ROLE_CONFIDENCE_GS_REFERENCE = 25.0
_ROLE_CONFIDENCE_G_REFERENCE = 40.0

# ----------------------------------------------------------------------------------------------
# RESERVE SAMPLE-SIZE FLOORS. 40 IS A MAXIMUM, NOT A QUOTA - CUP-OF-COFFEE CARDS ARE NOISE AND
# ARE DROPPED RATHER THAN PADDING THE RESERVE POOL. SCALED DOWN FOR SHORTENED REAL SEASONS.
# ----------------------------------------------------------------------------------------------

RESERVE_MIN_G_POSITION = 10
RESERVE_MIN_PA_POSITION = 25
RESERVE_MIN_G_PITCHER = 5
RESERVE_MIN_IP_PITCHER = 10


class InjuryProfile(BaseModel):
    """Per-player injury hazard, calibrated so a player's expected simulated missed games match
    the gap between his real games played and a role-adjusted healthy baseline. Built once per
    player at roster construction and never mutated afterward.
    """

    player_id: str
    expected_missed_games: float
    il_share: float
    hazard_per_game: float     # P(NEW IL STINT), ROLLED ONCE PER TEAM-GAME WHILE HEALTHY
    p_short: float
    p_medium: float
    p_long: float
    games_per_day: float

    @classmethod
    def _build(cls, player_id: str, missed_games: float, games_per_team: int, games_per_day: float, severity: float) -> 'InjuryProfile':
        S = max(games_per_team, 1)
        il_share = min(max(missed_games / S, _MIN_IL_SHARE), _MAX_IL_SHARE)
        missed_games = il_share * S

        p_long = min(_P_LONG_BASE + il_share, _P_LONG_MAX)
        p_medium = _P_MEDIUM
        p_short = 1.0 - p_long - p_medium
        if p_short < 0:
            p_medium += p_short
            p_short = 0.0

        expected_days_per_stint = p_short * _STINT_SHORT_MEAN + p_medium * _STINT_MEDIUM_MEAN + p_long * _STINT_LONG_MEAN
        expected_games_per_stint = max(expected_days_per_stint * games_per_day, 1.0)
        expected_stints = missed_games / expected_games_per_stint
        healthy_games = max(S - missed_games, 1.0)
        hazard_per_game = min(max((expected_stints / healthy_games) * severity, 0.0), _MAX_HAZARD_PER_GAME)

        return cls(
            player_id=player_id, expected_missed_games=missed_games, il_share=il_share,
            hazard_per_game=hazard_per_game, p_short=p_short, p_medium=p_medium, p_long=p_long,
            games_per_day=games_per_day,
        )

    @classmethod
    def for_position_player(cls, player: SimPlayer, games_per_team: int, real_games_per_team: int, games_per_day: float, severity: float) -> 'InjuryProfile':
        missed = 0.0
        if real_games_per_team > 0:
            r = player.expected_games_between_rest
            healthy_games = games_per_team * r / (r + 1)
            real_pa = player.stats.get('PA', 0)
            real_g_scaled = player.stats.get('G', 0) * games_per_team / real_games_per_team
            confidence = min(1.0, real_pa / _ROLE_CONFIDENCE_PA_REFERENCE)
            missed = max(0.0, healthy_games - real_g_scaled) * confidence
        return cls._build(player.id, missed, games_per_team, games_per_day, severity)

    @classmethod
    def for_starter(cls, pitcher: SimPitcher, games_per_team: int, real_games_per_team: int, games_per_day: float, severity: float, rotation_size: int) -> 'InjuryProfile':
        missed = 0.0
        if real_games_per_team > 0:
            rotation_size = max(rotation_size, 1)
            healthy_starts = games_per_team / rotation_size
            real_gs = pitcher.stats.get('GS', 0) or pitcher.stats.get('G', 0)
            real_gs_scaled = real_gs * games_per_team / real_games_per_team
            confidence = min(1.0, real_gs / _ROLE_CONFIDENCE_GS_REFERENCE)
            missed = max(0.0, healthy_starts - real_gs_scaled) * rotation_size * confidence
        return cls._build(pitcher.id, missed, games_per_team, games_per_day, severity)

    @classmethod
    def for_reliever(cls, pitcher: SimPitcher, games_per_team: int, real_games_per_team: int, games_per_day: float, severity: float) -> 'InjuryProfile':
        missed = 0.0
        if real_games_per_team > 0:
            real_g = pitcher.stats.get('G', 0)
            availability = min(1.0, real_g / (_RP_REFERENCE_APPEARANCE_RATE * real_games_per_team))
            confidence = min(1.0, real_g / _ROLE_CONFIDENCE_G_REFERENCE)
            missed = _RP_MISSED_DAMPENER * games_per_team * (1.0 - availability) * confidence
        return cls._build(pitcher.id, missed, games_per_team, games_per_day, severity)

    def roll_injury(self, rng: Random) -> Optional[int]:
        """IL length in days, or None if the roll comes up healthy. All randomness comes from the
        passed-in rng - roster code never imports module-level `random`."""
        if rng.random() >= self.hazard_per_game:
            return None
        draw = rng.random()
        if draw < self.p_short:
            lo, hi = _STINT_SHORT_RANGE
        elif draw < self.p_short + self.p_medium:
            lo, hi = _STINT_MEDIUM_RANGE
        else:
            lo, hi = _STINT_LONG_RANGE
        return rng.randint(lo, hi)


@dataclass
class RosterSelection:
    """Result of splitting a team's card pool into an active 26 and a reserve pool."""

    position_players: list[SimPlayer]
    rotation: list[SimPitcher]
    bullpen: list[SimPitcher]
    position_reserves: list[SimPlayer]
    sp_reserves: list[SimPitcher]
    rp_reserves: list[SimPitcher]
    warnings: list[str] = field(default_factory=list)


@dataclass
class InjuredPlayer:
    """An active internal-list bookkeeping record for a player currently on the IL."""

    player: Union[SimPlayer, SimPitcher]
    injured_on: date
    return_date: date
    group: PositionSlotParent
    rotation_slot_index: Optional[int] = None
    replacement_id: Optional[str] = None
    games_missed: int = 0


def _position_string(player: SimPlayer) -> str:
    return player.primary_position.value if player.positions_list else ""


class Roster:
    """Owns a real-season team's 40-man: the active 26 the sim plays with, the reserve pool, the
    IL, and the transaction log. Builder/tournament teams never get one - `SimTeam.roster` stays
    `None` for them, which is the scope guard every hook checks.
    """

    ACTIVE_POSITION_PLAYERS = 13
    ACTIVE_ROTATION = 5
    ACTIVE_BULLPEN = 8

    def __init__(self, team_name: str, selection: RosterSelection, enable_injuries: bool = False) -> None:
        self.team_name = team_name
        self.position_reserves = selection.position_reserves
        self.sp_reserves = selection.sp_reserves
        self.rp_reserves = selection.rp_reserves
        self.warnings = selection.warnings
        self.injuries_enabled = enable_injuries

        self.profiles: dict[str, InjuryProfile] = {}
        self.injured: dict[str, InjuredPlayer] = {}
        self.transactions: list[Transaction] = []
        self._last_processed_date: Optional[date] = None
        self._games_per_day: float = 1.0

    @property
    def reserves(self) -> list[SimPlayer]:
        return self.position_reserves + self.sp_reserves + self.rp_reserves

    # ------------------------------------------------------------------
    # SELECTION
    # ------------------------------------------------------------------

    @classmethod
    def select(cls, cards: list[ShowdownPlayerCard], card_ids: dict[str, str] = {}, min_pa: int = 100, min_ip_sp: int = 50, min_ip_rp: int = 30, active_size: int = 26, full_size: int = 40, games_per_season: int = 162) -> RosterSelection:
        """Pure roster selection: no mutation, no rng. Called by `SimTeam.from_player_pool`.

        `games_per_season` is the *real* per-team season length (e.g. 162, or shorter for a
        strike/shortened year) - used to scale the reserve sample-size floors so old/short seasons
        don't get rejected wholesale.

        `card_ids` maps each card's own computed `.id` to the id it's actually archived under
        (`card_bot.card_id`, when it has one - see `PlayerLoader.load_season_cards`). Every
        `SimPlayer`/`SimPitcher` built here is given that id explicitly, falling back to the
        card's own id for anything not pre-built/archived, so a real card can always be looked
        back up by a player's id when one exists.
        """

        warnings: list[str] = []
        scale = min(1.0, games_per_season / 162.0) if games_per_season > 0 else 1.0
        min_g_position = max(1, round(RESERVE_MIN_G_POSITION * scale))
        min_pa_position = max(1, round(RESERVE_MIN_PA_POSITION * scale))
        min_g_pitcher = max(1, round(RESERVE_MIN_G_PITCHER * scale))
        min_ip_pitcher = max(1, round(RESERVE_MIN_IP_PITCHER * scale))

        position_cards = sorted([c for c in cards if c.player_sub_type == PlayerSubType.POSITION_PLAYER], key=lambda c: c.points, reverse=True)
        sp_cards = sorted([c for c in cards if c.player_sub_type == PlayerSubType.STARTING_PITCHER], key=lambda c: c.points, reverse=True)
        rp_cards = sorted([c for c in cards if c.player_sub_type == PlayerSubType.RELIEF_PITCHER], key=lambda c: c.points, reverse=True)

        # ---- ROTATION (ACTIVE): TOP N SP, PREFERRED (>= min_ip_sp) TIER SEARCHED FIRST ----
        sp_preferred = [c for c in sp_cards if c.stats.get('IP', 0) >= min_ip_sp]
        sp_fallback = [c for c in sp_cards if c.stats.get('IP', 0) < min_ip_sp]
        sp_ordered = [SimPitcher(card=c, id=card_ids.get(c.id, c.id), position_slot=PositionSlot.SP) for c in (sp_preferred + sp_fallback)]
        rotation = sp_ordered[:cls.ACTIVE_ROTATION]
        sp_remaining = sp_ordered[cls.ACTIVE_ROTATION:]

        # ---- BULLPEN (ACTIVE): TOP N RP ----
        rp_preferred = [c for c in rp_cards if c.stats.get('IP', 0) >= min_ip_rp]
        rp_fallback = [c for c in rp_cards if c.stats.get('IP', 0) < min_ip_rp]
        rp_ordered = [SimPitcher(card=c, id=card_ids.get(c.id, c.id), position_slot=PositionSlot.BP) for c in (rp_preferred + rp_fallback)]
        bullpen = rp_ordered[:cls.ACTIVE_BULLPEN]
        rp_remaining = rp_ordered[cls.ACTIVE_BULLPEN:]

        # ---- POSITION PLAYERS (ACTIVE), COVERAGE-FIRST ----
        position_preferred = [c for c in position_cards if c.stats.get('PA', 0) >= min_pa]
        position_fallback = [c for c in position_cards if c.stats.get('PA', 0) < min_pa]
        position_ordered = [SimPlayer(card=c, id=card_ids.get(c.id, c.id)) for c in (position_preferred + position_fallback)]

        active_position: list[SimPlayer] = []
        selected_ids: set[str] = set()
        defensive_slots = [PositionSlot.CA, PositionSlot._1B, PositionSlot._2B, PositionSlot._3B, PositionSlot.SS, PositionSlot.LF, PositionSlot.CF, PositionSlot.RF]
        for slot in defensive_slots:
            eligible = PositionEligibility.players_for_slot(players=position_ordered, position_slot=slot, excluded_player_ids=list(selected_ids))
            if eligible:
                pick = eligible[0]
                active_position.append(pick)
                selected_ids.add(pick.id)
            else:
                warnings.append(f"no player eligible at {slot.value}")

        # BACKUP CATCHER - NON-NEGOTIABLE, CA.valid_positions IS ONLY [Position.CA]
        ca_eligible = PositionEligibility.players_for_slot(players=position_ordered, position_slot=PositionSlot.CA, excluded_player_ids=list(selected_ids))
        if ca_eligible:
            pick = ca_eligible[0]
            active_position.append(pick)
            selected_ids.add(pick.id)
        else:
            warnings.append("no backup catcher available")

        remaining_pool = [p for p in position_ordered if p.id not in selected_ids]
        while len(active_position) < cls.ACTIVE_POSITION_PLAYERS and remaining_pool:
            pick = remaining_pool.pop(0)
            active_position.append(pick)
            selected_ids.add(pick.id)
        position_remaining = [p for p in position_ordered if p.id not in selected_ids]

        # ---- RESERVES: UP TO full_size - active, SAMPLE-SIZE FLOORS APPLIED ----
        active_count = len(rotation) + len(bullpen) + len(active_position)
        reserve_target = max(full_size - active_count, 0)

        position_candidates = [p for p in position_remaining if p.stats.get('G', 0) >= min_g_position and p.stats.get('PA', 0) >= min_pa_position]
        sp_candidates = [p for p in sp_remaining if p.stats.get('G', 0) >= min_g_pitcher and p.stats.get('IP', 0) >= min_ip_pitcher]
        rp_candidates = [p for p in rp_remaining if p.stats.get('G', 0) >= min_g_pitcher and p.stats.get('IP', 0) >= min_ip_pitcher]

        position_reserves: list[SimPlayer] = []
        sp_reserves: list[SimPitcher] = []
        rp_reserves: list[SimPitcher] = []

        # GUARANTEE MINIMUM CALLUP DEPTH BEFORE FILLING BY POINTS
        if sp_candidates:
            sp_reserves.append(sp_candidates.pop(0))
        for _ in range(2):
            if rp_candidates:
                rp_reserves.append(rp_candidates.pop(0))
        ca_reserve_eligible = PositionEligibility.players_for_slot(players=position_candidates, position_slot=PositionSlot.CA)
        if ca_reserve_eligible:
            pick = ca_reserve_eligible[0]
            position_candidates.remove(pick)
            position_reserves.append(pick)

        guaranteed_count = len(position_reserves) + len(sp_reserves) + len(rp_reserves)
        fill_target = max(reserve_target - guaranteed_count, 0)

        combined = (
            [('pos', p) for p in position_candidates]
            + [('sp', p) for p in sp_candidates]
            + [('rp', p) for p in rp_candidates]
        )
        combined.sort(key=lambda t: t[1].points, reverse=True)
        for kind, player in combined[:fill_target]:
            if kind == 'pos':
                position_reserves.append(player)
            elif kind == 'sp':
                sp_reserves.append(player)
            else:
                rp_reserves.append(player)

        total_roster = active_count + len(position_reserves) + len(sp_reserves) + len(rp_reserves)
        if total_roster < full_size:
            warnings.append(f"{full_size - total_roster} man(s) short of a {full_size}-man roster (pool exhausted after sample-size floors)")

        return RosterSelection(
            position_players=active_position,
            rotation=rotation,
            bullpen=bullpen,
            position_reserves=position_reserves,
            sp_reserves=sp_reserves,
            rp_reserves=rp_reserves,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # INJURY PROFILES
    # ------------------------------------------------------------------

    def build_profiles(self, team: 'SimTeam', games_per_team: int, real_games_per_team: int, games_per_day: float, severity: float, rotation_size: int) -> None:
        """Populate hazard profiles for the whole 40-man (active + reserves)."""
        self._games_per_day = games_per_day
        self.profiles = {}
        for p in team.position_players + self.position_reserves:
            self.profiles[p.id] = InjuryProfile.for_position_player(p, games_per_team, real_games_per_team, games_per_day, severity)
        for p in team.rotation.players + self.sp_reserves:
            self.profiles[p.id] = InjuryProfile.for_starter(p, games_per_team, real_games_per_team, games_per_day, severity, rotation_size)
        for p in team.bullpen.players + self.rp_reserves:
            self.profiles[p.id] = InjuryProfile.for_reliever(p, games_per_team, real_games_per_team, games_per_day, severity)

    # ------------------------------------------------------------------
    # PER-DATE PROCESSING
    # ------------------------------------------------------------------

    def process_date(self, team: 'SimTeam', game_date: date, rng: Random) -> None:
        """Returns first, then injury rolls. Idempotent per calendar date (doubleheader-safe)."""
        if not self.injuries_enabled:
            return
        if game_date == self._last_processed_date:
            return
        self._last_processed_date = game_date

        self.process_returns(team=team, game_date=game_date)

        for player in list(team.position_players):
            self._maybe_injure(team=team, player=player, group=PositionSlotParent.BENCH, game_date=game_date, rng=rng)
        for pitcher in list(team.rotation.players):
            self._maybe_injure(team=team, player=pitcher, group=PositionSlotParent.ROTATION, game_date=game_date, rng=rng)
        for pitcher in list(team.bullpen.players):
            self._maybe_injure(team=team, player=pitcher, group=PositionSlotParent.BULLPEN, game_date=game_date, rng=rng)

    def process_returns(self, team: 'SimTeam', game_date: date) -> None:
        """Activate anyone whose IL stint has ended. Shared with the postseason (rng-free) hook."""
        ready = [inj for inj in self.injured.values() if inj.return_date <= game_date]
        for injured in ready:
            self.activate(team=team, injured=injured, game_date=game_date)

    def _maybe_injure(self, team: 'SimTeam', player: SimPlayer, group: PositionSlotParent, game_date: date, rng: Random) -> None:
        if player.id in self.injured:
            return
        profile = self.profiles.get(player.id)
        # SKIP THE RNG DRAW ENTIRELY WHEN HAZARD IS EXACTLY ZERO (severity=0) SO THAT SETTING
        # SEVERITY TO 0 IS A TRUE NO-OP ON THE SHARED RNG STREAM, NOT JUST ON INJURY OUTCOMES -
        # ANY DRAW HERE WOULD SHIFT EVERY SUBSEQUENT PITCH/SWING ROLL FOR THE REST OF THE SIM.
        if profile is None or profile.hazard_per_game <= 0.0:
            return
        il_days = profile.roll_injury(rng)
        if il_days is None:
            return
        self.place_on_il(team=team, player=player, group=group, game_date=game_date, il_days=il_days)

    # ------------------------------------------------------------------
    # ROSTER MOVES
    # ------------------------------------------------------------------

    def place_on_il(self, team: 'SimTeam', player: SimPlayer, group: PositionSlotParent, game_date: date, il_days: int) -> None:
        return_date = game_date + timedelta(days=il_days)
        rotation_slot_index: Optional[int] = None
        replacement: Optional[SimPlayer] = None

        if group == PositionSlotParent.ROTATION:
            rotation_slot_index = team.rotation.index_for_id(player.id)
            replacement = self._next_sp_replacement()
            if replacement is not None and rotation_slot_index is not None:
                team.rotation.replace_at_index(rotation_slot_index, replacement)
        elif group == PositionSlotParent.BULLPEN:
            team.bullpen.remove_player(player.id)
            replacement = self._next_rp_replacement()
            if replacement is not None:
                team.bullpen.add_player(replacement)
        else:
            team.position_players = [p for p in team.position_players if p.id != player.id]
            team.consecutive_starts.pop(player.id, None)
            replacement = self._next_position_replacement(team=team, injured_player=player)
            if replacement is not None:
                team.position_players.append(replacement)

        games_missed_estimate = round(il_days * self._games_per_day)
        self.injured[player.id] = InjuredPlayer(
            player=player, injured_on=game_date, return_date=return_date, group=group,
            rotation_slot_index=rotation_slot_index,
            replacement_id=replacement.id if replacement is not None else None,
            games_missed=games_missed_estimate,
        )

        self.transactions.append(Transaction(
            date=game_date, team=self.team_name, type=TransactionType.INJURY,
            player_id=player.id, player_name=player.name, position=_position_string(player),
            group=group, il_days=il_days, return_date=return_date, games_missed=games_missed_estimate,
            related_player_id=replacement.id if replacement is not None else None,
            related_player_name=replacement.name if replacement is not None else None,
            detail="" if replacement is not None else "NO REPLACEMENT AVAILABLE",
        ))
        if replacement is not None:
            self.transactions.append(Transaction(
                date=game_date, team=self.team_name, type=TransactionType.CALLUP,
                player_id=replacement.id, player_name=replacement.name, position=_position_string(replacement),
                group=group, related_player_id=player.id, related_player_name=player.name,
            ))

    def _next_sp_replacement(self) -> Optional[SimPitcher]:
        if self.sp_reserves:
            return self.sp_reserves.pop(0)
        if self.rp_reserves:
            pick = self.rp_reserves.pop(0)
            pick.position_slot = PositionSlot.SP
            return pick
        return None

    def _next_rp_replacement(self) -> Optional[SimPitcher]:
        if self.rp_reserves:
            return self.rp_reserves.pop(0)
        if self.sp_reserves:
            pick = self.sp_reserves.pop(0)
            pick.position_slot = PositionSlot.BP
            return pick
        return None

    def _next_position_replacement(self, team: 'SimTeam', injured_player: SimPlayer) -> Optional[SimPlayer]:
        if not self.position_reserves:
            return None
        primary_slot = injured_player.position_slot
        candidates = PositionEligibility.players_for_slot(players=self.position_reserves, position_slot=primary_slot) if primary_slot and primary_slot != PositionSlot.NONE else []
        pick = candidates[0] if candidates else self._best_coverage_reserve(team=team)
        if pick is None:
            return None
        self.position_reserves.remove(pick)
        return pick

    def _best_coverage_reserve(self, team: 'SimTeam') -> Optional[SimPlayer]:
        if not self.position_reserves:
            return None

        def coverage_score(candidate: SimPlayer) -> int:
            hypothetical = team.position_players + [candidate]
            return -len(PositionEligibility.uncovered_slots(hypothetical))

        return sorted(self.position_reserves, key=lambda c: (coverage_score(c), c.points), reverse=True)[0]

    def activate(self, team: 'SimTeam', injured: InjuredPlayer, game_date: date, skip_demote_ids: Optional[set[str]] = None) -> None:
        """Activate a player off the IL, optioning down whoever filled in for him.

        `skip_demote_ids` protects players already committed to an in-progress lineup build
        (see `emergency_activate_earliest`) - if the fill-in is protected, the returning player is
        added without demoting anyone, temporarily exceeding the active roster size. A legal
        lineup beats a legal roster.
        """
        skip_demote_ids = skip_demote_ids or set()
        del self.injured[injured.player.id]
        replacement: Optional[SimPlayer] = None

        if injured.group == PositionSlotParent.ROTATION and injured.rotation_slot_index is not None:
            replacement = team.rotation.replace_at_index(injured.rotation_slot_index, injured.player)
            if replacement is not None:
                self._option_pitcher(replacement, PositionSlot.SP)
        elif injured.group == PositionSlotParent.BULLPEN:
            if injured.replacement_id:
                replacement = team.bullpen.remove_player(injured.replacement_id)
            team.bullpen.add_player(injured.player)
            if replacement is not None:
                self._option_pitcher(replacement, PositionSlot.BP)
        else:
            if injured.replacement_id and injured.replacement_id not in skip_demote_ids:
                replacement = next((p for p in team.position_players if p.id == injured.replacement_id), None)
                if replacement is not None:
                    team.position_players = [p for p in team.position_players if p.id != replacement.id]
            team.position_players.append(injured.player)
            if replacement is not None:
                self.position_reserves.append(replacement)

        self.transactions.append(Transaction(
            date=game_date, team=self.team_name, type=TransactionType.ACTIVATION,
            player_id=injured.player.id, player_name=injured.player.name, position=_position_string(injured.player),
            group=injured.group, games_missed=injured.games_missed,
            related_player_id=replacement.id if replacement is not None else None,
            related_player_name=replacement.name if replacement is not None else None,
        ))
        if replacement is not None:
            self.transactions.append(Transaction(
                date=game_date, team=self.team_name, type=TransactionType.OPTION,
                player_id=replacement.id, player_name=replacement.name, position=_position_string(replacement),
                group=injured.group, related_player_id=injured.player.id, related_player_name=injured.player.name,
            ))

    def _option_pitcher(self, pitcher: SimPitcher, slot: PositionSlot) -> None:
        pitcher.position_slot = slot
        if slot == PositionSlot.SP:
            self.sp_reserves.append(pitcher)
        else:
            self.rp_reserves.append(pitcher)

    def emergency_activate_earliest(self, team: 'SimTeam', game_date: date, protected_ids: set[str]) -> Optional[SimPlayer]:
        """Force-activate the injured position player closest to returning, ahead of schedule.

        Last-resort fallback for a thin team whose active roster AND reserve pool are both
        exhausted mid-season (possible with `enable_injuries` on a full 2400+ game season and a
        team that started under-full). A legal lineup beats a legal IL stint, so this is tried
        before the lineup-fill code gives up and raises.

        `protected_ids` are players already committed to this game's in-progress lineup - the
        candidate whose fill-in isn't one of them is preferred, so activating doesn't bump someone
        who was just placed in an earlier slot this same build.
        """
        candidates = sorted(
            (inj for inj in self.injured.values() if inj.group == PositionSlotParent.BENCH),
            key=lambda inj: inj.return_date,
        )
        if not candidates:
            return None
        earliest = next((inj for inj in candidates if inj.replacement_id not in protected_ids), candidates[0])
        self.activate(team=team, injured=earliest, game_date=game_date, skip_demote_ids=protected_ids)
        return earliest.player

    def emergency_callup(self, team: 'SimTeam', position_slot: PositionSlot, game_date: date, protected_ids: set[str]) -> Optional[SimPlayer]:
        """Lineup-fill safety valve: promote a reserve eligible for `position_slot`, optioning
        down the lowest-points active player not already committed to this game's lineup
        (`protected_ids`). If the active roster is already at its floor, promote anyway - a legal
        lineup beats a legal roster.
        """
        eligible = PositionEligibility.players_for_slot(players=self.position_reserves, position_slot=position_slot)
        if not eligible:
            return None
        pick = eligible[0]
        self.position_reserves.remove(pick)
        team.position_players.append(pick)

        optionable = [p for p in team.position_players if p.id != pick.id and p.id not in protected_ids]
        detail = "ROSTER OVER LIMIT"
        if optionable:
            demoted = sorted(optionable, key=lambda p: p.points)[0]
            team.position_players = [p for p in team.position_players if p.id != demoted.id]
            self.position_reserves.append(demoted)
            detail = ""
            self.transactions.append(Transaction(
                date=game_date, team=self.team_name, type=TransactionType.OPTION,
                player_id=demoted.id, player_name=demoted.name, position=_position_string(demoted),
                group=PositionSlotParent.BENCH, related_player_id=pick.id, related_player_name=pick.name,
            ))

        self.transactions.append(Transaction(
            date=game_date, team=self.team_name, type=TransactionType.CALLUP,
            player_id=pick.id, player_name=pick.name, position=_position_string(pick),
            group=PositionSlotParent.BENCH, detail=detail,
        ))
        return pick
