from posixpath import join
import pandas as pd
import math
import requests
import operator
import os
import json
import statistics
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

from pathlib import Path
from io import BytesIO
from datetime import datetime, date
from bs4 import BeautifulSoup
from pprint import pprint
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from urllib.request import urlopen, Request
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from . import showdown_constants as sc
except ImportError:
    # USE LOCAL IMPORT
    import showdown_constants as sc

class ShowdownPlayerCardGenerator:

# ------------------------------------------------------------------------
# INIT

    def __init__(self, name, year, stats, context, expansion='BS', is_cooperstown=False, is_super_season=False, is_all_star_game=False, is_holiday=False, offset=0, player_image_url=None, player_image_path=None, card_img_output_folder_path='', set_number='001', test_numbers=None, run_stats=True, command_out_override=None, print_to_cli=False, show_player_card_image=False, is_running_in_flask=False):
        """Initializer for ShowdownPlayerCardGenerator Class"""

        # ASSIGNED ATTRIBUTES
        self.version = "2.6.4"
        self.name = stats['name'] if 'name' in stats.keys() else name
        self.bref_id = stats['bref_id'] if 'bref_id' in stats.keys() else ''
        self.year = str(year).upper()
        self.is_full_career = self.year == "CAREER"
        self.is_multi_year = len(self.year) > 4
        self.type_override = ''
        for type_str in ['(Pitcher)','(Hitter)']:
            if type_str in name:
                self.type_override = type_str
        if year.upper() == 'CAREER':
            self.year_list = [int(year) for year in stats['years_played']]
        elif '-' in year:
            # RANGE OF YEARS
            years = year.split('-')
            year_start = int(years[0].strip())
            year_end = int(years[1].strip())
            self.year_list = list(range(year_start,year_end+1))
        elif '+' in year:
            years = year.split('+')
            self.year_list = [int(x.strip()) for x in years]
        else:
            self.year_list = [int(year)]
        self.context = context
        self.expansion = expansion
        self.stats = stats
        # COMBINE BB AND HBP
        if 'HBP' in self.stats.keys():
            try:
                self.stats['BB'] = self.stats['BB'] + self.stats['HBP']
            except:
                print("ERROR COMBINING BB AND HBP")
        self.is_cooperstown = is_cooperstown
        self.is_super_season = is_super_season
        self.is_all_star_game = is_all_star_game
        self.is_holiday = is_holiday
        self.player_image_url = player_image_url
        self.player_image_path = player_image_path
        self.card_img_output_folder_path = card_img_output_folder_path if len(card_img_output_folder_path) > 0 else os.path.join(os.path.dirname(__file__), 'output')
        self.set_number = set_number
        self.test_numbers = test_numbers
        self.command_out_override = command_out_override
        self.is_running_in_flask = is_running_in_flask
        self.is_automated_image = False

        if run_stats:
            # DERIVED ATTRIBUTES
            self.is_pitcher = True if stats['type'] == 'Pitcher' else False
            self.team = stats['team_ID']

            # METADATA IS SET IN ANOTHER METHOD
            # POSITIONS_AND_DEFENSE, HAND, IP, SPEED, SPEED_LETTER
            self.__player_metadata(stats=stats)

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
            self.real_stats = self.stats_for_full_season(stats_per_400_pa=chart_results_per_400_pa)

            self.points = self.point_value(chart=self.chart,
                                            real_stats=self.real_stats,
                                            positions_and_defense=self.positions_and_defense,
                                            speed_or_ip=self.ip if self.is_pitcher else self.speed)
            if print_to_cli:
                self.print_player()

            if show_player_card_image or len(card_img_output_folder_path) > 0:
                self.player_image(show=True if show_player_card_image else False)

# ------------------------------------------------------------------------
# METADATA METHODS

    def __player_metadata(self, stats):
        """Parse all metadata (positions, hand, speed, ...) and assign to self.

        Args:
          stats: Dict of stats from Baseball Reference scraper

        Returns:
          None
        """

        # RAW METADATA FROM BASEBALL REFERENCE
        defensive_stats_raw = {k:v for (k,v) in stats.items() if 'Position' in k or 'dWAR' in k}
        hand_raw = stats['hand']
        innings_pitched_raw = float(stats['IP']) if self.is_pitcher else 0.0
        games_played_raw = int(stats['G'])
        games_started_raw = int(stats['GS']) if self.is_pitcher else 0
        saves_raw = int(stats['SV']) if self.is_pitcher else 0
        sprint_speed_raw = stats['sprint_speed']
        stolen_bases_raw = int(stats['SB']) if not self.is_pitcher else 0

        # DERIVED SB PER 650 PA (NORMAL SEASON)
        pa_to_650_ratio = int(stats['PA']) / 650.0
        stolen_bases_per_650_pa = stolen_bases_raw / pa_to_650_ratio

        # CALL METHODS AND ASSIGN TO SELF
        self.ip = self.__innings_pitched(innings_pitched=innings_pitched_raw, games=games_played_raw)
        self.positions_and_defense = self.__positions_and_defense(defensive_stats=defensive_stats_raw,
                                                                  games_played=games_played_raw,
                                                                  games_started=games_started_raw,
                                                                  saves=saves_raw)
        self.hand = self.__handedness(hand=hand_raw)
        self.speed, self.speed_letter = self.__speed(sprint_speed=sprint_speed_raw, stolen_bases=stolen_bases_per_650_pa)
        self.icons = self.__icons(awards=stats['award_summary'] if 'award_summary' in stats.keys() else '')

    def __positions_and_defense(self, defensive_stats, games_played, games_started, saves):
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

        # POPULATE POSITION DICTS
        # PARSE POSITION NAME, GAMES, AND TZ RATING AND CONVERT TO IN-GAME
        for position_index in range(1, num_positions+1):
            position_raw = defensive_stats['Position{}'.format(position_index)]
            # CHECK IF POSITION MATCHES PLAYER TYPE
            is_valid_position = self.is_pitcher == ('P' == position_raw)
            if is_valid_position:
                games_at_position = int(defensive_stats['gPosition{}'.format(position_index)])
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
                            is_drs_available = f'drsPosition{position_index}' in defensive_stats.keys()
                            is_d_war_available = 'dWAR' in defensive_stats.keys()
                            drs = int(defensive_stats['drsPosition{}'.format(position_index)]) if is_drs_available else None
                            tzr = int(defensive_stats['tzPosition{}'.format(position_index)])
                            dWar = float(defensive_stats['dWAR']) if is_d_war_available else None
                            if drs:
                                metric = 'drs'
                            elif tzr: 
                                metric = 'tzr'
                            else:
                                metric = 'dWAR'
                            defensive_rating = drs or tzr or dWar
                            in_game_defense = self.__convert_to_in_game_defense(position=position,rating=defensive_rating,metric=metric,games=games_at_position)
                        except:
                            in_game_defense = 0
                        positions_and_defense[position] = in_game_defense
                    else:
                        positions_and_defense[position] = 0

        # COMBINE ALIKE IN-GAME POSITIONS (LF/RF, OF, IF, ...)
        final_positions_in_game, final_position_games_played = self.__combine_like_positions(positions_and_defense, positions_and_games_played)

        # LIMIT TO ONLY 2 POSITIONS. CHOOSE BASED ON # OF GAMES PLAYED.
        position_limit = 2
        if len(final_positions_in_game.items()) > position_limit:
            sorted_positions = sorted(final_position_games_played.items(), key=operator.itemgetter(1), reverse=True)[0:position_limit]
            included_positions_list = [pos[0] for pos in sorted_positions]
            filtered_final_positions_in_game = {}
            for position, value in final_positions_in_game.items():
                # ONLY ADD IF THE POSITION IS IN THE TOP N BY GAMES PLAYED.
                if position in included_positions_list:
                    filtered_final_positions_in_game[position] = value
            final_positions_in_game = filtered_final_positions_in_game

        # ASSIGN DH IF POSITIONS DICT IS EMPTY
        if final_positions_in_game == {}:
            final_positions_in_game = {'DH': 0}

        return final_positions_in_game

    def __combine_like_positions(self, positions_and_defense, positions_and_games_played):
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

        return positions_and_defense, positions_and_games_played

    def __position_name_in_game(self, position, num_positions, position_appearances, games_played, games_started, saves):
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
            starter_threshold = 0.40
            if gsRatio > starter_threshold or self.ip > 4:
                # ASSIGN MINIMUM IP FOR STARTERS
                self.ip = 4 if self.ip < 4 else self.ip
                return 'STARTER'
            if saves > 10:
                return 'CLOSER'
            else:
                return 'RELIEVER'
        elif position_appearances < sc.NUMBER_OF_GAMES or (self.is_multi_year and ( (position_appearances / games_played) < 0.25 )):
            # IF POSIITION DOES NOT MEET REQUIREMENT, RETURN NONE
            return None
        elif position == 'DH' and num_positions > 1:
            # PLAYER MAY HAVE PLAYED AT DH, BUT HAS OTHER POSITIONS, SO DH WONT BE LISTED
            return None
        elif int(self.context) > 2001 and position == 'C':
            # CHANGE CATCHER POSITION NAME DEPENDING ON CONTEXT YEAR
            return 'CA'
        else:
            # RETURN BASEBALL REFERENCE STRING VALUE
            return position

    def __convert_to_in_game_defense(self, position, rating, metric, games):
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

        max_defense_for_position = sc.POSITION_DEFENSE_RANGE[self.context][position]
        defensive_range = MAX_SABER_FIELDING - MIN_SABER_FIELDING
        percentile = (rating-MIN_SABER_FIELDING) / defensive_range
        defense_raw = percentile * max_defense_for_position
        defense = round(defense_raw) if defense_raw > 0 else 0

        # ADD IN STATIC METRICS FOR 1B
        if position.upper() == '1B':
            if rating > sc.FIRST_BASE_PLUS_2_CUTOFF[metric]:
                defense = 2
            elif rating > sc.FIRST_BASE_PLUS_1_CUTOFF[metric]:
                defense = 1
            else:
                defense = 0
        
        # CAP DEFENSE IF GAMES PLAYED AT POSITION IS LESS THAN 80
        defense = int(max_defense_for_position) if games < 100 and defense > max_defense_for_position else defense

        return defense

    def __handedness(self, hand):
        """Get hand of player. Format to how card will display hand.

        Args:
          hand: Hand string from Baseball Reference. Will be "Left", "Right", or "Both".

        Returns:
          Formatted hand string (ex: "Bats R" or "RHP").
        """

        hand_first_letter = hand[0:1] if hand != 'Both' else 'S'
        hand_formatted_for_position = '{}HP'.format(hand_first_letter) if self.is_pitcher else 'Bats {}'.format(hand_first_letter)

        return hand_formatted_for_position

    def __innings_pitched(self, innings_pitched, games):
        """In game stamina for a pitcher. Position Player defaults to 0.

        Args:
          innings_pitched: The total innings pitched during the season.
          games: The total games played during the season.

        Returns:
          In game innings pitched ability.
        """

        ip = round(innings_pitched / games)
        ip = 1 if ip < 1 else ip

        return ip

    def __speed(self, sprint_speed, stolen_bases):
        """In game speed for a position player. Will use pure sprint speed
           if year is >= 2015, otherwise uses stolen bases. Pitcher defaults to 10.

        Args:
          sprint_speed: Average sprint speed according to baseballsavant.com.
                        IMPORTANT: Data is available for 2015+.
          stolen_bases: Number of steals during the season.

        Returns:
          In game speed ability, in game letter grade
        """

        if self.is_pitcher:
            # PITCHER DEFAULTS TO 10
            return 10, 'C'

        # IF FULL CAREER CARD, ONLY USE SPRINT SPEED IF PLAYER HAS OVER 35% of CAREER POST 2015
        pct_career_post_2015 = sum([1 if year >= 2015 else 0 for year in self.year_list]) / len(self.year_list)
        is_disqualied_career_speed = self.is_multi_year and pct_career_post_2015 < 0.35

        if sprint_speed is None or math.isnan(sprint_speed) or sprint_speed == '' or sprint_speed == 0 or is_disqualied_career_speed:
            # NO SPRINT SPEED AVAILABLE
            sb_range = sc.MAX_STOLEN_BASES - sc.MIN_STOLEN_BASES
            speed_percentile = sc.SB_MULTIPLIER[self.context] * (stolen_bases-sc.MIN_STOLEN_BASES) / sb_range
            max_speed_in_game = 18.0
        else:
            # SPRINT SPEED IS AVAILABLE
            sprint_speed_range = sc.MAX_SPRINT_SPEED - sc.MIN_SPRINT_SPEED
            speed_percentile = (sprint_speed-sc.MIN_SPRINT_SPEED) / sprint_speed_range
            max_speed_in_game = 25.0

        speed_raw = int(round(speed_percentile * max_speed_in_game))
        # CHANGE OUTLIERS
        speed = 8 if speed_raw < 8 else speed_raw
        speed = 27 if speed_raw > 27 else speed

        c_speeed_cutoff = 13 if self.context == '2002' else 12
        if speed < c_speeed_cutoff:
            letter = 'C'
        elif speed < 18:
            letter = 'B'
        else:
            letter = 'A'

        # IF 2000 OR 2001, SPEED VALUES CAN ONLY BE 10,15,20
        if self.context in ['2000','2001']:
            spd_letter_to_number = {'A': 20,'B': 15,'C': 10}
            speed = spd_letter_to_number[letter]

        return speed, letter

    def __icons(self,awards):
        """Converts awards_summary and other metadata fields into in game icons.

        Args:
          awards: String containing list of seasonal accolades.

        Returns:
          List of in game icons as strings.
        """

        # ICONS ONLY APPLY TO 2003+
        if int(self.context) < 2003:
            return []

        awards_string = '' if awards is None else str(awards).upper()
        awards_list = awards_string.split(',')
        # ICONS FROM BREF AWARDS FIELD
        awards_to_icon_map = {
            'SS': 'S',
            'GG': 'G',
            'MVP-1': 'V',
            'CYA-1': 'CY',
            'ROY-1': 'RY'
        }
        icons = []
        for award, icon in awards_to_icon_map.items():
            if award in awards_list:
                if not (self.is_pitcher and award in ['SS', 'GG']):
                    icons.append(icon)

        # DATA DRIVEN ICONS
        if self.is_pitcher:
            # 20, K
            for stat, icon in {"W": "20", "SO": "K"}.items():
                key = f"is_above_{stat.lower()}_threshold"
                if key in self.stats.keys():
                    if self.stats[key] == True:
                        icons.append(icon)
            # RP
            if 'is_sv_leader' in self.stats.keys():
                if self.stats['is_sv_leader'] == True:
                    icons.append('RP')
        else:
            # HR, SB
            for stat in ['HR', 'SB']:
                key = f"is_above_{stat.lower()}_threshold"
                if key in self.stats.keys():
                    if self.stats[key] == True:
                        icons.append(stat)

        # ROOKIE ICON
        rookie_key = 'is_rookie'
        if rookie_key in self.stats.keys():
            if self.stats[rookie_key] == True:
                icons.append('R')

        return icons

    def player_type(self):
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

# ------------------------------------------------------------------------
# COMMAND / OUTS METHODS

    def __top_accurate_command_out_combos(self, obp, num_results):
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
            accuracy = self.__relative_pct_accuracy(actual=obp, measurement=predicted_obp)
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

    def __onbase_control_outs(self, playercommand=0, playerOuts=0):
        """Give information needed to perform calculations of results.
           These numbers are needed to predict obp, home_runs, ...

        Args:
          command: The Onbase or Control number of player.
          outs: The number of out results on the player's chart.

        Returns:
          Dict object with onbase, control, pitcher outs, hitter outs
        """

        onbase_baseline = sc.BASELINE_HITTER[self.context]['command'] if self.test_numbers is None else self.test_numbers[0]
        hitter_outs_baseline = sc.BASELINE_HITTER[self.context]['outs'] if self.test_numbers is None else self.test_numbers[1]
        control_baseline = sc.BASELINE_PITCHER[self.context]['command'] if self.test_numbers is None else self.test_numbers[0]
        pitcher_outs_baseline = sc.BASELINE_PITCHER[self.context]['outs'] if self.test_numbers is None else self.test_numbers[1]

        return {
            'onbase': playercommand if not self.is_pitcher else onbase_baseline,
            'hitterOuts': playerOuts if not self.is_pitcher else hitter_outs_baseline,
            'control': playercommand if self.is_pitcher else control_baseline,
            'pitcherOuts': playerOuts if self.is_pitcher else pitcher_outs_baseline
        }

    def opponent_stats_for_calcs(self, command):
        """Convert __onbase_control_outs info to be specific to self.
           Used to derive:
             1. opponent_chart
             2. my_advantages_per_20
             3. opponent_advantages_per_20

        Args:
          command: The Onbase or Control number of player.

        Returns:
          Tuple with opponent_chart, my_advantages_per_20, opponent_advantages_per_20
        """

        if not self.is_pitcher:
            opponent_chart = sc.BASELINE_PITCHER[self.context]
            my_advantages_per_20 = command-self.__onbase_control_outs()['control']
            opponent_advantages_per_20 = 20 - my_advantages_per_20
        else:
            opponent_chart = sc.BASELINE_HITTER[self.context]
            opponent_advantages_per_20 = self.__onbase_control_outs()['onbase']-command
            my_advantages_per_20 = 20 - opponent_advantages_per_20

        return opponent_chart, my_advantages_per_20, opponent_advantages_per_20

    def __obp_for_command_outs(self, command_out_matchup):
        """Calc OBP for command out matchup

        Args:
          command_out_matchup: Dictionary of onbase, control, outs from hitter and pitcher

        Returns:
          Tuple with opponent_chart, my_advantages_per_20, opponent_advantages_per_20
        """
        return self.__pct_rate_for_result(
            onbase = command_out_matchup['onbase'],
            control = command_out_matchup['control'],
            num_results_hitter_chart = 20-command_out_matchup['hitterOuts'],
            num_results_pitcher_chart = 20-command_out_matchup['pitcherOuts']
        )

# ------------------------------------------------------------------------
# CHART METHODS

    def __most_accurate_chart(self, command_out_combos, stats_per_400_pa, offset):
        """Compare accuracy of all the command/outs combinations

        Args:
          command_out_combos: List of command/out tuples to test.
          stats_per_400_pa: Dict with number of results for a given
                            category per 400 PA (ex: {'hr_per_400_pa': 23.65})

        Returns:
          The dictionary containing stats for the most accurate command/out
          combination.
          A dictionary containing real life metrics (obp, slg, ...) per 400 PA.
        """

        chart_and_accuracies = []

        for command_out_tuple in command_out_combos:
            command = command_out_tuple[0]
            outs = command_out_tuple[1]
            chart, accuracy, real_stats = self.__chart_with_accuracy(
                                            command=command,
                                            outs=outs,
                                            stats_for_400_pa=stats_per_400_pa
                                          )
            chart_and_accuracies.append( (command_out_tuple, chart, accuracy, real_stats) )

        chart_and_accuracies.sort(key=operator.itemgetter(2),reverse=True)
        best_chart = chart_and_accuracies[offset][1]
        self.top_command_out_combinations = [(ca[0],ca[2]) for ca in chart_and_accuracies]
        real_stats_for_best_chart = chart_and_accuracies[offset][3]

        return best_chart, real_stats_for_best_chart

    def __chart_with_accuracy(self, command, outs, stats_for_400_pa):
        """Create Player's chart and compare back to input stats.

        Args:
          command: Onbase (Hitter) or Control (Pitcher) of the Player.
          outs: Number of Outs on the Player's chart.
          stats_per_400_pa: Dict with number of results for a given
                            category per 400 PA (ex: {'hr_per_400_pa': 23.65})

        Returns:
          - Dictionary for Player Chart ({'so': 1, 'hr': 2, ...})
          - Accuracy of chart compared to original input.
          - Dict of Player's chart converted to real stat output.
        """

        # NEED THE OPPONENT'S CHART TO CALCULATE NUM OF RESULTS FOR RESULT
        opponent_chart, my_advantages_per_20, opponent_advantages_per_20 = self.opponent_stats_for_calcs(command)

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
                chart_results = outs if key == 'so' and chart_results > outs else chart_results
                chart_results = chart_results if chart_results > 0 else 0
                # WE ROUND THE PREDICTED RESULTS (2.4 -> 2, 2.5 -> 3)
                if self.is_pitcher and key == 'hr' and chart_results < 1.0:
                    # TRADITIONAL ROUNDING CAUSES TOO MANY PITCHER HR RESULTS
                    # CHANGE TO ROUNDING FROM > .85 INSTEAD OF 0.5
                    chart_results_decimal = chart_results % 1
                    rounded_results = round(chart_results) if chart_results_decimal > 0.95 else math.floor(chart_results)
                else:                    
                    rounded_results = round(chart_results)
                # PITCHERS SHOULD ALWAYS GET 0 FOR 3B
                rounded_results = 0 if self.is_pitcher and key == '3b' else rounded_results
                # CHECK FOR BARRY BONDS EFFECT (HUGE WALK)
                rounded_results = 12 if key == 'bb' and rounded_results > 13 else rounded_results
                # MAX HR RESULTS AT 10
                rounded_results = 10 if key == 'hr' and rounded_results > 10 else rounded_results
                chart[key] = rounded_results

        # FILL "OUT" CATEGORIES (PU, GB, FB)
        # MAKE SURE 'SO' DON'T FILL UP MORE THAN 5 SLOTS IF HITTER. THIS MAY CAUSE SOME STATISTICAL ANOMILIES IN MODERN YEARS.
        max_hitter_so = sc.MAX_HITTER_SO_RESULTS[self.context]
        chart['so'] = max_hitter_so if not self.is_pitcher and chart['so'] > max_hitter_so else chart['so']
        out_slots_remaining = outs - float(chart['so'])
        chart['pu'], chart['gb'], chart['fb'] = self.__out_results(
                                                    stats_for_400_pa['GO/AO'],
                                                    stats_for_400_pa['IF/FB'],
                                                    out_slots_remaining
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
        in_game_stats_for_400_pa = self.chart_to_results_per_400_pa(chart,my_advantages_per_20,opponent_chart,opponent_advantages_per_20)
        weights = sc.CHART_CATEGORY_WEIGHTS[self.context][self.player_type()]
        accuracy, categorical_accuracy, above_below = self.accuracy_between_dicts(actuals_dict=stats_for_400_pa,
                                                                                  measurements_dict=in_game_stats_for_400_pa,
                                                                                  weights=weights,
                                                                                  only_use_weight_keys=True)
        
        # QA: CHANGE ACCURACY TO 0 IF CHART DOESN'T ADD UP TO 20
        is_over_20 = sum([v for k, v in chart.items() if k not in ['command','outs', 'sb'] ]) > 20
        accuracy = 0.0 if is_over_20 else accuracy

        return chart, accuracy, in_game_stats_for_400_pa

    def __out_results(self, gb_pct, popup_pct, out_slots_remaining):
        """Determine distribution of out results for Player.

        Args:
          gb_pct: Percent Ground Outs vs Air Outs.
          popup_pct: Percent hitting into a popup.
          out_slots_remaining: Total # Outs - SO

        Returns:
          Tuple of PU, GB, FB out result ints.
        """


        if out_slots_remaining > 0:
            # MULTIPLIERS SERVE TO CORRECT TOWARDS WOTC
            # REPLACE HAVING DEFAULT FOR OPPONENT CHART
            type = 'pitcher' if self.is_pitcher else 'hitter'
            gb_multi = sc.GB_MULTIPLIER[type][self.context]
            # SPLIT UP REMAINING SLOTS BETWEEN GROUND AND AIR OUTS
            gb_outs = round((out_slots_remaining / (gb_pct + 1)) * gb_pct * gb_multi)
            air_outs = out_slots_remaining - gb_outs
            # FOR PU, ADD A MULTIPLIER TO ALIGN MORE WITH OLD SCHOOL CARDS
            pu_multiplier = sc.PU_MULTIPLIER[self.context]
            pu_outs = 0.0 if not self.is_pitcher else math.ceil(air_outs*popup_pct*pu_multiplier)
            pu_outs = air_outs if pu_outs > air_outs else pu_outs
            fb_outs = air_outs-pu_outs
        else:
            fb_outs = 0.0
            pu_outs = 0.0
            gb_outs = 0.0

        return pu_outs, gb_outs, fb_outs

    def __single_and_single_plus_results(self, remaining_slots, sb, command):
        """Fill 1B and 1B+ categories on chart.

        Args:
          remaining_slots: Remaining slots out of 20.
          sb: Stolen bases per 400 PA
          command: Player's Onbase number

        Returns:
          Tuple of 1B, 1B+ result ints.
        """

        # Pitcher has no 1B+
        if self.is_pitcher:
            return remaining_slots, 0

        # Divide stolen bases per 400 PA by a scaler based on Onbase #
        is_context_old_sets = int(self.context) < 2002
        min_onbase = 4 if is_context_old_sets else 7
        max_onbase = 12 if is_context_old_sets else 16
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

    def __chart_categories(self):
        """Fill 1B and 1B+ categories on chart.

        Args:
          remaining_slots: Remaining slots out of 20.
          sb: Stolen bases per 400 PA

        Returns:
          Tuple of 1B, 1B+ result ints.
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

    def ranges_for_chart(self, chart, dbl_per_400_pa, trpl_per_400_pa, hr_per_400_pa):
        """Converts chart integers to Range Strings ({1B: 3} -> {'1B': '11-13'})

        Args:
          chart: Dict with # of slots per chart result category
          dbl_per_400_pa: Number of 2B results every 400 PA
          trpl_per_400_pa: Number of 3B results every 400 PA
          hr_per_400_pa: Number of HR results every 400 PA

        Returns:
          Dict of ranges for each result category.
        """

        categories = self.__chart_categories()
        current_chart_index = 1
        chart_ranges = {}
        is_post_2001 = int(self.context) > 2001
        for category in categories:
            category_results = int(chart[category])
            range_end = current_chart_index + category_results - 1

            # HANDLE RANGES > 20
            if is_post_2001 and range_end >= 20 and self.is_pitcher:
                add_to_1b, num_of_results_2b = self.__calculate_ranges_over_20(dbl_per_400_pa, hr_per_400_pa)
                # DEFINE OVER 20 RANGES
                if category == '1b':
                    category_results += add_to_1b
                    range_end = current_chart_index + category_results - 1
                elif category == '2b':
                    category_results += num_of_results_2b
                    range_end = current_chart_index + category_results - 1
            
            # HANDLE ERRORS WITH SMALL SAMPLE SIZE 2000/2001 FOR SMALL ONBASE
            if not is_post_2001 and range_end > 20:
                range_end = 20
                
            if category.upper() == 'HR' and is_post_2001:
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
        if self.context in ['2002','2003','2004','2005'] and int(chart['hr']) < 1 and not self.is_pitcher:
            chart_ranges = self.__hitter_chart_above_20(chart, chart_ranges, dbl_per_400_pa, trpl_per_400_pa, hr_per_400_pa)

        return chart_ranges

    def __calculate_ranges_over_20(self, dbl_per_400_pa, hr_per_400_pa):
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

    def __hitter_chart_above_20(self, chart, chart_ranges, dbl_per_400_pa, trpl_per_400_pa, hr_per_400_pa):
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
                    chart_ranges['1b Range'] = range_updated
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

    def __stats_per_n_pa(self,plate_appearances,stats):
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
        # GO/AO
        try:
            go_ao = float(stats['GO/AO'])
        except:
            # DEFAULT TO 1.0 FOR UNAVAILABLE YEARS
            go_ao = 1.0

        # POPULATE DICT WITH VALUES UNCHANGED BY SHIFT IN PA
        stats_for_n_pa = {
            'PA': plate_appearances,
            'pct_of_{}_pa'.format(plate_appearances): pct_of_n_pa,
            'slugging_perc': float(stats['slugging_perc']),
            'onbase_perc': float(stats['onbase_perc']),
            'batting_avg': float(stats['batting_avg']),
            'IF/FB': float(stats['IF/FB']),
            'GO/AO': go_ao
        }

        # ADD RESULT OCCURANCES PER N PA
        chart_result_categories = ['SO','BB','1B','2B','3B','HR','SB','H']
        for category in chart_result_categories:
            key = '{}_per_{}_pa'.format(category.lower(), plate_appearances)
            stats_for_n_pa[key] = int(stats[category]) / pct_of_n_pa

        return stats_for_n_pa

    def __pct_rate_for_result(self, onbase, control, num_results_hitter_chart, num_results_pitcher_chart, hitter_denom_adjust=0.0,pitch_denom_adjust=0.0):
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

    def chart_to_results_per_400_pa(self, chart, my_advantages_per_20, opponent_chart, opponent_advantages_per_20):
        """Predict real stats given Showdown in game chart.

        Args:
          chart: Dict for chart of Player.
          my_advantages_per_20: Int number of advantages my Player gets out of 20 (i.e. 5).
          opponent_chart: Dict for chart of baseline opponent.
          opponent_advantages_per_20: Int number of advantages opponent gets out of 20 (i.e. 15).

        Returns:
          Dict with stats per 400 Plate Appearances.
        """

        # MATCHUP VALUES
        command_out_matchup = self.__onbase_control_outs(chart['command'],chart['outs'])
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

    def __result_occurances_per_400_pa(self, my_results, opponent_results, my_advantages_per_20, opponent_advantages_per_20):
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

    def __slugging_pct(self,ab,singles,doubles,triples,homers):
        """Calculate Slugging Pct"""
        return (singles + (2 * doubles) + (3 * triples) + (4 * homers)) / ab

    def stats_for_full_season(self, stats_per_400_pa):
        """Predicted season stats (650 PA)

        Args:
          stats_per_400_pa: Stats and Ratios weighted for every 400 plate appearances.

        Returns:
          Dict with stats for 650 PA.
        """

        stats_per_650_pa = {}

        for category, value in stats_per_400_pa.items():
            if 'per_400_pa' in category:
                # CONVERT TO 650 PA
                stats_per_650_pa[category.replace('400', '650')] = value * 650 / 400
            else:
                # PCT VALUE (OBP, SLG, BA, ...)
                stats_per_650_pa[category] = value

        return stats_per_650_pa

# ------------------------------------------------------------------------
# PLAYER VALUE METHODS

    def point_value(self, chart, real_stats, positions_and_defense, speed_or_ip):
        """Derive player's value. Uses constants to compare against other cards in set.

        Args:
          chart: Dict containing number of results per result category ({'1b': 5, 'hr': 3}).
          real_stats: Dict with real metrics (obp, ba, ...) for 650 PA (~ full season)
          positions_and_defense: Dict with all valid positions and their corresponding defensive rating.
          speed_or_ip: In game speed ability or innings pitched.

        Returns:
          Points that the player is worth.
        """

        points = 0

        player_category = self.player_type()

        # PARSE POSITION MULTIPLIER
        command_outs = f"{str(self.chart['command'])}-{str(self.chart['outs'])}"
        pts_multiplier_dict = sc.POINTS_COMMAND_OUT_MULTIPLIER[self.context]
        pts_multiplier = pts_multiplier_dict[command_outs] if command_outs in pts_multiplier_dict.keys() else 1.0

        # SLASH LINE VALUE
        allow_negatives = sc.POINTS_ALLOW_NEGATIVE[self.context][player_category]
        self.obp_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['onbase'] \
                          * self.stat_percentile(stat=real_stats['onbase_perc'],
                                                 min_max_dict=sc.ONBASE_PCT_RANGE[self.context][player_category],
                                                 is_desc=self.is_pitcher,
                                                 allow_negative=allow_negatives) \
                          * pts_multiplier
        self.ba_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['average'] \
                         * self.stat_percentile(stat=real_stats['batting_avg'],
                                                min_max_dict=sc.BATTING_AVG_RANGE[self.context][player_category],
                                                is_desc=self.is_pitcher,
                                                allow_negative=allow_negatives) \
                         * pts_multiplier
        self.slg_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['slugging'] \
                          * self.stat_percentile(stat=real_stats['slugging_perc'],
                                                 min_max_dict=sc.SLG_RANGE[self.context][player_category],
                                                 is_desc=self.is_pitcher,
                                                 allow_negative=allow_negatives) \
                          * pts_multiplier
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
        self.spd_ip_points = spd_ip_weight \
                             * self.stat_percentile(stat=speed_or_ip,
                                                    min_max_dict=spd_ip_range,
                                                    is_desc=False,
                                                    allow_negative=allow_negatives_speed_ip)
        if not self.is_pitcher:
            # ONLY HITTERS HAVE HR ADD TO POINTS
            self.hr_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['home_runs'] \
                             * self.stat_percentile(stat=real_stats['hr_per_650_pa'],
                                                    min_max_dict=sc.HR_RANGE[self.context],
                                                    is_desc=self.is_pitcher,
                                                    allow_negative=allow_negatives) \
                             * pts_multiplier
            # AVERAGE POINT VALUE ACROSS POSITIONS
            defense_points = 0
            for position, fielding in positions_and_defense.items():
                if position != 'DH':
                    percentile = fielding / sc.POSITION_DEFENSE_RANGE[self.context][position]
                    position_pts = percentile * sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['defense']
                    position_pts = position_pts * sc.POINTS_POSITIONAL_DEFENSE_MULTIPLIER[self.context][position]
                    defense_points += position_pts
            use_avg = list(positions_and_defense.keys()) == ['CF', 'LF/RF'] or list(positions_and_defense.keys()) == ['LF/RF', 'CF']
            num_positions = len(positions_and_defense.keys()) if len(positions_and_defense.keys()) > 0 else 1
            avg_points_per_position = defense_points / (num_positions if num_positions < 2 or use_avg else (num_positions * 2 / 3))
            self.defense_points = avg_points_per_position

        # CLOSER BONUS (00 ONLY)
        apply_closer_bonus = 'CLOSER' in self.positions_and_defense.keys() and self.context == '2000'
        self.points_bonus = 25 if apply_closer_bonus else 0

        # ICONS (03+)
        icon_pts = 0
        if self.context in ['2003','2004','2005'] and len(self.icons) > 0:
            for icon in self.icons:
                icon_pts += sc.POINTS_ICONS[self.context][str(icon)]
        self.icon_points = icon_pts

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
            multi_inning_points_multiplier = self.ip * (sc.POINTS_RELIEVER_IP_MULTIPLIER[self.context] if is_multi_inning else 1.0)
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
                self.out_dist_points = pt_weight_gb * percentile_gb
                points += self.out_dist_points
                self.chart_pct_gb = pct_gb
            else:
                self.out_dist_points = 0
                self.chart_pct_gb = pct_gb

        # POINTS ARE ALWAYS ROUNDED TO TENTH
        points_to_nearest_tenth = int(round(points,-1))

        # POINTS CANNOT BE < 10
        points_final = 10 if points_to_nearest_tenth < 10 else points_to_nearest_tenth

        return points_final

    def stat_percentile(self, stat, min_max_dict, is_desc=False, allow_negative=False):
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

    def __normalize_points_towards_median(self, points):
        """Normalize points for subset on players towards the median.

        Args:
          points: Current Points attributed to player

        Returns:
          Updated PTS total for player after normalization.
        """

        # NORMALIZE SCORE ACROSS MEDIAN
        is_starting_pitcher = self.player_type() == 'starting_pitcher'
        is_relief_pitcher = self.player_type() == 'relief_pitcher'
        reliever_normalizer = sc.POINTS_NORMALIZER_RELIEVER_MULTIPLIER[self.context] if is_relief_pitcher else 1.0
        median = 310 / reliever_normalizer
        upper_limit = 800 if int(self.context) < 2002 else 800
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
            lower_multiplier = sc.POINTS_NORMALIZER_MULTIPLIER[self.context][self.player_type()]
            multiplier = percentile * (upper_multiplier - lower_multiplier) + lower_multiplier

            # APPLY THIS TO OFFENSIVE STATS
            self.obp_points = self.obp_points * multiplier
            self.ba_points = self.ba_points * multiplier
            self.slg_points = self.slg_points * multiplier

            if not self.is_pitcher:
                self.hr_points = self.hr_points * multiplier

            self.points_normalizer = multiplier
            return self.obp_points + self.ba_points + self.slg_points + self.spd_ip_points + self.points_bonus + self.icon_points
        else:
            self.points_normalizer = 1.0
            return points

# ------------------------------------------------------------------------
# GENERIC METHODS

    def accuracy_between_dicts(self, actuals_dict, measurements_dict, weights={}, all_or_nothing=[], only_use_weight_keys=False):
        """Compare two dictionaries of numbers to get overall difference

        Args:
          actuals_dict: First Dictionary. Use this dict to get keys to compare.
          measurements_dict: Second Dictionary.
          weights: X times to count certain category (ex: 3x for command)
          all_or_nothing: List of category names to compare as a boolean 1 or 0 instead
                          of pct difference.
          only_use_weight_keys: Bool for whether to only count an accuracy there is a weight associated
        Returns:
          Float with accuracy and Dict with accuracy per key. Also returns categorical accuracy and differences.
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
                    command_out_matchup = self.__onbase_control_outs(command, outs)
                    value1 = self.__obp_for_command_outs(command_out_matchup)
                    # VALUE 2
                    co_split = value2.split('-')
                    command = int(co_split[0])
                    outs = int(co_split[1])
                    command_out_matchup = self.__onbase_control_outs(command, outs)
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

    def __relative_pct_accuracy(self, actual, measurement):
        """ CALCULATE ACCURACY BETWEEN 2 NUMBERS"""

        denominator = actual

        # ACCURACY IS 100% IF BOTH ARE EQUAL (IF STATEMENT TO AVOID 0'S)
        if actual == measurement:
            return 1

        # CAN'T DIVIDE BY 0, SO USE OTHER VALUE AS BENCHMARK
        if actual == 0:
            denominator = measurement

        return (actual - abs(actual - measurement) ) / denominator

    def accuracy_against_wotc(self, wotc_card_dict, is_pts_only=False):
        """Compare My card output against official WOTC card.

        Args:
          wotc_card_dict: Dictionary with stats per category from wizards output.
          ignore_volatile_categories: If True, ignore individual out result categories and single+
          is_pts_only: Boolean flag to enabled testing for only point value.

        Returns:
          Float with overall accuracy and Dict with accuracy per stat category.
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

# ------------------------------------------------------------------------
# OUTPUT PLAYER METHODS

    def print_player(self):
        """Prints out self in readable format.
           Prints out the following:
            - Player Metadata
            - Player Chart
            - Predicted Real Life Stats

        Args:
          None

        Returns:
          String of output text for player info + stats
        """

        # POSITION
        positions_string = ''
        for position,fielding in self.positions_and_defense.items():
            positions_string += '{}+{}   '.format(position,fielding) if not self.is_pitcher else position

        # IP / SPEED
        ip_or_speed = 'Speed {} ({})'.format(self.speed_letter,self.speed) if not self.is_pitcher else '{} IP'.format(self.ip)

        # ICON(S)
        icon_string = ''
        for icon in self.icons:
            icon_string += '{}  '.format(icon)

        # CHART
        chart_string = ''
        for category in self.__chart_categories():
            range = self.chart_ranges['{} Range'.format(category)]
            chart_string += '{}: {}\n'.format(category.upper(), range)

        # SLASH LINE
        slash_categories = [('batting_avg', ' BA'),('onbase_perc', 'OBP'),('slugging_perc', 'SLG')]
        slash_as_string = ''
        for key, cleaned_category in slash_categories:
            showdown_stat_str = '{}: {}'.format(cleaned_category,str(round(self.real_stats[key],3)).replace('0.','.'))
            real_stat_str = '{}: {}'.format(cleaned_category,str(round(self.stats[key],3)).replace('0.','.'))
            slash_as_string += '{:<12}{:>12}\n'.format(showdown_stat_str,real_stat_str)

        # RESULT LINE
        real_life_pa = int(self.stats['PA'])
        real_life_pa_ratio = int(self.stats['PA']) / 650.0
        results_as_string = '{:<12}{:>12}\n'.format(' PA: {}'.format(real_life_pa),' PA: {:>4}'.format(real_life_pa))
        result_categories = [
            ('1b_per_650_pa', '1B'),
            ('2b_per_650_pa', '2B'),
            ('3b_per_650_pa', '3B'),
            ('hr_per_650_pa', 'HR'),
            ('bb_per_650_pa', 'BB'),
            ('so_per_650_pa', 'SO')
        ]
        for key, cleaned_category in result_categories:
            showdown_stat_str = ' {}: {}'.format(cleaned_category,int(round(self.real_stats[key]) * real_life_pa_ratio))
            real_stats_str = ' {}: {:>4}'.format(cleaned_category,self.stats[cleaned_category])
            results_as_string += '{:<12}{:>12}\n'.format(showdown_stat_str, real_stats_str)

        # DISPLAY INDIVIDUAL PT CATEGORIES
        pt_category_string = 'OBP:{obp}  BA:{ba}  SLG:{slg}  SPD/IP:{spd_ip}'.format(
            obp = round(self.obp_points,2),
            ba = round(self.ba_points,2),
            slg = round(self.slg_points,2),
            spd_ip = round(self.spd_ip_points,2)
        )
        if self.points_bonus > 0:
            pt_category_string += f"  BONUS:{self.points_bonus}"
        if self.icon_points != 0:
            pt_category_string += f"  ICONS:{self.icon_points}"
        if not self.is_pitcher:
            pt_category_string += '  HR:{hr}  DEF:{defense}'.format(hr=self.hr_points,defense=self.defense_points)
        else:
            pt_category_string += f"  OUT_DIST: {round(self.out_dist_points,2)}"
        if self.points_normalizer < 1.0:
            pt_category_string += f"  NORMALIZER: {round(self.points_normalizer,2)}"
        # NOT USING DOCSTRING FOR FORMATTING REASONS
        card_as_string = (
            '***********************************************\n' +
            '{name} ({year}) ({team})\n' +
            '{context} {expansion} Card\n' +
            '\n' +
            '{positions}\n' +
            '{hand}\n' +
            '{ip_or_speed}\n' +
            '{icons}\n' +
            '{points} PT.\n' +
            '{pts_per_category}\n' +
            '\n' +
            '{command_header}: {command}\n' +
            '{chart}\n' +
            '\n' +
            'Statline\n' +
            '\n' +
            'Showdown            Real\n' +
            '----------     ---------\n' +
            '{slash_line}\n' +
            '{results}\n' +
            '***********************************************'
        ).format(
            name = self.name,
            year = self.year,
            team = self.team,
            context = self.context,
            expansion = self.expansion,
            positions = positions_string,
            hand = self.hand,
            ip_or_speed = ip_or_speed,
            icons = icon_string,
            points = str(self.points),
            pts_per_category = pt_category_string,
            command_header = 'CONTROL' if self.is_pitcher else 'ONBASE',
            command=self.chart['command'],
            chart = chart_string,
            slash_line = slash_as_string,
            results = results_as_string
        )
        print(card_as_string)
        return card_as_string

    def player_data_for_html_table(self):
        """ Provides data needed to populate the statline shown on the
            showdownbot.com webpage.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of a category,
          real stat, and in-game Showdown estimated stat.
        """

        final_player_data = []

        # SLASH LINE
        slash_categories = [('batting_avg', 'BA'),('onbase_perc', 'OBP'),('slugging_perc', 'SLG')]
        for key, cleaned_category in slash_categories:
            in_game = f"{float(round(self.real_stats[key],3)):.3f}".replace('0.','.')
            actual = f"{float(self.stats[key]):.3f}".replace('0.','.')
            final_player_data.append([cleaned_category,actual,in_game])

        # PLATE APPEARANCES
        real_life_pa = int(self.stats['PA'])
        real_life_pa_ratio = int(self.stats['PA']) / 650.0
        final_player_data.append(['PA', str(real_life_pa), str(real_life_pa)])

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
            in_game = str(int(round(self.real_stats[key]) * real_life_pa_ratio))
            actual = str(self.stats[cleaned_category])
            final_player_data.append([cleaned_category,actual,in_game])
        
        # NON COMPARABLE STATS
        category_list = ['earned_run_avg', 'bWAR'] if self.is_pitcher else ['SB', 'onbase_plus_slugging_plus', 'dWAR', 'bWAR']
        for category in category_list:
            if category in self.stats.keys():
                stat = str(self.stats[category])
                short_name_map = {
                    'onbase_plus_slugging_plus': 'OPS+',
                    'bWAR': 'bWAR',
                    'dWAR': 'dWAR',
                    'SB': 'SB',
                    'earned_run_avg': 'ERA',
                }
                short_category_name = short_name_map[category]
                final_player_data.append([short_category_name,stat,'N/A'])


        return final_player_data

    def points_data_for_html_table(self):
        """Provides data needed to populate the points breakdown shown on the
           showdownbot.com webpage.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of a pts category, stat and value.
        """
        
        if self.player_type() == 'relief_pitcher' and self.ip > 1:
            spd_or_ip = ['IP', str(self.ip), f"{self.multi_inning_points_multiplier}x"]
        else:
            spd_or_ip = [
                'IP' if self.is_pitcher else 'SPD', 
                str(self.ip if self.is_pitcher else self.speed),
                str(round(self.spd_ip_points))
            ]
        pts_data = [
            ['BA', str(round(self.real_stats['batting_avg'],3)).replace("0.","."), str(round(self.ba_points))],
            ['OBP', str(round(self.real_stats['onbase_perc'],3)).replace("0.","."), str(round(self.obp_points))],
            ['SLG', str(round(self.real_stats['slugging_perc'],3)).replace("0.","."), str(round(self.slg_points))],
            spd_or_ip,

        ]

        if not self.is_pitcher:
            pts_data.append(['HR (650 PA)', str(round(self.real_stats['hr_per_650_pa'])), str(round(self.hr_points))])
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
            pts_data.append(['ICONS', ','.join(self.icons), str(round(self.icon_points))])
        if self.points_normalizer < 1.0:
            pts_data.append(['NORMALIZER', 'N/A', str(round(self.points_normalizer,2))])
        
        
        pts_data.append(['TOTAL', '', self.points])

        return pts_data

    def accuracy_data_for_html_table(self):
        """Provides data needed to populate the accuracy breakdown shown on the
           showdownbot.com webpage.

        Args:
          None

        Returns:
          Multi-Dimensional list where each row is a list of a offset and accuracy value.
        """
        accuracy_data = []
        for index, co_accuracy_tuple in enumerate(self.top_command_out_combinations):
            command_out_tuple = co_accuracy_tuple[0]
            command = command_out_tuple[0]
            outs = command_out_tuple[1]
            accuracy = co_accuracy_tuple[1]
            accuracy_data.append([str(index + 1), f"{command}", f"{outs}", f"{round(100 * accuracy, 2)}%"])

        return accuracy_data

    def __player_metadata_summary_text(self, is_horizontal=False):
        """Creates a multi line string with all player metadata for card output.

        Args:
          is_horizontal: Optional boolean for horizontally formatted text (04/05)

        Returns:
          String of output text for player info + stats
        """
        positions_string = self.__position_and_defense_as_string(is_horizontal=is_horizontal)

        ip = '{} IP'.format(self.ip) if int(self.context) < 2004 else 'IP {}'.format(self.ip)
        speed = 'Speed {} ({})'.format(self.speed_letter,self.speed)
        ip_or_speed = speed if not self.is_pitcher else ip
        if is_horizontal:
            final_text = '{points} PT.   {item2}   {hand}   {item4}'.format(
                points=self.points,
                item2=positions_string if self.is_pitcher else speed,
                hand=self.hand,
                item4=ip if self.is_pitcher else positions_string,
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

    def __position_and_defense_as_string(self, is_horizontal=False):
        """Creates a single line string with positions and defense.

        Args:
          is_horizontal: Optional boolean for horizontally formatted text (04/05)

        Returns:
          String of output text for player's defensive stats
        """
        positions_string = ''
        position_num = 1

        if self.positions_and_defense == {}:
            # THE PLAYER IS A DH
            positions_string = '–'
        else:
            for position,fielding in self.positions_and_defense.items():
                if self.is_pitcher:
                    positions_string += position
                elif position == 'DH':
                    positions_string += '—'
                else:
                    is_last_element = position_num == len(self.positions_and_defense.keys())
                    positions_separator = ' ' if is_horizontal else '\n'
                    positions_string += '{} +{}{}'.format(position,fielding,'' if is_last_element else positions_separator)
                position_num += 1
        
        return positions_string

# ------------------------------------------------------------------------
# IMAGE CREATION METHODS

    def player_image(self, show=False):
        """Generates a 500/700 player image mocking what a real MLB Showdown card
           would look like for the player output. Final image is dumped to
           mlb_showdown_bot/output folder.

        Args:
          show: Boolean flag for whether to open the final image after creation.

        Returns:
          None
        """

        # LOAD PLAYER IMAGE
        player_image = self.__background_image()

        # ADD HOLIDAY THEME
        if self.is_holiday:
            holiday_image_path = os.path.join(os.path.dirname(__file__), 'templates', 'Holiday.png')
            holiday_image = Image.open(holiday_image_path)
            player_image.paste(holiday_image,(0,0),holiday_image)

        # LOAD SHOWDOWN TEMPLATE
        showdown_template_frame_image = self.__template_image()
        player_image.paste(showdown_template_frame_image,(0,0),showdown_template_frame_image)

        # CREATE NAME TEXT
        name_text, color = self.__player_name_text_image()
        location_key = 'player_name_small' if len(self.name) > 18 else 'player_name'
        name_paste_location = sc.IMAGE_LOCATIONS[location_key][str(self.context)]
        if self.context in ['2000', '2001']:
            # ADD BACKGROUND BLUR EFFECT FOR 2001 CARDS
            name_text_blurred = name_text.filter(ImageFilter.BLUR)
            player_image.paste(sc.COLOR_BLACK, (name_paste_location[0] + 6, name_paste_location[1] + 6), name_text_blurred)
        player_image.paste(color, name_paste_location,  name_text)

        # ADD TEAM LOGO
        team_logo, team_logo_coords = self.__team_logo_image()
        player_image.paste(team_logo, team_logo_coords, team_logo)

        # METADATA
        metadata_image, color = self.__metadata_image()
        player_image.paste(color, sc.IMAGE_LOCATIONS['metadata'][str(self.context)], metadata_image)

        # CHART
        chart_image, color = self.__chart_image()
        if self.context in ['2000','2001']:
            chart_cords = sc.IMAGE_LOCATIONS['chart']['{}{}'.format(self.context,'p' if self.is_pitcher else 'h')]
        else:
            chart_cords = sc.IMAGE_LOCATIONS['chart'][str(self.context)]
        player_image.paste(color, chart_cords, chart_image)

        # BOT VERSION
        version_image = self.__version_image()
        player_image.paste("#b5b4b4", sc.IMAGE_LOCATIONS['version'][str(self.context)], version_image)
        
        # ICONS
        if int(self.context) > 2002:
            player_image = self.__add_icons_to_image(player_image)

        # SET
        set_image = self.__card_set_image()
        player_image.paste(set_image, (0,0), set_image)

        # EXPANSION
        if self.expansion != 'BS':
            expansion_image = self.__expansion_image()
            expansion_location = sc.IMAGE_LOCATIONS['expansion'][str(self.context)]
            if self.context == '2002' and self.expansion == 'TD':
                expansion_location = (expansion_location[0] + 20,expansion_location[1] - 17)
            player_image.paste(expansion_image, expansion_location, expansion_image)

        # SAVE AND SHOW IMAGE
        # CROP TO 63mmx88mm
        player_image = self.__center_crop(player_image,(1488,2079))
        player_image = self.__round_corners(player_image, 60)
        self.image_name = '{name}-{timestamp}.png'.format(name=self.name, timestamp=str(datetime.now()))
        if int(self.context) in [2002,2004,2005]:
            # TODO: SOLVE HTML PNG ISSUES
            player_image = player_image.convert('RGB')

        player_image.save(os.path.join(self.card_img_output_folder_path, self.image_name), dpi=(300, 300), quality=100)
        if self.is_running_in_flask:
            player_image.save(os.path.join(Path(os.path.dirname(__file__)).parent,'static', 'output', self.image_name), dpi=(300, 300), quality=100)

        # OPEN THE IMAGE LOCALLY
        if show:
            image_title = f"{self.name} - {self.year}"
            player_image.show(title=image_title)

        self.__clean_images_directory()

    def __background_image(self):
        """Loads background image for card. Either loads from upload, url, or default
           background.

        Args:
          None

        Returns:
          PIL image object for the player background.
          Boolean for whether a background player image was applied
        """
        default_image_path = os.path.join(os.path.dirname(__file__), 'templates', 'Default Background - {}.png'.format(self.context))
        is_default_image = False
        if self.player_image_path:
            # LOAD IMAGE FROM UPLOAD
            image_path = os.path.join(os.path.dirname(__file__), 'uploads', self.player_image_path)
            try:
                player_image = self.__default_background_image(search_for_image=False)
                player_image_actual = Image.open(image_path).convert('RGBA')
                player_image_actual_cropped = self.__center_crop(player_image_actual, (1500,2100))
                player_image.paste(player_image_actual_cropped,(0,0),player_image_actual_cropped)
            except:
                print("Error Loading Image from Path. Using default background...")
                player_image = Image.open(default_image_path)
        elif self.player_image_url:
            # LOAD IMAGE FROM URL
            image_url = self.player_image_url
            try:
                response = requests.get(image_url)
                player_image = Image.open(BytesIO(response.content))
            except:
                print("Error Loading Image from URL. Using default background...")
                player_image = Image.open(default_image_path)
        else:
            is_default_image = True
            try:
                player_image = self.__default_background_image()
            except:
                print("Error Loading Default Image from Drive. Using default background...")
                player_image = Image.open(default_image_path)
            

        player_image = self.__center_crop(player_image, (1500,2100))

        # IF 2000 CARD AND A DEFAULT WAS NOT USED, ADD NAME CONTAINER IN FRONT OF IMAGE
        if self.context == '2000' and not is_default_image:
            name_container = self.__2000_player_name_container_image()
            player_image.paste(name_container,(0,0),name_container)

        return player_image

    def __default_background_image(self, search_for_image=True):
        """Attempts to query google drive for a player image, if 
        it does not exist use siloutte background.

        Args:
          search_for_image: Boolean for whether to search google drive for image.

        Returns:
          PIL image object for the player background.
        """
        
        # GET TEAM BACKGROUND (00/01)
        default_image_path = os.path.join(os.path.dirname(__file__), 'templates', 'Default Background - {}.png'.format(self.context))
        if self.context in ['2000', '2001']:
            # TEAM BACKGROUNDS
            if self.is_cooperstown:
                background_image_name = 'CC'
            elif self.is_all_star_game and not self.is_multi_year:
                background_image_name = f"ASG-{self.year}"
            else:
                background_image_name = f"{self.team}{self.__team_logo_historical_alternate_extension()}"
            team_image_path = os.path.join(os.path.dirname(__file__), 'team_backgrounds', self.context, f"{background_image_name}.png")
            try:
                background_image = Image.open(team_image_path)
            except:
                background_image = Image.open(default_image_path)
        else:
            # DEFAULT TEAM BACKGROUND
            background_image = Image.open(default_image_path)
        
        # IF 2000, PASTE NAME CONTAINER BEFORE PLAYER CUTOUT
        if self.context == '2000':
            name_container = self.__2000_player_name_container_image()
            background_image.paste(name_container,(0,0),name_container)

        if search_for_image:
            # -- GET PLAYER IMAGE --
            # SEARCH FOR PLAYER IMAGE
            additional_substring_filters = [self.year]
            if self.is_super_season:
                additional_substring_filters.append('(SS)')
            elif self.is_cooperstown:
                additional_substring_filters.append('(CC)')
            elif self.is_all_star_game:
                additional_substring_filters.append('(ASG)')
            if len(self.type_override) > 0:
                additional_substring_filters.append(self.type_override)

            try:
                player_image_url = self.__query_google_drive_for_image_url(
                                        folder_id = sc.G_DRIVE_PLAYER_IMAGE_FOLDERS[self.context],
                                        substring_search = self.bref_id,
                                        additional_substring_search_list = additional_substring_filters,
                                        year = self.year,
                                    )
            except:
                player_image_url = None

            if player_image_url:
                # USE PLAYER IMAGE FROM GOOGLE
                response = requests.get(player_image_url)
                player_image = Image.open(BytesIO(response.content)).convert("RGBA")
                self.is_automated_image = True
            else:
                # ADD PLAYER SILHOUETTE
                type_string = 'P' if self.is_pitcher else 'H'
                hand_prefix = self.hand[0 if self.is_pitcher else -1]
                hand_string = 'L' if hand_prefix == 'S' else hand_prefix
                silhouetee_image_path = os.path.join(os.path.dirname(__file__), 'templates', f'{self.context}-SIL-{hand_string}H{type_string}.png')
                player_image = Image.open(silhouetee_image_path)
            
            background_image.paste(player_image,(0,0),player_image)

        # IF 2000, PASTE SET CONTAINER BEFORE PLAYER CUTOUT
        if self.context == '2000':
            set_container = self.__2000_player_set_container_image()
            background_image.paste(set_container,(0,0),set_container)

        return background_image

    def __text_image(self,text,size,font,fill=255,rotation=0,alignment='left',padding=0,spacing=3,opacity=1,has_border=False,border_color=None,border_size=3,overlay_image_path=None):
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

    def __team_logo_image(self):
        """Generates a new PIL image object with logo of player team.

        Args:
          None

        Returns:
          Tuple:
            - PIL image object with team logo.
            - Coordinates for pasting team logo.
        """

        # SETUP IMAGE METADATA
        logo_name = self.team
        logo_size = sc.IMAGE_SIZES['team_logo'][str(self.context)]
        logo_paste_coordinates = sc.IMAGE_LOCATIONS['team_logo'][str(self.context)]

        if self.is_cooperstown or self.is_all_star_game:
            # OVERRIDE TEAM LOGO WITH EITHER CC OR ASG
            logo_name = 'CC' if self.is_cooperstown else f'ASG-{self.year}'
            if int(self.context) >= 2004 and self.is_cooperstown:
                logo_size = (330,330)
                logo_paste_coordinates = (logo_paste_coordinates[0] - 180,logo_paste_coordinates[1] - 120)
        try:
            # TRY TO LOAD TEAM LOGO FROM FOLDER. LOAD ALTERNATE LOGOS FOR 2004/2005
            historical_alternate_ext = self.__team_logo_historical_alternate_extension()
            alternate_logo_ext = '-A' if int(self.context) >= 2004 and not self.is_all_star_game else ''
            team_logo = Image.open(os.path.join(os.path.dirname(__file__), 'team_logos', '{}{}{}.png'.format(logo_name,alternate_logo_ext,historical_alternate_ext))).convert("RGBA")
            team_logo = team_logo.resize(logo_size, Image.ANTIALIAS)
        except:
            # IF NO IMAGE IS FOUND, DEFAULT TO MLB LOGO
            team_logo = Image.open(os.path.join(os.path.dirname(__file__), 'team_logos', 'MLB.png')).convert("RGBA")
            team_logo = team_logo.resize((270, 147), Image.ANTIALIAS)
        team_logo = team_logo.rotate(10,resample=Image.BICUBIC) if self.context == '2002' and not self.is_cooperstown else team_logo

        # OVERRIDE IF SUPER SEASON
        if self.is_super_season:
            team_logo = self.__super_season_image()
            logo_paste_coordinates = sc.IMAGE_LOCATIONS['super_season'][str(self.context)]

        # ADD YEAR TEXT IF COOPERSTOWN
        if self.is_cooperstown and int(self.context) >= 2004 and not self.is_all_star_game:
            cooperstown_logo = Image.new('RGBA', (logo_size[0] + 300, logo_size[1]))
            cooperstown_logo.paste(team_logo,(150,0),team_logo)
            year_font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'BaskervilleBoldItalicBT.ttf')
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

        return team_logo, logo_paste_coordinates

    def __team_logo_historical_alternate_extension(self):
        """Check to see if there is an alternate team logo to use for the given team + year

        Args:
          None

        Returns:
          Index of alternate logo for team. If none exists, fn will return empty string
        """

        logo_historical_alternates = sc.TEAM_LOGO_ALTERNATES

        # DONT APPLY IF COOPERSTOWN OR SUPER SEASON
        if self.is_cooperstown or self.is_super_season or self.is_all_star_game:
            return ''

        # CHECK TO SEE IF THERE ARE ANY ALTERNATE LOGOS FOR TEAM
        if self.team not in logo_historical_alternates.keys():
            return ''

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
            year_for_team_logo = int(round(statistics.median(years_played_ints)))

        else:
            year_for_team_logo = int(self.year)
        for index, year_range in logo_historical_alternates[self.team].items():
            if year_for_team_logo in year_range:
                return '-{}'.format(index)

        # NO ALTERNATES FOUND, RETURN NONE
        return ''

    def __template_image(self):
        """Loads showdown frame template depending on player context.

        Args:
          None

        Returns:
          PIL image object for Player's template background.
        """

        year = str(self.context)

        # GET TEMPLATE FOR PLAYER TYPE (HITTER OR PITCHER)
        type = 'Pitcher' if self.is_pitcher else 'Hitter'
        cc_extension = '-CC' if self.is_cooperstown and int(self.context) >= 2004 else ''
        ss_extension = '-SS' if (self.is_super_season or self.is_holiday) and int(self.context) >= 2004 else ''
        type_template = '{context}-{type}{cc}{ss}.png'.format(context = year, type = type, cc = cc_extension, ss = ss_extension)
        template_image = Image.open(os.path.join(os.path.dirname(__file__), 'templates', type_template))

        # GET IMAGE WITH PLAYER COMMAND
        command_image_name = '{context}-{type}-{command}.png'.format(
            context = year,
            type = type,
            command = str(self.chart['command'])
        )
        command_image = Image.open(os.path.join(os.path.dirname(__file__), 'templates', command_image_name))
        template_image.paste(command_image, (0,0), command_image)

        # HANDLE MULTI POSITION TEMPLATES FOR 00/01 POSITION PLAYERS
        if year in ['2000','2001'] and not self.is_pitcher:
            positions_list = list(self.positions_and_defense.keys())
            is_multi_position = len(positions_list) > 1
            is_large_position_container = 'LF/RF' in positions_list
            positions_points_template = '{context}-{type}-{mp}-{sl}.png'.format(
                context = year,
                type = type,
                command = str(self.chart['command']),
                mp = 'MULTI' if is_multi_position else 'SINGLE',
                sl = 'LRG' if is_large_position_container else 'SML'
            )
            positions_points_image = Image.open(os.path.join(os.path.dirname(__file__), 'templates', positions_points_template))
            template_image.paste(positions_points_image, (0,0), positions_points_image)

        return template_image

    def __2000_player_name_container_image(self):
        """Gets template asset image for 2000 name container.

        Args:
          None

        Returns:
          PIL image object for 2000 name background/container
        """
        return Image.open(os.path.join(os.path.dirname(__file__), 'templates', "2000-Name.png"))

    def __2000_player_set_container_image(self):
        """Gets template asset image for 2000 set box.

        Args:
          None

        Returns:
          PIL image object for 2000 set background/container
        """
        return Image.open(os.path.join(os.path.dirname(__file__), 'templates', "2000-Set-Box.png"))

    def __player_name_text_image(self):
        """Creates Player name to match showdown context.

        Args:
          None

        Returns:
          Tuple
            - PIL image object for Player's name.
            - Hex Color of text as a String
        """

        # PARSE NAME STRING
        first, last = self.name.upper().split(" ", 1)
        name = self.name.upper() if self.context != '2001' else first
        is_name_over_char_limit = len(name) > 18

        futura_black_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Futura Black.ttf')
        helvetica_neue_lt_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique.ttf')

        # DEFAULT NAME ATTRIBUTES
        name_font_path = helvetica_neue_lt_path
        has_border = False
        border_color = None
        fill_color = 255
        overlay_image_path = None

        # DEFINE ATTRIBUTES BASED ON CONTEXT
        if self.context == '2000':
            name_rotation = 90
            name_alignment = "center"
            name_size = 110 if is_name_over_char_limit else 135
            name_color = "#D2D2D2"
            padding = 0
            overlay_image_path = os.path.join(os.path.dirname(__file__), 'templates', '2000-Name-Text-Background.png')
        elif self.context == '2001':
            name_rotation = 90
            name_alignment = "left"
            name_size = 96
            name_color = "#D2D2D2"
            padding = 0
            name_font_path = futura_black_path
            overlay_image_path = os.path.join(os.path.dirname(__file__), 'templates', '2001-Name-Text-Background.png')
        elif self.context == '2002':
            name_rotation = 90
            name_alignment = "left"
            name_size = 115 if is_name_over_char_limit else 144
            name_color = "#A09D9F"
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

        name_font = ImageFont.truetype(name_font_path, size=name_size)

        # CREATE TEXT IMAGE
        final_text = self.__text_image(
            text = name,
            size = sc.IMAGE_SIZES['player_name'][self.context],
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
            # STRETCH OUT NAME
            text_stretched = final_text.resize((300,5100), Image.ANTIALIAS)
            final_text = text_stretched.crop((0,1545,300,3555))
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

        return final_text, name_color

    def __metadata_image(self):
        """Creates PIL image for player metadata. Different across sets.
           TODO: Should probably split this function up.

        Args:
          None

        Returns:
          Tuple
            - PIL image object for Player metadata.
            - Hex Color of text as a String.
        """

        year = int(self.context)

        # COLOR WILL BE RETURNED
        color = sc.COLOR_WHITE

        if year in [2000,2001]:
            # 2000 & 2001

            metadata_image = Image.new('RGBA', (1500, 2100), 255)
            helvetica_neue_lt_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique.ttf')

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
                font_speed_hand = ImageFont.truetype(helvetica_neue_lt_path, size=54)
                speed_text = self.__text_image(text='SPEED {}'.format(self.speed_letter), size=(900, 300), font=font_speed_hand)
                hand_text = self.__text_image(text=self.hand[-1], size=(300, 300), font=font_speed_hand)
                metadata_image.paste(color, (969 if self.context == '2000' else 915,342), speed_text)
                metadata_image.paste(color, (1212,342), hand_text)
                if self.context == '2001':
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
                    metadata_image.paste(color, (1128,345), speed_num_text)
                # POSITION(S)
                font_position = ImageFont.truetype(helvetica_neue_lt_path, size=78)
                ordered_by_len_position = sorted(self.positions_and_defense.items(), key=lambda l: len(l[0]), reverse=True)
                y_position = 407
                for position, rating in ordered_by_len_position:
                    position_rating_text = '   —' if position == 'DH' else '{} +{}'.format(position,str(rating))
                    position_rating_image = self.__text_image(text=position_rating_text, size=(600, 300), font=font_position)
                    x_position = 1083 if len(position) > 4 else 1161
                    x_position += 18 if position in ['C','CA'] and rating < 10 else 0 # CATCHER POSITIONING ADJUSTMENT
                    metadata_image.paste(color, (x_position,y_position), position_rating_image)
                    y_position += 84
            # POINTS
            text_size = 48 if self.points >= 1000 else 57
            font_pts = ImageFont.truetype(helvetica_neue_lt_path, size=text_size)
            pts_text = self.__text_image(text=str(self.points), size=(300, 300), font=font_pts, alignment = "right")
            pts_y_pos = 576 if len(self.positions_and_defense) > 1 else 492
            pts_x_pos = 969 if self.is_pitcher else 999
            metadata_image.paste(color, (pts_x_pos,pts_y_pos), pts_text)

        elif year in [2002,2003]:
            # 2002 & 2003

            color = sc.COLOR_BLACK if self.context == '2002' else sc.COLOR_WHITE
            if year == 2002:
                helvetica_neue_lt_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique.ttf')
                metadata_font = ImageFont.truetype(helvetica_neue_lt_path, size=120)
            else:
                helvetica_neue_cond_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Helvetica Neue 77 Bold Condensed.ttf')
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
        elif year in [2004,2005]:
            # 2004 & 2005

            metadata_font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Helvetica Neue 77 Bold Condensed.ttf')
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

        return metadata_image, color

    def __chart_image(self):
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

        is_04_05 = self.context in ['2004','2005']

        # FONT
        chart_font_file_name = 'Helvetica Neue 77 Bold Condensed.ttf' if is_04_05 else 'HelveticaNeueCondensedMedium.ttf'
        chart_font_path = os.path.join(os.path.dirname(__file__), 'fonts', chart_font_file_name)
        chart_text_size = int(sc.TEXT_SIZES['chart'][self.context])
        chart_font = ImageFont.truetype(chart_font_path, size=chart_text_size)

        # CREATE CHART RANGES TEXT
        chart_string = ''
        # NEED IF 04/05
        chart_text = Image.new('RGBA',(6300,720))
        chart_text_x = 150 if self.is_pitcher else 141
        for category in self.__chart_categories():
            range = self.chart_ranges['{} Range'.format(category)]
            # 2004/2005 CHART IS HORIZONTAL. PASTE TEXT ONTO IMAGE INSTEAD OF STRING OBJECT.
            if is_04_05:
                range_text = self.__text_image(
                    text = range,
                    size = (450,450),
                    font = chart_font,
                    fill = sc.COLOR_WHITE,
                    alignment = "center",
                    has_border = True,
                    border_color = sc.COLOR_BLACK,
                    border_size = 9
                )
                chart_text.paste(range_text, (chart_text_x, 0), range_text)
                chart_text_x += 531 if self.is_pitcher else 468
            else:
                chart_string += '{}\n'.format(range)

        # CREATE FINAL CHART IMAGE
        if is_04_05:
            # COLOR IS TEXT ITSELF
            chart_text = chart_text.resize((2100,240), Image.ANTIALIAS)
            color = chart_text
        else:
            spacing = int(sc.TEXT_SIZES['chart_spacing'][self.context])
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

    def __card_set_image(self):
        """Creates image with card number and year text. Always defaults to card No 1.
           Uses YEAR and not CONTEXT as the set year.
        Args:
          None

        Returns:
          PIL image object for set text.
        """

        # FONT FOR SET
        helvetica_neue_cond_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Helvetica Neue 77 Bold Condensed.ttf')
        font_size = 100 if self.is_multi_year and self.context == '2003' else 135
        set_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=font_size)

        set_image = Image.new('RGBA', (1500, 2100), 255)
        set_image_location = sc.IMAGE_LOCATIONS['set'][str(self.context)]

        if int(self.context) <= 2002:
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
            year_suffix = "" if self.is_multi_year and int(self.context) > 2003 else f"'{str(self.year)[2:4]}"
            year_text = self.__text_image(
                text = year_suffix,
                size = (450, 450),
                font = set_font,
                alignment = "left"
            )
            year_text = year_text.resize((120,120), Image.ANTIALIAS)
            set_image.paste(sc.COLOR_WHITE, set_image_location, year_text)

            # CARD NUMBER
            number_text = self.__text_image(
                text = self.set_number,
                size = (600, 480),
                font = set_font,
                alignment = "center"
            )
            number_text = number_text.resize((150,120), Image.ANTIALIAS)
            number_color = sc.COLOR_BLACK if self.context == '2003' else sc.COLOR_WHITE
            set_image.paste(number_color, sc.IMAGE_LOCATIONS['number'][str(self.context)], number_text)

        return set_image

    def __expansion_image(self):
        """Creates image for card expansion (ex: Trade Deadline, Pennant Run)
        
        Args:
          None

        Returns:
          PIL image object for card expansion logo.
        """ 

        expansion_image = Image.open(os.path.join(os.path.dirname(__file__), 'templates', f'{self.context}-{self.expansion}.png'))
        return expansion_image

    def __version_image(self):
        """Adds version number licensing text.

        Args:
          None

        Returns:
          PIL image object for version number
        """
        helvetica_neue_cond_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'HelveticaNeueCondensedBold.ttf')
        text_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=50 if self.context not in ['2004','2005'] else 35)
        # DATE NUMBER
        version_text = self.__text_image(
            text = f"v{self.version}",
            size = (450, 450),
            font = text_font,
            alignment = "left"
        )
        version_text = version_text.resize((150,150), Image.ANTIALIAS)
        return version_text

    def __super_season_image(self):
        """Creates image for optional super season attributes. Add accolades for
           cards in set > 2001.

        Args:
          None

        Returns:
          PIL image object for super season logo + text.
        """

        is_04_05 = int(self.context) >= 2004

        # BACKGROUND IMAGE LOGO
        super_season_image = Image.open(os.path.join(os.path.dirname(__file__), 'templates', '{}-Super Season.png'.format(self.context)))

        # FONTS
        super_season_year_path = os.path.join(os.path.dirname(__file__), 'fonts', 'URW Corporate W01 Normal.ttf')
        super_season_accolade_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Zurich Bold Italic BT.ttf')
        super_season_year_font = ImageFont.truetype(super_season_year_path, size=225)
        super_season_accolade_font = ImageFont.truetype(super_season_accolade_path, size=150)

        # YEAR
        if self.is_multi_year:
            font_scaling = 0 if is_04_05 else 40
            if self.is_full_career:
                year_string = 'CAREER'
                font_size = 110 + font_scaling
            else:
                year_string = f"'{str(min(self.year_list))[2:4]}-'{str(max(self.year_list))[2:4]}"
                font_size = 130 + font_scaling
            super_season_year_font = ImageFont.truetype(super_season_year_path, size=font_size)
        else:
            year_string = '’{}'.format(str(self.year)[2:4]) if is_04_05 else str(self.year)
        year_text = self.__text_image(
            text = year_string,
            size = (750,540) if is_04_05 else (1125,600),
            font = super_season_year_font,
            alignment = "left",
            rotation = 0 if is_04_05 else 7
        )
        year_text = year_text.resize((180,180), Image.ANTIALIAS)
        year_paste_coords = (135,90) if is_04_05 else (24,282)
        if self.is_multi_year:
            year_paste_coords = (126,110) if is_04_05 else (26,290)
        super_season_image.paste("#982319",year_paste_coords,year_text)

        if int(self.context) > 2001:
            # ACCOLADES
            accolades_list = sorted(self.__super_season_accolades(),key=len,reverse=True)
            x_position = 18 if is_04_05 else 9
            y_position = 342 if is_04_05 else 324
            accolade_rotation = 15 if is_04_05 else 13
            accolade_spacing = 45 if is_04_05 else 72
            for accolade in accolades_list:
                accolade_text = self.__text_image(
                    text = accolade,
                    size = (1800,480),
                    font = super_season_accolade_font,
                    alignment = "center",
                    rotation = accolade_rotation
                )
                accolade_text = accolade_text.resize((375,150), Image.ANTIALIAS)
                super_season_image.paste(sc.COLOR_BLACK, (x_position, y_position), accolade_text)
                x_position += 6
                y_position += accolade_spacing

        # RESIZE
        super_season_image = super_season_image.resize(sc.IMAGE_SIZES['super_season'][self.context], Image.ANTIALIAS)
        return super_season_image

    def __super_season_accolades(self):
        """Generates array of 3 highlights for season.

        Args:
          None

        Returns:
          Array with 3 string elements showing accolades for season
        """

        # FIRST LOOK AT ICONS
        accolades_list = []
        for icon in self.icons:
            icons_full_description = {
                'V': 'MVP',
                'S': 'SILVER SLUGGER',
                'GG': 'GOLD GLOVE',
                'CY': 'CY YOUNG',
                'K': str(self.stats['SO']) + ' STRIKEOUTS',
                'RY': 'ROY',
                'HR': str(self.stats['HR']) + ' HOMERS',
                '20': '20 GAME WINNER'
            }
            if icon in icons_full_description.keys():
                accolades_list.append(icons_full_description[icon])

        if 'AS' in self.stats['award_summary']:
            accolades_list.append('ALL-STAR')

        # DEFAULT ACCOLADES
        # HANDLES CASE OF NO AWARDS
        if self.is_pitcher:
            accolades_list.append(str(self.stats['earned_run_avg']) + ' ERA')
            is_starter = 'STARTER' in self.positions_and_defense.keys()
            if is_starter:
                accolades_list.append(str(self.stats['W']) + ' WINS')
            else:
                accolades_list.append(str(self.stats['SV']) + ' SAVES')
            accolades_list.append(str(self.stats['batting_avg']).replace('0.','.') + ' BA AGAINST')
        else:
            accolades_list.append(str(self.stats['batting_avg']).replace('0.','.') + ' BA')
            accolades_list.append(str(self.stats['RBI']) + ' RBI')
            accolades_list.append(str(self.stats['HR']) + ' HOMERS')

        return accolades_list[0:3]

    def __add_icons_to_image(self, player_image):
        """Add icon images (if player has icons) to existing player_image object.
           Only for >= 2003 sets.

        Args:
          player_image: Current PIL image object for Showdown card.

        Returns:
          Updated PIL Image with icons for player.
        """

        icon_positional_mapping = sc.ICON_LOCATIONS[self.context]
        # ITERATE THROUGH AND PASTE ICONS
        for index, icon in enumerate(self.icons[0:4]):
            icon_image = Image.open(os.path.join(os.path.dirname(__file__), 'templates', '{}-{}.png'.format(self.context,icon)))
            position = icon_positional_mapping[index]
            # IN 2004/2005, ICON LOCATIONS DEPEND ON PLAYER POSITION LENGTH
            # EX: 'LF/RF' IS LONGER STRING THAN '3B'
            if int(self.context) >= 2004:
                positions_list = self.positions_and_defense.keys()
                offset = 0
                if len(positions_list) > 1:
                    # SHIFT ICONS TO RIGHT
                    offset = 165 if 'LF/RF' in positions_list else 135
                elif 'LF/RF' in positions_list:
                    offset = 75
                elif 'CA' in positions_list:
                    offset = 30
                position = (position[0] + offset, position[1])
            player_image.paste(icon_image, position, icon_image)

        return player_image

    def __round_corners(self, image, radius):
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

    def __center_crop(self, image, crop_size):
        """Uses image size to crop in the middle for given crop size.
           Used to automatically center player image background.

        Args:
          image: PIL image object to edit.
          crop_size: Tuple representing width and height of desired crop.

        Returns:
          Cropped PIL image object.
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

        new_width, new_height = image.size
        left = (new_width - crop_width) / 2
        top = (new_height - crop_height) / 2
        right = (new_width + crop_width) / 2
        bottom = (new_height + crop_height) / 2

        # CROP THE CENTER OF THE IMAGE
        return image.crop((left, top, right, bottom))

    def __clean_images_directory(self):
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
                    is_file_stale = self.__is_file_over_5_mins_old(item_path)
                    if is_file_stale:
                        # DELETE IF UPLOADED/MODIFIED OVER 5 MINS AGO
                        os.remove(item_path)

        # UPLOADED IMAGES (PACKAGE)
        for item in os.listdir(os.path.join(os.path.dirname(__file__), 'uploads')):
            if item != '.gitkeep':
                # CHECK TO SEE IF ITEM WAS MODIFIED MORE THAN 5 MINS AGO.
                item_path = os.path.join(os.path.dirname(__file__), 'uploads', item)
                is_file_stale = self.__is_file_over_5_mins_old(item_path)
                if is_file_stale:
                    # DELETE IF UPLOADED/MODIFIED OVER 5 MINS AGO
                    os.remove(item_path)

    def __is_file_over_5_mins_old(self, path):
        """Checks modified date of file to see if it is older than 5 mins.
           Used for cleaning output directory and image uploads.

        Args:
          path: String path to file in os.

        Returns:
            True if file in path is older than 5 mins, false if not.
        """

        datetime_current = datetime.now()
        datetime_uploaded = datetime.fromtimestamp(os.path.getmtime(path))
        file_age_mins = (datetime_current - datetime_uploaded).total_seconds() / 60.0

        return file_age_mins >= 5.0

# ------------------------------------------------------------------------
# IMAGE QUERIES

    def __query_google_drive_for_image_url(self, folder_id, substring_search, additional_substring_search_list=[], year=None):
        """Attempts to query google drive for a player image, if 
        it does not exist use siloutte background.

        Args:
          folder_id: Unique ID for folder in drive (found in URL)
          substring_search: string used to filter results 
          additional_substring_search_list: List of strings to filter down results in case of multiple results.
          year: Year(s) of card.

        Returns:
          List of dicts with file metadata
        """
        
        # GAIN ACCESS TO GOOGLE DRIVE
        SCOPES = ['https://www.googleapis.com/auth/drive']
        GOOGLE_CREDENTIALS_STR = os.getenv('GOOGLE_CREDENTIALS')
        if not GOOGLE_CREDENTIALS_STR:
            # IF NO CREDS, RETURN NONE
            return None
        # CREDS FILE FOUND, PROCEED
        GOOGLE_CREDENTIALS_JSON = json.loads(GOOGLE_CREDENTIALS_STR)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_JSON, SCOPES)

        # BUILD THE SERVICE OBJECT.
        service = build('drive', 'v3', credentials=creds)

        # GET LIST OF FILE METADATA FROM CORRECT FOLDER
        query = f"parents = '{folder_id}'"
        files = service.files()
        response = files.list(q=query,pageSize=1000).execute()
        files_metadata = response.get('files')

        # LOOK FOR SUBSTRING IN FILE NAMES
        player_matched_image_files = []
        for img_file in files_metadata:
            file_name_key = 'name'
            if file_name_key in img_file.keys():
                # LOOK FOR SUBSTRING MATCH
                if substring_search in img_file[file_name_key]:
                    player_matched_image_files.append(img_file)

        # IF MULTIPLE IMAGES, LOOK INTO ADDITIONAL QUERY
        num_files = len(player_matched_image_files)
        if num_files == 0:
            return None
        elif num_files > 1:
            player_matched_image_files = sorted(player_matched_image_files, key = lambda i: len(i['name']), reverse=False)
            match_rates = {}
            for img_metadata in player_matched_image_files:
                img_name = img_metadata['name']
                img_id = img_metadata['id']
                match_rate = sum(val in img_name for val in additional_substring_search_list)

                # ADD DISTANCE FROM YEAR                
                year_from_img_name = img_name.split(" ")[0]
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
        else:
            file_id = player_matched_image_files[0]['id']
        
        # GET WEB CONTENT URL
        img_url = files.get(fileId=file_id, fields="webContentLink").execute()['webContentLink']

        return img_url
