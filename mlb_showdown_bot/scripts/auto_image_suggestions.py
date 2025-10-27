import os
from datetime import datetime
from prettytable import PrettyTable
from typing import Optional
from pprint import pprint

from mlb_showdown_bot.core.database.postgres_db import PostgresDB, PlayerArchive

# ===================================================
# HELPER FUNCTIONS
# ===================================================

def _fetch_image_file_list() -> list[str]:
    file_names = []
    path = os.environ.get('AUTO_IMAGE_PATH', None)
    if not path:
        return []
    
    for _, _, files in os.walk(path):
        for name in files:
            file_names.append(name)
    return file_names

def _fetch_player_data(
    year_start: Optional[int] = None, 
    year_end: Optional[int] = None,
    limit: Optional[int] = None,
    sort_field: str = 'bWAR',
    hof: bool = False,
    mvp: bool = False,
    cya: bool = False,
    gold_glove: bool = False,
    team: Optional[str] = None
) -> list[PlayerArchive]:
    """Fetches player data from the stats archive.

    Args:
        year_start (Optional[int]): Optional start year filter.
        year_end (Optional[int]): Optional end year filter.

    Returns:
      List of PlayerArchive objects
    """

    # CONNECT TO DB
    db = PostgresDB(is_archive=True)
    if db.connection is None:
        print("ERROR: NO CONNECTION TO DB")
        return []

    # LIST OF YEAR INTS FROM 1900 TO NOW
    # GET CURRENT YEAR
    current_year = datetime.now().year
    year_list = list(range(1884, current_year + 1))
    
    # FILTER OUT YEARS BETWEEN YEAR START AND YEAR END ARGS
    if year_start is not None:
        year_list = [year for year in year_list if year >= year_start]
    if year_end is not None:
        year_list = [year for year in year_list if year <= year_end]

    # DEFINE FILTERS TO PASS TO DB
    filters = []
    if team: filters.append(('team_id', team.upper()))

    sort_sql = f"(case when length(coalesce(trim(stats->>'{sort_field}'), '')) = 0 then 0.0 else (stats->>'{sort_field}')::float end)"
    player_data = db.fetch_all_stats_from_archive(
        year_list=year_list, 
        filters=filters,
        limit=limit, 
        order_by=sort_sql, 
        exclude_records_with_stats=False
    )

    return player_data

# ===================================================
# MAIN FUNCTION
# ===================================================

def generate_auto_image_suggestions(
    player_subtype: Optional[str] = None,
    hof: bool = False,
    mvp: bool = False,
    cya: bool = False,
    gold_glove: bool = False,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    limit: Optional[int] = None,
    team: Optional[str] = None,
    year_threshold: Optional[int] = None,
    sort_field: str = 'bWAR'
):
    """Handles generating and printing list of player seasons without an image
    
    Args:
        player_subtype (Optional[str]): Optional player subtype filter (POSITION_PLAYER, STARTING_PITCHER, RELIEF_PITCHER)
        hof (bool): Only Hall of Fame Players
        mvp (bool): Only MVPs
        cya (bool): Only CYAs
        gold_glove (bool): Only Gold Glove Winners
        year_start (Optional[int]): Optional start year filter
        year_end (Optional[int]): Optional end year filter
        limit (Optional[int]): Optional limit on number of players to fetch
        team (Optional[str]): Optional team filter (e.g., NYY, LAD)
        year_threshold (Optional[int]): Optional year threshold. Only includes images that are <= the threshold
        sort_field (str): Field to sort players by (default: 'bWAR')

    Returns:
        None
    """

    # GRAB DATA FROM BREF
    image_list = _fetch_image_file_list()
    player_data = _fetch_player_data(
        year_start=year_start,
        year_end=year_end,
        limit=limit,
        sort_field=sort_field,
        team=team,
        hof=hof,
        mvp=mvp,
        cya=cya,
        gold_glove=gold_glove
    )

    if len(player_data) == 0:
        print("NO PLAYERS FOUND")
        return

    player_tbl = PrettyTable(field_names=['Player', 'Team', 'Year', 'Position', 'G', 'GS', 'bWAR', 'OPS', 'ERA', 'HOF', 'MVP', 'CYA'])

    for player in player_data:
        
        bwar = player.stats.get('bWAR', 0)
        is_hof = player.stats.get('is_hof', False)
        awards = player.stats.get('award_summary', '').split(',')
        games = str(player.g)
        games_started = str(player.gs or '-')
        era = str(player.stats.get('earned_run_avg', '-'))
        ops = str(player.stats.get('onbase_plus_slugging', '-')).replace('0.','.')
        mvp_str = 'X' if 'MVP-1' in awards else ''
        cy_str = 'X' if 'CYA-1' in awards else ''
        hof_str = 'X' if is_hof else ''

        # SKIP IF PLAYER IS IN IMAGE LIST
        images = [image for image in image_list \
                  if player.bref_id in image \
                    and f'({player.team_id})' in image \
                    and (abs(int(image.split('-')[1]) - player.year) <= year_threshold if year_threshold is not None else True)
                 ]    
        if len(images) > 0:
            continue

        # HOF CHECK
        if hof and not is_hof: continue

        # MVP CHECK
        if mvp and 'MVP-1' not in awards: continue

        # CYA CHECK
        if cya and 'CYA-1' not in awards: continue

        # GG CHECK
        if gold_glove and 'GG' not in awards: continue

        if player_subtype and player_subtype.upper() != player.player_subtype: continue

        # PRINT PLAYER'S NAME, TEAM, AND YEAR
        player_tbl.add_row([
            player.name,
            player.team_id,
            player.year,
            ",".join(player.primary_positions),
            games,
            games_started,
            bwar,
            ops,
            era,
            hof_str,
            mvp_str,
            cy_str
        ])

    print(player_tbl)
