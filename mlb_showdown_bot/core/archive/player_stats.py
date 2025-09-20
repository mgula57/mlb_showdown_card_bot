import json
import os, fnmatch, operator
from typing import Optional
from enum import Enum
from datetime import datetime

from ..card.stats.baseball_ref_scraper import BaseballReferenceScraper
from ..card.showdown_player_card import ShowdownPlayerCard, PlayerType, StatsPeriod, StatsPeriodType

class PlayerSubType(Enum):

    POSITION_PLAYER = "POSITION_PLAYER"
    RELIEF_PITCHER = "RELIEF_PITCHER"
    STARTING_PITCHER = "STARTING_PITCHER"
    

class PlayerStats:

# ------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------

    def __init__(self, year:int, type: PlayerType, data:dict, two_way_players_list:list[str], historical_date:str = None) -> None:

        # FROM BREF
        self.bref_id: str = None
        self.lg_id: str = None
        self.name: str = None
        self.team_override: str = None # TODO: ADD THIS FEATURE
        self.team_id: str = None
        self.team_id_list: list[str] = None
        self.team_games_played_dict: dict[str,int] = {}
        self.year: int = year
        self.historical_date = historical_date
        self.stats: dict = {}

        # STATS FOR FILTERING
        self.g: int = 0
        self.gs: int = 0
        self.pa: int = None
        self.ip: int = None
        self.war: Optional[float] = None

        # PLAYER TYPE
        self.player_type: PlayerType = type
        self.player_type_override: str = None
        
        # DEFINE SET OF FIELDS
        included_attr = list(self.__dict__.keys())
        excluded_cols = ['player_type']
        for key, value in data.items():
            key_lowered = key.lower()
            if key_lowered in included_attr and key_lowered not in excluded_cols:
                setattr(self, key, value)

        # 2 WAY PLAYER TYPE OVERRIDE
        self.is_two_way: bool = self.bref_id in two_way_players_list
        if self.is_two_way and self.player_type == PlayerType.PITCHER:
            self.player_type_override = "(pitcher)"

        # SET CONCATINATED ID
        id_components = [str(self.year), self.bref_id, self.player_type_override, self.historical_date]
        concat_str_list = [component for component in id_components if component is not None]
        self.id: str = "-".join(concat_str_list)

        # SET POSITIONS
        pos_summary_str = str(data.get('pos', '' if self.player_type == PlayerType.HITTER else '1'))
        self.primary_positions = self.__convert_position_summary_to_list(position_summary=pos_summary_str)
        self.secondary_positions = self.__convert_position_summary_to_list(position_summary=pos_summary_str, is_secondary_positions=True)

        # MODIFIED DATES
        self.created_date: datetime = None
        self.modified_date: datetime = None
        self.stats_modified_date: datetime = None

# ------------------------------------------------------------------------
# GET FULL STATS FROM BREF/SAVANT
# ------------------------------------------------------------------------

    def scrape_stats_data(self) -> None:
        """Leverage Showdown Bot's baseball reference class to get full player stats.
        Store resulting dict as class attribute.
        
        Args:
          None

        Returns:
          None
        """

        stats_period = StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(self.year))
        baseball_reference_stats = BaseballReferenceScraper(stats_period=stats_period, name=self.bref_id_and_overrides, year=str(self.year), ignore_cache=True, ignore_archive=True)
        self.stats = baseball_reference_stats.fetch_player_stats()

# ------------------------------------------------------------------------
# PROPERTIES
# ------------------------------------------------------------------------

    @property
    def all_positions(self) -> list[str]:
        return self.primary_positions + self.secondary_positions

    @property
    def player_subtype(self) -> PlayerSubType:
        if self.player_type == PlayerType.PITCHER:
            games_started_ratio = self.gs / self.g
            if games_started_ratio > 0.40:
                return PlayerSubType.STARTING_PITCHER
            else:
                return PlayerSubType.RELIEF_PITCHER
        else:
            return PlayerSubType.POSITION_PLAYER

    @property
    def primary_position(self) -> str:
        if len(self.all_positions) == 0:
            return None
        primary_position_raw = self.all_positions[0]
        if primary_position_raw in ['LF','RF']:
            return 'LF/RF'
        
        if primary_position_raw == 'P':
            return self.player_subtype.abbreviation
        
        return primary_position_raw

    @property
    def positions(self) -> str:
        return ','.join(self.all_positions)

    @property
    def bref_id_and_overrides(self) -> str:
        type_override = f" {self.player_type_override}" if self.player_type_override else ""
        team_override = "" # TODO: ADD INPUT FOR THIS
        return f"{self.bref_id}{type_override}{team_override}"

    @property
    def meets_minimum_pa_or_ip_requirements(self) -> bool:
        """Check that IP > 30 for pitchers and PA > 30 for hitters"""
        stat = self.pa if self.player_type == PlayerType.HITTER else self.ip
        limit = 0 if self.player_type == PlayerType.HITTER else 0
        if self.year == 2020:
            limit = limit * 0.4
        if stat is None:
            return False
        
        return stat >= limit

    def as_dict(self, convert_stats_to_json:bool = False) -> dict:
        """Convert to dictionary. Convert subclasses and enums to exportable types"""
        
        data = self.__dict__.copy()
        data['player_type'] = self.player_type.value.upper()

        if convert_stats_to_json:
            data['stats'] = json.dumps(self.stats)
            data['team_games_played_dict'] = json.dumps(self.team_games_played_dict)

        return data

    def games_played_for_team(self, team_id:str) -> int:
        return self.team_games_played_dict.get(team_id, 0)
    
    @property
    def games_as_rp(self) -> int:
        if self.player_type == PlayerType.HITTER:
            return 0
        
        return self.g - self.gs

    def is_over_team_games_played_threshold(self) -> bool:
        """Checks to see if the player played at least 25% of their games for the last team they were on."""
        return self.games_played_for_team(self.team_id) >= (self.g * 0.25)
    
    @property
    def is_single_team_id(self) -> bool:
        team_id_last_two = self.team_id[-2:]
        return self.team_id not in ['TOT'] and not (team_id_last_two == 'TM' and len(self.team_id) == 3)
    
    @property
    def is_multi_league_id(self) -> bool:
        return self.lg_id == 'MLB' or 'LG' in self.lg_id
    
# ------------------------------------------------------------------------
# PLAYER FUNCTIONS
# ------------------------------------------------------------------------

    def __convert_position_summary_to_list(self, position_summary:str, is_secondary_positions:bool = False) -> list[str]:
        """Transform position summary from Baseball Reference into a list of strings.

        Args:
          position_summary: Original position summary text from bref.
          is_secondary_position: Boolean for parsing primary (pre "/", > 10 games played) vs secondary positions.

        Returns:
          List of strings with all available positions.
        """

        # REMOVE * and H
        position_summary = position_summary.replace('*','').replace('H', '')

        # SPLIT BT / FOR PRIMARY VS SECONDARY
        split_key = '/'
        position_summary_split_list = position_summary.split(split_key, 1)
        if is_secondary_positions and len(position_summary_split_list) < 2:
            return []
        position_summary = position_summary_split_list[1 if is_secondary_positions else 0]

        # SPLIT INTO CHARACTERS
        position_digit_list = [*position_summary]

        # CONVERT TO POSITION NAMES
        position_digit_to_name_map = {
            '1': 'P',
            '2': 'C',
            '3': '1B',
            '4': '2B',
            '5': '3B',
            '6': 'SS',
            '7': 'LF',
            '8': 'CF',
            '9': 'RF',
            'D': 'DH',
            'O': 'OF',
        }
        position_list = [position_digit_to_name_map.get(digit) for digit in position_digit_list]

        return position_list

    def is_out_of_position_for_type(self, type: PlayerType, hitter_bref_ids:list[str]) -> bool:
        """Returns TRUE if the player and type do not match. 
        Used to remove Position Players that have pitching appearances and pitchers with plate appearances.

        Args:
          type: HITTER or PITCHER represented as an Enum.
          hitter_bref_ids: List of hitter bref_ids that have already been parsed in the archive set.

        Returns:
          Boolean for whether to skip player.
        """
        
        if type == PlayerType.HITTER:
            is_pitcher_only_position = self.all_positions == ['P']
            is_pitcher_only_main_position = self.primary_positions == ['P']
            if (is_pitcher_only_position or is_pitcher_only_main_position) and not self.is_two_way:
                return True
        else:
            if self.bref_id in hitter_bref_ids and not self.is_two_way:
                return True
        
        return False
    