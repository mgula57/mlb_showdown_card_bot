from typing import Optional

from .roster_to_team_converter import RosterToTeamConverter
from .team import TeamSource
from ...database.postgres_db import ExploreDataRecord, PostgresDB
from ...shared.player_position import Position


class EraRosterDrafter(RosterToTeamConverter):
    """Compose an Era Roster (all-time, or a single decade -- see RosterEraRegistry) from every
    qualified season a franchise's players recorded within the given era, ranked strictly by
    Showdown points -- with non-qualified fallback fill for any slot qualified seasons alone
    can't cover (see below).

    "Qualified" is the real batting-title/ERA-title standard -- 3.1 PA or ~1.0 IP per team game
    scheduled that year -- computed live here rather than persisted as a card_bot column, so it
    can be tuned without a full-table backfill. PostgresDB.fetch_era_candidate_pool only
    pre-filters cards down to non-small-sample (a much lower "played enough to show up" bar);
    _filter_qualified below applies the real standard on top of that pool. Which years are in
    play at all (all-time vs. a single decade) is entirely a property of the candidate pool
    passed in -- this class has no era-awareness of its own.

    A single decade is a narrow window (10 years) on one franchise -- it's common for a
    rebuilding/expansion team to have fewer than 5 pitchers who both started (by the card's own
    SP tag) and cleared the real ERA-title IP bar in their best season for that team, or no
    every-day player at a given field position at all. Rather than leave those roster slots
    empty, non-qualified (but still non-small-sample) candidates stay in the pool as fallback
    fill: qualified players always win a slot over them (see _qualified_rank / the sort-key
    overrides below), but an unfilled rotation/lineup slot still gets the best available
    candidate instead of nothing.

    Real playing time (games played/started, saves) isn't comparable across players pooled from
    different years, so this replaces the base class's playing-time filter and sort keys with a
    single "most points" comparator, and otherwise reuses RosterToTeamConverter's lineup
    assignment / rotation composition unchanged. Bullpen and bench composition are overridden
    too (see _bullpen_pool / _compose_depth below): a career-bests pool makes "leftover starter
    becomes a long reliever" and "best available regardless of type" meaningless in a way they
    aren't for a real single season, so those need their own rules here.
    """

    ERA_ROSTER_SIZE = 26  # no season to key a historical roster-size cap off of
    BULLPEN_MIN_SIZE = 7  # including the closer
    BENCH_MIN_SIZE = 5

    # A card's `ip` rating (distinct from `real_ip`, that season's real innings total) is how
    # many innings that pitcher can go per appearance in the simulated game -- real bullpens are
    # overwhelmingly one-inning arms, so a bullpen stacked with multi-inning (ip > 1) firemen
    # would be neither realistic nor a fair sim opponent. At most this many such cards are
    # eligible at all; the era's remaining one-inning relievers are deep enough at the points
    # level this pool draws from to fill the rest of the bullpen regardless.
    MAX_MULTI_INNING_RELIEVERS = 2

    # The bench must cover at least one backup at each of these position groups (scarcest
    # group filled first -- see _select_bench), so a career-bests bench can't end up all corner
    # bats with no true backup catcher, infielder, or outfielder on it.
    BENCH_QUOTA_POSITIONS = {
        'C': {Position.CA},
        'IF': {Position._1B, Position._2B, Position._3B, Position.SS, Position.IF},
        'OF': {Position.LF, Position.CF, Position.RF, Position.OF, Position.LFRF},
    }

    # The real batting-title standard is 3.1 PA per team game scheduled (502 over a 162-game
    # season). True ERA-title IP (1.0/team-game, ~162 IP) is unrealistic for a reliever's
    # workload, so the pitching bar is split SP/RP using the same ratios
    # core/simulation/summary.py already settled on for its League Leaders board: ~120 IP (2x a
    # full-season floor) for starters, ~45 IP (1.5x) for relievers, both over 162 games.
    _QUALIFIED_PA_RATIO = 502.0 / 162.0
    _QUALIFIED_IP_SP_RATIO = 120.0 / 162.0
    _QUALIFIED_IP_RP_RATIO = 45.0 / 162.0

    # Approximate team games scheduled per year, used to prorate the ratios above for
    # historical/strike-shortened seasons. Not team-specific -- a handful of early-1900s rainout
    # makeups aside, every team in a season plays the same schedule length -- so a year-keyed
    # approximation is accurate enough for a "qualified" cutoff. Anything not listed here falls
    # back to the 140-/154-/162-game eras in _team_games_scheduled.
    _SHORT_SEASON_GAMES = {1918: 126, 1919: 140, 1972: 155, 1981: 107, 1994: 115, 1995: 144, 2020: 60}

    def __init__(
        self,
        cards: list[ExploreDataRecord],
        team_id: str,
        name: str,
        abbreviation: str,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        source: TeamSource = TeamSource.MLB,
    ) -> None:
        # Each player's single best QUALIFYING season wins their spot in the pool. A player with
        # no qualifying season at all still gets one shot at a spot -- their single best season
        # overall (still non-small-sample, per the candidate pool's own floor) -- but only as
        # fallback fill; see _qualified_rank and the sort-key overrides below.
        qualified_best = self._best_season_per_player(self._filter_qualified(cards))
        qualified_keys = {(c.mlb_id, c.player_type) for c in qualified_best}
        fallback_only = [c for c in self._best_season_per_player(cards) if (c.mlb_id, c.player_type) not in qualified_keys]
        self._qualified_card_ids = {c.card_id for c in qualified_best}
        cards = self._cap_multi_inning_relievers(qualified_best + fallback_only)
        super().__init__(
            cards=cards,
            team_id=team_id,
            name=name,
            abbreviation=abbreviation,
            primary_color=primary_color,
            secondary_color=secondary_color,
            season=None,
            source=source,
        )

    @classmethod
    def _team_games_scheduled(cls, year: int) -> int:
        if year in cls._SHORT_SEASON_GAMES:
            return cls._SHORT_SEASON_GAMES[year]
        if year <= 1903:
            return 140
        if year <= 1961:
            return 154
        return 162

    @classmethod
    def _is_qualified(cls, card: ExploreDataRecord) -> bool:
        games = cls._team_games_scheduled(card.year)
        positions = card.positions_list or []
        if Position.SP in positions:
            return (card.real_ip or 0) >= cls._QUALIFIED_IP_SP_RATIO * games
        if Position.RP in positions or Position.CL in positions:
            return (card.real_ip or 0) >= cls._QUALIFIED_IP_RP_RATIO * games
        return (card.pa or 0) >= cls._QUALIFIED_PA_RATIO * games

    @classmethod
    def _filter_qualified(cls, cards: list[ExploreDataRecord]) -> list[ExploreDataRecord]:
        return [c for c in cards if cls._is_qualified(c)]

    @staticmethod
    def _best_season_per_player(cards: list[ExploreDataRecord]) -> list[ExploreDataRecord]:
        """Each player's single highest-points qualifying season, keyed by (mlb_id, player_type)
        so a two-way player keeps independent hitting and pitching candidacy, and a player's
        lesser seasons never compete against their own best one for a roster spot."""
        best: dict[tuple, ExploreDataRecord] = {}
        for c in cards:
            if c.mlb_id is None or c.card_id is None:
                continue
            key = (c.mlb_id, c.player_type)
            if key not in best or (c.points or 0) > (best[key].points or 0):
                best[key] = c
        return list(best.values())

    @classmethod
    def _cap_multi_inning_relievers(cls, cards: list[ExploreDataRecord]) -> list[ExploreDataRecord]:
        """Drop all but the best MAX_MULTI_INNING_RELIEVERS relief/closer cards whose `ip`
        rating is above 1, so the bullpen can never end up stacked with multi-inning arms.
        Starters are untouched even though some also carry an RP/CL tag on rare dual-role
        cards -- this only targets cards that would actually compete for a bullpen slot
        (see _bullpen_pool, which excludes starters the same way)."""
        def is_bullpen_eligible(c: ExploreDataRecord) -> bool:
            positions = c.positions_list or []
            return Position.SP not in positions and (Position.RP in positions or Position.CL in positions)

        multi_inning = sorted(
            (c for c in cards if is_bullpen_eligible(c) and (c.ip or 1) > 1),
            key=lambda c: c.points or 0, reverse=True,
        )
        dropped_ids = {c.card_id for c in multi_inning[cls.MAX_MULTI_INNING_RELIEVERS:]}
        return [c for c in cards if c.card_id not in dropped_ids]

    @classmethod
    def _filter_by_playing_time(cls, cards: list[ExploreDataRecord], protected_ids: set[str]) -> list[ExploreDataRecord]:
        # Already scoped to one team + deduped to each player's single best season (qualified-
        # first, fallback otherwise -- see __init__) -- real playing time isn't comparable across
        # pooled seasons, so no further cameo filtering happens here.
        return cards

    def _qualified_rank(self, card: ExploreDataRecord) -> int:
        """1 for a card drawn from a player's real qualifying season, 0 for fallback fill --
        every sort key below ranks this first so fallback candidates only ever win a slot that no
        qualified candidate is competing for."""
        return 1 if card.card_id in self._qualified_card_ids else 0

    def _by_games_played(self, card: ExploreDataRecord) -> tuple:
        return (self._qualified_rank(card), card.points or 0)

    def _by_games_started(self, card: ExploreDataRecord) -> tuple:
        return (self._qualified_rank(card), card.points or 0)

    def _by_saves(self, card: ExploreDataRecord) -> tuple:
        # No real saves data comparable across pooled seasons; prefer a card the bot itself
        # tagged as a closer that year, then fall back to points among all bullpen candidates.
        return (self._qualified_rank(card), 1 if Position.CL in (card.positions_list or []) else 0, card.points or 0)

    @staticmethod
    def _max_roster_size(season: Optional[int]) -> Optional[int]:
        return EraRosterDrafter.ERA_ROSTER_SIZE

    @staticmethod
    def _bullpen_pool(
        starters: list[ExploreDataRecord], relievers: list[ExploreDataRecord], rotation_ids: set[str],
    ) -> list[ExploreDataRecord]:
        # Unlike a real season, a starter who didn't make the rotation isn't "converted" to a
        # reliever here -- an ace's off year isn't a legitimate relief season, so that player is
        # simply left off the roster instead of occupying a bullpen slot he never actually filled.
        return [c for c in relievers if c.card_id not in rotation_ids]

    def _select_bench(self, bench_pool: list[ExploreDataRecord], bench_size: int) -> list[ExploreDataRecord]:
        """Pick `bench_size` bench bats from `bench_pool` (already sorted best-first by points),
        guaranteeing at least one who can back up each of BENCH_QUOTA_POSITIONS -- scarcest
        group filled first, same two-pass idea as _assign_lineup, so a versatile player isn't
        "wasted" on a group with plenty of other candidates. Remaining slots go to the next-best
        bats by points regardless of position."""
        if bench_size <= 0:
            return []
        used_ids: set[str] = set()
        selected: list[ExploreDataRecord] = []
        quota_pools = {
            label: [c for c in bench_pool if any(p in (c.positions_list or []) for p in positions)]
            for label, positions in self.BENCH_QUOTA_POSITIONS.items()
        }
        for label in sorted(quota_pools, key=lambda l: len(quota_pools[l])):
            if len(selected) >= bench_size:
                break
            candidates = [c for c in quota_pools[label] if c.card_id not in used_ids]
            if not candidates:
                continue
            picked = candidates[0]
            selected.append(picked)
            used_ids.add(picked.card_id)
        for c in bench_pool:
            if len(selected) >= bench_size:
                break
            if c.card_id not in used_ids:
                selected.append(c)
                used_ids.add(c.card_id)
        return selected

    def _compose_depth(
        self, bench: list[ExploreDataRecord], bullpen: list[ExploreDataRecord], closer: Optional[ExploreDataRecord],
        core_count: int, max_roster_size: int,
    ) -> tuple[list[ExploreDataRecord], list[ExploreDataRecord]]:
        """Fill the remaining roster slots (beyond lineup + rotation + closer) with a guaranteed
        floor of BULLPEN_MIN_SIZE relievers (closer included) and BENCH_MIN_SIZE bench bats
        (see _select_bench for the bench's own backup-catcher/infielder/outfielder quota).

        The base class pools bench and bullpen together and keeps whoever has the most points --
        fine for a real season, but a career-bests pool starves the bench entirely that way,
        since a non-rotation ace's points usually beat a great bench bat's. `bench` and `bullpen`
        arrive already sorted best-first (by points, via this class's own _by_games_played), and
        any slots left over after both floors go to whichever pool's next-best remaining
        candidate has more points -- bench stays hitters only and bullpen stays true relievers
        only either way.
        """
        remaining = max(0, max_roster_size - core_count)
        bullpen_rest = [c for c in bullpen if c is not closer]

        bullpen_min = max(0, min(self.BULLPEN_MIN_SIZE - (1 if closer else 0), len(bullpen_rest), remaining))
        bench_min = min(self.BENCH_MIN_SIZE, len(bench), max(0, remaining - bullpen_min))

        guaranteed_bullpen = bullpen_rest[:bullpen_min]
        guaranteed_bench = self._select_bench(bench, bench_min)
        guaranteed_bench_ids = {c.card_id for c in guaranteed_bench}

        extra = remaining - bullpen_min - bench_min
        if extra > 0:
            leftover = (
                [('bullpen', c) for c in bullpen_rest[bullpen_min:]]
                + [('bench', c) for c in bench if c.card_id not in guaranteed_bench_ids]
            )
            leftover.sort(key=lambda pair: pair[1].points or 0, reverse=True)
            for kind, c in leftover[:extra]:
                (guaranteed_bullpen if kind == 'bullpen' else guaranteed_bench).append(c)

        bullpen_out = ([closer] if closer else []) + guaranteed_bullpen
        return guaranteed_bench, bullpen_out

    def build_api_dict(self) -> dict:
        # self.cards (post-dedup) holds every distinct player who ever qualified within this
        # era for this team -- far more than the ~26 who make the final roster. Sum only the
        # actually-rostered cards, bench-discounted, matching how the base class's own
        # build_api_dict / StoredRosterToTeamConverter's total_points are computed.
        team = self.build()
        data = team.model_dump(mode='json')
        points_by_card_id = {c.card_id: (c.points or 0) for c in self.cards}
        data['total_points'] = round(sum(
            points_by_card_id.get(slot.card_id, 0) * (PostgresDB._HISTORICAL_BENCH_PTS_MULTIPLIER if slot.roster_position == 'BE' else 1)
            for slot in team.roster
        ))
        return data
