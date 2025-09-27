import typer, click
from typing import Optional
from pydantic import BaseModel
from pprint import pprint
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

# INTERNAL
from ..core.card.card_generation import *

# SETUP TYPER APP
app = typer.Typer(pretty_exceptions_enable=False)

# -----------------------------------------------------------------------
# MARK: CARD
# -----------------------------------------------------------------------

@app.command()
def card(
        name: str = typer.Option(None, "--name", "-n", help="Player name"),
        year: str = typer.Option(None, "--year", "-y", help="The year of the player"),

        # OVERRIDES
        player_type_override: str = typer.Option(None, "--player_type_override", "-pto", help="Override the card type. Either `Pitcher` or `Hitter`"),
        team_override: str = typer.Option(None, "--team_override", "-tmo", help="Only include stats from a specific team"),

        # SET
        set: str = typer.Option("2000", "--set", "-s", help="The showdown set meta to use (2000-2005)"),
        era: str = typer.Option("DYNAMIC", "--era", "-e", help="The baseball era to use."),
        
        # IMAGE SOURCE
        image_source_url: Optional[str] = typer.Option(None, "--image_source_url", "-url", help="URL link to Player background image"),
        image_source_path: Optional[str] = typer.Option(None, "--image_source_path", "-path", help="Path to Player background image on local machine"),
        
        # IMAGE
        image_output_folder_path: Optional[str] = typer.Option(None, "--image_output_folder_path", "-o_path", help="Path to folder for card image output"),
        expansion: str = typer.Option("BS", "--expansion", "-exp", help="Add optional expansion logo (ex: TD, PR)"),
        edition: str = typer.Option("NONE", "--edition", "-ed", help="Add optional edition (Values: None, Super Season, All-Star Game, Cooperstown Collection, Holiday, Nationality, Rookie Season)"),
        set_num: Optional[str] = typer.Option(None, "--set_num", "-num", help="Assign card a set number"),
        parallel: str = typer.Option("NONE", "--parallel", "-pl", help="Optionally add image parallel design like Rainbow Foil, Black & White, Sparkle, etc."),
        add_border: bool = typer.Option(False, "--add_border", "-bor", help="Optionally add border to player image"),
        dark_mode: bool = typer.Option(False, "--dark_mode", "-dark", help="Optionally toggle dark mode (2022+ sets only)"),
        add_one_to_set_year: bool = typer.Option(False, "--add_one_to_set_year", "-sy", help="Optionally add one to the set year on 04/05 set."),
        hide_team_logo: bool = typer.Option(False, "--hide_team_logo", "-htl", help="Optionally remove all team logos and branding."),
        coloring: str = typer.Option("PRIMARY", "--coloring", "-col", help="Optionally add coloring to the card."),
        stat_highlights_type: str = typer.Option("NONE", "--stat_highlights_type", "-sh", help="Type of stat highlights to use. (CLASSIC, MODERN, ALL)"),
        glow_multiplier: float = typer.Option(1.0, "--glow_multiplier", "-gm", help="Glow/Shadow multiplier for card image"),
        
        # STATS PERIOD
        stats_period_type: str = typer.Option("REGULAR", "--stats_period_type", "-sp", help="Period to use for stats. Allowed options are REGULAR,DATES,POST,SPLIT"),
        start_date: Optional[str] = typer.Option(None, "--start_date", "-start", help="Optional Start Date for stats. Only available post-1900."),
        end_date: Optional[str] = typer.Option(None, "--end_date", "-end", help="Optional End Date for stats. Only available post-1900."),
        split_name: Optional[str] = typer.Option(None, "--split_name", "-spl", help="Create a card using the splits page on baseball reference"),
        
        # CHART
        co_override: Optional[str] = typer.Option(None, "--co_override", "-co", help="Manually select a command/out combination"),
        variable_spd: bool = typer.Option(False, "--variable_spd", "-vs", help="Optionally toggle variable speed (2000 + 2001 sets only)"),
        chart_version: int = typer.Option(1, "--chart_version", "-cv", help="Get alternate chart n away from most accurate"),
        show_year_text: bool = typer.Option(False, "--show_year_text", "-yrt", help="Optionally add separate year text to the image. Applies to 2000-2005 only."),
        nickname_index: Optional[int] = typer.Option(None, "--nickname_index", "-nick", help="Optionally choose a nickname to show for images. Enter a number based on ordering from bref, max is 3"),
        is_wotc: bool = typer.Option(False, "--is_wotc", "-wotc", help="Try loading from WOTC cards."),
        
        # DATABASE/CACHE
        store_in_logs: bool = typer.Option(False, "--store_in_logs", "-store", help="Optionally store card in logs."),
        db_connection: bool = typer.Option(None, "--db_connection", "-dbc", help="Optionally pass a database connection for logs."),
        ignore_showdown_library: bool = typer.Option(False, "--ignore_showdown_library", "-isl", help="Optionally force ignore Showdown Library, will create card live."),
        ignore_cache: bool = typer.Option(False, "--ignore_cache", "-ic", help="Ignore local cache"),
        ignore_archive: bool = typer.Option(False, "--ignore_archive", "-ia", help="Ignore postgres showdown bot archive"),
        disable_cache_cleaning: bool = typer.Option(False, "--disable_cache_cleaning", "-dc", help="Disable removal of cached files after minutes threshold."),
        disable_realtime: bool = typer.Option(False, "--disable_realtime", "-drt", help="Skip query and integration of current days stats from MLB API."),
        
        # TRENDS
        show_historical_points: bool = typer.Option(False, "--show_historical_points", "-his", help="Optionally calculate all historical stats for player. Displays Year and Points in tabular form."),
        season_trend_date_aggregation: Optional[str] = typer.Option(None, "--season_trend_date_aggregation", "-st", help='Optionally calculate season trends for player. Input should be a date aggregation to show (ex: "MONTH", "WEEK", "DAY")'),

        # DISPLAYING CARD
        print_to_cli: bool = typer.Option(True, "--print_to_cli", "-print", help="Show visual representation of card in the CLI"),
        show_image: bool = typer.Option(False, "--show_image", "-show", help="Optionally open the final Player Card Image upon completion"),

        # RANDOM
        randomize: bool = typer.Option(False, "--randomize", "-rand", help="Generate a random player card"),
):
    # FINAL PAYLOAD
    payload: dict = {}

    # PARAMS
    ctx = click.get_current_context()
    params = ctx.params

    # ACTUAL CARD GENERATION
    payload = generate_card(**params)

    return payload

# -----------------------------------------------------------------------
# MARK: ARCHIVE
# -----------------------------------------------------------------------

@app.command()
def archive(
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
    from ..core.archive.player_stats_archive import PlayerStatsArchive
    from ..core.card.utils.shared_functions import convert_year_string_to_list

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


if __name__ == "__main__":
    app()