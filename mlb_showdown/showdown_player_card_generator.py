
import pandas as pd
import math
import requests
import operator
import os
from io import BytesIO
from datetime import datetime
import mlb_showdown.showdown_constants as sc
from bs4 import BeautifulSoup
from pprint import pprint
from PIL import Image, ImageDraw, ImageFont, ImageOps
import json
from urllib.request import urlopen, Request


class ShowdownPlayerCardGenerator:

# ------------------------------------------------------------------------
# INIT

    def __init__(self, name, year, stats, context, offset=0, test_numbers=None, printOutput=False, player_image_url=None):
        self.name = name
        self.year = year
        self.context = context
        self.stats = stats
        self.player_image_url = player_image_url

        self.test_numbers = test_numbers
        self.is_pitcher = True if stats['type'] == 'Pitcher' else False
        self.team = stats['team_ID']

        self.__player_metadata(stats)

        stats_for_400_pa = self.__stats_per_n_pa(400, stats)
        command_out_combos = self.__top_accurate_command_out_combos(float(stats['onbase_perc']), 5)

        self.chart, chart_results_per_400_abs = self.__most_accurate_chart(command_out_combos, stats_for_400_pa, int(offset))
        self.chart_ranges = self.__ranges_for_chart(self.chart, float(stats_for_400_pa['2b_per_400_pa']), float(stats_for_400_pa['hr_per_400_pa']))
        self.real_stats = self.__stats_for_full_season(chart_results_per_400_abs)

        self.icons = self.__icons(stats['award_summary'] if 'award_summary' in stats.keys() else '')

        self.points = self.__point_value(chart=self.chart,
                                        real_stats=self.real_stats,
                                        positions_and_defense=self.positions_and_defense,
                                        speed_or_ip=self.ip if self.is_pitcher else self.speed)
        if printOutput:
            self.print_player()
            self.player_image()

# ------------------------------------------------------------------------
# METADATA METHODS

    def __player_metadata(self, stats):
        """Parse all metadata (positions, hand, speed, ...) and assign to self

        Args:
          stats: Dict of stats from Baseball Reference scraper

        Returns:
          None
        """

        defensive_stats_raw = {k:v for (k,v) in stats.items() if 'Position' in k}
        hand_raw = stats['hand']
        innings_pitched_raw = float(stats['IP']) if self.is_pitcher else 0.0
        games_played_raw = int(stats['G'])
        games_started_raw = int(stats['GS']) if self.is_pitcher else 0
        saves_raw = int(stats['SV']) if self.is_pitcher else 0
        sprint_speed_raw = stats['sprint_speed']
        stolen_bases_raw = int(stats['SB']) if not self.is_pitcher else 0

        self.positions_and_defense = self.__positions_and_defense(defensive_stats_raw, games_played_raw, games_started_raw, saves_raw)
        self.hand = self.__handedness(hand_raw)
        self.ip = self.__innings_pitched(innings_pitched_raw, games_played_raw)
        self.speed, self.speed_letter = self.__speed(sprint_speed_raw, stolen_bases_raw)

    def __positions_and_defense(self, defensive_stats, games_played, games_started, saves):
        """Get in game defensive positions and ratings

        Args:
          defensive_stats: Dict of games played and total_zone for each position.
          games_played: Number of games played at any position.
          games_started: Number of games started as a pitcher.
          saves: Number of saves. Used to determine what kind of reliever a player is.

        Returns:
          Dict with in game positions and defensive ratings
        """

        num_positions = int(len(defensive_stats.keys()) / 3)
        positions_and_defense = {}
        positions_and_games_played = {}

        for position_index in range(1, num_positions+1):
            position_raw = defensive_stats['Position{}'.format(position_index)]
            games_at_position = int(defensive_stats['gPosition{}'.format(position_index)])
            position = self.__position_in_game(position_raw,num_positions,games_at_position,games_played,games_started,saves)
            positions_and_games_played[position] = games_at_position
            if position is not None:
                if not self.is_pitcher:
                    try:
                        total_zone_rating = int(defensive_stats['tzPosition{}'.format(position_index)])
                    except:
                        total_zone_rating = 0
                    defense = self.__convert_tzr_to_in_game_defense(position,total_zone_rating)
                    positions_and_defense[position] = defense
                else:
                    positions_and_defense[position] = 0

        final_positions_in_game, final_position_games_played = self.__combine_like_positions(positions_and_defense, positions_and_games_played)
        # LIMIT TO ONLY 2 POSITIONS
        if len(final_positions_in_game.items()) > 2:
            sorted_positions = sorted(final_position_games_played.items(), key=operator.itemgetter(1), reverse=True)[0:2]
            final_positions_in_game = {}
            for position, value in sorted_positions:
                final_positions_in_game[position] = value

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
                lf_rf_rating = round((positions_and_defense['LF'] + positions_and_defense['RF']) / 2)
                lf_rf_games = positions_and_games_played['LF'] + positions_and_games_played['RF']
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
        elif 'OF' in positions_set:
            del positions_and_defense['OF']
            del positions_and_games_played['OF']

        return positions_and_defense, positions_and_games_played

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

        return ip

    def __speed(self, sprint_speed, stolen_bases):
        """In game speed for a position player. Will use pure sprint speed
           if year is > 2015, otherwise uses stolen bases. Pitcher defaults to 10.

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

        if sprint_speed is None or math.isnan(sprint_speed) or sprint_speed == '':
            # NO SPRINT SPEED AVAILABLE
            sb_range = sc.MAX_STOLEN_BASES - sc.MIN_STOLEN_BASES
            speed_percentile = (stolen_bases-sc.MIN_STOLEN_BASES) / sb_range
            max_speed_in_game = 18.0
        else:
            # SPRINT SPEED IS AVAILABLE
            sprint_speed_range = sc.MAX_SPRINT_SPEED - sc.MIN_SPRINT_SPEED
            speed_percentile = (sprint_speed-sc.MIN_SPRINT_SPEED) / sprint_speed_range
            max_speed_in_game = 25.0

        speed_raw = int(round(speed_percentile * max_speed_in_game))
        # CHANGE OUTLIERS
        speed = 8 if speed_raw < 8 else speed_raw
        speed = 30 if speed_raw > 30 else speed_raw

        if speed < 12:
            letter = 'C'
        elif speed < 18:
            letter = 'B'
        else:
            letter = 'A'
        return speed, letter

    def __position_in_game(self, position, num_positions, position_appearances, games_played, games_started, saves):
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

        if position == 'P':
            # PITCHER IS EITHER STARTER, RELIEVER, OR CLOSER
            gsRatio = games_started / games_played
            starter_threshold = 0.65
            if gsRatio > starter_threshold:
                return 'STARTER'
            if saves > 10:
                return 'CLOSER'
            else:
                return 'RELIEVER'
        elif position_appearances < sc.NUMBER_OF_GAMES:
            # IF POSIITION DOES NOT MEET REQUIREMENT, RETURN NONE
            return None
        elif position == 'DH' and num_positions > 1:
            # PLAYER MAY HAVE PLAYED AT DH, BUT HAS OTHER POSITIONS, SO DH WONT BE LISTED
            return None
        else:
            # RETURN BASEBALL REFERENCE STRING VALUE
            return position

    def __convert_tzr_to_in_game_defense(self, position, tzr):
        """Converts Total Zone Rating (TZR) to in game defense at a position.
           We use TZR to calculate defense because it is available for most eras.
           More modern defensive metrics (like DRS)

        Args:
          position: In game position name.
          tzr: Total Zone Rating. 0 is average for a position.

        Returns:
          In game defensive rating.
        """

        max_defense_for_position = sc.POSITION_DEFENSE_RANGE[self.context][position]
        tzr_range = sc.MAX_SABER_FIELDING - sc.MIN_SABER_FIELDING
        defense_raw = ( (tzr-sc.MIN_SABER_FIELDING) * max_defense_for_position ) / tzr_range
        defense = round(defense_raw) if defense_raw > 0 else 0

        return defense

    def __icons(self,awards):
        """Converts awards_summary and other metadata fields into in game icons.

        Args:
          awards: String containing list of seasonal accolades.

        Returns:
          List of in game icons as strings.
        """

        awards_upper = '' if awards is None else str(awards).upper()
        awards_to_icon_map = {
            'SS': 'S',
            'GG': 'G',
            'MVP-1': 'V',
            'CYA-1': 'CY',
            'ROY-1': 'RY'
        }
        awards_list = awards_upper.split(',')

        icons = []
        for award, icon in awards_to_icon_map.items():
            if award in awards_list:
                icons.append(icon)

        # DATA DRIVEN ICONS
        if self.is_pitcher:
            # 20
            if int(self.stats['W']) >= 20:
                icons.append('20')
            # K
            if int(self.stats['SO']) >= 215:
                icons.append('K')
        else:
            # HR
            if int(self.stats['HR']) >= 40:
                icons.append('HR')

        return icons

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

        combos = self.__obp_for_command_out_combos()
        combo_accuracies = {}

        for combo, predicted_obp in combos.items():
            accuracy = 1 - self.__pct_difference(obp, predicted_obp)
            combo_accuracies[combo] = accuracy

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

        command_out_combos = sc.CONTROL_COMBOS[self.context] if self.is_pitcher else sc.OB_COMBOS[self.context]
        combo_and_obps = {}

        for combo in command_out_combos:
            command = combo[0]
            outs = combo[1]
            command_out_matchup = self.__onbase_control_outs(command, outs)
            predicted_obp = self.__pct_rate_for_result(
                                onbase = command_out_matchup['onbase'],
                                control = command_out_matchup['control'],
                                num_results_hitter_chart = 20-command_out_matchup['hitterOuts'],
                                num_results_pitcher_chart = 20-command_out_matchup['pitcherOuts']
                            )
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

        onbaseBaseline = sc.BASELINE_HITTER[self.context]['command'] if self.test_numbers is None else self.test_numbers[0]
        hitterOutsBaseline = sc.BASELINE_HITTER[self.context]['outs'] if self.test_numbers is None else self.test_numbers[1]
        controlBaseline = sc.BASELINE_PITCHER[self.context]['command'] if self.test_numbers is None else self.test_numbers[0]
        pitcherOutsBaseline = sc.BASELINE_PITCHER[self.context]['outs'] if self.test_numbers is None else self.test_numbers[1]

        return {
            'onbase': playercommand if not self.is_pitcher else onbaseBaseline,
            'hitterOuts': playerOuts if not self.is_pitcher else hitterOutsBaseline,
            'control': playercommand if self.is_pitcher else controlBaseline,
            'pitcherOuts': playerOuts if self.is_pitcher else pitcherOutsBaseline
        }

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
        if not self.is_pitcher:
            opponent_chart = sc.BASELINE_PITCHER[self.context]
            my_advantages_per_20 = command-self.__onbase_control_outs()['control']
            opponent_advantages_per_20 = 20 - my_advantages_per_20
        else:
            opponent_chart = sc.BASELINE_HITTER[self.context]
            opponent_advantages_per_20 = self.__onbase_control_outs()['onbase']-command
            my_advantages_per_20 = 20 - opponent_advantages_per_20

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
                # WE ROUND THE PREDICTED RESULTS (2.4 -> 2, 2.5 -> 3)
                rounded_results = round(chart_results) if chart_results > 0 else 0
                # CHECK FOR BARRY BONDS EFFECT (HUGE WALK)
                rounded_results = 13 if key == 'bb' and rounded_results > 13 else rounded_results
                chart[key] = rounded_results

        # FILL "OUT" CATEGORIES (PU, GB, FB)
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
        remaining_slots_qa = 0 if remaining_slots < 0 else remaining_slots
        # FILL 1B AND 1B+
        stolen_bases = int(stats_for_400_pa['sb_per_400_pa'])
        chart['1b'], chart['1b+'] = self.__single_and_single_plus_results(remaining_slots_qa,stolen_bases)
        # CHECK ACCURACY COMPARED TO REAL LIFE
        in_game_stats_for_400_pa = self.__chart_to_results_per_400_pa(chart,my_advantages_per_20,opponent_chart,opponent_advantages_per_20)
        weights = {
            'h_per_400_pa': 5.0,
            'slugging_perc': 1.0,
            'onbase_perc': 5.0
        }
        accuracy, categorical_accuracy = self.accuracy_between_dicts(in_game_stats_for_400_pa, stats_for_400_pa, weights)
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
            # SPLIT UP REMAINING SLOTS BETWEEN GROUND AND AIR OUTS
            gb_outs = round((out_slots_remaining / (gb_pct + 1)) * gb_pct)
            air_outs = out_slots_remaining - gb_outs
            pu_outs = 0.0 if not self.is_pitcher else round(air_outs*popup_pct)
            fb_outs = air_outs-pu_outs
        else:
            fb_outs = 0.0
            pu_outs = 0.0
            gb_outs = 0.0

        return pu_outs, gb_outs, fb_outs

    def __single_and_single_plus_results(self, remaining_slots, sb):
        """Fill 1B and 1B+ categories on chart.

        Args:
          remaining_slots: Remaining slots out of 20.
          sb: Stolen bases per 400 PA

        Returns:
          Tuple of 1B, 1B+ result ints.
        """

        # Pitcher has no 1B+
        if self.is_pitcher:
            return remaining_slots, 0

        # Divide stolen bases per 400 PA by 10
        single_plus_results_raw = math.trunc(sb / 10)
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

    def __ranges_for_chart(self, chart, dbl_per_400_pa, hr_per_400_pa):
        """Converts chart integers to Range Strings ({1B: 3} -> {'1B': '11-13'})

        Args:
          remaining_slots: Remaining slots out of 20.
          sb: Stolen bases per 400 PA

        Returns:
          Tuple of 1B, 1B+ result ints.
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
        # TODO: MAKE THIS MORE ACCURATE + ROBUST

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
        pct_of_n_pa = (float(stats['PA']) - float(stats['SH'])) / plate_appearances
        stats_for_n_pa = {
            'PA': plate_appearances,
            'pct_of_{}_pa'.format(plate_appearances): pct_of_n_pa,
            'slugging_perc': float(stats['slugging_perc']),
            'onbase_perc': float(stats['onbase_perc']),
            'batting_avg': float(stats['batting_avg']),
            'IF/FB': float(stats['IF/FB']),
            'GO/AO': float(stats['GO/AO']) if int(self.year) > 1940 else 1.0
        }

        stats['1B'] = int(stats['H']) - int(stats['HR']) - int(stats['3B']) - int(stats['2B'])

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
          hitter_denom_adjust: Adjust denominator for hitter calcs
          pitch_denom_adjust: Adjust denominator for pitcher calcs
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

    def __chart_to_results_per_400_pa(self, chart, my_advantages_per_20, opponent_chart, opponent_advantages_per_20):
        """Predict real stats given Showdown in game chart.

        Args:
          chart: Dict for chart of Player.
          my_advantages_per_20: Int number of advantages my Player gets out of 20 (i.e. 5).
          opponent_chart: Dict for chart of baseline opponent.
          opponent_advantages_per_20: Int number of advantages opponent gets out of 20 (i.e. 15).

        Returns:
          Dict with stats per 400 Plate Appearances.
        """
        # GET HITTER HITS FOR BATTING AVG CALCULATION
        command_out_matchup = self.__onbase_control_outs(chart['command'],chart['outs'])
        pitcher_chart = chart if self.is_pitcher else opponent_chart
        hitter_chart = chart if not self.is_pitcher else opponent_chart
        hits_pitcher_chart = pitcher_chart['1b'] + pitcher_chart['2b'] \
                             + pitcher_chart['3b'] + pitcher_chart['hr']
        hits_hitter_chart = hitter_chart['1b'] + hitter_chart['1b+'] + hitter_chart['2b'] \
                            + hitter_chart['3b'] + hitter_chart['hr']

        strikeouts_per_400_pa = self.__result_occurances_per_400_pa(chart['so'],opponent_chart['so'],
                                                            my_advantages_per_20,opponent_advantages_per_20)
        walks_per_400_pa = self.__result_occurances_per_400_pa(chart['bb'],opponent_chart['bb'],
                                                       my_advantages_per_20,opponent_advantages_per_20)
        singles_per_400_pa = self.__result_occurances_per_400_pa(chart['1b']+chart['1b+'],opponent_chart['1b'],
                                                         my_advantages_per_20,opponent_advantages_per_20)
        doubles_per_400_pa = self.__result_occurances_per_400_pa(chart['2b'],opponent_chart['2b'],
                                                         my_advantages_per_20,opponent_advantages_per_20)
        triples_per_400_pa = self.__result_occurances_per_400_pa(chart['3b'],opponent_chart['3b'],
                                                         my_advantages_per_20,opponent_advantages_per_20)
        home_runs_per_400_pa = self.__result_occurances_per_400_pa(chart['hr'],opponent_chart['hr'],
                                                           my_advantages_per_20,opponent_advantages_per_20)
        results_per_400_pa = {
            'so_per_400_pa': strikeouts_per_400_pa,
            'bb_per_400_pa': walks_per_400_pa,
            '1b_per_400_pa': singles_per_400_pa,
            '2b_per_400_pa': doubles_per_400_pa,
            '3b_per_400_pa': triples_per_400_pa,
            'hr_per_400_pa': home_runs_per_400_pa,
            'h_per_400_pa': singles_per_400_pa + doubles_per_400_pa + triples_per_400_pa + home_runs_per_400_pa,
            'batting_avg': self.__pct_rate_for_result(command_out_matchup['onbase'],
                                                      command_out_matchup['control'],
                                                      hits_hitter_chart,
                                                      hits_pitcher_chart,
                                                      hitter_chart['bb'],
                                                      pitcher_chart['bb']),
            'onbase_perc': self.__pct_rate_for_result(command_out_matchup['onbase'],command_out_matchup['control'],
                                              20-command_out_matchup['hitterOuts'],20-command_out_matchup['pitcherOuts']),
            'slugging_perc': self.__slugging_pct(400-walks_per_400_pa, singles_per_400_pa, doubles_per_400_pa,
                                         triples_per_400_pa, home_runs_per_400_pa),
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

    def __stats_for_full_season(self, stats_per_400_pa):
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

    def __point_value(self, chart, real_stats, positions_and_defense, speed_or_ip):
        """Derive player's value. Uses constants to compare against other cards in set.

        Args:
          chart: Dict containing number of results per result category ({'1b': 5, 'hr': 3}).
          real_stats: Dict with real metrics (obp, ba, ...) for 650 PA (~ full season)
          positions_and_defense: Dict with all valid positions and their corresponding defensive rating.
          speed: In game speed ability.

        Returns:
          Points that the player is worth.
        """

        points = 0

        # PARSE PLAYER TYPE
        is_starting_pitcher = 'STARTER' in positions_and_defense.keys()
        if self.is_pitcher:
            player_category = 'starting_pitcher' if is_starting_pitcher else 'relief_pitcher'
        else:
            player_category = 'position_player'

        obp_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['onbase'] \
                     * self.stat_percentile(real_stats['onbase_perc'],
                                            sc.ONBASE_PCT_RANGE[self.context],
                                            is_desc=self.is_pitcher)
        ba_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['average'] \
                    * self.stat_percentile(real_stats['batting_avg'],
                                           sc.BATTING_AVG_RANGE[self.context],
                                           is_desc=self.is_pitcher)
        slg_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['slugging'] \
                     * self.stat_percentile(real_stats['slugging_perc'],
                                            sc.SLG_RANGE[self.context],
                                            is_desc=self.is_pitcher)

        # USE EITHER SPEED OR IP DEPENDING ON PLAYER TYPE
        spd_ip_category = 'ip' if self.is_pitcher else 'speed'
        if self.is_pitcher:
            spd_ip_range = sc.IP_RANGE['starting_pitcher' if is_starting_pitcher else 'relief_pitcher']
        else:
            spd_ip_range = sc.SPEED_RANGE[self.context]
        spd_ip_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category][spd_ip_category] \
                         * self.stat_percentile(speed_or_ip,
                                                spd_ip_range,
                                                is_desc=False)

        points += (obp_points + ba_points + slg_points + spd_ip_points)

        if not self.is_pitcher:
            # ONLY HITTERS HAVE HR ADD TO POINTS
            hr_points = sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['home_runs'] \
                        * self.stat_percentile(real_stats['hr_per_650_pa'],
                                               sc.HR_RANGE[self.context],
                                               is_desc=self.is_pitcher)
            points += hr_points
            defense_points = 0
            for position, fielding in positions_and_defense.items():
                if position != 'DH':
                    percentile = fielding / sc.POSITION_DEFENSE_RANGE[self.context][position]
                    positionPts = percentile * sc.POINT_CATEGORY_WEIGHTS[self.context][player_category]['defense']
                    defense_points += positionPts
            points_per_position = defense_points / len(positions_and_defense.keys()) if len(positions_and_defense.keys()) > 0 else 1
            points += points_per_position

        return int(round(points,-1))

    def stat_percentile(self, stat, min_max_dict, is_desc=False):
        """Get the percentile for a particular stat.

        Args:
          stat: Value to get percentile of.
          min_max_dict: Dict with 'min' and 'max' range values for the stat
          is_desc: Boolean for whether the lowest value should be treated as positive.

        Returns:
          Percent of points to give for given category.
        """

        min = min_max_dict['min']
        max = min_max_dict['max']
        range = max - min
        stat_within_range = stat - min if stat - min > 0 else 0
        raw_percentile = stat_within_range / range
        percentile_adjusted = 1 - raw_percentile if is_desc else raw_percentile

        return percentile_adjusted

# ------------------------------------------------------------------------
# GENERIC METHODS

    def accuracy_between_dicts(self, dict1, dict2, weights={}, all_or_nothing=[]):
        """Compare two dictionaries of numbers to get overall difference

        Args:
          dict1: First Dictionary. Use this dict to get keys to compare.
          dict2: Second Dictionary.
          weights: X times to count certain category (ex: 3x for command)
          all_or_nothing: List of category names to compare as a boolean 1 or 0 instead
                          of pct difference.
        Returns:
          Float with accuracy and Dict with accuracy per key.
        """
        denominator = len(dict1.keys())
        output = {}
        accuracies = 0
        for key, value1 in dict1.items():
            if key in dict2.keys():
                value2 = dict2[key]
                if key in all_or_nothing:
                    accuracy_for_key = 1 if value1 == value2 else 0
                else:
                    pct_difference = self.__pct_difference(value1, value2)
                    accuracy_for_key = 1 - pct_difference
                output[key] = accuracy_for_key
                # APPLY WEIGHTS
                weight = float(weights[key]) if key in weights.keys() else 1
                denominator += float(weights[key]) - 1 if key in weights.keys() else 0
                accuracies += (accuracy_for_key * weight)

        overall_accuracy = accuracies / denominator

        return overall_accuracy, output

    def __pct_difference(self, num1, num2):
        """ CALCULATE % DIFFERENCE BETWEEN 2 NUMBERS"""
        if num1+num2 == 0:
            # PCT DIFF IS AUTOMATICALLY 0
            return 0
        else:
            return abs(num1 - num2) / ( (num1 + num2) / 2 )

    def accuracy_against_wotc(self, wotc_card_dict):
        """Compare My card output against official WOTC card.

        Args:
          wotc_card_dict: Dictionary with stats per category from wizards output.

        Returns:
          Float with overall accuracy and Dict with accuracy per stat category.
        """
        chart_w_combined_command_outs = self.chart
        # del chart_w_combined_command_outs['command']
        # del chart_w_combined_command_outs['outs']
        chart_w_combined_command_outs['command-outs'] = '{}-{}'.format(self.chart['command'],self.chart['outs'])
        return self.accuracy_between_dicts(wotc_card_dict,
                                           chart_w_combined_command_outs,
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
        slash_categories = [('batting_avg', 'BA'),('onbase_perc', 'OBP'),('slugging_perc', 'SLG')]
        slash_as_string = ''
        for key, cleaned_category in slash_categories:
            showdown_stat_str = '{}: {}'.format(cleaned_category,round(self.real_stats[key],3))
            real_stat_str = '{}: {}'.format(cleaned_category,self.stats[key])
            slash_as_string += '{:<12}{:>12}\n'.format(showdown_stat_str,real_stat_str)

        # RESULT LINE
        real_life_pa = int(self.stats['PA'])
        real_life_pa_ratio = int(self.stats['PA']) / 650.0
        results_as_string = '{:<12}{:>12}\n'.format(' PA: {}'.format(real_life_pa),' PA: {}'.format(real_life_pa))
        result_categories = [
            ('1b_per_650_pa', '1B'),
            ('2b_per_650_pa', '2B'),
            ('3b_per_650_pa', '3B'),
            ('hr_per_650_pa', 'HR'),
            ('bb_per_650_pa', 'BB'),
            ('so_per_650_pa', 'SO')
        ]
        for key, cleaned_category in result_categories:
            showdown_stat_str = ' {}: {}'.format(cleaned_category,str(int(round(self.real_stats[key]) * real_life_pa_ratio)).replace('0.',''))
            real_stats_str = ' {}: {}'.format(cleaned_category,self.stats[cleaned_category])
            results_as_string += '{:<12}{:>12}\n'.format(showdown_stat_str, real_stats_str)

        card_as_string = """
***********************************************
{name} ({year}) ({team})
{context} Base Set Card

{positions}
{hand}
{ip_or_speed}
{icons}
{points} PT.

{command_header}: {command}
{chart}

Statline

Showdown            Real
----------     ---------
{slash_line}
{results}
***********************************************
        """.format(
            name = self.name,
            year = self.year,
            team = self.team,
            context = self.context,
            positions = positions_string,
            hand = self.hand,
            ip_or_speed = ip_or_speed,
            icons = icon_string,
            points = str(self.points),
            command_header = 'CONTROL' if self.is_pitcher else 'ONBASE',
            command=self.chart['command'],
            chart = chart_string,
            slash_line = slash_as_string,
            results = results_as_string
        )
        print(card_as_string)
        return card_as_string

    def __player_metadata_summary_text(self):
        """Creates a multi line string with all player metadata for card output.

        Args:
          None

        Returns:
          String of output text for player info + stats
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
                    positions_string += '{} +{}{}'.format(position,fielding,'' if is_last_element else '\n')
                position_num += 1

        ip_or_speed = 'Speed {} ({})'.format(self.speed_letter,self.speed) if not self.is_pitcher else '{} IP'.format(self.ip)
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
        final_text = final_text.upper() if self.context == '2002' else final_text
        return final_text

    def player_image(self):
        """Generates a 500/700 player image mocking what a real MLB Showdown card
           would look like for the player output. Final image is dumped to
           static/image_output folder.

        Args:
          None

        Returns:
          None
        """
        # FONTS
        helvetica_neue_cond_bold_path = os.path.join('static', 'fonts', 'Helvetica Neue 77 Bold Condensed.ttf')

        helvetica_neue_cond_bold = ImageFont.truetype(helvetica_neue_cond_bold_path, size=45)
        helvetica_neue_cond_bold_alt = ImageFont.truetype(helvetica_neue_cond_bold_path, size=48)

        # LOAD PLAYER IMAGE
        default_image_path = os.path.join('static', 'templates', 'Default Background - {}.png'.format(self.context))
        if self.player_image_url is None:
            # image_url = self.__scrape_player_image_url(url=self.player_image_url)
            player_image = Image.open(default_image_path)
        else:
            image_url = self.player_image_url
            try:
                response = requests.get(image_url)
                player_image = Image.open(BytesIO(response.content))
                player_image = self.__center_crop(player_image, (500,700))
                player_image = self.__round_corners(player_image, 20)
            except:
                player_image = Image.open(default_image_path)

        # LOAD SHOWDOWN TEMPLATE
        showdown_template_frame_image = self.__template_image()
        player_image.paste(showdown_template_frame_image,(0,0),showdown_template_frame_image)

        # CREATE NAME TEXT
        name_text, color = self.__player_name_text_image()
        player_image.paste(color, sc.IMAGE_LOCATIONS['player_name'][str(self.context)],  name_text)

        # ADD TEAM LOGO
        try:
            team_logo = Image.open(os.path.join('static', 'logos', '{}.png'.format(self.team))).convert("RGBA")
            team_logo = team_logo.resize(sc.IMAGE_SIZES['team_logo'][str(self.context)], Image.ANTIALIAS)
        except:
            team_logo = Image.open(os.path.join('static', 'logos', 'mlb.png')).convert("RGBA")
            team_logo = team_logo.resize((90, 49), Image.ANTIALIAS)
        team_logo = team_logo.rotate(10,resample=Image.BICUBIC) if self.context == '2002' else team_logo
        player_image.paste(team_logo, sc.IMAGE_LOCATIONS['team_logo'][str(self.context)], team_logo)

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

        # ICONS
        if int(self.context) > 2002:
            icon_positional_mapping = [(335,635), (335,610), (310,635), (310,610)]
            for index, icon in enumerate(self.icons[0:4]):
                icon_image = Image.open(os.path.join('static', 'templates', '{}.png'.format(icon)))
                player_image.paste(icon_image, icon_positional_mapping[index], icon_image)

        set_image = self.__card_set_image()
        player_image.paste(set_image, (0,0), set_image)

        # SAVE AND SHOW IMAGE
        self.image_name = '{name}-{timestamp}.png'.format(name=self.name, timestamp=str(datetime.now()))
        player_image.save(os.path.join('static', 'images', self.image_name))
        self.__clean_images_directory()

    def __clean_images_directory(self):
        """Removes all images from output folder that are not the current card.

        Args:
          None

        Returns:
          None
        """
        for item in os.listdir(os.path.join('static', 'images')):
            if item != self.image_name and item != '.gitkeep':
                os.remove(os.path.join('static', 'images', item))

    def __text_image(self,text,size,font,rotation=0,alignment='left',padding=0,spacing=3,opacity=1):
        """Generates a new PIL image object with text.

        Args:
          text: string of text to display.
          size: Tuple of image size.
          font: PIL font object.
          rotation: Degrees of rotation for the text (optional)
          alignment: String (left, center, right) for alignment of text within image.
          padding: Number of pixels worth of padding from image edge.
          spacing: Pixels of space between lines of text.
          opacity: Transparency of text.

        Returns:
          PIL image object with desired text and formatting.
        """
        text_layer = Image.new('L', size)
        draw = ImageDraw.Draw(text_layer)
        w, h = draw.textsize(text, font=font)
        if alignment == "center":
            x = (size[0]-w) / 2.0
        elif alignment == "right":
            x = size[0] - padding - w
        else:
            x = 0 + padding
        draw.text((x, 0), text, font=font, spacing=spacing, fill=255, align=alignment)
        rotated_text_layer = text_layer.rotate(rotation, expand=1)
        return rotated_text_layer

    def __template_image(self):
        """Loads showdown frame template depending on player context.

        Args:
          None

        Returns:
          PIL image object for Player's template background.
        """
        year = str(self.context)
        type = 'Pitcher' if self.is_pitcher else 'Hitter'
        if year in ['2000','2001']:
            template_image_name = '{context}-{type}-{command}.png'.format(
                context = year,
                type = type,
                command = str(self.chart['command'])
            )
            if self.is_pitcher:
                template_image = Image.open(os.path.join('static', 'templates', template_image_name))
            else:
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
                template_image = Image.open(os.path.join('static', 'templates', positions_points_template))
                player_template_image = Image.open(os.path.join('static', 'templates', template_image_name))
                template_image.paste(player_template_image, (0,0), player_template_image)
        elif year == '2002':
            type_template = '{context}-{type}.png'.format(context = year, type = type)
            template_image = Image.open(os.path.join('static', 'templates', type_template))
            command_image_name = '{context}-{type}-{command}.png'.format(
                context = year,
                type = type,
                command = str(self.chart['command'])
            )
            command_image = Image.open(os.path.join('static', 'templates', command_image_name))
            template_image.paste(command_image, (0,0), command_image)
        elif year == '2003':
            template_image_name = '{context}-{type}-{command}.png'.format(
                context = year,
                type = type,
                command = str(self.chart['command'])
            )
            template_image = Image.open(os.path.join('static', 'templates', template_image_name))
        else:
            template_image_name = '2000-Pitcher.png'
            template_image = Image.open(os.path.join('static', 'templates', template_image_name))

        return template_image

    def __player_name_text_image(self):
        """Creates Player name to match showdown context.

        Args:
          None

        Returns:
          Tuple
            - PIL image object for Player's name.
            - Hex Color of text as a String
        """
        first, last = self.name.upper().split(" ", 1)
        name = self.name.upper() if self.context != '2001' else first

        futura_black_path = os.path.join('static', 'fonts', 'Futura Black.ttf')
        helvetica_neue_lt_path = os.path.join('static', 'fonts', 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique.ttf')

        if self.context == '2000':
            name_rotation = 90
            name_alignment = "center"
            name_size = 45
            name_color = "#FDFBF4"
            padding = 0
            name_font_path = helvetica_neue_lt_path
        elif self.context == '2001':
            name_rotation = 90
            name_alignment = "left"
            name_size = 32
            name_color = "#FDFBF4"
            padding = 0
            name_font_path = futura_black_path
        elif self.context == '2002':
            name_rotation = 90
            name_alignment = "left"
            name_size = 48
            name_color = "#A09D9F"
            padding = 5
            name_font_path = helvetica_neue_lt_path
        elif self.context == '2003':
            name_rotation = 90
            name_alignment = "right"
            name_size = 32
            name_color = "#FFFFFF"
            padding = 20
            name_font_path = helvetica_neue_lt_path
        else:
            rotation = 0
            name_font_path = helvetica_neue_lt_path

        name_font = ImageFont.truetype(name_font_path, size=name_size)

        final_text = self.__text_image(
            text = name,
            size = sc.IMAGE_SIZES['player_name'][self.context],
            font = name_font,
            rotation = name_rotation,
            alignment = name_alignment,
            padding = padding
        )
        if self.context == '2000':
            text_stretched = final_text.resize((100,1700), Image.ANTIALIAS)
            final_text = text_stretched.crop((0,515,100,1185))
        elif self.context == '2001':
            last_name = self.__text_image(
                text = last,
                size = sc.IMAGE_SIZES['player_name'][self.context],
                font = ImageFont.truetype(name_font_path, size=45),
                rotation = name_rotation,
                alignment = name_alignment,
                padding = padding
            )
            final_text.paste(name_color, (30,0), last_name)

        return final_text, name_color

    def __metadata_image(self):

        year = int(self.context)
        color = "#FFFFFF"
        if year in [2000,2001]:
            metadata_image = Image.new('RGBA', (500, 700), 255)
            helvetica_neue_lt_path = os.path.join('static', 'fonts', 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique.ttf')

            if self.is_pitcher:
                # POSITION
                font_position = ImageFont.truetype(helvetica_neue_lt_path, size=24)
                position = list(self.positions_and_defense.keys())[0]
                position_text = self.__text_image(text=position, size=(300, 100), font=font_position)
                metadata_image.paste("#FFFFFF", (325,114), position_text)
                # HAND | IP
                font_hand_ip = ImageFont.truetype(helvetica_neue_lt_path, size=21)
                hand_text = self.__text_image(text=self.hand, size=(300, 100), font=font_hand_ip)
                metadata_image.paste("#FFFFFF", (364,140), hand_text)
                ip_text = self.__text_image(text='IP {}'.format(str(self.ip)), size=(300, 100), font=font_hand_ip)
                metadata_image.paste("#FFFFFF", (420,140), ip_text)

            else:
                # SPEED | HAND

                font_speed_hand = ImageFont.truetype(helvetica_neue_lt_path, size=18)
                speed_text = self.__text_image(text='SPEED {}'.format(self.speed_letter), size=(300, 100), font=font_speed_hand)
                hand_text = self.__text_image(text=self.hand[-1], size=(100, 100), font=font_speed_hand)
                metadata_image.paste(color, (323 if self.context == '2000' else 305,114), speed_text)
                metadata_image.paste(color, (404,114), hand_text)
                if self.context == '2001':
                    # ADD # TO SPEED
                    font_speed_number = ImageFont.truetype(helvetica_neue_lt_path, size=14)
                    font_parenthesis = ImageFont.truetype(helvetica_neue_lt_path, size=15)
                    spd_letter_to_number = {
                        'A': 20,
                        'B': 15,
                        'C': 10
                    }
                    speed_num_text = self.__text_image(
                        text=str(spd_letter_to_number[self.speed_letter]),
                        size=(100, 100),
                        font=font_speed_number
                    )
                    parenthesis_left = self.__text_image(text='(   )', size=(100, 100), font=font_parenthesis)
                    metadata_image.paste(color, (372,114), parenthesis_left)
                    metadata_image.paste(color, (376,115), speed_num_text)
                # POSITION(S)
                font_position = ImageFont.truetype(helvetica_neue_lt_path, size=26)
                ordered_by_len_position = sorted(self.positions_and_defense.items(), key=operator.itemgetter(0), reverse=True)
                y_position = 135
                for position, rating in ordered_by_len_position:
                    speed_text = self.__text_image(text='{} +{}'.format(position,str(rating)), size=(200, 100), font=font_position)
                    x_position = 361 if len(position) > 4 else 387
                    x_position += 6 if position == 'C' and rating < 10 else 0 # CATCHER POSITIONING ADJUSTMENT
                    metadata_image.paste(color, (x_position,y_position), speed_text)
                    y_position += 28

            # POINTS
            text_size = 16 if self.points >= 1000 else 19
            font_pts = ImageFont.truetype(helvetica_neue_lt_path, size=text_size)
            pts_text = self.__text_image(text=str(self.points), size=(100, 100), font=font_pts, alignment = "right")
            pts_y_pos = 190 if len(self.positions_and_defense) > 1 else 164
            pts_x_pos = 323 if self.is_pitcher else 333
            metadata_image.paste(color, (pts_x_pos,pts_y_pos), pts_text)

        elif year in [2002,2003]:
            color = "#000000" if self.context == '2002' else "#FFFFFF"
            if year == 2002:
                helvetica_neue_lt_path = os.path.join('static', 'fonts', 'Helvetica-Neue-LT-Std-97-Black-Condensed-Oblique.ttf')
                metadata_font = ImageFont.truetype(helvetica_neue_lt_path, size=40)
            else:
                helvetica_neue_cond_bold_path = os.path.join('static', 'fonts', 'Helvetica Neue 77 Bold Condensed.ttf')
                metadata_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=45)

            metadata_text = self.__text_image(
                text = self.__player_metadata_summary_text(),
                size = (255, 900),
                font = metadata_font,
                rotation = 0,
                alignment = "right",
                padding=0,
                spacing= 22 if self.context == '2003' else 19
            )
            metadata_image = metadata_text.resize((85,300), Image.ANTIALIAS)

        return metadata_image, color

    def __chart_image(self):

        helvetica_neue_cond_bold_path = os.path.join('static', 'fonts', 'Helvetica Neue 77 Bold Condensed.ttf')
        chart_text_size = int(sc.TEXT_SIZES['chart'][self.context])
        helvetica_neue_cond_bold_alt = ImageFont.truetype(helvetica_neue_cond_bold_path, size=chart_text_size)

        # CREATE CHART RANGES TEXT
        chart_string = ''
        for category in self.__chart_categories():
            range = self.chart_ranges['{} Range'.format(category)]
            chart_string += '{}\n'.format(range)

        spacing = int(sc.TEXT_SIZES['chart_spacing'][self.context])
        chart_text = self.__text_image(
            text = chart_string,
            size = (255, 1200),
            font = helvetica_neue_cond_bold_alt,
            rotation = 0,
            alignment = "right",
            padding=0,
            spacing=spacing
        )
        color = "#000000" if self.context == '2002' else "#414040"
        return chart_text.resize((85,400), Image.ANTIALIAS), color

    def __card_set_image(self):
        """Creates image with card number and year text

        Args:
          None

        Returns:
          PIL image object for set text.
        """
        helvetica_neue_cond_bold_path = os.path.join('static', 'fonts', 'Helvetica Neue 77 Bold Condensed.ttf')
        set_font = ImageFont.truetype(helvetica_neue_cond_bold_path, size=45)

        set_image = Image.new('RGBA', (500, 700), 255)
        set_image_location = sc.IMAGE_LOCATIONS['set'][str(self.context)]
        if self.context in ['2000','2001','2002']:
            set_text = self.__text_image(
                text = '001 / 462' if self.context == '2002' else '001/462',
                size = (200, 100),
                font = set_font,
                alignment = "left"
            )
            set_text = set_text.resize((50,25), Image.ANTIALIAS)
            set_image.paste("#FFFFFF", set_image_location, set_text)

        elif self.context == '2003':
            # CARD YEAR
            year_text = self.__text_image(
                text = "'{}".format(str(self.year)[2:4]),
                size = (150, 150),
                font = set_font,
                alignment = "left"
            )
            year_text = year_text.resize((40,40), Image.ANTIALIAS)
            set_image.paste("#FFFFFF", (31,595), year_text)

            # CARD NUMBER
            number_text = self.__text_image(
                text = '001',
                size = (150, 150),
                font = set_font,
                alignment = "left"
            )
            number_text = number_text.resize((40,40), Image.ANTIALIAS)
            set_image.paste("#000000", set_image_location, number_text)

        return set_image

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
        """Uses image size to crop in the middle for given crop size

        Args:
          image: PIL image object to edit.
          crop_size: Tuple representing width and height of desired crop.

        Returns:
          Cropped PIL image object.
        """

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

    def __scrape_player_image_url(self,url=None):
        """ Scrape google images for guess on picture to use for
        player background.

        Args:
            None

        Returns:
          String url of first player image on google search.
        """
        query = '{name}+{year}+{type}'.format(
            name = self.name.replace(' ', '+'),
            year = str(self.year),
            type = 'pitching' if self.is_pitcher else 'batting'
        )
        url = 'https://www.bing.com/images/search?q=' + query + '&qft=+filterui:photo-photo+filterui:imagesize-large&form=IRFLTR&first=1&scenario=ImageHoverTitle'
        header = {'User-Agent':"Chrome/84.0.4147.135"}
        html = urlopen(Request(url, headers=header))
        soup = BeautifulSoup(html, 'html.parser')
        first_image = soup.find('li',{ 'data-idx': "1" })
        first_image_attributes = first_image.find('a', {'class': "iusc"})
        first_image_url = json.loads(first_image_attributes.get("m"))['murl']
        return first_image_url
