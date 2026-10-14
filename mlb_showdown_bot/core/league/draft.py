"""League draft: snake order, roster fit, the bot drafter, and the orchestrator that records picks.

A league draft is a snake draft of `roster_size` rounds. Every pick lands straight on the
member's `user_teams` roster in a concrete roster position, so the team is a normal team-builder
team the moment the draft ends. The server is the only judge of whose turn it is and whether a
card fits: clients just poll the board and submit a card id.
"""

import random
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..card.team_builder.autofill import OFFENSE_POSITIONS
from ..card.team_builder.team import ROTATION_ROLES
from ..shared.player_position import Position, PositionSlot
from .settings import LeagueSettings


class DraftError(Exception):
    """A pick the rules don't allow. The message is safe to show the drafter."""


class DraftConflict(Exception):
    """The board moved between reading it and writing the pick - someone else picked first.
    The client should re-read the board and try again."""


# ---------------------------------------------------------------------------
# MARK: - ORDER
# ---------------------------------------------------------------------------

class SnakeOrder:
    """Pick order for a snake draft: slot 0 → T-1 in odd rounds, T-1 → 0 in even rounds.
    Picks are 1-based, slots 0-based."""

    def __init__(self, team_count: int, rounds: int) -> None:
        self.team_count = team_count
        self.rounds = rounds

    @property
    def total_picks(self) -> int:
        return self.team_count * self.rounds

    def round_for_pick(self, overall_pick: int) -> int:
        return (overall_pick - 1) // self.team_count + 1

    def slot_for_pick(self, overall_pick: int) -> int:
        index = (overall_pick - 1) % self.team_count
        return index if self.round_for_pick(overall_pick) % 2 == 1 else self.team_count - 1 - index

    def upcoming(self, from_pick: int, count: int) -> list[tuple[int, int]]:
        """`(overall_pick, slot)` for the next `count` picks starting at `from_pick`."""
        last = min(self.total_picks, from_pick + count - 1)
        return [(pick, self.slot_for_pick(pick)) for pick in range(from_pick, last + 1)]


# ---------------------------------------------------------------------------
# MARK: - CARDS AND ROSTERS
# ---------------------------------------------------------------------------

# Scarcest defensive spots first, so a card that can play several fills the one that's
# hardest to cover. DH comes after every field spot.
_FIELD_FILL_ORDER = ['C', 'SS', '2B', 'CF', '3B', 'LF', 'RF', '1B']
_BULLPEN_POSITIONS = ('RP', 'CL')


# Card positions that can man each lineup spot - the same rule the sim uses.
_FIELD_VALID_POSITIONS: dict[str, frozenset[Position]] = {
    pos: frozenset(PositionSlot('CA' if pos == 'C' else pos).valid_positions) for pos in OFFENSE_POSITIONS
}


@dataclass
class DraftCard:
    """The fields the draft reads off a release card (a `_LEAGUE_DRAFT_CARD_COLUMNS` row)."""

    release_card_id: str
    source_card_id: Optional[str]
    name: str
    points: float
    is_pitcher: bool
    positions: set[Position]
    is_small_sample: bool = False

    @classmethod
    def from_row(cls, row: dict) -> 'DraftCard':
        positions: set[Position] = set()
        for key in (row.get('positions_and_defense') or {}):
            try:
                positions.add(Position(key))
            except ValueError:
                continue
        return cls(
            release_card_id=str(row['release_card_id']),
            source_card_id=row.get('source_card_id'),
            name=row.get('name') or '',
            points=float(row.get('points') or 0),
            is_pitcher=(row.get('player_type') or '').upper() == 'PITCHER',
            positions=positions,
            is_small_sample=bool(row.get('is_small_sample_size')),
        )

    @property
    def is_starter(self) -> bool:
        return self.is_pitcher and Position.SP in self.positions

    def can_play(self, field_position: str) -> bool:
        """Whether this hitter can man a lineup spot."""
        return not self.is_pitcher and bool(self.positions & _FIELD_VALID_POSITIONS[field_position])


@dataclass
class DraftRoster:
    """One team's roster as the draft sees it: which roster positions are filled.

    Hard needs are the 9 lineup spots, the rotation, and the bench/bullpen minimums. Every pick
    either fills one, or (only while there are more picks left than needs) adds depth on the
    bench or in the bullpen."""

    settings: LeagueSettings
    positions: list[str] = field(default_factory=list)
    points: float = 0

    @property
    def picks_left(self) -> int:
        return self.settings.roster_size - len(self.positions)

    @property
    def open_field_positions(self) -> list[str]:
        return [pos for pos in OFFENSE_POSITIONS if pos not in self.positions]

    @property
    def open_rotation_roles(self) -> list[str]:
        return [role for role in ROTATION_ROLES[:self.settings.num_starters] if role not in self.positions]

    @property
    def bullpen_count(self) -> int:
        return sum(1 for pos in self.positions if pos in _BULLPEN_POSITIONS)

    @property
    def bench_count(self) -> int:
        return self.positions.count('BE')

    @property
    def hard_needs(self) -> int:
        return (
            len(self.open_field_positions)
            + len(self.open_rotation_roles)
            + max(0, self.settings.min_bullpen - self.bullpen_count)
            + max(0, self.settings.min_bench - self.bench_count)
        )

    @property
    def slack(self) -> int:
        """Picks left beyond what the hard needs still require."""
        return self.picks_left - self.hard_needs

    def _need_and_depth_slot(self, card: DraftCard) -> tuple[Optional[str], Optional[str]]:
        """The roster position `card` would fill as a hard need (or None), and the depth position
        it could take instead once needs are covered (or None if it has none)."""
        if card.is_pitcher:
            if card.is_starter:
                # Starters only ever fill rotation roles - the bullpen is relievers and closers.
                open_roles = self.open_rotation_roles
                return (open_roles[0] if open_roles else None), None
            return ('RP' if self.bullpen_count < self.settings.min_bullpen else None), 'RP'
        open_field = self.open_field_positions
        for pos in _FIELD_FILL_ORDER:
            if pos in open_field and card.can_play(pos):
                return pos, 'BE'
        if 'DH' in open_field:
            return 'DH', 'BE'
        return ('BE' if self.bench_count < self.settings.min_bench else None), 'BE'

    def slot_for(self, card: DraftCard) -> Optional[str]:
        """Roster position `card` takes if drafted now, or None if it doesn't fit."""
        if self.picks_left <= 0:
            return None
        need, depth = self._need_and_depth_slot(card)
        if need:
            return need
        return depth if depth and self.slack > 0 else None

    def fills_need(self, card: DraftCard) -> bool:
        return self._need_and_depth_slot(card)[0] is not None

    def fallback_slot(self, card: DraftCard) -> Optional[str]:
        """Where `card` goes when nothing left in the pool fits this roster (e.g. no catchers
        remain): the first open spot of its kind, played out of position. Keeps a thin pool
        from deadlocking the draft."""
        if self.picks_left <= 0:
            return None
        if card.is_pitcher:
            open_roles = self.open_rotation_roles
            return open_roles[0] if open_roles else 'RP'
        open_field = self.open_field_positions
        return open_field[0] if open_field else 'BE'

    def with_pick(self, slot: str, points: float) -> 'DraftRoster':
        """This roster as it would stand after drafting a card into `slot`."""
        return DraftRoster(settings=self.settings, positions=self.positions + [slot], points=self.points + points)

    def cheapest_fill(self, pool: list['DraftCard'], exclude_id: Optional[str] = None, competitors: int = 0) -> tuple[float, set[str]]:
        """Lowest points it would take to fill out the roster from `pool` - every remaining hard
        need (greedy, scarcest lineup spot first) plus the depth picks after them - and the card
        ids that fill uses. A need nothing left in
        the pool can fill costs 0 - it'll be filled out of position.

        `competitors` > 0 assumes that many other teams take the cheapest fitting card ahead of
        this one for each need, so the estimate holds up while rival teams drain the bargains."""
        available = sorted((c for c in pool if c.release_card_id != exclude_id), key=lambda c: c.points)
        needs: list[Callable[[DraftCard], bool]] = [
            (lambda c, pos=pos: c.can_play(pos)) for pos in _FIELD_FILL_ORDER + ['DH'] if pos in self.open_field_positions
        ]
        needs += [lambda c: c.is_starter] * len(self.open_rotation_roles)
        needs += [lambda c: c.is_pitcher and not c.is_starter] * max(0, self.settings.min_bullpen - self.bullpen_count)
        needs += [lambda c: not c.is_pitcher] * max(0, self.settings.min_bench - self.bench_count)
        # Every roster still drafts all the way to roster_size, so the depth picks past the hard
        # needs cost points too (bench or bullpen - anything but a starter)
        needs += [lambda c: not c.is_starter] * max(0, self.slack)

        used: set[str] = set()
        taken_by_others: set[str] = set()
        cost = 0.0
        for matches in needs:
            fitting = (c for c in available if c.release_card_id not in used and c.release_card_id not in taken_by_others and matches(c))
            for _ in range(competitors):
                rival_pick = next(fitting, None)
                if rival_pick is not None:
                    taken_by_others.add(rival_pick.release_card_id)
            card = next(fitting, None)
            if card is not None:
                used.add(card.release_card_id)
                cost += card.points
        return cost, used

    def rejection_reason(self, card: DraftCard) -> str:
        if self.picks_left <= 0:
            return "Your roster is full."
        if card.is_starter:
            return "Your rotation is full."
        if self.slack <= 0:
            return "Your remaining picks are needed for open lineup, rotation, bench or bullpen spots."
        return "That card doesn't fit any open spot on your roster."


# ---------------------------------------------------------------------------
# MARK: - BOT
# ---------------------------------------------------------------------------

class LeagueDraftBot:
    """Picks for bot seats, and for a human seat the commissioner auto-picks for.

    Best available by points, nudged by need: a pick that only adds depth is discounted, a
    small-sample card is discounted unless it's headed for the bench, and a lineup spot few
    remaining cards can play gets a boost. The final choice is a weighted draw from the top few
    so bots don't all draft identically."""

    DEPTH_DISCOUNT = 0.6
    BENCH_DISCOUNT = 0.75
    SMALL_SAMPLE_DISCOUNT = 0.85
    SCARCITY_BOOST = 1.15
    TOP_CHOICE_WEIGHTS = (0.6, 0.25, 0.15)

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def choose(self, roster: DraftRoster, pool: list[DraftCard], team_count: int, pts_cap: Optional[int] = None) -> Optional[tuple[DraftCard, str]]:
        """The `(card, roster_position)` to draft, or None if the pool is empty."""
        # Lineup spots so few remaining cards can play that every team can't get one
        scarce = {pos for pos in roster.open_field_positions if pos != 'DH' and sum(1 for c in pool if c.can_play(pos)) <= team_count}
        reserve_cache: dict[str, tuple[float, set[str]]] = {}
        scored: list[tuple[float, DraftCard, str]] = []
        for card in pool:
            slot = roster.slot_for(card)
            if slot is None or not LeagueDraft.fits_points_cap(roster, card, slot, pool, pts_cap, reserve_cache, competitors=team_count - 1):
                continue
            scored.append((self._score(roster, card, slot, scarce), card, slot))

        if not scored:
            # Nothing fits (a thin pool, or nothing affordable under the cap): take a card out of
            # position - the best one, or the cheapest when a cap is what's in the way.
            fallbacks = [(card, roster.slot_for(card) or roster.fallback_slot(card)) for card in pool]
            fallbacks = [(card, slot) for card, slot in fallbacks if slot is not None]
            if not fallbacks:
                return None
            return min(fallbacks, key=lambda entry: entry[0].points) if pts_cap else max(fallbacks, key=lambda entry: entry[0].points)

        scored.sort(key=lambda entry: entry[0], reverse=True)
        top = scored[:len(self.TOP_CHOICE_WEIGHTS)]
        _, card, slot = self.rng.choices(top, weights=self.TOP_CHOICE_WEIGHTS[:len(top)])[0]
        return card, slot

    def _score(self, roster: DraftRoster, card: DraftCard, slot: str, scarce: set[str]) -> float:
        score = card.points
        if not roster.fills_need(card):
            score *= self.DEPTH_DISCOUNT
        if slot == 'BE':
            score *= self.BENCH_DISCOUNT
        elif card.is_small_sample:
            score *= self.SMALL_SAMPLE_DISCOUNT
        if slot in scarce:
            score *= self.SCARCITY_BOOST
        return score


# ---------------------------------------------------------------------------
# MARK: - ORCHESTRATOR
# ---------------------------------------------------------------------------

@dataclass
class DraftBoard:
    """The draft as read from the DB at one moment."""

    order: SnakeOrder
    teams: list[dict]                  # league_team rows, in draft-slot order
    picks: list[dict]                  # league_draft_pick rows, in pick order
    rosters: dict[str, DraftRoster]    # member_id -> roster

    @property
    def next_pick(self) -> int:
        return len(self.picks) + 1

    @property
    def is_complete(self) -> bool:
        return len(self.picks) >= self.order.total_picks

    @property
    def on_the_clock(self) -> Optional[dict]:
        if self.is_complete:
            return None
        return self.teams[self.order.slot_for_pick(self.next_pick)]

    def drafted(self, card: DraftCard) -> bool:
        return any(
            pick['release_card_id'] == card.release_card_id
            or (card.source_card_id and pick.get('source_card_id') == card.source_card_id)
            for pick in self.picks
        )


class LeagueDraft:
    """Runs one league season's draft against the DB: starting it, validating and recording
    picks, and making bot picks until a human is on the clock."""

    def __init__(self, db, league: dict, season: dict) -> None:
        self.db = db
        self.league = league
        self.season = season
        self.settings = LeagueSettings(**(league.get('settings') or {}))

    # MARK: Start

    @staticmethod
    def start(db, league: dict, members: list[dict], season_number: int, manual_order: Optional[list[str]] = None) -> str:
        """Create season `season_number` in the `drafting` state: set each member's draft slot
        (random, or `manual_order` as a list of member ids) and give each an empty league team.
        Returns the season id."""
        settings = LeagueSettings(**(league.get('settings') or {}))
        if len(members) < 2:
            raise DraftError("A league needs at least 2 teams to draft.")
        if len(members) > settings.team_count:
            raise DraftError(f"This league is set to {settings.team_count} teams but has {len(members)} members.")

        seed = random.SystemRandom().getrandbits(62)
        member_ids = [m['member_id'] for m in members]
        if manual_order:
            if sorted(manual_order) != sorted(member_ids):
                raise DraftError("The draft order must list every member exactly once.")
            ordered = list(manual_order)
        else:
            ordered = member_ids[:]
            random.Random(seed).shuffle(ordered)

        pool = [DraftCard.from_row(row) for row in db.fetch_league_card_pool(None, league['edition_ids'])]
        if len(pool) < settings.roster_size * len(members):
            raise DraftError(
                f"This league's editions have {len(pool)} cards, but {len(members)} teams of {settings.roster_size} "
                f"need {settings.roster_size * len(members)}. Add editions or shrink the rosters."
            )
        if settings.pts_cap:
            minimum = LeagueDraft.minimum_points_per_team(pool, settings, len(members))
            if minimum > settings.pts_cap:
                raise DraftError(
                    f"The {settings.pts_cap}-point cap is too low for this card pool: {len(members)} full rosters "
                    f"need at least {round(minimum)} points each. Raise the cap or add editions."
                )

        members_by_id = {m['member_id']: m for m in members}
        teams = {
            member_id: {
                'user_id': members_by_id[member_id].get('user_id'),
                'name': f"{members_by_id[member_id]['display_name']}'s Team",
                'abbreviation': LeagueDraft._abbreviation(members_by_id[member_id]['display_name']),
                'showdown_set': league['showdown_set'],
                'pts_limit': settings.pts_cap,
                'roster_size': settings.roster_size,
                'min_bench': settings.min_bench,
                'min_bullpen': settings.min_bullpen,
                'num_starters': settings.num_starters,
            }
            for member_id in ordered
        }
        season_id = db.start_league_season(
            league_id=league['league_id'],
            season_number=season_number,
            status='drafting',
            draft_slots={member_id: slot for slot, member_id in enumerate(ordered)},
            teams=teams,
            seed=seed,
        )
        if season_id is None:
            raise DraftConflict(f"Season {season_number} has already started.")
        return season_id

    @staticmethod
    def minimum_points_per_team(pool: list[DraftCard], settings: LeagueSettings, team_count: int) -> float:
        """Rough floor on what the priciest of `team_count` rosters costs if every team drafts as
        cheaply as possible: teams fill one after another from what's left, so later teams pay
        for the bargains earlier teams took."""
        remaining = list(pool)
        worst = 0.0
        for _ in range(team_count):
            cost, used = DraftRoster(settings=settings).cheapest_fill(remaining)
            worst = max(worst, cost)
            remaining = [card for card in remaining if card.release_card_id not in used]
        return worst

    @staticmethod
    def _abbreviation(display_name: str) -> str:
        letters = ''.join(ch for ch in display_name.upper() if ch.isalnum())
        return letters[:3] if len(letters) >= 2 else 'TM'

    # MARK: Board

    def board(self) -> DraftBoard:
        season_id = self.season['season_id']
        teams = self.db.get_league_teams(season_id)
        rosters = {team['member_id']: DraftRoster(settings=self.settings) for team in teams}
        for slot in self.db.get_league_roster_slots(season_id):
            roster = rosters.get(slot['member_id'])
            if roster is not None:
                roster.positions.append(slot['roster_position'])
                roster.points += slot.get('points') or 0
        return DraftBoard(
            order=SnakeOrder(len(teams), self.settings.roster_size),
            teams=teams,
            picks=self.db.get_league_draft_picks(season_id),
            rosters=rosters,
        )

    def state(self, viewer_member_id: Optional[str] = None, upcoming_count: Optional[int] = None) -> dict:
        """The draft as the draft room shows it: teams, picks, who's on the clock, the next
        picks, and the viewer's open roster needs."""
        board = self.board()
        on_the_clock = board.on_the_clock
        upcoming = board.order.upcoming(board.next_pick, upcoming_count or len(board.teams) * 2)
        roster = board.rosters.get(viewer_member_id) if viewer_member_id else None
        return {
            'status': self.season.get('status'),
            'total_picks': board.order.total_picks,
            'rounds': board.order.rounds,
            'next_pick': None if board.is_complete else board.next_pick,
            'current_round': None if board.is_complete else board.order.round_for_pick(board.next_pick),
            'on_the_clock_member_id': on_the_clock['member_id'] if on_the_clock else None,
            'upcoming': [
                {'overall_pick': pick, 'round': board.order.round_for_pick(pick), 'member_id': board.teams[slot]['member_id']}
                for pick, slot in upcoming
            ],
            'teams': board.teams,
            'picks': board.picks,
            'my_roster': None if roster is None else {
                'picks_left': roster.picks_left,
                'points': roster.points,
                'open_field_positions': roster.open_field_positions,
                'open_rotation_roles': roster.open_rotation_roles,
                'bullpen_count': roster.bullpen_count,
                'bench_count': roster.bench_count,
                'hard_needs': roster.hard_needs,
                'slack': roster.slack,
            },
        }

    def _pool(self) -> list[DraftCard]:
        rows = self.db.fetch_league_card_pool(self.season['season_id'], self.league['edition_ids'])
        return [DraftCard.from_row(row) for row in rows]

    @staticmethod
    def fits_points_cap(roster: DraftRoster, card: DraftCard, slot: str, pool: list[DraftCard], pts_cap: Optional[int],
                        reserve_cache: Optional[dict[str, tuple[float, set[str]]]] = None, competitors: int = 0) -> bool:
        """Whether drafting `card` into `slot` still leaves room under `pts_cap` to fill every
        remaining hard need with the cheapest cards left that can fill them.

        `reserve_cache` (slot -> cheapest fill) lets a caller checking many cards compute each
        slot's reserve once: it's exact for any card the fill didn't use, so only a card that is
        itself part of the cheapest fill needs its own recompute. `competitors` is passed through
        to `cheapest_fill` (bots plan conservatively; a human pick is checked exactly)."""
        if not pts_cap:
            return True
        after = roster.with_pick(slot, card.points)
        cached = reserve_cache.get(slot) if reserve_cache is not None else None
        if cached is None:
            cached = after.cheapest_fill(pool, competitors=competitors)
            if reserve_cache is not None:
                reserve_cache[slot] = cached
        reserve, used = cached
        if card.release_card_id in used:
            reserve, _ = after.cheapest_fill(pool, exclude_id=card.release_card_id, competitors=competitors)
        return after.points + reserve <= pts_cap

    # MARK: Picks

    def make_pick(self, acting_member_id: Optional[str], is_commissioner: bool, release_card_id: Optional[str]) -> dict:
        """Draft `release_card_id` for the team on the clock, or let the bot choose when it's
        None (an auto-pick). Only the member on the clock, or the commissioner, may pick.
        Raises DraftError for a disallowed pick and DraftConflict if the board moved meanwhile."""
        if self.season.get('status') != 'drafting':
            raise DraftError("This season isn't drafting.")
        board = self.board()
        team = board.on_the_clock
        if team is None:
            raise DraftError("The draft is complete.")
        if team['member_id'] != acting_member_id and not is_commissioner:
            raise DraftError("It's not your pick.")

        if release_card_id is None:
            return self._auto_pick(board, team, self._pool())

        row = self.db.fetch_league_draft_card(release_card_id, self.league['edition_ids'])
        if row is None:
            raise DraftError("That card isn't in this league's card pool.")
        card = DraftCard.from_row(row)
        if board.drafted(card):
            raise DraftError(f"{card.name} has already been drafted.")

        roster = board.rosters[team['member_id']]
        slot = roster.slot_for(card)
        pool: Optional[list[DraftCard]] = None
        if slot is None:
            pool = self._pool()
            if any(roster.slot_for(other) for other in pool):
                raise DraftError(roster.rejection_reason(card))
            slot = roster.fallback_slot(card)
        if self.settings.pts_cap:
            pool = pool if pool is not None else self._pool()
            if not self.fits_points_cap(roster, card, slot, pool, self.settings.pts_cap):
                raise DraftError(f"Drafting {card.name} would leave too few points under the {self.settings.pts_cap}-point cap to fill your roster.")
        return self._record(board, team, card, slot, is_auto=False)

    def run_bot_picks(self, limit: Optional[int] = None) -> list[dict]:
        """Make picks for bot seats while a bot is on the clock. Returns the picks made.

        Reads the board and pool once and keeps them current in memory between picks; each
        pick's write still re-checks the board under a lock, so a human pick landing mid-run
        surfaces as a DraftConflict rather than a bad pick."""
        made: list[dict] = []
        if self.season.get('status') != 'drafting':
            return made
        board = self.board()
        pool = self._pool()
        while limit is None or len(made) < limit:
            team = board.on_the_clock
            if team is None or team.get('user_id'):
                break
            made.append(self._auto_pick(board, team, pool))
        return made

    def _auto_pick(self, board: DraftBoard, team: dict, pool: list[DraftCard]) -> dict:
        roster = board.rosters[team['member_id']]
        choice = LeagueDraftBot(self._pick_rng(board.next_pick)).choose(
            roster, pool, team_count=len(board.teams), pts_cap=self.settings.pts_cap,
        )
        if choice is None:
            raise DraftError("No cards are left to draft.")
        card, slot = choice
        pick = self._record(board, team, card, slot, is_auto=True)
        pool[:] = [other for other in pool if not (
            other.release_card_id == card.release_card_id
            or (card.source_card_id and other.source_card_id == card.source_card_id)
        )]
        return pick

    def _pick_rng(self, overall_pick: int) -> random.Random:
        """Seeded per pick, so an auto-pick retried after a conflict draws the same way."""
        return random.Random((self.season.get('seed') or 0) + overall_pick)

    def _record(self, board: DraftBoard, team: dict, card: DraftCard, slot: str, is_auto: bool) -> dict:
        """Write the pick, then advance `board` in memory to match."""
        overall_pick = board.next_pick
        round = board.order.round_for_pick(overall_pick)
        recorded = self.db.record_league_draft_pick(
            season_id=self.season['season_id'],
            overall_pick=overall_pick,
            round=round,
            member_id=team['member_id'],
            team_id=team['team_id'],
            release_card_id=card.release_card_id,
            roster_position=slot,
            is_auto=is_auto,
        )
        if not recorded:
            raise DraftConflict("Someone else picked first. Refresh the board and try again.")

        pick = {
            'overall_pick': overall_pick,
            'round': round,
            'member_id': team['member_id'],
            'release_card_id': card.release_card_id,
            'source_card_id': card.source_card_id,
            'name': card.name,
            'points': card.points,
            'roster_position': slot,
            'is_auto': is_auto,
        }
        board.picks.append(pick)
        roster = board.rosters[team['member_id']]
        roster.positions.append(slot)
        roster.points += card.points

        if board.is_complete:
            self.db.update_league_season_status(self.season['season_id'], 'drafting', 'setup')
            self.season['status'] = 'setup'
        return pick
