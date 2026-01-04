import math
from pydantic import BaseModel
from enum import Enum
from math import isnan
import pandas as pd
import os, json
from pathlib import Path
from typing import Optional
from rich.progress import track
from pprint import pprint
import unidecode

# INTERNAL
from ..showdown_player_card import ShowdownPlayerCard, Set, Era, Edition, Speed, \
                                    PlayerType, Chart, ChartCategory, Expansion, PlayerSubType, \
                                    Points, Position, StatsPeriod, StatsPeriodType, ShowdownImage \
                                    , StatHighlightsType
from ...database.postgres_db import PostgresDB, PlayerArchive
from ...card.stats.normalized_player_stats import NormalizedPlayerStats, PlayerStatsNormalizer

# ------------------------------
# WOTC PLAYER CARD
# ------------------------------
    
class WotcDataSource(str, Enum):
    GSHEET = 'GSHEET'
    FILE = 'FILE'

class WotcPlayerCard(ShowdownPlayerCard):
    """Expansion of the ShowdownPlayerCard class to include WOTC specific fields"""

    def __init__(self, data_source: WotcDataSource = WotcDataSource.FILE, update_projections:bool = False, stats:dict = None, stats_period:Optional[StatsPeriod] = None, **data):
        match data_source:
            case WotcDataSource.FILE:
                data['build_on_init'] = False
                if data.get('stats', None) is None:
                    data['stats'] = stats or {}
                super().__init__(**data)

            case WotcDataSource.GSHEET:
                # DATA NEEDS TO BE CONFORMED TO SHOWDOWN PLAYER CARD CLASS
                data: dict = {k.lower().replace(' ', '_'): v for k,v in data.items() if type(v) is str or not isnan(v)}

                # DERIVE REQUIRED FIELDS
                data['name'] = unidecode.unidecode(data['name'])
                set = Set(str(data['set']))
                set_year = int(set.year)
                expansion = Expansion(data['expansion'])
                data['set'] = set
                data['era'] = Era.STEROID.value
                data['set_number'] = f"P{str(data['set_number']).zfill(2)}" if expansion == Expansion.PM else str(data['set_number']).zfill(3)
                data['edition'] = Edition(data['edition']) if data['edition'] in ('SS', 'RS', 'CC', 'ASG', 'PM') else Edition.NONE
                data['source'] = 'WOTC'
                data['build_on_init'] = False
                data['is_wotc'] = True

                bref_id = data.get('bref_id', '')
                if bref_id:
                    data['bref_url'] = f"https://www.baseball-reference.com/players/{bref_id[:1]}/{bref_id}.shtml"
                
                # STATS
                name = (stats or {}).get('name', None)
                if name:
                    stats['name'] = unidecode.unidecode(name)
                data['stats'] = stats or {}

                # IMAGE
                image = ShowdownImage(
                    expansion = expansion,
                    edition= data['edition'],
                    set_year = set_year,
                    set_number = str(data['set_number']),
                    add_one_to_set_year = False,
                    disable_showing_stat_highlights = True
                )
                data['image'] = image

                # TYPE
                player_type = PlayerType(data['player_type'])
                data['player_type'] = player_type
                match data.get('position1', None):
                    case 'STARTER': player_sub_type = PlayerSubType.STARTING_PITCHER
                    case 'RELIEVER' | 'CLOSER': player_sub_type = PlayerSubType.RELIEF_PITCHER
                    case _: player_sub_type = PlayerSubType.POSITION_PLAYER
                data['player_sub_type'] = player_sub_type

                # SPEED
                speed = data['speed']
                if speed < set.speed_c_cutoff: letter = 'C'
                elif speed < 18: letter = 'B'
                else: letter = 'A'
                data['speed'] = Speed(speed=speed, letter=letter)

                # POSITIONS
                positions_and_defense: dict[Position, int] = {}
                for i in range(1, 4):
                    position = data.get(f'position{i}', None)
                    if position:
                        defense = data.get(f'fielding{i}', 0)
                        positions_and_defense[Position(position)] = defense
                data['positions_and_defense'] = positions_and_defense

                # ICONS
                icons: list[str] = []
                for i in range(1, 5):
                    icon = data.get(f'icon{i}', None)
                    if icon:
                        icons.append(icon)
                data['icons'] = icons

                stats_period = stats_period or StatsPeriod(
                    period_type=StatsPeriodType.REGULAR_SEASON,
                    year=data['year'],
                    disable_display_text_on_card=True,
                )

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
                opponent_chart = set.wotc_baseline_chart(player_type.opponent_type, my_type=player_sub_type, adjust_for_simulation_accuracy=True)
                chart = Chart(
                    is_pitcher = player_type.is_pitcher,
                    player_subtype = player_sub_type.value,
                    set = set.value,
                    era_year_list=stats_period.year_list,
                    era = Era.STEROID.value,
                    is_expanded = set.has_expanded_chart,
                    command = data['command'],
                    outs = data['outs'],
                    opponent = opponent_chart,
                    wotc_chart_results = chart_results,
                )
                data['chart'] = chart

                data['stats_period'] = stats_period
                
                # INIT WITH DATA
                super().__init__(**data)

                self.chart.is_command_out_anomaly = self.chart.is_chart_an_outlier
                self.image.color_primary = self._team_color_rgb_str()
                self.image.color_secondary = self._team_color_rgb_str(is_secondary_color=True)

                self.stats = self.clean_stats(self.stats) if stats else {}

                game_logs: list[dict] = self.stats.get(self.stats_period.type.stats_dict_key or 'n/a', [])
                # ADD LOGS AS STATS IN PERIOD
                self.stats_period.add_stats_from_game_logs(game_logs=game_logs, is_pitcher=self.is_pitcher, team_override=self.team_override)

                if self.stats_period.stats:
                    full_season_stats_used_for_stats_period = {k: v for k, v in self.stats.items() if k in ['IF/FB', 'GO/AO',]}
                    self.stats_period.stats.update(full_season_stats_used_for_stats_period)
                    self.stats_period.stats = self.clean_stats(stats=self.stats_period.stats)

                self.positions_and_defense_for_visuals = self.calc_positions_and_defense_for_visuals()
                self.positions_and_defense_string = self.positions_and_defense_as_string(is_horizontal=True)
                self.positions_list = list(self.positions_and_defense.keys())
                stats_per_400_pa = self.stats_per_n_pa(plate_appearances=400, stats=self.stats_for_card)
                self.chart.stats_per_400_pa = stats_per_400_pa
                self.chart.generate_accuracy_rating()

        if update_projections:
            self.update_projections()

    def update_projections(self) -> None:
        """Update projections based on current Showdown Bot weights"""

        # UPDATE OPPONENT CHART
        opponent_chart_w_adjustments = self.set.wotc_baseline_chart(self.player_type.opponent_type, my_type=self.player_sub_type, adjust_for_simulation_accuracy=True)
        self.chart.opponent = opponent_chart_w_adjustments
        
        # ADD PROJECTIONS
        chart_results_per_400_pa = self.chart.projected_stats_per_400_pa
        self.projected = self.projected_statline(stats_per_400_pa=chart_results_per_400_pa, command=self.chart.command, pa=self.stats.get('PA', 650))

        # ADD ESTIMATED PTS
        chart_for_pts = self.chart.model_copy()
        chart_for_pts.opponent = self.set.wotc_baseline_chart(self.player_type.opponent_type, my_type=self.player_sub_type, adjust_for_simulation_accuracy=True)
        projections_for_pts_per_400_pa = chart_for_pts.projected_stats_per_400_pa
        projections_for_pts = self.projected_statline(stats_per_400_pa=projections_for_pts_per_400_pa, command=chart_for_pts.command, pa=650)
        self.points_estimated_breakdown = self.calculate_points(projected=projections_for_pts, positions_and_defense=self.positions_and_defense, speed_or_ip=self.ip if self.is_pitcher else self.speed.speed)
        self.points_estimated = self.points_estimated_breakdown.total_points

        if len(self.stats) > 0:
            self.accolades = self.parse_accolades()
            self.real_vs_projected_stats = self._calculate_real_vs_projected_stats()
            self.image.stat_highlights_type = StatHighlightsType.CLASSIC
            self.image.stat_highlights_list = self._generate_stat_highlights_list(stats=self.stats_for_card)

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
        # REFER TO GOOGLE SHEET BELOW FOR LATEST DATA
        sheet_link = 'https://docs.google.com/spreadsheets/d/1WCrgXHIH0-amVd5pDPbhoMVnlhLuo1hU620lYCnh0VQ/edit#gid=0'
        export_url = sheet_link.replace('/edit#gid=', '/export?format=csv&gid=')
        df_wotc_cards = pd.read_csv(export_url)

        # FILTER PANDAS FOR CARDS IN SETS AND EXPANSIONS LIST
        expansion_values = [e.value for e in self.expansions]
        set_values = [int(s.year) for s in self.sets]
        player_type_values = [t.value for t in self.player_types]
        df_wotc_cards = df_wotc_cards[df_wotc_cards['Set'].isin(set_values) & df_wotc_cards['Expansion'].isin(expansion_values) & df_wotc_cards['Player Type'].isin(player_type_values)]

        # GET DISTINCT VALUES FROM THE 'SS YEAR' COLUMN
        ss_year_values = [int(s) for s in df_wotc_cards['Stats Year'].unique() if len(str(s or "")) == 4]
        ss_multi_year_values_multi_dim = [s for s in df_wotc_cards['Stats Year'].unique() if len(str(s or "")) == 9]
        for ss_multi_year in ss_multi_year_values_multi_dim:
            year_start_and_end = [int(y) for y in str(ss_multi_year).split('-')]
            years = list(range(year_start_and_end[0], year_start_and_end[1]+1))
            ss_year_values.extend(years)
        ss_year_values = list(set(ss_year_values))

        # CONVERT TO LIST OF DICTS
        list_of_dicts: list[dict[str, any]] = df_wotc_cards.to_dict(orient='records')

        # LOAD PLAYER STATS FROM ARCHIVE DB
        postgres_db = PostgresDB(is_archive=True)
        year_list = [y-1 for y in set_values] + ss_year_values
        print("FETCHING PLAYER STATS")
        real_player_stats_archive: list[PlayerArchive] = postgres_db.fetch_all_stats_from_archive(year_list=year_list, exclude_records_with_stats=False)
        if len(real_player_stats_archive) == 0:
            raise Exception('No player stats found in archive for WOTC conversion.')

        # CREATE LIST OF SHOWDOWN OBJECTS
        print("CONVERTING TO SHOWDOWN CARDS")
        converted_cards: list[WotcPlayerCard] = {}
        for gsheet_row in track(list_of_dicts, description="Converting WOTC Player Cards"):

            try:
                showdown_set = int(gsheet_row.get('Set', 0))
                if showdown_set < 2002 and gsheet_row.get('Expansion') == 'PM':
                    continue

                # ADD STATS FROM ARCHIVE
                bref_id = gsheet_row.get('BRef Id', '')
                expansion = gsheet_row.get('Expansion', 'N/A')
                edition = gsheet_row.get('Edition', 'N/A')
                ss_year_raw = str(gsheet_row.get('Stats Year', 'N/A'))
                ss_year = None if ss_year_raw == 'N/A' or len(ss_year_raw) != 4 else int(ss_year_raw)
                ss_range_start_end = tuple(int(y) for y in str(ss_year_raw).split('-')) if len(ss_year_raw) == 9 else None
                ss_years = list(range(ss_range_start_end[0], ss_range_start_end[1]+1)) if ss_range_start_end else None
                set_year = showdown_set - 1
                year = ss_year or set_year
                archive_id = f'{year}-{bref_id}'
                
                stats: dict = None
                stats_period: StatsPeriod = None
                stats_list: list[NormalizedPlayerStats] = []
                    
                # FIND YEAR OF STATS TO USE
                if expansion in ['BS', 'PM'] or ss_year:
                    player_archive = next((p for p in real_player_stats_archive if p.id == archive_id), None)
                    if player_archive:

                        # CHECK IF SMALL SAMPLE SIZE
                        # IF SO USE COMBINE STATS WITH PRIOR YEAR IF IT EXISTS
                        uses_multi_year_due_to_small_sample_size = \
                            showdown_set < 2004 \
                            and ss_year is None \
                            and player_archive.player_type == 'HITTER' \
                            and player_archive.stats.get('G', 0) < 90 \
                            and player_archive.stats.get('is_rookie_season', False)
                        if uses_multi_year_due_to_small_sample_size:
                            two_years_ago = showdown_set - 2
                            prior_year_archive_id = f'{two_years_ago}-{bref_id}'
                            prior_year_player_archive = next((p for p in real_player_stats_archive if p.id == prior_year_archive_id), None)
                            if prior_year_player_archive:
                                stats_list = [
                                    NormalizedPlayerStats(primary_datasource='bref', **player_archive.stats),
                                    NormalizedPlayerStats(primary_datasource='bref', **prior_year_player_archive.stats)
                                ]
                                stats_period = StatsPeriod(
                                    period_type=StatsPeriodType.REGULAR_SEASON,
                                    year=f'{two_years_ago}-{set_year}',
                                    year_list=[two_years_ago, set_year]
                                )
                                combined_stats = PlayerStatsNormalizer.combine_multi_year_stats(stats_list, stats_period)
                                stats = combined_stats.model_dump(
                                    exclude_unset=True,
                                    exclude_none=True,
                                    by_alias=True,
                                )
                            else:
                                stats = player_archive.stats
                        else:
                            stats = player_archive.stats

                # MID-SEASON EXPANSIONS
                elif expansion in ['TD', 'PR', 'ASG']:

                    if ss_years:
                        # DATE RANGE
                        classification = 'MULTI YEAR - FULL SEASONS'
                    elif expansion == 'ASG':
                        classification = 'MULTI YEAR - APRIL'
                    elif (showdown_set < 2002 and expansion == 'PR') or (showdown_set >= 2002 and expansion == 'TD'):
                        classification = 'MULTI YEAR - APRIL'
                    elif (showdown_set >= 2002 and expansion == 'PR'):
                        classification = 'CURRENT YEAR - ASG' if edition == 'ASG' else 'CURRENT YEAR - MAY'
                    
                    
                    match classification:
                        case 'MULTI YEAR - FULL SEASONS':
                            # SOME CC PLAYERS HAVE MULTIPLE YEARS IN SS YEAR FIELD (EX: 2000-2001)
                            stats_list = [
                                NormalizedPlayerStats(primary_datasource='bref', **p.stats) 
                                for p in real_player_stats_archive 
                                if p.bref_id == bref_id and p.year in ss_years
                            ]
                            stats_period = StatsPeriod(
                                type=StatsPeriodType.REGULAR_SEASON,
                                year=str(ss_year_raw),
                                year_list=ss_years,
                                is_multi_year=True,
                            )
                            year = str(ss_year_raw)
                        case 'MULTI YEAR - APRIL':
                            # FOR TD, PR, ASG USE STATS FROM SET AND SHOWDOWN SET (EX: 2001 TD USES 2000 AND APRIL 2001 STATS)
                            start_date = f'{set_year}-03-01'
                            end_date = f'{set_year + 1}-04-30'
                            year = f'{set_year}-{set_year + 1}'
                            stats_period = StatsPeriod(
                                type=StatsPeriodType.DATE_RANGE,
                                year=year, year_list=[set_year, showdown_set],
                                start_date=start_date, end_date=end_date,
                                disable_display_text_on_card=True,
                            )
                            stats_list = [
                                NormalizedPlayerStats(primary_datasource='bref', **p.stats) 
                                for p in real_player_stats_archive 
                                if p.bref_id == bref_id and p.year in [set_year, showdown_set]
                            ]
                        case 'CURRENT YEAR - MAY' | 'CURRENT YEAR - ASG':
                            # FOR PR IN 2002 AND BEYOND, USE STATS FROM SHOWDOWN SET YEAR ONLY (EX: 2002 PR USES ONLY APRIL-MAY 2002 STATS)
                            start_date = f'{showdown_set}-03-01'
                            end_date = f'{showdown_set}-05-31' if classification == 'CURRENT YEAR - MAY' else f'{showdown_set}-07-13'
                            year = str(showdown_set)
                            stats_period = StatsPeriod(
                                type=StatsPeriodType.DATE_RANGE,
                                year=year, year_list=[showdown_set],
                                start_date=start_date, end_date=end_date,
                                disable_display_text_on_card=True,
                            )
                            new_archive_id = f'{showdown_set}-{bref_id}'
                            player_archive = next((p for p in real_player_stats_archive if p.id == new_archive_id), None)
                            stats = player_archive.stats if player_archive else None

                    if len(stats_list) > 0:
                        combined_stats = PlayerStatsNormalizer.combine_multi_year_stats(stats_list, stats_period)
                        stats = combined_stats.model_dump(
                            exclude_unset=True,
                            exclude_none=True,
                            by_alias=True,
                        )
                card = WotcPlayerCard(data_source=WotcDataSource.GSHEET, update_projections=True, stats=stats, stats_period=stats_period, year=year, **gsheet_row)
                converted_cards[card.id] = card
            except Exception as e:
                print(f'Error converting WOTC card for {gsheet_row.get("Name", "N/A")}: {e}')
                import traceback
                traceback.print_exc()
                break
        
        self.cards = converted_cards
        return

    def export_to_local_file(self, formats: list[str] = ['csv', 'json']) -> None:
        """Export cards locally to files: json and csv"""
        
        # JSON
        if 'json' in formats:
            json_data = self.model_dump(mode="json", exclude_none=True)

            # Create directory if it doesn't exist
            file_path = Path(self.local_file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

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