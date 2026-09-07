import json

import typer

from ...core.database.postgres_db import PostgresDB
from ...core.simulation.challenge_generator import (
    MAX_YEAR_ATTEMPTS,
    MIN_ROSTER_SIZE,
    PRUNE_AFTER_DAYS,
    ChallengeCategory,
    ChallengeError,
    ChallengeGenerator,
    GoalType,
    build_goal_value,
    validate_year_pool,
)

app = typer.Typer()


def _target_db_label(env: str) -> str:
    """`--env prod` hits DATABASE_URL_ARCHIVE, anything else hits DATABASE_URL_LOGS - these are
    two different databases, and inserting a template into one while `rotate` reads the other
    silently looks like "no templates exist" with no error anywhere. Echoing this on every
    command makes that mismatch obvious instead of silent."""
    return "DATABASE_URL_ARCHIVE" if env.lower() == "prod" else "DATABASE_URL_LOGS"


def _open_db(env: str) -> PostgresDB:
    typer.echo(f"Using --env {env} ({_target_db_label(env)}).")
    return PostgresDB(is_archive=env.lower() == "prod")


@app.callback(invoke_without_command=True)
def challenges_main():
    """Manage Team Challenge templates/instances."""


@app.command("rotate")
def rotate_challenges(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
    prune_after_days: int = typer.Option(PRUNE_AFTER_DAYS, "--prune-after-days", help="Delete instances expired longer than this many days"),
):
    """Advance the weekly rotation: prune old expired instances, then fill every category that
    has no live challenge with ONE instance - the least-recently-used active template in that
    category. Meant to run weekly (see .github/workflows/rotate_challenges.yml), not by hand.

    To force a specific template outside the rotation, use `challenges instance <slug>`.
    """
    db = _open_db(env)
    try:
        report = ChallengeGenerator(db).rotate(prune_after_days=prune_after_days)
        if report.pruned:
            typer.echo(f"Pruned {report.pruned} expired challenge instance(s).")
        for result in report.created:
            typer.echo(f"Generated '{result.slug}': {result.year} {result.replaces_abbr} (instance {result.instance_id})")
        for skip in report.skipped:
            typer.echo(f"SKIP {skip}.")
        typer.echo(f"Done. {len(report.created)} new challenge instance(s) generated.")
    finally:
        db.close_connection()


@app.command("instance")
def create_instance(
    slug: str = typer.Argument(..., help="Template slug to instance now"),
    force: bool = typer.Option(False, "--force", help="Generate even if this template already has a live instance"),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
):
    """Force one live instance for a single template right now, outside the category rotation.

    Skips the prune and the one-per-category gate that `challenges rotate` enforces. Works on
    inactive templates too (with a notice). Use it right after `create-template`, or to
    hand-pick the next challenge in a category.
    """
    db = _open_db(env)
    try:
        template = db.get_challenge_template_by_slug(slug)
        if template is None:
            typer.echo(f"ERROR: no template with slug '{slug}'.")
            raise typer.Exit(code=1)
        if not template['active']:
            typer.echo(f"NOTE: template '{slug}' is inactive - generating anyway (manual override).")
        try:
            result = ChallengeGenerator(db).instance_from_template(template, force=force)
        except ChallengeError as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(code=1)
        typer.echo(f"Generated '{result.slug}': {result.year} {result.replaces_abbr} (instance {result.instance_id})")
        typer.echo("Done. 1 new challenge instance generated.")
    finally:
        db.close_connection()


@app.command("create-template")
def create_template(
    slug: str = typer.Option(..., "--slug", help="Unique short id, e.g. 'small-budget-pennant'"),
    title: str = typer.Option(..., "--title", help="Display title, e.g. 'Cinderella Run'"),
    description: str = typer.Option(..., "--description", help="Flavor text shown on the challenge card"),
    goal_type: GoalType = typer.Option(..., "--goal-type", help="What the player needs to accomplish"),
    min_wins: int = typer.Option(None, "--min-wins", help="Required when --goal-type is min_wins"),
    beat_team_abbr: str = typer.Option(None, "--beat-team-abbr", help="Required when --goal-type is beat_team_record - the club abbr (e.g. NYY) whose win total must be beaten"),
    category: ChallengeCategory = typer.Option(ChallengeCategory.THEMED, "--category", help="Rotation pool + accent color for the challenges list - one live instance per category at a time"),
    pts_limit: int = typer.Option(None, "--pts-limit", help="Team budget cap. Omit for no cap"),
    roster_size: int = typer.Option(25, "--roster-size", help="Minimum roster size a team needs to take on this challenge (also the size a challenge 'New Team' is pre-built at)"),
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
    """Add a new challenge template - the hand-authored content that `challenges rotate` picks
    concrete year/club instances from. It joins its `--category` rotation pool; run
    `challenges instance <slug>` afterward to produce a live instance right away (rotate only
    fills a category that has no live challenge).

    Example - copy, edit, and run:

    showdown_bot challenges create-template --slug small-budget-pennant --title "Cinderella Run" --description "Take over a real club on a shoestring budget and win the pennant." --goal-type win_pennant --pts-limit 3000 --year-pool any --replaces-pool worst_record --env dev

    Example with a win_division goal:

    showdown_bot challenges create-template --slug take-the-division --title "Division Crown" --description "Take over a real club and finish first in your division." --goal-type win_division --pts-limit 4000 --year-pool any --replaces-pool worst_record --env dev

    Example with a min_wins goal, limited to one year:

    showdown_bot challenges create-template --slug classic-90-wins --title "90-Win Season" --description "Build a 1998 club and hit 90 wins." --goal-type min_wins --min-wins 90 --pts-limit 4500 --year-pool 1998 --replaces-pool any --env dev

    Example restricted to left-handed Mets/Yankees players:

    showdown_bot challenges create-template --slug lefty-subway --title "Lefty Subway Series" --description "Only lefties from the Mets or Yankees allowed." --goal-type made_playoffs --player-filters '{"team": ["NYM", "NYY"], "hand": ["L"]}' --env dev

    Example - beat a specific iconic club's win total in that same simulated season:

    showdown_bot challenges create-template --slug dethrone-27-yankees --title "Dethrone the '27 Yankees" --description "Take over another 1927 club and finish with more wins than Murderers' Row." --goal-type beat_team_record --beat-team-abbr NYY --category legendary --year-pool 1927 --replaces-pool worst_record --env dev
    """
    if roster_size < MIN_ROSTER_SIZE:
        typer.echo(f"ERROR: --roster-size must be at least {MIN_ROSTER_SIZE}.")
        raise typer.Exit(code=1)
    try:
        validate_year_pool(year_pool)
        goal_value = build_goal_value(goal_type, min_wins, beat_team_abbr)
    except ChallengeError as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1)

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

    db = _open_db(env)
    try:
        template_id = db.create_challenge_template(
            slug=slug, title=title, description=description, goal_type=goal_type.value,
            goal_value=goal_value, pts_limit=pts_limit, year_pool=year_pool,
            replaces_pool=replaces_pool, active=not inactive, player_filters=parsed_player_filters,
            category=category.value, roster_size=roster_size,
        )
        typer.echo(f"Created template '{slug}' ({template_id}).")
        typer.echo(f"Run `challenges instance {slug}` to produce a live instance now.")
    finally:
        db.close_connection()


@app.command("list-templates")
def list_templates(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
):
    """List every challenge template, active or not."""
    db = _open_db(env)
    try:
        templates = db.list_challenge_templates()
        if not templates:
            typer.echo("No templates found.")
            return
        for t in templates:
            flag = "" if t['active'] else "  (inactive)"
            cap = f"{t['pts_limit']} pts" if t['pts_limit'] is not None else "no cap"
            roster = f"{t.get('roster_size') or 25}-man"
            filters = f"  filters: {t['player_filters']}" if t.get('player_filters') else ""
            category = t.get('category') or "themed"
            typer.echo(f"{t['slug']:<28} {t['title']:<30} {category:<12} {t['goal_type']:<18} {cap:<10} {roster:<8}{flag}{filters}")
    finally:
        db.close_connection()
