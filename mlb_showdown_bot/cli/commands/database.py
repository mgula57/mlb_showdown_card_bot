import typer
from typing import Optional
from datetime import datetime, timedelta, timezone
import time

# Import business logic
from ...core.archive.player_stats_archive import PlayerStatsArchive, PostgresDB
from ...core.card.utils.shared_functions import convert_year_string_to_list

app = typer.Typer()

@app.command("run")
def database_update(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
    years: str = typer.Option(None, "--years", "-y", help="Which year(s) to archive."),
    showdown_sets: str = typer.Option("CLASSIC,EXPANDED,2000,2001,2002,2003,2004,2005", "--showdown_sets", "-s", help="Showdown Set(s) to use, comma-separated."),
    publish_to_postgres: bool = typer.Option(False, "--publish_to_postgres", "-pg", help="Publish archived data to Postgres"),
    run_player_list: bool = typer.Option(False, "--run_player_list", "-list", help="Scrape player list from baseball reference"),
    run_player_stats: bool = typer.Option(False, "--run_player_stats", "-stats", help="Scrape player stats from baseball reference"),
    run_player_cards: bool = typer.Option(False, "--run_player_cards", "-cards", help="Generate Showdown Player Cards for archived players"),
    run_auto_image_suggestions: bool = typer.Option(False, "--run_auto_image_suggestions", "-auto_im", help="Generate auto image suggestions for archived players"),
    refresh_explore: bool = typer.Option(False, "--refresh_explore", "-exp", help="Refresh Explore materialized views"),
    refresh_trends: bool = typer.Option(False, "--refresh_trends", "-trends", help="Refresh trending cards data"),
    drop_existing: bool = typer.Option(False, "--drop_existing", "-drop", help="Drop existing materialized views before refreshing"),
    exclude_records_with_stats: bool = typer.Option(False, "--exclude_records_with_stats", "-ers", help="Exclude records that already have stats in the database when scraping player stats"),
    daily_mid_season_update: bool = typer.Option(False, "--daily_mid_season_update", "-dmsu", help="Run a daily mid-season update to catch stat changes"),
    modified_start_date: Optional[str] = typer.Option(None, "--modified_start_date", "-mod_s", help="Only include records modified after this date"),
    modified_end_date: Optional[str] = typer.Option(None, "--modified_end_date", "-mod_e", help="Only include records modified before this date"),
    player_id_list: Optional[str] = typer.Option(None, "--player_id_list", "-pil", help="Comma-separated list of player IDs (e.g., 'abreuwi02,bailepa01,crowape01')"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit how many players are processed"),
    ignore_minimums: bool = typer.Option(False, "--ignore_minimums", "-im", help="Ignore minimum PA/IP when archiving stats")
):
    """Archive player stats to Postgres"""

    start_time = time.time()
    is_production = env.lower() == "prod"
    
    try:
        year_list = convert_year_string_to_list(years) if years else []
        
        # Parse player_id_list from comma-separated string
        parsed_player_id_list = None
        if player_id_list:
            parsed_player_id_list = [pid.strip() for pid in player_id_list.split(',') if pid.strip()]

        # Parse showdown sets
        showdown_set_list = [s.strip() for s in showdown_sets.split(',') if s.strip()]

        # RUN DAILY MID-SEASON UPDATE
        if daily_mid_season_update and year_list == [datetime.now().year]:
            # CHANGE MODIFIED END DATE TO 16 HOURS AGO
            modified_end_date:str = (datetime.now(timezone.utc) - timedelta(hours=16)).strftime("%Y-%m-%d %H:%M:%S")
            
        # UPDATE PLAYER LIST
        if run_player_list:
            player_stats_archive = PlayerStatsArchive(years=year_list, is_snapshot=False)
            player_stats_archive.generate_player_list(delay_between_years=0.5, publish_to_postgres=publish_to_postgres)
            print(f"Total players found: {len(player_stats_archive.player_list)}")

        if run_player_stats:
            player_stats_archive = PlayerStatsArchive(years=year_list, is_snapshot=False)
            player_stats_archive.scrape_stats_for_player_list(
                publish_to_postgres=publish_to_postgres, 
                exclude_records_with_stats=exclude_records_with_stats,
                modified_start_date=modified_start_date,
                modified_end_date=modified_end_date,
                limit=limit,
                player_id_list=parsed_player_id_list
            )

        if run_player_cards:
            player_stats_archive = PlayerStatsArchive(years=year_list, is_snapshot=False)
            player_stats_archive.generate_showdown_player_cards(
                publish_to_postgres=publish_to_postgres, 
                refresh_explore=refresh_explore, 
                sets=showdown_set_list,
                ignore_minimums=ignore_minimums
            )

        if run_auto_image_suggestions:
            db = PostgresDB(is_archive=is_production)
            db.build_auto_image_table(refresh_explore=refresh_explore, drop_existing=drop_existing)

        if not run_player_cards and refresh_explore:
            print("Refreshing Explore materialized views...")
            db = PostgresDB(is_archive=is_production)
            db.refresh_explore_views(drop_existing=drop_existing)

        if refresh_trends:
            print("Refreshing Trending Cards data...")
            db = PostgresDB(is_archive=is_production)
            db.refresh_all_trends()

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
        
        print(f"\n✅ Database operation completed in {time_str}")


@app.command("feature_status")
def database_feature_status(
    feature_name: str = typer.Option(None, "--feature_name", "-f", help="Name of the feature to check status."),
    disable_feature: bool = typer.Option(False, "--disable", "-d", help="Is the feature disabled?"),
    message: str = typer.Option(None, "--message", "-m", help="Optional message for the status update."),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
):
    """Check status of database features"""
    print(f"Updating feature '{feature_name}' to disabled={disable_feature} with message='{message}'")
    is_production = env.lower() == "prod"
    db = PostgresDB(is_archive=is_production)
    db.update_feature_status(feature_name=feature_name, is_disabled=disable_feature, message=message)
    print("✅ Feature status updated.")

@app.command("store_fielding_stats")
def store_fielding_stats_in_db():
    """Fetch fielding stats from Fangraphs and store in Postgres DB"""
    from ...core.fangraphs.client import FangraphsAPIClient
    from ...core.archive.player_stats_archive import PostgresDB

    print("Fetching fielding stats from Fangraphs...")
    fg_api = FangraphsAPIClient()
    df = fg_api.fetch_fielding_stats(season=2025, position="LF", fangraphs_player_ids=[])

@app.command("refresh_player_id_table")
def refresh_player_id_table(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in")
):
    """Fetch player ID mapping data and refresh the player_id_master table in Postgres DB"""
    from ...core.ids.fetch_player_id_csv import fetch_player_id_csv
    from ...core.database.postgres_db import PostgresDB
    is_production = env.lower() == "prod"

    print("Fetching player ID mapping data...")
    data = fetch_player_id_csv()
    print(f"Fetched {len(data)} player ID records.")

    print("Updating player_id_master table in Postgres DB...")
    db = PostgresDB(is_archive=is_production)
    db.update_player_id_table(data)
    print("✅ player_id_master table refreshed.")

@app.command("spotlight")
def publish_spotlight_cards(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
    player_ids: str = typer.Option(..., "--player_ids", "-p", help="Comma-separated list of player IDs to spotlight."),
    message: str = typer.Option("Featured by the MLB Showdown Bot team", "--message", "-m", help="Message or reason for spotlighting the cards.")
):
    """Publish spotlight cards to the database"""
    parsed_player_ids = [pid.strip() for pid in player_ids.split(',') if pid.strip()]
    print(f"Publishing spotlight for player IDs: {parsed_player_ids} with message: '{message}'")

    is_production = env.lower() == "prod"
    db = PostgresDB(is_archive=is_production)
    db.publish_new_spotlight(player_ids=parsed_player_ids, message=message)
    print("✅ Spotlight cards published.")

@app.command("refresh_card_of_the_day")
def refresh_card_of_the_day(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
):
    """Refresh the Card of the Day in the database"""
    from ...core.database.postgres_db import PostgresDB

    print("Refreshing Card of the Day...")
    is_production = env.lower() == "prod"
    db = PostgresDB(is_archive=is_production)
    db.refresh_card_of_the_day()
    print("✅ Card of the Day refreshed.")

@app.command("build_logging_tables")
def build_logging_tables(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in")
):
    """Build logging tables in the archive database"""
    from ...core.database.postgres_db import PostgresDB

    print("Building logging tables in the archive database...")
    is_production = env.lower() == "prod"
    db = PostgresDB(is_archive=is_production)
    db.build_logging_tables()
    print("✅ Logging tables built.")

# Make database the default command
@app.callback(invoke_without_command=True)
def database_main(ctx: typer.Context):
    """Archive operations"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(database_update)