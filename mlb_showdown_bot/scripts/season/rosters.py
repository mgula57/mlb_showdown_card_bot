from typing import Optional, List
from time import sleep

from ...core.mlb_stats_api import MLBStatsAPI, LeagueEnum, RosterTypeEnum
from ...core.card.card_generation import generate_cards as _generate_cards, NormalizedPlayerStats
from ...core.card.showdown_player_card import Set as ShowdownSet

def snapshot_rosters(
    seasons: str, 
    publish_to_database: bool = False, 
    generate_cards: bool = False,
    env: str = 'dev', 
    league_ids: Optional[List[int]] = None,
    showdown_sets: Optional[List[str]] = None
) -> None:
    """Fetch active roster data and snapshot in Postgres DB"""
    from ...core.database.postgres_db import PostgresDB
    is_production = env.lower() == "prod"

    if publish_to_database:
        db = PostgresDB(is_archive=is_production)

    season_list = [int(season.strip()) for season in seasons.split(',')] if seasons else None
    if season_list is None:
        print("Required: Please specify at least one season using the --seasons option (e.g. --seasons 2023,2024)")
        return
    
    if generate_cards and not showdown_sets:
        print("Warning: --generate-cards flag is set but no --showdown-sets specified. Defaulting to all sets.")
        showdown_sets = [s.value for s in ShowdownSet]
    
    # -----------------
    # 1. STORE ROSTER DATA
    # -----------------
    print("Fetching active roster data from MLB API...")
    _mlb_api = MLBStatsAPI(use_persistent_cache=True)
    leagues = league_ids or [LeagueEnum.AL.value, LeagueEnum.NL.value]
    rosters = _mlb_api.fetch_rosters_by_season(seasons=season_list, league_ids=leagues, roster_type=RosterTypeEnum.MAN_40.value)
    print(f"Fetched roster data for {len(rosters)} players.")

    print("Snapshotting roster data in Postgres DB...")
    if publish_to_database:
        db.store_rosters(rosters)
        print("✅ Roster snapshot completed.")

    # -----------------
    # 2. OPTIONAL: PROCESS CARDS 
    # -----------------

    if generate_cards:

        # CHUNK PLAYERS INTO BATCHES OF 10 FOR CARD GENERATION
        print("Generating cards for rostered players...")
        player_ids = [roster['player_id'] for roster in rosters]
        player_id_chunks = [player_ids[i:i + 10] for i in range(0, len(player_ids), 10)]
        
        for idx, chunk in enumerate(player_id_chunks[:2]):  # Limit to first 3 chunks for testing
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
                **card_settings
            )
            sleep(1)  # Add a delay between chunks to avoid overwhelming the API

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
            


    