import math
from pydantic import BaseModel
from math import isnan
import pandas as pd
import os, json
from pathlib import Path
from rich.progress import track

try:
    from .showdown_player_card import ShowdownPlayerCard, Set, Era, Speed, PlayerType, Chart, ChartCategory, Expansion, PlayerSubType
    from .postgres_db import PostgresDB, PlayerArchive
except ImportError:
    from showdown_player_card import ShowdownPlayerCard, Set, Era, Speed, PlayerType, Chart, ChartCategory, Expansion, PlayerSubType
    from postgres_db import PostgresDB, PlayerArchive

# ------------------------------
# WOTC PLAYER CARD
# ------------------------------
class WotcPlayerCard(ShowdownPlayerCard):
    """Expansion of the ShowdownPlayerCard class to include WOTC specific fields"""

    points_estimated: int = 0

    def __init__(self, is_data_from_gsheet:bool = False, stats:dict = None, **data):

        # DATA IS ALREADY CONVERTED
        if not is_data_from_gsheet:
            super().__init__(**data)
            return
        
        # DATA NEEDS TO BE CONFORMED TO SHOWDOWN PLAYER CARD CLASS
        data: dict = {k.lower().replace(' ', '_'): v for k,v in data.items() if type(v) is str or not isnan(v)}

        # DERIVE REQUIRED FIELDS
        set = Set(str(data['set']))
        set_year = int(set.year)
        data['set'] = set
        data['era'] = Era.STEROID.value
        data['set_number'] = str(data['set_number'])
        if data['expansion'] == 'BS':
            data['year'] = str(set_year - 1)
        else:
            ss_year = data.get('ss_year', None)
            data['year'] = str(int(ss_year) if ss_year else set_year)
        data['stats'] = {}
        data['source'] = 'WOTC'
        data['disable_running_card'] = True
        data['is_wotc'] = True
        data['set_year_plus_one'] = True

        # TYPE
        player_type = PlayerType(data['player_type'])
        data['player_type'] = player_type

        # SPEED
        speed = data['speed']
        if speed < set.speed_c_cutoff: letter = 'C'
        elif speed < 18: letter = 'B'
        else: letter = 'A'
        data['speed'] = Speed(speed=speed, letter=letter)

        # POSITIONS
        positions_and_defense: dict[str, int] = {}
        for i in range(1, 4):
            position = data.get(f'position{i}', None)
            if position:
                defense = data.get(f'fielding{i}', 0)
                positions_and_defense[position] = defense
        data['positions_and_defense'] = positions_and_defense

        # ICONS
        icons: list[str] = []
        for i in range(1, 5):
            icon = data.get(f'icon{i}', None)
            if icon:
                icons.append(icon)
        data['icons'] = icons

        # CHART
        possible_above_20_values = [data.get(f, 0) for f in ['2b','3b','hr']]
        dbl_range_start, trpl_range_start, hr_range_start = ( (v if v > 20 else None) for v in possible_above_20_values)
        chart_values = {ChartCategory(k.upper()): (v if v < 20 else 0) for k,v in data.items() if k in ['pu','so','gb','fb','bb','1b','1b+','2b','3b','hr']}
        chart = Chart(
            is_pitcher = player_type.is_pitcher,
            set = set.value,
            is_expanded = set.has_expanded_chart,
            command = data['command'],
            outs = data['outs'],
            values = chart_values,
            dbl_range_start = dbl_range_start, 
            trpl_range_start = trpl_range_start, 
            hr_range_start = hr_range_start
        )
        data['chart'] = chart
        data['stats'] = {'type': player_type.value}
        
        # INIT WITH DATA
        super().__init__(**data)

        self.stats = stats or {}

        # ADD PROJECTIONS
        proj_opponent_chart, proj_my_advantages_per_20, proj_opponent_advantages_per_20 = self.opponent_stats_for_calcs(command=self.chart.command)
        chart_results_per_400_pa = self.chart_to_results_per_400_pa(chart=self.chart, my_advantages_per_20=proj_my_advantages_per_20, opponent_chart=proj_opponent_chart, opponent_advantages_per_20=proj_opponent_advantages_per_20)
        self.projected = self.projected_statline(stats_per_400_pa=chart_results_per_400_pa, command=self.chart.command, pa=self.stats.get('PA', 650))
        self.accolades = self.parse_accolades()

        # ADD ESTIMATED PTS
        self.points_estimated = self.calculate_points(projected=self.projected, positions_and_defense=self.positions_and_defense, speed_or_ip=self.ip if self.is_pitcher else self.speed.speed).total_points


# ------------------------------
# WOTC PLAYER CARDS
# ------------------------------
class WotcPlayerCardSet(BaseModel):
    """Set of WOTC Player Cards"""
    
    sets: list[Set] = [s for s in Set if s.is_wotc]
    expansions: list[Expansion] = [e for e in Expansion]
    player_types: list[PlayerType] = [t for t in PlayerType]
    local_file_path: str = os.path.join(Path(os.path.dirname(__file__)), 'data', 'wotc_player_card_set.json')
    cards: dict[str, WotcPlayerCard] = {}

    def __init__(self, **data):
        
        super().__init__(**data)

        # IF CARDS IF EMPTY, LOAD FROM GOOGLE SHEET
        if len(data.get('cards', [])) == 0:
            self.load_cards_from_gsheet()

    def load_cards_from_gsheet(self) -> None:
        """Load cards from google sheet and return as list of WotcPlayerCard objects."""

        # LOAD CSV WITH ORIGINAL CARD DATA
        sheet_link = 'https://docs.google.com/spreadsheets/d/1WCrgXHIH0-amVd5pDPbhoMVnlhLuo1hU620lYCnh0VQ/edit#gid=0'
        export_url = sheet_link.replace('/edit#gid=', '/export?format=csv&gid=')
        df_wotc_cards = pd.read_csv(export_url)

        # FILTER PANDAS FOR CARDS IN SETS AND EXPANSIONS LIST
        expansion_values = [e.value for e in self.expansions]
        set_values = [int(s.year) for s in self.sets]
        player_type_values = [t.value for t in self.player_types]
        df_wotc_cards = df_wotc_cards[df_wotc_cards['Set'].isin(set_values) & df_wotc_cards['Expansion'].isin(expansion_values) & df_wotc_cards['Player Type'].isin(player_type_values)]

        # GET DISTINCT VALUES FROM THE 'SS YEAR' COLUMN
        ss_year_values = [int(s) for s in df_wotc_cards['SS Year'].unique() if math.isnan(s) == False]

        # CONVERT TO LIST OF DICTS
        list_of_dicts: list[dict[str, any]] = df_wotc_cards.to_dict(orient='records')

        # LOAD PLAYER STATS FROM ARCHIVE DB
        postgres_db = PostgresDB(is_archive=True)
        year_list = [y-1 for y in set_values] + ss_year_values
        real_player_stats_archive: list[PlayerArchive] = postgres_db.fetch_all_stats_from_archive(year_list=year_list, exclude_records_with_stats=False)

        # CREATE LIST OF SHOWDOWN OBJECTS
        converted_cards: list[WotcPlayerCard] = {}
        for gsheet_row in track(list_of_dicts, description="Converting WOTC Player Cards"):

            if int(gsheet_row.get('Set', 0)) < 2002 and gsheet_row.get('Expansion') == 'PM':
                continue

            # ADD STATS FROM ARCHIVE
            bref_id = gsheet_row.get('BRef Id', '')
            expansion = gsheet_row.get('Expansion', 'N/A')
            ss_year = None if math.isnan(gsheet_row.get('SS Year', 0)) else int(gsheet_row.get('SS Year', 0))
            set_year = int(gsheet_row.get('Set', 2000)) - 1
            year = ss_year or set_year
            archive_id = f'{year}-{bref_id}'
            stats: dict = None
            if expansion == Expansion.BS.value or ss_year:
                player_archive = next((p for p in real_player_stats_archive if p.id == archive_id), None)
                if player_archive:
                    stats = player_archive.stats

            card = WotcPlayerCard(is_data_from_gsheet=True, stats=stats, **gsheet_row)
            converted_cards[card.id] = card
        
        self.cards = converted_cards
        return

    def export_to_local_file(self) -> None:
        """Export cards locally to files: json and csv"""
        
        # JSON
        json_data = self.model_dump(mode="json", exclude_none=True)
        with open(self.local_file_path, "w") as json_file:
            json.dump(json_data, json_file, indent=4, ensure_ascii=False)

        # CSV
        dict_list = [card.as_json() for card in self.cards.values()]
        df = pd.json_normalize(dict_list, sep='.', max_level=None)
        df.to_csv(self.local_file_path.replace('.json', '.csv'))
        
        print("Exported WOTC Player Cards to local file.")

    @property
    def num_cards(self) -> int:
        return len(self.cards)
    
    def get_card_by_id(self, id:str) -> WotcPlayerCard:
        """Return card by id"""
        return self.cards.get(id, None)