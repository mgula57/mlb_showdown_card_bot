import numpy as np
import math
import requests
import operator
import os
import re
import json
import statistics
import pandas as pd
import ast
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials
from collections import Counter
from pathlib import Path
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from prettytable import PrettyTable
from pprint import pprint
from pydantic import BaseModel, validator
from typing import Any, Optional, Union
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from . import showdown_constants as sc
    from .classes.team import Team
    from .classes.icon import Icon
    from .classes.accolade import Accolade
    from .classes.sets import Set, Era, SpeedMetric, PlayerType, PlayerSubType, Stat, PointsMetric, Position, PlayerImageComponent, TemplateImageComponent, ValueRange, Chart, ImageParallel
    from .classes.metrics import DefenseMetric
    from .classes.nationality import Nationality
    from .classes.chart import ChartCategory
    from .classes.images import ImageSource, ImageSourceType, SpecialEdition, Edition, Expansion, ShowdownImage
    from .classes.points import Points
    from .classes.metadata import Speed, SpeedLetter, Hand
    from .classes import colors
    from .classes.stats_period import StatsPeriod, StatsPeriodType
    from .version import __version__
except ImportError:
    # USE LOCAL IMPORT
    import showdown_constants as sc
    from classes.team import Team
    from classes.icon import Icon
    from classes.accolade import Accolade
    from classes.sets import Set, Era, SpeedMetric, PlayerType, PlayerSubType, Stat, PointsMetric, Position, PlayerImageComponent, TemplateImageComponent, ValueRange, Chart, ImageParallel
    from classes.player_position import PlayerSubType
    from classes.metrics import DefenseMetric
    from classes.nationality import Nationality
    from classes.chart import ChartCategory
    from classes.images import ImageSource, ImageSourceType, SpecialEdition, Edition, Expansion, ShowdownImage
    from classes.points import Points
    from classes.metadata import Speed, SpeedLetter, Hand
    from classes import colors
    from classes.stats_period import StatsPeriod, StatsPeriodType
    from version import __version__

class ShowdownPlayerCard(BaseModel):

    # REQUIRED
    year: str
    set: Set
    stats: dict # TODO: VALIDATE NO HBP DOUBLE COUNTING WHEN INIT FROM DICT
    year_list: list[int] = []
    era: Era
    name: str

    # TIME PERIOD
    stats_period: StatsPeriod = StatsPeriod()

    # DERIVED
    is_full_career: bool = False
    is_multi_year: bool = False
    bref_id: str = ''
    bref_url: str = ''
    league: str = 'MLB'
    team: Team = Team.MLB
    nationality: Nationality = Nationality.NONE
    player_type: PlayerType = None
    player_type_override: Optional[PlayerType] = None
    nicknames: list[str] = []
    
    # OPTIONALS
    version: str = __version__
    source: str = 'Baseball Reference'
    is_stats_estimate: bool = False
    chart_version:int = 0
    ignore_cache: bool = False
    disable_cache_cleaning: bool = False
    date_override: Optional[str] = None
    test_numbers: Optional[tuple[int,int]] = None
    command_out_override: Optional[tuple[int,int]] = None
    is_variable_speed_00_01: bool = False
    is_wotc: bool = False
    
    # ENVIRONMENT
    is_running_in_flask: bool = False
    load_time: float = 0.0
    warnings: list[str] = []

    # RANKS
    rank: dict = {}
    pct_rank: dict = {}

    # PROCESSED BY CLASS
    image: ShowdownImage = ShowdownImage()
    chart: Chart = None
    positions_and_defense: dict[Position, int] = {}
    positions_and_real_life_ratings: dict[str, dict[DefenseMetric, Union[float, int]]] = {}
    command_out_accuracies: dict[str, float] = {}
    ip:int = None
    hand: Hand = None
    speed: Speed = None
    accolades: list[str] = None
    icons: list[Icon] = None
    projected: dict = {}
    points_breakdown: Points = Points()
    points: int = 0.0

# ------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------

    def __init__(self, **data) -> None:
        """Initializer for ShowdownPlayerCard Class"""
        
        # HANDLE EMPTY ERA INPUT AS DYNAMIC
        if data.get('era', None) is None:
            data['era'] = "DYNAMIC"

        # INIT
        super().__init__(**data)

        # PARSE NICKNAMES
        self.nicknames = self.extract_player_nicknames_list()

        # PARSE TYPE OVERRIDE
        self.player_type_override = self.parse_player_type_override(player_type_override=self.player_type_override, name_user_input=data.get('name', None))

        # IMAGE
        if data.get('image', None) is None:
            self.image: ShowdownImage = ShowdownImage(
                edition = data.get('edition', Edition.NONE),
                expansion = data.get('expansion', Expansion.BS),
                source = ImageSource(url=data.get('player_image_url', None), path=data.get('player_image_path', None)),
                parallel = data.get('parallel', ImageParallel.NONE),
                output_folder_path = data.get('card_img_output_folder_path', '') if len(data.get('card_img_output_folder_path', '')) > 0 else os.path.join(os.path.dirname(__file__), 'output'),
                set_number = data.get('set_number', '') if data.get('set_number', '') != '' else self.set.default_set_number(self.year),
                add_one_to_set_year = data.get('set_year_plus_one', False) and self.set.is_eligibile_for_year_plus_one,
                show_year_text = data.get('show_year_text', False) and self.set.is_eligibile_for_year_container,
                is_bordered = data.get('add_image_border', False),
                is_dark_mode = data.get('is_dark_mode', False),
                hide_team_logo = data.get('hide_team_logo', False),
                use_secondary_color = data.get('use_secondary_color', False),
                nickname_index=data.get('nickname_index', None)
            )
            self.image.update_special_edition(has_nationality=self.nationality.is_populated, enable_cooperstown_special_edition=self.set.enable_cooperstown_special_edition, year=self.year, is_04_05=self.set.is_04_05)
        
        disable_running_card: bool = data.get('disable_running_card', False)
        if not self.is_populated and not disable_running_card:

            # POSITIONS_AND_DEFENSE, HAND, IP, SPEED, SPEED_LETTER
            self.positions_and_defense: dict[Position, int] = self.__positions_and_defense(stats_dict=self.stats)
            self.ip: int = self.__innings_pitched(innings_pitched=float(self.stats.get('IP', 0)), games=self.stats.get('G', 0), games_started=self.stats.get('GS', 0), ip_per_start=self.stats.get('IP/GS', 0))
            self.hand: Hand = self.__handedness(hand_raw=self.stats.get('hand', None))
            self.speed: Speed = self.__speed(sprint_speed=self.stats.get('sprint_speed', None), stolen_bases=self.stats.get('SB', 0) / ( self.stats.get('PA', 0) / 650.0 ), is_sb_empty=len(str(self.stats.get('SB',''))) == 0, games=self.stats.get('G', 0))
            self.accolades: list[str] = self.parse_accolades()
            self.icons: list[Icon] = self.__icons(awards=self.stats.get('award_summary',''))

            # CONVERT STATS TO PER 400 PA
            # MAKES MATH EASIER (20 SIDED DICE)
            stats_for_400_pa = self.__stats_per_n_pa(plate_appearances=400, stats=self.stats)

            command_out_combos = [self.command_out_override] if self.command_out_override else self.__top_accurate_command_out_combos(obp=float(self.stats['onbase_perc']), num_results=5)

            self.chart: Chart = None
            self.chart, chart_results_per_400_pa = self.__most_accurate_chart(command_out_combos=command_out_combos,
                                                                              stats_per_400_pa=stats_for_400_pa,
                                                                              offset=int(self.chart_version))
            self.projected: dict = self.projected_statline(stats_per_400_pa=chart_results_per_400_pa, command=self.chart.command)

            # FOR PTS, USE STEROID ERA OPPONENT
            proj_opponent_chart, proj_my_advantages_per_20, proj_opponent_advantages_per_20 = self.opponent_stats_for_calcs(command=self.chart.command, era_override=Era.STEROID)
            projections_for_pts_per_400_pa = self.chart_to_results_per_400_pa(chart=self.chart, my_advantages_per_20=proj_my_advantages_per_20, opponent_chart=proj_opponent_chart, opponent_advantages_per_20=proj_opponent_advantages_per_20, era_override=Era.STEROID)
            projections_for_pts = self.projected_statline(stats_per_400_pa=projections_for_pts_per_400_pa, command=self.chart.command)

            self.points_breakdown: Points = self.calculate_points(projected=projections_for_pts,
                                            positions_and_defense=self.positions_and_defense,
                                            speed_or_ip=self.ip if self.is_pitcher else self.speed.speed)
            self.points: int = self.points_breakdown.total_points

            show_image = data.get('show_image', False)
            if data.get('show_image', False) or len(data.get('card_img_output_folder_path', '')) > 0:
                self.card_image(show=show_image)
            
            if data.get('print_to_cli', False):
                self.print_player()

# ------------------------------------------------------------------------
# VALIDATORS
# ------------------------------------------------------------------------

    @validator('year', always=True)
    def clean_year(cls, year:str) -> str:
        return str(year).upper()

    @validator('year_list', always=True)
    def parse_year_list(cls, year_list:list[int], values:dict) -> list[int]:

        if year_list is not None:
            if len(year_list) > 0:
                return year_list
        
        year:str = values.get('year')
        stats:dict = values.get('stats', {})
        all_years_played:list[str] = stats.get('years_played', [])
        if year.upper() == 'CAREER':
            return [int(year) for year in all_years_played]
        elif '-' in year:
            # RANGE OF YEARS
            years = year.split('-')
            year_start = int(years[0].strip())
            year_end = int(years[1].strip())
            return list(range(year_start,year_end+1))
        elif '+' in year:
            years = year.split('+')
            return [int(x.strip()) for x in years]
        else:
            return [int(year)]

    @validator('is_full_career', always=True)
    def parse_is_full_career(cls, is_full_career:bool, values:dict) -> bool:
        if is_full_career:
            return is_full_career
        
        year:str = values.get('year', '')
        return year.upper() == 'CAREER'
    
    @validator('is_multi_year', always=True)
    def parse_is_multi_year(cls, is_multi_year:bool, values:dict) -> bool:
        if is_multi_year:
            return is_multi_year
        
        year_list:list[int] = values.get('year_list', [])
        return len(year_list) > 1

    @validator('stats')
    def clean_stats(cls, stats:dict, values:dict) -> dict[str, Any]:

        # ADD OPS IF NOT IN DICT (< 1900 CARDS)
        if 'onbase_plus_slugging' not in stats.keys() and 'slugging_perc' in stats.keys() and 'onbase_perc' in stats.keys():
            stats['onbase_plus_slugging'] = stats['slugging_perc'] + stats['onbase_perc']

        # REDUCE IF/FB FOR 1988
        if 'IF/FB' in stats.keys() and values.get('year', '') == '1988':
            stats['IF/FB'] = stats.get('IF/FB', 0.0) * Set(values.get('set', None)).pu_normalizer_1988

        # COMBINE BB AND HBP
        if 'HBP' in stats.keys():
            stats['BB'] = stats.get('BB',0) + stats.get('HBP',0)

        return stats
    
    @validator('era', pre=True)
    def handle_dynamic_era(cls, era:str, values:dict) -> Era:

        if era.upper() != 'DYNAMIC':
            return Era(era)
        
        year_list = values.get('year_list', [])
        eras = []
        for year in year_list:
            for era in Era:
                if year in era.year_range:
                    eras.append(era)
        
        # FILTER TO MOST
        most_common_era_tuples_list = Counter(eras).most_common(1)

        if len(most_common_era_tuples_list) == 0:
            return Era.STEROID
        
        return most_common_era_tuples_list[0][0]

    @validator('name')
    def parse_name(cls, name:str, values:dict) -> str:
        """Use the bref name first, user input as a backup"""
        stats:dict = values.get('stats', {})
        return stats.get('name', name)
    
    @validator('player_type', always=True)
    def parse_player_type(cls, _ :str, values:dict) -> PlayerType:        
        stats:dict = values.get('stats', {})
        return PlayerType(stats.get('type', None))
    
    @validator('bref_id', always=True)
    def parse_bref_id(cls, bref_id:str, values:dict) -> str:
        if bref_id:
            if len(bref_id) > 1:
                return bref_id
        stats: dict = values.get('stats', {})
        return stats.get('bref_id', '')
    
    @validator('bref_url', always=True)
    def parse_bref_url(cls, bref_url:str, values:dict) -> str:
        if bref_url:
            if len(bref_url) > 0:
                return bref_url
        stats: dict = values.get('stats', {})
        return stats.get('bref_url', '')
    
    @validator('is_stats_estimate', always=True)
    def parse_is_stats_estimate(cls, is_stats_estimate:str, values:dict) -> bool:
        if is_stats_estimate:
            return is_stats_estimate
        stats: dict = values.get('stats', {})
        return stats.get('is_stats_estimate', False)

    @validator('league', always=True)
    def parse_league(cls, league:str, values:dict) -> str:
        if league != 'MLB':
            return league
        stats: dict = values.get('stats', {})
        return stats.get('lg_ID', 'MLB')
    
    @validator('team', always=True)
    def parse_team(cls, team:Team, values:dict) -> Team:
        if team != Team.MLB:
            return team
        stats:dict = values.get('stats', {})
        return Team(stats.get('team_ID', None))
    
    @validator('nationality', always=True)
    def parse_nationality(cls, nationality:Nationality, values:dict) -> Nationality:
        if nationality != Nationality.NONE:
            return nationality
        stats:dict = values.get('stats', {})
        return Nationality(stats.get('nationality', None))

    def parse_player_type_override(cls, player_type_override:str, name_user_input: str) -> PlayerType:
        """Check for player type override as an input and within the user inputted name."""

        if player_type_override:
            return player_type_override

        if name_user_input:
            for type in PlayerType:
                values_in_name = [substr for substr in type.override_user_input_substrings if f'({substr})' in name_user_input.upper()]
                has_an_override_in_name_input = len(values_in_name) > 0
                if has_an_override_in_name_input:
                    return type
        
        return None

    def extract_player_nicknames_list(self) -> list[str]:
        """Use nicknames csv file to check if the player has nicknames available."""
        
        nicknames_file_path = os.path.join(Path(os.path.dirname(__file__)),'nicknames.csv')
        nicknames_df = pd.read_csv(nicknames_file_path)
        nicknames_filtered = nicknames_df.loc[nicknames_df['bref_id'] == self.bref_id]

        if len(nicknames_filtered) == 0:
            return []
        
        nicknames_str = nicknames_filtered['nicknames'].max()

        try:
            nicknames_list = ast.literal_eval(nicknames_str)
            return nicknames_list
        except:
            return []


# ------------------------------------------------------------------------
# STATIC PROPERTIES
# ------------------------------------------------------------------------

    @property
    def id(self) -> str:
        """Generate a unique ID to classify the player's card. Does not include image styling."""
        fields = [self.year, self.bref_id, self.set.value, self.image.expansion.value,]
        if self.player_type_override:
            fields.append(self.player_type_override.value)
        return "-".join(fields)

    @property
    def is_populated(self) -> bool:
        if self.chart is None:
            return False
        return self.points > 0

    @property
    def is_pitcher(self) -> bool:
        return self.player_type.is_pitcher

    @property
    def player_sub_type(self) -> PlayerSubType:
        """Gets full player type (position_player, starting_pitcher, relief_pitcher).
           Used for applying weights

        Args:
          None

        Returns:
          String for full player type ('position_player', 'tarting_pitcher', 'relief_pitcher').
        """
        # PARSE PLAYER TYPE
        if self.player_type.is_pitcher:
            is_starting_pitcher = self.has_position(Position.SP)
            return PlayerSubType.STARTING_PITCHER if is_starting_pitcher else PlayerSubType.RELIEF_PITCHER
        else:
            return PlayerSubType.POSITION_PLAYER

    @property
    def player_classification(self) -> str:
        """Gives the player a classification based on their stats, hand, and position. 
          Used to inform which silhouette is given to a player.

        Args:
          None

        Returns:
          String with player's classification (ex: "LHH", "LHH-OF", "RHP-CL")
        """

        positions = self.positions_and_defense.keys()
        is_catcher = any(pos in positions for pos in ['C','CA'])
        is_middle_infield = any(pos in positions for pos in ['IF','2B','SS'])
        is_outfield = any(pos in positions for pos in ['OF','CF','LF/RF'])
        is_1b = '1B' in positions
        is_multi_position = len(positions) > 1
        hand_prefix = self.hand.silhouette_name(self.is_pitcher)
        hand_throwing = self.stats['hand_throw']
        throwing_hand_prefix = f"{hand_throwing[0].upper()}H"

        # CATCHERS
        if is_catcher:
            return "CA"

        # MIDDLE INFIELDERS
        if is_middle_infield and not is_outfield:
            return "MIF"

        # OLD TIMERS
        if min(self.year_list) < 1950:
            # IF YEAR IS LESS THAN 1950, ASSIGN OLD TIMER SILHOUETTES
            return f"{hand_prefix}-OT"

        # PITCHERS
        if self.is_pitcher:
            # PITCHERS ARE CLASSIFIED AS SP, RP, CL
            if 'RELIEVER' in positions:
                return f"{hand_prefix}-RP"
            elif 'CLOSER' in positions:
                return f"{hand_prefix}-CL"
            else:
                return f"{hand_prefix}-SP"
        # HITTERS
        else:
            is_slg_above_threshold = self.stats['slugging_perc'] >= 0.475
            # FOR HITTERS CHECK FOR POSITIONS
            # 1. LHH OUTFIELDER
            if is_outfield and hand_throwing == "Left" and not is_slg_above_threshold:
                return f"LH-OF"

            # 2. CHECK FOR 1B
            if is_1b and not is_multi_position:
                return f"{throwing_hand_prefix}-1B"

            # 3. CHECK FOR POWER HITTER
            if is_slg_above_threshold:
                return f"{hand_prefix}-POW"

        # RETURN STANDARD CUTOUT
        return hand_prefix
        
    @property
    def num_positions_playable(self) -> int:
        """Count how many positions the player is eligible to play. 
           Pitchers (not named Ohtani) default to 1 position.
        
        Args:
          None

        Returns:
          Integer with number of unique playable positions for the player.
        """

        num_positions = 0
        for position in self.positions_and_defense.keys():
            match position:
                case "LF/RF": num_positions += 2
                case "IF": num_positions += 4
                case "OF": num_positions += 3
                case _: num_positions += 1 # DEFAULT
        return num_positions
    
    @property
    def positions_and_defense_for_visuals(self) -> dict[str, int]:
        """ Transform the player's positions_and_defense dictionary for visuals (printing, card image)
        
        Args:
          None

        Returns:
          Dictionary where key is the position, value is the defense at that position
        """

        positions_and_defense_as_str = { p.value_visual(ca_position_name=self.set.catcher_position_name) : v for p,v in self.positions_and_defense.items() }

        # NO NEED TO COMBINE IF < 3 POSITIONS
        if self.set.is_showdown_bot or len(self.positions_and_defense) < 3:
            return positions_and_defense_as_str
        
        positions_to_combine = self.__find_position_combination_opportunity(self.positions_and_defense)
        positions_to_combine_as_str = [pos.value for pos in positions_to_combine]
        if positions_to_combine is None:
            return positions_and_defense_as_str
        positions_to_combine_str =  "/".join(positions_to_combine_as_str)
        
        avg_defense = self.positions_and_defense.get(positions_to_combine[0], None)
        if avg_defense is None:
            return positions_and_defense_as_str
        combined_positions_and_defense = {pos: df for pos, df in positions_and_defense_as_str.items() if pos not in positions_to_combine_as_str}
        combined_positions_and_defense[positions_to_combine_str] = avg_defense

        return combined_positions_and_defense

    @property
    def positions_and_defense_img_order(self) -> list:
        """ Sort the positions and defense by how they will appear on the card image.

        Args:
          None
        
        Returns:
          List of positions and defense ordered by how they will appear on the card image.
        """
        position_enum_values = [pos.value for pos in Position]
        return sorted(self.positions_and_defense_for_visuals.items(), key=lambda pos_and_def: (Position(pos_and_def[0]).ordering_index if pos_and_def[0] in position_enum_values else 0) )
    
    @property
    def positions_list(self) -> [Position]:
        """ List of player's in-game positions"""
        return list(self.positions_and_defense.keys())

    @property 
    def median_year(self) -> int:
        """ Median of all player seasons used. """
        # CHECK IF PLAYER FITS IN ANY ALTERNATE RANGE
        if self.is_multi_year:
            if self.is_full_career:
                # USE MEDIAN YEAR OF YEARS PLAYED
                years_played_ints = [int(year) for year in self.stats['years_played']]
            elif '-' in self.year:
                # RANGE OF YEARS
                years = self.year.split('-')
                year_start = int(years[0].strip())
                year_end = int(years[1].strip())
                years_played_ints = list(range(year_start,year_end+1))
            elif '+' in self.year:
                years = self.year.split('+')
                years_played_ints = [int(x.strip()) for x in years]
            return int(round(statistics.median(years_played_ints)))
        else:
            return int(self.year)

    @property
    def use_alternate_logo(self) -> bool:
        """ Alternate logos are used in 2004+ sets """
        return self.set.use_alternate_team_logo and not self.image.edition.use_edition_logo_as_team_logo

    @property
    def image_component_ordered_list(self) -> list[PlayerImageComponent]:
        all_image_components = [c for c in PlayerImageComponent if c.layering_index is not None]
        return list(sorted(all_image_components, key=lambda comp: comp.layering_index))

    @property
    def team_override_for_images(self) -> Team:
        """ Team override to use for background images and colors (ex: CC)"""
        
        # COOPERSTOWN COLLECTION LOGO
        if self.image.edition == Edition.COOPERSTOWN_COLLECTION or self.image.parallel == ImageParallel.GOLD_FRAME:
            return Team.CCC
        
        # HIDE TEAM LOGO, USE MLB
        if self.image.hide_team_logo:
            return Team.MLB
        
        return None
    
    @property
    def command_type(self) -> str:
        """ Type of Command, either 'Onbase' or 'Control'"""
        return "Control" if self.is_pitcher else "Onbase"
    
    @property
    def is_using_nickname(self) -> bool:
        """Check to see availability of nickname for the player."""
        
        # NO NICKNAME CHOOSEN OR AVAILABLE
        num_nicknames = len(self.nicknames)
        if self.image.nickname_index is None or num_nicknames == 0:
            return False
        
        # NICKNAME INDEX NOT AVAILABLE
        is_index_to_high = self.image.nickname_index > num_nicknames
        if is_index_to_high:
            return False
        
        try:
            _ = self.nicknames[self.image.nickname_index - 1]
            return True
        except:
            return False

    @property
    def name_for_visuals(self) -> str:
        """Returns name that is used for visuals, accounting for custom nicknames"""

        if self.is_using_nickname:
            return self.nicknames[self.image.nickname_index - 1]
        
        return self.name


# ------------------------------------------------------------------------
# METADATA METHODS
# ------------------------------------------------------------------------

    def __positions_and_defense(self, stats_dict:dict) -> dict[Position, int]:
        """Get in-game defensive positions and ratings

        Args:
          stats_dict: All stats from the player's real life season.

        Returns:
          Dict with in game positions and defensive ratings
        """

        total_games_played = stats_dict.get('G_RS', None) or stats_dict.get('G', 0)
        total_games_started = stats_dict.get('GS', 0)
        total_saves = stats_dict.get('SV', 0)

        positions_and_defense = {}
        positions_and_games_played = {}
        positions_and_real_life_ratings = {}

        # FLAG IF OF IS AVAILABLE BUT NOT CF (SHOHEI OHTANI 2021 CASE)
        defense_stats_dict:dict = stats_dict.get('positions', {})
        positions_list: list[str] = list(defense_stats_dict.keys())
        num_positions = len(positions_list)
        is_of_but_hasnt_played_cf = 'OF' in positions_list and 'CF' not in positions_list

        for position_name, defensive_stats in defense_stats_dict.items():
            is_valid_position = self.is_pitcher == ('P' == position_name)
            if is_valid_position:
                games_at_position = defensive_stats.get('g', 0)
                position = self.__position_name_in_game(position=position_name,
                                                        num_positions=num_positions,
                                                        position_appearances=games_at_position,
                                                        games_played=total_games_played,
                                                        games_started=total_games_started,
                                                        saves=total_saves)
                if position is not None:
                    positions_and_games_played[position] = games_at_position
                    if not self.is_pitcher:
                        try:
                            # FOR MULTI YEAR CARDS THAT SPAN CROSS OVER 2016, IGNORE OAA
                            # CHECK WHAT YEARS THE CARD SPANS OVER
                            start_year = min(self.year_list)
                            end_year = max(self.year_list)
                            use_drs_over_oaa = start_year < 2016 and end_year >= 2016
                            
                            # CHECK WHICH DEFENSIVE METRIC TO USE
                            is_drs_available = 'drs' in defensive_stats.keys()
                            is_d_war_available = 'dWAR' in stats_dict.keys()
                            is_oaa_available = 'oaa' in defensive_stats.keys() and not use_drs_over_oaa
                            oaa = defensive_stats['oaa'] if is_oaa_available else None
                            # DRS
                            try:
                                if is_drs_available:
                                    drs = int(defensive_stats['drs']) if defensive_stats['drs'] != None else None
                                else:
                                    drs = None
                            except:
                                drs = None
                            # TZR
                            try:
                                tzr = int(defensive_stats['tzr']) if defensive_stats['tzr'] != None else None
                            except:
                                tzr = None
                            # DWAR
                            dWar = float(stats_dict['dWAR']) if is_d_war_available else None
                            
                            if is_oaa_available:
                                metric = DefenseMetric.OAA
                                defensive_rating = oaa
                            elif drs != None:
                                metric = DefenseMetric.DRS
                                defensive_rating = drs
                            elif tzr != None: 
                                metric = DefenseMetric.TZR
                                defensive_rating = tzr
                            else:
                                metric = DefenseMetric.DWAR
                                defensive_rating = dWar
                            positions_and_real_life_ratings[position] = { metric: round(defensive_rating,3) }
                            in_game_defense = self.__convert_to_in_game_defense(position=position,rating=defensive_rating,metric=metric,games=games_at_position)
                        except Exception as e:
                            print(e)
                            in_game_defense = 0
                        positions_and_defense[position] = in_game_defense
                    else:
                        positions_and_defense[position] = 0

        # COMBINE ALIKE IN-GAME POSITIONS (LF/RF, OF, IF, ...)
        initial_position_name_and_rating, final_position_games_played = self.__combine_like_positions(positions_and_defense, positions_and_games_played,is_of_but_hasnt_played_cf=is_of_but_hasnt_played_cf)

        # FILTER TO TOP POSITIONS BY GAMES PLAYED
        final_positions_in_game = self.__finalize_in_game_positions(positions_and_defense=initial_position_name_and_rating, positions_and_games_played=final_position_games_played)

        # ASSIGN DH IF POSITIONS DICT IS EMPTY
        if final_positions_in_game == {}:
            final_positions_in_game = {Position.DH: 0}

        # STORE TO REAL LIFE NUMBERS TO SELF
        self.positions_and_real_life_ratings = positions_and_real_life_ratings

        return final_positions_in_game

    def __combine_like_positions(self, positions_and_defense:dict[Position,int], positions_and_games_played:dict, is_of_but_hasnt_played_cf=False) -> tuple[dict,dict]:
        """Limit and combine positions (ex: combine LF and RF -> LF/RF)

        Args:
          positions_and_defense: Dict of positions and in game defensive ratings.
          positions_and_games_played: Dict of positions and number of appearance at each position.

        Returns:
          Tuple
            - Dict with relevant in game positions and defensive ratings
            - Dict with relevant in game positions and games played in those positions
        """

        positions_set = set(positions_and_defense.keys())
        # IF HAS EITHER CORNER OUTFIELD POSITION
        if 'LF' in positions_set or 'RF' in positions_set:
            # IF BOTH LF AND RF
            if set(['LF','RF']).issubset(positions_set):
                lf_games = positions_and_games_played['LF']
                rf_games = positions_and_games_played['RF']
                lf_rf_games = lf_games + rf_games
                # WEIGHTED AVG
                lf_rf_rating = round(( (positions_and_defense['LF']*lf_games) + (positions_and_defense['RF']*rf_games) ) / lf_rf_games)
                del positions_and_defense['LF']
                del positions_and_defense['RF']
                del positions_and_games_played['LF']
                del positions_and_games_played['RF']
            # IF JUST LF
            elif 'LF' in positions_set:
                lf_rf_rating = positions_and_defense['LF']
                lf_rf_games = positions_and_games_played['LF']
                del positions_and_defense['LF']
                del positions_and_games_played['LF']
            # IF JUST RF
            else:
                lf_rf_rating = positions_and_defense['RF']
                lf_rf_games = positions_and_games_played['RF']
                del positions_and_defense['RF']
                del positions_and_games_played['RF']
            positions_and_defense['LF/RF'] = lf_rf_rating
            positions_and_games_played['LF/RF'] = lf_rf_games
            positions_set = set(positions_and_defense.keys())
        # IF PLAYER HAS ALL OUTFIELD POSITIONS
        if set(['LF/RF','CF','OF']).issubset(positions_set):
            if self.set.is_outfield_split and positions_and_defense['LF/RF'] != positions_and_defense['CF']:
                del positions_and_defense['OF']
                del positions_and_games_played['OF']
            else:
                del positions_and_defense['LF/RF']
                del positions_and_defense['CF']
                del positions_and_games_played['LF/RF']
                del positions_and_games_played['CF']
        # IF JUST OF
        elif 'OF' in positions_set and ('LF/RF' in positions_set or 'CF' in positions_set):
            del positions_and_defense['OF']
            del positions_and_games_played['OF']
        
        # IS CF AND 2000/2001
        # 2000/2001 SETS ALWAYS INCLUDED LF/RF FOR CF PLAYERS
        if 'CF' in positions_set and len(positions_and_defense) == 1 and self.set.is_00_01:
            if 'CF' in positions_and_defense.keys():
                cf_defense = positions_and_defense['CF']
                lf_rf_defense = round(positions_and_defense['CF'] / 2)
                if lf_rf_defense == cf_defense:
                    positions_and_games_played['OF'] = positions_and_games_played['CF']
                    positions_and_defense['OF'] = cf_defense
                    del positions_and_defense['CF']
                    del positions_and_games_played['CF']
                else:
                    positions_and_defense['LF/RF'] = lf_rf_defense
                    positions_and_games_played['LF/RF'] = positions_and_games_played['CF']
        
        # CHANGE OF TO LF/RF IF PLAYER HASNT PLAYED CF
        # EXCEPTION IS PRE-1900, WHERE 'OF' POSITIONAL BREAKOUTS ARE NOT AVAILABLE
        start_year = min(self.year_list)
        if 'OF' in positions_set and is_of_but_hasnt_played_cf and 'OF' in positions_and_defense.keys() and start_year > 1900:
            positions_and_games_played['LF/RF'] = positions_and_games_played['OF']
            positions_and_defense['LF/RF'] = positions_and_defense['OF']
            del positions_and_defense['OF']
            del positions_and_games_played['OF']

        return positions_and_defense, positions_and_games_played

    def __finalize_in_game_positions(self, positions_and_defense:dict[str,int], positions_and_games_played:dict[str,int]) -> dict[Position,int]:
        """ Filter number of positions, find opportunities to combine positions. Convert position strings to classes.
        
        Args:
          positions_and_defense: Dict of positions and in-game defensive ratings.
          positions_and_games_played: Dict of positions and number of appearance at each position.

        Returns:
          Dict of positions and defense filtered to max positions.
        """

        # CONVERT POSITION STRINGS TO POSITION CLASS
        positions_and_defense: dict[Position, int] = { Position(p): v for p, v in positions_and_defense.items() }
        positions_and_games_played: dict[Position, int] = { Position(p): v for p, v in positions_and_games_played.items() }

        # CHECK FOR IF ELIGIBILITY
        infield_positions_and_defense = { p:v for p, v in positions_and_defense.items() if p.is_infield }
        infield_positions_and_games_played = { p:v for p, v in positions_and_games_played.items() if p.is_infield }
        is_infield_eligible = len(infield_positions_and_defense) == 4
        if is_infield_eligible:
            # SEE IF TOTAL DEFENSE IS ABOVE REQUIREMENT FOR +1
            infield_positions = list(infield_positions_and_defense.keys())
            total_defense_infield = sum(list(infield_positions_and_defense.values()))
            total_games_played_infield = sum(list(infield_positions_and_games_played.values()))
            in_game_rating_infield = int(total_defense_infield >= self.set.infield_plus_one_requirement)

            # REMOVE OLD POSITIONS
            for position in infield_positions:
                positions_and_defense.pop(position, None)
                positions_and_games_played.pop(position, None)

            # ADD IF DEFENSE
            positions_and_defense[Position.IF] = in_game_rating_infield
            positions_and_games_played[Position.IF] = total_games_played_infield

        # LIMIT TO ONLY 2 POSITIONS. CHOOSE BASED ON # OF GAMES PLAYED.
        position_slots = self.set.num_position_slots

        if len(positions_and_defense) <= position_slots:
            # NO NEED TO FILTER, RETURN CURRENT DICT
            return positions_and_defense
        
        sorted_positions = sorted(positions_and_games_played.items(), key=operator.itemgetter(1), reverse=True)[0:3]
        included_positions_list = [pos[0] for pos in sorted_positions]
        final_positions_and_defense = {position: value for position, value in positions_and_defense.items() if position in included_positions_list}

        if self.set.is_wotc and len(final_positions_and_defense) > 2:
            positions_to_merge = self.__find_position_combination_opportunity(positions_and_defense=final_positions_and_defense)
            if positions_to_merge is None:
                # NOTHING CAN BE COMBINED, REMOVE LAST POSITION
                final_positions_and_defense.pop(included_positions_list[-1], None)
            else:
                # AVERAGE DEFENSE FOR POSITIONS THAT WILL BE COMBINED
                avg_defense = int(round(statistics.mean([defense for pos, defense in final_positions_and_defense.items() if pos in positions_to_merge])))
                for pos in positions_to_merge:
                    final_positions_and_defense[pos] = avg_defense

        return final_positions_and_defense

    def __find_position_combination_opportunity(self, positions_and_defense:dict[Position, int]) -> list[Position]:
        """ From dictionary of player with > 2 positions, see if there is an opportunity to combine positions together.

        If no combination opportunies exist, return None.

        Args:
          positions_and_defense: Dict of positions and in-game defensive ratings.

        Returns:
          List of positions that will be combined into one.
        """

        # CREATE DICTIONARY OF POSITIONS ABLE TO BE COMBINED + DIFFERENCE IN DEFENSE
        positions_able_to_be_combined: dict[Position, tuple[Position, int]] = {}
        position_list = list(positions_and_defense.keys())
        for position, defense in positions_and_defense.items():
            combinations_list_for_pos = [Position(pos_str) for pos_str in position.allowed_combinations]
            combinations_available_for_player = {p: abs(defense - positions_and_defense.get(p, 0)) for p in position_list if p != position and p in combinations_list_for_pos}
            if len(combinations_available_for_player) > 0:
                sorted_combinations = sorted(combinations_available_for_player.items(), key=lambda x: x[1])
                positions_able_to_be_combined[position] = sorted_combinations[0]

        # SELECT ONE POSITION TO CHANGE
        # FIRST SORT BASED ON DIFFERENCE IN DEFENSE, THEN BY POSITION'S ORDERING
        sorted_positions = sorted(positions_able_to_be_combined.items(), key=lambda x: (x[1][1], -x[0].ordering_index))
        
        if len(sorted_positions) == 0:
            return None
        
        top_combo = sorted_positions[0]
        position1 = top_combo[0]
        position2 = top_combo[1][0]
        difference = top_combo[1][1]

        # ONLY RETURN COMBINATION IF DIFFERENCE IS < 3
        if difference > 2:
            return None
        
        return [position1, position2]

    def __position_name_in_game(self, position:str, num_positions:int, position_appearances:int, games_played:int, games_started:int, saves:int) -> str:
        """Cleans position name to conform to game standards.

        Args:
          position: Baseball Reference name for position.
          num_positions: Number of positions listed for the player.
          position_appearances: Total games played for the position.
          games_played: Total games played for all positions.
          games_started: Total starts for a Pitcher.
          saves: Saves recorded for a Pitcher.

        Returns:
          In game position name.
        """

        pct_of_games_played = position_appearances / games_played
        if position == 'P' and self.is_pitcher:
            # PITCHER IS EITHER STARTER, RELIEVER, OR CLOSER
            gsRatio = games_started / games_played
            if gsRatio > self.set.starting_pitcher_pct_games_started:
                # ASSIGN MINIMUM IP FOR STARTERS
                return 'STARTER'
            if saves > self.set.closer_min_saves_required:
                return 'CLOSER'
            else:
                return 'RELIEVER'
        elif ( position_appearances < self.set.min_number_of_games_defense and pct_of_games_played < self.set.min_pct_of_games_defense(is_multi_year=False) ) or (self.is_multi_year and pct_of_games_played < self.set.min_pct_of_games_defense(is_multi_year=True)):
            # IF POSIITION DOES NOT MEET REQUIREMENT, RETURN NONE
            return None
        elif position == 'DH' and num_positions > 1:
            # PLAYER MAY HAVE PLAYED AT DH, BUT HAS OTHER POSITIONS, SO DH WONT BE LISTED
            return None
        elif not self.set.is_00_01 and position == 'C':
            # CHANGE CATCHER POSITION NAME DEPENDING ON CONTEXT YEAR
            return 'CA'
        else:
            # RETURN BASEBALL REFERENCE STRING VALUE
            return position

    def __convert_to_in_game_defense(self, position:str, rating:float, metric:DefenseMetric, games:int) -> int:
        """Converts the best available fielding metric to in game defense at a position.
           Uses DRS for 2003+, TZR for 1953-2002, dWAR for <1953.
           More modern defensive metrics (like DRS) are not available for historical
           seasons.

        Args:
          position: In game position.
          rating: Total Zone Rating or dWAR. 0 is average for a position.
          metric: Metric used for calculations (ex: drs, tzr, dWAR, oaa)
          games: Games played at position.

        Returns:
          In game defensive rating.
        """
        # IF USING OUTS ABOVE AVG, CALCULATE RATING PER 162 GAMES
        position = Position(position)
        is_1b = position == Position._1B
        if metric == DefenseMetric.OAA:
            rating = rating / games * 162.0
            # FOR OUTS ABOVE AVG OUTLIERS, SLIGHTLY DISCOUNT DEFENSE OVER THE MAX
            # EX: NICK AHMED 2018 - 38.45 OAA per 162
            #   - OAA FOR +5 = 16
            #   - OAA OVER MAX = 38.45 - 16 = 22.45
            #   - REDUCED OVER MAX = 22.45 * 0.5 = 11.23
            #   - NEW RATING = 16 + 11.23 = 26.23            
            if rating > metric.range_max and not is_1b:
                amount_over_max = rating - metric.range_max
                reduced_amount_over_max = amount_over_max * metric.over_max_multiplier
                rating = reduced_amount_over_max + metric.range_max

        max_defense_for_position = self.set.position_defense_max(position=position)
        percentile = (rating-metric.range_min) / metric.range_total_values
        defense_raw = percentile * max_defense_for_position
        defense = round(defense_raw) if defense_raw > 0 or self.set.is_showdown_bot else 0
        
        # FOR NEGATIVES, CAP DEFENSE AT -2
        defense = max(self.set.defense_floor, defense)

        # ADD IN STATIC METRICS FOR 1B
        if is_1b:
            if rating > metric.first_base_plus_2_cutoff:
                defense = 2
            elif rating > metric.first_base_plus_1_cutoff:
                defense = 1
            elif rating < metric.first_base_minus_1_cutoff and self.set.is_showdown_bot:
                defense = -1
            else:
                defense = 0
        
        # CAP DEFENSE IF GAMES PLAYED AT POSITION IS LESS THAN 80
        defense_over_the_max = defense > max_defense_for_position
        defense = int(max_defense_for_position) if games < 100 and defense_over_the_max else defense

        # CAP DEFENSE AT +0 IF IN NEGATIVES AND GAMES PLAYED IS UNDER 0 (CLASSIC/EXPANDED SETS)
        defense = 0 if defense < 0 and games < 50 else defense

        return defense

    def __handedness(self, hand_raw:str) -> Hand:
        """Get hand of player. Format to how card will display hand.

        Args:
          hand_raw: Hand string from Baseball Reference. Will be "Left", "Right", or "Both".

        Returns:
          Formatted hand string (ex: "Bats R" or "RHP").
        """

        hand_first_letter = hand_raw[0:1].upper() if hand_raw != 'Both' else 'S'

        return Hand(hand_first_letter)

    def __innings_pitched(self, innings_pitched:float, games:int, games_started:int, ip_per_start:float) -> int:
        """In game stamina for a pitcher. Position Player defaults to 0.

        Args:
          innings_pitched: The total innings pitched during the season.
          games: The total games played during the season.
          games_started: The total games started during the season.
          ip_per_start: IP per game started.

        Returns:
          In game innings pitched ability.
        """
        # ACCOUNT FOR HYBRID STARTER/RELIEVERS
        if self.player_sub_type == PlayerSubType.RELIEF_PITCHER:
            # REMOVE STARTER INNINGS AND GAMES STARTED
            ip_as_starter = games_started * ip_per_start
            innings_pitched -= ip_as_starter
            games -= games_started
            ip = min(round(innings_pitched / games),3) # CAP RELIEVERS AT 3 IP
        elif ip_per_start > 0:
            ip = max(round(ip_per_start),4) # MINIMUM FOR SP IS 4 IP
        else:
            ip = round(innings_pitched / games)
        
        ip = 1 if ip < 1 else ip
        
        return ip

    def __speed(self, sprint_speed:float, stolen_bases:int, is_sb_empty:bool, games:int = 0) -> Speed:
        """In game speed for a position player. Will use pure sprint speed
           if year is >= 2015, otherwise uses stolen bases. Pitcher defaults to 10.

        Args:
          sprint_speed: Average sprint speed according to baseballsavant.com.
                        IMPORTANT: Data is available for 2015+.
          stolen_bases: Number of steals during the season.
          is_sb_empty: Bool for whether SB are unavailable for the player.
          games: Number of games played in the season(s).

        Returns:
          Speed class with speed and letter.
        """

        if self.is_pitcher:
            # PITCHER DEFAULTS TO 10
            return Speed(speed=10, letter=SpeedLetter.C)
    
        if is_sb_empty and sprint_speed is None:
            # DEFAULT PLAYERS WITHOUT SB/SS AVAILABLE TO 12
            return Speed(speed=10, letter=SpeedLetter.C if self.set == Set._2002 else SpeedLetter.B)

        # IF FULL CAREER CARD, ONLY USE SPRINT SPEED IF PLAYER HAS OVER 35% of CAREER POST 2015
        pct_career_post_2015 = sum([1 if year >= 2015 else 0 for year in self.year_list]) / len(self.year_list)
        is_disqualied_career_speed = self.is_multi_year and pct_career_post_2015 < 0.35

        # DEFINE METRICS USED TO DETERMINE IN-GAME SPEED
        disable_sprint_speed = sprint_speed is None or math.isnan(sprint_speed) or sprint_speed == '' or sprint_speed == 0 or is_disqualied_career_speed
        speed_elements = {SpeedMetric.STOLEN_BASES: stolen_bases} 
        if not disable_sprint_speed:
            speed_elements.update( {SpeedMetric.SPRINT_SPEED: sprint_speed} )

        in_game_speed_for_metric: dict[SpeedMetric, float] = {}
        for metric, value in speed_elements.items():
            use_variable_speed_multiplier = self.set.is_00_01 and self.is_variable_speed_00_01
            metric_multiplier = self.set.speed_metric_multiplier(metric=metric, use_variable_speed_multiplier=use_variable_speed_multiplier)
            era_multiplier = self.era.speed_multiplier

            speed_percentile = era_multiplier * metric_multiplier * (value-metric.minimum_range_value) / (metric.maximum_range_value - metric.minimum_range_value)
            speed = int(round(speed_percentile * metric.top_percentile_range_value))

            # CHANGE OUTLIERS
            min_in_game = self.set.min_in_game_spd
            max_in_game = (self.set.max_in_game_spd if games > 85 else (self.set.max_in_game_spd - 3))

            cutoff_for_sub_percentile_sb = 20
            if metric == SpeedMetric.STOLEN_BASES and speed > cutoff_for_sub_percentile_sb:
                sb_cap = SpeedMetric.STOLEN_BASES.threshold_max_650_pa * metric_multiplier
                sub_percentile = (value - metric.maximum_range_value) / (sb_cap - metric.maximum_range_value)
                remaining_slots_over_cutoff = max_in_game - cutoff_for_sub_percentile_sb
                additional_speed_over_cutoff = sub_percentile * remaining_slots_over_cutoff
                speed = int(additional_speed_over_cutoff + cutoff_for_sub_percentile_sb)
            
            final_speed_for_metric = min( max(speed, min_in_game), max_in_game )

            in_game_speed_for_metric[metric] = final_speed_for_metric

        # AVERAGE SPRINT SPEED WITH SB SPEED
        num_metrics = len(in_game_speed_for_metric)
        sb_speed = in_game_speed_for_metric.get(SpeedMetric.STOLEN_BASES, 0)
        ss_speed = in_game_speed_for_metric.get(SpeedMetric.SPRINT_SPEED, 0)
        
        # CHANGE WEIGHTS TO EMPHASIZE STOLEN BASES OVER SPRINT SPEED
        use_sb_outliers_weights = num_metrics > 1 and sb_speed > SpeedMetric.STOLEN_BASES.outlier_cutoff and sb_speed > ss_speed
        
        # FINALIZE SPEED, ASSIGN LETTER
        final_speed = int(round( sum([( (metric.weight_sb_outliers if use_sb_outliers_weights else metric.weight) if num_metrics > 1 else 1.0) * in_game_spd for metric, in_game_spd in in_game_speed_for_metric.items() ]) ))
        if final_speed < self.set.speed_c_cutoff:
            letter = SpeedLetter.C
        elif final_speed < 18:
            letter = SpeedLetter.B
        else:
            letter = SpeedLetter.A

        # IF 2000 OR 2001, SPEED VALUES CAN ONLY BE 10,15,20
        if self.set.is_00_01 and not self.is_variable_speed_00_01:
            final_speed = letter.speed_00_01

        return Speed(speed=final_speed, letter=letter)

    def __icons(self, awards:str) -> list[Icon]:
        """Converts awards_summary and other metadata fields into in game icons.

        Args:
          awards: String containing list of seasonal accolades.

        Returns:
          List of in game icons as strings.
        """

        # ICONS ONLY APPLY TO 2003+
        if not self.set.has_icons:
            return []
        
        # PARSE PLAYER'S AWARDS
        awards_string = '' if awards is None else str(awards).upper()
        awards_list = awards_string.split(',')
        
        icons = []
        available_icons = [icon for icon in Icon if icon.is_available(is_pitcher=self.is_pitcher)]
        for icon in available_icons:

            # ROOKIE
            if icon == Icon.R and self.stats.get('is_rookie', False):
                icons.append(icon)
                continue

            # ATTRIBUTES
            stat_category = icon.stat_category
            stat_value_requirement = icon.stat_value_requirement

            # AWARDS
            if icon.is_award_based:
                if icon.award_str in awards_list:
                    icons.append(icon)
                    continue
            
            # THRESHOLDS
            if stat_value_requirement and stat_category:
                if self.stats.get(f"is_above_{stat_category.lower()}_threshold", False):
                    icons.append(icon)
                    continue
            
            # LEADER
            if stat_category:
                is_top_2 = len([a for a in self.accolades if ("2ND" in a or "LEADER" in a) and (f" {icon.accolade_search_term}" in a and 'SO/9' not in a)]) > 0
                is_leader = self.stats.get(f"is_{stat_category.lower()}_leader", False)
                if is_top_2 or is_leader:
                    icons.append(icon)
                    continue


        # IF REMOVE R ICON IF THERE'S NO ROOM FOR IT (EX: ICHIRO 2001)
        if len(icons) >= 5 and not self.is_pitcher and Icon.R in icons and Icon.RY in icons:
            icons.remove(Icon.R)

        return icons

    def parse_accolades(self, maximum:int = None) -> list[str]:
        """Generates array of player highlights for season.

        Args:
          maximum: Maximum accolades to include.

        Returns:
          Array with 3 string elements showing accolades for season
        """

        # HELPER ATTRIBUTES 
        num_seasons = len(self.year_list)
        is_pre_2004 = not self.set.is_after_03
        is_icons = self.set.has_icons
        ba_champ_text = 'BATTING TITLE'
        is_starting_pitcher = self.has_position(Position.SP)

        # -- PART 1: AWARDS AND RANKINGS --
        accolades_dict = self.stats.get('accolades', {})
        accolades_rank_and_priority_tuples = []
        for accolade_type, accolade_list in accolades_dict.items():

            try:
                accolade_class = Accolade(accolade_type)
            except ValueError:
                continue
            
            # CONTINUE IF THERE ARE NO 
            if len(accolade_list) == 0:
                continue

            # DOES NOT MATCH PLAYER TYPE
            if (accolade_class.is_hitter_exclusive and self.is_pitcher) or (accolade_class.is_pitcher_exclusive and not self.is_pitcher):
                continue

            league_and_stat = (f"{self.league} " if self.league != 'MLB' else "") + accolade_class.title
            match accolade_class.value_type:
                case "AWARD (PLACEMENT, PCT)":
                    # MVP, CY YOUNG PLACEMENTS
                    # EX: "2004 NL (1, 91%)""
                    accolade_list_cleaned = [a for a in accolade_list if '(1,' not in a and ', ' in a] # REMOVE ANY TOP FINISHES, THOSE WILL SHOW UP IN AWARDS
                    awards_tuple = []
                    award_name_and_abbr = {
                        "CY YOUNG": ("CY YOUNG" if is_pre_2004 else "CYA"),
                        "MVP": "MVP",
                    }
                    for accolade in accolade_list_cleaned:
                        try:
                            rank_int = int(accolade.split('(',1)[1].split(',')[0])
                        except:
                            continue
                        ordinal_rank = self.ordinal(rank_int).upper()
                        year_parsed = accolade.split(' ', 1)[0]
                        year_str = f"{year_parsed} " if num_seasons > 1 else ''
                        final_string = f"{ordinal_rank} IN {year_str}{league_and_stat}"
                        priority = 1 if rank_int <= 3 else rank_int * accolade_class.priority_multiplier
                        # SHORTEN NAMES IF NECESSARY
                        for type, abbr in award_name_and_abbr.items():
                            final_string = final_string.replace(type, abbr)
                        awards_tuple.append( (final_string, accolade_class.rank, priority) )
                    accolades_rank_and_priority_tuples += awards_tuple
                case "AWARD (NO VOTING)":
                    # GOLD GLOVE, SILVER SLUGGER, ALL STAR
                    # EX: "2001 AL (OF)"
                    accolade_list_cleaned = [a for a in accolade_list if a not in ['ALL MULTIPLE WINNERS']]
                    num_awards = len(accolade_list_cleaned)
                    year_parsed = accolade_list_cleaned[0].split(' ', 1)[0]
                    award_title = accolade_class.title if is_pre_2004 else accolade_class.title.replace('SLUGGER', 'SLG')
                    final_string = f"{num_awards}X {award_title}" if num_awards > 1 and num_seasons > 1 else award_title
                    if num_awards == 1 and num_seasons > 1 and is_pre_2004:
                        final_string = f"{year_parsed} {final_string}"
                    priority = (1 if accolade_class == Accolade.ALL_STAR else 0) if not is_icons or num_awards > 1 else 10 
                    accolades_rank_and_priority_tuples.append( (final_string, accolade_class.rank, priority) )
                case "AWARDS (LIST)":
                    # EX: "2014 NL ROOKIE OF THE YEAR"
                    award_name_and_abbr = {
                        "CY YOUNG": "CY YOUNG",
                        "MVP": "MVP",
                        "ROOKIE OF THE YEAR": "ROY",
                    }
                    # KEEP ONLY CYA, MVP, ROY
                    accolade_list_cleaned = [a for a in accolade_list if len([aw for aw in accolade_class.awards_to_keep if aw in a]) > 0]
                    awards_accolades = []
                    for accolade in accolade_list_cleaned:
                        accolade_split_first_space = accolade.split(' ',1)
                        accolade = accolade.split(' ',1)[1] if num_seasons == 1 and len(accolade_split_first_space) > 1 else accolade
                        # SHORTEN NAMES IF NECESSARY
                        for type, abbr in award_name_and_abbr.items():
                            accolade = accolade.replace(type, abbr)
                        priority = 0 if not is_icons or num_seasons > 1 else (4 if 'MVP' in accolade else 2)
                        awards_accolades.append( (accolade, accolade_class.rank, priority) )

                    if num_seasons > 1:
                        # SORT INTO LIST FOR EACH AWARD TYPE
                        awards_dict = {}
                        awards_list = list(award_name_and_abbr.values())
                        for award_type in awards_list:
                            awards_dict[award_type] = [(a if is_pre_2004 else award_name_and_abbr.get(a,a)) for a in awards_accolades if award_type in a[0]]
                        
                        new_awards_accolades = []
                        for award_type, awards_list in awards_dict.items():
                            num_awards = len(awards_list)
                            if num_awards > 1:
                                new_awards_accolades += [(f"{num_awards}X {award_type}", accolade_class.rank, 0)]
                            else:
                                new_awards_accolades += awards_list
                        awards_accolades = new_awards_accolades

                    accolades_rank_and_priority_tuples += awards_accolades
                case "ORDINAL":

                    # SKIP IF SAVES AND STARTING PITCHER
                    if is_starting_pitcher and accolade_class == Accolade.SAVES:
                        continue

                    def parse_ordinal(value:str, keep_year:bool=False) -> tuple[str, int, int]:
                        year_parsed = value.split(' ', 1)[0]
                        year_str = f"{year_parsed} " if keep_year else ''
                        rank_split_1 = value.split('(',1)[1]
                        rank_str = rank_split_1.split(')')[0]
                        ordinal_rank_int = int(re.sub('[^0-9]','', rank_str))
                        is_leader = ordinal_rank_int == 1
                        final_string = f"{year_str}{league_and_stat} LEADER" if is_leader else f"{rank_str} IN {year_str}{league_and_stat}"
                        if accolade_class == Accolade.BA and is_leader:
                            final_string = final_string.replace('BA LEADER', ba_champ_text)
                        priority = ordinal_rank_int
                        return (final_string, accolade_class.rank, priority * accolade_class.priority_multiplier)
                    
                    # EX: "2001 NL 73 (1ST)"
                    accolade_list_cleaned = [a for a in accolade_list if '(' in a and ')' in a and 'CAREER' not in a]
                    ordinal_accolades = []
                    for accolade in accolade_list_cleaned:
                        ordinal_parsed = parse_ordinal(accolade, keep_year=num_seasons > 1)
                        ordinal_accolades.append( ordinal_parsed )
                    
                    if num_seasons > 1:
                        # REPLACE INDIVIDUAL PLACEMENTS WITH COUNTS ACROSS SEASONS
                        # EX: ['07 NL OPS LEADER, '08 NL OPS LEADER, '11 AL OPS LEADER] -> [3X OPS LEADER]
                        leader_list = []
                        leader_text = ba_champ_text if accolade_class == Accolade.BA else f'{accolade_class.title} LEADER'
                        for accolade_tuple in ordinal_accolades:
                            accolade = accolade_tuple[0]
                            if leader_text in accolade:
                                leader_list.append(accolade)
                        if len(leader_list) > 1:
                            ordinal_accolades = [(f"{len(leader_list)}X {leader_text}" ,accolade_class.rank, 0)]                            

                    accolades_rank_and_priority_tuples += ordinal_accolades
        
        # ADD ROOKIE OF THE YEAR VOTING, NOT INCLUDED IN BREF ACCOLADES SECTION
        awards_summary_list = self.stats.get('award_summary', '').upper().split(',')
        for award in awards_summary_list:
            if 'ROY-' not in award:
                continue
            award_split = award.split('-')
            if len(award_split) > 1:
                award_placement_str = award_split[-1]
                try:
                    award_placement_int = int(award_placement_str)
                except:
                    continue
                # IGNORE 1ST PLACE, ALREADY REPRESENTED ELSEWHERE
                if award_placement_int == 1:
                    continue
                ordinal_rank = self.ordinal(award_placement_int).upper()
                league = f"{self.league} " if self.league != 'MLB' else ''
                accolade_str = f"{ordinal_rank} IN {league}ROY"
                accolades_rank_and_priority_tuples.append( (accolade_str, Accolade.AWARDS.rank, award_placement_int) )
                    
        # CREATE LIST OF CURRENT ACCOLADES
        # USED TO FILTER OUT REDUNDANCIES
        current_accolades = [at[0] for at in accolades_rank_and_priority_tuples]

        # CHECK FOR TRIPLE CROWN
        substrings_triple_crown = [ba_champ_text, 'HR LEADER', 'RBI LEADER']
        num_triple_crown_leading = len([cat for cat in substrings_triple_crown if self.is_substring_in_list(cat, current_accolades)])
        if num_seasons == 1 and not self.is_pitcher and num_triple_crown_leading == 3:
            accolades_rank_and_priority_tuples.append( (f'{self.league} TRIPLE CROWN', 0, 0) )
            accolades_to_remove = []
            for accolade_tuple in accolades_rank_and_priority_tuples:
                for substring in substrings_triple_crown:
                    if substring in accolade_tuple[0]:
                        accolades_to_remove.append(accolade_tuple)
            accolades_rank_and_priority_tuples = [a for a in accolades_rank_and_priority_tuples if a not in accolades_to_remove]

        # -- PART 2: STAT NUMBERS --

        default_stat_priority = 20
        # PITCHERS ----
        if self.is_pitcher:
            if is_starting_pitcher:
                # WINS
                wins = self.stats.get('W', 0)
                if ( (wins / num_seasons) > 14 and not self.is_substring_in_list('WINS',current_accolades) ) or wins >= 300:
                    accolades_rank_and_priority_tuples.append( (f"{wins} WINS", 50, default_stat_priority) )
            else:
                # SAVES
                saves = self.stats.get('SV', 0)
                if (saves / num_seasons) > 20 and not self.is_substring_in_list('SAVES',current_accolades):
                    accolades_rank_and_priority_tuples.append( (f"{saves} SAVES", 51, default_stat_priority) )
            
            # ERA
            era_2_decimals = '%.2f' % self.stats.get('earned_run_avg', 0.0)
            if not self.is_substring_in_list('ERA',current_accolades):
                accolades_rank_and_priority_tuples.append( (f"{era_2_decimals} ERA", 52, default_stat_priority) )

            # WHIP
            whip = self.stats.get('whip', 0.000)
            if not self.is_substring_in_list('WHIP',current_accolades):
                accolades_rank_and_priority_tuples.append( (f"{whip} WHIP", 53, default_stat_priority) )
        
        else:
        # HITTERS ----
            # HOME RUNS
            hr = self.stats.get('HR', 0)
            hr_per_year = hr / num_seasons
            is_hr_all_time = (hr >= 500 or hr_per_year >= 60)
            if ( hr_per_year >= (15 if self.year == 2020 else 30) and not self.is_substring_in_list('HR',current_accolades) ) or is_hr_all_time:
                hr_suffix = "HOME RUNS" if is_pre_2004 else 'HR'
                if is_hr_all_time:
                    # MOVE DOWN PRIORITY OF LEADERS
                    accolades_rank_and_priority_tuples = [( (at[0], at[1], default_stat_priority) if 'HR' in at[0] else at) for at in accolades_rank_and_priority_tuples]
                hr_priority = 0 if is_hr_all_time else default_stat_priority
                accolades_rank_and_priority_tuples.append( (f"{hr} {hr_suffix}", 50, hr_priority) )
                
            # RBI
            rbi = self.stats.get('RBI', 0)
            if (rbi / num_seasons) >= 100 and not self.is_substring_in_list('RBI',current_accolades):
                accolades_rank_and_priority_tuples.append( (f"{rbi} RBI", 51, default_stat_priority) )
            # HITS
            hits = self.stats.get('H', 0)
            hits_per_year = hits / num_seasons
            is_hits_all_time = (hits >= 3000 or hits_per_year >= 240)
            if ( hits_per_year >= 175 and not self.is_substring_in_list('HITS',current_accolades) ) or is_hits_all_time:
                if is_hits_all_time:
                    # MOVE DOWN PRIORITY OF LEADERS
                    accolades_rank_and_priority_tuples = [( (at[0], at[1], default_stat_priority) if 'HITS' in at[0] else at) for at in accolades_rank_and_priority_tuples]
                hits_priority = 0 if is_hits_all_time else default_stat_priority
                accolades_rank_and_priority_tuples.append( (f"{hits} HITS", 52, hits_priority) )
            # BATTING AVG
            ba = self.stats.get('batting_avg', 0.00)
            is_ba_all_time = ba >= 0.390
            if ( ba >= 0.300 and not self.is_substring_in_list('BA',current_accolades) ) or is_ba_all_time:
                ba_3_decimals = ('%.3f' % ba).replace('0.','.')
                ba_suffix = 'BATTING AVG' if is_pre_2004 else "BA"
                ba_priority = 0 if is_ba_all_time else default_stat_priority
                accolades_rank_and_priority_tuples.append( (f"{ba_3_decimals} {ba_suffix}", 53, ba_priority) )
            # OBP
            obp = self.stats.get('onbase_perc', 0.00)
            if obp >= 0.400 and not self.is_substring_in_list('OBP',current_accolades):
                obp_3_decimals = ('%.3f' % obp).replace('0.','.')
                accolades_rank_and_priority_tuples.append( (f"{obp_3_decimals} OBP", 54, default_stat_priority) )
            # SLG
            slg = self.stats.get('slugging_perc', 0.00)
            if slg >= 0.550 and not self.is_substring_in_list('SLG',current_accolades):
                slg_3_decimals = ('%.3f' % slg).replace('0.','.')
                accolades_rank_and_priority_tuples.append( (f"{slg_3_decimals} SLG%", 55, default_stat_priority) )
            # dWAR
            dWAR = self.stats.get('dWAR', 0.00)
            if float(dWAR) >= (2.5 * num_seasons) and not self.is_substring_in_list('DWAR',current_accolades):
                accolades_rank_and_priority_tuples.append( (f"{dWAR} dWAR", 56, 10) )
        
        # GENERIC, ONLY IF EMPTY ----
        length_req = self.set.super_season_text_length_cutoff(index=3)
        usable_accolades = [a for a in accolades_rank_and_priority_tuples if len(a[0]) <= length_req]
        if len(usable_accolades) < 2:
            # OPS+
            ops_plus = self.stats.get('onbase_plus_slugging_plus', None)
            if ops_plus and not self.is_pitcher and not self.is_substring_in_list('OPS+',current_accolades):
                accolades_rank_and_priority_tuples.append( (f"{int(ops_plus)} OPS+", 57, default_stat_priority) )
            # bWAR
            bWAR = self.stats.get('bWAR', None)
            if bWAR:
                accolades_rank_and_priority_tuples.append( (f"{bWAR} WAR", 58, default_stat_priority) )

        sorted_tuples = sorted(accolades_rank_and_priority_tuples, key=lambda t: (t[2],t[1]))
        sorted_accolades = [tup[0] for tup in sorted_tuples]

        return sorted_accolades[0:maximum] if maximum else sorted_accolades

    def has_position(self, position: Position) -> bool:
        """Checks for position in positions list"""
        return position in self.positions_list

    def split_name(self, name:str, is_nickname:bool=False) -> tuple[str, str]:
        """ Splits name into first and last. Handles even split for nicknames 
        
        Args:
          name: Name string to use for split.
          is_nickname: Optional flag for whether it's a nickname.
        """

        # EVENLY SPLIT LONG NICKNAMES
        name_split_full = name.split(" ")
        num_words = len(name_split_full)
        if num_words > 3 and is_nickname:
            middle_index = int(num_words / 2.0)
            first = " ".join(name_split_full[0:middle_index])
            last = " ".join(name_split_full[middle_index:num_words])
            return first, last
            
        # SPLIT NORMALLY
        name_split = name.split(" ", 1)
        first, last = name_split if len(name_split) > 1 else tuple(['', name_split[0]])

        return first, last

# ------------------------------------------------------------------------
# COMMAND / OUTS METHODS
# ------------------------------------------------------------------------

    def __top_accurate_command_out_combos(self, obp:float, num_results:int) -> list[tuple[int, int]]:
        """Finds most accurate combinations of command/out compared to real onbase pct.

        Args:
          obp: Real life onbase percent.
          num_results: How many results included in output.

        Returns:
          List of Top N most accurate command/out tuples.
        """

        # OBP DICT FOR ALL COMMAND OUT COMBOS
        combos = self.__obp_for_command_out_combos()

        combo_accuracies = {}
        for combo, predicted_obp in combos.items():
            obp_for_measurement = 0.001 if obp == 0 else obp
            accuracy = self.__relative_pct_accuracy(actual=obp_for_measurement, measurement=predicted_obp)
            combo_accuracies[combo] = accuracy

        # LIMIT TO TOP N BY ACCURACY
        sorted_combo_accuracies = sorted(combo_accuracies.items(), key=operator.itemgetter(1), reverse=True)
        top_combo_accuracies = sorted_combo_accuracies[:num_results]
        top_command_out_tuples = [c[0] for c in top_combo_accuracies]

        return top_command_out_tuples

    def __obp_for_command_out_combos(self):
        """Values to be compared against to decide command and out for player.
           Uses constants from showdown_constants.py.

        Args:
          None

        Returns:
          Dict with tuples of command, outs and their corresponding obp.
        """

        # STATIC COMBINATIONS LIST
        command_out_combos = self.set.command_out_combinations(player_type=self.player_type)

        # CALCULATE ONBASE PCT FOR EACH COMBO
        combo_and_obps = {}
        for combo in command_out_combos:
            command = combo[0]
            outs = combo[1]
            command_out_matchup = self.__onbase_control_outs(command, outs)
            predicted_obp = self.__obp_for_command_outs(command_out_matchup)
            key = (command, outs)
            combo_and_obps[key] = predicted_obp

        return combo_and_obps

    def __onbase_control_outs(self, command:int=0, outs:int=0, era_override:Era = None) -> dict[str, int]:
        """Give information needed to perform calculations of results.
           These numbers are needed to predict obp, home_runs, ...

        Args:
          command: The Onbase or Control number of player.
          outs: The number of out results on the player's chart.
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          Dict object with onbase, control, pitcher outs, hitter outs
        """
        era = era_override if era_override else self.era
        baseline_hitter = self.set.baseline_chart(player_type=PlayerType.HITTER, era=era)
        baseline_pitcher = self.set.baseline_chart(player_type=PlayerType.PITCHER, era=era)
        onbase_baseline = baseline_hitter.command if self.test_numbers is None else self.test_numbers[0]
        hitter_outs_baseline = baseline_hitter.outs if self.test_numbers is None else self.test_numbers[1]
        control_baseline = baseline_pitcher.command if self.test_numbers is None else self.test_numbers[0]
        pitcher_outs_baseline = baseline_pitcher.outs if self.test_numbers is None else self.test_numbers[1]

        return {
            'onbase': command if not self.is_pitcher else onbase_baseline,
            'hitterOuts': outs if not self.is_pitcher else hitter_outs_baseline,
            'control': command if self.is_pitcher else control_baseline,
            'pitcherOuts': outs if self.is_pitcher else pitcher_outs_baseline
        }

    def opponent_stats_for_calcs(self, command:int, era_override:Era = None) -> tuple[Chart, float, float]:
        """Convert __onbase_control_outs info to be specific to self.
           Used to derive:
             1. opponent_chart
             2. my_advantages_per_20
             3. opponent_advantages_per_20

        Args:
          command: The Onbase or Control number of player.
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          Tuple with opponent_chart, my_advantages_per_20, opponent_advantages_per_20
        """

        era = era_override if era_override else self.era
        if not self.is_pitcher:
            opponent_chart = self.set.baseline_chart(player_type=PlayerType.PITCHER, era=era)
            my_advantages_per_20 = command-self.__onbase_control_outs(era_override=era_override)['control']
            opponent_advantages_per_20 = 20 - my_advantages_per_20
        else:
            opponent_chart = self.set.baseline_chart(player_type=PlayerType.HITTER, era=era)
            opponent_advantages_per_20 = self.__onbase_control_outs(era_override=era_override)['onbase']-command
            my_advantages_per_20 = 20 - opponent_advantages_per_20

        return opponent_chart, my_advantages_per_20, opponent_advantages_per_20

    def __obp_for_command_outs(self, command_out_matchup:dict[str, float]) -> float:
        """Calc OBP for command out matchup

        Args:
          command_out_matchup: Dictionary of onbase, control, outs from hitter and pitcher

        Returns:
          Float with obp for given command out matchup.
        """
        return self.__pct_rate_for_result(
            onbase = command_out_matchup['onbase'],
            control = command_out_matchup['control'],
            num_results_hitter_chart = 20-command_out_matchup['hitterOuts'],
            num_results_pitcher_chart = 20-command_out_matchup['pitcherOuts']
        )


# ------------------------------------------------------------------------
# CHART METHODS
# ------------------------------------------------------------------------

    def __most_accurate_chart(self, command_out_combos: list[tuple[int, int]], stats_per_400_pa:dict, offset:int) -> tuple[Chart, dict]:
        """Compare accuracy of all the command/outs combinations.

        Args:
          command_out_combos: List of command/out tuples to test.
          stats_per_400_pa: Dict with number of results for a given
                            category per 400 PA (ex: {'hr_per_400_pa': 23.65})
          offset: Index of chart accuracy selected.

        Returns:
          The dictionary containing stats for the most accurate command/out
          combination.
          A dictionary containing real life metrics (obp, slg, ...) per 400 PA.
        """

        chart_and_accuracies = []

        for command_out_tuple in command_out_combos:
            command = command_out_tuple[0]
            outs = command_out_tuple[1]
            chart, accuracy, projected = self.__chart_with_accuracy(
                                            command=command,
                                            outs=outs,
                                            stats_for_400_pa=stats_per_400_pa
                                          )
            chart_and_accuracies.append( (command_out_tuple, chart, accuracy, projected) )

        chart_and_accuracies.sort(key=operator.itemgetter(2),reverse=True)
        best_chart = chart_and_accuracies[offset][1]
        self.command_out_accuracies = { f"{ca[0][0]}-{ca[0][1]}": round(ca[2],4) for ca in chart_and_accuracies }
        projected_stats_for_best_chart = chart_and_accuracies[offset][3]

        return best_chart, projected_stats_for_best_chart

    def __chart_with_accuracy(self, command:int, outs:int, stats_for_400_pa:dict, era_override:Era = None) -> tuple[Chart, float, dict]:
        """Create Player's chart and compare back to input stats.

        Args:
          command: Onbase (Hitter) or Control (Pitcher) of the Player.
          outs: Number of Outs on the Player's chart.
          stats_per_400_pa: Dict with number of results for a given
                            category per 400 PA (ex: {'hr_per_400_pa': 23.65})
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          - Chart Object.
          - Accuracy of chart compared to original input.
          - Dict of Player's chart converted to real stat output.
        """

        # NEED THE OPPONENT'S CHART TO CALCULATE NUM OF RESULTS FOR RESULT
        opponent_chart, my_advantages_per_20, opponent_advantages_per_20 = self.opponent_stats_for_calcs(command=command, era_override=era_override)

        # CREATE THE CHART DICTIONARY
        chart = Chart(
            is_pitcher=self.is_pitcher, 
            set=self.set.value, 
            command=command, 
            outs=outs, 
            is_expanded=self.set.has_expanded_chart, 
            dbl_per_400_pa = round(stats_for_400_pa.get('2b_per_400_pa', 0), 4),
            trpl_per_400_pa = round(stats_for_400_pa.get('3b_per_400_pa', 0), 4),
            hr_per_400_pa = round(stats_for_400_pa.get('hr_per_400_pa', 0), 4)
        )

        for category, results_per_400_pa in stats_for_400_pa.items():
            if '_per_400_pa' in category and category != 'h_per_400_pa':

                # CONVERT EACH REAL STAT CATEGORY INTO NUMBER OF RESULTS ON CHART
                key:str = category[:2]

                # STOLEN BASES HAS NO OPPONENT RESULTS
                if key == 'sb':
                    chart.sb = round(results_per_400_pa / stats_for_400_pa['pct_of_400_pa'], 3)
                    continue              
            
                # CALCULATE NUM OF RESULTS
                chart_category = ChartCategory(key.upper())
                opponent_values = opponent_chart.num_values(chart_category)
                chart_results = (results_per_400_pa - (opponent_advantages_per_20*opponent_values)) / my_advantages_per_20
                
                if chart_category == ChartCategory.SO:
                    chart_results = self.__so_results(current_so=chart_results, num_out_slots=outs)
                
                # HANDLE CASE OF < 0
                chart_results = chart_results if chart_results > 0 else 0

                # WE ROUND THE PREDICTED RESULTS (2.4 -> 2, 2.5 -> 3)
                if self.is_pitcher and chart_category == ChartCategory.HR and chart_results < 1.0:
                    # TRADITIONAL ROUNDING CAUSES TOO MANY PITCHER HR RESULTS
                    chart_results_decimal = chart_results % 1
                    era = era_override if era_override else self.era
                    rounded_results = round(chart_results) if chart_results_decimal > era.hr_rounding_cutoff else math.floor(chart_results)
                else:                    
                    rounded_results = round(chart_results)
                # PITCHERS SHOULD ALWAYS GET 0 FOR 3B
                rounded_results = 0 if self.is_pitcher and chart_category == ChartCategory._3B else rounded_results
                # CHECK FOR BARRY BONDS EFFECT (HUGE WALK)
                rounded_results = 12 if chart_category == ChartCategory.BB and rounded_results > 13 else rounded_results
                # MAX HR RESULTS AT 10
                rounded_results = 10 if chart_category == ChartCategory.HR and rounded_results > 10 else rounded_results
                # MAX 2B RESULTS AT 12
                rounded_results = 12 if chart_category == ChartCategory._2B and rounded_results > 12 else rounded_results
                chart.values[chart_category] = rounded_results

        # FILL "OUT" CATEGORIES (PU, GB, FB)
        out_slots_remaining = outs - float(chart.num_values(ChartCategory.SO))
        pu, gb, fb = self.__out_results(
                        gb_pct=stats_for_400_pa.get('GO/AO', None),
                        popup_pct=stats_for_400_pa.get('IF/FB', None),
                        out_slots_remaining=out_slots_remaining,
                        slg=stats_for_400_pa.get('slugging_perc', None),
                        era_override=era_override
                    )
        chart.values.update({
            ChartCategory.PU: pu,
            ChartCategory.GB: gb,
            ChartCategory.FB: fb,
        })

        # CALCULATE HOW MANY SPOTS ARE LEFT TO FILL 1B AND 1B+
        remaining_slots = chart.remaining_slots(excluded_categories=[ChartCategory._1B])
        chart.check_and_fix_value_overage(excluded_categories=[ChartCategory._1B])
        remaining_slots = chart.remaining_slots(excluded_categories=[ChartCategory._1B]) # RE-CHECK
        remaining_slots_qad = 0 if remaining_slots < 0 else remaining_slots

        # FILL 1B AND 1B+
        stolen_bases = int(stats_for_400_pa.get('sb_per_400_pa',0))
        single_results, single_plus_results = self.__single_and_single_plus_results(remaining_slots_qad,stolen_bases,command)
        chart.values.update({
            ChartCategory._1B: single_results,
            ChartCategory._1B_PLUS: single_plus_results,
        })
        chart.generate_range_strings()

        # CHECK ACCURACY COMPARED TO REAL LIFE
        in_game_stats_for_400_pa = self.chart_to_results_per_400_pa(chart,my_advantages_per_20,opponent_chart,opponent_advantages_per_20, era_override=era_override)
        weights = self.set.chart_accuracy_slashline_weights(player_sub_type=self.player_sub_type)
        accuracy, _, _ = self.accuracy_between_dicts(
            actuals_dict=stats_for_400_pa,
            measurements_dict=in_game_stats_for_400_pa,
            weights=weights,
            only_use_weight_keys=True
        )
        
        # QA: CHANGE ACCURACY TO 0 IF CHART DOESN'T ADD UP TO 20
        accuracy = 0.0 if chart.is_num_values_over_20 else accuracy

        # ADD WEIGHTING OF ACCURACY
        # LIMITS AMOUNT OF RESULTS PER SET FOR CERTAIN COMMAND/OUT COMBINATIONS
        weight = self.set.command_out_accuracy_weighting(command=command, outs=outs)
        accuracy = accuracy * weight

        return chart, accuracy, in_game_stats_for_400_pa

    def __out_results(self, gb_pct:float, popup_pct:float, out_slots_remaining:int, slg:float, era_override:Era = None) -> tuple[int, int, int]:
        """Determine distribution of out results for Player.

        Args:
          gb_pct: Percent Ground Outs vs Air Outs.
          popup_pct: Percent hitting into a popup.
          out_slots_remaining: Total # Outs - SO
          slg: Real-life stats slugging percent.
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          Tuple of PU, GB, FB out result ints.
        """

        # SET DEFAULTS FOR EMPTY DATA, BASED ON SLG
        if gb_pct is None or popup_pct is None:
            slg_range = ValueRange(min = 0.250, max = 0.500)
            slg_percentile = slg_range.percentile(value=slg)
            multiplier = 1.0 if slg_percentile < 0 else 1.0 - slg_percentile
            gb_pct = gb_pct if gb_pct else round(1.5 * max(multiplier, 0.5),3)
            popup_pct = popup_pct if popup_pct else round(0.16 * max(multiplier, 0.5),3)

        era = era_override if era_override else self.era
        if out_slots_remaining > 0:
            # MULTIPLIERS SERVE TO CORRECT TOWARDS WOTC
            # REPLACE HAVING DEFAULT FOR OPPONENT CHART
            gb_multiplier = self.set.gb_multiplier(player_type=self.player_type, era=era)
            # SPLIT UP REMAINING SLOTS BETWEEN GROUND AND AIR OUTS
            gb_outs = int(round((out_slots_remaining / (gb_pct + 1)) * gb_pct * gb_multiplier))
            air_outs = out_slots_remaining - gb_outs
            # FOR PU, ADD A MULTIPLIER TO ALIGN MORE WITH OLD SCHOOL CARDS
            pu_multiplier = self.set.pu_multiplier
            pu_outs = 0 if not self.is_pitcher else int(math.ceil(air_outs*popup_pct*pu_multiplier))
            pu_outs = air_outs if pu_outs > air_outs else pu_outs
            fb_outs = int(air_outs-pu_outs)
        else:
            fb_outs = 0
            pu_outs = 0
            gb_outs = 0

        return pu_outs, gb_outs, fb_outs

    def __so_results(self, current_so:int, num_out_slots:int) -> int:
        """Update SO chart value to account for outliers and maximums

        Args:
          current_so: Number of slots currently occupied
          num_out_slots: Total numbers of slots for outs available.

        Returns:
          Updated SO chart slots.
        """

        # FOR PITCHERS, SIMPLY RETURN CURRENT SO NUMBER
        if self.is_pitcher:
            return min(current_so, num_out_slots)
        
        # --- HITTERS ---
        hard_limit_hitter = min(num_out_slots, self.set.hitter_so_results_hard_cap)
        soft_limit_hitter = self.set.hitter_so_results_soft_cap
        
        # IF HITTER'S STRIKEOUTS ARE UNDER SOFT LIMIT, RETURN CURRENT RESULTS
        if current_so < soft_limit_hitter:
            return min(current_so, hard_limit_hitter)
        
        # IF PLAYER HAS SMALL SAMPLE SIZE, USE SOFT LIMIT AS HARD CAP
        real_pa = self.stats.get('PA', 400)
        if real_pa < 100:
            return min(current_so, hard_limit_hitter, soft_limit_hitter)
        
        # IF PLAYER IS OVER THE SOFT LIMIT, SCALE BACK RESULTS TOWARDS SOFT CAP AND USE FLOOR INSTEAD OF ROUND
        if current_so > soft_limit_hitter:
            multiplier = 0.80
            current_so *= multiplier
            current_so = max(soft_limit_hitter, current_so) # MAKE SURE MULTIPLIER DOESN'T MOVE CARD UNDER SOFT LIMIT
            current_so = math.floor(current_so)
            return min(current_so, hard_limit_hitter)

        return min(current_so, hard_limit_hitter)

    def __single_and_single_plus_results(self, remaining_slots:int, sb:int, command:int) -> tuple[int, int]:
        """Fill 1B and 1B+ categories on chart.

        Args:
          remaining_slots: Remaining slots out of 20.
          sb: Stolen bases per 400 PA
          command: Player's Onbase number

        Returns:
          Tuple of 1B, 1B+ result ints.
        """

        # PITCHER HAS NO 1B+
        if self.is_pitcher:
            return remaining_slots, 0

        # DIVIDE STOLEN BASES PER 400 PA BY A SCALER BASED ON ONBASE #
        onbase_range = ValueRange(min=self.set.min_onbase_single_plus, max=self.set.max_onbase_single_plus)
        min_denominator = self.set.hitter_single_plus_denominator_minimum
        max_denominator = self.set.hitter_single_plus_denominator_maximum
        onbase_pctile = onbase_range.percentile(value=command)
        single_plus_denominator = min_denominator + ( (max_denominator-min_denominator) * onbase_pctile )
        single_plus_results_raw = math.trunc(sb / single_plus_denominator)

        # MAKE SURE 1B+ IS NOT OVER REMAINING SLOTS
        single_plus_results = single_plus_results_raw if single_plus_results_raw <= remaining_slots else remaining_slots
        single_results = remaining_slots - single_plus_results

        return single_results, single_plus_results

# ------------------------------------------------------------------------
# REAL LIFE STATS METHODS
# ------------------------------------------------------------------------

    def __stats_per_n_pa(self, plate_appearances:int, stats:dict) -> dict:
        """Season stats per every n Plate Appearances.

        Args:
          plate_appearances: Number of Plate Appearances to be converted to.
          stats: Dict of stats for season.

        Returns:
          Dict of stats weighted for n PA.
        """

        # SUBTRACT SACRIFICES?
        sh = stats.get('SH', 0)
        pct_of_n_pa = (float(stats['PA']) - sh) / plate_appearances

        # POPULATE DICT WITH VALUES UNCHANGED BY SHIFT IN PA
        stats_for_n_pa = {
            'PA': plate_appearances,
            'pct_of_{}_pa'.format(plate_appearances): pct_of_n_pa,
            'slugging_perc': float(stats['slugging_perc']) if len(str(stats['slugging_perc'])) > 0 else 1.0,
            'onbase_perc': float(stats['onbase_perc']) if len(str(stats['onbase_perc'])) > 0 else 1.0,
            'batting_avg': float(stats['batting_avg']) if len(str(stats['batting_avg'])) > 0 else 1.0,
            'IF/FB': stats.get('IF/FB', 0.2),
            'GO/AO': stats.get('GO/AO', 1.0),
        }

        # ADD RESULT OCCURANCES PER N PA
        chart_result_categories = ['SO','BB','1B','2B','3B','HR','SB','H']
        for category in chart_result_categories:
            key = '{}_per_{}_pa'.format(category.lower(), plate_appearances)
            stat_value = int(stats[category]) if len(str(stats[category])) > 0 else 0
            stats_for_n_pa[key] = stat_value / pct_of_n_pa

        return stats_for_n_pa

    def __pct_rate_for_result(self, onbase:float, control:float, num_results_hitter_chart:float, num_results_pitcher_chart:float, hitter_denom_adjust:float=0.0,pitch_denom_adjust:float=0.0) -> float:
        """Percent chance a result will happen.

        Args:
          onbase: Hitter's command number.
          control: Pitcher's command number.
          num_results_hitter_chart: Number of results for the outcome located on hitter's chart.
          num_results_pitcher_chart: Number of results for the outcome located on pitcher's chart.
          hitter_denom_adjust: Adjust denominator for hitter calcs by subtraction.
          pitch_denom_adjust: Adjust denominator for pitcher calcs by subtraction.
        
        Returns:
          Percent change a given result will occur.
        """

        # PROBABILITY OF ADVANTAGE FOR HITTER AND PITCHER
        hitter_denominator = 20.0 - hitter_denom_adjust
        pitcher_denominator = 20.0 - pitch_denom_adjust
        prob_hitter_advantage = (onbase-control) / 20.0
        prob_pitcher_advantage = 1.0 - prob_hitter_advantage
        # PROBABILTY OF RESULT ASSUMING ADVANTAGE
        prob_result_after_hitter_advantage = num_results_hitter_chart / hitter_denominator if hitter_denominator != 0 else 0
        prob_result_after_pitcher_advantage = num_results_pitcher_chart / pitcher_denominator if pitcher_denominator != 0 else 0
        # ADD PROBABILITY OF RESULT FOR BOTH PATHS (HITTER ADV AND PITCHER ADV)
        rate = (prob_hitter_advantage * prob_result_after_hitter_advantage) \
               + (prob_pitcher_advantage * prob_result_after_pitcher_advantage)

        return rate

    def chart_to_results_per_400_pa(self, chart:Chart, my_advantages_per_20:float, opponent_chart:Chart, opponent_advantages_per_20:float, era_override:Era = None) -> dict:
        """Predict real stats given Showdown in game chart.

        Args:
          chart: Chart object.
          my_advantages_per_20: Number of advantages my Player gets out of 20 (i.e. 5). Can be a float.
          opponent_chart: Dict for chart of baseline opponent.
          opponent_advantages_per_20: Number of advantages opponent gets out of 20 (i.e. 15). Can be a float.
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          Dict with stats per 400 Plate Appearances.
        """

        # MATCHUP VALUES
        command_out_matchup = self.__onbase_control_outs(chart.command, chart.outs, era_override=era_override)
        strikeouts_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart.num_values(ChartCategory.SO),
                                                                    opponent_results=opponent_chart.num_values(ChartCategory.SO),
                                                                    my_advantages_per_20=my_advantages_per_20,
                                                                    opponent_advantages_per_20=opponent_advantages_per_20)
        walks_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart.num_values(ChartCategory.BB),
                                                               opponent_results=opponent_chart.num_values(ChartCategory.BB),
                                                               my_advantages_per_20=my_advantages_per_20,
                                                               opponent_advantages_per_20=opponent_advantages_per_20)
        singles_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart.num_values(ChartCategory._1B) + chart.num_values(ChartCategory._1B_PLUS),
                                                                 opponent_results=opponent_chart.num_values(ChartCategory._1B),
                                                                 my_advantages_per_20=my_advantages_per_20,
                                                                 opponent_advantages_per_20=opponent_advantages_per_20)
        doubles_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart.num_values(ChartCategory._2B),
                                                                 opponent_results=opponent_chart.num_values(ChartCategory._2B),
                                                                 my_advantages_per_20=my_advantages_per_20,
                                                                 opponent_advantages_per_20=opponent_advantages_per_20)
        triples_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart.num_values(ChartCategory._3B),
                                                                 opponent_results=opponent_chart.num_values(ChartCategory._3B),
                                                                 my_advantages_per_20=my_advantages_per_20,
                                                                 opponent_advantages_per_20=opponent_advantages_per_20)
        home_runs_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart.num_values(ChartCategory.HR),
                                                                   opponent_results=opponent_chart.num_values(ChartCategory.HR),
                                                                   my_advantages_per_20=my_advantages_per_20,
                                                                   opponent_advantages_per_20=opponent_advantages_per_20)
        hits_per_400_pa = round(singles_per_400_pa) \
                            + round(doubles_per_400_pa) \
                            + round(triples_per_400_pa) \
                            + round(home_runs_per_400_pa)
        # SLASH LINE

        # BA
        batting_avg = hits_per_400_pa / (400.0 - walks_per_400_pa)

        # OBP
        onbase_results_per_400_pa = round(walks_per_400_pa) + hits_per_400_pa
        obp = onbase_results_per_400_pa / 400.0
        obp = self.__obp_for_command_outs(command_out_matchup)
        # SLG
        slugging_pct = self.__slugging_pct(ab=400-walks_per_400_pa,
                                           singles=singles_per_400_pa,
                                           doubles=doubles_per_400_pa,
                                           triples=triples_per_400_pa,
                                           homers=home_runs_per_400_pa)
        # GROUP ESTIMATIONS IN DICTIONARY
        results_per_400_pa = {
            'so_per_400_pa': strikeouts_per_400_pa,
            'bb_per_400_pa': walks_per_400_pa,
            '1b_per_400_pa': singles_per_400_pa,
            '2b_per_400_pa': doubles_per_400_pa,
            '3b_per_400_pa': triples_per_400_pa,
            'hr_per_400_pa': home_runs_per_400_pa,
            'h_per_400_pa': hits_per_400_pa,
            'batting_avg': batting_avg,
            'onbase_perc': obp,
            'slugging_perc': slugging_pct,
        }

        return results_per_400_pa

    def __result_occurances_per_400_pa(self, my_results:float, opponent_results:float, my_advantages_per_20:float, opponent_advantages_per_20:float) -> float:
        """Predict real stats given Showdown in game chart.

        Args:
          my_results: Number of results on my Player chart.
          opponent_results: Number of results on opponents chart.
          my_advantages_per_20: Int number of advantages my Player gets out of 20 (i.e. 5).
          opponent_advantages_per_20: Int number of advantages opponent gets out of 20 (i.e. 15).

        Returns:
          Number of occurances per 400 PA
        """
        return ((my_results * my_advantages_per_20) + (opponent_results * opponent_advantages_per_20))

    def __slugging_pct(self, ab:float, singles:float, doubles:float, triples:float, homers:float)  -> float:
        """ Calculate Slugging Pct"""
        return (singles + (2 * doubles) + (3 * triples) + (4 * homers)) / ab

    def projected_statline(self, stats_per_400_pa:dict, command: int) -> dict:
        """Predicted season stats (650 PA)

        Args:
          stats_per_400_pa: Stats and Ratios weighted for every 400 plate appearances.
          command: Player Onbase or Control

        Returns:
          Dict with stats for 650 PA.
        """

        stats_per_650_pa = {}

        for category, value in stats_per_400_pa.items():
            if 'per_400_pa' in category:
                # CONVERT TO 650 PA
                stats_per_650_pa[category.replace('400', '650')] = round(value * 650 / 400,2)
            else:
                # PCT VALUE (OBP, SLG, BA, ...)
                stats_per_650_pa[category] = round(value,4)

        # ADD OPS
        keys = stats_per_650_pa.keys()
        has_slg_and_obp = 'onbase_perc' in keys and 'slugging_perc' in keys
        if has_slg_and_obp:
            stats_per_650_pa['onbase_plus_slugging'] = round(stats_per_650_pa['onbase_perc'] + stats_per_650_pa['slugging_perc'], 4)

        # ADD shOPS+ (SHOWDOWN OPS+ EQUIVALENT)
        try:
            stats_per_650_pa['onbase_plus_slugging_plus'] = self.calculate_shOPS_plus(command=command, proj_obp=stats_per_650_pa['onbase_perc'], proj_slg=stats_per_650_pa['slugging_perc'])
        except:
            stats_per_650_pa['onbase_plus_slugging_plus'] = None
        
        return stats_per_650_pa


# ------------------------------------------------------------------------
# PLAYER VALUE METHODS
# ------------------------------------------------------------------------

    def calculate_points(self, projected:dict, positions_and_defense:dict[Position, int], speed_or_ip:int) -> Points:
        """Derive player's value. Uses constants to compare against other cards in set.

        Args:
          projected: Dict with projected metrics (obp, ba, ...) for 650 PA (~ full season)
          positions_and_defense: Dict with all valid positions and their corresponding defensive rating.
          speed_or_ip: In game speed ability or innings pitched.

        Returns:
          Breakdown of points categories
        """

        points = Points()

        # PARSE POSITION MULTIPLIER
        pts_multiplier = self.set.pts_command_out_multiplier(command=self.chart.command, outs=self.chart.outs)
        points.command_out_multiplier = pts_multiplier

        # SLASH LINE VALUE
        allow_negatives = self.set.pts_allow_negatives(self.player_sub_type)

        # SLASHLNE METRICS (AND HR IF HITTER)
        slash_metrics = [PointsMetric.ONBASE, PointsMetric.AVERAGE, PointsMetric.SLUGGING] + ([] if self.is_pitcher else [PointsMetric.HOME_RUNS])
        for slash_metric in slash_metrics:
            # OBP
            range = self.set.pts_range_for_metric(metric=slash_metric, player_sub_type=self.player_sub_type)
            percentile = range.percentile(value=projected.get(slash_metric.metric_name_bref), is_desc=self.is_pitcher, allow_negative=allow_negatives)
            pts_weight = self.set.pts_metric_weight(player_sub_type=self.player_sub_type, metric=slash_metric)
            setattr(points, slash_metric.points_breakdown_attr_name, round(pts_weight * percentile * pts_multiplier, 3))

        # USE EITHER SPEED OR IP DEPENDING ON PLAYER TYPE
        spd_ip_category = PointsMetric.IP if self.is_pitcher else PointsMetric.SPEED
        allow_negatives_speed_ip = True if self.is_pitcher else allow_negatives
        spd_ip_percentile = self.set.pts_speed_or_ip_percentile_range(self.player_sub_type).percentile(value=speed_or_ip, is_desc=False, allow_negative=allow_negatives_speed_ip)
        ip_under_5_negative_multiplier = self.player_sub_type.ip_under_5_negative_multiplier if speed_or_ip < 5 else 1.0
        spd_ip_weight = self.set.pts_metric_weight(player_sub_type=self.player_sub_type, metric=spd_ip_category) * ip_under_5_negative_multiplier
        setattr(points, spd_ip_category.points_breakdown_attr_name, round(spd_ip_weight * spd_ip_percentile, 3))

        if not self.is_pitcher:
            # AVERAGE POINT VALUE ACROSS POSITIONS
            defense_points = 0
            for position, fielding in positions_and_defense.items():
                if position != Position.DH:
                    percentile = fielding / self.set.position_defense_max(position=position)
                    position_pts = percentile * self.set.pts_metric_weight(player_sub_type=self.player_sub_type, metric=PointsMetric.DEFENSE)
                    position_pts = position_pts * self.set.pts_positional_defense_weight(position=Position(position))
                    defense_points += position_pts
            use_avg = list(positions_and_defense.keys()) == [Position.CF, Position.LFRF] or list(positions_and_defense.keys()) == [Position.LFRF, Position.CF]
            num_positions_w_non_zero_def = len([pos for pos, df in positions_and_defense.items() if df != 0])
            num_positions = max(num_positions_w_non_zero_def, 1)
            avg_points_per_position = defense_points / (num_positions if num_positions < 2 or use_avg else ( (num_positions + 2) / 3.0))
            points.defense = round(avg_points_per_position,3)

        # CLOSER BONUS (00 ONLY)
        apply_closer_bonus = self.has_position(Position.CL) and self.set == Set._2000
        points.bonus = 25 if apply_closer_bonus else 0

        # ICONS (03+)
        icon_pts = 0
        if self.set.has_icon_pts and len(self.icons) > 0:
            for icon in self.icons:
                icon_pts += icon.points
        points.icons = round(icon_pts,3)

        # --- APPLY ANY ADDITIONAL PT ADJUSTMENTS FOR DIFFERENT SETS ---

        # SOME SETS PULL CARDS SLIGHTLY TOWARDS THE MEDIAN
        points = self.__normalize_points_towards_median(points)

        # ADJUST POINTS FOR RELIEVERS WITH 2X IP
        if self.player_sub_type == PlayerSubType.RELIEF_PITCHER:
            multi_inning_points_multiplier = self.set.pts_reliever_ip_multiplier(ip=self.ip)
            if multi_inning_points_multiplier > 1.0:
                points.multi_inning_mutliplier = multi_inning_points_multiplier
        
        if self.is_pitcher:
            # PITCHERS GET PTS FOR OUT DISTRIBUTION IN SOME SETS
            out_dist_pts_weight = self.set.pts_metric_weight(player_sub_type=self.player_sub_type, metric=PointsMetric.OUT_DISTRIBUTION)
            if out_dist_pts_weight:
                percentile_gb = self.set.pts_gb_min_max_dict.percentile(value=self.chart.gb_pct, allow_negative=True)          
                points.out_distribution = round(out_dist_pts_weight * percentile_gb,3)

        return points

    def __normalize_points_towards_median(self, points:Points) -> Points:
        """Normalize points for subset on players towards the median.

        Args:
          points: Current Points object

        Returns:
          Updated PTS total for player after normalization.
        """

        if not self.set.pts_normalize_towards_median(self.player_sub_type):
            return points

        # NORMALIZE SCORE ACROSS MEDIAN
        type_normalizer_weight = self.set.pts_normalizer_weighting(player_sub_type=self.player_sub_type)
        median = 310 / type_normalizer_weight
        upper_limit = self.set.pts_normalizer_upper_limit
        upper_limit = upper_limit / type_normalizer_weight

        # CHECK FOR STARTER WITH LOW IP
        if self.player_sub_type == PlayerSubType.STARTING_PITCHER and self.ip < 7 and points.total_points_unrounded < 550:
            pts_percentile = self.set.pts_speed_or_ip_percentile_range(self.player_sub_type).percentile(value=7, is_desc=False, allow_negative=True)
            pts_ip_add = self.set.pts_metric_weight(player_sub_type=self.player_sub_type, metric=PointsMetric.IP) * pts_percentile
            pts_to_compare = round(points.total_points_unrounded + pts_ip_add, -1)
        else:
            pts_to_compare = round(points.total_points_unrounded, -1)

        # RETURN CURRENT OBJECT IF LESS THAN CUTOFF
        if pts_to_compare < self.player_sub_type.pts_normalizer_cutoff:
            return points

        normalizer_value_range = ValueRange(min=median, max=upper_limit)
        percentile = normalizer_value_range.percentile(
            value = pts_to_compare if pts_to_compare < upper_limit else upper_limit,
            is_desc = True
        )
        upper_multiplier = 1.0
        lower_multiplier = self.set.pts_normalizer_lower_threshold(player_sub_type=self.player_sub_type)
        multiplier = percentile * (upper_multiplier - lower_multiplier) + lower_multiplier

        # APPLY THIS TO OFFENSIVE STATS
        points.obp = round(points.obp * multiplier,3)
        points.ba = round(points.ba * multiplier,3)
        points.slg = round(points.slg * multiplier,3)

        if not self.is_pitcher:
            points.hr = round(points.hr * multiplier,3)

        points.normalizer = round(multiplier,3)
        return points

    def calculate_shOPS_plus(self, command:int, proj_obp:float, proj_slg:float) -> float:
        """Calculates shoOPS+ metric.

        shOPS+ provides context around projected OPS numbers accounting for Command adjustments.

        Args:
          - command: Player's command (Onbase or Control).
          - proj_obp: Player's in-game projected OBP against baseline opponent.
          - proj_slg: Player's in-game projected SLG against baseline opponent.

        Returns:
          shOPS+ number (100 is avg). Rounded to one decimal place.
        """

        # -- CHECK FOR CONSTANTS --
        key_command = 'command'
        key_obp = 'obp'
        key_slg = 'slg'
        type = 'Pitcher' if self.is_pitcher else 'Hitter'
        years_list_str = [str(yr) for yr in self.year_list]
        sources_dict = {
            key_command: sc.LEAGUE_AVG_COMMAND[self.set.value], 
            key_obp: sc.LEAGUE_AVG_PROJ_OBP[self.set.value],
            key_slg: sc.LEAGUE_AVG_PROJ_SLG[self.set.value],
        }
        metric_values_list_dict = {}
        for metric, source in sources_dict.items():
            values_list = []
            for year in years_list_str:
                # SKIP IF AVG DOESN'T EXIST
                if year not in source.keys():
                    continue
                if type not in source[year].keys():
                    continue
                    
                # ADD VALUE TO LIST
                values_list.append(source[year][type])
            
            if len(values_list) == 0:
                # NO RESULTS, RETURN NONE
                return None
            
            # TAKE AVG OF EACH YEAR IF MULTI YEAR CARD
            metric_values_list_dict[metric] = round(statistics.mean(values_list),3)

        # -- CALCULATE ADJUSTMENT FACTOR --
        # ADJUSTMENT FACTOR USED TO ACCOUNT FOR TYPICAL SHOWDOWN ROSTER BUILDS THAT FEATURE HIGHER COMMAND PLAYERS.
        # WILL SLIGHTLY ADJUST EXPECTED OPS UP FOR HIGHER COMMAND AND DOWN FOR LOWER COMMAND.
        # WORKS BY COMPARING TO THE AVG COMMAND IN THAT GIVEN YEAR.
        lg_avg_command = metric_values_list_dict[key_command]
        is_below_avg = command < lg_avg_command
        negative_multiplier = -1 if is_below_avg else 1
        abs_pct_above_or_below_avg = abs(command - lg_avg_command) / lg_avg_command
        command_adjustment_factor = 1.0 + ( abs_pct_above_or_below_avg * self.set.shOPS_command_adjustment_factor_weight * negative_multiplier)

        # -- CALCULATE FINAL shOPS+ --
        lg_avg_obp = metric_values_list_dict[key_obp]
        lg_avg_slg = metric_values_list_dict[key_slg]
        obp_numerator = lg_avg_obp if self.is_pitcher else proj_obp
        obp_denominator = proj_obp if self.is_pitcher else lg_avg_obp
        slg_numerator = lg_avg_slg if self.is_pitcher else (proj_slg * command_adjustment_factor)
        slg_denominator = (proj_slg / command_adjustment_factor) if self.is_pitcher else lg_avg_slg

        shOPS_plus = round(100 * ( (obp_numerator / obp_denominator) + (slg_numerator / slg_denominator) - 1), 0)
        
        return shOPS_plus


# ------------------------------------------------------------------------
# GENERIC METHODS
# ------------------------------------------------------------------------

    def accuracy_between_dicts(self, actuals_dict:dict, measurements_dict:dict, weights:dict={}, all_or_nothing:list[str]=[], only_use_weight_keys:bool=False, era_override:Era = None) -> tuple[float, dict, dict]:
        """Compare two dictionaries of numbers to get overall difference

        Args:
          actuals_dict: First Dictionary. Use this dict to get keys to compare.
          measurements_dict: Second Dictionary.
          weights: X times to count certain category (ex: 3x for command)
          all_or_nothing: List of category names to compare as a boolean 1 or 0 instead
                          of pct difference.
          only_use_weight_keys: Bool for whether to only count an accuracy there is a weight associated
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          Tuple:
           - Float for overall accuracy
           - Dict with accuracy per key
           - Dict with categorical accuracy and differences.
        """

        denominator = len((weights if only_use_weight_keys else actuals_dict).keys())
        categorical_accuracy_dict = {}
        categorical_above_below_dict = {}
        accuracies = 0

        # CALCULATE CATEGORICAL ACCURACY
        for key, value1 in actuals_dict.items():
            evaluate_key = key in measurements_dict.keys()
            evaluate_key = key in weights.keys() if only_use_weight_keys else evaluate_key
            if evaluate_key:
                value2 = measurements_dict[key]

                if key == 'command-outs':
                    # VALUE 1
                    co_split = value1.split('-')
                    command = int(co_split[0])
                    outs = int(co_split[1])
                    command_out_matchup = self.__onbase_control_outs(command, outs, era_override)
                    value1 = self.__obp_for_command_outs(command_out_matchup)
                    # VALUE 2
                    co_split = value2.split('-')
                    command = int(co_split[0])
                    outs = int(co_split[1])
                    command_out_matchup = self.__onbase_control_outs(command, outs, era_override)
                    value2 = self.__obp_for_command_outs(command_out_matchup)
                
                if key in all_or_nothing:
                    accuracy_for_key = 1 if value1 == value2 else 0
                else:
                    accuracy_for_key = self.__relative_pct_accuracy(actual=value1, measurement=value2)
                
                # CATEGORICAL ACCURACY
                categorical_accuracy_dict[key] = accuracy_for_key
                categorical_above_below_dict[key] = {'above_wotc': 1 if value1 < value2 else 0,
                                                     'below_wotc': 1 if value1 > value2 else 0,
                                                     'matches_wotc': 1 if value1 == value2 else 0,
                                                     'difference_wotc': abs(value2 - value1)}

                # APPLY WEIGHTS
                weight = float(weights[key]) if key in weights.keys() else 1
                denominator += float(weights[key]) - 1 if key in weights.keys() else 0
                accuracies += (accuracy_for_key * weight)

        overall_accuracy = accuracies / denominator

        return overall_accuracy, categorical_accuracy_dict, categorical_above_below_dict

    def accuracy_against_wotc(self, wotc_card_dict:dict, is_pts_only:bool=False) -> tuple[float, dict, dict]:
        """Compare My card output against official WOTC card.

        Args:
          wotc_card_dict: Dictionary with stats per category from wizards output.
          is_pts_only: Boolean flag to enabled testing for only point value.

        Returns:
          Tuple:
           - Float for overall accuracy
           - Dict with accuracy per key
           - Dict with categorical accuracy and differences.
        """

        chart_w_combined_command_outs = self.chart
        chart_w_combined_command_outs['command-outs'] = '{}-{}'.format(self.chart.command,self.chart.outs)
        chart_w_combined_command_outs['spd'] = self.speed.speed
        chart_w_combined_command_outs['defense'] = int(list(self.positions_and_defense.values())[0])
        
        # COMBINE 1B and 1B+ IF NON-VOLATILE CATEGORIES
        if not self.is_pitcher and '1b+' not in wotc_card_dict.keys():
            chart_w_combined_command_outs['1b'] = chart_w_combined_command_outs['1b'] + chart_w_combined_command_outs['1b+']
            
        if is_pts_only:
            chart_w_combined_command_outs['points'] = self.points

        return self.accuracy_between_dicts(
            actuals_dict=wotc_card_dict,
            measurements_dict=chart_w_combined_command_outs,
            weights={},
            all_or_nothing=['command-outs']
        )

    def __relative_pct_accuracy(self, actual:float, measurement:float) -> float:
        """ CALCULATE ACCURACY BETWEEN 2 NUMBERS"""

        denominator = actual

        # ACCURACY IS 100% IF BOTH ARE EQUAL (IF STATEMENT TO AVOID 0'S)
        if actual == measurement:
            return 1

        # CAN'T DIVIDE BY 0, SO USE OTHER VALUE AS BENCHMARK
        if actual == 0:
            denominator = measurement

        return (actual - abs(actual - measurement) ) / denominator
    
    def ordinal(self, number:int) -> str:
        """Convert int to string with ordinal (ex: 1 -> 1st, 13 -> 13th)

        Args:
          number: Integer value to convert.

        Returns:
          String with ordinal number
        """
        return "%d%s" % (number,"tsnrhtdd"[(number//10%10!=1)*(number%10<4)*number%10::4])

    def __rbgs_to_hex(self, rgbs:tuple[int, int, int, int]) -> str:
        """Convert RGB tuples to hex string (Ex: (255, 255, 255, 0) -> "#fffffff")

        Args:
          rgbs: Tuple of RGB values

        Returns:
          String representation of hex color code
        """
        return '#' + ''.join(f'{i:02X}' for i in rgbs[0:3])

    def is_substring_in_list(self, substring:str, str_list: list[str]) -> bool:
        """Check to see if the substring is in ANY of the list of strings"""

        for string in str_list:
            if substring in string:
                return True
        return False


# ------------------------------------------------------------------------
# OUTPUT PLAYER METHODS
# ------------------------------------------------------------------------

    def print_player(self) -> None:
        """Prints out self in readable format.
           Prints out the following:
            - Player Metadata
            - Player Chart
            - Projected Real Life Stats

        Args:
          None

        Returns:
          String of output text for player info + stats
        """

        # ----- NAME AND SET  ----- #
        print("----------------------------------------")
        print(f"{self.name_for_visuals} ({self.year}) - {self.stats_period.string}")
        print("----------------------------------------")
        print(f"Team: {self.team.value}")
        print(f"Set: {self.set.value} {self.image.expansion} (v{self.version})")
        print(f"Era: {self.era.value.title()}")
        print(f"Data Source: {self.source}")
        if not self.image.source.type.is_empty:
            print(f"Img Source: {self.image.source.type}")

        # ----- POSITION AND ICONS  ----- #

        # POSITION
        positions_string = self.positions_and_defense_as_string(is_horizontal=True) + ' '
        # IP / SPEED
        ip_or_speed = self.speed.full_string if not self.is_pitcher else '{} IP'.format(self.ip)
        # ICON(S)
        icon_string = ''
        for index, icon in enumerate(self.icons):
            icon_string += f"{'|' if index == 0 else ''} {icon.value} "

        print(f"\n{self.points} PTS | {positions_string}| {ip_or_speed} {icon_string}")
        print(self.points_breakdown.breakdown_str)

        print(f"\n{self.chart.command} {self.command_type.upper()}")

        chart_tbl = PrettyTable(field_names=[col.value for col in self.chart.categories_list])
        chart_tbl.add_row(self.chart.ranges_list)

        print("\nCHART")
        print(chart_tbl)

        stat_categories_dict = {
            'BA': 'batting_avg',
            'OBP': 'onbase_perc',
            'SLG': 'slugging_perc',
            'OPS': 'onbase_plus_slugging',
            'OPS+': 'onbase_plus_slugging_plus',
            'PA': 'PA',
            'AB': 'AB',
            '1B': '1b_per_650_pa',
            '2B': '2b_per_650_pa',
            '3B': '3b_per_650_pa',
            'HR': 'hr_per_650_pa',
            'BB': 'bb_per_650_pa',
            'SO': 'so_per_650_pa',
            'SB': 'SB',
        }

        statline_tbl = PrettyTable(field_names=[' '] + list(stat_categories_dict.keys()))
        slash_categories = ['batting_avg','onbase_perc','slugging_perc','onbase_plus_slugging']
        final_dict = {
            'projected': [],
            'stats': [],
        }
        real_life_pa = int(self.stats.get('PA', 0))
        real_life_pa_ratio = real_life_pa / 650.0
        all_numeric_value_lists = []
        for source in final_dict.keys():
            source_dict = getattr(self, source)
            src_value_name = source.replace('stats', 'real').replace('projected', 'proj').upper()
            values = [src_value_name]
            numeric_values = []
            for abbr, full_name in stat_categories_dict.items():
                key = full_name if source == 'projected' or full_name in slash_categories else abbr
                multiplier = real_life_pa_ratio if 'per_650_pa' in key else 1.0
                stat_raw = ( ( source_dict.get(key, 0) or 0 ) * multiplier ) if abbr != 'PA' else real_life_pa
                stat_raw_cleaned = round(stat_raw, 3) if full_name in slash_categories else int(stat_raw)
                stat_str = str(stat_raw_cleaned).replace('0.', '.') if stat_raw_cleaned != 0 else '-'
                values.append(stat_str)
                numeric_values.append(stat_raw_cleaned)
            final_dict[source] = values
            all_numeric_value_lists.append(numeric_values)
        
        # ADD ROWS
        for source, values in final_dict.items():
            statline_tbl.add_row(values, divider=source == 'stats')
        
        # ADD DIFFS ROW
        diffs_row = ['DIFF'] + [round(all_numeric_value_lists[0][i] - all_numeric_value_lists[1][i], 3 if i < 4 else 0) for i in range(len(all_numeric_value_lists[0]))]
        statline_tbl.add_row(diffs_row)

        print('\nPROJECTED STATS')
        print(statline_tbl)

        for warning in self.warnings:
            print(f"** {warning}")

    def player_data_for_html_table(self) -> list[list[str]]:
        """Provides data needed to populate the statline shown on the showdownbot.com webpage.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of a category,
          real stat, and in-game Showdown estimated stat.
        """

        final_player_data = []
        en_dash = '—'

        # ADD WHETHER STATS ESTIMATIONS WERE INVOLVED
        category_prefix = ''
        if self.is_stats_estimate:
            category_prefix = '*'

        # SLASH LINE
        slash_categories = [('batting_avg', 'BA'),('onbase_perc', 'OBP'),('slugging_perc', 'SLG'),('onbase_plus_slugging', 'OPS')]
        for key, cleaned_category in slash_categories:
            in_game = f"{float(round(self.projected[key],3)):.3f}".replace('0.','.')
            actual = f"{float(self.stats[key]):.3f}".replace('0.','.')
            final_player_data.append([category_prefix+cleaned_category,actual,in_game])

        # GAMES/IP
        final_player_data.append(['G', str(self.stats.get('G', 0)), en_dash])
        ip_real = self.stats.get('IP', None)
        if ip_real:
            final_player_data.append(['IP', str(self.stats.get('IP', 0)), en_dash])

        # PLATE APPEARANCES
        real_life_pa = int(self.stats['PA'])
        real_life_pa_ratio = int(self.stats['PA']) / 650.0
        final_player_data.append([f'{category_prefix}PA', str(real_life_pa), str(real_life_pa)])

        # ADD EACH RESULT CATEGORY, REAL LIFE # RESULTS, AND PROJECTED IN-GAME # RESULTS
        # EX: [['1B','75','80'],['2B','30','29']]
        result_categories = [
            ('1b_per_650_pa', '1B'),
            ('2b_per_650_pa', '2B'),
            ('3b_per_650_pa', '3B'),
            ('hr_per_650_pa', 'HR'),
            ('bb_per_650_pa', 'BB'),
            ('so_per_650_pa', 'SO')
        ]
        for key, cleaned_category in result_categories:
            in_game = str(int(round(self.projected[key]) * real_life_pa_ratio))
            actual = str(int(self.stats[cleaned_category]))
            prefix = category_prefix if cleaned_category in ['2B','3B'] else ''
            final_player_data.append([f'{prefix}{cleaned_category}',actual,in_game])
        
        # NON COMPARABLE STATS
        category_list = ['earned_run_avg', 'whip', 'bWAR'] if self.is_pitcher else ['SB', 'onbase_plus_slugging_plus', 'dWAR', 'bWAR']
        rounded_metrics_list = ['SB', 'onbase_plus_slugging_plus']
        for category in category_list:
            if category in self.stats.keys():
                stat_raw = self.stats.get(category, None)
                if stat_raw is None:
                    stat = en_dash
                else:
                    stat_raw = 0 if str(stat_raw) == '' else stat_raw
                    stat_cleaned = int(stat_raw) if category in rounded_metrics_list else stat_raw
                    stat = str(stat_cleaned) if stat_raw is not None else en_dash
                short_name_map = {
                    'onbase_plus_slugging_plus': 'OPS+',
                    'whip': 'WHIP',
                    'bWAR': 'bWAR',
                    'dWAR': 'dWAR',
                    'SB': f'{category_prefix}SB',
                    'earned_run_avg': 'ERA',
                }
                short_category_name = short_name_map[category]
                final_player_data.append([short_category_name,stat,en_dash])

        # DEFENSE (IF APPLICABLE)
        for position, metric_and_value_dict in self.positions_and_real_life_ratings.items():
            for metric, value in metric_and_value_dict.items():
                final_player_data.append([f'{metric.value.upper()}-{position}',str(round(value)),en_dash])
        
        return final_player_data

    def points_data_for_html_table(self) -> list[list[str]]:
        """Provides data needed to populate the points breakdown shown on the showdownbot.com webpage.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of a pts category, stat and value.
        """
        
        en_dash = '—'
        if self.player_sub_type == PlayerSubType.RELIEF_PITCHER and self.ip > 1:
            spd_or_ip = ['IP', str(self.ip), f"{self.points_breakdown.multi_inning_mutliplier}x"]
        else:
            spd_or_ip = [
                'IP' if self.is_pitcher else 'SPD', 
                str(self.ip if self.is_pitcher else self.speed.speed),
                str(round(self.points_breakdown.ip if self.is_pitcher else self.points_breakdown.speed))
            ]
        pts_data = [
            ['BA', self.__format_slash_pct(self.projected['batting_avg']), str(round(self.points_breakdown.ba))],
            ['OBP', self.__format_slash_pct(self.projected['onbase_perc']), str(round(self.points_breakdown.obp))],
            ['SLG', self.__format_slash_pct(self.projected['slugging_perc']), str(round(self.points_breakdown.slg))],
            spd_or_ip,

        ]

        if not self.is_pitcher:
            pts_data.append(['HR (650 PA)', str(round(self.projected['hr_per_650_pa'])), str(round(self.points_breakdown.hr))])
            pts_data.append([
                'DEFENSE', 
                self.positions_and_defense_as_string(is_horizontal=True),
                str(round(self.points_breakdown.defense))
            ])
        else:
            pts_data.append(['OUT DIST', str(round(self.chart.gb_pct,2)), str(round(self.points_breakdown.out_distribution))])
        
        if self.points_breakdown.bonus > 0:
            pts_data.append(['BONUS', en_dash, str(round(self.points_breakdown.bonus))])
        if self.points_breakdown.icons > 0:
            pts_data.append(['ICONS', ','.join([i.value for i in self.icons]), str(round(self.points_breakdown.icons))])
        if self.points_breakdown.normalizer < 1.0:
            pts_data.append(['NORMALIZER', en_dash, str(round(self.points_breakdown.normalizer,2))])
        if self.points_breakdown.command_out_multiplier != 1.0:
            command_name = 'CTRL' if self.is_pitcher else 'OB'
            pts_data.append([f'{command_name}/OUT MULTLIPLIER', en_dash, str(round(self.points_breakdown.command_out_multiplier,2))])
        
        
        pts_data.append(['TOTAL', '', self.points])

        return pts_data

    def accuracy_data_for_html_table(self) -> list[list[str]]:
        """Provides data needed to populate the accuracy breakdown shown on the showdownbot.com webpage.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of a offset and accuracy value.
        """
        accuracy_data: list[list[str]] = []
        sorted_accuracies_as_tuples = sorted(self.command_out_accuracies.items(), key=lambda co_and_ac: co_and_ac[1], reverse=True)
        for index, co_accuracy_tuple in enumerate(sorted_accuracies_as_tuples):
            command_out_str = co_accuracy_tuple[0]
            command, outs = command_out_str.split('-')
            accuracy = co_accuracy_tuple[1]
            accuracy_data.append([str(index + 1), f"{command}", f"{outs}", f"{round(100 * accuracy, 2)}%"])

        return accuracy_data

    def rank_data_for_html_table(self) -> list[list[str]]:
        """Provides data needed to populate the rank breakdown shown on the showdownbot.com webpage. 
        
        Only applies to cards loaded via the Showdown Library.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of ranks for a given category.
        """

        if len(self.rank) == 0 or len(self.pct_rank) == 0:
            # EMPTY RANKS, RETURN EMPTY MESSAGE
            return [['RANKINGS NOT AVAILABLE']]
        
        categories_to_exclude = ['speed', 'defense'] if self.is_pitcher else ['ip', 'defense']
        alias_mapping = {
            'points': 'PTS',
            'speed': 'SPD',
            'ip': 'IP',
            'onbase_perc': 'PROJ. OBP',
            'slugging_perc': 'PROJ. SLG',
            'batting_avg': 'PROJ. BA',
            'onbase_plus_slugging': 'PROJ. OPS',
            'hr_per_650_pa': 'PROJ. HR/650 PA',
        }
        values_mapping = {
            'points': self.points,
            'speed': self.speed.speed,
            'ip': self.ip,
            'onbase_perc': self.__format_slash_pct(self.projected['onbase_perc']) if 'onbase_perc' in self.projected.keys() else 0.00,
            'slugging_perc': self.__format_slash_pct(self.projected['slugging_perc']) if 'slugging_perc' in self.projected.keys() else 0.00,
            'batting_avg': self.__format_slash_pct(self.projected['batting_avg']) if 'batting_avg' in self.projected.keys() else 0.00,
            'onbase_plus_slugging': self.__format_slash_pct(self.projected['onbase_plus_slugging']) if 'onbase_plus_slugging' in self.projected.keys() else 0.00,
            'hr_per_650_pa': round(self.projected['hr_per_650_pa'],1) if 'hr_per_650_pa' in self.projected.keys() else 0,
        }
        for position, defense in self.positions_and_defense.items():
            if position.is_hitter and position != Position.DH:
                values_mapping[position.value] = defense

        ranking_data = []
        for category in self.rank.keys():
            if category in self.pct_rank.keys() and category not in categories_to_exclude:
                category_cleaned = alias_mapping[category] if category in alias_mapping.keys() else category.upper()
                value = values_mapping[category] if category in values_mapping.keys() else 0.00
                rank = round(self.rank[category])
                pct_rank = round(self.pct_rank[category] * 100,1)
                ranking_data.append([category_cleaned, f"{value}", f"{rank}", f"{pct_rank}"])
        
        ranking_data.sort()
        
        return ranking_data

    def opponent_data_for_html_table(self) -> list[list[str]]:
        """ List of attributes of the avg opponent used to create player's chart 
        
        Args:
          None

        Returns:
          Multi-dimensional list of avg opponent chart results.
        """

        opponent_type = PlayerType.HITTER if self.is_pitcher else PlayerType.PITCHER
        opponent_chart: Chart = self.set.baseline_chart(player_type=opponent_type, era=self.era)

        return opponent_chart.values_as_list

    def __player_metadata_summary_text(self, is_horizontal:bool=False, return_as_list:bool=False) -> str:
        """Creates a multi line string with all player metadata for card output.

        Args:
          is_horizontal: Optional boolean for horizontally formatted text (04/05)
          return_as_list: Boolean for return type

        Returns:
          String/list of output text for player info + stats
        """
        positions_string = self.positions_and_defense_as_string(is_horizontal=is_horizontal)

        ip = f'IP {self.ip}' if self.set.is_after_03 else f'{self.ip} IP'
        speed = f'SPD {self.speed.speed}' if self.set.is_showdown_bot else self.speed.full_string
        ip_or_speed = speed if not self.is_pitcher else ip
        if is_horizontal:
            if return_as_list:
                final_text = [
                    f'{self.points} PT.',
                    positions_string if self.is_pitcher else speed,
                    self.hand.visual(self.is_pitcher),
                    (ip if self.is_pitcher else positions_string),
                ]
            else:
                spacing_between_hand_and_final_item = '  ' if self.set.is_04_05 and not self.is_pitcher and len(positions_string) > 13 and len(self.icons) > 0 else '   '
                final_text = '{points} PT.   {item2}   {hand}{spacing_between_hand_and_final_item}{item4}'.format(
                    points=self.points,
                    item2=positions_string if self.is_pitcher else speed,
                    hand=self.hand.visual(self.is_pitcher),
                    spacing_between_hand_and_final_item=spacing_between_hand_and_final_item,
                    item4=ip if self.is_pitcher else positions_string
                )
        else:

            final_text = """\
            {line1}
            {hand}
            {line3}
            {points} PT.
            """.format(
                line1=positions_string if self.is_pitcher else ip_or_speed,
                hand=self.hand.visual(self.is_pitcher),
                line3=ip_or_speed if self.is_pitcher else positions_string,
                points=self.points
            )
        final_text = final_text.upper() if self.set.is_metadata_text_uppercased else final_text
        return final_text

    def positions_and_defense_as_string(self, is_horizontal:bool=False) -> str:
        """Creates a single line string with positions and defense.

        Args:
          is_horizontal: Optional boolean for horizontally formatted text (04/05)

        Returns:
          String of output text for player's defensive stats
        """
        positions_string = ''
        position_num = 1
        dh_string = self.set.dh_string

        if self.positions_and_defense_for_visuals == {}:
            # THE PLAYER IS A DH
            positions_string = dh_string
        else:
            for position,fielding in self.positions_and_defense_for_visuals.items():
                if self.is_pitcher:
                    positions_string += position
                elif position == 'DH':
                    positions_string += dh_string
                else:
                    is_last_element = position_num == len(self.positions_and_defense_for_visuals.keys())
                    positions_separator = ' ' if is_horizontal else '\n'
                    fielding_plus = "" if fielding < 0 else "+"
                    positions_string += f'{position} {fielding_plus}{fielding}{"" if is_last_element else positions_separator}'
                position_num += 1
        
        return positions_string

    def radar_chart_labels_as_values(self) -> tuple[list[str], list[float]]:
        """Defines the labels and values used in the radar chart shown on the front end.

        Args:
          None

        Returns:
          Tuples of lists, one label and one value
        """
        # RETURN NONE FOR EMPTY OBJECT
        if self.pct_rank == {}:
            return None, None

        # DEFINE LABEL CATEGORIES
        all_labels_pitcher = {
            'batting_avg': 'BAa', 
            'onbase_perc': 'OBPa',
            'slugging_perc': 'SLGa',  
            'onbase_plus_slugging': 'OPSa', 
            'ip': 'IP',
        }
        all_labels_hitter = {
            'batting_avg': 'BA', 
            'onbase_perc': 'OBP', 
            'slugging_perc': 'SLG',
            'onbase_plus_slugging': 'OPS', 
            'speed': 'SPD',
            'C': 'DEF-C',
            'CA': 'DEF-CA',
            '1B': 'DEF-1B',
            '2B': 'DEF-2B',
            '3B': 'DEF-3B',
            'SS': 'DEF-SS',
            'LF/RF': 'DEF-LF/RF',
            'CF': 'DEF-CF',
            'OF': 'DEF-OF',
        }
        all_labels = all_labels_pitcher if self.is_pitcher else all_labels_hitter

        labels: list[str] = []
        values: list[float] = []
        for category, label in all_labels.items():
            if category in self.pct_rank.keys():
                percentile_value = self.pct_rank[category]
                labels.append(label)
                values.append(round(percentile_value * 100, 1))

        return labels, values

    def radar_chart_color(self) -> str:
        """RGB color scheme for the player's team, used for the inside of the radar chart.

        Args:
          None

        Returns:
          String with RGB codes (ex: "rgba(255, 50, 25, 1.0)")
        """
        tm_colors = self.__team_color_rgbs(is_secondary_color=self.image.use_secondary_color)

        return f'rgb({tm_colors[0]}, {tm_colors[1]}, {tm_colors[2]})'

    def __format_slash_pct(self, value:float) -> str:
        """Converts a float value into a rounded decimal string without the leading 0.

        Args:
          value: Float value to be converted.

        Returns:
          Formatted string version of slashline percentage.
        
        """
        return str(round(value,3)).replace('0.','.')


# ------------------------------------------------------------------------
# CARD IMAGE COMPONENTS
# ------------------------------------------------------------------------

    def card_image(self, show:bool=False, img_name_suffix:str='') -> None:
        """Generates a 1500/2100 (larger if bordered) card image mocking what a real MLB Showdown card
        would look like for the player output. Final image is dumped to mlb_showdown_bot/output folder.

        Args:
          show: Boolean flag for whether to open the final image after creation.
          img_name_suffix: Optional suffix added to the image name.

        Returns:
          None
        """

        start_time = datetime.now()

        # CHECK IF IMAGE EXISTS ALREADY IN CACHE
        cached_img_link = self.cached_img_link()
        if cached_img_link:
            # LOAD DIRECTLY FROM GOOGLE DRIVE
            response = requests.get(cached_img_link)
            card_image = Image.open(BytesIO(response.content))
            self.save_image(image=card_image, start_time=start_time, show=show, disable_add_border=True)
            return
        
        # BACKGROUND IMAGE
        card_image = self.__background_image()
        
        # PLAYER IMAGE
        player_image_layers = self.__player_image_layers()
        for img, coordinates in player_image_layers:
            card_image.paste(img, coordinates, img)

        # ADD HOLIDAY THEME
        if self.image.edition == Edition.HOLIDAY:
            holiday_image_path = self.__template_img_path('Holiday')
            holiday_image = Image.open(holiday_image_path)
            card_image.paste(holiday_image,self.__coordinates_adjusted_for_bordering(coordinates=(0,0)),holiday_image)

        # LOAD SHOWDOWN TEMPLATE
        showdown_template_frame_image = self.__template_image()
        card_image.paste(showdown_template_frame_image,self.__coordinates_adjusted_for_bordering(coordinates=(0,0)),showdown_template_frame_image)

        # CREATE NAME TEXT
        name_text, color = self.__player_name_text_image()
        small_name_cutoff = self.set.small_name_text_length_cutoff
        name_image_component = TemplateImageComponent.PLAYER_NAME_SMALL if len(self.name_for_visuals) >= small_name_cutoff and self.image.parallel != ImageParallel.MYSTERY else TemplateImageComponent.PLAYER_NAME
        name_paste_location = self.set.template_component_paste_coordinates(name_image_component)
        if self.set.is_00_01:
            # ADD BACKGROUND BLUR EFFECT FOR 2001 CARDS
            name_text_blurred = name_text.filter(ImageFilter.BLUR)
            shadow_paste_coordinates = (name_paste_location[0] + 6, name_paste_location[1] + 6)
            card_image.paste(colors.BLACK, self.__coordinates_adjusted_for_bordering(shadow_paste_coordinates), name_text_blurred)
        card_image.paste(color, self.__coordinates_adjusted_for_bordering(name_paste_location),  name_text)

        # ADD TEAM LOGO
        disable_team_logo = self.image.hide_team_logo or (self.image.edition.has_additional_logo_00_01 and self.set == Set._2000)
        if not disable_team_logo:
            team_logo, team_logo_coords = self.__team_logo_image()
            card_image.paste(team_logo, self.__coordinates_adjusted_for_bordering(team_logo_coords), team_logo)

        # 00/01 ADDITIONAL LOGO
        card_image = self.__add_additional_logos_00_01(image=card_image)

        # METADATA
        metadata_image, color = self.__metadata_image()
        metadata_image_x, metadata_image_y = self.set.template_component_paste_coordinates(TemplateImageComponent.METADATA)
        if len(self.icons) > 4 and self.set in [Set._2004, Set._2005]:
            metadata_image_x += -10
        metadata_paste_coordinates = self.__coordinates_adjusted_for_bordering((metadata_image_x, metadata_image_y))
        card_image.paste(color, metadata_paste_coordinates, metadata_image)

        # CHART
        chart_image, color = self.__chart_image()
        chart_cords = self.set.template_component_paste_coordinates(TemplateImageComponent.CHART, player_type=self.player_type)
        card_image.paste(color, self.__coordinates_adjusted_for_bordering(chart_cords), chart_image)

        # STYLE (IF APPLICABLE)
        if self.set.is_showdown_bot:
            style_img = self.__style_image()
            style_coordinates = self.__coordinates_adjusted_for_bordering(self.set.template_component_paste_coordinates(TemplateImageComponent.STYLE))
            card_image.paste(style_img, style_coordinates, style_img)
        
        # ICONS
        if self.set.has_icons:
            card_image = self.__add_icons_to_image(card_image)

        # SET
        set_image = self.__card_set_image()
        card_image.paste(set_image, self.__coordinates_adjusted_for_bordering((0,0)), set_image)

        # YEAR CONTAINER
        if self.image.show_year_text and not self.set.is_year_container_text:
            paste_location = self.set.template_component_paste_coordinates(TemplateImageComponent.YEAR_CONTAINER)

            # ADJUST IF THERE'S STATS PERIOD TEXT
            if self.stats_period.type.show_text_on_card_image and self.set == Set._2003:
                paste_location = (paste_location[0], paste_location[1] - 65)

            year_container_img = self.__year_container_add_on()
            card_image.paste(year_container_img, self.__coordinates_adjusted_for_bordering(paste_location), year_container_img)

        # EXPANSION
        if self.image.expansion.has_image:
            expansion_image = self.__expansion_image()
            expansion_location = self.set.template_component_paste_coordinates(TemplateImageComponent.EXPANSION)
            if self.image.show_year_text and self.set.is_00_01:
                # IF YEAR CONTAINER EXISTS, MOVE OVER EXPANSION LOGO
                expansion_location = (expansion_location[0] - 140, expansion_location[1] + 5)
            if self.set == Set._2002 and self.image.expansion == Expansion.TD:
                expansion_location = (expansion_location[0] + 20,expansion_location[1] - 17)
            elif self.set.is_showdown_bot and self.image.expansion == Expansion.TD:
                expansion_location = (expansion_location[0],expansion_location[1] - 12)
            
            if self.stats_period.type.show_text_on_card_image and self.set.is_showdown_bot:
                new_expansion_size = tuple(int(x * 0.85) for x in expansion_image.size)
                expansion_image = expansion_image.resize(new_expansion_size, Image.ANTIALIAS)
                expansion_location = (expansion_location[0] - 120, expansion_location[1] + 10)                

            card_image.paste(expansion_image, self.__coordinates_adjusted_for_bordering(expansion_location), expansion_image)

        # SPLIT/DATE RANGE
        if self.stats_period.type.show_text_on_card_image:
            split_image = self.__date_range_or_split_image()
            paste_coordinates = self.set.template_component_paste_coordinates(TemplateImageComponent.SPLIT)
            card_image.paste(split_image, self.__coordinates_adjusted_for_bordering(paste_coordinates), split_image)

        # BETA TAG
        # TO BE REMOVED AFTER TEST PERIOD
        # if self.set.is_showdown_bot:
        #     beta_img_path = self.__template_img_path('BETA')
        #     beta_banner_image = Image.open(beta_img_path)
        #     card_image.paste(beta_banner_image,(0,0),beta_banner_image)

        # SAVE AND SHOW IMAGE
        # CROP TO 63mmx88mm or bordered
        final_size = self.set.card_size_bordered_final if self.image.is_bordered else self.set.card_size_final
        card_image = self.__center_and_crop(card_image,final_size)
        card_image = self.__round_corners(card_image, 60)

        # MAKE IMAGE BLACK AND WHITE IF PARALLEL IS SELECTED
        if self.image.parallel == ImageParallel.BLACK_AND_WHITE:
            card_image = self.__change_image_saturation(image=card_image, saturation=0.05)

        if self.image.error:
            print(self.image.error)

        self.save_image(image=card_image, start_time=start_time, show=show, img_name_suffix=img_name_suffix)

    def __background_image(self) -> Image.Image:
        """Loads background image for card. Either loads from upload, url, or default
           background.

        Args:
          None

        Returns:
          PIL image object for the player background.
        """

        is_00_01_set = self.set.is_00_01        
        dark_mode_suffix = '-DARK' if self.image.is_dark_mode and self.set.is_showdown_bot else ''
        default_image_path = self.__template_img_path(f'Default Background - {self.set.template_year}{dark_mode_suffix}')
        
        # CHECK FOR CUSTOM LOCAL IMAGE ASSET (EX: NATIONALITY, ASG)
        custom_image_path = None
        background_image = None
        if self.image.special_edition == SpecialEdition.NATIONALITY:
            custom_image_path = os.path.join(os.path.dirname(__file__), 'countries', 'backgrounds', f"{self.nationality.value}.png")
        elif self.image.special_edition == SpecialEdition.ASG_2023:
            custom_image_path = self.__card_art_path(f"ASG-{str(self.year)}-BG-{self.league}")

        # CUSTOM BACKGROUND 
        if custom_image_path:
            try:
                background_image = Image.open(custom_image_path)
            except:
                background_image = None

            if background_image:
                if background_image.size != (1500, 2100):
                    background_image = self.__img_crop(background_image, (1500, 2100))
        
        # 2000/2001: CREATE TEAM LOGO BACKGROUND IMAGE
        if background_image is None and is_00_01_set:
            background_image = self.team_background_image()

        # DEFAULT IMAGE
        if background_image is None:
            background_image = Image.open(default_image_path)

        has_border_already = background_image.size == self.set.card_size_bordered

        # IF 2000, ADD NAME CONTAINER
        if self.set == Set._2000:
            name_container = self.__2000_player_name_container_image()
            paste_coordinates = self.__coordinates_adjusted_for_bordering((0,0), is_disabled = not has_border_already)
            background_image.paste(name_container, paste_coordinates, name_container)

        if self.image.parallel.is_team_background_black_and_white:
            background_image = self.__change_image_saturation(image=background_image, saturation=0.10)
        
        if self.image.is_bordered and not has_border_already:
            # USE WHITE OR BLACK
            border_color = colors.BLACK if self.image.is_dark_mode else colors.WHITE
            image_border = Image.new('RGBA', self.set.card_size_bordered, color=border_color)
            image_border.paste(background_image.convert("RGBA"),(self.set.card_border_padding,self.set.card_border_padding),background_image.convert("RGBA"))
            background_image = image_border

        return background_image

    def team_background_image(self) -> Image.Image:
        """Create team background image dynamically for 2000/2001 sets
        
        Args:
          None
        
        Returns:
          PIL Image for team background art.
        """
        
        is_2001_set = self.set == Set._2001
        image_size = self.set.card_size_bordered if self.image.is_bordered else self.set.card_size
        team_override = self.team_override_for_images
        background_color = self.__team_color_rgbs(is_secondary_color=self.image.use_secondary_color, team_override=team_override)
        team_background_image = Image.new('RGB', image_size, color=background_color)
        
        # ADD 2001 SET ADDITIONS
        if is_2001_set:
            # BLACK OVERLAY
            color_overlay_image = Image.new('RGBA', image_size, color=colors.BLACK)
            opacity_rgb = int(255 * 0.25)
            color_overlay_image.putalpha(opacity_rgb)
            team_background_image.paste(color_overlay_image, (0,0), color_overlay_image)

            # ADD LINES
            line_colors = ['BLACK','WHITE']
            for color in line_colors:
                image_path = self.__card_art_path(f"2001-{color}-LINES")
                color_image = Image.open(image_path)
                if color_image.size != image_size:
                    color_image = self.__img_crop(color_image, image_size)
                team_background_image.paste(color_image, (0,0), color_image)

        # ADD TEAM LOGO
        team_logo_image, paste_location = self.team_logo_for_background(team_override=team_override)
        team_background_image.paste(team_logo_image, paste_location, team_logo_image)

        return team_background_image
        
    def __team_logo_image(self, ignore_dynamic_elements:bool=False, size:tuple[int,int]=None, rotation:int=0, force_use_alternate:bool=False) -> tuple[Image.Image, tuple[int,int]]:
        """Generates a new PIL image object with logo of player team.

        Args:
          ignore_dynamic_elements: Ignore Super Season, Cooperstown Year, Rookie Season overrides.
          size: Tuple of ints used for sizing the team logo. If no size is provided, method will use set defaults.
          rotation: Degrees of rotation. If no rotation is provided, method will use set defaults.
          force_use_alternate: Use alternate logo, for cases where there are 2 different logos in the image (ex: 00 ATL)

        Returns:
          Tuple:
            - PIL image object with team logo.
            - Coordinates for pasting team logo.
        """

        # SETUP IMAGE METADATA
        is_alternate = self.use_alternate_logo or force_use_alternate
        logo_name = self.team.logo_name(year=self.median_year, is_alternate=is_alternate, set=self.set.value, is_dark=self.image.is_dark_mode)
        logo_size = self.set.template_component_size(TemplateImageComponent.TEAM_LOGO)
        logo_rotation = rotation if rotation else (10 if self.set == Set._2002 and self.image.edition.rotate_team_logo_2002 and not ignore_dynamic_elements else 0 )
        logo_paste_coordinates = self.set.template_component_paste_coordinates(TemplateImageComponent.TEAM_LOGO)
        is_04_05 = self.set.is_04_05
        is_00_01 = self.set.is_00_01
        is_cooperstown = self.image.edition == Edition.COOPERSTOWN_COLLECTION
        is_all_star_game = self.image.edition == Edition.ALL_STAR_GAME
        is_edition_static_logo = self.image.edition in [Edition.ROOKIE_SEASON, Edition.POSTSEASON]
        logo_size_multiplier = 1.0

        # USE INPUT SIZE IF IT EXISTS
        if size:
            logo_size = size
    
        try:
            if self.image.edition.use_edition_logo_as_team_logo and not is_00_01:
                # OVERRIDE TEAM LOGO WITH EITHER CC OR ASG
                logo_name = 'CCC' if is_cooperstown else f'ASG-{self.year}'
                team_logo_path = self.__team_logo_path(name=logo_name)
                is_wide_logo = logo_name == 'ASG-2022'
                if is_04_05 and is_cooperstown:
                    logo_size = (330,330)
                    logo_paste_coordinates = (logo_paste_coordinates[0] - 180,logo_paste_coordinates[1] - 105)
                elif is_wide_logo and is_all_star_game:
                    logo_size = (logo_size[0] + 85, logo_size[1] + 85)
                    x_movement = -40 if self.set.is_00_01 else -85
                    logo_paste_coordinates = (logo_paste_coordinates[0] + x_movement,logo_paste_coordinates[1] - 40)
            else:
                # TRY TO LOAD TEAM LOGO FROM FOLDER. LOAD ALTERNATE LOGOS FOR 2004/2005
                logo_name = self.team.logo_name(year=self.median_year, is_alternate=is_alternate, set=self.set.value, is_dark=self.image.is_dark_mode)
                logo_size_multiplier = self.team.logo_size_multiplier(year=self.median_year, is_alternate=is_alternate)
                team_logo_path = self.__team_logo_path(name=logo_name)
                if self.image.special_edition == SpecialEdition.NATIONALITY:
                    team_logo_path = os.path.join(os.path.dirname(__file__), 'countries', 'flags', f'{self.nationality.value}.png')
                    logo_size_multiplier = self.nationality.logo_size_multiplier
            team_logo = Image.open(team_logo_path).convert("RGBA")
            size_adjusted = tuple(int(v * logo_size_multiplier) for v in logo_size)
            if size_adjusted != logo_size:
                pixel_difference = size_adjusted[0] - logo_size[0]
                logo_paste_coordinates = tuple(int(v - (pixel_difference / 2)) for v in logo_paste_coordinates)
                logo_size = size_adjusted
            team_logo = team_logo.resize(size_adjusted, Image.ANTIALIAS)
        except:
            # IF NO IMAGE IS FOUND, DEFAULT TO MLB LOGO
            team_logo = Image.open(self.__team_logo_path(name=Team.MLB.logo_name(year=2023))).convert("RGBA")
            team_logo = team_logo.resize(logo_size, Image.ANTIALIAS)

        # ROTATE LOGO IF APPLICABLE
        if logo_rotation != 0:
            size_original = team_logo.size
            team_logo = team_logo.rotate(logo_rotation, expand=True, resample=Image.BICUBIC)
            size_new = team_logo.size
            if size_original != size_new:
                movement = size_new[0] - size_original[0]
                logo_paste_coordinates = (logo_paste_coordinates[0] - int(movement / 2.0), logo_paste_coordinates[1] - int(movement / 2.0))

        # RETURN STATIC LOGO IF IGNORE_DYNAMIC_ELEMENTS IS ENABLED
        # IGNORES ROOKIE SEASON, SUPER SEASON
        if ignore_dynamic_elements:
            return team_logo, logo_paste_coordinates

        # OVERRIDE IF SUPER SEASON
        if self.image.edition == Edition.SUPER_SEASON and not is_00_01:
            team_logo, _ = self.__super_season_image()
            logo_paste_coordinates = self.set.template_component_paste_coordinates(TemplateImageComponent.SUPER_SEASON)

        # ADD YEAR TEXT IF COOPERSTOWN OR YEAR TEXT OPTION IF SELECTED
        text_enabled_for_set = ( is_04_05 and (is_cooperstown or self.image.show_year_text) ) or ( self.set.is_showdown_bot and self.image.show_year_text and self.image.edition != Edition.COOPERSTOWN_COLLECTION)
        if text_enabled_for_set and self.image.edition not in [Edition.ROOKIE_SEASON, Edition.SUPER_SEASON]:
            
            new_logo = Image.new('RGBA', (logo_size[0] + 300, logo_size[1]))
            new_logo_coords = (150, 0)
            new_logo.paste(team_logo, new_logo_coords, team_logo)
            font_name = 'BaskervilleBoldItalicBT' if is_cooperstown else 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique'
            year_font_path = self.__font_path(font_name)
            year_font = ImageFont.truetype(year_font_path, size=87)
            year_font_blurred = ImageFont.truetype(year_font_path, size=90)
            year_abbrev = f"’{self.year[2:4]}" if not self.is_multi_year else " "
            year_text_color = "#E6DABD" if is_cooperstown else "#E5E4E2"
            year_text_border_color = colors.BLACK
            
            # CREATE TEXT IMAGES
            year_text = self.__text_image(
                text = year_abbrev,
                size = (180,180),
                font = year_font,
                alignment = "center",
                fill = year_text_color,
                has_border = True,
                border_color = year_text_border_color
            )
            year_coords = (0,195) if is_cooperstown else (-25, int(120 * logo_size_multiplier))
            if is_cooperstown:
                year_text_blurred = self.__text_image(
                    text = year_abbrev,
                    size = (180,180),
                    font = year_font_blurred,
                    alignment = "center",
                    fill = colors.WHITE
                )
                new_logo.paste(colors.BLACK,year_coords,year_text_blurred.filter(ImageFilter.BLUR))
            new_logo.paste(year_text, year_coords, year_text)
            team_logo = new_logo
            logo_paste_coordinates = logo_paste_coordinates if is_cooperstown else (logo_paste_coordinates[0] - 150, logo_paste_coordinates[1])

        # OVERRIDE IF ROOKIE SEASON
        if is_edition_static_logo and not is_00_01:
            component = TemplateImageComponent.ROOKIE_SEASON if self.image.edition == Edition.ROOKIE_SEASON else TemplateImageComponent.POSTSEASON
            team_logo = self.__rookie_season_image() if self.image.edition == Edition.ROOKIE_SEASON else self.__postseason_image()
            team_logo = team_logo.rotate(10, resample=Image.BICUBIC) if self.set == Set._2002 else team_logo
            logo_paste_coordinates = self.set.template_component_paste_coordinates(component)

        return team_logo, logo_paste_coordinates

    def team_logo_for_background(self, team_override:Team = None) -> tuple[Image.Image, tuple[int,int]]:
        """Open and manipulate the team logo used for 2000/2001 team backgrounds.
        
        Args:
          team_override: Optionally use a different team. Used for some special editions like CC.

        Returns:
          Tuple with:
            PIL Image object with edited team logo.
            Coordinates to paste logo.
        """

        # DEFINE TEAM TO USE
        team = team_override if team_override else self.team

        # ATTRIBUTES FOR THE LOGO
        force_alternate = team.use_alternate_for_background(set=self.set.value)
        use_alternate = self.use_alternate_logo or force_alternate
        logo_name = team.logo_name(year=self.median_year, is_alternate=use_alternate, set=self.set.value, is_dark=self.image.is_dark_mode)

        # OPACITY
        opacity = team.background_logo_opacity(set=self.set.value)
        team_logo = Image.open(self.__team_logo_path(logo_name))
        team_logo_copy = team_logo.copy()
        team_logo_copy.putalpha(int(255 * opacity))
        team_logo.paste(team_logo_copy, team_logo)

        # SATURATION
        if self.set == Set._2000:
            team_logo = self.__change_image_saturation(image=team_logo, saturation=0.2)

        # SIZE
        size = team.background_logo_size(year=self.median_year, set=self.set.value, is_alternate=use_alternate)
        team_logo = team_logo.resize(size=size, resample=Image.ANTIALIAS)

        # ROTATION
        rotation = team.background_logo_rotation(set=self.set.value)
        if rotation != 0:
            team_logo = team_logo.rotate(rotation, resample=Image.BICUBIC, expand=True)

        default_image_size = self.set.card_size
        paste_location = self.__coordinates_adjusted_for_bordering(team.background_logo_paste_location(year=self.median_year, is_alternate=use_alternate, set=self.set.value, image_size=default_image_size))
        return team_logo, paste_location

    def __template_image(self) -> Image.Image:
        """Loads showdown frame template depending on player context.

        Args:
          None

        Returns:
          PIL image object for Player's template background.
        """

        year = self.set.template_year

        # GET TEMPLATE FOR PLAYER TYPE (HITTER OR PITCHER)
        type = 'Pitcher' if self.is_pitcher else 'Hitter'
        is_04_05 = self.set.is_04_05
        edition_extension = ''
        if is_04_05:
            # 04/05 HAS MORE TEMPLATE OPTIONS
            edition_extension = ''
            default_template_color = self.player_type.template_color_04_05
            team_color_name = self.team.color_name(year=self.median_year, is_secondary=self.image.use_secondary_color)
            if self.image.edition.template_color_0405:
                edition_extension = f'-{self.image.edition.template_color_0405}'
            elif self.image.special_edition == SpecialEdition.NATIONALITY:
                edition_extension = f'-{self.nationality.template_color}'
            elif self.image.parallel == ImageParallel.TEAM_COLOR_BLAST and team_color_name:
                edition_extension = f'-{team_color_name}'
            elif self.image.parallel.template_color_04_05:
                edition_extension = f'-{self.image.parallel.template_color_04_05}'
            elif self.image.is_dark_mode:
                edition_extension = '-BLACK'
            else:
                edition_extension = f'-{default_template_color}'

            if self.image.parallel.color_override_04_05_chart:
                edition_extension = f"-{self.image.parallel.color_override_04_05_chart}"
            type_template = f'{year}-{type}{edition_extension}'
            template_image = Image.open(self.__template_img_path(type_template))
        else:
            custom_extension = self.set.template_custom_extension(self.image.parallel)
            dark_mode_extension = '-DARK' if self.set.is_showdown_bot and self.image.is_dark_mode else ''
            type_template = f'{year}-{type}{edition_extension}{dark_mode_extension}{custom_extension}'
            template_image = Image.open(self.__template_img_path(type_template))

        # GET IMAGE WITH PLAYER COMMAND
        paste_location = self.set.template_component_paste_coordinates(TemplateImageComponent.COMMAND)
        if self.set.is_showdown_bot:
            # ADD TEXT + BACKGROUND AS IMAGE
            command_image = self.__command_image()
            if not self.is_pitcher:
                paste_location = (paste_location[0] + 15, paste_location[1])

            # ADD CHART ROUNDED RECT
            container_img_path = self.__template_img_path(f'{year}-ChartOutsContainer-{type}')
            container_img_black = Image.open(container_img_path)
            team_override = self.team_override_for_images
            fill_color = self.__team_color_rgbs(is_secondary_color=self.image.use_secondary_color, team_override=team_override)
            if self.image.special_edition == SpecialEdition.NATIONALITY:
                colors = self.nationality.colors
                if len(colors) >= 2:
                    # GRADIENT
                    gradient_img_width = self.player_sub_type.nationality_chart_gradient_img_width
                    gradient_img_rect = self.__gradient_img(size=(gradient_img_width, 190), colors=colors)
                    container_img_black.paste(gradient_img_rect, (70, 1770), gradient_img_rect)
                    container_img = self.__add_alpha_mask(img=container_img_black, mask_img=Image.open(container_img_path))
                else:
                    # SOLID COLOR
                    container_img = self.__add_color_overlay_to_img(img=container_img_black,color=fill_color)
            else:
                container_img = self.__add_color_overlay_to_img(img=container_img_black,color=fill_color)
            use_dark_text = self.team.use_dark_text(year=self.median_year, is_secondary=self.image.use_secondary_color)
            dark_mode_suffix = '-DARK' if use_dark_text else ''
            text_img = Image.open(self.__template_img_path(f'{year}-ChartOutsText-{type}{dark_mode_suffix}'))
            template_image.paste(container_img, (0,0), container_img)
            template_image.paste(text_img, (0,0), text_img)
        else:
            command_image_name = f"{year}-{type}-{str(self.chart.command)}"
            command_image = Image.open(self.__template_img_path(command_image_name))
            
        template_image.paste(command_image, paste_location, command_image)

        # HANDLE MULTI POSITION TEMPLATES FOR 00/01 POSITION PLAYERS
        if self.set.is_00_01 and not self.is_pitcher:
            positions_list = [pos for pos, _ in self.positions_and_defense_img_order]
            sizing = "-".join(['LARGE' if len(pos) > 4 else 'SMALL' for pos in positions_list])
            positions_points_template = f"0001-{type}-{sizing}"
            positions_points_image = Image.open(self.__template_img_path(positions_points_template))
            template_image.paste(positions_points_image, (0,0), positions_points_image)
        
        # ADD SHOWDOWN BOT LOGO AND ERA
        logo_img = self.__bot_logo_img()
        logo_paste_location = self.set.template_component_paste_coordinates(TemplateImageComponent.BOT_LOGO)
        template_image.paste(logo_img, logo_paste_location, logo_img)

        return template_image

    def __bot_logo_img(self) -> Image.Image:
        """ Load bot's logo to display on the bottom of the card. 
        Add the version in the bottom right corner of the logo, as well as the Era underneath.

        Returns:
          PIL Image with Bot logo.
        """

        # CREATE NEW IMAGE FOR LOGO AND ERA TEXT
        img_size = (620,620)
        logo_img_with_text = Image.new('RGBA',img_size)

        # LOAD LOGO IMAGE
        is_dark_mode = self.set.is_showdown_bot and self.image.is_dark_mode
        dark_mode_extension = '-DARK' if is_dark_mode else ''
        logo_size = self.set.template_component_size(TemplateImageComponent.BOT_LOGO)
        logo_img_name = f"BOT-LOGO{dark_mode_extension}"
        logo_img = Image.open(self.__template_img_path(logo_img_name))

        # ADD VERSION NUMBER
        helvetica_neue_cond_bold_path = self.__font_path('HelveticaNeueCondensedBold')
        text_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=65)
        # DATE NUMBER
        version_text = self.__text_image(text=f"v{self.version}", size=(500, 500), font=text_font, alignment="right")
        logo_img.paste("#b5b4b4", (-15, 326), version_text)

        # ERA TEXT
        helvetica_neue_lt_path = self.__font_path('Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique')
        era_font = ImageFont.truetype(helvetica_neue_lt_path, size=70)
        era_txt_color = "#b5b5b5" if self.set.is_showdown_bot and self.image.is_dark_mode else "#585858"
        era_text = self.__text_image(text=self.era.value_no_era_suffix, size=(620, 100), font=era_font, alignment="center")
        text_paste_location = (0, 435) 
        
        # PASTE TO BLANK 600x600 IMAGE
        x_centered = int((img_size[1] - 500) / 2)
        logo_img_with_text.paste(logo_img, (x_centered, 0), logo_img)
        logo_img_with_text.paste(era_txt_color, text_paste_location, era_text)

        return logo_img_with_text.resize(logo_size, Image.ANTIALIAS)

    def __2000_player_name_container_image(self) -> Image.Image:
        """Gets template asset image for 2000 name container.

        Args:
          None

        Returns:
          PIL image object for 2000 name background/container
        """
        image_suffix = self.image.parallel.name_container_suffix_2000
        return Image.open(self.__template_img_path(f"2000-Name{image_suffix}"))

    def __2000_player_set_container_image(self) -> Image.Image:
        """Gets template asset image for 2000 set box.

        Args:
          None

        Returns:
          PIL image object for 2000 set background/container
        """
        return Image.open(self.__template_img_path("2000-Set-Box"))

    def __player_name_text_image(self) -> tuple[Image.Image, str]:
        """Creates Player name to match showdown context.

        Args:
          None

        Returns:
          Tuple
            - PIL image object for Player's name.
            - Hex Color of text as a String
        """

        # PARSE NAME STRING
        name_upper = "????? ?????" if self.image.parallel == ImageParallel.MYSTERY else self.name_for_visuals.upper()
        first, last = self.split_name(name=name_upper, is_nickname=self.is_using_nickname)
        name = first if self.set.has_split_first_and_last_names else name_upper
        default_chart_char_cutoff = 19 if self.set == Set._2002 else 15
        is_name_over_char_limit =  len(name) > default_chart_char_cutoff

        futura_black_path = self.__font_path('Futura Black')
        helvetica_neue_lt_path = self.__font_path('Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique')
        helvetica_neue_cond_black_path = self.__font_path('HelveticaNeueLtStd107ExtraBlack', extension='otf')
        helvetica_neue_lt_93_path = self.__font_path('Helvetica-Neue-LT-Std-93-Black-Extended-Oblique')

        # DEFAULT NAME ATTRIBUTES
        name_font_path = helvetica_neue_lt_path
        name_color = self.set.template_component_color(TemplateImageComponent.PLAYER_NAME, parallel=self.image.parallel)
        has_border = False
        border_color = None
        overlay_image_path = None

        # DEFINE ATTRIBUTES BASED ON CONTEXT
        match self.set:
            case Set._2000:
                name_rotation = 90
                name_alignment = "center"
                is_name_over_18_chars = len(name) >= 18
                is_name_over_15_chars = len(name) >= 15
                name_size = 145
                if is_name_over_18_chars:
                    name_size = 110
                elif is_name_over_15_chars:
                    name_size = 127
                name_font_path = helvetica_neue_lt_93_path
                padding = 0
                overlay_image_path = self.__template_img_path('2000-Name-Text-Background')
            case Set._2001:
                name_rotation = 90
                name_alignment = "left"
                name_size = 96
                padding = 0
                name_font_path = futura_black_path
                overlay_image_path = self.__template_img_path('2001-Name-Text-Background')
            case Set._2002:
                name_rotation = 90
                name_alignment = "left"
                name_size = 115 if is_name_over_char_limit else 144
                padding = 15
            case Set._2003:
                name_rotation = 90
                name_alignment = "right"
                name_size = 90 if is_name_over_char_limit else 96
                padding = 60
            case Set._2004 | Set._2005:
                name_rotation = 0
                name_alignment = "left"
                name_size = 80 if is_name_over_char_limit else 96
                padding = 3
                has_border = True
                border_color = colors.RED
            case _:
                name_rotation = 0
                name_alignment = "left"
                name_size = 80 if is_name_over_char_limit else 96
                name_font_path = helvetica_neue_cond_black_path
                padding = 3
                has_border = False

        name_font = ImageFont.truetype(name_font_path, size=name_size)
        # CREATE TEXT IMAGE
        final_text = self.__text_image(
            text = name,
            size = self.set.template_component_size(TemplateImageComponent.PLAYER_NAME),
            font = name_font,
            fill = name_color,
            rotation = name_rotation,
            alignment = name_alignment,
            padding = padding,
            has_border = has_border,
            border_color = border_color,
            overlay_image_path = overlay_image_path
        )

        # ADJUSTMENTS
        match self.set:
            case Set._2000:
                # SETUP COLOR FOR LATER STEP OF IMAGE OVERLAY
                name_color = final_text
            case Set._2001:
                # ADD LAST NAME
                last_name = self.__text_image(
                    text = last,
                    size = self.set.template_component_size(TemplateImageComponent.PLAYER_NAME),
                    font = ImageFont.truetype(name_font_path, size=135),
                    rotation = name_rotation,
                    alignment = name_alignment,
                    padding = padding,
                    fill = name_color,
                    overlay_image_path = overlay_image_path
                )
                x_coord = 45 if first == '' else 90
                final_text.paste(last_name, (x_coord,0), last_name)
                name_color = final_text
            case Set._2002:
                if self.image.parallel == ImageParallel.GOLD_FRAME:
                    name_color = "#616161"
            case Set._2004 | Set._2005:
                # DONT ASSIGN A COLOR TO TEXT AS 04/05 HAS MULTIPLE COLORS.
                # ASSIGN THE TEXT ITSELF AS THE COLOR OBJECT
                name_color = final_text
            case Set.CLASSIC | Set.EXPANDED:
                name_color = colors.WHITE if self.image.is_dark_mode else colors.BLACK

        return final_text, name_color

    def __metadata_image(self) -> tuple[Image.Image, str]:
        """Creates PIL image for player metadata. Different across sets.
           TODO: Should probably split this function up.

        Args:
          None

        Returns:
          Tuple
            - PIL image object for Player metadata.
            - Hex Color of text as a String.
        """

        # COLOR WILL BE RETURNED
        color = colors.WHITE

        if self.set.is_00_01:
            # 2000 & 2001

            metadata_image = Image.new('RGBA', (1500, 2100), 255)
            helvetica_neue_lt_path = self.__font_path('Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique')

            # PITCHER AND HITTER SPECIFIC METADATA
            if self.is_pitcher:
                # POSITION
                font_position = ImageFont.truetype(helvetica_neue_lt_path, size=72)
                position = self.positions_list[0]
                position_text = self.__text_image(text=position.value, size=(900, 300), font=font_position, alignment='center')
                metadata_image.paste(colors.WHITE, (660,342), position_text)
                # HAND | IP
                font_hand_ip = ImageFont.truetype(helvetica_neue_lt_path, size=63)
                hand_text = self.__text_image(text=self.hand.visual(self.is_pitcher), size=(900, 300), font=font_hand_ip)
                metadata_image.paste(colors.WHITE, (1092,420), hand_text)
                ip_text = self.__text_image(text='IP {}'.format(str(self.ip)), size=(900, 300), font=font_hand_ip)
                metadata_image.paste(colors.WHITE, (1260,420), ip_text)
            else:
                # SPEED | HAND
                is_variable_spd_2000 = self.set == Set._2000 and self.is_variable_speed_00_01
                font_size_speed = 40 if is_variable_spd_2000 else 54
                font_speed = ImageFont.truetype(helvetica_neue_lt_path, size=font_size_speed)
                font_hand = ImageFont.truetype(helvetica_neue_lt_path, size=54)
                speed_text = self.__text_image(text=f'SPEED {self.speed.letter}', size=(900, 300), font=font_speed)
                hand_text = self.__text_image(text=self.hand.value, size=(300, 300), font=font_hand)
                metadata_image.paste(color, (969 if self.set == Set._2000 else 915, 345 if is_variable_spd_2000 else 342), speed_text)
                metadata_image.paste(color, (1212,342), hand_text)
                if self.set == Set._2001 or is_variable_spd_2000:
                    # ADD # TO SPEED
                    font_speed_number = ImageFont.truetype(helvetica_neue_lt_path, size=40)
                    font_parenthesis = ImageFont.truetype(helvetica_neue_lt_path, size=45)
                    speed_num_text = self.__text_image(
                        text=str(self.speed.speed),
                        size=(300, 300),
                        font=font_speed_number
                    )
                    parenthesis_left = self.__text_image(text='(   )', size=(300, 300), font=font_parenthesis)
                    metadata_image.paste(color, (1116,342), parenthesis_left)
                    spd_number_x_position = 1138 if len(str(self.speed.speed)) < 2 else 1128
                    metadata_image.paste(color, (spd_number_x_position,345), speed_num_text)
                # POSITION(S)
                font_position = ImageFont.truetype(helvetica_neue_lt_path, size=78)
                y_position = 407
                for index, (position, rating) in enumerate(self.positions_and_defense_img_order):
                    dh_string = '   —' if self.set != Set._2000 else '   DH'
                    position_rating_text = dh_string if position == 'DH' else '{} +{}'.format(position,str(rating))
                    position_rating_image = self.__text_image(text=position_rating_text, size=(600, 300), font=font_position)
                    x_adjust = 10 if index == 0 and len(position) < 5 and len(self.positions_and_defense_img_order) > 1 else 0
                    x_position = (1083 if len(position) > 4 else 1161) + x_adjust
                    x_position += 18 if position in ['C','CA'] and rating < 10 else 0 # CATCHER POSITIONING ADJUSTMENT
                    metadata_image.paste(color, (x_position,y_position), position_rating_image)
                    y_position += 84
            # POINTS
            text_size = 48 if self.points >= 1000 else 57
            font_pts = ImageFont.truetype(helvetica_neue_lt_path, size=text_size)
            pts_text = self.__text_image(text=str(self.points), size=(300, 300), font=font_pts, alignment = "right")
            pts_y_pos = 576 if len(self.positions_and_defense_for_visuals) > 1 else 492
            pts_x_pos = 969 if self.is_pitcher else 999
            metadata_image.paste(color, (pts_x_pos,pts_y_pos), pts_text)

        elif self.set in [Set._2002, Set._2003]:
            # 2002 & 2003

            is_02 = self.set == Set._2002
            color = colors.BLACK if is_02 else colors.WHITE
            if is_02:
                helvetica_neue_lt_path = self.__font_path('Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique')
                metadata_font = ImageFont.truetype(helvetica_neue_lt_path, size=120)
            else:
                helvetica_neue_cond_bold_path = self.__font_path('Helvetica Neue 77 Bold Condensed')
                metadata_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=135)

            metadata_text = self.__text_image(
                text = self.__player_metadata_summary_text(),
                size = (765, 2700),
                font = metadata_font,
                rotation = 0,
                alignment = "right",
                padding=0,
                spacing= 57 if is_02 else 66
            )
            metadata_image = metadata_text.resize((255,900), Image.ANTIALIAS)
        elif self.set.is_04_05:
            # 2004 & 2005
            metadata_font_path = self.__font_path('Helvetica Neue 77 Bold Condensed')
            metadata_font = ImageFont.truetype(metadata_font_path, size=144)
            metadata_text_string = self.__player_metadata_summary_text(is_horizontal=True)
            metadata_text = self.__text_image(
                text = metadata_text_string,
                size = (3600, 900),
                font = metadata_font,
                fill = colors.WHITE,
                rotation = 0,
                alignment = "left",
                padding = 0,
                has_border = True,
                border_color = colors.BLACK,
                border_size = 9
            )
            metadata_image = metadata_text.resize((1200,300), Image.ANTIALIAS)
            # DONT WANT TO RETURN A COLOR (BECAUSE IT'S MULTI-COLORED)
            # PASS THE IMAGE ITSELF AS THE COLOR
            color = metadata_image
        else:
            metadata_image = Image.new('RGBA', (1400, 200), 255)
            metadata_font_path = self.__font_path('HelveticaNeueCondensedBold')
            metadata_font = ImageFont.truetype(metadata_font_path, size=170)
            metadata_font_small = ImageFont.truetype(metadata_font_path, size=150)
            metadata_text_list = self.__player_metadata_summary_text(is_horizontal=True, return_as_list=True)
            current_x_position = 0
            for index, category in enumerate(metadata_text_list):
                category_length = len(metadata_text_list)
                is_last = (index + 1) == category_length
                is_small_text = is_last and len(category) > 17
                category_font = metadata_font_small if is_small_text else metadata_font
                metadata_text = self.__text_image(
                    text = category,
                    size = (1500, 900),
                    font = category_font,
                    fill = colors.WHITE,
                    rotation = 0,
                    alignment = "left",
                    padding = 0,
                )
                metadata_text = metadata_text.resize((500,300), Image.ANTIALIAS)
                y_position = 5 if is_small_text else 0
                metadata_image.paste(metadata_text, (int(current_x_position),y_position), metadata_text)
                category_font_width = category_font.getsize(category)[0] / 3.0
                current_x_position += category_font_width
                if not is_last:
                    # DIVIDER
                    divider_text = self.__text_image(
                        text = '|',
                        size = (900, 900),
                        font = category_font,
                        fill = colors.WHITE,
                        rotation = 0,
                        alignment = "left",
                        padding = 0,
                    )
                    divider_text = divider_text.resize((300,300), Image.ANTIALIAS)
                    metadata_image.paste((255,255,255,50), (int(current_x_position) + 30, 0), divider_text)
                    current_x_position += 65
                

            color = colors.GRAY if self.image.is_dark_mode else colors.BLACK

        return metadata_image, color

    def __chart_image(self) -> tuple[Image.Image, str]:
        """Creates PIL image for player chart. Different across sets.
           Vertical for 2000-2004.
           Horizontal for 2004/2005

        Args:
          None

        Returns:
          Tuple
            - PIL image object for Player metadata.
            - Hex Color of text as a String.
        """

        is_horizontal = self.set.is_chart_horizontal

        # FONT
        chart_font_file_name = 'Helvetica Neue 77 Bold Condensed' if is_horizontal else 'HelveticaNeueCondensedMedium'
        chart_font_path = self.__font_path(chart_font_file_name)
        chart_font_size = self.set.template_component_font_size(TemplateImageComponent.CHART)
        chart_font = ImageFont.truetype(chart_font_path, size=chart_font_size)

        # CREATE CHART RANGES TEXT
        chart_string = ''
        # NEED IF 04/05
        chart_text = Image.new('RGBA',(6300,720))
        chart_text_addition = -20 if self.set.is_showdown_bot else 0
        chart_text_x = 150 + chart_text_addition if self.is_pitcher else 141
        for category in self.chart.categories_list:
            is_out_category = category.is_out
            range = self.chart.ranges[category]
            # 2004/2005 CHART IS HORIZONTAL. PASTE TEXT ONTO IMAGE INSTEAD OF STRING OBJECT.
            if is_horizontal:
                is_wotc = self.set.is_04_05
                range_text = self.__text_image(
                    text = range,
                    size = (450,450),
                    font = chart_font,
                    fill = colors.WHITE,
                    alignment = "center",
                    has_border = is_wotc,
                    border_color = colors.BLACK,
                    border_size = 9
                )
                use_dark_text = self.team.use_dark_text(year=self.median_year, is_secondary=self.image.use_secondary_color) and self.set.year == '2022' and is_out_category
                color_range = range_text if (is_wotc or is_out_category or self.image.is_dark_mode) and not use_dark_text else colors.BLACK
                chart_text.paste(color_range, (chart_text_x, 0), range_text)
                pitcher_spacing = 531 if is_wotc else 510
                hitter_spacing = 468 if is_wotc else 445
                chart_text_x += pitcher_spacing if self.is_pitcher else hitter_spacing
            else:
                chart_string += '{}\n'.format(range)

        # CREATE FINAL CHART IMAGE
        if is_horizontal:
            # COLOR IS TEXT ITSELF
            chart_text = chart_text.resize((2100,240), Image.ANTIALIAS)
            color = chart_text
        else:
            spacing = self.set.template_component_font_spacing(TemplateImageComponent.CHART)
            chart_text = self.__text_image(
                text = chart_string,
                size = (765, 3600),
                font = chart_font,
                rotation = 0,
                alignment = "right",
                padding=0,
                spacing=spacing
            )
            color = colors.BLACK
            chart_text = chart_text.resize((255,1200), Image.ANTIALIAS)

        return chart_text, color

    def __card_set_image(self) -> Image.Image:
        """Creates image with card number and year text. Always defaults to card No 1.
           Uses YEAR and not CONTEXT as the set year.
        Args:
          None

        Returns:
          PIL image object for set text.
        """

        # FONT FOR SET
        helvetica_neue_cond_bold_path = self.__font_path('Helvetica Neue 77 Bold Condensed')
        font_size = 180 if self.set.is_showdown_bot else 135
        set_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=font_size)

        set_image = Image.new('RGBA', (1500, 2100), 255)
        set_image_location = self.set.template_component_paste_coordinates(TemplateImageComponent.SET)

        if self.set.has_unified_set_and_year_strings:
            # SET AND NUMBER IN SAME STRING
            set_text = self.__text_image(
                text = self.image.set_number,
                size = (600, 300),
                font = set_font,
                alignment = "center"
            )
            set_text = set_text.resize((150,75), Image.ANTIALIAS)
            set_image.paste(colors.WHITE, set_image_location, set_text)
        else:
            # DIFFERENT STYLES BETWEEN NUMBER AND SET
            # CARD YEAR
            set_font_year = set_font
            year_as_str = str(self.year)
            if self.is_multi_year and self.set.is_04_05:
                # EMPTY YEAR
                year_string = ''
            elif (self.is_full_career or self.is_multi_year) and self.set == Set._2003:
                year_string = 'ALL' if self.is_full_career else 'MLT'
                set_image_location = (set_image_location[0]-5,set_image_location[1])
            elif self.is_multi_year and self.set.is_showdown_bot:
                set_image_location = (set_image_location[0]-15,set_image_location[1])
                if '-' in year_as_str:
                    try:
                        years_split = year_as_str.split('-')
                        year_string = f"'{years_split[0][2:4]}-'{years_split[1][2:4]}"                        
                    except:
                        year_string = year_as_str
                else:
                    year_string = "CAREER" if self.is_full_career else year_as_str
                    if self.is_full_career:
                        set_font_year = ImageFont.truetype(helvetica_neue_cond_bold_path, size=font_size-20)
                        set_image_location = (set_image_location[0]-5,set_image_location[1]+3)
            else:
                try:
                    year_as_str = str(int(year_as_str) + (1 if self.image.add_one_to_set_year else 0))
                except:
                    year_as_str = year_as_str
                year_string = year_as_str if self.set.is_showdown_bot else f"'{year_as_str[2:4]}"
            year_text = self.__text_image(
                text = year_string,
                size = (525, 450),
                font = set_font_year,
                alignment = "left"
            )
            year_text = year_text.resize((140,120), Image.ANTIALIAS)
            set_image.paste(colors.WHITE, set_image_location, year_text)

            # CARD NUMBER
            number_text = self.__text_image(
                text = self.image.set_number,
                size = (600, 450),
                font = set_font,
                alignment = "center"
            )
            number_text = number_text.resize((160,120), Image.ANTIALIAS)
            number_color = colors.BLACK if self.set == Set._2003 else colors.WHITE
            set_image.paste(number_color, self.set.template_component_paste_coordinates(TemplateImageComponent.NUMBER), number_text)

        return set_image

    def __expansion_image(self) -> Image.Image:
        """Creates image for card expansion (ex: Trade Deadline, Pennant Run)
        
        Args:
          None

        Returns:
          PIL image object for card expansion logo.
        """ 

        expansion_image = Image.open(self.__template_img_path(f'{self.set.template_year}-{self.image.expansion.value}'))
        return expansion_image

    def __super_season_image(self) -> tuple[Image.Image, tuple[int,int]]:
        """Creates image for optional super season attributes. Add accolades for
           cards in set > 2001.

        Args:
          None

        Returns:
          Tuple with:
            PIL image object for super season logo + text.
            Y Adjustment for paste coordinates (applies to 00/01)
        """

        is_after_03 = self.set.is_after_03
        include_accolades = self.set.show_super_season_accolades

        # FONTS
        super_season_year_path = self.__font_path('URW Corporate W01 Normal')
        super_season_accolade_path = self.__font_path('Zurich Bold Italic BT')
        super_season_year_font = ImageFont.truetype(super_season_year_path, size=225)
        super_season_accolade_font = ImageFont.truetype(super_season_accolade_path, size=150)

        accolade_text_images = []
        if include_accolades:
            
            # SLOT MAX CHARACTERS
            slot_max_characters_dict = {i: self.set.super_season_text_length_cutoff(i) for i in [1,2,3] }

            # ACCOLADES
            x_position = 18 if is_after_03 else 9
            x_incremental = 10 if is_after_03 else 1
            y_position = 338 if is_after_03 else 324
            accolade_rotation = 15 if is_after_03 else 13
            accolade_spacing = 41 if is_after_03 else 72
            accolades_used = []
            for index, max_characters in slot_max_characters_dict.items():
                accolades_available = [a for a in self.accolades if (a not in accolades_used and len(a) <= max_characters)]                
                num_available = len(accolades_available)

                if num_available == 0:
                    continue
                
                # IF ACCOLADE IS SHORT AND CAN FIT IN SLOT 3 FOR 04/05, POSTPONE IT
                accolade = accolades_available[0]
                if index < 3 and is_after_03 and len(accolade) <= slot_max_characters_dict.get(3, 0) and num_available > 2:
                    accolade = accolades_available[1]

                accolades_used.append(accolade)
                accolade_text = self.__text_image(
                    text = accolade,
                    size = (1800,480),
                    font = super_season_accolade_font,
                    alignment = "center",
                    rotation = accolade_rotation
                )
                accolade_text = accolade_text.resize((375,150), Image.ANTIALIAS)
                accolade_text_images.append( (accolade_text, (x_position, y_position), accolade) )
                x_position += x_incremental
                y_position += accolade_spacing

        # BACKGROUND IMAGE LOGO
        num_accolades = max(len(accolade_text_images),1)
        num_accolades_str = "" if is_after_03 else f"-{num_accolades}"
        ss_type_index = self.set.super_season_image_index
        super_season_image = Image.open(self.__template_img_path(f'Super Season-{ss_type_index}{num_accolades_str}'))

        # ORDER 04/05 ACCOLADES BY TEXT LENGTH
        if is_after_03:
            coordinates = [tup[1] for tup in accolade_text_images]
            sorted_accolade_img_and_text = sorted([(tup[0], tup[2]) for tup in accolade_text_images], key=lambda a: len(a[1]), reverse=True)
            accolade_text_images = [(sorted_accolade_img_and_text[index][0], coordinates[index], sorted_accolade_img_and_text[index][1]) for index in range(0, len(accolade_text_images))]

        # PASTE ACCOLADES
        for accolade_img, paste_coordinates, _ in accolade_text_images:
            super_season_image.paste(colors.BLACK, paste_coordinates, accolade_img)

        # YEAR
        if self.is_multi_year:
            font_scaling = 0 if is_after_03 else 40
            if self.is_multi_year:
                year_string = f"'{str(min(self.year_list))[2:4]}-'{str(max(self.year_list))[2:4]}"
                font_size = 130 + font_scaling
            super_season_year_font = ImageFont.truetype(super_season_year_path, size=font_size)
        else:
            year_string = '’{}'.format(str(self.year)[2:4]) if is_after_03 else str(self.year)
        year_text = self.__text_image(
            text = year_string,
            size = (750,540) if is_after_03 else (1125,600),
            font = super_season_year_font,
            alignment = "left",
            rotation = 0 if is_after_03 else 7
        )
        year_text = year_text.resize((180,180), Image.ANTIALIAS)
        year_paste_coords = self.set.super_season_year_paste_coordinates(is_multi_year=self.is_multi_year)
        year_color = self.set.super_season_year_text_color
        super_season_image.paste(year_color, year_paste_coords, year_text)

        # ADJUSTMENTS TO 00/01 Y COORDINATES
        y_coord_adjustment = ( (3 - num_accolades) * 55 ) if self.set.is_00_01 and num_accolades < 3 else 0

        # RESIZE
        super_season_image = super_season_image.resize(self.set.template_component_size(TemplateImageComponent.SUPER_SEASON), Image.ANTIALIAS)
        return super_season_image, y_coord_adjustment

    def __rookie_season_image(self) -> Image.Image:
        """Creates image for optional rookie season logo.

        Args:
          None

        Returns:
          PIL image object for rookie season logo + year.
        """

        # BACKGROUND IMAGE LOGO
        rookie_season_image = Image.open(self.__template_img_path(f'{self.set.template_year}-Rookie Season'))

        # ADD YEAR
        first_year = str(min(self.year_list))
        year_font_path = self.__font_path('SquareSlabSerif')
        year_font = ImageFont.truetype(year_font_path, size=70)
        for index, year_part in enumerate([first_year[0:2],first_year[2:4]]):
            is_suffix = index > 0
            year_text = self.__text_image(
                text = year_part,
                size = (150,150),
                font = year_font,
                alignment = "left"
            )
            location_original = self.set.template_component_paste_coordinates(TemplateImageComponent.ROOKIE_SEASON_YEAR_TEXT)
            x_adjustment = 230 if is_suffix else 0
            paste_location = (location_original[0] + x_adjustment, location_original[1])
            rookie_season_image.paste(year_text,paste_location,year_text)

        # RESIZE
        logo_size = self.set.template_component_size(TemplateImageComponent.ROOKIE_SEASON)
        rookie_season_image = rookie_season_image.resize(logo_size, Image.ANTIALIAS)

        return rookie_season_image

    def __postseason_image(self) -> Image.Image:
        """Creates image for optional postseason edition logo.

        Args:
          None

        Returns:
          PIL image object for postseason logo + year(s).
        """

        # LOGO
        postseason_logo_image = Image.open(self.__template_img_path('Postseason'))

        # ADD YEAR(S)
        if not self.is_full_career:

            # BACKGROUND RED RECTANGLE
            box_width, box_height = self.set.template_component_size(TemplateImageComponent.POSTSEASON_YEAR_TEXT_BOX)
            red_rect_image = self.__rectangle_image(width=box_width, height=box_height, fill="#c44242")
            red_rect_paste_coords = self.set.template_component_paste_coordinates(TemplateImageComponent.POSTSEASON_YEAR_TEXT_BOX)
            postseason_logo_image.paste(red_rect_image, red_rect_paste_coords)

            # DEFINE YEAR TEXT
            year_range = f"'{str(min(self.year_list))[2:4]}-'{str(max(self.year_list))[2:4]}"
            year_str = year_range if self.is_multi_year else self.year

            year_font_path = self.__font_path('HelveticaNeueLtStd107ExtraBlack', extension='otf')
            font_size = 120 if self.is_multi_year else 140
            year_font = ImageFont.truetype(year_font_path, size=font_size)
            year_text = self.__text_image(
                text = year_str,
                size = (box_width, box_height),
                font = year_font,
                alignment='center'
            )
            year_text_x, year_text_y = self.set.template_component_paste_coordinates(TemplateImageComponent.POSTSEASON_YEAR_TEXT)
            if self.is_multi_year:
                year_text_y += 10
            postseason_logo_image.paste(year_text, (year_text_x, year_text_y), year_text)

        # RESIZE
        logo_size = self.set.template_component_size(TemplateImageComponent.POSTSEASON)
        postseason_logo_image = postseason_logo_image.resize(logo_size, Image.ANTIALIAS)

        return postseason_logo_image

    def __add_icons_to_image(self, player_image:Image.Image) -> Image.Image:
        """Add icon images (if player has icons) to existing player_image object.
           Only for >= 2003 sets.

        Args:
          player_image: Current PIL image object for Showdown card.

        Returns:
          Updated PIL Image with icons for player.
        """

        # ITERATE THROUGH AND PASTE ICONS
        for index, icon in enumerate(self.icons):
            position = self.set.icon_paste_coordinates(index+1)
            if self.set.is_wotc:
                icon_img_path = self.__template_img_path(f'{self.set.template_year}-{icon.value}')
                icon_image = Image.open(icon_img_path)
                # IN 2004/2005, ICON LOCATIONS DEPEND ON PLAYER POSITION LENGTH
                # EX: 'LF/RF' IS LONGER STRING THAN '3B'
                if self.set.is_04_05:
                    positions_list = self.positions_and_defense_for_visuals.keys()
                    positions_over_4_char = len([pos for pos in positions_list if len(pos) > 4 and not self.is_pitcher])
                    offset = 0
                    if len(positions_list) > 1:
                        # SHIFT ICONS TO RIGHT
                        additional_padding = 40 * positions_over_4_char if positions_over_4_char > 0 else 0
                        offset = 135 + additional_padding
                    elif positions_over_4_char > 0:
                        offset = 75
                    elif 'CA' in positions_list:
                        offset = 30
                    position = (position[0] + offset, position[1])
            else:
                icon_image = self.__icon_image_circle(text=icon.value)
            player_image.paste(icon_image, self.__coordinates_adjusted_for_bordering(position), icon_image)

        return player_image

    def __icon_image_circle(self, text:str) -> Image.Image:
        """For CLASSIC and EXPANDED sets, generate a circle image with text for the icons.

        Args:
          text: String to show on the icon

        Returns:
          PIL Image for with icon text and background circle.
        """
        # CIRCLE
        text_color = colors.WHITE
        border_size = 9
        icon_img = Image.new('RGBA',(220,220))
        draw = ImageDraw.Draw(icon_img)
        x1 = 20
        y1 = 20
        x2 = 190
        y2 = 190       
        draw.ellipse((x1-border_size, y1-border_size, x2+border_size, y2+border_size), fill=text_color)
        draw.ellipse((x1, y1, x2, y2), fill=self.__team_color_rgbs(is_secondary_color=self.image.use_secondary_color, team_override=self.team_override_for_images))

        # ADD TEXT
        font_path = self.__font_path('Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique')
        font = ImageFont.truetype(font_path, size=120)
        text_img = self.__text_image(text=text,size=(210,220),font=font,alignment='center',fill=text_color)
        icon_img.paste(text_img, (0,60), text_img)
        icon_img = icon_img.resize((80, 80), Image.ANTIALIAS)

        return icon_img
        
    def __add_additional_logos_00_01(self, image:Image.Image) -> Image.Image:
        """Add CC/RS/SS/PS logo to existing player_image object.
           Only for 2000/2001 sets.

        Args:
          image: Current PIL image object for Showdown card.

        Returns:
          Updated PIL Image with logos added above the chart.
        """
        
        # ONLY FOR 00/01 SETS
        if not self.set.is_00_01:
            return image
        
        # DEFINE COORDINATES, START WITH ROOKIE SEASON DESTINATION AND EDIT FOR OTHERS
        template_component = TemplateImageComponent.POSTSEASON if self.image.edition == Edition.POSTSEASON else TemplateImageComponent.ROOKIE_SEASON
        paste_coordinates = self.set.template_component_paste_coordinates(template_component)
        if self.image.edition != Edition.ROOKIE_SEASON and self.set == Set._2001:
            # MOVE LOGO TO THE RIGHT
            paste_coordinates = (paste_coordinates[0] + 30, paste_coordinates[1])
        if self.set == Set._2000:
            # MOVE LOGO ABOVE TEAM LOGO AND SLIGHTLY TO THE LEFT
            y_movement = -35 if self.image.edition == Edition.SUPER_SEASON else 0
            x_movement = -35 if self.image.edition == Edition.SUPER_SEASON else 0
            paste_coordinates = (paste_coordinates[0] - 25 + x_movement, paste_coordinates[1] + y_movement)

        # ADD LOGO
        match self.image.edition:
            case Edition.ALL_STAR_GAME | Edition.COOPERSTOWN_COLLECTION:
                logo_name = 'CCC' if self.image.edition == Edition.COOPERSTOWN_COLLECTION else f'ASG-{self.year}'
                logo_size_x, logo_size_y = self.set.template_component_size(TemplateImageComponent.TEAM_LOGO)
                logo_size = (logo_size_x + 85, logo_size_y + 85) if logo_name == 'ASG-2022' else (logo_size_x, logo_size_y)
                logo_path = self.__team_logo_path(name=logo_name)
                logo = Image.open(logo_path).convert("RGBA").resize(logo_size, Image.ANTIALIAS)
                image.paste(logo, self.__coordinates_adjusted_for_bordering(paste_coordinates), logo)
            case Edition.SUPER_SEASON:
                super_season_img, y_adjustment = self.__super_season_image()
                paste_coordinates_x, paste_coordinates_y = paste_coordinates
                paste_coordinates = (paste_coordinates_x, paste_coordinates_y - 220 + y_adjustment)
                image.paste(super_season_img, self.__coordinates_adjusted_for_bordering(paste_coordinates), super_season_img)
            case Edition.ROOKIE_SEASON:
                rs_logo = self.__rookie_season_image()
                image.paste(rs_logo, self.__coordinates_adjusted_for_bordering(paste_coordinates), rs_logo)
            case Edition.POSTSEASON:
                ps_logo = self.__postseason_image()
                image.paste(ps_logo, self.__coordinates_adjusted_for_bordering(paste_coordinates), ps_logo)
            case _:
                return image
            
        return image

    def __command_image(self) -> Image.Image:
        """For CLASSIC and EXPANDED sets, create onbase/control image asset dynamically

        Args:
          None

        Returns:
          PIL image object for Control/Onbase 
        """

        # BACKGROUND CONTAINER IMAGE
        img_type_suffix = 'Control' if self.is_pitcher else 'Onbase'
        dark_mode_suffix = '-DARK' if self.image.is_dark_mode else ''
        background_img = Image.open(self.__template_img_path(f'{self.set.template_year}-{img_type_suffix}{dark_mode_suffix}'))
        font_path = self.__font_path('HelveticaNeueLtStd107ExtraBlack', extension='otf')
        command = str(self.chart.command)
        num_chars_command = len(command)
        size = 170 if self.is_pitcher else 155
        font = ImageFont.truetype(font_path, size=size)

        # ADD TEXT
        fill_color = self.__team_color_rgbs(is_secondary_color=self.image.use_secondary_color, team_override=self.team_override_for_images)
        fill_color_hex = self.__rbgs_to_hex(rgbs=fill_color)
        # SEPARATE 
        for index, char in enumerate(command):
            position_multiplier = 1 if (index + 1) == num_chars_command else -1
            x_position = 0 if num_chars_command == 1 else 35 * position_multiplier
            command_text_img = self.__text_image(
                text = char,
                size = (188,210),
                font = font,
                alignment = "center",
            )
            paste_location = (22,43) if self.is_pitcher else (x_position,28)
            background_img.paste(fill_color_hex, paste_location, command_text_img)

        return background_img

    def __style_image(self) -> Image.Image:
        """ Style image for CLASSIC AND EXPANDED sets. Color scheme matches team colors
        
        Args:
          None

        Returns:
          PIL image with style logo
        """

        color = self.__team_color_rgbs(is_secondary_color=self.image.use_secondary_color) # NOTE: USES OPPOSITE COLOR
        color_hex = self.__rbgs_to_hex(rgbs=color)
        red, green, blue, _ = color
        color_lightness = (red*0.299 + green*0.587 + blue*0.114)
        is_shadow = color_lightness < 75 if self.image.is_dark_mode else color_lightness > 186

        # LOAD BACKGROUND
        theme_suffix = 'DARK' if self.image.is_dark_mode else 'LIGHT'
        shadow_suffix = '-SHADOW' if is_shadow else ''
        bg_image_path = self.__template_img_path(f'STYLE-BG-{theme_suffix}{shadow_suffix}')
        bg_image = Image.open(bg_image_path)

        # BACKGROUND
        logo_bg_original = Image.open(self.__template_img_path('STYLE-LOGO-BG'))
        logo_bg = self.__add_color_overlay_to_img(img=logo_bg_original, color=color)
        logo_bg_paste_coordinates = self.set.template_component_paste_coordinates(TemplateImageComponent.STYLE_LOGO_BG)
        bg_image.paste(logo_bg, logo_bg_paste_coordinates, logo_bg)

        # STYLE LOGO
        style_logo = Image.open(self.__template_img_path(f'STYLE-LOGO-{self.set.value}'))
        logo_paste_coordinates = self.set.template_component_paste_coordinates(TemplateImageComponent.STYLE_LOGO)
        bg_image.paste(style_logo, logo_paste_coordinates, style_logo)

        # STYLE TEXT
        style_font_path = self.__font_path('HelveticaNeueLtStd107ExtraBlack', extension='otf')
        style_font = ImageFont.truetype(style_font_path, size=225)
        style_text = self.__text_image(
            text = self.set.value,
            size = (1800, 300),
            font = style_font,
            alignment = "left"
        )
        style_text = style_text.resize((450,75), Image.ANTIALIAS)
        style_text_paste_location = self.set.template_component_paste_coordinates(TemplateImageComponent.STYLE_TEXT)
        bg_image.paste(color_hex, style_text_paste_location, style_text)
                
        return bg_image

    def __year_container_add_on(self) -> Image.Image:
        """User can optionally add a box dedicated to showing years used for the card.

        Applies to only the following contexts:
            - 2000
            - 2001
            - 2002
            - 2003

        Args:
          None

        Returns:
          PIL image with year range.
        """

        # LOAD CONTAINER
        path = self.__template_img_path("YEAR CONTAINER")
        year_img = Image.open(path)

        # ADD TEXT
        helvetica_neue_cond_bold_path = self.__font_path('HelveticaNeueLtStd107ExtraBlack', extension='otf')
        is_multi_year = len(self.year_list) > 1
        set_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=120 if is_multi_year else 160)
        year_end = max(self.year_list)
        year_start = min(self.year_list)
        year_str = f'{year_start}-{year_end}' if len(self.year_list) > 1 else f'{year_end}'
        year_text = self.__text_image(
            text = year_str,
            size = (600, 300),
            font = set_font,
            alignment = "center"
        )
        multi_year_y_adjustment = 3 if is_multi_year else 0
        year_text = year_text.resize((150,75), Image.ANTIALIAS)
        year_img.paste("#272727", (4,13 + multi_year_y_adjustment), year_text)

        return year_img

    def __date_range_or_split_image(self) -> Image.Image:
        """ Date Range or Split text image for partial year cards. Rounded rectangle with text.

        Args: 
          None

        Returns:
          PIL Image showing date range / split being shown on card.
        """

        # OPEN BACKGROUND IMAGE
        image_name = "DATE-RANGE-BG-LONG" if self.set.is_split_image_long else "DATE-RANGE-BG"
        split_image = Image.open(self.__template_img_path(image_name)).convert('RGBA')

        # SPLIT TEXT
        font_path = self.__font_path('HelveticaNeueLtStd107ExtraBlack', extension='otf')
        size = 120 if self.set.is_split_image_long else 135
        font = ImageFont.truetype(font_path, size=size)

        # GRAB TEXT
        match self.stats_period.type:
            case StatsPeriodType.POSTSEASON:
                text = 'POSTSEASON' if self.set.is_split_image_long else 'POST'
                text_list = [text]
            case StatsPeriodType.DATE_RANGE:
                text_list = [self.stats.get('first_game_date', None), self.stats.get('last_game_date', None)]
                text_list = [t for t in text_list if t]
                game_1_comp = self.stats.get('first_game_date', 'g1').strip()
                game_2_comp = self.stats.get('last_game_date', 'g2').strip()                    
                text = game_1_comp if game_1_comp == game_2_comp else ' - '.join(text_list)
            case StatsPeriodType.SPLIT:
                text = self.stats_period.split.upper()
                text_no_slash = text.replace('/',' ')
                text_list = [text]
                text_split_by_word = text_no_slash.split(' ')
                num_words = len(text_split_by_word)
                if len(text) > 7 and num_words > 1 and not self.set.is_split_image_long:
                    mid_point = int(num_words / 2)
                    part_1 = ' '.join(text_split_by_word[:mid_point])
                    part_2 = ' '.join(text_split_by_word[mid_point:])
                    text_list = [part_1, part_2]
                
        num_words = len(text_list)
        if self.set.is_split_image_long:
            text = text if len(text) < 17 else f"{text[:13]}.."
            text_image_large = self.__text_image(
                text = text,
                size = (1050, 900), # WONT MATCH DIMENSIONS OF RESIZE ON PURPOSE TO CREATE THICKER TEXT
                font = font,
                fill=colors.WHITE,
                alignment = "center",
            )
            text_image = text_image_large.resize((280,240), Image.ANTIALIAS)
            split_image.paste(text_image, (-5, 12), text_image)
        else:
            # ADD PERIOD
            y_position = 5 if num_words > 1 else 25
            for text in text_list:

                # SKIP IF NONE
                if text is None:
                    continue
                text = text if len(text) < 8 else f"{text[:6]}.."
                
                text_image_large = self.__text_image(
                    text = text,
                    size = (525, 450), # WONT MATCH DIMENSIONS OF RESIZE ON PURPOSE TO CREATE THICKER TEXT
                    font = font,
                    fill=colors.WHITE,
                    alignment = "center",
                )
                text_image = text_image_large.resize((140,120), Image.ANTIALIAS)
                split_image.paste(text_image, (0, y_position), text_image)
                y_position += 45

            # ADD DASH
            if self.stats_period.type == StatsPeriodType.DATE_RANGE and num_words > 1:
                dash_image_large = self.__text_image(
                    text = '-',
                    size = (525, 450), # WONT MATCH DIMENSIONS OF RESIZE ON PURPOSE TO CREATE THICKER TEXT
                    font = font,
                    fill=colors.WHITE,
                    alignment = "center",
                )
                dash_image = dash_image_large.resize((140,120), Image.ANTIALIAS)
                split_image.paste(dash_image, (0, 25), dash_image)

        return split_image


# ------------------------------------------------------------------------
# AUTOMATED PLAYER IMAGE
# ------------------------------------------------------------------------
    
    def __player_image_layers(self) -> list[tuple[Image.Image, tuple[int,int]]]:
        """Attempts to query google drive for a player image, if 
        it does not exist use siloutte background.

        Args:
          search_for_image: Boolean for whether to search google drive for image.
          uploaded_player_image: Optional image to use instead of searching. 

        Returns:
          List of tuples.
          Tuple contains:
            PIL image object for each component of the player's image.
            Coordinates for pasting to background image.
        """
        
        # DEFINE FINAL IMAGE
        images_to_paste: list[tuple[Image.Image, tuple[int,int]]] = []
        default_img_paste_coordinates = self.__coordinates_adjusted_for_bordering((0,0))

        # CHECK FOR USER UPLOADED IMAGE
        player_img_user_uploaded = None
        player_img_user_upload_transparency_pct = 0.0
        # ---- LOCAL/UPLOADED IMAGE -----
        if self.image.source.path:
            image_path = os.path.join(os.path.dirname(__file__), 'uploads', self.image.source.path)
            try:
                player_img_uploaded_raw = Image.open(image_path).convert('RGBA')
                player_img_user_uploaded = self.__center_and_crop(player_img_uploaded_raw, (1500,2100))
                images_to_paste.append((player_img_user_uploaded, default_img_paste_coordinates))
                player_img_user_upload_transparency_pct = self.__img_transparency_pct(player_img_user_uploaded)
            except Exception as err:
                self.image.error = str(err)
        
        # ---- IMAGE FROM URL -----
        elif self.image.source.url:
            # LOAD IMAGE FROM URL
            try:
                response = requests.get(self.image.source.url)
                player_img_raw = Image.open(BytesIO(response.content)).convert('RGBA')
                player_img_user_uploaded = self.__center_and_crop(player_img_raw, (1500,2100))
                images_to_paste.append((player_img_user_uploaded, default_img_paste_coordinates))
                player_img_user_upload_transparency_pct = self.__img_transparency_pct(player_img_user_uploaded)
            except Exception as err:
                self.image.error = str(err)

        # ---- IMAGE FROM GOOGLE DRIVE -----
        file_service = None
        if player_img_user_uploaded is None:
            search_for_universal_img = self.image.parallel != ImageParallel.MYSTERY
            img_components_dict = self.__player_image_components_dict()
            if search_for_universal_img:
                folder_id = self.set.player_image_gdrive_folder_id
                file_service, img_components_dict = self.__query_google_drive_for_auto_player_image_urls(folder_id=folder_id, components_dict=img_components_dict, bref_id=self.bref_id, year=self.year)
            
            # ADD SILHOUETTE IF NECESSARY
            non_empty_components = [typ for typ in self.image_component_ordered_list if img_components_dict.get(typ, None) is not None and typ.is_loaded_via_download]
            if len(non_empty_components) == 0:
                img_components_dict[PlayerImageComponent.SILHOUETTE] = self.__template_img_path(f'{self.set.template_year}-SIL-{self.player_classification}')
            
            player_imgs = self.__automated_player_image_layers(component_img_urls_dict=img_components_dict, file_service=file_service)
            if len(player_imgs) > 0:
                images_to_paste += player_imgs

        # IF 2000, ADD SET CONTAINER AND NAME CONTAINER IF USER UPLOADED IMAGE THATS NOT TRANSPARENT
        if self.set == Set._2000:
            if player_img_user_uploaded and player_img_user_upload_transparency_pct < 0.30:
                name_container = self.__2000_player_name_container_image()
                images_to_paste.append((name_container, default_img_paste_coordinates))
            set_container = self.__2000_player_set_container_image()
            images_to_paste.append((set_container, default_img_paste_coordinates))

        return images_to_paste

    def __automated_player_image_layers(self, file_service, component_img_urls_dict:dict) -> list[tuple[Image.Image, tuple[int,int]]]:
        """ Download and manipulate player image asset(s) to fit the current set's style.

        Args:
          component_img_urls_dict: Dict of image urls per component.

        Returns:
          List of tuples that contain a PIL image objects and coordinates to paste them
        """
        
        player_img_components = []
        is_img_download_error = False
        for img_component in self.image_component_ordered_list:
            
            # ADD SILHOUETTE IF NECESSARY
            if img_component == PlayerImageComponent.SILHOUETTE and is_img_download_error:
                component_img_urls_dict[PlayerImageComponent.SILHOUETTE] = self.__template_img_path(f'{self.set.template_year}-SIL-{self.player_classification}')
            
            # CHECK FOR IMAGE TYPE
            img_url = component_img_urls_dict.get(img_component, None)
            paste_coordinates = self.__coordinates_adjusted_for_bordering(coordinates=(0,0),is_disabled=not img_component.adjust_paste_coordinates_for_bordered)
            if img_url is None and not (img_component.load_source == 'COLOR' and img_component in component_img_urls_dict.keys()):
                continue

            # CARD SIZING
            card_size = self.set.card_size_bordered if self.image.is_bordered and not img_component.adjust_paste_coordinates_for_bordered else self.set.card_size
            card_width, card_height = card_size
            default_card_width, default_card_height = self.set.card_size
            size_growth_multiplier = ( card_width / default_card_width, card_height / default_card_height)
            original_crop_size = self.set.player_image_crop_size
            player_crop_size = (int(original_crop_size[0] * size_growth_multiplier[0]), int(original_crop_size[1] * size_growth_multiplier[1])) if self.image.is_bordered else original_crop_size
            special_crop_adjustment = self.set.player_image_crop_adjustment
            if self.set.is_showdown_bot and (self.image.special_edition == SpecialEdition.ASG_2023 or self.image.parallel == ImageParallel.TEAM_COLOR_BLAST):
                player_crop_size = (1275, 1785) #TODO: MAKE THIS DYNAMIC
                special_crop_adjustment = (0,int((1785 - 2100) / 2))
                if self.image.is_bordered:
                    player_crop_size = (int(player_crop_size[0] * size_growth_multiplier[0]), int(player_crop_size[1] * size_growth_multiplier[1]))
            default_crop_size = card_size

            # MOVE CROP WINDOW IF NECESSARY
            default_crop_adjustment = (0,0)
            if self.set in [Set._2002, Set._2003] and img_component.crop_adjustment_02_03 is not None:
                default_crop_adjustment = img_component.crop_adjustment_02_03
            set_crop_adjustment_for_component = self.set.player_image_component_crop_adjustment(img_component)
            if set_crop_adjustment_for_component:                
                default_crop_adjustment = set_crop_adjustment_for_component

            # DOWNLOAD IMAGE
            image = None
            match img_component.load_source:
                case "DOWNLOAD":
                    # 1. CHECK FOR IMAGE IN LOCAL CACHE. CACHE EXPIRES AFTER 20 MINS.
                    image = None
                    type_override = self.player_type_override.override_string if self.player_type_override else ''
                    stats_period = self.stats_period.type.player_image_search_term if self.stats_period.type.player_image_search_term else ''
                    cached_image_filename = f"{img_component.value}-{self.year}-({self.bref_id})-({self.team.value}){type_override}{stats_period}.png"
                    cached_image_path = os.path.join(os.path.dirname(__file__), 'uploads', cached_image_filename)
                    if not self.ignore_cache:
                        try:
                            image = Image.open(cached_image_path)
                            self.image.source.type = ImageSourceType.LOCAL_CACHE
                        except:
                            image = None

                    # 2. DOWNLOAD FROM GOOGLE DRIVE IF IMAGE IS NOT FOUND FROM CACHE.
                    if image is None:
                        image = self.__download_google_drive_image(file_service=file_service,file_id=img_url)
                        if image:
                            self.__cache_downloaded_image(image=image, path=cached_image_path)
                            self.image.source.type = ImageSourceType.GOOGLE_DRIVE
                case "COLOR":
                    image = Image.new(mode='RGBA',size=card_size,color=self.__team_color_rgbs(is_secondary_color=self.image.use_secondary_color, ignore_team_overrides=True, team_override=self.team_override_for_images))
                case "CARD_ART" | "SILHOUETTE":
                    image = Image.open(img_url).convert('RGBA')
                case "TEAM_LOGOS":
                    if self.image.parallel == ImageParallel.MOONLIGHT:
                        image, paste_coordinates = self.team_logo_for_background(team_override=self.team_override_for_images)
                        image = self.__change_image_saturation(image=image, saturation=0.05)
                        player_img_components.append((image, paste_coordinates))
                        continue
                    else:
                        image = Image.open(img_url).convert('RGBA').resize((1200,1200), resample=Image.ANTIALIAS)
                case "NAME_CONTAINER":
                    image = self.__2000_player_name_container_image()
                case _: 
                    break

            if image is None:
                if img_component.load_source == "DOWNLOAD":
                    is_img_download_error = True
                continue
            
            # ADJUST SATURATION
            saturation_adjustment = self.image.special_edition.image_component_saturation_adjustments_dict
            saturation_adjustment.update(self.image.parallel.image_type_saturations_dict)
            if len(saturation_adjustment) > 0:
                component_adjustment_factor = saturation_adjustment.get(img_component, None)
                if component_adjustment_factor:
                    image = self.__change_image_saturation(image=image, saturation=component_adjustment_factor)

            # ADJUST OPACITY
            if img_component.opacity < 1.0:
                opacity_255_scale = int(255 * img_component.opacity)
                image.putalpha(opacity_255_scale)

            # ADJUST SIZE
            size_adjustment_for_set = self.set.player_image_component_size_adjustment(img_component)
            if size_adjustment_for_set:
                new_size = (int(image.size[0] * size_adjustment_for_set), int(image.size[1] * size_adjustment_for_set))
                image = image.resize(size=new_size, resample=Image.ANTIALIAS)
            
            # CROP IMAGE
            crop_size = default_crop_size if img_component.ignores_custom_crop else player_crop_size
            crop_adjustment = default_crop_adjustment if img_component.ignores_custom_crop else special_crop_adjustment
            image = self.__img_crop(image, crop_size=crop_size, crop_adjustment=crop_adjustment)
            if crop_size != card_size:
                image = image.resize(size=card_size, resample=Image.ANTIALIAS)

            # SUPER SEASON: FIND LOCATIONS FOR ELLIPSES
            is_super_season_glow = img_component in [PlayerImageComponent.GLOW, PlayerImageComponent.SILHOUETTE] and self.image.special_edition == SpecialEdition.SUPER_SEASON
            if is_super_season_glow:

                # CALCULATE COORDINATES OF ELLIPSES

                # RANDOMIZE Y
                first_letter_name_ord = ord(self.name[0])
                year_ord = ord(str(self.median_year)[-1])
                total_index = min(first_letter_name_ord + year_ord, 179)

                random_bool_1 = total_index < 162
                random_bool_2 = year_ord > 54

                y_cords = {
                    PlayerImageComponent.ELLIPSE_LARGE: 850 if random_bool_2 else 800,
                    PlayerImageComponent.ELLIPSE_MEDIUM: 400 if random_bool_2 else 300,
                    PlayerImageComponent.ELLIPSE_SMALL: 1300 if random_bool_2 else 1400,
                }
                is_reversed_map = {
                    PlayerImageComponent.ELLIPSE_LARGE: random_bool_1,
                    PlayerImageComponent.ELLIPSE_MEDIUM: not random_bool_1,
                    PlayerImageComponent.ELLIPSE_SMALL: random_bool_1,
                }
                img_width, _ = image.size
                for ellipse_type, ycord in y_cords.items():
                    is_reversed = is_reversed_map.get(ellipse_type, False)
                    for x_index in range(1, img_width):
                        x_cord = img_width - x_index if is_reversed else x_index
                        coordinates = (x_cord, ycord)
                        try:
                            pixel = image.getpixel(coordinates)
                            pixel_opacity = pixel[3]
                        except:
                            break
                        if pixel_opacity > 200: # OUT OF 255
                            ellipse_circle_image = Image.open(self.__card_art_path(ellipse_type.value)).convert('RGBA')
                            ellipse_width, _ = ellipse_circle_image.size
                            ellipse_x_movement_mutliplier = 0.60 if is_reversed else 0.30
                            x_adjustment = -1 * int(ellipse_width * ellipse_x_movement_mutliplier)
                            coordinates_adjusted = (int(x_cord + x_adjustment), int(ycord))
                            player_img_components.append((ellipse_circle_image, coordinates_adjusted))
                            break

            # PASTE IMAGE
            player_img_components.append((image, paste_coordinates))

        return player_img_components

    def __query_google_drive_for_auto_player_image_urls(self, folder_id:str, components_dict:dict[PlayerImageComponent, str], bref_id:str, year:int = None) -> tuple:
        """Attempts to query google drive for a player image, if 
        it does not exist use siloutte background.

        Args:
          folder_id: Unique ID for folder in drive (found in URL)
          components_dict: Dict of all the image types to included in the image.
          bref_id: Unique ID for the player.
          additional_substring_search_list: List of strings to filter down results in case of multiple results.
          year: Year(s) of card.

        Returns:
          Tuple with the following:
            Google Drive file service object
            Dict of image urls per component.
        """
        
        # GAIN ACCESS TO GOOGLE DRIVE
        file_service = None
        SCOPES = ['https://www.googleapis.com/auth/drive']
        GOOGLE_CREDENTIALS_STR = os.getenv('GOOGLE_CREDENTIALS')
        if not GOOGLE_CREDENTIALS_STR:
            # IF NO CREDS, RETURN NONE
            return (file_service, components_dict)
        
        # CREDS FILE FOUND, PROCEED
        GOOGLE_CREDENTIALS_STR = GOOGLE_CREDENTIALS_STR.replace("\'", "\"")
        try:
            GOOGLE_CREDENTIALS_JSON = json.loads(GOOGLE_CREDENTIALS_STR)
        except:
            return (file_service, components_dict)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_JSON, SCOPES)

        # BUILD THE SERVICE OBJECT.
        service = build('drive', 'v3', credentials=creds)

        # GET LIST OF FILE METADATA FROM CORRECT FOLDER
        files_metadata = []
        page_token = None
        failure_number = 0
        while True and failure_number < 3:
            try:
                bref_id_cleaned = bref_id.replace("'",'')
                query = f"parents = '{folder_id}' and name contains '({bref_id_cleaned})'"
                file_service = service.files()
                response = file_service.list(q=query,pageSize=1000,pageToken=page_token).execute()
                new_files_list = response.get('files')
                page_token = response.get('nextPageToken', None)
                files_metadata = files_metadata + new_files_list
                if not page_token:
                    break
            except Exception as err:
                # IMAGE MAY FAIL TO LOAD SOMETIMES
                self.image.error = str(err)
                failure_number += 1
                continue
            
        
        # LOOK FOR SUBSTRING IN FILE NAMES
        file_matches_metadata_dict = self.__img_file_matches_dict(files_metadata=files_metadata, components_dict=components_dict, bref_id=bref_id, year=year)
        
        return (file_service, file_matches_metadata_dict)
    
    def __img_file_matches_dict(self, files_metadata:list[dict], components_dict:dict[PlayerImageComponent, str], bref_id:str, year:int) -> dict[PlayerImageComponent, str]:
        """ Iterate through gdrive files and find matches to the player and other settings defined by user.
         
        Args:
          files_metadata: List of file metadata dicts from google drive.
          components_dict: Dict of all the image types to included in the image.
          bref_id: Unique ID for the player.
          year: Year(s) of card.

        Returns:
          Dict where the key represents the component type and the value is the file id for download.
        """

        # FILTER LIST TO ONLY BREF ID MATCHES FOR IMG COMPONENT TYPE
        component_player_file_matches_dict = {component: [] for component in components_dict.keys() if component.is_loaded_via_download}
        for img_file in files_metadata:
            file_name_key = 'name'
            if file_name_key not in img_file.keys():
                continue
            # LOOK FOR SUBSTRING MATCH
            file_name = img_file[file_name_key]
            num_components_in_filename = len([c for c in components_dict.keys() if f'{c.value}-' in file_name])
            bref_id = bref_id.replace("'",'')
            if bref_id in file_name and num_components_in_filename > 0:
                component_name = file_name.split('-')[0].upper()
                component = PlayerImageComponent(component_name)
                current_files_for_component = component_player_file_matches_dict.get(component, [])
                current_files_for_component.append(img_file)
                component_player_file_matches_dict[component] = current_files_for_component

        # CHECK THAT THERE ARE MATCHES IN EACH COMPONENT
        num_matches_per_component = [len(matches) for _, matches in component_player_file_matches_dict.items()]
        if min(num_matches_per_component) < 1:
            return components_dict

        # ORDER EACH COMPONENT'S FILE LIST BY HOW WELL IT MATCHES PARAMETERS
        component_img_url_dict: dict[PlayerImageComponent, str] = {}
        additional_substring_search_list = self.__img_match_keyword_list()
        for component, img_file_list in component_player_file_matches_dict.items():
            img_file_list = sorted(img_file_list, key = lambda i: len(i['name']), reverse=False)
            match_scores: dict[str, float] = {}
            for img_metadata in img_file_list:
                img_name: str = img_metadata.get('name', None)
                img_id: str = img_metadata.get('id', None)
                match_score = sum(val in img_name for val in additional_substring_search_list)

                # ADD DISTANCE FROM YEAR                
                year_from_img_name = img_name.split(f"-")[1] if len(img_name.split(f"-")) > 1 else 1000
                is_img_multi_year = len(year_from_img_name) > 4
                if year_from_img_name == year:
                    # EXACT YEAR MATCH
                    match_score += 1
                elif is_img_multi_year == False and self.is_multi_year == False:
                    year_img = float(year_from_img_name)
                    year_self = float(year)
                    pct_diff = 1 - (abs(year_img - year_self) / year_self)
                    match_score += pct_diff

                # ADD TYPE OVERRIDE
                if self.player_type_override:
                    if self.player_type_override.override_string in img_name.upper():
                        match_score += 1

                # IF POSTSEASON IMAGE BUT NOT POSTSEASON CARD, REDUCE ACCURACY
                if '(POST)' in img_name and self.stats_period.type != StatsPeriodType.POSTSEASON:
                    match_score -= 2
                
                # ADD MATCH RATE SCORE
                match_scores[img_id] = match_score
            
            # GET BEST MATCH
            sorted_matches = sorted(match_scores.items(), key=operator.itemgetter(1), reverse=True)
            file_id = sorted_matches[0][0]
            component_img_url_dict[component] = file_id

        # UPDATE EXISTING DICT
        components_dict.update(component_img_url_dict)

        return components_dict

    def __img_match_keyword_list(self) -> list[str]:
        """ Generate list of keywords to match again google drive image

        Args:
          None

        Returns:
          List of keywords to match image fit with card.
        """
        # SEARCH FOR PLAYER IMAGE
        additional_substring_filters = [self.year, f'({self.team.value})',f'({self.team.value})'] # ADDS TEAM TWICE TO GIVE IT 2X IMPORTANCE
        
        # EDITION
        if self.image.edition != Edition.NONE:
            for _ in range(0,3): # ADD 3X VALUE
                additional_substring_filters.append(f'({self.image.edition.value})')

        # PLAYER TYPE OVERRIDE
        if self.player_type_override:
            additional_substring_filters.append(self.player_type_override.override_string)
        
        # DARK MODE
        if self.image.is_dark_mode:
            additional_substring_filters.append('(DARK)')

        # NATIONALITY
        if self.image.special_edition == SpecialEdition.NATIONALITY:
            for _ in range(0,4):
                additional_substring_filters.append(f'({self.nationality.value})') # ADDS NATIONALITY THREE TIMES TO GIVE IT 3X IMPORTANCE
        
        # PERIOD TYPE
        if self.stats_period.type.player_image_search_term: 
            additional_substring_filters.append(self.stats_period.type.player_image_search_term)

        return additional_substring_filters

    def __player_image_components_dict(self) -> dict[PlayerImageComponent, str]:
        """ Add card art image paths (ex: Cooperstown, Super Season, Gradient, etc). 
        
        Add empty placeholders for image assets that are loaded from google drive.

        Returns:
          Dict with all components
        """

        # COOPERSTOWN
        is_cooperstown = self.image.edition == Edition.COOPERSTOWN_COLLECTION
        default_components_for_context = {c: self.__template_img_path("2000-Name") if c == PlayerImageComponent.NAME_CONTAINER_2000 else None for c in self.set.player_image_components_list() }
        special_components_for_context = {c: self.__template_img_path("2000-Name") if c == PlayerImageComponent.NAME_CONTAINER_2000 else None for c in self.set.player_image_components_list(is_special=True) }

        if self.image.parallel.has_special_components:
            # ADD ADDITIONAL COMPONENTS
            if len(self.image.parallel.special_component_additions(self.set.value)) > 0:
                team_logo_name = self.team.logo_name(year=self.median_year)
                special_components_for_context.update({img_component: self.__team_logo_path(team_logo_name) if img_component == PlayerImageComponent.TEAM_LOGO else self.__card_art_path(relative_path) for img_component, relative_path in self.image.parallel.special_component_additions(self.set.value).items()})
            # EDITING EXISTING COMPONENTS
            replacements_dict = self.image.parallel.special_components_replacements
            for old_component, new_component in replacements_dict.items():
                special_components_for_context.pop(old_component, None)
                special_components_for_context[new_component] = None
            is_asg_and_team_color_blast_dark = ( self.image.special_edition == SpecialEdition.ASG_2023 and self.image.is_dark_mode and self.image.parallel == ImageParallel.TEAM_COLOR_BLAST )
            if self.image.special_edition == SpecialEdition.TEAM_COLOR_BLAST_DARK or is_asg_and_team_color_blast_dark:
                special_components_for_context.pop(PlayerImageComponent.WHITE_CIRCLE, None)
                special_components_for_context[PlayerImageComponent.BLACK_CIRCLE] = self.__card_art_path(PlayerImageComponent.BLACK_CIRCLE.name)
            default_components_for_context = special_components_for_context

        if is_cooperstown and not self.set.is_00_01:
            components_dict = special_components_for_context
            components_dict[PlayerImageComponent.COOPERSTOWN] = self.__card_art_path('RADIAL' if self.set in [Set._2002, Set._2003] else 'COOPERSTOWN')
            return components_dict

        # SUPER SEASON
        if self.image.edition == Edition.SUPER_SEASON and self.set.is_04_05:
            components_dict = special_components_for_context
            components_dict[PlayerImageComponent.DARKENER] = self.__card_art_path('DARKENER')
            components_dict[PlayerImageComponent.SUPER_SEASON] = self.__card_art_path('SUPER SEASON')
            return components_dict
        
        # ALL STAR
        if self.image.special_edition == SpecialEdition.ASG_2023 and not self.set.is_00_01:
            components_dict = { c:v for c, v in special_components_for_context.items() if not c.is_loaded_via_download }
            components_dict.update({
                PlayerImageComponent.GLOW: None,
                PlayerImageComponent.CUSTOM_BACKGROUND: self.__card_art_path(f'ASG-2023-BG-{self.league}'),
            })
            if self.set.is_after_03:
                components_dict[PlayerImageComponent.CUSTOM_FOREGROUND] = self.__card_art_path(f'ASG-2023-FG')
            return components_dict

        # CLASSIC/EXPANDED
        if self.set.is_showdown_bot and not is_cooperstown and self.image.parallel == ImageParallel.NONE:
            components_dict = default_components_for_context
            components_dict[PlayerImageComponent.GRADIENT] = self.__card_art_path(f"{'DARK' if self.image.is_dark_mode else 'LIGHT'}-GRADIENT")
            return components_dict

        return default_components_for_context

    def __cache_downloaded_image(self, image:Image.Image, path:str) -> None:
        """Store downloaded image to the uploads folder in order to cache it
        
        Args:
          image: PIL Image to cache in uploads folder.
          path: Path for storing the image.

        Returns:
          None
        """
        image.save(path, quality=100)


# ------------------------------------------------------------------------
# IMAGE HELPER METHODS
# ------------------------------------------------------------------------

    def __template_img_path(self, img_name:str) -> str:
        """ Produces full path string for the image.

        Args:
          img_name: Name of the image, excluding extension.

        Returns:
          string with full image path.
        """

        return os.path.join(os.path.dirname(__file__), 'templates', f'{img_name}.png')

    def __font_path(self, name:str, extension:str = 'ttf') -> str:
        """ Produces full path string for the image.

        Args:
          name: Name of the font, excluding extension.
          extension: Font file extension (ex: ttf, otf)

        Returns:
          String with full font path.
        """

        return os.path.join(os.path.dirname(__file__), 'fonts', f'{name}.{extension}')

    def __card_art_path(self, name:str, extension:str = 'png') -> str:
        """ Produces full path string for the image.

        Args:
          name: Name of the image without the extension
          extension: Image file extension (ex: png, jpg)

        Returns:
          String with full image path.
        """

        if name is None:
            return None
        
        return os.path.join(os.path.dirname(__file__), 'card_art', f'{name}.{extension}')

    def __team_logo_path(self, name:str, extension:str = 'png') -> str:
        """ Produces full path string for the logo image.

        Args:
          name: Name of the image without the extension
          extension: Image file extension (ex: png, jpg)

        Returns:
          String with full image path.
        """

        alternate_substring = '-A'
        is_alternate = alternate_substring in name
        path = os.path.join(os.path.dirname(__file__), 'team_logos', f'{name}.{extension}')
        if not os.path.isfile(path) and is_alternate:
            path = path.replace(alternate_substring, '')

        return path

    def __coordinates_adjusted_for_bordering(self, coordinates:tuple[int,int], is_disabled:bool = False) -> tuple[int,int]:
        """Add padding to paste coordinates to account for a border on the image.
         
        Args:
          coordinates: Tuple for original coordinates (ex: (0,0))
          is_disabled: Return coordinates without an update

        Returns:
          Updated tuple for adjusted coordinates.
        """

        if not self.image.is_bordered or is_disabled:
            return coordinates
        
        padding = self.set.card_border_padding
        return (coordinates[0] + padding, coordinates[1] + padding)

    def __team_color_rgbs(self, is_secondary_color:bool=False, ignore_team_overrides:bool = False, team_override:Team = None) -> tuple[int,int,int,int]:
        """RGB colors for player team

        Args:
          is_secondary_color: Optionally use secondary color instead of primary.
          ignore_team_overrides: Boolean to optionally skip overrides.
          team_override: Optionally use a different team. Used for some special editions like CC.

        Returns:
            Tuple with RGB team colors
        """

        team = team_override if team_override else self.team

        # NATIONALITY COLOR
        if self.image.special_edition == SpecialEdition.NATIONALITY and not ignore_team_overrides:
            return self.nationality.primary_color
        
        # SPECIAL EDITION COLOR
        special_edition_color = self.image.special_edition.color(league=self.league)
        if special_edition_color and not ignore_team_overrides:
            return special_edition_color
        
        # GRAB FROM CURRENT TEAM COLORS
        return team.color(year=self.median_year, is_secondary=is_secondary_color)

    def __img_transparency_pct(self, image: Image.Image) -> float:
        """ Calculate what percent of an image is transparent/transclucent 
        
        Args:
          image: PIL Image to conduct transparency test on.

        Returns:
          Float for percentage of image with transparent pixels.
        """

        img_width, img_height = image.size

        results: list[int] = []
        for x_coord in range(1, img_width):
            for y_coord in range(1, img_height):
                coordinates = (x_coord, y_coord)
                try:
                    pixel = image.getpixel(coordinates)
                    pixel_opacity = pixel[3]
                    results.append(int(pixel_opacity < 200))
                except:
                    continue
        
        if len(results) == 0:
            return 0.0
        
        pct = sum(results) / len(results)
        return pct


# ------------------------------------------------------------------------
# GENERIC IMAGE METHODS
# ------------------------------------------------------------------------

    def __text_image(self, text:str, size:tuple[int,int], font:ImageFont.FreeTypeFont, fill=255, rotation:int=0, alignment:str='left', padding:int=0, spacing:int=3, opacity:float=1, has_border:bool=False, border_color=None, border_size:int=3, overlay_image_path:str=None) -> Image.Image:
        """Generates a new PIL image object with text.

        Args:
          text: string of text to display.
          size: Tuple of image size.
          font: PIL font object.
          fill: Hex color of text body.
          rotation: Degrees of rotation for the text (optional)
          alignment: String (left, center, right) for alignment of text within image.
          padding: Number of pixels worth of padding from image edge.
          spacing: Pixels of space between lines of text.
          opacity: Transparency of text.
          has_border: Boolean flag to add border.
          border_color: Color of border.
          border_size: Pixel size of border thickness.
          overlay_image_path: Path of overlay image.
        
        Returns:
          PIL image object with desired text and formatting.
        """

        mode = 'RGBA' if has_border else 'L'
        text_layer = Image.new(mode,size)
        draw = ImageDraw.Draw(text_layer)
        w, h = draw.textsize(text, font=font)
        if alignment == "center":
            x = (size[0]-w) / 2.0
        elif alignment == "right":
            x = size[0] - padding - w
        else:
            x = 0 + padding
        y = 0
        # OPTIONAL BORDER
        if has_border:
            y += border_size
            draw.text((x-border_size, y), text, font=font, spacing=spacing, fill=border_color, align=alignment)
            draw.text((x+border_size, y), text, font=font, spacing=spacing, fill=border_color, align=alignment)
            draw.text((x, y-border_size), text, font=font, spacing=spacing, fill=border_color, align=alignment)
            draw.text((x, y+border_size), text, font=font, spacing=spacing, fill=border_color, align=alignment)
        draw.text((x, y), text, font=font, spacing=spacing, fill=fill, align=alignment)
        rotated_text_layer = text_layer.rotate(rotation, expand=1, resample=Image.BICUBIC)

        # OPTIONAL IMAGE OVERLAY
        if overlay_image_path is not None:
            # CREATE BACKGROUND/TRANSPARENCY
            texture_background = Image.open(overlay_image_path).convert('RGBA')
            transparent_overlay_image = Image.new('RGBA', texture_background.size, color=(0,0,0,0))
            # ADD TEXT MASK
            mask_img = Image.new('L', texture_background.size, color=255)
            mask_img_draw = ImageDraw.Draw(mask_img)
            mask_img_draw.text((x, y), text, fill=0, font=font, spacing=spacing, align=alignment)
            # CREATE FINAL IMAGE
            combined_image = Image.composite(transparent_overlay_image, texture_background, mask_img)
            combined_image_rotated = combined_image.rotate(rotation, expand=1, resample=Image.BICUBIC)
            return combined_image_rotated
        else:
            return rotated_text_layer

    def __round_corners(self, image:Image.Image, radius:int) -> Image.Image:
        """Round corners of a given image to a certain radius.

        Args:
          image: PIL image object to edit.
          radius: Number of pixels to round corner.

        Returns:
          PIL image object with desired rounded corners.
        """

        circle = Image.new ('L', (radius * 2, radius * 2), 0)
        draw = ImageDraw.Draw (circle)
        draw.ellipse ((0, 0, radius * 2, radius * 2), fill = 255)
        alpha = Image.new ('L', image.size, 255)
        w, h = image.size

        alpha.paste (circle.crop ((0, 0, radius, radius)), (0, 0))
        alpha.paste (circle.crop ((0, radius, radius, radius * 2)), (0, h-radius))
        alpha.paste (circle.crop ((radius, 0, radius * 2, radius)), (w-radius, 0))
        alpha.paste (circle.crop ((radius, radius, radius * 2, radius * 2)), (w-radius, h-radius))
        image.putalpha (alpha)

        return image

    def __center_and_crop(self, image:Image.Image, crop_size:tuple[int,int]) -> Image.Image:
        """Uses image size to crop in the middle for given crop size.
           Used to automatically center player image background.

        Args:
          image: PIL image object to edit.
          crop_size: Tuple representing width and height of desired crop.

        Returns:
          Centered and cropped PIL image object.
        """

        # IMAGE AND CROP WIDTH/HEIGHT
        width, height = image.size
        crop_width, crop_height = crop_size

        # FIND CLOSEST SIDE (X VS Y)
        x_ratio = crop_width / width
        y_ratio = crop_height / height
        x_diff = abs(x_ratio)
        y_diff = abs(y_ratio)
        scale = x_ratio if x_diff > y_diff else y_ratio
        image = image.resize((int(width * scale), int(height * scale)), Image.ANTIALIAS)

        # CROP THE CENTER OF THE IMAGE
        return self.__img_crop(image=image, crop_size=crop_size)

    def __img_crop(self, image:Image.Image, crop_size:tuple[int,int], crop_adjustment:tuple[int,int] = (0,0)) -> Image.Image:
        """Crop and image in the center to the given size.

        Args:
          image: PIL image object to edit.
          crop_size: Tuple representing width and height of desired crop.
          crop_adjustment:  Tuple representing width and height adjustment (optional)

        Returns:
          Cropped PIL image object.
        """
        crop_width, crop_height = crop_size
        current_width, current_height = image.size
        width_adjustment, height_adjustment = crop_adjustment
        left = ( (current_width - crop_width) / 2 ) + width_adjustment
        top = ( (current_height - crop_height) / 2 ) + height_adjustment
        right = ( (current_width + crop_width) / 2 ) + width_adjustment
        bottom = ( (current_height + crop_height) / 2 ) + height_adjustment

        # CROP THE CENTER OF THE IMAGE
        return image.crop((left, top, right, bottom))

    def __add_alpha_mask(self, img:Image.Image, mask_img:Image.Image) -> Image.Image:
        """Adds mask to image

        Args:
          img: PIL image to apply mask to
          mask_img: PIL image to take alpha values from

        Returns:
            PIL image with mask applied
        """
        
        alpha = mask_img.getchannel('A')
        img.putalpha(alpha)

        return img

    def __add_color_overlay_to_img(self, img:Image.Image, color:str) -> Image.Image:
        """Adds mask to image with input color.

        Args:
          img: PIL image to apply color overlay to
          color: HEX color for overlay

        Returns:
            PIL image with color overlay
        """

        # CREATE COLORED IMAGE THE SAME SIZE AND COPY ALPHA CHANNEL ACROSS
        colored_img = Image.new('RGBA', img.size, color=color)
        colored_img = self.__add_alpha_mask(img=colored_img, mask_img=img)

        return colored_img

    def __gradient_img(self, size:tuple[int,int], colors:list[tuple[int,int,int,int]]) -> Image.Image:
        """Create PIL Image with a horizontal gradient of 2 colors

        Args:
          size: Tuple of x and y sizing of output
          colors: List of colors to use. Order determines left -> right.

        Returns:
            PIL image with color gradient
        """

        # MAKE OUTPUT IMAGE
        final_image = Image.new('RGBA', size, color=0)
        num_iterations = len(colors) - 1
        w, h = (int(size[0] / num_iterations), size[1])

        for index in range(0, num_iterations):
            # GRADIENT
            color1 = colors[index]
            color2 = colors[index + 1]
            
            gradient = np.zeros((h,w,3), np.uint8)
            
            # FILL R, G AND B CHANNELS WITH LINEAR GRADIENT BETWEEN TWO COLORS
            gradient[:,:,0] = np.linspace(color1[0], color2[0], w, dtype=np.uint8)
            gradient[:,:,1] = np.linspace(color1[1], color2[1], w, dtype=np.uint8)
            gradient[:,:,2] = np.linspace(color1[2], color2[2], w, dtype=np.uint8)

            sub_image = Image.fromarray(gradient).convert("RGBA")
            final_image.paste(sub_image, (int(index * w),0))

        return final_image

    def __change_image_saturation(self, image:Image.Image, saturation:float) -> Image.Image:
        """Adjust an image's saturation.

        Args:
          image: PIL Image to update saturation for.
          saturation: Float from 0.0-1.0 where 1.0 is full color, 0.0 is greyscale.

        Returns:
          Updated PIL Image with changed saturation.
        """

        if saturation == 1.0:
            return image
        
        img_enhance = ImageEnhance.Color(image)
        image = img_enhance.enhance(saturation)

        return image

    def __download_google_drive_image(self, file_service, file_id:str, num_tries:int = 1) -> Image.Image:
        """ Attempt a download of the google drive image for url.
         
        Args:
          file_service: Google file service that executes the download for the file.
          file_id: Unique file id for the image.
          num_tries: Number of tries before returning download failure.

        Returns:
          PIL Image for url.
        """

        # CHECK FOR EMPTY VARIABLES
        if file_id is None or file_service is None:
            return None

        num_tries = 1
        for try_num in range(num_tries):
            try:
                request = file_service.get_media(fileId=file_id)
                file = BytesIO()
                downloader = MediaIoBaseDownload(file, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                image = Image.open(file).convert("RGBA")
                return image
            except Exception as err:
                # IMAGE MAY FAIL TO LOAD SOMETIMES
                self.image.error = str(err)
                continue
        
        return None

    def __rectangle_image(self, width:int, height:int, fill:str) -> Image.Image:
        """Create a new rectangle image with a particular color.

        Args:
          width: Width of the rectangle.
          height: Height of the rectangle.
          fill: Fill color of the rectangle.

        Returns:
          PIL Image for colored rectangle.
        """

        rect_image = Image.new("RGB", (width, height), fill)

        return rect_image


# ------------------------------------------------------------------------
# SHOWDOWN IMAGE LIBRARY IMPORT
# ------------------------------------------------------------------------

    def cached_img_link(self) -> str:
        """URL for the cached player image from Showdown Library. 

        Will return None if the image is custom and does not match cache.

        Player can have 4 different types of images:
            - Standard
            - Standard w/ Border
            - Dark Mode (CLASSIC & EXPANDED)
            - Dark Mode w/ Border (CLASSIC & EXPANDED)

        Args:
          None

        Returns:
          URL for image if it exists.
        """
        cached_img_id = self.__img_id_for_style()
        if cached_img_id and not self.is_img_processing_required():
            # LOAD DIRECTLY FROM GOOGLE DRIVE
            return f'https://drive.google.com/uc?id={cached_img_id}'
        else:
            return None

    def __img_id_for_style(self) -> str:
        """Unique ID for the google drive image for the player.

        Player can have 4 different types of images:
            - Standard
            - Standard w/ Border
            - Dark Mode (CLASSIC & EXPANDED)
            - Dark Mode w/ Border (CLASSIC & EXPANDED)

        Args:
          None

        Returns:
          Id for image if it exists
        """

        return None  # TODO: ADD IMAGE CACHING FROM FIREBASE STORAGE

    def is_img_processing_required(self) -> bool:
        """Certain attributes about a card dictate when processing a new image is required, 
        even if the card has an image in the Showdown Library.

        List of reasons:
            - Non V1 Card.
            - Custom set number
            - Has special edition (ex: CC, SS, RS)
            - Has variable speed
            - Is a Foil
            - Img Link was provided by user
            - Img Upload was provided by user
            - Set Year Plus 1 Enabled
            - Hide Team Logo Enabled

        Args:
          None

        Returns:
          Id for image if it exists
        """

        is_not_v1 = self.chart_version != 0
        has_user_uploaded_img = self.image.source.type.is_user_generated
        has_special_edition = self.image.edition.is_not_empty
        has_expansion = self.image.expansion != Expansion.BS
        has_variable_spd_diff = self.is_variable_speed_00_01 and self.set.is_00_01
        set_yr_plus_one_enabled = self.image.add_one_to_set_year and self.set.is_04_05
        return has_user_uploaded_img or has_expansion or is_not_v1 or has_special_edition or has_variable_spd_diff or self.image.set_number or set_yr_plus_one_enabled or self.image.hide_team_logo


# ------------------------------------------------------------------------
# EXPORTING
# ------------------------------------------------------------------------

    def save_image(self, image:Image.Image, start_time:datetime, show:bool=False, img_name_suffix:str='') -> None:
        """Stores image in proper folder depending on the context of the run.

        Args:
          image: PIL image object
          start_time: Datetime in which card image processing began.
          show: Boolean flag for whether to open the final image after creation.
          disable_add_border: Optional flag to skip border addition.
          img_name_suffix: Optional suffix added to the image name.

        Returns:
          None
        """

        self.image.output_file_name = f'{self.name}-{str(datetime.now())}.png'
        if self.image.set_name:
            self.image.output_file_name = f'{self.image.set_number} {self.name}{img_name_suffix}.png'            
        
        if self.set.convert_final_image_to_rgb:
            image = image.convert('RGB')

        save_img_path = os.path.join(self.image.output_folder_path, self.image.output_file_name)
        image.save(save_img_path, dpi=(300, 300), quality=100)
        
        if self.is_running_in_flask:
            flask_img_path = os.path.join(Path(os.path.dirname(__file__)).parent,'static', 'output', self.image.output_file_name)
            image.save(flask_img_path, dpi=(300, 300), quality=100)

        # OPEN THE IMAGE LOCALLY
        if show:
            image_title = f"{self.name} - {self.year}"
            image.show(title=image_title)

        self.__clean_images_directory()

        # CALCULATE LOAD TIME
        end_time = datetime.now()
        self.load_time = round((end_time - start_time).total_seconds(),2)

    def __clean_images_directory(self) -> None:
        """Removes all images from output folder that are not the current card. Leaves
           photos that are less than 5 mins old to prevent errors from simultaneous uploads.

        Args:
          None

        Returns:
          None
        """

        # IGNORE CLEANING
        if self.disable_cache_cleaning:
            return

        # FINAL IMAGES
        output_folder_paths = [os.path.join(os.path.dirname(__file__), 'output')]
        flask_output_path = os.path.join('static', 'output')
        if os.path.isdir(flask_output_path):
            output_folder_paths.append(flask_output_path)

        for folder_path in output_folder_paths:
            for item in os.listdir(folder_path):
                if item != self.image.output_file_name and item != '.gitkeep':
                    item_path = os.path.join(folder_path, item)
                    is_file_stale = self.__is_file_over_mins_threshold(path=item_path, mins=5)
                    if is_file_stale:
                        # DELETE IF UPLOADED/MODIFIED OVER 5 MINS AGO
                        os.remove(item_path)

        # UPLOADED IMAGES (PACKAGE)
        for item in os.listdir(os.path.join(os.path.dirname(__file__), 'uploads')):
            if item != '.gitkeep':
                # CHECK TO SEE IF ITEM WAS MODIFIED MORE THAN 5 MINS AGO.
                item_path = os.path.join(os.path.dirname(__file__), 'uploads', item)
                is_file_stale = self.__is_file_over_mins_threshold(path=item_path, mins=20)
                if is_file_stale:
                    # DELETE IF UPLOADED/MODIFIED OVER 20 MINS AGO
                    os.remove(item_path)

    def __is_file_over_mins_threshold(self, path:str, mins:float = 5.0) -> bool:
        """Checks modified date of file to see if it is older than 5 mins.
           Used for cleaning output directory and image uploads.

        Args:
          path: String path to file in os.
          mins: Number of minutes to check for

        Returns:
            True if file in path is older than 5 mins, false if not.
        """

        datetime_current = datetime.now()
        datetime_uploaded = datetime.fromtimestamp(os.path.getmtime(path))
        file_age_mins = (datetime_current - datetime_uploaded).total_seconds() / 60.0

        return file_age_mins >= mins

    def as_json(self) -> dict:
        """Convert current class to a json"""
        
        return self.model_dump(mode="json", exclude_none=True)