from firebase_admin import db
import typer
from typing import Optional
from datetime import datetime, timedelta, timezone
import unidecode
import time
from prettytable import PrettyTable

from ...core.mlb_stats_api import MLBStatsAPI
from ...core.mlb_stats_api.models.leagues.league import LeagueListEnum

# Import business logic
from ...core.archive.player_stats_archive import PlayerStatsArchive, PostgresDB
from ...core.database.classes import WbcShowdownCardRecord, FangraphsLeaderboardRecord
from ...core.card.utils.shared_functions import convert_year_string_to_list
from ...core.card.showdown_player_card import Edition, SpecialEdition, StatsPeriod, WBCTeam, Position, ShowdownPlayerCard, PlayerType, StatsPeriodType
from ...core.data.replacement_season_averages import get_replacement_hitting_avgs, get_replacement_pitching_avgs, build_replacement_level_stats_for_card
from ...core.card.stats.normalized_player_stats import NormalizedPlayerStats, PlayerStatsNormalizer

app = typer.Typer()

_mlb_api = MLBStatsAPI(use_persistent_cache=True)

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
    is_full_refresh: bool = typer.Option(False, "--is_full_refresh", "-f", help="Is this a full refresh of player cards"),
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
            player_stats_archive = PlayerStatsArchive(years=year_list, is_snapshot=False, player_ids=parsed_player_id_list)
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
                ignore_minimums=ignore_minimums,
                player_id_list=parsed_player_id_list
            )

        if run_auto_image_suggestions:
            db = PostgresDB(is_archive=is_production)
            db.build_auto_image_table(refresh_explore=refresh_explore, drop_existing=drop_existing)

        if not run_player_cards and refresh_explore:
            print("Refreshing Explore materialized views...")
            db = PostgresDB(is_archive=is_production)
            db.refresh_explore_views(drop_existing=drop_existing, is_full_refresh=is_full_refresh)

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

# -------------------------------
# MARK: - Fangraphs
# -------------------------------
@app.command("store_fielding_stats")
def store_fielding_stats_in_db():
    """Fetch fielding stats from Fangraphs and store in Postgres DB"""
    from ...core.fangraphs.client import FangraphsAPIClient
    from ...core.archive.player_stats_archive import PostgresDB

    print("Fetching fielding stats from Fangraphs...")
    fg_api = FangraphsAPIClient()
    df = fg_api.fetch_leaderboard_stats(season=2025, position="LF", fangraphs_player_ids=[])

@app.command("store_leaderboard_stats_fangraphs")
def store_leaderboard_stats_fangraphs(
    league: str = typer.Option("NPB", "--league", "-l", help="League to fetch stats for (e.g., MLB, NPB, KBO)"),
    season: int = typer.Option(2025, "--season", "-s", help="Season year to fetch NPB stats for"),
    types: str = typer.Option("bat,pit", "--types", "-t", help="Comma-separated list of stat types to fetch (e.g., 'bat,pit')"),
):
    """Fetch NPB data from Fangraphs and store in Postgres DB"""
    from ...core.fangraphs.client import FangraphsAPIClient
    from ...core.archive.player_stats_archive import PostgresDB
    
    print(f"Fetching {league} stats from Fangraphs...")
    db = PostgresDB()
    fg_api = FangraphsAPIClient()
    for type in types.split(","):
        data = fg_api.fetch_leaderboard_stats(stats_period=StatsPeriod(year=season), stat_type=type, league=league, fangraphs_player_ids=[])  
        db.store_league_fangraphs_leaderboard_stats(league=league, stat_type=type, data=data)

# -------------------------------
# MARK: - WBC
# -------------------------------
@app.command("store_wbc_data")
def store_wbc_data(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run the command in"),
    run_rosters: bool = typer.Option(False, "--run_rosters", "-r", help="Whether to fetch and store WBC roster data"),
    run_cards: bool = typer.Option(False, "--run_cards", "-c", help="Whether to generate showdown cards for WBC players after storing data"),
    seasons: str = typer.Option(None, "--seasons", "-s", help="Which WBC season(s) to include when fetching card data, comma-separated (e.g. '2006,2009,2013'). If not provided, will include all seasons."),
    sets: str = typer.Option("CLASSIC,EXPANDED,2000,2001,2002,2003,2004,2005", "--showdown_sets", "-cs", help="Showdown Set(s) to use when fetching card data, comma-separated.")
):
    """Fetch all WBC players by year and store in database"""
    db = PostgresDB(is_archive=env.lower() == "prod")
    seasons_list = convert_year_string_to_list(seasons) if seasons else None
    showdown_sets_list = [s.strip() for s in sets.split(",")] if sets else None
    
    if run_rosters:
        print("Fetching WBC roster data and storing in database...")
        wbc_players = _mlb_api.fetch_wbc_players_by_year(seasons=seasons_list)
        print(f"Fetched {len(wbc_players)} WBC players across all years.")
        
        # Initialize database connection
        db.store_wbc_roster_history(wbc_players)
        print("WBC roster history stored in database successfully.")

    if run_cards:
        print("Generating showdown cards for WBC players...")
        wbc_rosters = db.fetch_wbc_rosters_and_mlb_card_matches(seasons=seasons_list, showdown_sets=showdown_sets_list)

        missing_cards = len([record for record in wbc_rosters if record.card_data is None])
        total_records = len(wbc_rosters)
        print(f"Found {total_records} WBC roster records with {missing_cards} missing card matches based on the specified seasons and showdown sets.")

        if total_records == 0:
            print("No WBC roster records found for the specified seasons and showdown sets. Please check your filters and try again.")
            return
        
        # Get stats for other leagues for players missing card matches to try to fill in gaps
        all_fangraph_stats: list[FangraphsLeaderboardRecord] = []
        for league in ["NPB", "KBO"]:
            for stat_type in ["bat", "pit"]:
                stats = db.fetch_league_fangraphs_leaderboard_stats(league=league, stat_type=stat_type, seasons=[season - 1 for season in seasons_list] if seasons_list else None) # Fetch stats for the season before the WBC season(s) to try to fill in gaps for players who may have played in those leagues before or after the WBC
                all_fangraph_stats.extend(stats)
        
        # Replacement stats
        replacement_stat_baselines = {
            'HITTER': get_replacement_hitting_avgs(year=2025), # TODO: Make this dynamic based on the WBC season(s) being processed, but for now just use 2025 as a baseline since it's the most recent season and should be somewhat representative of current player performance levels
            'PITCHER': get_replacement_pitching_avgs(year=2025)
        }

        # Iterate through cards and adjust or fill in card data as needed, then store in database
        roster_progress_rows: list[dict] = [
            {
                "name": record.name,
                "wbc_season": record.wbc_season,
                "showdown_set": record.showdown_set.value,
                "processed": "⬜",
                "stat_source": "PENDING",
            }
            for record in wbc_rosters
        ]

        for record_index, record in enumerate(wbc_rosters):

            year = record.wbc_season - 1

            # Wipe card if games played was < 3
            if record.card_data and record.card_data.stats.get('G', 0) < 3:
                record.card_data = None

            # Card Exists from MLB Season - Update theming
            if record.card_data:
                # Adjust card settings to add WBC edition and theming
                record.card_data.wbc_team = record.wbc_team
                record.card_data.wbc_year = record.wbc_season
                record.card_data.image.apply_wbc_team_theming(record.wbc_team, record.wbc_season)
                record.stat_source = "MLB"
                roster_progress_rows[record_index]["processed"] = "✅"
                roster_progress_rows[record_index]["stat_source"] = record.stat_source
                continue

            # ----------------------
            # 1. NPB and KBO
            # ----------------------
            player_stats = next((
                stats for stats in all_fangraph_stats 
                if stats.name_safe_for_matching == record.name_safe_for_matching and stats.player_type_for_matching == record.player_type_for_matching \
                    and stats.is_pitcher_stat_type == (record.player_type_for_matching.is_pitcher) and stats.season == year
            ), None)
            if player_stats:
                normalized_player_stats = PlayerStatsNormalizer.from_fangraphs_leaderboard_data(player_stats.stats, mlb_id=record.mlb_id)
                stats = normalized_player_stats.as_dict()
                record.card_data = ShowdownPlayerCard(
                    name=record.name_safe_for_matching.title(), # Use the name from the WBC roster
                    year=str(year),
                    set=record.showdown_set,
                    wbc_team=record.wbc_team,
                    wbc_year=record.wbc_season,
                    league=player_stats.league,
                    image={
                        "edition": Edition.WBC if record.wbc_team else Edition.NONE,
                        "special_edition": SpecialEdition.WBC,
                    },
                    era="DYNAMIC",
                    stats_period=StatsPeriod(year=str(year), type=StatsPeriodType.REGULAR_SEASON),
                    stats=stats,
                )
                record.card_data.warnings.append(f"This card is populated from the player's performance in the {player_stats.league} league, not MLB. Stats may not be directly comparable to MLB performance.")
                record.stat_source = player_stats.league
                roster_progress_rows[record_index]["processed"] = "✅"
                roster_progress_rows[record_index]["stat_source"] = record.stat_source
                continue

            # ----------------------
            # 2. Minor Leagues
            # ----------------------
            stats_period = StatsPeriod(year=str(year), type=StatsPeriodType.REGULAR_SEASON)
            mlb_stats_player = _mlb_api.people.get_player(record.mlb_id, stats_period=stats_period, include_stats=True, league_list=LeagueListEnum.MILB_FULL)
            if mlb_stats_player and mlb_stats_player.stats:
                print(f"Found minor league stats for WBC player {record.name} (BREF ID: {record.bref_id}), which may help fill in gaps for card data.")
                normalized_player_stats = PlayerStatsNormalizer.from_mlb_api(player=mlb_stats_player, stats_period=stats_period)
                stats = normalized_player_stats.as_dict()
                record.card_data = ShowdownPlayerCard(
                    name=record.name_safe_for_matching.title(), # Use the name from the WBC roster
                    year=str(year),
                    set=record.showdown_set,
                    wbc_team=record.wbc_team,
                    wbc_year=record.wbc_season,
                    league="MILB",
                    image={
                        "edition": Edition.WBC if record.wbc_team else Edition.NONE,
                        "special_edition": SpecialEdition.WBC,
                    },
                    era="DYNAMIC",
                    stats_period=stats_period,
                    stats=stats,
                )
                record.card_data.warnings.append(f"This card is populated from the player's performance in the minor leagues, not MLB. Stats may not be directly comparable to MLB performance.")
                record.stat_source = "MILB"
                roster_progress_rows[record_index]["processed"] = "✅"
                roster_progress_rows[record_index]["stat_source"] = record.stat_source
                continue

            # ----------------------
            # Last: Fill with replacement card data
            # ----------------------
            
            try: showdown_position = Position(record.position.upper())
            except: showdown_position = None
            replacement_stat_baseline = replacement_stat_baselines.get(record.player_type_for_matching.name, {}).copy()
            replacement_stats = build_replacement_level_stats_for_card(year=year, player_type=record.player_type_for_matching, positions=[showdown_position], original_stats=replacement_stat_baseline)
            replacement_stats['name'] = record.name
            replacement_stats['team'] = 'MLB'
            record.card_data = ShowdownPlayerCard(
                name=record.name_safe_for_matching.title(), # Use the name from the WBC roster, but convert it to title case for better display on the card
                year=str(record.wbc_season - 1),
                set=record.showdown_set,
                wbc_team=record.wbc_team,
                wbc_year=record.wbc_season,
                image={
                    "edition": Edition.WBC if record.wbc_team else Edition.NONE,
                    "special_edition": SpecialEdition.WBC,
                },
                era="DYNAMIC",
                stats_period=StatsPeriod(year=str(year), type=StatsPeriodType.REPLACEMENT),
                stats=replacement_stats,
            )
            record.card_data.warnings.append(f"This player does not have a {year} Showdown card. A replacement level card has been generated based on their position.")
            record.stat_source = "REPLACEMENT"
            roster_progress_rows[record_index]["processed"] = "✅"
            roster_progress_rows[record_index]["stat_source"] = record.stat_source
            continue

        progress_table = PrettyTable()
        progress_table.field_names = ["Player", "WBC Season", "Set", "Looped", "Stat Source"]
        for row in roster_progress_rows:
            progress_table.add_row([
                row["name"],
                row["wbc_season"],
                row["showdown_set"],
                row["processed"],
                row["stat_source"],
            ])

        print("\nWBC Roster Processing Summary")
        print(progress_table)
                
        # Store updated records in database
        db.build_wbc_card_table(wbc_rosters)
        print("Showdown cards for WBC players stored in database successfully.")

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