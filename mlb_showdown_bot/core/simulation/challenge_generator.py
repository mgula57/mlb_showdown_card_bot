"""Team Challenge template validation and instance generation.

The single source of truth shared by the CLI (`mlb_showdown_bot/cli/commands/challenges.py`)
and the admin API (`mlb_showdown_bot/api/admin_challenges.py`). A **template** is hand-authored
content; an **instance** is one concrete playable challenge (a real year + club resolved from
the template's pools). `ChallengeGenerator.rotate()` keeps one live instance per category;
`instance_from_template()` forces one for a single template outside that rotation.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..database.postgres_db import PostgresDB
from .takeover import TakeoverOptions


class GoalType(str, Enum):
    MADE_PLAYOFFS = "made_playoffs"
    WIN_DIVISION = "win_division"
    WIN_PENNANT = "win_pennant"
    WIN_WORLD_SERIES = "win_world_series"
    MIN_WINS = "min_wins"
    BEAT_TEAM_RECORD = "beat_team_record"


class BeatTarget(str, Enum):
    """Special `target_abbr` values for a `beat_team_record` goal that resolve to a club
    dynamically, per playthrough, instead of naming one. Unlike a fixed abbr, which club has the
    best/worst record isn't known until that instance's season is actually simulated (the games
    aren't deterministic), so these can't be resolved at template- or instance-creation time -
    see `_challenge_passed` in `api/sim.py`, which resolves them from the played standings."""
    BEST_RECORD = "BEST_RECORD"
    WORST_RECORD = "WORST_RECORD"


class ChallengeCategory(str, Enum):
    """Presentation grouping for the challenges list - drives the accent color and the
    one-per-category weekly rotation. Not a mechanic: the goal/cap/filters do the actual work."""
    LEGENDARY = "legendary"
    BUDGET_CAP = "budget_cap"
    SUPERTEAM = "superteam"
    THEMED = "themed"


# MATCHES api/sim.py's _EARLIEST_SEASON - THE ARCHIVE HAS NO FULL CARD COVERAGE BEFORE THIS.
EARLIEST_SEASON = 1975
INSTANCE_LIFETIME_DAYS = 7
PRUNE_AFTER_DAYS = 30
# A CHOSEN YEAR CAN COME BACK WITH NO STANDINGS (TRANSIENT MLB STATS API HICCUP) - RETRY A FEW
# TIMES WITH A FRESH YEAR BEFORE GIVING UP ON A TEMPLATE FOR THIS CYCLE.
MAX_YEAR_ATTEMPTS = 3
# 9 FIELDERS + 5 STARTERS + 5 BULLPEN + 3 BENCH IS THE BUCKET SPLIT A CHALLENGE 'NEW TEAM' IS
# BUILT WITH - A SMALLER ROSTER CAN'T HOLD IT AND WOULD FAIL THE TEAM SETUP STEP.
MIN_ROSTER_SIZE = 22


class ChallengeError(Exception):
    """A validation/precondition failure a caller should surface to the user. `status` is the
    HTTP code the API should return; the CLI just prints the message."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def validate_year_pool(year_pool: str) -> None:
    """Raise ChallengeError unless `year_pool` is 'any', 'random_range:lo,hi', or a comma list
    of years."""
    if year_pool == 'any':
        return
    if year_pool.startswith('random_range:'):
        bounds = year_pool.removeprefix('random_range:').split(',')
        if len(bounds) == 2 and all(b.strip().isdigit() for b in bounds):
            return
        raise ChallengeError("year_pool random_range must look like 'random_range:1977,2024'")
    if all(y.strip().isdigit() for y in year_pool.split(',')):
        return
    raise ChallengeError("year_pool must be 'any', 'random_range:lo,hi', or a comma list of years")


def build_goal_value(goal_type: GoalType, min_wins: int | None, beat_team_abbr: str | None) -> dict | None:
    """The `goal_value` JSON for a template, validated against its `goal_type`."""
    if goal_type == GoalType.MIN_WINS:
        if min_wins is None:
            raise ChallengeError("min_wins is required when goal_type is min_wins")
        return {"min_wins": int(min_wins)}
    if goal_type == GoalType.BEAT_TEAM_RECORD:
        if not beat_team_abbr:
            raise ChallengeError("beat_team_abbr is required when goal_type is beat_team_record")
        # A REAL CLUB ABBR (E.G. "NYY") OR A `BeatTarget` SENTINEL (E.G. "best_record") - BOTH
        # NORMALIZE THE SAME WAY, SO NO BRANCH IS NEEDED HERE.
        return {"target_abbr": beat_team_abbr.strip().upper()}
    return None


@dataclass
class InstanceResult:
    """One instance produced by the generator."""
    instance_id: str
    slug: str
    year: int
    replaces_abbr: str
    beat_team_record: dict | None = None


@dataclass
class RotationReport:
    pruned: int = 0
    created: list[InstanceResult] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # "slug: reason" / "category 'x': reason"


class ChallengeGenerator:
    """Resolves templates into instances against one `PostgresDB` connection."""

    def __init__(self, db: PostgresDB):
        self.db = db

    # -- resolution -------------------------------------------------------------

    def _resolve_year(self, year_pool: str) -> int:
        if year_pool.startswith('random_range:'):
            low, high = (int(bound) for bound in year_pool.removeprefix('random_range:').split(','))
            return random.randint(low, high)
        if year_pool != 'any':
            return random.choice([int(y) for y in year_pool.split(',')])
        return random.randint(EARLIEST_SEASON, datetime.now().year)

    def _resolve_replaces(self, replaces_pool: str, options: TakeoverOptions) -> str | None:
        """Pick a real club abbreviation. Caller must have confirmed `options.clubs` is non-empty."""
        if replaces_pool == 'worst_record':
            return options.default_abbr
        if replaces_pool == 'any':
            return random.choice(options.clubs).abbreviation
        # COMMA LIST OF EXPLICIT ABBREVIATIONS - PICK ONE THAT ACTUALLY PLAYED THIS YEAR
        # (FRANCHISES RELOCATE/RENAME ACROSS ERAS, SO NOT EVERY CANDIDATE IS VALID EVERY YEAR).
        candidates = [abbr.strip().upper() for abbr in replaces_pool.split(',')]
        random.shuffle(candidates)
        known = {club.abbreviation for club in options.clubs}
        return next((c for c in candidates if c in known), None)

    def resolve_target(self, template: dict) -> tuple[int, str, TakeoverOptions] | None:
        """A (year, replaces_abbr, options) triple for a template, retrying on years with no
        data. `options` is handed back (rather than re-fetched) so `create_instance` can resolve
        `beat_team_record` off the same standings. None if nothing valid turned up within the
        attempt budget."""
        # A `BeatTarget` SENTINEL (E.G. "BEST_RECORD") NEVER MATCHES A REAL CLUB ABBR, SO THIS
        # GUARD IS A NATURAL NO-OP FOR A DYNAMIC TARGET - ONLY A FIXED-ABBR GOAL EXCLUDES A CLUB.
        forbidden_abbr = None
        if template.get('goal_type') == GoalType.BEAT_TEAM_RECORD.value:
            forbidden_abbr = (template.get('goal_value') or {}).get('target_abbr')
        for _ in range(MAX_YEAR_ATTEMPTS):
            year = self._resolve_year(template['year_pool'])
            if year < EARLIEST_SEASON:
                continue
            options = TakeoverOptions(year=year)
            if not options.clubs:
                continue
            replaces_abbr = self._resolve_replaces(template['replaces_pool'], options)
            if replaces_abbr and replaces_abbr != forbidden_abbr:
                return year, replaces_abbr, options
        return None

    def _resolve_beat_team_record(self, template: dict, replaces_abbr: str, options: TakeoverOptions) -> dict | None:
        """The real club (name/wins/losses) a `beat_team_record` template's `target_abbr` names,
        for display on the challenge card before anyone has played it. None for any other goal
        type, or if the club can't be found.

        For a fixed abbr this is exact. For a `BeatTarget` sentinel it's the actual real-history
        best/worst club that season (excluding `replaces_abbr` - the player's own takeover club,
        same exclusion `_challenge_passed` in api/sim.py applies) - flavor only, since the
        simulated season the player actually plays out can end up different from history.
        """
        if template.get('goal_type') != GoalType.BEAT_TEAM_RECORD.value:
            return None
        target_abbr = (template.get('goal_value') or {}).get('target_abbr')
        if not target_abbr:
            return None
        if target_abbr in (BeatTarget.BEST_RECORD.value, BeatTarget.WORST_RECORD.value):
            # `options.clubs` IS ALREADY SORTED WORST RECORD FIRST.
            candidates = [club for club in options.clubs if club.abbreviation != replaces_abbr]
            if not candidates:
                return None
            club = candidates[-1] if target_abbr == BeatTarget.BEST_RECORD.value else candidates[0]
        else:
            club = next((c for c in options.clubs if c.abbreviation == target_abbr), None)
            if club is None:
                return None
        return {"abbr": club.abbreviation, "name": club.name, "wins": club.wins, "losses": club.losses}

    # -- creation -------------------------------------------------------------

    def create_instance(self, template: dict) -> InstanceResult | None:
        """Resolve a year/club for `template` and insert one instance. None if no valid combo
        turned up (the template's pools don't line up with any year that has data)."""
        target = self.resolve_target(template)
        if target is None:
            return None
        year, replaces_abbr, options = target
        beat_team_record = self._resolve_beat_team_record(template, replaces_abbr, options)
        instance_id = self.db.create_challenge_instance(
            template_id=template['template_id'], year=year, replaces_abbr=replaces_abbr,
            pts_limit=template['pts_limit'], expires_in_days=INSTANCE_LIFETIME_DAYS,
            player_filters=template.get('player_filters'),
            roster_size=template.get('roster_size') or 25,
            beat_team_record=beat_team_record,
        )
        return InstanceResult(
            instance_id=instance_id, slug=template['slug'], year=year, replaces_abbr=replaces_abbr,
            beat_team_record=beat_team_record,
        )

    def instance_from_template(self, template: dict, force: bool = False) -> InstanceResult:
        """Force one instance for a single template, outside the category rotation. Raises
        ChallengeError if the template already has a live instance (unless `force`) or if no
        valid year/club combo can be resolved."""
        if not force and self.db.has_unexpired_challenge_instance(template['template_id']):
            raise ChallengeError(
                f"'{template['slug']}' already has a live instance. Pass force to add another.", status=409
            )
        result = self.create_instance(template)
        if result is None:
            raise ChallengeError(
                f"No valid year/club combo for '{template['slug']}' after {MAX_YEAR_ATTEMPTS} attempts "
                "- check its year_pool / replaces_pool.", status=422
            )
        return result

    @staticmethod
    def _lru_key(template: dict):
        """Rotation order within a category: never-instanced first, then oldest instance first,
        random tie-break so a stale pool doesn't lock into one order."""
        last = template.get('last_instanced_at')
        return (last is not None, last or datetime.min, random.random())

    def rotate(self, prune_after_days: int = PRUNE_AFTER_DAYS) -> RotationReport:
        """Prune old expired instances, then fill every category with no live challenge from its
        least-recently-used active template."""
        report = RotationReport()
        report.pruned = self.db.prune_expired_challenge_instances(older_than_days=prune_after_days)

        pools: dict[str, list[dict]] = {}
        for template in self.db.list_active_challenge_templates():
            pools.setdefault(template['category'], []).append(template)

        for category in sorted(pools):
            if self.db.has_unexpired_challenge_instance_for_category(category):
                continue
            for template in sorted(pools[category], key=self._lru_key):
                result = self.create_instance(template)
                if result is not None:
                    report.created.append(result)
                    break
            else:
                report.skipped.append(f"category '{category}': no template produced a valid instance")

        return report
