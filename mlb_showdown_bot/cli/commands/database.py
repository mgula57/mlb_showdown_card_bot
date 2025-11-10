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
    years: str = typer.Option(None, "--years", "-y", help="Which year(s) to archive."),
    showdown_sets: str = typer.Option("CLASSIC,EXPANDED,2000,2001,2002,2003,2004,2005", "--showdown_sets", "-s", help="Showdown Set(s) to use, comma-separated."),
    publish_to_postgres: bool = typer.Option(False, "--publish_to_postgres", "-pg", help="Publish archived data to Postgres"),
    run_player_list: bool = typer.Option(False, "--run_player_list", "-list", help="Scrape player list from baseball reference"),
    run_player_stats: bool = typer.Option(False, "--run_player_stats", "-stats", help="Scrape player stats from baseball reference"),
    run_player_cards: bool = typer.Option(False, "--run_player_cards", "-cards", help="Generate Showdown Player Cards for archived players"),
    run_auto_image_suggestions: bool = typer.Option(False, "--run_auto_image_suggestions", "-auto_im", help="Generate auto image suggestions for archived players"),
    refresh_explore: bool = typer.Option(False, "--refresh_explore", "-exp", help="Refresh Explore materialized views"),
    drop_existing: bool = typer.Option(False, "--drop_existing", "-drop", help="Drop existing materialized views before refreshing"),
    exclude_records_with_stats: bool = typer.Option(False, "--exclude_records_with_stats", "-ers", help="Exclude records that already have stats in the database when scraping player stats"),
    daily_mid_season_update: bool = typer.Option(False, "--daily_mid_season_update", "-dmsu", help="Run a daily mid-season update to catch stat changes"),
    modified_start_date: Optional[str] = typer.Option(None, "--modified_start_date", "-mod_s", help="Only include records modified after this date"),
    modified_end_date: Optional[str] = typer.Option(None, "--modified_end_date", "-mod_e", help="Only include records modified before this date"),
    player_id_list: Optional[str] = typer.Option(None, "--player_id_list", "-pil", help="Comma-separated list of player IDs (e.g., 'abreuwi02,bailepa01,crowape01')"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit how many players are processed"),
):
    """Archive player stats to Postgres"""

    start_time = time.time()
    
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
                sets=showdown_set_list
            )

        if run_auto_image_suggestions:
            db = PostgresDB(is_archive=True)
            db.build_auto_images_table(refresh_explore=refresh_explore)

        if not run_player_cards and refresh_explore:
            print("Refreshing Explore materialized views...")
            db = PostgresDB(is_archive=True)
            db.refresh_explore_views(drop_existing=drop_existing)

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

# Make database the default command
@app.callback(invoke_without_command=True)
def database_main(ctx: typer.Context):
    """Archive operations"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(database_update)