import math
from pydantic import BaseModel
from enum import Enum
from math import isnan
import pandas as pd
import os, json
from pathlib import Path
from rich.progress import track

try:
    from .showdown_player_card import ShowdownPlayerCard, Set, Era, Speed, PlayerType, Chart, ChartCategory, Expansion, PlayerSubType, Points, Position
    from .postgres_db import PostgresDB, PlayerArchive
except ImportError:
    from showdown_player_card import ShowdownPlayerCard, Set, Era, Speed, PlayerType, Chart, ChartCategory, Expansion, PlayerSubType, Points, Position
    from postgres_db import PostgresDB, PlayerArchive

# ------------------------------
# WOTC PLAYER CARD
# ------------------------------
    
class WotcDataSource(str, Enum):
    GSHEET = 'GSHEET'
    FILE = 'FILE'

class WotcPlayerCard(ShowdownPlayerCard):
    """Expansion of the ShowdownPlayerCard class to include WOTC specific fields"""

    points_estimated_breakdown: Points = Points()
    points_estimated: int = 0

    def __init__(self, data_source: WotcDataSource = WotcDataSource.FILE, update_projections:bool = False, stats:dict = None, **data):
        match data_source:
            case WotcDataSource.FILE:
                data['disable_running_card'] = True
                if data.get('stats', None) is None:
                    data['stats'] = stats or {}
                super().__init__(**data)

            case WotcDataSource.GSHEET:
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
                match data.get('position1', None):
                    case 'STARTER': player_sub_type = PlayerSubType.STARTING_PITCHER
                    case 'RELIEVER' | 'CLOSER': player_sub_type = PlayerSubType.RELIEF_PITCHER
                    case _: player_sub_type = PlayerSubType.POSITION_PLAYER

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
                categories_as_str = ['so','pu','gb','fb','bb','1b','1b+','2b','3b','hr'] if set == Set._2000 else ['pu','so','gb','fb','bb','1b','1b+','2b','3b','hr']
                categories = [ChartCategory(cat.upper()) for cat in categories_as_str]
                chart_values = {ChartCategory(k.upper()): (v if v < 20 else 0) for k,v in data.items() if k in categories_as_str}
                # COVERT TO LIST OF RESULTS
                chart_results = [[cat] * chart_values.get(cat, 0) for cat in categories if chart_values.get(cat, 0) > 0]
                chart_results = [item for sublist in chart_results for item in sublist] # FLATTEN LIST
                if set.has_expanded_chart:
                    # ADD 21+ RESULTS
                    cats_above_20_dict: dict[str] = {ChartCategory(cat.upper()): data.get(cat, 0) for cat in ['bb','1b','1b+','2b','3b','hr'] if data.get(cat, 0) > 20}
                    cats_above_20_dict = {k: v for k, v in sorted(cats_above_20_dict.items(), key=lambda item: item[1])}
                    last_category = chart_results[-1] if len(chart_results) > 0 else None
                    # GET FIRST VALUE IN DICT 
                    if len(cats_above_20_dict) == 0:
                        chart_results += [chart_results[-1]] * 10
                    else:
                        # FILL IN ANY DIFFERENCES WITH THE LAST CATEGORY
                        categories_w_above_20_values = list(cats_above_20_dict.keys())
                        first_cat = categories_w_above_20_values[0]
                        first_cat_start = cats_above_20_dict.get(first_cat, 0)
                        if first_cat_start > 21:
                            chart_results += [last_category] * (first_cat_start - 21)
                        for category, start in cats_above_20_dict.items():
                            # CHECK NEXT CATEGORY'S START VALUE
                            next_category = categories_w_above_20_values[categories_w_above_20_values.index(category) + 1] if category != categories_w_above_20_values[-1] else None
                            next_category_start = cats_above_20_dict.get(next_category, 0) if next_category else 30
                            
                            chart_results += [category] * (next_category_start - start)

                        if len(chart_results) < 30:
                            chart_results += [chart_results[-1]] * (30 - len(chart_results))
                opponent_chart = set.opponent_chart(player_sub_type=player_sub_type, era=Era.STEROID)
                chart = Chart(
                    is_pitcher = player_type.is_pitcher,
                    set = set.value,
                    era = Era.STEROID.value,
                    is_expanded = set.has_expanded_chart,
                    command = data['command'],
                    outs = data['outs'],
                    opponent = opponent_chart,
                    convert_from_wotc = chart_results,
                )
                data['chart'] = chart
                data['stats'] = {'type': player_type.value}
                
                # INIT WITH DATA
                super().__init__(**data)

                self.stats = self.add_estimates_to_stats(stats=stats) if stats else {}
                self.positions_and_defense_string = self.positions_and_defense_as_string(is_horizontal=True)

                stats_per_400_pa = self.stats_per_n_pa(plate_appearances=400, stats=self.stats)
                self.chart.stats_per_400_pa = stats_per_400_pa
                self.chart.generate_accuracy_rating()

        if update_projections and len(self.stats) > 0:
            self.update_projections()

    def update_projections(self) -> None:
        """Update projections based on current Showdown Bot weights"""

        # UPDATE OPPONENT CHART
        opponent_chart = self.set.opponent_chart(player_sub_type=self.player_sub_type, era=Era.STEROID)
        self.chart.opponent = opponent_chart
        
        # ADD PROJECTIONS
        chart_results_per_400_pa = self.chart.projected_stats_per_400_pa
        self.projected = self.projected_statline(stats_per_400_pa=chart_results_per_400_pa, command=self.chart.command, pa=self.stats.get('PA', 650))
        self.accolades = self.parse_accolades()

        # ADD ESTIMATED PTS
        self.points_estimated_breakdown = self.calculate_points(projected=self.projected, positions_and_defense=self.positions_and_defense, speed_or_ip=self.ip if self.is_pitcher else self.speed.speed)
        self.points_estimated = self.points_estimated_breakdown.total_points

# ------------------------------
# WOTC PLAYER CARDS
# ------------------------------
class WotcPlayerCardSet(BaseModel):
    """Set of WOTC Player Cards"""
    
    source: WotcDataSource = WotcDataSource.GSHEET
    sets: list[Set] = [s for s in Set if s.is_wotc]
    expansions: list[Expansion] = [e for e in Expansion]
    player_types: list[PlayerType] = [t for t in PlayerType]
    local_file_path: str = os.path.join(Path(os.path.dirname(__file__)), 'data', 'wotc_player_card_set.json')
    cards: dict[str, WotcPlayerCard] = {}

    def __init__(self, **data):
        
        super().__init__(**data)
        num_cards = len(data.get('cards', []))
        match self.source:
            case WotcDataSource.FILE:
                self.reload_from_file_export()
            case WotcDataSource.GSHEET:
                # IF CARDS ARE EMPTY, LOAD FROM GOOGLE SHEET
                if num_cards == 0:
                    self.load_cards_from_gsheet()

    def reload_from_file_export(self) -> None:
        """Load dataset from existing file. Update projections based on current Showdown Bot weightings."""

        # LOAD FROM FILE
        file = open(self.local_file_path.replace('wotc_player_card_set', 'wotc_player_card_set_prod'), 'r')
        data = json.loads(file.read())

        cards: dict[str, dict] = data.get('cards', None)
        if cards is None:
            raise Exception(f'Error, no cards found in {self.local_file_path}')

        # FILTERS
        expansion_values = [e.value for e in self.expansions]
        set_values = [int(s.year) for s in self.sets]
        player_type_values = [t.value for t in self.player_types]

        updated_cards: dict[str, WotcPlayerCard] = {}
        for id, card_data in track(cards.items(), description="Converting WOTC Player Cards"):
            
            # FILTER DATASET IF APPLICABLE
            is_in_set_filter = int(card_data.get('set', 'n/a')) in set_values
            is_in_expansion_filter = card_data.get('image', {}).get('expansion', 'n/a') in expansion_values
            is_in_player_type_filter = card_data.get('player_type') in player_type_values

            if is_in_set_filter and is_in_expansion_filter and is_in_player_type_filter:

                card = WotcPlayerCard(data_source=self.source, update_projections=True, **card_data)
                updated_cards[id] = card

        self.cards = updated_cards

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

        # MAKE LIST OF ARCHIVE IDS TO IGNORE STATS FOR. DUE TO WOTC USING MULTIPLE YEARS FOR THEM.
        ignore_stats: list[str] = [
            '2000-mcgwima01' # MARK MCGWIRE 2001
        ]

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
            if (expansion == Expansion.BS.value or ss_year) and archive_id not in ignore_stats:
                player_archive = next((p for p in real_player_stats_archive if p.id == archive_id), None)
                if player_archive:
                    stats = player_archive.stats
                if not player_archive:
                    print(f'No stats found for {archive_id}')

            card = WotcPlayerCard(data_source=WotcDataSource.GSHEET, update_projections=True, stats=stats, **gsheet_row)
            converted_cards[card.id] = card
        
        self.cards = converted_cards
        return

    def export_to_local_file(self, formats: list[str] = ['csv', 'json']) -> None:
        """Export cards locally to files: json and csv"""
        
        # JSON
        if 'json' in formats:
            json_data = self.model_dump(mode="json", exclude_none=True)
            with open(self.local_file_path, "w") as json_file:
                json.dump(json_data, json_file, indent=4, ensure_ascii=False)

        # CSV
        if 'csv' in formats:
            dict_list: list[dict] = []
            for card in self.cards.values():
                card_dict = card.as_json()
                # EXCLUDE ACCOLADES
                # THEY CAUSE TABLE IMPORT ISSUES
                card_dict['stats'].pop('accolades', None)
                dict_list.append(card_dict)
            df = pd.json_normalize(dict_list, sep='.', max_level=None)
            df.to_csv(self.local_file_path.replace('.json', '.csv'))
        
        print("Exported WOTC Player Cards to local file.")

    @property
    def num_cards(self) -> int:
        return len(self.cards)
    
    def get_card_by_id(self, id:str) -> WotcPlayerCard:
        """Return card by id"""
        return self.cards.get(id, None)