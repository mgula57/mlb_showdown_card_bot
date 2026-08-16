import json
import random
from datetime import datetime
from enum import Enum

import typer

from ...core.database.postgres_db import PostgresDB
from ...core.simulation.takeover import TakeoverOptions

app = typer.Typer()


class GoalType(str, Enum):
    MADE_PLAYOFFS = "made_playoffs"
    WIN_PENNANT = "win_pennant"
    WIN_WORLD_SERIES = "win_world_series"
    MIN_WINS = "min_wins"


def _target_db_label(env: str) -> str:
    """`--env prod` hits DATABASE_URL_ARCHIVE, anything else hits DATABASE_URL_LOGS - these are
    two different databases, and inserting a template into one while `generate` reads the other
    silently looks like "no templates exist" with no error anywhere. Echoing this on every
    template-touching command makes that mismatch obvious instead of silent."""
    return "DATABASE_URL_ARCHIVE" if env.lower() == "prod" else "DATABASE_URL_LOGS"


def _validate_year_pool(year_pool: str) -> None:
    if year_pool == 'any':
        return
    if year_pool.startswith('random_range:'):
        bounds = year_pool.removeprefix('random_range:').split(',')
        if len(bounds) == 2 and all(b.strip().isdigit() for b in bounds):
            return
        raise ValueError("--year-pool random_range must look like 'random_range:1977,2024'")
    if all(y.strip().isdigit() for y in year_pool.split(',')):
        return
    raise ValueError("--year-pool must be 'any', 'random_range:lo,hi', or a comma list of years")

# MATCHES api/sim.py's _EARLIEST_SEASON - THE ARCHIVE HAS NO FULL CARD COVERAGE BEFORE THIS.
_EARLIEST_SEASON = 1975
_INSTANCE_LIFETIME_DAYS = 7
_PRUNE_AFTER_DAYS = 30
# A CHOSEN YEAR CAN COME BACK WITH NO STANDINGS (TRANSIENT MLB STATS API HICCUP) - RETRY A FEW
# TIMES WITH A FRESH YEAR BEFORE GIVING UP ON A TEMPLATE FOR THIS CYCLE.
_MAX_YEAR_ATTEMPTS = 3


def _resolve_year(year_pool: str) -> int:
    """Pick a concrete year for a template's year_pool spec."""
    if year_pool.startswith('random_range:'):
        low, high = (int(bound) for bound in year_pool.removeprefix('random_range:').split(','))
        return random.randint(low, high)
    if year_pool != 'any':
        years = [int(y) for y in year_pool.split(',')]
        return random.choice(years)
    return random.randint(_EARLIEST_SEASON, datetime.now().year)


def _resolve_replaces(replaces_pool: str, options: TakeoverOptions) -> str | None:
    """Pick a real club abbreviation for a template's replaces_pool spec. Caller must already
    have confirmed `options.clubs` is non-empty for this year."""
    if replaces_pool == 'worst_record':
        return options.default_abbr
    if replaces_pool == 'any':
        return random.choice(options.clubs).abbreviation
    # COMMA LIST OF EXPLICIT ABBREVIATIONS - PICK ONE THAT ACTUALLY PLAYED THIS YEAR (FRANCHISES
    # RELOCATE/RENAME ACROSS ERAS, SO NOT EVERY CANDIDATE IS VALID FOR EVERY YEAR).
    candidates = [abbr.strip().upper() for abbr in replaces_pool.split(',')]
    random.shuffle(candidates)
    known = {club.abbreviation for club in options.clubs}
    for candidate in candidates:
        if candidate in known:
            return candidate
    return None


def _generate_instance_target(template: dict) -> tuple[int, str] | None:
    """Resolve a (year, replaces_abbr) pair for a template, retrying on years with no data.
    Returns None if nothing valid turned up within the attempt budget."""
    for _ in range(_MAX_YEAR_ATTEMPTS):
        year = _resolve_year(template['year_pool'])
        if year < _EARLIEST_SEASON:
            continue
        options = TakeoverOptions(year=year)
        if not options.clubs:
            continue
        replaces_abbr = _resolve_replaces(template['replaces_pool'], options)
        if replaces_abbr:
            return year, replaces_abbr
    return None


@app.callback(invoke_without_command=True)
def challenges_main():
    """Manage Team Challenge templates/instances."""


@app.command("generate")
def generate_challenges(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
    prune_after_days: int = typer.Option(_PRUNE_AFTER_DAYS, "--prune-after-days", help="Delete instances expired longer than this many days"),
):
    """Top up any active template with no unexpired instance, and prune old expired ones.

    Meant to run on a schedule (e.g. weekly, via Heroku Scheduler or a cron hitting an internal
    endpoint) - not something to run by hand outside of testing.
    """
    typer.echo(f"Using --env {env} ({_target_db_label(env)}).")
    db = PostgresDB(is_archive=env.lower() == "prod")
    try:
        pruned = db.prune_expired_challenge_instances(older_than_days=prune_after_days)
        if pruned:
            typer.echo(f"Pruned {pruned} expired challenge instance(s) older than {prune_after_days} days.")

        templates = db.list_active_challenge_templates()
        created = 0
        for template in templates:
            if db.has_unexpired_challenge_instance(template['template_id']):
                continue

            target = _generate_instance_target(template)
            if target is None:
                typer.echo(f"SKIP '{template['slug']}': no valid year/club combo found after {_MAX_YEAR_ATTEMPTS} attempts.")
                continue

            year, replaces_abbr = target
            instance_id = db.create_challenge_instance(
                template_id=template['template_id'], year=year, replaces_abbr=replaces_abbr,
                pts_limit=template['pts_limit'], expires_in_days=_INSTANCE_LIFETIME_DAYS,
                player_filters=template.get('player_filters'),
            )
            typer.echo(f"Generated '{template['slug']}': {year} {replaces_abbr} (instance {instance_id})")
            created += 1

        typer.echo(f"Done. {created} new challenge instance(s) generated.")
    finally:
        db.close_connection()


@app.command("create-template")
def create_template(
    slug: str = typer.Option(..., "--slug", help="Unique short id, e.g. 'small-budget-pennant'"),
    title: str = typer.Option(..., "--title", help="Display title, e.g. 'Cinderella Run'"),
    description: str = typer.Option(..., "--description", help="Flavor text shown on the challenge card"),
    goal_type: GoalType = typer.Option(..., "--goal-type", help="What the player needs to accomplish"),
    min_wins: int = typer.Option(None, "--min-wins", help="Required when --goal-type is min_wins"),
    pts_limit: int = typer.Option(None, "--pts-limit", help="Team budget cap. Omit for no cap"),
    year_pool: str = typer.Option("any", "--year-pool", help="'any' | comma list of years | 'random_range:lo,hi'"),
    replaces_pool: str = typer.Option("any", "--replaces-pool", help="'any' | 'worst_record' | comma list of abbrs"),
    player_filters: str = typer.Option(
        None, "--player-filters",
        help='JSON object restricting which players are eligible, e.g. \'{"team": ["NYM", "NYY"], "hand": ["L"]}\'. '
             "Same shape as a team's player_filters (min_year/max_year/organization/league/team/hand). Omit for no restriction.",
    ),
    inactive: bool = typer.Option(False, "--inactive", help="Create it disabled - the generator will skip it"),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
):
    """Add a new challenge template - the hand-authored content `challenges generate` picks
    concrete year/club instances from. Run `challenges generate` afterward to actually produce
    a live instance from it.

    Example - copy, edit, and run:

    showdown_bot challenges create-template --slug small-budget-pennant --title "Cinderella Run" --description "Take over a real club on a shoestring budget and win the pennant." --goal-type win_pennant --pts-limit 3000 --year-pool any --replaces-pool worst_record --env dev

    Example with a min_wins goal, limited to one year:

    showdown_bot challenges create-template --slug classic-90-wins --title "90-Win Season" --description "Build a 1998 club and hit 90 wins." --goal-type min_wins --min-wins 90 --pts-limit 4500 --year-pool 1998 --replaces-pool any --env dev

    Example restricted to left-handed Mets/Yankees players:

    showdown_bot challenges create-template --slug lefty-subway --title "Lefty Subway Series" --description "Only lefties from the Mets or Yankees allowed." --goal-type made_playoffs --player-filters '{"team": ["NYM", "NYY"], "hand": ["L"]}' --env dev
    """
    if goal_type == GoalType.MIN_WINS and min_wins is None:
        typer.echo("ERROR: --min-wins is required when --goal-type is min_wins.")
        raise typer.Exit(code=1)
    try:
        _validate_year_pool(year_pool)
    except ValueError as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1)
    goal_value = {"min_wins": min_wins} if goal_type == GoalType.MIN_WINS else None

    parsed_player_filters = None
    if player_filters is not None:
        try:
            parsed_player_filters = json.loads(player_filters)
        except json.JSONDecodeError as exc:
            typer.echo(f"ERROR: --player-filters must be valid JSON: {exc}")
            raise typer.Exit(code=1)
        if not isinstance(parsed_player_filters, dict):
            typer.echo("ERROR: --player-filters must be a JSON object.")
            raise typer.Exit(code=1)

    typer.echo(f"Using --env {env} ({_target_db_label(env)}).")
    db = PostgresDB(is_archive=env.lower() == "prod")
    try:
        template_id = db.create_challenge_template(
            slug=slug, title=title, description=description, goal_type=goal_type.value,
            goal_value=goal_value, pts_limit=pts_limit, year_pool=year_pool,
            replaces_pool=replaces_pool, active=not inactive, player_filters=parsed_player_filters,
        )
        typer.echo(f"Created template '{slug}' ({template_id}).")
        typer.echo("Run `challenges generate` to produce a live instance from it.")
    finally:
        db.close_connection()


@app.command("list-templates")
def list_templates(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
):
    """List every challenge template, active or not."""
    typer.echo(f"Using --env {env} ({_target_db_label(env)}).")
    db = PostgresDB(is_archive=env.lower() == "prod")
    try:
        templates = db.list_challenge_templates()
        if not templates:
            typer.echo("No templates found.")
            return
        for t in templates:
            flag = "" if t['active'] else "  (inactive)"
            cap = f"{t['pts_limit']} pts" if t['pts_limit'] is not None else "no cap"
            filters = f"  filters: {t['player_filters']}" if t.get('player_filters') else ""
            typer.echo(f"{t['slug']:<28} {t['title']:<30} {t['goal_type']:<18} {cap:<10}{flag}{filters}")
    finally:
        db.close_connection()
