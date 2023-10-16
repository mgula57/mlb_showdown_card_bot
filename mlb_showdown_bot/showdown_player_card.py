from posixpath import join
import numpy as np
import math
import requests
import operator
import os
import re
import json
import statistics
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
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from . import showdown_constants as sc
    from .enums.team import Team
    from .enums.icon import Icon
    from .enums.edition import Edition
    from .enums.accolade import Accolade
except ImportError:
    # USE LOCAL IMPORT
    import showdown_constants as sc
    from enums.team import Team
    from enums.icon import Icon
    from enums.edition import Edition
    from enums.accolade import Accolade

class ShowdownPlayerCard:

# ------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------

    def __init__(self, name:str, year:str, stats:dict, context:str, expansion:str='FINAL', edition:str="NONE", offset:int=0, player_image_url:str=None, player_image_path:str=None, card_img_output_folder_path:str='', set_number:str='', test_numbers:tuple[int,int]=None, run_stats:bool=True, command_out_override:tuple[int,int]=None, print_to_cli:bool=False, show_player_card_image:bool=False, is_img_part_of_a_set:bool=False, add_image_border:bool=False, is_dark_mode:bool=False, is_variable_speed_00_01:bool=False, image_parallel:str="NONE", add_year_container:bool=False, set_year_plus_one:bool=False, hide_team_logo:bool=False, date_override:str=None, era:str="DYNAMIC", use_secondary_color:bool=False, is_running_in_flask:bool=False, source:str='Baseball Reference') -> None:
        """Initializer for ShowdownPlayerCard Class"""

        # ASSIGNED ATTRIBUTES
        self.version: str = "3.6"
        self.name: str = stats.get('name', name)
        self.bref_id: str = stats.get('bref_id', '')
        self.bref_url = stats.get('bref_url', '')
        self.year = str(year).upper()
        self.is_full_career: bool = self.year.upper() == "CAREER"
        self.is_multi_year: bool = len(self.year) > 4
        self.year_list: list[int] = self.__convert_year_str_to_list(year=year, all_years_played=stats.get('years_played', []))

        # TYPE OVERRIDE
        self.type_override: str = ''
        for type_str in ['(Pitcher)','(Hitter)']:
            if type_str in name:
                self.type_override = type_str        

        # SET INFO
        self.context: str = context.upper()
        self.context_year: str = '2022' if self.context in sc.CLASSIC_AND_EXPANDED_SETS else context
        self.expansion: str = expansion
        self.era = self.era_dynamic if era == "DYNAMIC" else era
        self.is_expanded: bool = self.context in sc.EXPANDED_SETS
        self.is_classic: bool = self.context in sc.CLASSIC_SETS
        self.has_icons: bool = self.context in sc.SETS_HAS_ICONS

        # STATS
        # ADD OPS IF NOT IN DICT (< 1900 CARDS)
        if 'onbase_plus_slugging' not in stats.keys() and 'slugging_perc' in stats.keys() and 'onbase_perc' in stats.keys():
            stats['onbase_plus_slugging'] = stats['slugging_perc'] + stats['onbase_perc']
        # REDUCE IF/FB FOR 1988
        if 'IF/FB' in stats.keys() and year == '1988':
            stats['IF/FB'] = stats.get('IF/FB', 0.0) * sc.PU_MULTIPLIER_1988
        # COMBINE BB AND HBP
        if 'HBP' in stats.keys():
            try:
                stats['BB'] = stats['BB'] + stats['HBP']
            except:
                print("ERROR COMBINING BB AND HBP")
        self.stats: dict = stats
        self.source: str = source
        self.is_stats_estimate = stats.get('is_stats_estimate', False)
        self.stats_version:int = int(offset)

        # METADATA
        self.is_pitcher: bool = stats.get('type', '') == 'Pitcher'
        self.league: str = stats.get('lg_ID', 'MLB')
        try:
            self.team: Team = Team(stats.get('team_ID', 'MLB'))
        except:
            self.team = Team.MLB
        self.edition: Edition = Edition(edition)
        self.nationality: str = stats.get('nationality', None)
        self.use_secondary_color = use_secondary_color

        # IMAGE
        self.image_parallel: sc.ImageParallel = sc.ImageParallel(image_parallel)
        self.player_image_url: str = player_image_url
        self.player_image_path: str = player_image_path
        self.card_img_output_folder_path: str = card_img_output_folder_path if len(card_img_output_folder_path) > 0 else os.path.join(os.path.dirname(__file__), 'output')
        self.is_automated_image: bool = False
        self.player_image_source: str = None
        self.is_img_part_of_a_set: bool = is_img_part_of_a_set
        self.add_image_border: bool = add_image_border
        self.is_dark_mode: bool = is_dark_mode
        self.img_loading_error: str = None
        self.img_id: str = None
        self.img_bordered_id: str = None
        self.img_dark_id: str = None
        self.img_dark_bordered_id: str = None
        
        # CUSTOMIZATIONS
        default_set_number: str = '—' if self.context in ['2003',sc.EXPANDED_SET, sc.CLASSIC_SET] else year
        self.has_custom_set_number: bool = set_number != ''
        self.set_number: str = set_number if self.has_custom_set_number else default_set_number
        self.add_year_container: bool = add_year_container and self.context in sc.CONTEXTS_ELIGIBLE_FOR_YEAR_CONTAINER
        self.set_year_plus_one: bool = set_year_plus_one and self.context in sc.CONTEXTS_ELIGIBLE_FOR_SET_YEAR_PLUS_ONE
        self.hide_team_logo: bool = hide_team_logo
        self.date_override: str = date_override
        self.test_numbers: tuple[int,int] = test_numbers
        self.command_out_override: tuple[int,int] = command_out_override
        self.is_variable_speed_00_01: bool = is_variable_speed_00_01

        # RANKS
        self.rank: dict = {}
        self.pct_rank: dict = {}
        
        # RUNTIME
        self.is_running_in_flask: bool = is_running_in_flask
        self.load_time: float = None
        
        if run_stats:            

            # POSITIONS_AND_DEFENSE, HAND, IP, SPEED, SPEED_LETTER
            self.__player_metadata(stats=stats)

            # CONVERT STATS TO PER 400 PA
            # MAKES MATH EASIER (20 SIDED DICE)
            stats_for_400_pa = self.__stats_per_n_pa(plate_appearances=400, stats=stats)

            if command_out_override is None:
                command_out_combos = self.__top_accurate_command_out_combos(obp=float(stats['onbase_perc']), num_results=5)
            else:
                # OVERRIDE WILL MANUALLY CHOOSE COMMAND OUTS COMBO (USED FOR TESTING)
                command_out_combos = [command_out_override]

            self.chart, chart_results_per_400_pa = self.__most_accurate_chart(command_out_combos=command_out_combos,
                                                                              stats_per_400_pa=stats_for_400_pa,
                                                                              offset=int(offset))
            self.chart_ranges = self.ranges_for_chart(chart=self.chart,
                                                      dbl_per_400_pa=float(stats_for_400_pa['2b_per_400_pa']),
                                                      trpl_per_400_pa=float(stats_for_400_pa['3b_per_400_pa']),
                                                      hr_per_400_pa=float(stats_for_400_pa['hr_per_400_pa']))
            self.projected = self.projected_statline(stats_per_400_pa=chart_results_per_400_pa, command=self.chart['command'])

            # FOR PTS, USE STEROID ERA OPPONENT
            proj_opponent_chart, proj_my_advantages_per_20, proj_opponent_advantages_per_20 = self.opponent_stats_for_calcs(command=self.chart['command'], era_override=sc.ERA_STEROID)
            projections_for_pts_per_400_pa = self.chart_to_results_per_400_pa(self.chart,proj_my_advantages_per_20,proj_opponent_chart,proj_opponent_advantages_per_20, era_override=sc.ERA_STEROID)
            projections_for_pts = self.projected_statline(stats_per_400_pa=projections_for_pts_per_400_pa, command=self.chart['command'])

            self.points = self.point_value(projected=projections_for_pts,
                                            positions_and_defense=self.positions_and_defense,
                                            speed_or_ip=self.ip if self.is_pitcher else self.speed)

            if show_player_card_image or len(card_img_output_folder_path) > 0:
                self.card_image(show=True if show_player_card_image else False)
            
            if print_to_cli:
                self.print_player()


# ------------------------------------------------------------------------
# STATIC PROPERTIES
# ------------------------------------------------------------------------

    @property
    def player_type(self) -> str:
        """Gets full player type (position_player, starting_pitcher, relief_pitcher).
           Used for applying weights

        Args:
          None

        Returns:
          String for full player type ('position_player', 'tarting_pitcher', 'relief_pitcher').
        """
        # PARSE PLAYER TYPE
        if self.is_pitcher:
            is_starting_pitcher = 'STARTER' in self.positions_and_defense.keys()
            player_category = 'starting_pitcher' if is_starting_pitcher else 'relief_pitcher'
        else:
            player_category = 'position_player'

        return player_category

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
        hitter_hand = "LHH" if self.hand[-1] == "S" else f"{self.hand[-1]}HH"
        hand_prefix = self.hand if self.is_pitcher else hitter_hand
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
    def era_dynamic(self) -> str:
        """Returns the era that best fits the player's season.
        If multi-season, return the era with the most years in it.

        Returns:
            Era name string.
        """

        eras = []
        for year in self.year_list:
            for era, year_range in sc.ERA_YEAR_RANGE.items():
                if year in year_range:
                    eras.append(era)
        
        # FILTER TO MOST
        most_common_era_tuples_list = Counter(eras).most_common(1)

        if len(most_common_era_tuples_list) == 0:
            return sc.ERA_STEROID
        
        return most_common_era_tuples_list[0][0]

    @property
    def special_edition(self) -> sc.SpecialEdition:
        """ Special Editions are cards with unique art and characteristics """

        if self.edition == Edition.ALL_STAR_GAME and str(self.year) == '2023':
            return sc.SpecialEdition.ASG_2023
        
        if self.edition == Edition.SUPER_SEASON and self.context in ['2004','2005',]:
            return sc.SpecialEdition.SUPER_SEASON
        
        if self.edition == Edition.COOPERSTOWN_COLLECTION and self.context in ['2002','2003','2004','2005',]:
            return sc.SpecialEdition.COOPERSTOWN_COLLECTION
        
        if self.image_parallel == sc.ImageParallel.TEAM_COLOR_BLAST and self.is_dark_mode:
            return sc.SpecialEdition.TEAM_COLOR_BLAST_DARK
        
        return sc.SpecialEdition.NONE
    
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
    def positions_and_defense_for_visuals(self) -> dict:
        """ Transform the player's positions_and_defense dictionary for visuals (printing, card image)
        
        Args:
          None

        Returns:
          Dictionary where key is the position, value is the defense at that position
        """

        # NO NEED TO COMBINE IF < 3 POSITIONS
        if self.context in sc.CLASSIC_AND_EXPANDED_SETS or len(self.positions_and_defense) < 3:
            return self.positions_and_defense
        
        positions_to_combine = self.__find_position_combination_opportunity(self.positions_and_defense)
        if positions_to_combine is None:
            return self.positions_and_defense
        positions_to_combine_str =  "/".join(positions_to_combine)
        
        avg_defense = self.positions_and_defense.get(positions_to_combine[0], None)
        if avg_defense is None:
            return self.positions_and_defense
        combined_positions_and_defense = {pos: df for pos, df in self.positions_and_defense.items() if pos not in positions_to_combine}
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
        
        return sorted(self.positions_and_defense_for_visuals.items(), key=lambda p: sc.POSITION_ORDERING.get(p[0],0))
    
    @property
    def template_set_year(self) -> str:
        match self.context:
            case sc.EXPANDED_SET | sc.CLASSIC_SET: return '2022'
            case '2005': return '2004'
            case _: return self.context_year

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
        return self.context in ['2004','2005',sc.CLASSIC_SET,sc.EXPANDED_SET] and not self.edition.use_edition_logo_as_team_logo

    @property
    def team_override_for_images(self) -> Team :
        """ Team override to use for background images and colors (ex: CC)"""
        return Team.CCC if self.edition == Edition.COOPERSTOWN_COLLECTION else None
    
# ------------------------------------------------------------------------
# METADATA METHODS
# ------------------------------------------------------------------------

    def __player_metadata(self, stats:dict) -> None:
        """Parse all metadata (positions, hand, speed, ...) and assign to self.

        Args:
          stats: Dict of stats from Baseball Reference scraper

        Returns:
          None
        """

        # RAW METADATA FROM BASEBALL REFERENCE
        defensive_stats_raw = {k:v for (k,v) in stats.items() if 'Position' in k or 'dWAR' in k or 'outs_above_avg' in k}
        hand_raw = stats['hand']
        innings_pitched_raw = float(stats['IP']) if self.is_pitcher else 0.0
        ip_per_start = (stats['IP/GS'] or 0.0) if 'IP/GS' in stats.keys() else 0.0
        games_played_raw = int(stats['G'])
        games_started_raw = int(stats['GS']) if self.is_pitcher else 0
        saves_raw = int(stats['SV']) if self.is_pitcher else 0
        sprint_speed_raw = stats['sprint_speed'] if 'sprint_speed' in stats.keys() else None
        is_sb_empty = len(str(stats['SB'])) == 0
        stolen_bases_raw = int(0 if is_sb_empty else stats['SB']) if not self.is_pitcher else 0

        # DERIVED SB PER 650 PA (NORMAL SEASON)
        pa_to_650_ratio = int(stats['PA']) / 650.0
        stolen_bases_per_650_pa = stolen_bases_raw / pa_to_650_ratio

        # CALL METHODS AND ASSIGN TO SELF
        self.positions_and_defense = self.__positions_and_defense(defensive_stats=defensive_stats_raw,
                                                                  games_played=games_played_raw,
                                                                  games_started=games_started_raw,
                                                                  saves=saves_raw)
        self.ip = self.__innings_pitched(innings_pitched=innings_pitched_raw, games=games_played_raw, games_started=games_started_raw, ip_per_start=ip_per_start)
        self.hand = self.__handedness(hand=hand_raw)
        self.speed, self.speed_letter = self.__speed(sprint_speed=sprint_speed_raw, stolen_bases=stolen_bases_per_650_pa, is_sb_empty=is_sb_empty)
        self.accolades = self.__accolades()
        self.icons: list[Icon] = self.__icons(awards=stats.get('award_summary',''))

    def __positions_and_defense(self, defensive_stats:dict, games_played:int, games_started:int, saves:int) -> dict:
        """Get in-game defensive positions and ratings

        Args:
          defensive_stats: Dict of games played and total_zone for each position.
          games_played: Number of games played at any position.
          games_started: Number of games started as a pitcher.
          saves: Number of saves. Used to determine what kind of reliever a player is.

        Returns:
          Dict with in game positions and defensive ratings
        """

        # THERE ARE ALWAYS 4 KEYS FOR EACH POSITION
        num_positions = int((len(defensive_stats.keys())-1) / 4)

        # INITIAL DICTS TO STORE POSITIONS AND DEFENSE
        positions_and_defense = {}
        positions_and_games_played = {}
        positions_and_real_life_ratings = {}

        # FLAG IF OF IS AVAILABLE BUT NOT CF (SHOHEI OHTANI 2021 CASE)
        positions_list = [defensive_stats[f'Position{i}'] for i in range(1, num_positions+1)]
        is_of_but_hasnt_played_cf = 'OF' in positions_list and 'CF' not in positions_list

        # POPULATE POSITION DICTS
        # PARSE POSITION NAME, GAMES, AND TZ RATING AND CONVERT TO IN-GAME
        for position_index in range(1, num_positions+1):
            position_raw = defensive_stats['Position{}'.format(position_index)]
            # CHECK IF POSITION MATCHES PLAYER TYPE
            is_valid_position = self.is_pitcher == ('P' == position_raw)
            if is_valid_position:
                games_at_position = int(defensive_stats[f'gPosition{position_index}'])
                position = self.__position_name_in_game(position=position_raw,
                                                        num_positions=num_positions,
                                                        position_appearances=games_at_position,
                                                        games_played=games_played,
                                                        games_started=games_started,
                                                        saves=saves)
                positions_and_games_played[position] = games_at_position
                # IN-GAME RATING AT
                if position is not None:
                    if not self.is_pitcher:
                        try:
                            # FOR MULTI YEAR CARDS THAT SPAN CROSS OVER 2016, IGNORE OAA
                            # CHECK WHAT YEARS THE CARD SPANS OVER
                            start_year = min(self.year_list)
                            end_year = max(self.year_list)
                            use_drs_over_oaa = start_year < 2016 and end_year >= 2016
                            
                            # CHECK WHICH DEFENSIVE METRIC TO USE
                            is_drs_available = f'drsPosition{position_index}' in defensive_stats.keys()
                            is_d_war_available = 'dWAR' in defensive_stats.keys()
                            is_oaa_available = position in defensive_stats['outs_above_avg'].keys() and not use_drs_over_oaa
                            oaa = defensive_stats['outs_above_avg'][position] if is_oaa_available else None
                            # DRS
                            try:
                                if is_drs_available:
                                    drs = int(defensive_stats[f'drsPosition{position_index}']) if defensive_stats[f'drsPosition{position_index}'] != None else None
                                else:
                                    drs = None
                            except:
                                drs = None
                            # TZR
                            try:
                                tzr = int(defensive_stats[f'tzPosition{position_index}']) if defensive_stats[f'tzPosition{position_index}'] != None else None
                            except:
                                tzr = None
                            # DWAR
                            dWar = float(defensive_stats['dWAR']) if is_d_war_available else None
                            
                            if is_oaa_available:
                                metric = 'oaa'
                                defensive_rating = oaa
                            elif drs != None:
                                metric = 'drs'
                                defensive_rating = drs
                            elif tzr != None: 
                                metric = 'tzr'
                                defensive_rating = tzr
                            else:
                                metric = 'dWAR'
                                defensive_rating = dWar
                            positions_and_real_life_ratings[position] = { metric: round(defensive_rating,3) }
                            in_game_defense = self.__convert_to_in_game_defense(position=position,rating=defensive_rating,metric=metric,games=games_at_position)
                        except:
                            in_game_defense = 0
                        positions_and_defense[position] = in_game_defense
                    else:
                        positions_and_defense[position] = 0

        # COMBINE ALIKE IN-GAME POSITIONS (LF/RF, OF, IF, ...)
        final_positions_in_game, final_position_games_played = self.__combine_like_positions(positions_and_defense, positions_and_games_played,is_of_but_hasnt_played_cf=is_of_but_hasnt_played_cf)

        # FILTER TO TOP POSITIONS BY GAMES PLAYED
        final_positions_in_game = self.__filter_to_top_positions(positions_and_defense=final_positions_in_game, positions_and_games_played=final_position_games_played)

        # ASSIGN DH IF POSITIONS DICT IS EMPTY
        if final_positions_in_game == {}:
            final_positions_in_game = {'DH': 0}

        # STORE TO REAL LIFE NUMBERS TO SELF
        self.positions_and_real_life_ratings = positions_and_real_life_ratings

        return final_positions_in_game

    def __combine_like_positions(self, positions_and_defense:dict, positions_and_games_played:dict, is_of_but_hasnt_played_cf=False) -> tuple[dict,dict]:
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
            if self.context in ['2000','2001','2002'] and positions_and_defense['LF/RF'] != positions_and_defense['CF']:
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
        if 'CF' in positions_set and len(positions_and_defense) == 1 and self.context in ['2000','2001']:
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

    def __filter_to_top_positions(self, positions_and_defense:dict, positions_and_games_played:dict) -> dict:
        """ Filter number of positions, find opportunities to combine positions 
        
        Args:
          positions_and_defense: Dict of positions and in-game defensive ratings.
          positions_and_games_played: Dict of positions and number of appearance at each position.

        Returns:
          Dict of positions and defense filtered to max positions.
        """

        # CHECK FOR IF ELIGIBILITY
        if_positions = ['1B','2B','SS','3B']
        is_if_eligible = set(['1B','2B','SS','3B']) == set([pos for pos in positions_and_defense.keys() if pos in if_positions])
        if is_if_eligible:
            # SEE IF TOTAL DEFENSE IS ABOVE REQUIREMENT FOR +1
            total_defense = sum([defense for pos, defense in positions_and_defense.items() if pos in if_positions])
            total_games_played_if = sum([games_played for pos, games_played in positions_and_games_played.items() if pos in if_positions])
            in_game_rating_if = 1 if total_defense >= sc.INFIELD_PLUS_ONE_REQUIREMENT else 0

            # REMOVE OLD POSITIONS
            for position in if_positions:
                positions_and_defense.pop(position, None)
                positions_and_games_played.pop(position, None)

            # ADD IF DEFENSE
            positions_and_defense['IF'] = in_game_rating_if
            positions_and_games_played['IF'] = total_games_played_if

        # LIMIT TO ONLY 2 POSITIONS. CHOOSE BASED ON # OF GAMES PLAYED.
        position_slots = sc.NUM_POSITION_SLOTS[self.context]

        if len(positions_and_defense) <= position_slots:
            # NO NEED TO FILTER, RETURN CURRENT DICT
            return positions_and_defense
        
        sorted_positions = sorted(positions_and_games_played.items(), key=operator.itemgetter(1), reverse=True)[0:3]
        included_positions_list = [pos[0] for pos in sorted_positions]
        final_positions_and_defense = {position: value for position, value in positions_and_defense.items() if position in included_positions_list}

        if self.context not in sc.CLASSIC_AND_EXPANDED_SETS and len(final_positions_and_defense) > 2:
            positions_to_merge = self.__find_position_combination_opportunity(final_positions_and_defense)
            if positions_to_merge is None:
                # NOTHING CAN BE COMBINED, REMOVE LAST POSITION
                final_positions_and_defense.pop(included_positions_list[-1], None)
            else:
                # AVERAGE DEFENSE FOR POSITIONS THAT WILL BE COMBINED
                avg_defense = int(round(statistics.mean([defense for pos, defense in final_positions_and_defense.items() if pos in positions_to_merge])))
                for pos in positions_to_merge:
                    final_positions_and_defense[pos] = avg_defense

        return final_positions_and_defense

    def __find_position_combination_opportunity(self, positions_and_defense:dict) -> list[str]:
        """ From dictionary of player with > 2 positions, see if there is an opportunity to combine positions together.

        If no combination opportunies exist, return None.

        Args:
          positions_and_defense: Dict of positions and in-game defensive ratings.

        Returns:
          List of positions that will be combined into one.
        """

        # CREATE DICTIONARY OF POSITIONS ABLE TO BE COMBINED + DIFFERENCE IN DEFENSE
        positions_able_to_be_combined = {}
        position_list = list(positions_and_defense.keys())
        for position, defense in positions_and_defense.items():
            combinations_list_for_pos = sc.POSITIONS_ALLOWED_COMBINATIONS.get(position,[])
            combinations_available_for_player = {p: abs(defense - positions_and_defense.get(p, 0)) for p in position_list if p != position and p in combinations_list_for_pos}
            if len(combinations_available_for_player) > 0:
                sorted_combinations = sorted(combinations_available_for_player.items(), key=lambda x: x[1])
                positions_able_to_be_combined[position] = sorted_combinations[0]

        # SELECT ONE POSITION TO CHANGE
        # FIRST SORT BASED ON DIFFERENCE IN DEFENSE, THEN BY POSITION'S ORDERING
        sorted_positions = sorted(positions_able_to_be_combined.items(), key=lambda x: (x[1][1], -sc.POSITION_ORDERING.get(x[1], 0)))
        if len(sorted_positions) == 0:
            return None
        
        top_combo = sorted_positions[0]
        position1 = top_combo[0]
        position2 = top_combo[1][0]
        difference = top_combo[1][1]

        # ONLY RETURN COMBINATION IF DIFFERENCE IS < 3
        if difference > 2:
            return None
        else:
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

        if position == 'P' and self.is_pitcher:
            # PITCHER IS EITHER STARTER, RELIEVER, OR CLOSER
            gsRatio = games_started / games_played
            if gsRatio > sc.STARTING_PITCHER_PCT_GAMES_STARTED:
                # ASSIGN MINIMUM IP FOR STARTERS
                return 'STARTER'
            if saves > sc.CLOSER_MIN_SAVES_REQUIRED:
                return 'CLOSER'
            else:
                return 'RELIEVER'
        elif ( position_appearances < sc.NUMBER_OF_GAMES_DEFENSE and (position_appearances / games_played < sc.PCT_OF_GAMES_DEFENSE) ) or (self.is_multi_year and ( (position_appearances / games_played) < sc.PCT_OF_GAMES_DEFENSE_MULTI_YEAR )):
            # IF POSIITION DOES NOT MEET REQUIREMENT, RETURN NONE
            return None
        elif position == 'DH' and num_positions > 1:
            # PLAYER MAY HAVE PLAYED AT DH, BUT HAS OTHER POSITIONS, SO DH WONT BE LISTED
            return None
        elif self.context not in ['2000', '2001'] and position == 'C':
            # CHANGE CATCHER POSITION NAME DEPENDING ON CONTEXT YEAR
            return 'CA'
        else:
            # RETURN BASEBALL REFERENCE STRING VALUE
            return position

    def __convert_to_in_game_defense(self, position:str, rating:float, metric:str, games:int) -> int:
        """Converts the best available fielding metric to in game defense at a position.
           Uses DRS for 2003+, TZR for 1953-2002, dWAR for <1953.
           More modern defensive metrics (like DRS) are not available for historical
           seasons.

        Args:
          position: In game position name.
          rating: Total Zone Rating or dWAR. 0 is average for a position.
          metric: String name of metric used for calculations (drs,tzr,dWAR)
          games: Games played at position.

        Returns:
          In game defensive rating.
        """
        MIN_SABER_FIELDING = sc.MIN_SABER_FIELDING[metric]
        MAX_SABER_FIELDING = sc.MAX_SABER_FIELDING[metric]
        # IF USING OUTS ABOVE AVG, CALCULATE RATING PER 162 GAMES
        is_using_oaa = metric == 'oaa'
        is_1b = position.upper() == '1B'
        if is_using_oaa:
            rating = rating / games * 162.0
            # FOR OUTS ABOVE AVG OUTLIERS, SLIGHTLY DISCOUNT DEFENSE OVER THE MAX
            # EX: NICK AHMED 2018 - 38.45 OAA per 162
            #   - OAA FOR +5 = 16
            #   - OAA OVER MAX = 38.45 - 16 = 22.45
            #   - REDUCED OVER MAX = 22.45 * 0.5 = 11.23
            #   - NEW RATING = 16 + 11.23 = 26.23            
            if rating > MAX_SABER_FIELDING and not is_1b:
                amount_over_max = rating - MAX_SABER_FIELDING
                reduced_amount_over_max = amount_over_max * sc.OAA_OVER_MAX_MULTIPLIER
                rating = reduced_amount_over_max + MAX_SABER_FIELDING

        max_defense_for_position = sc.POSITION_DEFENSE_RANGE[self.context][position]
        defensive_range = MAX_SABER_FIELDING - MIN_SABER_FIELDING
        percentile = (rating-MIN_SABER_FIELDING) / defensive_range
        defense_raw = percentile * max_defense_for_position
        defense = round(defense_raw) if defense_raw > 0 or self.context in sc.CLASSIC_AND_EXPANDED_SETS else 0
        
        # FOR NEGATIVES, CAP DEFENSE AT -2
        defense = -2 if self.context in sc.CLASSIC_AND_EXPANDED_SETS and defense < -2 else defense

        # ADD IN STATIC METRICS FOR 1B
        if is_1b:
            if rating > sc.FIRST_BASE_PLUS_2_CUTOFF[metric]:
                defense = 2
            elif rating > sc.FIRST_BASE_PLUS_1_CUTOFF[metric]:
                defense = 1
            elif rating < sc.FIRST_BASE_MINUS_1_CUTOFF[metric] and self.context in sc.CLASSIC_AND_EXPANDED_SETS:
                defense = -1
            else:
                defense = 0
        
        # CAP DEFENSE IF GAMES PLAYED AT POSITION IS LESS THAN 80
        defense_over_the_max = defense > max_defense_for_position
        defense = int(max_defense_for_position) if games < 100 and defense_over_the_max else defense

        # CAP DEFENSE AT +0 IF IN NEGATIVES AND GAMES PLAYED IS UNDER 0 (CLASSIC/EXPANDED SETS)
        defense = 0 if defense < 0 and games < 50 else defense

        return defense

    def __handedness(self, hand:str) -> str:
        """Get hand of player. Format to how card will display hand.

        Args:
          hand: Hand string from Baseball Reference. Will be "Left", "Right", or "Both".

        Returns:
          Formatted hand string (ex: "Bats R" or "RHP").
        """

        hand_first_letter = hand[0:1] if hand != 'Both' else 'S'
        hand_formatted_for_position = '{}HP'.format(hand_first_letter) if self.is_pitcher else 'Bats {}'.format(hand_first_letter)

        return hand_formatted_for_position

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
        type = self.player_type
        is_reliever = type == 'relief_pitcher'
        if is_reliever:
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

    def __speed(self, sprint_speed:float, stolen_bases:int, is_sb_empty:bool) -> tuple[int, str]:
        """In game speed for a position player. Will use pure sprint speed
           if year is >= 2015, otherwise uses stolen bases. Pitcher defaults to 10.

        Args:
          sprint_speed: Average sprint speed according to baseballsavant.com.
                        IMPORTANT: Data is available for 2015+.
          stolen_bases: Number of steals during the season.
          is_sb_empty: Bool for whether SB are unavailable for the player.

        Returns:
          Tuple with in game speed ability, in game letter grade
        """

        if self.is_pitcher:
            # PITCHER DEFAULTS TO 10
            return 10, 'C'
    
        if is_sb_empty:
            # DEFAULT PLAYERS WITHOUT SB AVAILABLE TO 12
            return 12, 'C' if self.context == '2002' else 'B'

        # IF FULL CAREER CARD, ONLY USE SPRINT SPEED IF PLAYER HAS OVER 35% of CAREER POST 2015
        pct_career_post_2015 = sum([1 if year >= 2015 else 0 for year in self.year_list]) / len(self.year_list)
        is_disqualied_career_speed = self.is_multi_year and pct_career_post_2015 < 0.35

        # DEFINE METRICS USED TO DETERMINE IN-GAME SPEED
        disable_sprint_speed = sprint_speed is None or math.isnan(sprint_speed) or sprint_speed == '' or sprint_speed == 0 or is_disqualied_career_speed
        speed_elements = {sc.STOLEN_BASES_KEY: stolen_bases} 
        if not disable_sprint_speed:
            speed_elements.update( {sc.SPRINT_SPEED_KEY: sprint_speed} )

        in_game_speed_for_metric = {}
        for metric, value in speed_elements.items():
            metric_max = sc.SPEED_METRIC_MAX[metric]
            metric_min = sc.SPEED_METRIC_MIN[metric]
            ignore_multiplier = self.context in ['2000', '2001'] and self.is_variable_speed_00_01
            metric_multiplier = 1.05 if ignore_multiplier else sc.SPEED_METRIC_MULTIPLIER[metric][self.context]
            era_multiplier = sc.SPEED_ERA_MULTIPLIER[self.era]
            top_percentile_speed_for_metric = sc.SPEED_METRIC_TOP_PERCENTILE[metric]

            speed_percentile = era_multiplier * metric_multiplier * (value-metric_min) / (metric_max - metric_min)
            speed = int(round(speed_percentile * top_percentile_speed_for_metric))

            # CHANGE OUTLIERS
            min_in_game = sc.MIN_IN_GAME_SPD[self.context]
            max_in_game = sc.MAX_IN_GAME_SPD[self.context]

            cutoff_for_sub_percentile_sb = 20
            if metric == sc.STOLEN_BASES_KEY and speed > cutoff_for_sub_percentile_sb:
                sb_cap = sc.STOLEN_BASES_PER_650_PA_THRESHOLD_MAX[self.context] * metric_multiplier
                sub_percentile = (value - metric_max) / (sb_cap - metric_max)
                remaining_slots_over_cutoff = max_in_game - cutoff_for_sub_percentile_sb
                additional_speed_over_cutoff = sub_percentile * remaining_slots_over_cutoff
                speed = int(additional_speed_over_cutoff + cutoff_for_sub_percentile_sb)
            
            final_speed_for_metric = min( max(speed, min_in_game), max_in_game )

            in_game_speed_for_metric[metric] = final_speed_for_metric

        # AVERAGE SPRINT SPEED WITH SB SPEED
        num_metrics = len(in_game_speed_for_metric)
        metric_weights = sc.SPEED_METRIC_WEIGHT
        sb_speed = in_game_speed_for_metric.get(sc.STOLEN_BASES_KEY, 0)
        ss_speed = in_game_speed_for_metric.get(sc.SPRINT_SPEED_KEY, 0)
        if num_metrics > 1 and sb_speed > sc.SB_OUTLIER_SPEED_CUTOFF and sb_speed > ss_speed:
            # CHANGE WEIGHTS TO EMPHASIZE STOLEN BASES OVER SPRINT SPEED
            metric_weights = sc.SPEED_METRIC_WEIGHT_SB_OUTLIERS
        
        final_speed = int(round( sum([(metric_weights.get(metric, 1.0) if num_metrics > 1 else 1.0) * in_game_spd for metric, in_game_spd in in_game_speed_for_metric.items() ]) ))

        if final_speed < sc.SPEED_C_CUTOFF[self.context]:
            letter = 'C'
        elif final_speed < 18:
            letter = 'B'
        else:
            letter = 'A'

        # IF 2000 OR 2001, SPEED VALUES CAN ONLY BE 10,15,20
        if self.context in ['2000', '2001'] and not self.is_variable_speed_00_01:
            spd_letter_to_number = {'A': 20,'B': 15,'C': 10}
            final_speed = spd_letter_to_number[letter]

        return final_speed, letter

    def __icons(self, awards:str) -> list[Icon]:
        """Converts awards_summary and other metadata fields into in game icons.

        Args:
          awards: String containing list of seasonal accolades.

        Returns:
          List of in game icons as strings.
        """

        # ICONS ONLY APPLY TO 2003+
        if not self.has_icons:
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


        # IF PITCHER AND MORE THAN 4 ICONS (EX: BOB GIBSON 1968), FILTER OUT A G
        if len(icons) >= 5 and self.is_pitcher and Icon.G in icons:
            icons.remove(Icon.G)

        return icons

    def __accolades(self, maximum:int = None) -> list[str]:
        """Generates array of player highlights for season.

        Args:
          maximum: Maximum accolades to include.

        Returns:
          Array with 3 string elements showing accolades for season
        """

        # HELPER ATTRIBUTES 
        num_seasons = len(self.year_list)
        is_pre_2004 = self.context in ['2000','2001','2002','2003']
        is_icons = self.context not in ['2000','2001','2002',]
        ba_champ_text = 'BATTING TITLE'
        is_starting_pitcher = 'STARTER' in self.positions_and_defense.keys()

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
        length_req = sc.SUPER_SEASON_PRE_04_TEXT_LENGTH if is_pre_2004 else sc.SUPER_SEASON_04_05_MIN_TEXT_LENGTH
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

    def __convert_year_str_to_list(self, year:str, all_years_played:list[str]) -> list[int]:
        """Convert user input year string to a list of year integers.

        Ex: "2020-2022" -> [2020, 2021, 2022]
        
        Args:
          year: Year string input by the user.
          all_years_played: List of all years played by the player. Used if year input is CAREER.

        Returns:
          List of years converted to integers.
        """

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
        command_out_combos = sc.CONTROL_COMBOS[self.context] if self.is_pitcher else sc.OB_COMBOS[self.context]

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

    def __onbase_control_outs(self, command:int=0, outs:int=0, era_override:str = None) -> dict[str, int]:
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
        onbase_baseline = sc.BASELINE_HITTER[self.context][era]['command'] if self.test_numbers is None else self.test_numbers[0]
        hitter_outs_baseline = sc.BASELINE_HITTER[self.context][era]['outs'] if self.test_numbers is None else self.test_numbers[1]
        control_baseline = sc.BASELINE_PITCHER[self.context][era]['command'] if self.test_numbers is None else self.test_numbers[0]
        pitcher_outs_baseline = sc.BASELINE_PITCHER[self.context][era]['outs'] if self.test_numbers is None else self.test_numbers[1]

        return {
            'onbase': command if not self.is_pitcher else onbase_baseline,
            'hitterOuts': outs if not self.is_pitcher else hitter_outs_baseline,
            'control': command if self.is_pitcher else control_baseline,
            'pitcherOuts': outs if self.is_pitcher else pitcher_outs_baseline
        }

    def opponent_stats_for_calcs(self, command:int, era_override:str = None) -> tuple[dict[str, float], float, float]:
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
            opponent_chart = sc.BASELINE_PITCHER[self.context][era]
            my_advantages_per_20 = command-self.__onbase_control_outs(era_override=era_override)['control']
            opponent_advantages_per_20 = 20 - my_advantages_per_20
        else:
            opponent_chart = sc.BASELINE_HITTER[self.context][era]
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

    @property
    def chart_categories(self) -> list[str]:
        """List of all chart categories depending on player type.

        Note: 2000 set pitchers starts with SO instead PU.

        Args:
          None

        Returns:
          List of chart categories lowercased.
        """

        if self.is_pitcher:
            # 2000 HAS 'SO' FIRST, ALL OTHER YEARS HAVE 'PU' FIRST
            firstCategory = 'so' if self.context == '2000' else 'pu'
            secondCategory = 'pu' if self.context == '2000' else 'so'
            categories = [firstCategory,secondCategory,'gb','fb','bb','1b','2b','hr']
        else:
            # HITTER CATEGORIES
            categories = ['so','gb','fb','bb','1b','1b+','2b','3b','hr']

        return categories

    def __most_accurate_chart(self, command_out_combos: list[tuple[int, int]], stats_per_400_pa:dict, offset:int) -> tuple[dict, dict]:
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
        self.top_command_out_combinations = [(ca[0],round(ca[2],4)) for ca in chart_and_accuracies]
        projected_stats_for_best_chart = chart_and_accuracies[offset][3]

        return best_chart, projected_stats_for_best_chart

    def __chart_with_accuracy(self, command:int, outs:int, stats_for_400_pa:dict, era_override:str = None) -> tuple[dict[str, int], float, dict]:
        """Create Player's chart and compare back to input stats.

        Args:
          command: Onbase (Hitter) or Control (Pitcher) of the Player.
          outs: Number of Outs on the Player's chart.
          stats_per_400_pa: Dict with number of results for a given
                            category per 400 PA (ex: {'hr_per_400_pa': 23.65})
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          - Dictionary for Player Chart ({'so': 1, 'hr': 2, ...})
          - Accuracy of chart compared to original input.
          - Dict of Player's chart converted to real stat output.
        """

        # NEED THE OPPONENT'S CHART TO CALCULATE NUM OF RESULTS FOR RESULT
        opponent_chart, my_advantages_per_20, opponent_advantages_per_20 = self.opponent_stats_for_calcs(command=command, era_override=era_override)

        # CREATE THE CHART DICTIONARY
        chart = {
            'command': command,
            'outs': outs
        }

        for category, results_per_400_pa in stats_for_400_pa.items():
            if '_per_400_pa' in category and category != 'h_per_400_pa':

                # CONVERT EACH REAL STAT CATEGORY INTO NUMBER OF RESULTS ON CHART
                key = category[:2]
                if key == 'sb':
                    # STOLEN BASES HAS NO OPPONENT RESULTS
                    chart_results = results_per_400_pa / stats_for_400_pa['pct_of_400_pa']
                else:
                    # CALCULATE NUM OF RESULTS
                    chart_results = (results_per_400_pa - (opponent_advantages_per_20*opponent_chart[key])) / my_advantages_per_20

                if key == 'so':
                    chart_results = self.__so_results(current_so=chart_results, num_out_slots=outs)
                
                # HANDLE CASE OF < 0
                chart_results = chart_results if chart_results > 0 else 0

                # WE ROUND THE PREDICTED RESULTS (2.4 -> 2, 2.5 -> 3)
                if self.is_pitcher and key == 'hr' and chart_results < 1.0:
                    # TRADITIONAL ROUNDING CAUSES TOO MANY PITCHER HR RESULTS
                    chart_results_decimal = chart_results % 1
                    era = era_override if era_override else self.era
                    rounded_results = round(chart_results) if chart_results_decimal > sc.HR_ROUNDING_CUTOFF[self.context][era] else math.floor(chart_results)
                else:                    
                    rounded_results = round(chart_results)
                # PITCHERS SHOULD ALWAYS GET 0 FOR 3B
                rounded_results = 0 if self.is_pitcher and key == '3b' else rounded_results
                # CHECK FOR BARRY BONDS EFFECT (HUGE WALK)
                rounded_results = 12 if key == 'bb' and rounded_results > 13 else rounded_results
                # MAX HR RESULTS AT 10
                rounded_results = 10 if key == 'hr' and rounded_results > 10 else rounded_results
                # MAX 2B RESULTS AT 12
                rounded_results = 12 if key == '2b' and rounded_results > 12 else rounded_results
                chart[key] = rounded_results

        # FILL "OUT" CATEGORIES (PU, GB, FB)
        out_slots_remaining = outs - float(chart['so'])
        chart['pu'], chart['gb'], chart['fb'] = self.__out_results(
                                                    gb_pct=stats_for_400_pa.get('GO/AO', None),
                                                    popup_pct=stats_for_400_pa.get('IF/FB', None),
                                                    out_slots_remaining=out_slots_remaining,
                                                    slg=stats_for_400_pa.get('slugging_perc', None),
                                                    era_override=era_override
                                                )
        # CALCULATE HOW MANY SPOTS ARE LEFT TO FILL 1B AND 1B+
        remaining_slots = 20
        for category, results in chart.items():
            # IGNORE NON RESULT KEYS (EXCEPT 1B, WHICH WE WANT TO FILL OURSELVES)
            if category not in ['command','outs','sb','1b']:
                remaining_slots -= int(results)

        # QA BARRY BONDS EFFECT (HUGE WALK)
        if remaining_slots < 0:
            walk_results = chart['bb']
            if walk_results >= abs(remaining_slots):
                chart['bb'] = walk_results - abs(remaining_slots)
                remaining_slots += abs(remaining_slots)
        remaining_slots_qa = 0 if remaining_slots < 0 else remaining_slots

        # FILL 1B AND 1B+
        stolen_bases = int(stats_for_400_pa['sb_per_400_pa'])
        chart['1b'], chart['1b+'] = self.__single_and_single_plus_results(remaining_slots_qa,stolen_bases,command)
        # CHECK ACCURACY COMPARED TO REAL LIFE
        in_game_stats_for_400_pa = self.chart_to_results_per_400_pa(chart,my_advantages_per_20,opponent_chart,opponent_advantages_per_20, era_override=era_override)
        weights = sc.CHART_CATEGORY_WEIGHTS[self.context][self.player_type]
        accuracy, categorical_accuracy, above_below = self.accuracy_between_dicts(actuals_dict=stats_for_400_pa,
                                                                                  measurements_dict=in_game_stats_for_400_pa,
                                                                                  weights=weights,
                                                                                  only_use_weight_keys=True)
        
        # QA: CHANGE ACCURACY TO 0 IF CHART DOESN'T ADD UP TO 20
        is_over_20 = sum([v for k, v in chart.items() if k not in ['command','outs', 'sb'] ]) > 20
        accuracy = 0.0 if is_over_20 else accuracy

        # ADD WEIGHTING OF ACCURACY
        # LIMITS AMOUNT OF RESULTS PER SET FOR CERTAIN COMMAND/OUT COMBINATIONS
        weight = sc.COMMAND_ACCURACY_WEIGHTING[self.context].get(f"{command}-{outs}", 1.0)
        accuracy = accuracy * weight

        return chart, accuracy, in_game_stats_for_400_pa

    def __out_results(self, gb_pct:float, popup_pct:float, out_slots_remaining:int, slg:float, era_override:str = None) -> tuple[int, int, int]:
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
            slg_percentile = self.stat_percentile(stat=slg, min_max_dict={'min': 0.250, 'max': 0.500})
            multiplier = 1.0 if slg_percentile < 0 else 1.0 - slg_percentile
            gb_pct = gb_pct if gb_pct else round(1.5 * max(multiplier, 0.5),3)
            popup_pct = popup_pct if popup_pct else round(0.16 * max(multiplier, 0.5),3)

        era = era_override if era_override else self.era
        if out_slots_remaining > 0:
            # MULTIPLIERS SERVE TO CORRECT TOWARDS WOTC
            # REPLACE HAVING DEFAULT FOR OPPONENT CHART
            type = 'pitcher' if self.is_pitcher else 'hitter'
            gb_multi = sc.GB_MULTIPLIER[type][self.context][era]
            # SPLIT UP REMAINING SLOTS BETWEEN GROUND AND AIR OUTS
            gb_outs = int(round((out_slots_remaining / (gb_pct + 1)) * gb_pct * gb_multi))
            air_outs = out_slots_remaining - gb_outs
            # FOR PU, ADD A MULTIPLIER TO ALIGN MORE WITH OLD SCHOOL CARDS
            pu_multiplier = sc.PU_MULTIPLIER[self.context]
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
        hard_limit_hitter = min(num_out_slots, sc.HITTER_SO_RESULTS_HARD_CAP.get(self.context, 6))
        soft_limit_hitter = sc.HITTER_SO_RESULTS_SOFT_CAP.get(self.context, 3)
        
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
        min_onbase = 4 if self.is_classic else 7
        max_onbase = 12 if self.is_classic else 16
        ob_min_max_dict = {'min': min_onbase, 'max': max_onbase}
        min_denominator = sc.HITTER_SINGLE_PLUS_DENOMINATOR_RANGE[self.context]['min']
        max_denominator = sc.HITTER_SINGLE_PLUS_DENOMINATOR_RANGE[self.context]['max']
        onbase_pctile = self.stat_percentile(stat=command, min_max_dict=ob_min_max_dict)
        single_plus_denominator = min_denominator + ( (max_denominator-min_denominator) * onbase_pctile )
        single_plus_results_raw = math.trunc(sb / single_plus_denominator)

        # MAKE SURE 1B+ IS NOT OVER REMAINING SLOTS
        single_plus_results = single_plus_results_raw if single_plus_results_raw <= remaining_slots else remaining_slots
        single_results = remaining_slots - single_plus_results

        return single_results, single_plus_results

    def ranges_for_chart(self, chart: dict[str, int], dbl_per_400_pa:float, trpl_per_400_pa:float, hr_per_400_pa:float) -> dict[str, str]:
        """Converts chart integers to Range Strings ({1B: 3} -> {'1B': '11-13'})

        Args:
          chart: Dict with # of slots per chart result category
          dbl_per_400_pa: Number of 2B results every 400 PA
          trpl_per_400_pa: Number of 3B results every 400 PA
          hr_per_400_pa: Number of HR results every 400 PA

        Returns:
          Dict of ranges for each result category.
        """

        current_chart_index = 1
        chart_ranges: dict[str, str] = {}
        for category in self.chart_categories:
            category_results = int(chart[category])
            range_end = current_chart_index + category_results - 1

            # HANDLE RANGES > 20
            if self.is_expanded and range_end >= 20 and self.is_pitcher:
                add_to_1b, num_of_results_2b = self.__calculate_ranges_over_20(dbl_per_400_pa, hr_per_400_pa)
                # DEFINE OVER 20 RANGES
                if category == '1b':
                    category_results += add_to_1b
                    range_end = current_chart_index + category_results - 1
                elif category == '2b':
                    category_results += num_of_results_2b
                    range_end = current_chart_index + category_results - 1
            
            # HANDLE ERRORS WITH SMALL SAMPLE SIZE 2000/2001 FOR SMALL ONBASE
            if not self.is_expanded and range_end > 20:
                range_end = 20
                
            if category.upper() == 'HR' and self.is_expanded:
                # ADD PLUS AFTER HR
                range = '{}+'.format(str(current_chart_index))
            elif category_results == 0:
                # EMPTY RANGE
                range = '—'
            elif category_results == 1:
                # RANGE IS CURRENT INDEX
                range = str(current_chart_index)
                current_chart_index += 1
            else:
                # MULTIPLE RESULTS
                range_start = current_chart_index
                range = '{}–{}'.format(range_start,range_end)
                current_chart_index = range_end + 1

            chart_ranges['{} Range'.format(category)] = range

        # FILL IN ABOVE 20 RESULTS IF APPLICABLE
        if self.is_expanded and int(chart['hr']) < 1 and not self.is_pitcher:
            chart_ranges = self.__hitter_chart_above_20(chart, chart_ranges, dbl_per_400_pa, trpl_per_400_pa, hr_per_400_pa)

        return chart_ranges

    def __calculate_ranges_over_20(self, dbl_per_400_pa:float, hr_per_400_pa:float) -> tuple[int, int]:
        """Calculates starting points of 2B and HR ranges for post 2001 cards
           whose charts expand past 20.

        Args:
          dbl_per_400_pa: Number of 2B results every 400 PA
          hr_per_400_pa: Number of HR results every 400 PA

        Returns:
          Tuple of 1b_additions, 2b results
        """
        # TODO: MAKE THIS LESS STATIC

        # HR
        if hr_per_400_pa >= 13:
            hr_start = 21
        elif hr_per_400_pa >= 11:
            hr_start = 22
        elif hr_per_400_pa >= 8.5:
            hr_start = 23
        elif hr_per_400_pa >= 7.0:
            hr_start = 24
        elif hr_per_400_pa >= 5.0:
            hr_start = 25
        elif hr_per_400_pa >= 3.0:
            hr_start = 26
        else:
            hr_start = 27

        # 2B
        if dbl_per_400_pa >= 13:
            dbl_start = 21
        elif dbl_per_400_pa >= 9.0:
            dbl_start = 22
        elif dbl_per_400_pa >= 5.5:
            dbl_start = 23
        else:
            dbl_start = 24

        add_to_1b = dbl_start - 20
        hr_start_final = hr_start if dbl_start < hr_start else dbl_start + 1
        num_of_results_2b = hr_start_final - dbl_start

        return add_to_1b, num_of_results_2b

    def __hitter_chart_above_20(self, chart:dict[str, int], chart_ranges:dict[str, str], dbl_per_400_pa:float, trpl_per_400_pa:float, hr_per_400_pa:float) -> dict[str, str]:
        """If a hitter has remaining result categories above 20, populate them.
        Only for sets > 2001.

        Args:
            chart: Dict with # of slots per chart result category
            chart_ranges: Dict with visual representation of range per result category
            dbl_per_400_pa: Number of 2B results every 400 PA
            trpl_per_400_pa: Number of 3B results every 400 PA
            hr_per_400_pa: Number of HR results every 400 PA

        Returns:
            Dict of ranges for each result category.
        """
        # VALIDATE THAT CHART HAS VALUES ABOVE 20
        if int(chart['hr']) > 0:
            return chart_ranges

        # STATIC THRESHOLDS FOR END HR #
        # THIS COULD BE MORE PROBABILITY BASED, BUT SEEMS LIKE ORIGINAL SETS USED STATIC METHODOLOGY
        # NOTE: 2002 HAS MORE EXTREME RANGES
        is_2002 = self.context == '2002'
        threshold_adjustment = 0 if is_2002 else -3
        if hr_per_400_pa < 1.0:
            hr_end = 27
        elif hr_per_400_pa < 2.5 and is_2002: # RESTRICT TO 2002
            hr_end = 26
        elif hr_per_400_pa < 3.75 and is_2002: # RESTRICT TO 2002
            hr_end = 25
        elif hr_per_400_pa < 4.75 + threshold_adjustment:
            hr_end = 24
        elif hr_per_400_pa < 6.25 + threshold_adjustment:
            hr_end = 23
        elif hr_per_400_pa < 7.5 + threshold_adjustment:
            hr_end = 22
        else:
            hr_end = 21
        chart_ranges['hr Range'] = '{}+'.format(hr_end)

        # SPLIT REMAINING OVER 20 SPACES BETWEEN 1B, 2B, AND 3B
        remaining_slots = hr_end - 21
        is_remaining_slots = remaining_slots > 0
        is_last_under_20_result_3b = int(chart['3b']) > 0
        is_last_under_20_result_2b = not is_last_under_20_result_3b and int(chart['2b'] > 0)

        if is_remaining_slots:
            # FILL WITH 3B
            if is_last_under_20_result_3b:
                current_range_start = chart_ranges['3b Range'][0:2]
                new_range_end = hr_end - 1
                range_updated = '{}–{}'.format(current_range_start,new_range_end)
                chart_ranges['3b Range'] = range_updated
            # FILL WITH 2B (AND POSSIBLY 3B)
            elif is_last_under_20_result_2b:
                new_range_end = hr_end - 1
                if trpl_per_400_pa >= 3.5:
                    # GIVE TRIPLE 21-HR
                    triple_range = '21' if remaining_slots == 1 else '21-{}'.format(new_range_end)
                    chart_ranges['3b Range'] = triple_range
                else:
                    # GIVE 2B-HR
                    current_range_start = chart_ranges['2b Range'][0:2]
                    range_updated = '{}–{}'.format(current_range_start,new_range_end)
                    chart_ranges['2b Range'] = range_updated
            # FILL WITH 1B (AND POSSIBLY 2B AND 3B)
            else:
                new_range_end = hr_end - 1
                if trpl_per_400_pa + dbl_per_400_pa == 0:
                    # FILL WITH 1B
                    category_1b = '1b+ Range' if chart['1b+'] > 0 else '1b Range'
                    current_range_start = chart_ranges[category_1b][0:2]
                    # CHECK FOR IF SOMEHOW PLAYER HAS 0 1B TOO
                    if current_range_start == '—':
                        current_range_start = '21'
                    range_updated = '{}–{}'.format(current_range_start,new_range_end)
                    chart_ranges[category_1b] = range_updated
                else:
                    # SPLIT BETWEEN 2B AND 3B
                    dbl_pct = dbl_per_400_pa / (trpl_per_400_pa + dbl_per_400_pa)
                    dbl_slots = int(round((remaining_slots * dbl_pct)))
                    trpl_slots = remaining_slots - dbl_slots

                    # FILL 2B
                    dbl_range = '21' if dbl_slots == 1 else '21-{}'.format(20 + dbl_slots)
                    dbl_range = '—' if dbl_slots == 0 else dbl_range
                    chart_ranges['2b Range'] = dbl_range

                    # FILL 3B
                    trpl_start = 21 + dbl_slots
                    trpl_range = str(trpl_start) if trpl_slots == 1 else '{}-{}'.format(trpl_start, trpl_start + trpl_slots - 1)
                    trpl_range = '—' if trpl_slots == 0 else trpl_range
                    chart_ranges['3b Range'] = trpl_range
        return chart_ranges


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
        sh = float(stats['SH'] if stats['SH'] != '' else 0)
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

    def chart_to_results_per_400_pa(self, chart:dict[str, int], my_advantages_per_20:float, opponent_chart:dict[str, float], opponent_advantages_per_20:float, era_override:str = None) -> dict:
        """Predict real stats given Showdown in game chart.

        Args:
          chart: Dict for chart of Player.
          my_advantages_per_20: Number of advantages my Player gets out of 20 (i.e. 5). Can be a float.
          opponent_chart: Dict for chart of baseline opponent.
          opponent_advantages_per_20: Number of advantages opponent gets out of 20 (i.e. 15). Can be a float.
          era_override: Optionally override the era used for baseline opponents.

        Returns:
          Dict with stats per 400 Plate Appearances.
        """

        # MATCHUP VALUES
        command_out_matchup = self.__onbase_control_outs(chart['command'],chart['outs'],era_override=era_override)
        pitcher_chart = chart if self.is_pitcher else opponent_chart
        hitter_chart = chart if not self.is_pitcher else opponent_chart
        hits_pitcher_chart = pitcher_chart['1b'] + pitcher_chart['2b'] \
                             + pitcher_chart['3b'] + pitcher_chart['hr']
        hits_hitter_chart = hitter_chart['1b'] + hitter_chart['1b+'] + hitter_chart['2b'] \
                            + hitter_chart['3b'] + hitter_chart['hr']

        strikeouts_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart['so'],
                                                                    opponent_results=opponent_chart['so'],
                                                                    my_advantages_per_20=my_advantages_per_20,
                                                                    opponent_advantages_per_20=opponent_advantages_per_20)
        walks_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart['bb'],
                                                               opponent_results=opponent_chart['bb'],
                                                               my_advantages_per_20=my_advantages_per_20,
                                                               opponent_advantages_per_20=opponent_advantages_per_20)
        singles_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart['1b']+chart['1b+'],
                                                                 opponent_results=opponent_chart['1b'],
                                                                 my_advantages_per_20=my_advantages_per_20,
                                                                 opponent_advantages_per_20=opponent_advantages_per_20)
        doubles_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart['2b'],
                                                                 opponent_results=opponent_chart['2b'],
                                                                 my_advantages_per_20=my_advantages_per_20,
                                                                 opponent_advantages_per_20=opponent_advantages_per_20)
        triples_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart['3b'],
                                                                 opponent_results=opponent_chart['3b'],
                                                                 my_advantages_per_20=my_advantages_per_20,
                                                                 opponent_advantages_per_20=opponent_advantages_per_20)
        home_runs_per_400_pa = self.__result_occurances_per_400_pa(my_results=chart['hr'],
                                                                   opponent_results=opponent_chart['hr'],
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

    def point_value(self, projected:dict, positions_and_defense:dict, speed_or_ip:int) -> int:
        """Derive player's value. Uses constants to compare against other cards in set.

        Args:
          projected: Dict with projected metrics (obp, ba, ...) for 650 PA (~ full season)
          positions_and_defense: Dict with all valid positions and their corresponding defensive rating.
          speed_or_ip: In game speed ability or innings pitched.

        Returns:
          Points that the player is worth.
        """

        points = 0

        player_category = self.player_type

        # PARSE POSITION MULTIPLIER
        command_outs = f"{str(self.chart['command'])}-{str(self.chart['outs'])}"
        pts_multiplier_dict = sc.POINTS_COMMAND_OUT_MULTIPLIER[self.context]
        pts_multiplier = pts_multiplier_dict[command_outs] if command_outs in pts_multiplier_dict.keys() else 1.0
        self.points_command_out_multiplier = pts_multiplier

        # SLASH LINE VALUE
        allow_negatives = sc.POINTS_ALLOW_NEGATIVE[self.context][player_category]
        self.obp_points = round(
                            sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['onbase'] \
                            * self.stat_percentile(stat=projected['onbase_perc'],
                                                    min_max_dict=sc.ONBASE_PCT_RANGE[self.context][player_category],
                                                    is_desc=self.is_pitcher,
                                                    allow_negative=allow_negatives) \
                            * pts_multiplier
                            , 3
                        )
        self.ba_points = round(
                            sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['average'] \
                            * self.stat_percentile(stat=projected['batting_avg'],
                                                    min_max_dict=sc.BATTING_AVG_RANGE[self.context][player_category],
                                                    is_desc=self.is_pitcher,
                                                    allow_negative=allow_negatives) \
                            * pts_multiplier
                            , 3
                        )
        self.slg_points = round(
                            sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['slugging'] \
                            * self.stat_percentile(stat=projected['slugging_perc'],
                                                    min_max_dict=sc.SLG_RANGE[self.context][player_category],
                                                    is_desc=self.is_pitcher,
                                                    allow_negative=allow_negatives) \
                            * pts_multiplier
                            , 3
                        )

        # USE EITHER SPEED OR IP DEPENDING ON PLAYER TYPE
        spd_ip_category = 'ip' if self.is_pitcher else 'speed'
        if self.is_pitcher:
            spd_ip_range = sc.IP_RANGE[player_category]
            allow_negatives_speed_ip = True
        else:
            spd_ip_range = sc.SPEED_RANGE[self.context]
            allow_negatives_speed_ip = allow_negatives
        ip_under_5_negative_multiplier = 1.5 if player_category == 'starting_pitcher' and speed_or_ip < 5 else 1.0
        spd_ip_weight = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category][spd_ip_category] * ip_under_5_negative_multiplier
        self.spd_ip_points = round(
                                spd_ip_weight \
                                * self.stat_percentile(stat=speed_or_ip,
                                                        min_max_dict=spd_ip_range,
                                                        is_desc=False,
                                                        allow_negative=allow_negatives_speed_ip)
                                , 3
                            )
        if not self.is_pitcher:
            # ONLY HITTERS HAVE HR ADD TO POINTS
            self.hr_points = round(
                                sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['home_runs'] \
                                * self.stat_percentile(stat=projected['hr_per_650_pa'],
                                                        min_max_dict=sc.HR_RANGE[self.context],
                                                        is_desc=self.is_pitcher,
                                                        allow_negative=allow_negatives) \
                                * pts_multiplier
                                , 3
                            )
            # AVERAGE POINT VALUE ACROSS POSITIONS
            defense_points = 0
            for position, fielding in positions_and_defense.items():
                if position != 'DH':
                    percentile = fielding / sc.POSITION_DEFENSE_RANGE[self.context][position]
                    position_pts = percentile * sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['defense']
                    position_pts = position_pts * sc.POINTS_POSITIONAL_DEFENSE_MULTIPLIER[self.context][position]
                    defense_points += position_pts
            use_avg = list(positions_and_defense.keys()) == ['CF', 'LF/RF'] or list(positions_and_defense.keys()) == ['LF/RF', 'CF']
            num_positions_w_non_zero_def = len([pos for pos, df in positions_and_defense.items() if df != 0])
            num_positions = max(num_positions_w_non_zero_def, 1)
            avg_points_per_position = defense_points / (num_positions if num_positions < 2 or use_avg else ( (num_positions + 2) / 3.0))
            self.defense_points = round(avg_points_per_position,3)

        # CLOSER BONUS (00 ONLY)
        apply_closer_bonus = 'CLOSER' in self.positions_and_defense.keys() and self.context == '2000'
        self.points_bonus = 25 if apply_closer_bonus else 0

        # ICONS (03+)
        icon_pts = 0
        if self.context in ['2003','2004','2005',sc.EXPANDED_SET] and len(self.icons) > 0:
            for icon in self.icons:
                icon_pts += icon.points
        self.icon_points = round(icon_pts,3)

        # COMBINE POINT VALUES
        points = self.obp_points + self.ba_points + self.slg_points + self.spd_ip_points + self.points_bonus + self.icon_points
        if not self.is_pitcher:
            points += self.hr_points + self.defense_points

        # --- APPLY ANY ADDITIONAL PT ADJUSTMENTS FOR DIFFERENT SETS ---

        # SOME SETS PULL CARDS SLIGHTLY TOWARDS THE MEDIAN
        if sc.POINTS_NORMALIZE_TOWARDS_MEDIAN[self.context][player_category]:
            points = self.__normalize_points_towards_median(points)
        else:
            self.points_normalizer = 1.0

        # ADJUST POINTS FOR RELIEVERS WITH 2X IP
        if player_category == 'relief_pitcher':
            is_multi_inning = self.ip > 1
            ip_as_string = str(self.ip)
            if ip_as_string in sc.POINTS_RELIEVER_IP_MULTIPLIER[self.context].keys():
                multi_inning_points_multiplier = sc.POINTS_RELIEVER_IP_MULTIPLIER[self.context][ip_as_string] if is_multi_inning else 1.0
                if is_multi_inning:
                    self.multi_inning_points_multiplier = multi_inning_points_multiplier
                points *= multi_inning_points_multiplier
        
        if self.is_pitcher:
            # PITCHERS GET PTS FOR OUT DISTRIBUTION IN SOME SETS
            pct_gb = self.chart['gb'] / self.chart['outs']
            if 'out_distribution' in sc.POINT_CATEGORY_WEIGHTS[self.context][player_category].keys():
                pt_weight_gb = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['out_distribution']
                percentile_gb = self.stat_percentile(
                    stat = pct_gb, 
                    min_max_dict = sc.POINT_GB_MIN_MAX,
                    allow_negative=True
                )               
                self.out_dist_points = round(pt_weight_gb * percentile_gb,3)
                points += self.out_dist_points
                self.chart_pct_gb = round(pct_gb,4)
            else:
                self.out_dist_points = 0
                self.chart_pct_gb = round(pct_gb,4)

        # POINTS ARE ALWAYS ROUNDED TO TENTH
        points_to_nearest_tenth = int(round(points,-1))

        # POINTS CANNOT BE < 10
        points_final = 10 if points_to_nearest_tenth < 10 else points_to_nearest_tenth

        return points_final

    def stat_percentile(self, stat:float, min_max_dict:dict, is_desc:bool=False, allow_negative:bool=False) -> float:
        """Get the percentile for a particular stat.

        Args:
          stat: Value to get percentile of.
          min_max_dict: Dict with 'min' and 'max' range values for the stat
          is_desc: Boolean for whether the lowest value should be treated as positive.
          allow_negative: Boolean flag for whether to allow percentile to be < 0
        Returns:
          Percent of points to give for given category.
        """

        min = min_max_dict['min']
        max = min_max_dict['max']
        range = max - min
        stat_within_range = stat - min

        if not allow_negative and stat_within_range < 0 and not is_desc:
            stat_within_range = 0

        raw_percentile = stat_within_range / range

        # REVERSE IF DESC
        percentile_adjusted = 1 - raw_percentile if is_desc else raw_percentile

        if not allow_negative and percentile_adjusted < 0:
            percentile_adjusted = 0

        return percentile_adjusted

    def __normalize_points_towards_median(self, points:float) -> float:
        """Normalize points for subset on players towards the median.

        Args:
          points: Current Points attributed to player

        Returns:
          Updated PTS total for player after normalization.
        """

        # NORMALIZE SCORE ACROSS MEDIAN
        is_starting_pitcher = self.player_type == 'starting_pitcher'
        is_relief_pitcher = self.player_type == 'relief_pitcher'
        reliever_normalizer = sc.POINTS_NORMALIZER_RELIEVER_MULTIPLIER[self.context] if is_relief_pitcher else 1.0
        median = 310 / reliever_normalizer
        upper_limit = 800 if self.is_classic else 800
        upper_limit = upper_limit / reliever_normalizer

        # CHECK FOR STARTER WITH LOW IP
        if is_starting_pitcher and self.ip < 7 and points < 550:
            pts_ip_add = sc.POINT_CATEGORY_WEIGHTS[self.context]['starting_pitcher']['ip'] \
                            * self.stat_percentile(stat=7,
                                                   min_max_dict=sc.IP_RANGE['starting_pitcher'],
                                                   is_desc=False,
                                                   allow_negative=True)
            pts_to_compare = round(points + pts_ip_add,-1)
        else:
            pts_to_compare = round(points,-1)

        # CENTER SLIGHTLY TOWARDS MEDIAN
        points_cutoff = 120 if is_relief_pitcher else 500
        if pts_to_compare >= points_cutoff:
            min_max = {
                'min': median,
                'max': upper_limit
            }
            percentile = self.stat_percentile(
                stat = pts_to_compare if pts_to_compare < upper_limit else upper_limit,
                min_max_dict = min_max,
                is_desc = True
            )
            upper_multiplier = 1.0
            lower_multiplier = sc.POINTS_NORMALIZER_MULTIPLIER[self.context][self.player_type]
            multiplier = percentile * (upper_multiplier - lower_multiplier) + lower_multiplier

            # APPLY THIS TO OFFENSIVE STATS
            self.obp_points = round(self.obp_points * multiplier,3)
            self.ba_points = round(self.ba_points * multiplier,3)
            self.slg_points = round(self.slg_points * multiplier,3)

            if not self.is_pitcher:
                self.hr_points = round(self.hr_points * multiplier,3)

            self.points_normalizer = round(multiplier,3)
            return self.obp_points + self.ba_points + self.slg_points + self.spd_ip_points + self.points_bonus + self.icon_points
        else:
            self.points_normalizer = 1.0
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
            key_command: sc.LEAGUE_AVG_COMMAND[self.context], 
            key_obp: sc.LEAGUE_AVG_PROJ_OBP[self.context],
            key_slg: sc.LEAGUE_AVG_PROJ_SLG[self.context],
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
        command_adjustment_factor = 1.0 + ( abs_pct_above_or_below_avg * sc.COMMAND_ADJUSTMENT_FACTOR_WEIGHT * negative_multiplier)

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

    def accuracy_between_dicts(self, actuals_dict:dict, measurements_dict:dict, weights:dict={}, all_or_nothing:list[str]=[], only_use_weight_keys:bool=False, era_override:str = None) -> tuple[float, dict, dict]:
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
        chart_w_combined_command_outs['command-outs'] = '{}-{}'.format(self.chart['command'],self.chart['outs'])
        chart_w_combined_command_outs['spd'] = self.speed
        chart_w_combined_command_outs['defense'] = int(list(self.positions_and_defense.values())[0])
        
        # COMBINE 1B and 1B+ IF NON-VOLATILE CATEGORIES
        if not self.is_pitcher and '1b+' not in wotc_card_dict.keys():
            chart_w_combined_command_outs['1b'] = chart_w_combined_command_outs['1b'] + chart_w_combined_command_outs['1b+']
            
        if is_pts_only:
            chart_w_combined_command_outs['points'] = self.points

        return self.accuracy_between_dicts(actuals_dict=wotc_card_dict,
                                           measurements_dict=chart_w_combined_command_outs,
                                           weights={},
                                           all_or_nothing=['command-outs'])

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
        print(f"{self.name} ({self.year})")
        print("----------------------------------------")
        print(f"Team: {self.team.value}")
        print(f"Set: {self.context} {self.expansion} (v{self.version})")
        print(f"Era: {self.era.title()}")
        print(f"Data Source: {self.source}")
        if self.player_image_source:
            print(f"Img Source: {self.player_image_source}")

        # ----- POSITION AND ICONS  ----- #

        # POSITION
        positions_string = ''
        for position,fielding in self.positions_and_defense_for_visuals.items():
            positions_string += f'{position}{"" if fielding < 0 else "+"}{fielding} ' if not self.is_pitcher else position
        # IP / SPEED
        ip_or_speed = 'Speed {} ({})'.format(self.speed_letter,self.speed) if not self.is_pitcher else '{} IP'.format(self.ip)
        # ICON(S)
        icon_string = ''
        for index, icon in enumerate(self.icons):
            icon_string += f"{'|' if index == 0 else ''} {icon.value} "

        print(f"\n{self.points} PTS | {positions_string}| {ip_or_speed} {icon_string}")

        print(f"{self.chart['command']} {'CONTROL' if self.is_pitcher else 'ONBASE'}")

        chart_columns = self.chart_categories
        chart_ranges = [self.chart_ranges[f'{category} Range'] for category in chart_columns]
        chart_tbl = PrettyTable(field_names=[col.upper() for col in chart_columns])
        chart_tbl.add_row(chart_ranges)

        print("\nCHART")
        print(chart_tbl)

        stat_categories_dict = {
            'BA': 'batting_avg',
            'OBP': 'onbase_perc',
            'SLG': 'slugging_perc',
            'OPS': 'onbase_plus_slugging',
            'OPS+': 'onbase_plus_slugging_plus',
            'PA': 'PA',
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
        real_life_pa = int(self.stats['PA'])
        real_life_pa_ratio = int(self.stats['PA']) / 650.0
        all_numeric_value_lists = []
        for source in final_dict.keys():
            source_dict = getattr(self, source)
            src_value_name = source.replace('stats', 'real').upper()
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

    def player_data_for_html_table(self) -> list[list[str]]:
        """Provides data needed to populate the statline shown on the showdownbot.com webpage.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of a category,
          real stat, and in-game Showdown estimated stat.
        """

        final_player_data = []

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
                    stat = 'N/A'
                else:
                    stat_raw = 0 if str(stat_raw) == '' else stat_raw
                    stat_cleaned = int(stat_raw) if category in rounded_metrics_list else stat_raw
                    stat = str(stat_cleaned) if stat_raw else 'N/A'
                short_name_map = {
                    'onbase_plus_slugging_plus': 'OPS+',
                    'whip': 'WHIP',
                    'bWAR': 'bWAR',
                    'dWAR': 'dWAR',
                    'SB': f'{category_prefix}SB',
                    'earned_run_avg': 'ERA',
                }
                short_category_name = short_name_map[category]
                final_player_data.append([short_category_name,stat,'N/A'])

        # DEFENSE (IF APPLICABLE)
        for position, metric_and_value_dict in self.positions_and_real_life_ratings.items():
            for metric, value in metric_and_value_dict.items():
                final_player_data.append([f'{metric.upper()}-{position}',str(round(value)),'N/A'])
        
        return final_player_data

    def points_data_for_html_table(self) -> list[list[str]]:
        """Provides data needed to populate the points breakdown shown on the showdownbot.com webpage.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of a pts category, stat and value.
        """
        
        if self.player_type == 'relief_pitcher' and self.ip > 1:
            spd_or_ip = ['IP', str(self.ip), f"{self.multi_inning_points_multiplier}x"]
        else:
            spd_or_ip = [
                'IP' if self.is_pitcher else 'SPD', 
                str(self.ip if self.is_pitcher else self.speed),
                str(round(self.spd_ip_points))
            ]
        pts_data = [
            ['BA', self.__format_slash_pct(self.projected['batting_avg']), str(round(self.ba_points))],
            ['OBP', self.__format_slash_pct(self.projected['onbase_perc']), str(round(self.obp_points))],
            ['SLG', self.__format_slash_pct(self.projected['slugging_perc']), str(round(self.slg_points))],
            spd_or_ip,

        ]

        if not self.is_pitcher:
            pts_data.append(['HR (650 PA)', str(round(self.projected['hr_per_650_pa'])), str(round(self.hr_points))])
            pts_data.append([
                'DEFENSE', 
                self.__position_and_defense_as_string(is_horizontal=True),
                str(round(self.defense_points))
            ])
        else:
            pts_data.append(['OUT DIST', str(round(self.chart_pct_gb,2)), str(round(self.out_dist_points))])
        
        if self.points_bonus > 0:
            pts_data.append(['BONUS', 'N/A', str(round(self.points_bonus))])
        if self.icon_points > 0:
            pts_data.append(['ICONS', ','.join([i.value for i in self.icons]), str(round(self.icon_points))])
        if self.points_normalizer < 1.0:
            pts_data.append(['NORMALIZER', 'N/A', str(round(self.points_normalizer,2))])
        if self.points_command_out_multiplier != 1.0:
            command_name = 'CTRL' if self.is_pitcher else 'OB'
            pts_data.append([f'{command_name}/OUT MULTLIPLIER', 'N/A', str(round(self.points_command_out_multiplier,2))])
        
        
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
        for index, co_accuracy_tuple in enumerate(self.top_command_out_combinations):
            command_out_tuple = co_accuracy_tuple[0]
            command = command_out_tuple[0]
            outs = command_out_tuple[1]
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
            'speed': self.speed,
            'ip': self.ip,
            'onbase_perc': self.__format_slash_pct(self.projected['onbase_perc']) if 'onbase_perc' in self.projected.keys() else 0.00,
            'slugging_perc': self.__format_slash_pct(self.projected['slugging_perc']) if 'slugging_perc' in self.projected.keys() else 0.00,
            'batting_avg': self.__format_slash_pct(self.projected['batting_avg']) if 'batting_avg' in self.projected.keys() else 0.00,
            'onbase_plus_slugging': self.__format_slash_pct(self.projected['onbase_plus_slugging']) if 'onbase_plus_slugging' in self.projected.keys() else 0.00,
            'hr_per_650_pa': round(self.projected['hr_per_650_pa'],1) if 'hr_per_650_pa' in self.projected.keys() else 0,
        }
        positions = ['CA','C','1B','2B','3B','SS','LF/RF','CF','OF']
        for position in positions:
            values_mapping[position] = self.positions_and_defense[position] if position in self.positions_and_defense.keys() else 0

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

        opponent_dict = sc.BASELINE_HITTER[self.context][self.era] if self.is_pitcher else sc.BASELINE_PITCHER[self.context][self.era]

        return [[category.upper(), str(round(value,2))] for category, value in opponent_dict.items()]

    def __player_metadata_summary_text(self, is_horizontal:bool=False, return_as_list:bool=False) -> str:
        """Creates a multi line string with all player metadata for card output.

        Args:
          is_horizontal: Optional boolean for horizontally formatted text (04/05)
          return_as_list: Boolean for return type

        Returns:
          String/list of output text for player info + stats
        """
        positions_string = self.__position_and_defense_as_string(is_horizontal=is_horizontal)

        ip = '{} IP'.format(self.ip) if self.context in ['2000','2001','2002','2003'] else 'IP {}'.format(self.ip)
        speed = f'SPD {self.speed}' if self.context in sc.CLASSIC_AND_EXPANDED_SETS else f'Speed {self.speed_letter} ({self.speed})'
        ip_or_speed = speed if not self.is_pitcher else ip
        if is_horizontal:
            if return_as_list:
                final_text = [
                    f'{self.points} PT.',
                    positions_string if self.is_pitcher else speed,
                    self.hand,
                    (ip if self.is_pitcher else positions_string),
                ]
            else:
                spacing_between_hand_and_final_item = '  ' if self.context in ['2004','2005'] and not self.is_pitcher and len(positions_string) > 13 and len(self.icons) > 0 else '   '
                final_text = '{points} PT.   {item2}   {hand}{spacing_between_hand_and_final_item}{item4}'.format(
                    points=self.points,
                    item2=positions_string if self.is_pitcher else speed,
                    hand=self.hand,
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
                hand=self.hand,
                line3=ip_or_speed if self.is_pitcher else positions_string,
                points=self.points
            )
        final_text = final_text.upper() if self.context in ['2002','2004','2005'] else final_text
        return final_text

    def __position_and_defense_as_string(self, is_horizontal:bool=False) -> str:
        """Creates a single line string with positions and defense.

        Args:
          is_horizontal: Optional boolean for horizontally formatted text (04/05)

        Returns:
          String of output text for player's defensive stats
        """
        positions_string = ''
        position_num = 1
        dh_string = '–' if self.context != '2000' else 'DH'

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
        tm_colors = self.__team_color_rgbs(is_secondary_color=self.use_secondary_color)

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
        if self.edition == Edition.HOLIDAY:
            holiday_image_path = self.__template_img_path('Holiday')
            holiday_image = Image.open(holiday_image_path)
            card_image.paste(holiday_image,self.__coordinates_adjusted_for_bordering(coordinates=(0,0)),holiday_image)

        # LOAD SHOWDOWN TEMPLATE
        showdown_template_frame_image = self.__template_image()
        card_image.paste(showdown_template_frame_image,self.__coordinates_adjusted_for_bordering(coordinates=(0,0)),showdown_template_frame_image)

        # CREATE NAME TEXT
        name_text, color = self.__player_name_text_image()
        small_name_cutoff = 18 if self.context == '2000' else 19
        location_key = 'player_name_small' if len(self.name) >= small_name_cutoff and self.image_parallel != sc.ImageParallel.MYSTERY else 'player_name'
        name_paste_location = sc.IMAGE_LOCATIONS[location_key][str(self.context_year)]
        if self.context in ['2000', '2001']:
            # ADD BACKGROUND BLUR EFFECT FOR 2001 CARDS
            name_text_blurred = name_text.filter(ImageFilter.BLUR)
            shadow_paste_coordinates = (name_paste_location[0] + 6, name_paste_location[1] + 6)
            card_image.paste(sc.COLOR_BLACK, self.__coordinates_adjusted_for_bordering(shadow_paste_coordinates), name_text_blurred)
        card_image.paste(color, self.__coordinates_adjusted_for_bordering(name_paste_location),  name_text)

        # ADD TEAM LOGO
        disable_team_logo = self.hide_team_logo or (self.edition.has_additional_logo_00_01 and self.context == '2000')
        if not disable_team_logo:
            team_logo, team_logo_coords = self.__team_logo_image()
            card_image.paste(team_logo, self.__coordinates_adjusted_for_bordering(team_logo_coords), team_logo)

        # 00/01 ADDITIONAL LOGO
        card_image = self.__add_additional_logos_00_01(image=card_image)

        # METADATA
        metadata_image, color = self.__metadata_image()
        metadata_paste_coordinates = self.__coordinates_adjusted_for_bordering(sc.IMAGE_LOCATIONS['metadata'][str(self.context_year)])
        card_image.paste(color, metadata_paste_coordinates, metadata_image)

        # CHART
        chart_image, color = self.__chart_image()
        if self.context in ['2000','2001']:
            chart_cords = sc.IMAGE_LOCATIONS['chart'][f"{self.context_year}{'p' if self.is_pitcher else 'h'}"]
        else:
            chart_cords = sc.IMAGE_LOCATIONS['chart'][f'{self.context_year}']
        card_image.paste(color, self.__coordinates_adjusted_for_bordering(chart_cords), chart_image)

        # STYLE (IF APPLICABLE)
        if self.context in sc.CLASSIC_AND_EXPANDED_SETS:
            theme_suffix = '-DARK' if self.is_dark_mode else ''
            style_img_path = self.__template_img_path(f'{self.context}{theme_suffix}')
            style_img = Image.open(style_img_path)
            style_coordinates = self.__coordinates_adjusted_for_bordering(sc.IMAGE_LOCATIONS['style'][self.context_year])
            card_image.paste(style_img, style_coordinates, style_img)
        
        # ICONS
        if self.has_icons:
            card_image = self.__add_icons_to_image(card_image)

        # SET
        set_image = self.__card_set_image()
        card_image.paste(set_image, self.__coordinates_adjusted_for_bordering((0,0)), set_image)

        # YEAR CONTAINER
        if self.add_year_container:
            paste_location = sc.IMAGE_LOCATIONS['year_container'][str(self.context_year)]
            year_container_img = self.__year_container_add_on()
            card_image.paste(year_container_img, self.__coordinates_adjusted_for_bordering(paste_location), year_container_img)

        # EXPANSION
        if self.expansion != 'FINAL':
            expansion_image = self.__expansion_image()
            expansion_location = sc.IMAGE_LOCATIONS['expansion'][str(self.context_year)]
            if self.add_year_container and self.context in ['2000','2001']:
                # IF YEAR CONTAINER EXISTS, MOVE OVER EXPANSION LOGO
                expansion_location = (expansion_location[0] - 140, expansion_location[1] + 5)
            if self.context == '2002' and self.expansion == 'TD':
                expansion_location = (expansion_location[0] + 20,expansion_location[1] - 17)
            elif self.context in sc.CLASSIC_AND_EXPANDED_SETS and self.expansion == 'TD':
                expansion_location = (expansion_location[0],expansion_location[1] - 12)
            card_image.paste(expansion_image, self.__coordinates_adjusted_for_bordering(expansion_location), expansion_image)

        # BETA TAG
        # TO BE REMOVED AFTER TEST PERIOD
        # if self.context in sc.CLASSIC_AND_EXPANDED_SETS:
        #     beta_img_path = self.__template_img_path('BETA')
        #     beta_banner_image = Image.open(beta_img_path)
        #     card_image.paste(beta_banner_image,(0,0),beta_banner_image)

        # SAVE AND SHOW IMAGE
        # CROP TO 63mmx88mm or bordered
        final_size = sc.CARD_SIZE_BORDERED_FINAL if self.add_image_border else sc.CARD_SIZE_FINAL
        card_image = self.__center_and_crop(card_image,final_size)
        card_image = self.__round_corners(card_image, 60)

        # MAKE IMAGE BLACK AND WHITE IF PARALLEL IS SELECTED
        if self.image_parallel == sc.ImageParallel.BLACK_AND_WHITE:
            card_image = self.__change_image_saturation(image=card_image, saturation=0.05)

        if self.img_loading_error:
            print(self.img_loading_error)

        self.save_image(image=card_image, start_time=start_time, show=show, img_name_suffix=img_name_suffix)

    def __background_image(self) -> Image.Image:
        """Loads background image for card. Either loads from upload, url, or default
           background.

        Args:
          None

        Returns:
          PIL image object for the player background.
        """

        is_00_01_set = self.context in ['2000','2001']        
        dark_mode_suffix = '-DARK' if self.is_dark_mode and self.context in sc.CLASSIC_AND_EXPANDED_SETS else ''
        default_image_path = self.__template_img_path(f'Default Background - {self.template_set_year}{dark_mode_suffix}')
        
        # CHECK FOR CUSTOM LOCAL IMAGE ASSET (EX: NATIONALITY, ASG)
        use_nationality = self.edition == Edition.NATIONALITY and self.nationality
        country_exists = self.nationality in sc.NATIONALITY_COLORS.keys() if use_nationality else False
        custom_image_path = None
        background_image = None
        if use_nationality and country_exists:
            custom_image_path = os.path.join(os.path.dirname(__file__), 'countries', 'backgrounds', f"{self.nationality}.png")
        elif self.special_edition == sc.SpecialEdition.ASG_2023:
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

        has_border_already = background_image.size == sc.CARD_SIZE_BORDERED

        # IF 2000, ADD NAME CONTAINER
        if self.context == '2000':
            name_container = self.__2000_player_name_container_image()
            paste_coordinates = self.__coordinates_adjusted_for_bordering((0,0), is_disabled = not has_border_already)
            background_image.paste(name_container, paste_coordinates, name_container)

        if self.image_parallel.is_team_background_black_and_white:
            background_image = self.__change_image_saturation(image=background_image, saturation=0.10)
        
        if self.add_image_border and not has_border_already:
            # USE WHITE OR BLACK
            border_color = sc.COLOR_BLACK if self.is_dark_mode else sc.COLOR_WHITE
            image_border = Image.new('RGBA', sc.CARD_SIZE_BORDERED, color=border_color)
            image_border.paste(background_image.convert("RGBA"),(sc.CARD_BORDER_PADDING,sc.CARD_BORDER_PADDING),background_image.convert("RGBA"))
            background_image = image_border

        return background_image

    def team_background_image(self) -> Image.Image:
        """Create team background image dynamically for 2000/2001 sets
        
        Args:
          None
        
        Returns:
          PIL Image for team background art.
        """
        
        is_2001_set = self.context == '2001'
        image_size = sc.CARD_SIZE_BORDERED if self.add_image_border else sc.CARD_SIZE
        team_override = self.team_override_for_images
        background_color = self.__team_color_rgbs(is_secondary_color=self.use_secondary_color, team_override=team_override)
        team_background_image = Image.new('RGB', image_size, color=background_color)
        
        # ADD 2001 SET ADDITIONS
        if is_2001_set:
            # BLACK OVERLAY
            color_overlay_image = Image.new('RGBA', image_size, color=sc.COLOR_BLACK)
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
        logo_name = self.team.logo_name(year=self.median_year, is_alternate=is_alternate)
        logo_size = sc.IMAGE_SIZES['team_logo'][str(self.context_year)]
        logo_rotation = rotation if rotation else (10 if self.context == '2002' and self.edition.rotate_team_logo_2002 and not ignore_dynamic_elements else 0 )
        logo_paste_coordinates = sc.IMAGE_LOCATIONS['team_logo'][str(self.context_year)]
        is_04_05 = self.context in ['2004','2005']
        is_00_01 = self.context in ['2000','2001']
        is_cooperstown = self.edition == Edition.COOPERSTOWN_COLLECTION
        is_all_star_game = self.edition == Edition.ALL_STAR_GAME
        is_rookie_season = self.edition == Edition.ROOKIE_SEASON

        # USE INPUT SIZE IF IT EXISTS
        if size:
            logo_size = size
    
        try:
            if self.edition.use_edition_logo_as_team_logo and not is_00_01:
                # OVERRIDE TEAM LOGO WITH EITHER CC OR ASG
                logo_name = 'CCC' if is_cooperstown else f'ASG-{self.year}'
                team_logo_path = self.__team_logo_path(name=logo_name)
                is_wide_logo = logo_name == 'ASG-2022'
                logo_size_multiplier = 1.0
                if is_04_05 and is_cooperstown:
                    logo_size = (330,330)
                    logo_paste_coordinates = (logo_paste_coordinates[0] - 180,logo_paste_coordinates[1] - 105)
                elif is_wide_logo and is_all_star_game:
                    logo_size = (logo_size[0] + 85, logo_size[1] + 85)
                    x_movement = -40 if self.context in ['2000','2001'] else -85
                    logo_paste_coordinates = (logo_paste_coordinates[0] + x_movement,logo_paste_coordinates[1] - 40)
            else:
                # TRY TO LOAD TEAM LOGO FROM FOLDER. LOAD ALTERNATE LOGOS FOR 2004/2005
                logo_name = self.team.logo_name(year=self.median_year, is_alternate=is_alternate)
                logo_size_multiplier = self.team.logo_size_multiplier(year=self.median_year, is_alternate=is_alternate)
                team_logo_path = self.__team_logo_path(name=logo_name)
                if self.edition == Edition.NATIONALITY and self.nationality:
                    if self.nationality in sc.NATIONALITY_COLORS.keys():
                        team_logo_path = os.path.join(os.path.dirname(__file__), 'countries', 'flags', f'{self.nationality}.png')
                        logo_size_multiplier = 1.25
            team_logo = Image.open(team_logo_path).convert("RGBA")
            size_adjusted = tuple(int(v * logo_size_multiplier) for v in logo_size)
            if size_adjusted != logo_size:
                pixel_difference = size_adjusted[0] - logo_size[0]
                logo_paste_coordinates = tuple(int(v - (pixel_difference / 2)) for v in logo_paste_coordinates)
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
        if self.edition == Edition.SUPER_SEASON and not is_00_01:
            team_logo, _ = self.__super_season_image()
            logo_paste_coordinates = sc.IMAGE_LOCATIONS['super_season'][str(self.context_year)]

        # ADD YEAR TEXT IF COOPERSTOWN
        if is_cooperstown and is_04_05 and not is_all_star_game:
            cooperstown_logo = Image.new('RGBA', (logo_size[0] + 300, logo_size[1]))
            cooperstown_logo.paste(team_logo,(150,0),team_logo)
            year_font_path = self.__font_path('BaskervilleBoldItalicBT')
            year_font = ImageFont.truetype(year_font_path, size=87)
            year_font_blurred = ImageFont.truetype(year_font_path, size=90)
            year_abbrev = f"’{self.year[2:4]}" if not self.is_multi_year else " "
            year_text = self.__text_image(
                text = year_abbrev,
                size = (180,180),
                font = year_font,
                alignment = "center",
                fill = "#E6DABD",
                has_border = True,
                border_color = sc.COLOR_BLACK
            )
            year_text_blurred = self.__text_image(
                text = year_abbrev,
                size = (180,180),
                font = year_font_blurred,
                alignment = "center",
                fill = sc.COLOR_WHITE
            )
            year_coords = (0,195)
            cooperstown_logo.paste(sc.COLOR_BLACK,year_coords,year_text_blurred.filter(ImageFilter.BLUR))
            cooperstown_logo.paste(year_text, year_coords, year_text)
            team_logo = cooperstown_logo

        # OVERRIDE IF ROOKIE SEASON
        if is_rookie_season and not is_00_01:
            team_logo = self.__rookie_season_image()
            team_logo = team_logo.rotate(10, resample=Image.BICUBIC) if self.context == '2002' else team_logo
            logo_paste_coordinates = sc.IMAGE_LOCATIONS['rookie_season'][str(self.context_year)]

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
        force_alternate = team.use_alternate_for_background(set=self.context)
        use_alternate = self.use_alternate_logo or force_alternate
        logo_name = team.logo_name(year=self.median_year, is_alternate=use_alternate)

        # OPACITY
        opacity = team.background_logo_opacity(set=self.context)
        team_logo = Image.open(self.__team_logo_path(logo_name))
        team_logo_copy = team_logo.copy()
        team_logo_copy.putalpha(int(255 * opacity))
        team_logo.paste(team_logo_copy, team_logo)

        # SATURATION
        if self.context == '2000':
            team_logo = self.__change_image_saturation(image=team_logo, saturation=0.2)

        # SIZE
        size = team.background_logo_size(year=self.median_year, set=self.context, is_alternate=use_alternate)
        team_logo = team_logo.resize(size=size, resample=Image.ANTIALIAS)

        # ROTATION
        rotation = team.background_logo_rotation(set=self.context)
        if rotation != 0:
            team_logo = team_logo.rotate(rotation, resample=Image.BICUBIC, expand=True)

        paste_location = self.__coordinates_adjusted_for_bordering(team.background_logo_paste_location(year=self.median_year, is_alternate=use_alternate, set=self.context, image_size=sc.CARD_SIZE))
        return team_logo, paste_location

    def __template_image(self) -> Image.Image:
        """Loads showdown frame template depending on player context.

        Args:
          None

        Returns:
          PIL image object for Player's template background.
        """

        year = self.template_set_year

        # GET TEMPLATE FOR PLAYER TYPE (HITTER OR PITCHER)
        type = 'Pitcher' if self.is_pitcher else 'Hitter'
        is_04_05 = self.context in ['2004','2005']
        edition_extension = ''
        if is_04_05:
            # 04/05 HAS MORE TEMPLATE OPTIONS
            edition_extension = ''
            if self.edition.template_color_0405:
                edition_extension = f'-{self.edition.template_color_0405}'
            elif self.edition == Edition.NATIONALITY and self.nationality:
                if self.nationality in sc.NATIONALITY_TEMPLATE_COLOR.keys():
                    edition_extension = f'-{sc.NATIONALITY_TEMPLATE_COLOR[self.nationality]}'
                else:
                    edition_extension = f'-{sc.TEMPLATE_COLOR_0405[type]}'
                    self.img_loading_error = f"Country {self.nationality} not supported. Select a different Edition."
            else:
                edition_extension = f'-{sc.TEMPLATE_COLOR_0405[type]}'

            if self.image_parallel.color_override_04_05_chart:
                edition_extension = f"-{self.image_parallel.color_override_04_05_chart}"
            type_template = f'{year}-{type}{edition_extension}'
            template_image = Image.open(self.__template_img_path(type_template))
        else:
            dark_mode_extension = '-DARK' if self.context in sc.CLASSIC_AND_EXPANDED_SETS and self.is_dark_mode else ''
            type_template = f'{year}-{type}{edition_extension}{dark_mode_extension}'
            template_image = Image.open(self.__template_img_path(type_template))

        # GET IMAGE WITH PLAYER COMMAND
        paste_location = sc.IMAGE_LOCATIONS['command'][self.context_year]
        if self.context in sc.CLASSIC_AND_EXPANDED_SETS:
            # ADD TEXT + BACKGROUND AS IMAGE
            command_image = self.__command_image()
            if not self.is_pitcher:
                paste_location = (paste_location[0] + 15, paste_location[1])

            # ADD CHART ROUNDED RECT
            container_img_path = self.__template_img_path(f'{year}-ChartOutsContainer-{type}')
            container_img_black = Image.open(container_img_path)
            team_override = self.team_override_for_images
            fill_color = self.__team_color_rgbs(is_secondary_color=self.use_secondary_color, team_override=team_override)
            if self.edition == Edition.NATIONALITY and self.nationality:
                if self.nationality in sc.NATIONALITY_COLORS.keys():
                    colors = sc.NATIONALITY_COLORS[self.nationality]
                    if len(colors) >= 2:
                        gradient_img_width = 475 if self.player_type == 'position_player' else 680
                        gradient_img_rect = self.__gradient_img(size=(gradient_img_width, 190), colors=colors)
                        container_img_black.paste(gradient_img_rect, (70, 1770), gradient_img_rect)
                        container_img = self.__add_alpha_mask(img=container_img_black, mask_img=Image.open(container_img_path))
                    else:
                        container_img = self.__add_color_overlay_to_img(img=container_img_black,color=fill_color)
                else:
                    container_img = self.__add_color_overlay_to_img(img=container_img_black,color=fill_color)
            else:
                container_img = self.__add_color_overlay_to_img(img=container_img_black,color=fill_color)
            use_dark_text = self.team.use_dark_text(year=self.median_year, is_secondary=self.use_secondary_color)
            dark_mode_suffix = '-DARK' if use_dark_text else ''
            text_img = Image.open(self.__template_img_path(f'{year}-ChartOutsText-{type}{dark_mode_suffix}'))
            template_image.paste(container_img, (0,0), container_img)
            template_image.paste(text_img, (0,0), text_img)
        else:
            command_image_name = f"{year}-{type}-{str(self.chart['command'])}"
            command_image = Image.open(self.__template_img_path(command_image_name))
            
        template_image.paste(command_image, paste_location, command_image)

        # HANDLE MULTI POSITION TEMPLATES FOR 00/01 POSITION PLAYERS
        if year in ['2000','2001'] and not self.is_pitcher:
            positions_list = [pos for pos, _ in self.positions_and_defense_img_order]
            sizing = "-".join(['LARGE' if len(pos) > 4 else 'SMALL' for pos in positions_list])
            positions_points_template = f"0001-{type}-{sizing}"
            positions_points_image = Image.open(self.__template_img_path(positions_points_template))
            template_image.paste(positions_points_image, (0,0), positions_points_image)
        
        # ADD SHOWDOWN BOT LOGO AND ERA
        logo_img = self.__bot_logo_img()
        logo_paste_location = sc.IMAGE_LOCATIONS['bot_logo'][self.context_year]
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
        bot_logo_key = 'bot_logo'
        is_dark_mode = self.context in sc.CLASSIC_AND_EXPANDED_SETS and self.is_dark_mode
        dark_mode_extension = '-DARK' if is_dark_mode else ''
        logo_size = sc.IMAGE_SIZES[bot_logo_key][self.context_year]
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
        era_txt_color = "#b5b5b5" if self.context in sc.CLASSIC_AND_EXPANDED_SETS and self.is_dark_mode else "#585858"
        era_text = self.__text_image(text=self.era.replace(' ERA', ''), size=(620, 100), font=era_font, alignment="center")
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
        return Image.open(self.__template_img_path("2000-Name"))

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
        name_upper = "????? ?????" if self.image_parallel == sc.ImageParallel.MYSTERY else self.name.upper()
        first, last = name_upper.split(" ", 1)
        name = name_upper if self.context != '2001' else first
        default_chart_char_cutoff = 19 if self.context == '2002' else 15
        is_name_over_char_limit =  len(name) > default_chart_char_cutoff

        futura_black_path = self.__font_path('Futura Black')
        helvetica_neue_lt_path = self.__font_path('Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique')
        helvetica_neue_cond_black_path = self.__font_path('HelveticaNeueLtStd107ExtraBlack', extension='otf')
        helvetica_neue_lt_93_path = self.__font_path('Helvetica-Neue-LT-Std-93-Black-Extended-Oblique')

        # DEFAULT NAME ATTRIBUTES
        name_font_path = helvetica_neue_lt_path
        has_border = False
        border_color = None
        overlay_image_path = None

        # DEFINE ATTRIBUTES BASED ON CONTEXT
        if self.context == '2000':
            name_rotation = 90
            name_alignment = "center"
            is_name_over_18_chars = len(name) >= 18
            is_name_over_15_chars = len(name) >= 15
            name_size = 145
            if is_name_over_18_chars:
                name_size = 110
            elif is_name_over_15_chars:
                name_size = 127
            name_color = "#D2D2D2"
            name_font_path = helvetica_neue_lt_93_path
            padding = 0
            overlay_image_path = self.__template_img_path('2000-Name-Text-Background')
        elif self.context == '2001':
            name_rotation = 90
            name_alignment = "left"
            name_size = 96
            name_color = "#D2D2D2"
            padding = 0
            name_font_path = futura_black_path
            overlay_image_path = self.__template_img_path('2001-Name-Text-Background')
        elif self.context == '2002':
            name_rotation = 90
            name_alignment = "left"
            name_size = 115 if is_name_over_char_limit else 144
            name_color = "#b5b4b5"
            padding = 15
        elif self.context == '2003':
            name_rotation = 90
            name_alignment = "right"
            name_size = 90 if is_name_over_char_limit else 96
            name_color = sc.COLOR_WHITE
            padding = 60
        elif self.context in ['2004','2005']:
            name_rotation = 0
            name_alignment = "left"
            name_size = 80 if is_name_over_char_limit else 96
            name_color = sc.COLOR_WHITE
            padding = 3
            has_border = True
            border_color = sc.COLOR_RED
        else:
            name_rotation = 0
            name_alignment = "left"
            name_size = 80 if is_name_over_char_limit else 96
            name_color = sc.COLOR_WHITE
            name_font_path = helvetica_neue_cond_black_path
            padding = 3
            has_border = False

        name_font = ImageFont.truetype(name_font_path, size=name_size)
        # CREATE TEXT IMAGE
        final_text = self.__text_image(
            text = name,
            size = sc.IMAGE_SIZES['player_name'][self.context_year],
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
        if self.context == '2000':
            # SETUP COLOR FOR LATER STEP OF IMAGE OVERLAY
            name_color = final_text
        elif self.context == '2001':
            # ADD LAST NAME
            last_name = self.__text_image(
                text = last,
                size = sc.IMAGE_SIZES['player_name'][self.context],
                font = ImageFont.truetype(name_font_path, size=135),
                rotation = name_rotation,
                alignment = name_alignment,
                padding = padding,
                fill = name_color,
                overlay_image_path = overlay_image_path
            )
            final_text.paste(last_name, (90,0), last_name)
            name_color = final_text
        elif self.context in ['2004','2005']:
            # DONT ASSIGN A COLOR TO TEXT AS 04/05 HAS MULTIPLE COLORS.
            # ASSIGN THE TEXT ITSELF AS THE COLOR OBJECT
            name_color = final_text
        elif self.context in sc.CLASSIC_AND_EXPANDED_SETS:
            name_color = sc.COLOR_WHITE if self.is_dark_mode else sc.COLOR_BLACK

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
        color = sc.COLOR_WHITE

        if self.context in ['2000','2001']:
            # 2000 & 2001

            metadata_image = Image.new('RGBA', (1500, 2100), 255)
            helvetica_neue_lt_path = self.__font_path('Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique')

            # PITCHER AND HITTER SPECIFIC METADATA
            if self.is_pitcher:
                # POSITION
                font_position = ImageFont.truetype(helvetica_neue_lt_path, size=72)
                position = list(self.positions_and_defense.keys())[0]
                position_text = self.__text_image(text=position, size=(900, 300), font=font_position, alignment='center')
                metadata_image.paste(sc.COLOR_WHITE, (660,342), position_text)
                # HAND | IP
                font_hand_ip = ImageFont.truetype(helvetica_neue_lt_path, size=63)
                hand_text = self.__text_image(text=self.hand, size=(900, 300), font=font_hand_ip)
                metadata_image.paste(sc.COLOR_WHITE, (1092,420), hand_text)
                ip_text = self.__text_image(text='IP {}'.format(str(self.ip)), size=(900, 300), font=font_hand_ip)
                metadata_image.paste(sc.COLOR_WHITE, (1260,420), ip_text)
            else:
                # SPEED | HAND
                is_variable_spd_2000 = self.context == '2000' and self.is_variable_speed_00_01
                font_size_speed = 40 if is_variable_spd_2000 else 54
                font_speed = ImageFont.truetype(helvetica_neue_lt_path, size=font_size_speed)
                font_hand = ImageFont.truetype(helvetica_neue_lt_path, size=54)
                speed_text = self.__text_image(text='SPEED {}'.format(self.speed_letter), size=(900, 300), font=font_speed)
                hand_text = self.__text_image(text=self.hand[-1], size=(300, 300), font=font_hand)
                metadata_image.paste(color, (969 if self.context == '2000' else 915, 345 if is_variable_spd_2000 else 342), speed_text)
                metadata_image.paste(color, (1212,342), hand_text)
                if self.context == '2001' or is_variable_spd_2000:
                    # ADD # TO SPEED
                    font_speed_number = ImageFont.truetype(helvetica_neue_lt_path, size=40)
                    font_parenthesis = ImageFont.truetype(helvetica_neue_lt_path, size=45)
                    speed_num_text = self.__text_image(
                        text=str(self.speed),
                        size=(300, 300),
                        font=font_speed_number
                    )
                    parenthesis_left = self.__text_image(text='(   )', size=(300, 300), font=font_parenthesis)
                    metadata_image.paste(color, (1116,342), parenthesis_left)
                    spd_number_x_position = 1138 if len(str(self.speed)) < 2 else 1128
                    metadata_image.paste(color, (spd_number_x_position,345), speed_num_text)
                # POSITION(S)
                font_position = ImageFont.truetype(helvetica_neue_lt_path, size=78)
                y_position = 407
                for index, (position, rating) in enumerate(self.positions_and_defense_img_order):
                    dh_string = '   —' if self.context != '2000' else '   DH'
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

        elif self.context in ['2002','2003']:
            # 2002 & 2003

            color = sc.COLOR_BLACK if self.context == '2002' else sc.COLOR_WHITE
            if self.context_year == '2002':
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
                spacing= 66 if self.context == '2003' else 57
            )
            metadata_image = metadata_text.resize((255,900), Image.ANTIALIAS)
        elif self.context in ['2004','2005']:
            # 2004 & 2005

            metadata_font_path = self.__font_path('Helvetica Neue 77 Bold Condensed')
            metadata_font = ImageFont.truetype(metadata_font_path, size=144)
            metadata_text_string = self.__player_metadata_summary_text(is_horizontal=True)
            metadata_text = self.__text_image(
                text = metadata_text_string,
                size = (3600, 900),
                font = metadata_font,
                fill = sc.COLOR_WHITE,
                rotation = 0,
                alignment = "left",
                padding = 0,
                has_border = True,
                border_color = sc.COLOR_BLACK,
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
                    fill = sc.COLOR_WHITE,
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
                        fill = sc.COLOR_WHITE,
                        rotation = 0,
                        alignment = "left",
                        padding = 0,
                    )
                    divider_text = divider_text.resize((300,300), Image.ANTIALIAS)
                    metadata_image.paste((255,255,255,50), (int(current_x_position) + 30, 0), divider_text)
                    current_x_position += 65
                

            color = sc.COLOR_GRAY if self.is_dark_mode else sc.COLOR_BLACK

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

        is_horizontal = self.context in ['2004','2005',sc.CLASSIC_SET, sc.EXPANDED_SET]

        # FONT
        chart_font_file_name = 'Helvetica Neue 77 Bold Condensed' if is_horizontal else 'HelveticaNeueCondensedMedium'
        chart_font_path = self.__font_path(chart_font_file_name)
        chart_text_size = int(sc.TEXT_SIZES['chart'][self.context_year])
        chart_font = ImageFont.truetype(chart_font_path, size=chart_text_size)

        # CREATE CHART RANGES TEXT
        chart_string = ''
        # NEED IF 04/05
        chart_text = Image.new('RGBA',(6300,720))
        chart_text_addition = -20 if self.context in sc.CLASSIC_AND_EXPANDED_SETS else 0
        chart_text_x = 150 + chart_text_addition if self.is_pitcher else 141
        for category in self.chart_categories:
            is_out_category = category.lower() in ['pu','so','gb','fb']
            range = self.chart_ranges['{} Range'.format(category)]
            # 2004/2005 CHART IS HORIZONTAL. PASTE TEXT ONTO IMAGE INSTEAD OF STRING OBJECT.
            if is_horizontal:
                is_wotc = self.context in ['2004','2005']
                range_text = self.__text_image(
                    text = range,
                    size = (450,450),
                    font = chart_font,
                    fill = sc.COLOR_WHITE,
                    alignment = "center",
                    has_border = is_wotc,
                    border_color = sc.COLOR_BLACK,
                    border_size = 9
                )
                use_dark_text = self.team.use_dark_text(year=self.median_year, is_secondary=self.use_secondary_color) and self.context_year == '2022' and is_out_category
                color_range = range_text if (is_wotc or is_out_category or self.is_dark_mode) and not use_dark_text else sc.COLOR_BLACK
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
            spacing = int(sc.TEXT_SIZES['chart_spacing'][self.context_year])
            chart_text = self.__text_image(
                text = chart_string,
                size = (765, 3600),
                font = chart_font,
                rotation = 0,
                alignment = "right",
                padding=0,
                spacing=spacing
            )
            color = sc.COLOR_BLACK
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
        font_size = 180 if self.context in sc.CLASSIC_AND_EXPANDED_SETS else 135
        set_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=font_size)

        set_image = Image.new('RGBA', (1500, 2100), 255)
        set_image_location = sc.IMAGE_LOCATIONS['set'][str(self.context_year)]

        if self.context in ['2000', '2001', '2002']:
            # SET AND NUMBER IN SAME STRING
            set_text = self.__text_image(
                text = self.set_number,
                size = (600, 300),
                font = set_font,
                alignment = "center"
            )
            set_text = set_text.resize((150,75), Image.ANTIALIAS)
            set_image.paste(sc.COLOR_WHITE, set_image_location, set_text)
        else:
            # DIFFERENT STYLES BETWEEN NUMBER AND SET
            # CARD YEAR
            set_font_year = set_font
            year_as_str = str(self.year)
            if self.is_multi_year and self.context in ['2004','2005']:
                # EMPTY YEAR
                year_string = ''
            elif (self.is_full_career or self.is_multi_year) and self.context == '2003':
                year_string = 'ALL' if self.is_full_career else 'MLT'
                set_image_location = (set_image_location[0]-5,set_image_location[1])
            elif self.is_multi_year and self.context in sc.CLASSIC_AND_EXPANDED_SETS:
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
                    year_as_str = str(int(year_as_str) + (1 if self.set_year_plus_one else 0))
                except:
                    year_as_str = year_as_str
                year_string = year_as_str if self.context in sc.CLASSIC_AND_EXPANDED_SETS else f"'{year_as_str[2:4]}"
            year_text = self.__text_image(
                text = year_string,
                size = (525, 450),
                font = set_font_year,
                alignment = "left"
            )
            year_text = year_text.resize((140,120), Image.ANTIALIAS)
            set_image.paste(sc.COLOR_WHITE, set_image_location, year_text)

            # CARD NUMBER
            number_text = self.__text_image(
                text = self.set_number,
                size = (600, 450),
                font = set_font,
                alignment = "center"
            )
            number_text = number_text.resize((160,120), Image.ANTIALIAS)
            number_color = sc.COLOR_BLACK if self.context == '2003' else sc.COLOR_WHITE
            set_image.paste(number_color, sc.IMAGE_LOCATIONS['number'][str(self.context_year)], number_text)

        return set_image

    def __expansion_image(self) -> Image.Image:
        """Creates image for card expansion (ex: Trade Deadline, Pennant Run)
        
        Args:
          None

        Returns:
          PIL image object for card expansion logo.
        """ 

        expansion_image = Image.open(self.__template_img_path(f'{self.template_set_year}-{self.expansion}'))
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

        is_after_03 = self.context in ['2004','2005',sc.CLASSIC_SET,sc.EXPANDED_SET]
        include_accolades = self.context not in [sc.CLASSIC_SET,sc.EXPANDED_SET]

        # FONTS
        super_season_year_path = self.__font_path('URW Corporate W01 Normal')
        super_season_accolade_path = self.__font_path('Zurich Bold Italic BT')
        super_season_year_font = ImageFont.truetype(super_season_year_path, size=225)
        super_season_accolade_font = ImageFont.truetype(super_season_accolade_path, size=150)

        accolade_text_images = []
        if include_accolades:
            
            # SLOT MAX CHARACTERS
            slot_max_characters_dict = {
                1: (16 if is_after_03 else sc.SUPER_SEASON_PRE_04_TEXT_LENGTH),
                2: (15 if is_after_03 else sc.SUPER_SEASON_PRE_04_TEXT_LENGTH),
                3: (sc.SUPER_SEASON_04_05_MIN_TEXT_LENGTH if is_after_03 else sc.SUPER_SEASON_PRE_04_TEXT_LENGTH),
            }

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
        ss_type_index = sc.SUPER_SEASON_IMG_INDEX.get(self.context, '1')
        super_season_image = Image.open(self.__template_img_path(f'Super Season-{ss_type_index}{num_accolades_str}'))

        # ORDER 04/05 ACCOLADES BY TEXT LENGTH
        if is_after_03:
            coordinates = [tup[1] for tup in accolade_text_images]
            sorted_accolade_img_and_text = sorted([(tup[0], tup[2]) for tup in accolade_text_images], key=lambda a: len(a[1]), reverse=True)
            accolade_text_images = [(sorted_accolade_img_and_text[index][0], coordinates[index], sorted_accolade_img_and_text[index][1]) for index in range(0, len(accolade_text_images))]

        # PASTE ACCOLADES
        for accolade_img, paste_coordinates, _ in accolade_text_images:
            super_season_image.paste(sc.COLOR_BLACK, paste_coordinates, accolade_img)

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
        year_paste_coords = sc.IMAGE_LOCATIONS['super_season_year_text'][self.context_year]
        if self.is_multi_year:
            if self.context in sc.CLASSIC_AND_EXPANDED_SETS:
                year_paste_coords = (122,265)
            else:
                year_paste_coords = (126,110) if is_after_03 else (26,290)
        year_color = "#ffffff" if self.context in sc.CLASSIC_AND_EXPANDED_SETS else "#982319"
        super_season_image.paste(year_color,year_paste_coords,year_text)

        # ADJUSTMENTS TO 00/01 Y COORDINATES
        y_coord_adjustment = ( (3 - num_accolades) * 55 ) if self.context in ['2000','2001'] and num_accolades < 3 else 0

        # RESIZE
        super_season_image = super_season_image.resize(sc.IMAGE_SIZES['super_season'][self.context_year], Image.ANTIALIAS)
        return super_season_image, y_coord_adjustment

    def __rookie_season_image(self) -> Image.Image:
        """Creates image for optional rookie season logo.

        Args:
          None

        Returns:
          PIL image object for rookie season logo + year.
        """

        # BACKGROUND IMAGE LOGO
        rookie_season_image = Image.open(self.__template_img_path(f'{self.template_set_year}-Rookie Season'))

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
            location_original = sc.IMAGE_LOCATIONS['rookie_season_year_text'][self.context_year]
            x_adjustment = 230 if is_suffix else 0
            paste_location = (location_original[0] + x_adjustment, location_original[1])
            rookie_season_image.paste(year_text,paste_location,year_text)

        # RESIZE
        logo_size = sc.IMAGE_SIZES['rookie_season'][str(self.context_year)]
        rookie_season_image = rookie_season_image.resize(logo_size, Image.ANTIALIAS)

        return rookie_season_image

    def __add_icons_to_image(self, player_image:Image.Image) -> Image.Image:
        """Add icon images (if player has icons) to existing player_image object.
           Only for >= 2003 sets.

        Args:
          player_image: Current PIL image object for Showdown card.

        Returns:
          Updated PIL Image with icons for player.
        """

        icon_positional_mapping = sc.ICON_LOCATIONS[self.context_year]
        # ITERATE THROUGH AND PASTE ICONS
        for index, icon in enumerate(self.icons[0:4]):
            position = icon_positional_mapping[index]
            if self.context not in sc.CLASSIC_AND_EXPANDED_SETS:
                icon_img_path = self.__template_img_path(f'{self.template_set_year}-{icon.value}')
                icon_image = Image.open(icon_img_path)
                # IN 2004/2005, ICON LOCATIONS DEPEND ON PLAYER POSITION LENGTH
                # EX: 'LF/RF' IS LONGER STRING THAN '3B'
                if self.context in ['2004','2005']:
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
        text_color = sc.COLOR_WHITE
        border_size = 9
        icon_img = Image.new('RGBA',(220,220))
        draw = ImageDraw.Draw(icon_img)
        x1 = 20
        y1 = 20
        x2 = 190
        y2 = 190       
        draw.ellipse((x1-border_size, y1-border_size, x2+border_size, y2+border_size), fill=text_color)
        draw.ellipse((x1, y1, x2, y2), fill=self.__team_color_rgbs(is_secondary_color=self.use_secondary_color, team_override=self.team_override_for_images))

        # ADD TEXT
        font_path = self.__font_path('Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique')
        font = ImageFont.truetype(font_path, size=120)
        text_img = self.__text_image(text=text,size=(210,220),font=font,alignment='center',fill=text_color)
        icon_img.paste(text_img, (0,60), text_img)
        icon_img = icon_img.resize((80, 80), Image.ANTIALIAS)

        return icon_img
        
    def __add_additional_logos_00_01(self, image:Image.Image) -> Image.Image:
        """Add CC/RS/SS logo to existing player_image object.
           Only for 2000/2001 sets.

        Args:
          image: Current PIL image object for Showdown card.

        Returns:
          Updated PIL Image with logos added above the chart.
        """
        
        # ONLY FOR 00/01 SETS
        if self.context not in ['2000','2001']:
            return image
        
        # DEFINE COORDINATES, START WITH ROOKIE SEASON DESTINATION AND EDIT FOR OTHERS
        paste_coordinates = sc.IMAGE_LOCATIONS['rookie_season'][str(self.context_year)]
        if self.edition != Edition.ROOKIE_SEASON and self.context == '2001':
            # MOVE LOGO TO THE RIGHT
            paste_coordinates = (paste_coordinates[0] + 30, paste_coordinates[1])
        if self.context == '2000':
            # MOVE LOGO ABOVE TEAM LOGO AND SLIGHTLY TO THE LEFT
            y_movement = -35 if self.edition == Edition.SUPER_SEASON else 0
            x_movement = -35 if self.edition == Edition.SUPER_SEASON else 0
            paste_coordinates = (paste_coordinates[0] - 25 + x_movement, paste_coordinates[1] + y_movement)

        # ADD LOGO
        match self.edition:
            case Edition.ALL_STAR_GAME | Edition.COOPERSTOWN_COLLECTION:
                logo_name = 'CCC' if self.edition == Edition.COOPERSTOWN_COLLECTION else f'ASG-{self.year}'
                logo_size_x, logo_size_y = sc.IMAGE_SIZES['team_logo'][str(self.context_year)]
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
        dark_mode_suffix = '-DARK' if self.is_dark_mode else ''
        background_img = Image.open(self.__template_img_path(f'{self.template_set_year}-{img_type_suffix}{dark_mode_suffix}'))
        font_path = self.__font_path('HelveticaNeueLtStd107ExtraBlack', extension='otf')
        command = str(self.chart['command'])
        num_chars_command = len(command)
        size = 170 if self.is_pitcher else 155
        font = ImageFont.truetype(font_path, size=size)

        # ADD TEXT
        fill_color = self.__team_color_rgbs(is_secondary_color=self.use_secondary_color, team_override=self.team_override_for_images)
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
        # ---- LOCAL/UPLOADED IMAGE -----
        if self.player_image_path:
            image_path = os.path.join(os.path.dirname(__file__), 'uploads', self.player_image_path)
            try:
                player_img_uploaded_raw = Image.open(image_path).convert('RGBA')
                player_img_user_uploaded = self.__center_and_crop(player_img_uploaded_raw, (1500,2100))
                images_to_paste.append((player_img_user_uploaded, default_img_paste_coordinates))
                self.player_image_source = 'Upload'
            except Exception as err:
                self.img_loading_error = str(err)
        
        # ---- IMAGE FROM URL -----
        elif self.player_image_url:
            # LOAD IMAGE FROM URL
            image_url = self.player_image_url
            try:
                response = requests.get(image_url)
                player_img_raw = Image.open(BytesIO(response.content)).convert('RGBA')
                player_img_user_uploaded = self.__center_and_crop(player_img_raw, (1500,2100))
                images_to_paste.append((player_img_user_uploaded, default_img_paste_coordinates))
                self.player_image_source = 'Link'
            except Exception as err:
                self.img_loading_error = str(err)

        # ---- IMAGE FROM GOOGLE DRIVE -----
        file_service = None
        if player_img_user_uploaded is None:
            search_for_universal_img = self.image_parallel != sc.ImageParallel.MYSTERY
            img_components_dict = self.__player_image_components_dict()
            if search_for_universal_img:
                folder_id = sc.G_DRIVE_PLAYER_IMAGE_FOLDERS['UNIVERSAL']
                file_service, img_components_dict = self.__query_google_drive_for_auto_player_image_urls(folder_id=folder_id, components_dict=img_components_dict, bref_id=self.bref_id, year=self.year)
            
            # ADD SILHOUETTE IF NECESSARY
            non_empty_components = [typ for typ in sc.IMAGE_COMPONENT_ORDERED_LIST if img_components_dict.get(typ, None) is not None and typ.is_loaded_via_download]
            if len(non_empty_components) == 0:
                img_components_dict[sc.ImageComponent.SILHOUETTE] = self.__template_img_path(f'{self.template_set_year}-SIL-{self.player_classification}')
            
            player_imgs = self.__automated_player_image_layers(component_img_urls_dict=img_components_dict, file_service=file_service)
            if len(player_imgs) > 0:
                images_to_paste += player_imgs
                if self.player_image_source is not None:
                    self.is_automated_image = True

        # IF 2000, ADD SET CONTAINER AND NAME CONTAINER IF USER UPLOADED IMAGE
        if self.context == '2000':
            if player_img_user_uploaded:
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
        for img_component in sc.IMAGE_COMPONENT_ORDERED_LIST:
            
            # ADD SILHOUETTE IF NECESSARY
            if img_component == sc.ImageComponent.SILHOUETTE and is_img_download_error:
                component_img_urls_dict[sc.ImageComponent.SILHOUETTE] = self.__template_img_path(f'{self.template_set_year}-SIL-{self.player_classification}')
            
            # CHECK FOR IMAGE TYPE
            img_url = component_img_urls_dict.get(img_component, None)
            paste_coordinates = self.__coordinates_adjusted_for_bordering(coordinates=(0,0),is_disabled=not img_component.adjust_paste_coordinates_for_bordered)
            if img_url is None and not (img_component.load_source == 'COLOR' and img_component in component_img_urls_dict.keys()):
                continue

            # CARD SIZING
            card_size = sc.CARD_SIZE_BORDERED if self.add_image_border and not img_component.adjust_paste_coordinates_for_bordered else sc.CARD_SIZE
            size_growth_multiplier = ( card_size[0] / sc.CARD_SIZE[0], card_size[1] / sc.CARD_SIZE[1])
            original_crop_size = sc.PLAYER_IMAGE_CROP_SIZE[self.context]
            player_crop_size = (int(original_crop_size[0] * size_growth_multiplier[0]), int(original_crop_size[1] * size_growth_multiplier[1])) if self.add_image_border else original_crop_size
            special_crop_adjustment = sc.PLAYER_IMAGE_CROP_ADJUSTMENT[self.context]
            if self.context in sc.CLASSIC_AND_EXPANDED_SETS and (self.special_edition == sc.SpecialEdition.ASG_2023 or self.image_parallel == sc.ImageParallel.TEAM_COLOR_BLAST):
                player_crop_size = (1275, 1785) #TODO: MAKE THIS DYNAMIC
                special_crop_adjustment = (0,int((1785 - 2100) / 2))
                if self.add_image_border:
                    player_crop_size = (int(player_crop_size[0] * size_growth_multiplier[0]), int(player_crop_size[1] * size_growth_multiplier[1]))
            default_crop_size = card_size
            default_crop_adjustment = (0,0)
            if self.context in ['2002','2003'] and img_component.crop_adjustment_02_03 is not None:
                default_crop_adjustment = img_component.crop_adjustment_02_03

            # DOWNLOAD IMAGE
            image = None
            match img_component.load_source:
                case "DOWNLOAD":
                    # 1. CHECK FOR IMAGE IN LOCAL CACHE. CACHE EXPIRES AFTER 20 MINS.
                    cached_image_filename = f"{img_component.value}-{self.year}-({self.bref_id})-({self.team.value}){self.type_override}.png"
                    cached_image_path = os.path.join(os.path.dirname(__file__), 'uploads', cached_image_filename)
                    try:
                        image = Image.open(cached_image_path)
                        self.player_image_source = 'Local Cache'
                    except:
                        image = None

                    # 2. DOWNLOAD FROM GOOGLE DRIVE IF IMAGE IS NOT FOUND FROM CACHE.
                    if image is None:
                        image = self.__download_google_drive_image(file_service=file_service,file_id=img_url)
                        if image:
                            self.__cache_downloaded_image(image=image, path=cached_image_path)
                            self.player_image_source = 'Google Drive'
                case "COLOR":
                    image = Image.new(mode='RGBA',size=card_size,color=self.__team_color_rgbs(is_secondary_color=self.use_secondary_color, ignore_team_overrides=True, team_override=self.team_override_for_images))
                case "CARD_ART" | "SILHOUETTE":
                    image = Image.open(img_url).convert('RGBA')
                case "TEAM_LOGOS":
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
            saturation_adjustment = sc.SPECIAL_EDITION_IMG_SATURATION_ADJUSTMENT.get(self.special_edition, {})
            saturation_adjustment.update(self.image_parallel.image_type_saturations_dict)
            if len(saturation_adjustment) > 0:
                component_adjustment_factor = saturation_adjustment.get(img_component, None)
                if component_adjustment_factor:
                    image = self.__change_image_saturation(image=image, saturation=component_adjustment_factor)

            # ADJUST OPACITY
            if img_component.opacity < 1.0:
                opacity_255_scale = int(255 * img_component.opacity)
                image.putalpha(opacity_255_scale)
            
            # CROP IMAGE
            crop_size = default_crop_size if img_component.ignores_custom_crop else player_crop_size
            crop_adjustment = default_crop_adjustment if img_component.ignores_custom_crop else special_crop_adjustment
            image = self.__img_crop(image, crop_size=crop_size, crop_adjustment=crop_adjustment)
            if crop_size != card_size:
                image = image.resize(size=card_size, resample=Image.ANTIALIAS)

            # SUPER SEASON: FIND LOCATIONS FOR ELLIPSES
            is_super_season_glow = img_component in [sc.ImageComponent.GLOW, sc.ImageComponent.SILHOUETTE] and self.special_edition == sc.SpecialEdition.SUPER_SEASON
            if is_super_season_glow:

                # CALCULATE COORDINATES OF ELLIPSES
                y_cords = {
                    sc.ImageComponent.ELLIPSE_LARGE: 850 if self.is_pitcher else 800,
                    sc.ImageComponent.ELLIPSE_MEDIUM: 400 if self.is_pitcher else 300,
                    sc.ImageComponent.ELLIPSE_SMALL: 1200 if self.is_pitcher else 1300,
                }
                is_reversed_map = {
                    sc.ImageComponent.ELLIPSE_LARGE: False,
                    sc.ImageComponent.ELLIPSE_MEDIUM: not self.is_pitcher,
                    sc.ImageComponent.ELLIPSE_SMALL: self.is_pitcher,
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

    def __query_google_drive_for_auto_player_image_urls(self, folder_id:str, components_dict:dict[sc.ImageComponent, str], bref_id:str, year:int = None) -> tuple:
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
                self.img_loading_error = str(err)
                failure_number += 1
                continue
            
        
        # LOOK FOR SUBSTRING IN FILE NAMES
        file_matches_metadata_dict = self.__img_file_matches_dict(files_metadata=files_metadata, components_dict=components_dict, bref_id=bref_id, year=year)
        
        return (file_service, file_matches_metadata_dict)
    
    def __img_file_matches_dict(self, files_metadata:list[dict], components_dict:dict[sc.ImageComponent, str], bref_id:str, year:int) -> dict[sc.ImageComponent, str]:
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
            if bref_id in file_name and num_components_in_filename > 0:
                component_name = file_name.split('-')[0].upper()
                component = sc.ImageComponent(component_name)
                current_files_for_component = component_player_file_matches_dict.get(component, [])
                current_files_for_component.append(img_file)
                component_player_file_matches_dict[component] = current_files_for_component

        # CHECK THAT THERE ARE MATCHES IN EACH COMPONENT
        num_matches_per_component = [len(matches) for _, matches in component_player_file_matches_dict.items()]
        if min(num_matches_per_component) < 1:
            return components_dict

        # ORDER EACH COMPONENT'S FILE LIST BY HOW WELL IT MATCHES PARAMETERS
        component_img_url_dict: dict[sc.ImageComponent, str] = {}
        additional_substring_search_list = self.__img_match_keyword_list()
        for component, img_file_list in component_player_file_matches_dict.items():
            img_file_list = sorted(img_file_list, key = lambda i: len(i['name']), reverse=False)
            match_rates = {}
            for img_metadata in img_file_list:
                img_name = img_metadata['name']
                img_id = img_metadata['id']
                match_rate = sum(val in img_name for val in additional_substring_search_list)

                # ADD DISTANCE FROM YEAR                
                year_from_img_name = img_name.split(f"-")[1] if len(img_name.split(f"-")) > 1 else 1000
                is_img_multi_year = len(year_from_img_name) > 4
                if year_from_img_name == year:
                    # EXACT YEAR MATCH
                    match_rate += 1
                elif is_img_multi_year == False and self.is_multi_year == False:
                    year_img = float(year_from_img_name)
                    year_self = float(year)
                    pct_diff = 1 - (abs(year_img - year_self) / year_self)
                    match_rate += pct_diff
                
                # ADD MATCH RATE SCORE
                match_rates[img_id] = match_rate
            
            # GET BEST MATCH
            sorted_matches = sorted(match_rates.items(), key=operator.itemgetter(1), reverse=True)
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
        use_nationality = self.edition == Edition.NATIONALITY and self.nationality
        if self.edition != Edition.NONE:
            for _ in range(0,3): # ADD 3X VALUE
                additional_substring_filters.append(f'({self.edition.value})')
        if len(self.type_override) > 0:
            additional_substring_filters.append(self.type_override)
        if self.is_dark_mode:
            additional_substring_filters.append('(DARK)')
        if use_nationality:
            for _ in range(0,4):
                additional_substring_filters.append(f'({self.nationality})') # ADDS NATIONALITY THREE TIMES TO GIVE IT 3X IMPORTANCE

        return additional_substring_filters

    def __player_image_components_dict(self) -> dict[sc.ImageComponent, str]:
        """ Add card art image paths (ex: Cooperstown, Super Season, Gradient, etc). 
        
        Add empty placeholders for image assets that are loaded from google drive.

        Returns:
          Dict with all components
        """

        # COOPERSTOWN
        is_cooperstown = self.edition == Edition.COOPERSTOWN_COLLECTION
        default_components_for_context = {c: self.__template_img_path("2000-Name") if c == sc.ImageComponent.NAME_CONTAINER_2000 else None for c in sc.AUTO_IMAGE_COMPONENTS[self.context] }
        special_components_for_context = {c: self.__template_img_path("2000-Name") if c == sc.ImageComponent.NAME_CONTAINER_2000 else None for c in sc.AUTO_IMAGE_COMPONENTS_SPECIAL[self.context] }

        if self.image_parallel.has_special_components:
            # ADD ADDITIONAL COMPONENTS
            if len(self.image_parallel.special_component_additions) > 0:
                team_logo_name = self.team.logo_name(year=self.median_year)
                special_components_for_context.update({img_component: self.__team_logo_path(team_logo_name) if img_component == sc.ImageComponent.TEAM_LOGO else self.__card_art_path(relative_path) for img_component, relative_path in self.image_parallel.special_component_additions.items()})
            # EDITING EXISTING COMPONENTS
            replacements_dict = self.image_parallel.special_components_replacements
            for old_component, new_component in replacements_dict.items():
                special_components_for_context.pop(old_component, None)
                special_components_for_context[new_component] = None
            is_asg_and_team_color_blast_dark = ( self.special_edition == sc.SpecialEdition.ASG_2023 and self.is_dark_mode and self.image_parallel == sc.ImageParallel.TEAM_COLOR_BLAST )
            if self.special_edition == sc.SpecialEdition.TEAM_COLOR_BLAST_DARK or is_asg_and_team_color_blast_dark:
                special_components_for_context.pop(sc.ImageComponent.WHITE_CIRCLE, None)
                special_components_for_context[sc.ImageComponent.BLACK_CIRCLE] = self.__card_art_path(sc.ImageComponent.BLACK_CIRCLE.name)
            default_components_for_context = special_components_for_context

        if is_cooperstown and self.context not in ['2000','2001']:
            components_dict = special_components_for_context
            components_dict[sc.ImageComponent.COOPERSTOWN] = self.__card_art_path('RADIAL' if self.context in ['2002','2003'] else 'COOPERSTOWN')
            return components_dict

        # SUPER SEASON
        if self.edition == Edition.SUPER_SEASON and self.context in ['2004','2005']:
            components_dict = special_components_for_context
            components_dict[sc.ImageComponent.DARKENER] = self.__card_art_path('DARKENER')
            components_dict[sc.ImageComponent.SUPER_SEASON] = self.__card_art_path('SUPER SEASON')
            return components_dict
        
        # ALL STAR
        if self.special_edition == sc.SpecialEdition.ASG_2023 and self.context not in ['2000','2001']:
            components_dict = { c:v for c, v in special_components_for_context.items() if not c.is_loaded_via_download }
            components_dict.update({
                sc.ImageComponent.GLOW: None,
                sc.ImageComponent.CUSTOM_BACKGROUND: self.__card_art_path(f'ASG-2023-BG-{self.league}'),
            })
            if self.context in ['2004','2005',sc.CLASSIC_SET,sc.EXPANDED_SET]:
                components_dict[sc.ImageComponent.CUSTOM_FOREGROUND] = self.__card_art_path(f'ASG-2023-FG')
            return components_dict

        # CLASSIC/EXPANDED
        if self.context in sc.CLASSIC_AND_EXPANDED_SETS and not is_cooperstown and self.image_parallel == sc.ImageParallel.NONE:
            components_dict = default_components_for_context
            components_dict[sc.ImageComponent.GRADIENT] = self.__card_art_path(f"{'DARK' if self.is_dark_mode else 'LIGHT'}-GRADIENT")
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

        if not self.add_image_border or is_disabled:
            return coordinates
        
        return (coordinates[0] + sc.CARD_BORDER_PADDING, coordinates[1] + sc.CARD_BORDER_PADDING)

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
        country_exists = self.nationality in sc.NATIONALITY_COLORS.keys() if self.nationality else False
        if self.edition == Edition.NATIONALITY and self.nationality and country_exists and not ignore_team_overrides:
            return sc.NATIONALITY_COLORS[self.nationality][0]
        
        # ASG COLOR
        if self.edition == Edition.ALL_STAR_GAME and str(self.year) in sc.ALL_STAR_GAME_COLORS.keys() and not ignore_team_overrides:
            color_for_league = sc.ALL_STAR_GAME_COLORS[str(self.year)].get(self.league, None)
            if color_for_league:
                return color_for_league
        
        # GRAB FROM CURRENT TEAM COLORS
        return team.color(year=self.median_year, is_secondary=is_secondary_color)


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
                self.img_loading_error = None
                return image
            except Exception as err:
                # IMAGE MAY FAIL TO LOAD SOMETIMES
                self.img_loading_error = str(err)
                continue
        
        return None

    def __update_image_opacity(self, image:Image.Image, opacity: float) -> Image.Image:
        """ Apply new opacity value to each pixel in the image.
        Only changes opacity of non-transparent pixels.

        Args:
          image: PIL Image to change the opacity for.
          opacity: Updated image opacity. Using 0.0 -> 1.0 scale.

        Returns:
          PIL Image updated for new opacity value.
        """
        opacity_for_rgb = int(255 * opacity)
        color_data = image.getdata()
        new_color_data = []
        for color_tuple in color_data:
            current_opacity = color_tuple[3]
            new_opacity = current_opacity if current_opacity == 0 else opacity_for_rgb
            color_tuple = color_tuple[:3]
            color_tuple = color_tuple + (new_opacity, ) #change the 100 to any transparency number you like between (0,255)
            new_color_data.append(color_tuple)
        
        image.putdata(new_color_data)
        return image
    

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

        if self.is_dark_mode:
            return self.img_dark_bordered_id if self.add_image_border else self.img_dark_id
        else:
            return self.img_bordered_id if self.add_image_border else self.img_id

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

        is_not_v1 = self.stats_version != 0
        has_user_uploaded_img = self.player_image_url or self.player_image_path
        has_special_edition = self.edition.is_not_empty
        has_expansion = self.expansion != 'FINAL'
        has_variable_spd_diff = self.is_variable_speed_00_01 and self.context in ['2000','2001']
        set_yr_plus_one_enabled = self.set_year_plus_one and self.context in ['2004','2005']
        return has_user_uploaded_img or has_expansion or is_not_v1 or has_special_edition or has_variable_spd_diff or self.has_custom_set_number or set_yr_plus_one_enabled or self.hide_team_logo


# ------------------------------------------------------------------------
# IMAGE EXPORTING
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
        if self.is_img_part_of_a_set:
            self.image_name = f'{self.set_number} {self.name}{img_name_suffix}.png'
        else:
            self.image_name = '{name}-{timestamp}.png'.format(name=self.name, timestamp=str(datetime.now()))
        
        if self.context in ['2002','2004','2005',sc.CLASSIC_SET, sc.EXPANDED_SET]:
            image = image.convert('RGB')

        save_img_path = os.path.join(self.card_img_output_folder_path, self.image_name)
        image.save(save_img_path, dpi=(300, 300), quality=100)
        
        if self.is_running_in_flask:
            flask_img_path = os.path.join(Path(os.path.dirname(__file__)).parent,'static', 'output', self.image_name)
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

        # FINAL IMAGES
        output_folder_paths = [os.path.join(os.path.dirname(__file__), 'output')]
        flask_output_path = os.path.join('static', 'output')
        if os.path.isdir(flask_output_path):
            output_folder_paths.append(flask_output_path)

        for folder_path in output_folder_paths:
            for item in os.listdir(folder_path):
                if item != self.image_name and item != '.gitkeep':
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
