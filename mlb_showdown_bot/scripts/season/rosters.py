from typing import Optional, List
from time import sleep
from datetime import date, timedelta

from ...core.mlb_stats_api import MLBStatsAPI, LeagueEnum, RosterTypeEnum
from ...core.card.card_generation import generate_cards as _generate_cards, NormalizedPlayerStats
from ...core.card.showdown_player_card import Set as ShowdownSet

def snapshot_rosters(
    seasons: str, 
    publish_to_database: bool = False, 
    generate_cards: bool = False,
    env: str = 'dev', 
    league_ids: Optional[List[int]] = None,
    showdown_sets: Optional[List[str]] = None,
    player_ids: Optional[List[int]] = None,
    all_players: bool = False,
    skip_rosters: bool = False,
) -> None:
    """Fetch active roster data and snapshot in Postgres DB

    Args:
        player_ids: Optional list of MLB player IDs to limit card generation to (for testing). 
                    The full roster snapshot is still stored so the latest snapshot stays complete.
        all_players: Generate cards for every player who recorded stats in the season(s),
                     regardless of whether they're currently on a 40-man roster.
                     The roster snapshot itself is unchanged.
        skip_rosters: Skip fetching and storing the roster snapshot. Requires all_players
                      when generating cards, since the roster is otherwise the card pool.
    """
    from ...core.database.postgres_db import PostgresDB
    is_production = env.lower() == "prod"

    if publish_to_database:
        db = PostgresDB(is_archive=is_production)

    season_list = [int(season.strip()) for season in seasons.split(',')] if seasons else None
    if season_list is None:
        print("Required: Please specify at least one season using the --seasons option (e.g. --seasons 2023,2024)")
        return
    
    if skip_rosters and generate_cards and not all_players:
        print("Required: --skip-rosters with --generate-cards needs --all-players, since the roster is otherwise the card pool.")
        return

    if generate_cards and not showdown_sets:
        print("Warning: --generate-cards flag is set but no --showdown-sets specified. Defaulting to all sets.")
        showdown_sets = [s.value for s in ShowdownSet]
    
    # -----------------
    # 1. STORE ROSTER DATA
    # -----------------
    _mlb_api = MLBStatsAPI(use_persistent_cache=True)
    rosters: list[dict] = []
    if skip_rosters:
        print("Skipping roster fetch and snapshot.")
    else:
        print("Fetching active roster data from MLB API...")
        leagues = league_ids or [LeagueEnum.AL.value, LeagueEnum.NL.value]
        rosters = _mlb_api.fetch_rosters_by_season(seasons=season_list, league_ids=leagues, roster_type=RosterTypeEnum.MAN_40.value)
        print(f"Fetched roster data for {len(rosters)} players.")

        if publish_to_database:
            print("Snapshotting roster data in Postgres DB...")
            db.store_rosters(rosters)
            print("✅ Roster snapshot completed.")

    # -----------------
    # 2. OPTIONAL: PROCESS CARDS 
    # -----------------

    if generate_cards:

        # CHUNK PLAYERS INTO BATCHES OF 10 FOR CARD GENERATION
        if all_players:
            # EVERY PLAYER WITH STATS IN ANY OF THE SEASONS, ROSTERED OR NOT
            print("Generating cards for all players with stats...")
            ids_with_stats: set[int] = set()
            for season in season_list:
                ids_with_stats |= _mlb_api.stats.get_player_ids_with_stats(season=season)
            candidate_ids = sorted(ids_with_stats)
        else:
            print("Generating cards for rostered players...")
            candidate_ids = [roster['player_id'] for roster in rosters]

        rostered_player_ids = [pid for pid in candidate_ids if not player_ids or pid in player_ids]
        if player_ids:
            missing_ids = set(player_ids) - set(rostered_player_ids)
            if missing_ids:
                source = "with stats in the given season(s)" if all_players else "on any fetched roster"
                print(f"Warning: player IDs not found {source}: {sorted(missing_ids)}")

        # SKIP PLAYERS WITH NO STATS (ex: 40-man players who haven't appeared in the majors this season).
        # A single bulk call per stat group avoids hydrating and processing them in card generation.
        # Not needed in all_players mode since the candidate pool is already players with stats.
        if len(season_list) == 1 and not all_players:
            ids_with_stats = _mlb_api.stats.get_player_ids_with_stats(season=season_list[0])
            statless_ids = [pid for pid in rostered_player_ids if pid not in ids_with_stats]
            if statless_ids:
                print(f"Skipping {len(statless_ids)} rostered players with no {season_list[0]} stats.")
            rostered_player_ids = [pid for pid in rostered_player_ids if pid in ids_with_stats]
        print(f"Generating cards for {len(rostered_player_ids)} players.")
        player_id_chunks = [rostered_player_ids[i:i + 10] for i in range(0, len(rostered_player_ids), 10)]
        two_way_ids = [roster['player_id'] for roster in rosters if roster.get('position', 'N/A') == 'TWP']

        for idx, chunk in enumerate(player_id_chunks): 
            print(f"Processing chunk {idx + 1}/{len(player_id_chunks)} with player IDs: {chunk}")
            # In a real implementation, you would call the card generation function here
            card_settings = {
                "year": season_list[0],  # Use the first season for card generation; adjust as needed
                "stat_highlights_type": "ALL",
                "stats_period_type": "REGULAR",
            }
            chunk_card_data = _generate_cards(
                player_ids=chunk,
                years=season_list,
                sets=showdown_sets,
                keep_as_py_objects=True,
                inject_bref_ids=True,
                points_change_cutoff_date=date.today() - timedelta(days=7),
                two_way_ids=two_way_ids,
                **card_settings
            )
            sleep(2)  # Add a delay between chunks to avoid overwhelming the API

            # UPLOAD GENERATED CARDS TO DATABASE
            if publish_to_database:
                # UPSERT PLAYER SEASON STATS ROWS
                db_cursor = db.connection.cursor()
                ids_uploaded: set[str] = set()
                for result in chunk_card_data:
                    normalized_stats: NormalizedPlayerStats = result.get("normalized_player_stats", None)
                    if normalized_stats:
                        row = normalized_stats.as_player_season_stats_row()
                        if row["id"] in ids_uploaded:
                            continue
                        db.upsert_player_season_stats_row(
                            cursor=db_cursor,
                            data=row,
                            conflict_strategy="update_all_columns",
                        )
                        ids_uploaded.add(row["id"])
                db_cursor.close()

                # UPLOAD CARD DATA
                chunk_cards = [result["card"] for result in chunk_card_data if result.get("card") is not None]
                db.upload_to_card_data(chunk_cards)
                print(f"✅ Stored {len(chunk_cards)} cards and season stats for chunk {idx + 1}/{len(player_id_chunks)} in database.")
            


    