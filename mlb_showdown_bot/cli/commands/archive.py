import typer
from typing import Optional
from datetime import datetime, timedelta, timezone

# Import business logic
from ...core.archive.player_stats_archive import PlayerStatsArchive
from ...core.card.utils.shared_functions import convert_year_string_to_list

app = typer.Typer()

@app.command("run")
def archive_stats(
    years: str = typer.Option(None, "--years", "-y", help="Which year(s) to archive."),
    publish_to_postgres: bool = typer.Option(False, "--publish_to_postgres", "-pg", help="Publish archived data to Postgres"),
    run_player_list: bool = typer.Option(False, "--run_player_list", "-list", help="Scrape player list from baseball reference"),
    run_player_stats: bool = typer.Option(False, "--run_player_stats", "-stats", help="Scrape player stats from baseball reference"),
    exclude_records_with_stats: bool = typer.Option(False, "--exclude_records_with_stats", "-ers", help="Exclude records that already have stats in the database when scraping player stats"),
    daily_mid_season_update: bool = typer.Option(False, "--daily_mid_season_update", "-dmsu", help="Run a daily mid-season update to catch stat changes"),
    modified_start_date: Optional[str] = typer.Option(None, "--modified_start_date", "-mod_s", help="Only include records modified after this date"),
    modified_end_date: Optional[str] = typer.Option(None, "--modified_end_date", "-mod_e", help="Only include records modified before this date"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit how many players are processed"),
):
    """Archive player stats to Postgres"""
    
    try:
        year_list = convert_year_string_to_list(years)

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
                limit=limit
            )

    except Exception as e:
        # Full traceback
        import traceback
        traceback.print_exc()

# Make archive the default command
@app.callback(invoke_without_command=True)
def archive_main(ctx: typer.Context):
    """Archive operations"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(archive_stats)