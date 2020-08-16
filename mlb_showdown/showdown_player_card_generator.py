
import pandas as pd
import math
import requests
import operator
import mlb_showdown.showdown_constants as sc
from pprint import pprint

class ShowdownPlayerCardGenerator:

# ------------------------------------------------------------------------
# INIT

    def __init__(self, name, year, stats, context, offset=0, test_numbers=None, printOutput=False):
        self.name = name
        self.year = year
        self.context = context
        self.stats = stats

        self.test_numbers = test_numbers
        self.is_pitcher = True if stats['type'] == 'Pitcher' else False

        self.__player_metadata(stats)

        stats_for_400_pa = self.__stats_per_n_pa(400, stats)
        command_out_combos = self.__top_accurate_command_out_combos(float(stats['onbase_perc']), 5)

        self.chart, chart_results_per_400_abs = self.__most_accurate_chart(command_out_combos, stats_for_400_pa, int(offset))
        self.chart_ranges = self.__ranges_for_chart(self.chart)
        self.real_stats = self.__stats_for_full_season(chart_results_per_400_abs)

        self.icons = self.__icons(stats['award_summary'])

        self.points = self.__point_value(self.chart, self.real_stats, self.positions_and_defense, self.speed)
        if printOutput:
            self.print_player()

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
        self.speed = self.__speed(sprint_speed_raw, stolen_bases_raw)

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

        for position_index in range(1, num_positions+1):
            position_raw = defensive_stats['Position{}'.format(position_index)]
            games_at_position = int(defensive_stats['gPosition{}'.format(position_index)])
            position = self.__position_in_game(position_raw,num_positions,games_at_position,games_played,games_started,saves)
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

        return self.__combine_like_positions(positions_and_defense)

    def __combine_like_positions(self, positions_and_defense):
        """Limit and combine positions (ex: combine LF and RF -> LF/RF)

        Args:
          positions_and_defense: Dict of positions and in game defensive ratings.

        Returns:
          Dict with relevant in game positions and defensive ratings
        """

        positions_set = set(positions_and_defense.keys())
        # IF HAS EITHER CORNER OUTFIELD POSITION
        if 'LF' in positions_set or 'RF' in positions_set:
            # IF BOTH LF AND RF
            if set(['LF','RF']).issubset(positions_set):
                lf_rf_rating = round((positions_and_defense['LF'] + positions_and_defense['RF']) / 2)
                del positions_and_defense['LF']
                del positions_and_defense['RF']
            # IF JUST LF
            elif 'LF' in positions_set:
                lf_rf_rating = positions_and_defense['LF']
                del positions_and_defense['LF']
            # IF JUST RF
            else:
                lf_rf_rating = positions_and_defense['RF']
                del positions_and_defense['RF']
            positions_and_defense['LF/RF'] = lf_rf_rating
            positions_set = set(positions_and_defense.keys())
        # IF PLAYER HAS ALL OUTFIELD POSITIONS
        if set(['LF/RF','CF','OF']).issubset(positions_set):
            if self.context in ['2000','2001','2002'] and positions_and_defense['LF/RF'] != positions_and_defense['CF']:
                del positions_and_defense['OF']
            else:
                del positions_and_defense['LF/RF']
                del positions_and_defense['CF']
        # IF JUST OF
        elif 'OF' in positions_set:
            del positions_and_defense['OF']

        return positions_and_defense

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
          In game speed ability.
        """

        if self.is_pitcher:
            # PITCHER DEFAULTS TO 10
            return 10

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

        return speed

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

        if position_appearances < sc.NUMBER_OF_GAMES:
            # IF POSIITION DOES NOT MEET REQUIREMENT, RETURN NONE
            return None
        elif position == 'DH' and num_positions > 1:
            # PLAYER MAY HAVE PLAYED AT DH, BUT HAS OTHER POSITIONS, SO DH WONT BE LISTED
            return None
        elif position == 'P':
            # PITCHER IS EITHER STARTER, RELIEVER, OR CLOSER
            gsRatio = games_started / games_played
            starter_threshold = 0.65
            if gsRatio > starter_threshold:
                return 'STARTER'
            if saves > 10:
                return 'CLOSER'
            else:
                return 'RELIEVER'
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

        icons = []
        for award, icon in awards_to_icon_map.items():
            if award in awards_upper:
                icons.append(icon)

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

        onbaseBaseline = sc.BASELINE_HITTER[self.context]['onbase'] if self.test_numbers is None else self.test_numbers[0]
        hitterOutsBaseline = sc.BASELINE_HITTER[self.context]['outs'] if self.test_numbers is None else self.test_numbers[1]
        controlBaseline = sc.BASELINE_PITCHER[self.context]['control'] if self.test_numbers is None else self.test_numbers[0]
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
            if '_per_400_pa' in category:
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
                chart[key] = round(chart_results) if chart_results > 0 else 0

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
            'batting_avg': 5.0,
            'slugging_perc': 2.0,
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

    def __ranges_for_chart(self, chart):
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

        for category in categories:
            category_results = int(chart[category])
            if category_results == 0:
                # EMPTY RANGE
                range = '-'
            elif category_results == 1:
                # RANGE IS CURRENT INDEX
                range = str(current_chart_index)
                current_chart_index += 1
            else:
                # MULTIPLE RESULTS
                range_start = current_chart_index
                range_end = current_chart_index + category_results - 1
                range = '{}-{}'.format(range_start,range_end)
                current_chart_index = range_end + 1

            chart_ranges['{} Range'.format(category)] = range

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

        pct_of_n_pa = float(stats['PA']) / plate_appearances
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

        chart_result_categories = ['SO','BB','1B','2B','3B','HR','SB']
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
        prob_result_after_hitter_advantage = num_results_hitter_chart / hitter_denominator
        prob_result_after_pitcher_advantage = num_results_pitcher_chart / pitcher_denominator
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

    def __point_value(self, chart, real_stats, positions_and_defense, speed):
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

        obp_points = sc.POINT_CATEGORY_WEIGHTS[self.context]['position_player']['onbase'] \
                     * self.stat_percentile(real_stats['onbase_perc'],sc.ONBASE_PCT_RANGE[self.context])
        ba_points = sc.POINT_CATEGORY_WEIGHTS[self.context]['position_player']['average'] \
                    * self.stat_percentile(real_stats['batting_avg'],sc.BATTING_AVG_RANGE[self.context])
        slg_points = sc.POINT_CATEGORY_WEIGHTS[self.context]['position_player']['slugging'] \
                     * self.stat_percentile(real_stats['slugging_perc'],sc.SLG_RANGE[self.context])
        spd_points = sc.POINT_CATEGORY_WEIGHTS[self.context]['position_player']['speed'] \
                     * self.stat_percentile(speed,sc.SPEED_RANGE[self.context])
        hr_points = sc.POINT_CATEGORY_WEIGHTS[self.context]['position_player']['home_runs'] \
                    * self.stat_percentile(real_stats['hr_per_650_pa'],sc.HR_RANGE[self.context])

        points += (obp_points + ba_points + slg_points + spd_points + hr_points)

        if not self.is_pitcher:
            defense_points = 0
            for position, fielding in positions_and_defense.items():
                if position != 'DH':
                    percentile = fielding / sc.POSITION_DEFENSE_RANGE[self.context][position]
                    positionPts = percentile * sc.POINT_CATEGORY_WEIGHTS[self.context]['position_player']['defense']
                    defense_points += positionPts
            points_per_position = defense_points / len(positions_and_defense.keys()) if len(positions_and_defense.keys()) > 0 else 1
            points += points_per_position

        return int(round(points,-1))

    def stat_percentile(self, stat, min_max_dict):
        """Get the percentile for a particular stat.

        Args:
          stat: Value to get percentile of.
          min_max_dict: Dict with 'min' and 'max' range values for the stat

        Returns:
          Points that the player is worth.
        """

        min = min_max_dict['min']
        max = min_max_dict['max']
        range = max - min
        stat_within_range = stat - min if stat - min > 0 else 0
        percentile = stat_within_range / range

        return percentile

# ------------------------------------------------------------------------
# GENERIC METHODS

    def accuracy_between_dicts(self, dict1, dict2, weights={}):
        """Compare two dictionaries of numbers to get overall difference

        Args:
          dict1: First Dictionary. Use this dict to get keys to compare.
          dict2: Second Dictionary.
          weights: X times to count certain category (ex: 3x for command)

        Returns:
          Float with accuracy and Dict with accuracy per key.
        """
        denominator = len(dict1.keys())
        output = {}
        accuracies = 0
        for key, value1 in dict1.items():
            if key in dict2.keys():
                value2 = dict2[key]
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
        return self.accuracy_between_dicts(wotc_card_dict,self.chart)

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
          None
        """

        print('\n ************************************************ \n')
        print('{} ({})'.format(self.name,self.year))
        print('{} Base Set Card\n'.format(self.context))

        for position,fielding in self.positions_and_defense.items():
            positionString = '{}+{}'.format(position,fielding) if not self.is_pitcher else position
            print(positionString)
        print(self.hand)
        if self.speed >= 18:
            speed_letter = 'A'
        elif self.speed >= 12:
            speed_letter = 'B'
        else:
            speed_letter = 'C'
        speed_letter
        ipOrSpeed = 'Speed {} ({})'.format(speed_letter,self.speed) if not self.is_pitcher else '{} IP'.format(self.ip)
        print(ipOrSpeed)
        print('{} PTS'.format(self.points))
        icon_string = ''
        for icon in self.icons:
            icon_string += '{}  '.format(icon)
        print(icon_string)

        print('\n{}: {}'.format('CONTROL' if self.is_pitcher else 'ONBASE',self.chart['command']))
        for category in self.__chart_categories():
            range = self.chart_ranges['{} Range'.format(category)]
            print('{}: {}'.format(category.upper(), range))

        print('\nStatline\n')
        print('{:<12}{:>12}'.format('Showdown', 'Real'))
        print('{:<12}{:>12}'.format('----------', '---------'))
        slash_categories = [('batting_avg', ' BA'),('onbase_perc', 'OBP'),('slugging_perc', 'SLG')]
        for key, cleaned_category in slash_categories:
            showdown_stat_str = '{}: {}'.format(cleaned_category,round(self.real_stats[key],3))
            real_stat_str = '{}: {}'.format(cleaned_category,self.stats[key])
            print('{:<12}{:>12}'.format(showdown_stat_str,real_stat_str))

        real_life_pa = int(self.stats['PA'])
        real_life_pa_ratio = int(self.stats['PA']) / 650.0
        print('{:<12}{:>12}'.format(' PA: {}'.format(real_life_pa),' PA: {}'.format(real_life_pa)))
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
            print('{:<12}{:>12}'.format(showdown_stat_str, real_stats_str))


        print('\n ************************************************ \n')
