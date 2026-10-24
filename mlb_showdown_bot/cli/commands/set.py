import typer
import time

# Import business logic
from ...core.set_builder.showdown_bot_set import ShowdownBotSet, PointBucket
from ...core.set_builder.wotc_set_profile import WotcSetProfile
from ...core.set_builder.selection import TeamWeighting
from ...core.set_builder.release_importer import ReleaseImporter
from ...core.set_builder.release_images import ReleaseImageJanitor
from ...core.database.postgres_db import PostgresDB

app = typer.Typer()

@app.command("build")
def set_builder(
    years: str = typer.Option(None, "--years", "-y", help="Which year(s) to archive."),
    set_name: str = typer.Option(None, "--set_name", "-n", help="Optional name for the set."),
    showdown_sets: str = typer.Option("CLASSIC,EXPANDED,2000,2001,2002,2003,2004,2005", "--showdown_sets", "-s", help="Showdown Set(s) to use, comma-separated."),
    set_size: int = typer.Option(100, "--set_size", "-ss", help="Number of cards to include in the set."),
    all_star_game: bool = typer.Option(False, "--all_star_game", "-asg", help="Build the full All-Star Game roster set for the given year(s)."),
    team_breakdown: str = typer.Option(None, "--team_breakdown", "-tb", help="Show team breakdown for a specific team."),
    point_buckets: str = typer.Option(None, "--point_buckets", "-pb", help="Point ranges with an ideal share of each player type, as 'min-max:pct' pairs, comma-separated. Ex: '10-50:0.15,60-100:0.10'."),
    wotc_base_set: str = typer.Option(None, "--wotc_base_set", "-wbs", help="Match the position counts, average points and low point buckets of a WOTC base set (2000-2005), scaled to --set_size. --point_buckets overrides the buckets."),
    manually_included_ids: str = typer.Option(None, "--manually_included_ids", "-inc", help="Specific player IDs to include in the set, comma-separated."),
    manually_excluded_ids: str = typer.Option(None, "--manually_excluded_ids", "-exc", help="Specific player IDs to exclude from the set, comma-separated."),
    year_overrides: str = typer.Option(None, "--year_overrides", "-yo", help="Per-player year overrides as 'bref_id:years' pairs, comma-separated. Ex: 'verlaju01:2025-2026'. Cards are generated live instead of pulled from the DB."),
    team_selection: str = typer.Option("GAMES_PLAYED", "--team_selection", "-tsel", help="For year-override cards, how to choose the card's team. Options: GAMES_PLAYED, LAST_TEAM, FIRST_TEAM."),
    csv_file_path: str = typer.Option(None, "--csv_file", "-csv", help="Path to CSV file with bref_id and year columns (relative to core/set_builder folder)."),
    build_images: bool = typer.Option(False, "--build_images", "-img", help="Optionally build card images for the set after building."),
    dark_mode: bool = typer.Option(False, "--dark_mode", "-dark", help="Render card images in dark mode."),
    variable_spd: bool = typer.Option(False, "--variable_spd", "-vs", help="Enable variable speed for 2000/2001 set cards."),
    export_data: bool = typer.Option(False, "--export_data", "-data", help="Optionally export card data to JSON after building the set."),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to use, e.g., development, production."),
):
    """Archive player stats to Postgres"""

    # Parse showdown sets
    showdown_set_list = [s.strip() for s in showdown_sets.split(',') if s.strip()]

    if all_star_game and len(showdown_set_list) > 1:
        raise typer.BadParameter("All-Star Game mode requires a single --showdown_sets value, e.g. -s EXPANDED")

    # Parse year overrides ("bref_id:years" pairs)
    year_overrides_dict = None
    if year_overrides:
        year_overrides_dict = {}
        for pair in year_overrides.split(','):
            pair = pair.strip()
            if not pair:
                continue
            if ':' not in pair:
                raise typer.BadParameter(f"Invalid --year_overrides entry '{pair}'. Expected 'bref_id:years', e.g. 'verlaju01:2025-2026'")
            player_id, override_years = pair.split(':', 1)
            year_overrides_dict[player_id.strip()] = override_years.strip()

    start_time = time.time()

    try:
        # Parse years
        year_list = [int(y.strip()) for y in years.split(',')] if years else []

        # BUILD THE SET
        wotc_profile = WotcSetProfile.load(wotc_base_set) if wotc_base_set else None
        showdown_bot_set = ShowdownBotSet(
            years=year_list,
            showdown_sets=showdown_set_list,
            set_size=set_size,
            all_stars_only=all_star_game,
            point_buckets=PointBucket.parse_cli(point_buckets) if point_buckets else (wotc_profile.point_buckets if wotc_profile else []),
            position_targets=wotc_profile.position_targets if wotc_profile else [],
            team_weighting=wotc_profile.team_weighting if wotc_profile else TeamWeighting.EVEN,
            manually_included_ids=[pid.strip() for pid in manually_included_ids.split(',')] if manually_included_ids else None,
            manually_excluded_ids=[pid.strip() for pid in manually_excluded_ids.split(',')] if manually_excluded_ids else None,
            year_overrides=year_overrides_dict,
            team_selection=team_selection,
            csv_file_path=csv_file_path
        )
        showdown_bot_set.build_set_player_list(show_team_breakdown=team_breakdown, source_env=env)
        if build_images or export_data:
            showdown_bot_set.generate_showdown_cards_for_final_players(
                export_data=export_data,
                skip_images=not build_images,
                set_name=set_name,
                dark_mode=dark_mode,
                variable_speed=variable_spd,
                source_env=env
            )

    except Exception as e:
        # Full traceback
        import traceback
        traceback.print_exc()

    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Format the elapsed time nicely
        if elapsed_time < 60:
            time_str = f"{elapsed_time:.2f} seconds"
        elif elapsed_time < 3600:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            time_str = f"{minutes}m {seconds:.1f}s"
        else:
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = elapsed_time % 60
            time_str = f"{hours}h {minutes}m {seconds:.1f}s"
        
        print(f"\n✅ Set Builder operation completed in {time_str}")


@app.command("import_release")
def import_release(
    json_path: str = typer.Argument(..., help="Path to a set export JSON (from `set build --export_data`)."),
    release_name: str = typer.Option(..., "--name", "-n", help="Release name. An existing release you own with this name is updated in place."),
    user_id: str = typer.Option(..., "--user_id", "-u", help="Supabase user id that owns the release."),
    base_edition_name: str = typer.Option("Base Set", "--base_edition_name", "-b", help="Edition name for the non-expansion cards. Expansions are named by their code (e.g. CC)."),
    publish: bool = typer.Option(False, "--publish", "-p", help="Publish the editions so the release is publicly visible."),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to write to (dev or prod)."),
):
    """Load a locally built set export into the Release Builder, one edition per image edition."""
    db = PostgresDB(is_archive=env.lower() == "prod")
    if db.connection is None:
        raise typer.Exit(code=1)
    importer = ReleaseImporter(json_path=json_path, release_name=release_name, user_id=user_id, db=db, base_edition_name=base_edition_name, publish=publish)
    release_id = importer.run()
    db.close_connection()
    print(f"\n✅ Release ready: /release-builder/{release_id}")


@app.command("clean_release_images")
def clean_release_images(
    dry_run: bool = typer.Option(False, "--dry_run", "-d", help="Only report how many files would be deleted."),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to clean (dev or prod)."),
):
    """Delete release images in Supabase storage that no release card image row points to
    (deleted releases/editions, replaced renders, failed best-effort deletes)."""
    db = PostgresDB(is_archive=env.lower() == "prod")
    if db.connection is None:
        raise typer.Exit(code=1)
    deleted_count = ReleaseImageJanitor(db=db, dry_run=dry_run).run()
    db.close_connection()
    print(f"\n✅ {'Would delete' if dry_run else 'Deleted'} {deleted_count} release image files")


# Make set builder the default command
@app.callback(invoke_without_command=True)
def set_builder_main(ctx: typer.Context):
    """Build a Showdown Bot Set"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(set_builder)