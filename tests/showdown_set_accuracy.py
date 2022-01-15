
import pandas as pd
import math
from time import sleep
import os
from pathlib import Path
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown_bot.showdown_player_card_generator import ShowdownPlayerCardGenerator
import mlb_showdown_bot.showdown_constants as sc

class ShowdownSetAccuracy:

# ------------------------------------------------------------------------
# INIT

    def __init__(self, context, real_player_stats_cache, wotc_card_outputs, command_control_combo=None, is_only_command_outs_accuracy=False, ignore_volatile_categories=False, is_pts_only=False,use_wotc_command_outs=False,command_out_combos=[]):
        self.context = context
        self.real_player_stats_cache = real_player_stats_cache
        self.wotc_card_outputs = wotc_card_outputs
        self.command_control_combo = command_control_combo
        self.is_only_command_outs_accuracy = is_only_command_outs_accuracy
        self.ignore_volatile_categories = ignore_volatile_categories
        self.is_pts_only = is_pts_only
        self.use_wotc_command_outs = use_wotc_command_outs
        self.command_out_combos = command_out_combos

# ------------------------------------------------------------------------
# MEASURE ACCURACY METHODS

    def calc_set_accuracy(self):
        """Calculate accuracy of an a set of the custom generated cards vs. the actual
        official MLB Showdown card set.

        Args:
          None

        Returns:
          Dict with in game positions and defensive ratings
        """

        sum_of_card_accuracy = 0
        num_perfect_match = 0
        perfect_match_players = []
        category_accuracies = []
        category_accuracies_for_command_matches = []
        command_match_players = []
        category_above_below_list = []
        category_above_below_list_for_matches = []
        command_out_accuracies = {}
        category_above_below_for_command_outs = {}
        positional_above_below = {}
        positional_accuracies = {}
        players_excluded_from_testing = sc.EXCLUDED_PLAYERS_FOR_TESTING[str(self.context)]

        for index, wotc_player_card in self.wotc_card_outputs.iterrows():
            
            name_year_string = '{} - {}'.format(wotc_player_card.Name,str(wotc_player_card.Year))
            is_player_stats_in_cache = name_year_string in self.real_player_stats_cache.NameAndYear.values

            if is_player_stats_in_cache:
                # HAVE ALREADY SCRAPED DATA LOCALLY
                real_player_stats = self.real_player_stats_cache[self.real_player_stats_cache.NameAndYear == name_year_string]
                real_player_stats = real_player_stats.where(pd.notnull(real_player_stats), 0)
                real_player_stats = real_player_stats.to_dict('records')[0]
            else:
                # NEED TO SCRAPE FROM BASEBALL REFERENCE
                if wotc_player_card.Name in players_excluded_from_testing:
                    print('Skipping - {}'.format(wotc_player_card.Name))
                    continue
                try:
                    print('Scraping - {} stats for {}'.format(wotc_player_card.Name, str(wotc_player_card.Year - 1)))
                    scraper = BaseballReferenceScraper(wotc_player_card.Name,str(self.context-1))
                    real_player_stats = scraper.player_statline()
                    real_player_stats['NameAndYear'] = name_year_string
                    self.real_player_stats_cache = self.real_player_stats_cache.append(pd.DataFrame.from_records([real_player_stats]), sort=False)
                    sleep(10) # DO NOT WANT TO MAKE TOO MANY QUICK REQUESTS TO BASEBALL REFERENCE
                except:
                    continue
            
            # USER CAN TEST CHART WITH CORRECT WOTC COMMAND/OUTS
            command_out_override = None
            if self.use_wotc_command_outs:
                command_out_override = (wotc_player_card.OnbaseOrControl,wotc_player_card.OUTS)

            my_player_card = ShowdownPlayerCardGenerator(wotc_player_card.Name,str(self.context-1),real_player_stats,str(self.context),test_numbers=self.command_control_combo, run_stats= self.is_pts_only==False, offset=0,command_out_override=command_out_override)
            
            # IF CALCULATING POINTS, WE WANT TO USE ORIGINAL SET STATS
            if self.is_pts_only:
                my_player_card = self.__convert_wotc_to_showdown_player_object(wotc_player_card, my_player_card)
            wotc_player_card_dict = self.__parse_player_card_categories_for_accuracy(wotc_player_card=wotc_player_card, is_pitcher=my_player_card.is_pitcher)
            command_outs_str = '{}-{}'.format(my_player_card.chart['command'],my_player_card.chart['outs'])

            # ---- APPEND TO ACCURACY TRACKING OBJECTS ----
            if self.command_out_combos != [''] and command_outs_str not in self.command_out_combos:
                continue
            else:
                if self.is_pts_only:
                    print(my_player_card.points - wotc_player_card.PTS, wotc_player_card.Name,('Me', my_player_card.points),('WOTC', wotc_player_card.PTS)) 
                    # my_player_card.print_player()
                else:
                    print(my_player_card.positions_and_defense)
                    print(wotc_player_card.Name,('Me', list(my_player_card.positions_and_defense.values())[0]),('WOTC', wotc_player_card.Fielding1))
            
            accuracy, categorical_accuracy, categorical_above_below = my_player_card.accuracy_against_wotc(wotc_card_dict=wotc_player_card_dict, is_pts_only=self.is_pts_only)
            sum_of_card_accuracy += accuracy

            # ADD TO COMMAND OUT CATEGORY
            if self.is_pts_only:
                if command_outs_str in command_out_accuracies.keys():
                    command_out_accuracies[command_outs_str].append(categorical_accuracy['points'])
                    category_above_below_for_command_outs[command_outs_str].append(categorical_above_below)
                else:
                    command_out_accuracies[command_outs_str] = [categorical_accuracy['points']]
                    category_above_below_for_command_outs[command_outs_str] = [categorical_above_below]

                # ADD TO POSITIONS
                for position in my_player_card.positions_and_defense.keys():
                    if position in positional_accuracies.keys():
                        positional_accuracies[position].append(categorical_accuracy['points'])
                        positional_above_below[position].append(categorical_above_below)
                    else:
                        positional_accuracies[position] = [categorical_accuracy['points']]
                        positional_above_below[position] = [categorical_above_below]

            # CARD IS PERFECT
            is_perfect = accuracy == 1
            if is_perfect:
                num_perfect_match += 1
                perfect_match_players.append(wotc_player_card.Name)
            
            # CARD IS MATCH FOR COMMAND-OUTS
            is_command_match = categorical_accuracy['command-outs'] == 1.0
            if is_command_match:
                category_accuracies_for_command_matches.append(categorical_accuracy)
                command_match_players.append(wotc_player_card.Name)
                category_above_below_list_for_matches.append(categorical_above_below)

            category_accuracies.append(categorical_accuracy)
            category_above_below_list.append(categorical_above_below)
            
        # CALC COMMAND OUT ACCURACY ACROSS PLAYERS
        command_outs_summarized = {}
        for command_out, accuracy_list in command_out_accuracies.items():
            command_outs_summarized[command_out] = round(sum(accuracy for accuracy in accuracy_list) / len(accuracy_list),4)

        # CALC COMMAND OUT ABOVE BELOW ACROSS PLAYERS
        all_command_out_categories_above_below_summarized = {}
        for command_out, category_above_below_list in category_above_below_for_command_outs.items():
            categories_above_below_summarized = {}
            if len(category_above_below_list) > 0:
                for category in category_above_below_list[0].keys():
                    if category == 'points':
                        category_dict = {}
                        for above_or_below in ['above_wotc', 'below_wotc', 'matches_wotc', 'difference_wotc']:
                            denominator = float(len(category_above_below_list)) if above_or_below == 'difference_wotc' else 1.0
                            category_dict[above_or_below] = sum(player[category][above_or_below] for player in category_above_below_list) / denominator
                        categories_above_below_summarized[category] = category_dict
                all_command_out_categories_above_below_summarized[command_out] = categories_above_below_summarized
        
        # CALC POSITIONAL ACROSS PLAYERS
        positional_accuracy_summarized = {}
        for position, accuracy_list in positional_accuracies.items():
            positional_accuracy_summarized[position] = round(sum(accuracy for accuracy in accuracy_list) / len(accuracy_list),4)

        # CALC POSITION ABOVE BELOW ACROSS PLAYERS
        all_positions_above_below_summarized = {}
        for position, category_above_below_list in positional_above_below.items():
            categories_above_below_summarized = {}
            if len(category_above_below_list) > 0:
                for category in category_above_below_list[0].keys():
                    if category == 'points':
                        category_dict = {}
                        for above_or_below in ['above_wotc', 'below_wotc', 'matches_wotc', 'difference_wotc']:
                            denominator = float(len(category_above_below_list)) if above_or_below == 'difference_wotc' else 1.0
                            category_dict[above_or_below] = sum(player[category][above_or_below] for player in category_above_below_list) / denominator
                        categories_above_below_summarized[category] = category_dict
                all_positions_above_below_summarized[position] = categories_above_below_summarized
        
        # CALC CATEGORICAL ACCURACY ACROSS PLAYERS
        categories_summarized = {}
        if len(category_accuracies) > 0:
            for category in category_accuracies[0].keys():
                categories_summarized[category] = round(sum(player[category] for player in category_accuracies) / len(category_accuracies),4)

        # CALC CATEGORICAL ACCURACY ACROSS PLAYERS (ONLY FOR COMMAND-OUT MATCHES)
        is_command_match = len(category_accuracies_for_command_matches) > 0
        categories_for_matches_summarized = {}
        if is_command_match:
            for category in category_accuracies_for_command_matches[0].keys():
                categories_for_matches_summarized[category] = round(sum(player[category] for player in category_accuracies_for_command_matches) / len(category_accuracies_for_command_matches),4)

        # CALC CATEGORICAL ACCURACY ACROSS PLAYERS
        categories_above_below_summarized = {}
        categories_above_below_summarized_for_matches = {}
        if len(category_above_below_list) > 0:
            for category in category_above_below_list[0].keys():
                category_dict = {}
                category_dict_for_matches = {}
                for above_or_below in ['above_wotc', 'below_wotc', 'matches_wotc', 'difference_wotc']:
                    denominator = float(len(category_above_below_list)) if above_or_below == 'difference_wotc' else 1.0
                    denominator_matches = float(len(category_above_below_list_for_matches)) if above_or_below == 'difference_wotc' else 1.0
                    category_dict[above_or_below] = sum(player[category][above_or_below] for player in category_above_below_list) / denominator
                    category_dict_for_matches[above_or_below] = sum(player[category][above_or_below] for player in category_above_below_list_for_matches) / denominator_matches if denominator_matches != 0 else 1
                categories_above_below_summarized[category] = category_dict
                categories_above_below_summarized_for_matches[category] = category_dict_for_matches
        
        # STORE NEWLY CACHED PLAYERS IF ANY
        cache_destination_path = os.path.join(Path(os.path.dirname(__file__)),'cache','player_cache.csv')
        self.real_player_stats_cache.to_csv(cache_destination_path, index= False)

        return (
            sum_of_card_accuracy, 
            num_perfect_match, 
            categories_summarized, 
            categories_for_matches_summarized, 
            categories_above_below_summarized, 
            categories_above_below_summarized_for_matches, 
            perfect_match_players, 
            command_match_players,
            command_outs_summarized,
            all_command_out_categories_above_below_summarized,
            positional_accuracy_summarized,
            all_positions_above_below_summarized,
        )

    def __parse_player_card_categories_for_accuracy(self,wotc_player_card,is_pitcher):
        """Creates dictionary of WOTC card output for only the categories used to calculate
        card accuracy.

        Args:
          wotc_player_card: Pandas DataFrame row for WOTC official player card.
          is_pitcher: Boolean for whether the player is a pitcher.
        Returns:
          Dict of player attributes used in accuracy comparison.
        """
            
        wotc_player_card_dict = {
            'command-outs': '{}-{}'.format(int(wotc_player_card.OnbaseOrControl),int(wotc_player_card.OUTS))
        }

        # IF TESTING FOR POINTS
        if self.is_pts_only:
            wotc_player_card_dict['points'] = int(wotc_player_card['PTS'])
            return wotc_player_card_dict

        if not self.is_only_command_outs_accuracy:
            wotc_player_card_dict.update({
                '1b': int(wotc_player_card['1B']),
                '2b': int(wotc_player_card['2B']) if int(wotc_player_card['2B']) < 21 else 0,
                'bb': int(wotc_player_card['BB']),
                'fb': int(wotc_player_card['FB']),
                'gb': int(wotc_player_card['GB']),
                'hr': int(wotc_player_card['HR']) if int(wotc_player_card['HR']) < 21 else 0,
                'so': int(wotc_player_card['SO']),
            })
            if is_pitcher:
                wotc_player_card_dict.update({'pu': int(wotc_player_card['PU'])})
            else:
                wotc_player_card_dict.update({
                    '1b+': int(wotc_player_card['1B+']),
                    '3b': int(wotc_player_card['3B']) if int(wotc_player_card['3B']) < 21 else 0,
                    'spd': int(wotc_player_card['Speed']),
                    'defense': int(wotc_player_card['Fielding1'])
                })
        
        # REMOVE EXCLUDED CATEGORIES
        if self.ignore_volatile_categories:
            if not is_pitcher:
                wotc_player_card_dict['1b'] = wotc_player_card_dict['1b'] + wotc_player_card_dict['1b+']
            excluded_categories = ['so', 'gb', 'fb', '1b+', 'pu']
            
                
            for category in excluded_categories:
                if category in wotc_player_card_dict.keys():
                    del wotc_player_card_dict[category]
        return wotc_player_card_dict

    def __convert_wotc_to_showdown_player_object(self,wotc_player_card,my_player_card):
        """Creates Showdown Player Card Generator object version of WOTC stats

        Args:
          wotc_player_card: Pandas DataFrame row for WOTC official player card.
          my_player_card: Showdown Player Card Generator object

        Returns:
          Showdown Player Card Generator object w/ WOTC stats
        """

        # ADD CLASS ATTRIBUTES NEEDED TO CALCULATE POINTS
        my_player_card.team = wotc_player_card.Team
        my_player_card.is_pitcher = wotc_player_card.Type == 'Pitcher'
        my_player_card.hand = wotc_player_card.Hand
        my_player_card.chart = {
            '1b': 0 if wotc_player_card['1B'] > 20 else wotc_player_card['1B'],
            '1b+': wotc_player_card['1B+'],
            '2b': wotc_player_card['2B For Calcs'],
            '3b': wotc_player_card['3B For Calcs'],
            'bb': wotc_player_card['BB'],
            'command': wotc_player_card.OnbaseOrControl,
            'fb': wotc_player_card['FB'],
            'gb': wotc_player_card['GB'],
            'hr': wotc_player_card['HR For Calcs'],
            'outs': wotc_player_card.OUTS,
            'pu': wotc_player_card['PU'],
            'so': wotc_player_card['SO'],
        }
        opponent_chart, my_advantages_per_20, opponent_advantages_per_20 = my_player_card.opponent_stats_for_calcs(command=wotc_player_card.OnbaseOrControl)
        chart_results_per_400_pa = my_player_card.chart_to_results_per_400_pa(my_player_card.chart, my_advantages_per_20, opponent_chart, opponent_advantages_per_20)
        my_player_card.real_stats = my_player_card.stats_for_full_season(stats_per_400_pa=chart_results_per_400_pa)
        rep = {"SP": "STARTER", "RP": "RELIEVER", "CL": "CLOSER"}
        position_1 = str(wotc_player_card.Position1)            
        if position_1 in rep.keys():
            position_1 = rep[position_1]
        defense = {position_1: wotc_player_card.Fielding1}
        if wotc_player_card.Position2 is not None and not str(wotc_player_card.Position2) == 'nan':
            defense[str(wotc_player_card.Position2)] = wotc_player_card.Fielding2
        if wotc_player_card.Position3 is not None and not str(wotc_player_card.Position3) == 'nan':
            defense[str(wotc_player_card.Position3)] = wotc_player_card.Fielding3
        if int(self.context) > 2001 and 'C' in defense.keys():
            defense['CA'] = defense['C']
            del defense['C']

        my_player_card.positions_and_defense = defense
        my_player_card.ip = int(wotc_player_card.IP)
        icons = [wotc_player_card.Icon1, wotc_player_card.Icon2, wotc_player_card.Icon3, wotc_player_card.Icon4]
        icons = [x for x in icons if str(x) != 'nan']
        my_player_card.icons = icons
        my_player_card.chart_ranges = my_player_card.ranges_for_chart(my_player_card.chart, 5.0, 5.0, 5.0)
        my_player_card.speed = wotc_player_card.Speed
        if wotc_player_card.Speed < 12:
            letter = 'C'
        elif wotc_player_card.Speed < 18:
            letter = 'B'
        else:
            letter = 'A'
        my_player_card.speed_letter = letter
        my_player_card.points = my_player_card.point_value(chart=my_player_card.chart,
                                                            real_stats=my_player_card.real_stats,
                                                            positions_and_defense=defense,
                                                            speed_or_ip=my_player_card.ip if my_player_card.is_pitcher else wotc_player_card.Speed)
        return my_player_card