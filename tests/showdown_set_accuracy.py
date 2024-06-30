
import pandas as pd
import math
from time import sleep
import os
from pathlib import Path
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown_bot.showdown_player_card import ShowdownPlayerCard, Set, ChartCategory
from mlb_showdown_bot.classes.team import Team
from mlb_showdown_bot.classes.icon import Icon
from mlb_showdown_bot.postgres_db import PlayerArchive

class ShowdownSetAccuracy:

# ------------------------------------------------------------------------
# INIT

    def __init__(self, set: Set, real_stats: list[PlayerArchive], wotc_cards: dict[str, ShowdownPlayerCard], command_control_combo=None, is_only_command_outs_accuracy=False, ignore_volatile_categories=False, is_pts_only=False,use_wotc_command_outs=False,command_out_combos=[]):
        self.set = set
        self.real_stats = real_stats
        self.wotc_cards = wotc_cards
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
        player_ids_to_skip = [
            '2004-spoonti01-2005-BS', # TIM SPOONEYBARGER
            '2004-hernaru03-2005-BS', # RUNELVYS HERNANDEZ
        ]

        for id, wotc_card in self.wotc_cards.items():
            
            # SKIP CERTAIN PLAYERS
            if id in player_ids_to_skip:
                continue

            # GET REAL STATS
            player_matches = [pa.stats for pa in self.real_stats if pa.bref_id in id]
            if len(player_matches) == 0:
                raise Exception(f'No stats found for {wotc_card.name} (id: {id})')
            real_player_stats: dict[str, any] = next(iter(player_matches))
            
            # USER CAN TEST CHART WITH CORRECT WOTC COMMAND/OUTS
            command_out_override = None
            if self.use_wotc_command_outs:
                command_out_override = (wotc_card.chart.command, wotc_card.chart.outs)

            showdown_bot_card = ShowdownPlayerCard(
                name = wotc_card.name,
                year = str(int(self.set.year) - 1),
                stats = real_player_stats,
                set = self.set,
                test_numbers = self.command_control_combo, 
                run_stats = self.is_pts_only==False, 
                command_out_override = command_out_override
            )
            
            # IF CALCULATING POINTS, WE WANT TO USE ORIGINAL SET STATS
            if self.is_pts_only:
                showdown_bot_card = wotc_card
            
            wotc_card_dict = self.__parse_player_card_categories_for_accuracy(wotc_card=wotc_card, is_pitcher=showdown_bot_card.is_pitcher)
            command_outs_str = f'{showdown_bot_card.chart.command}-{showdown_bot_card.chart.outs}'

            # ---- APPEND TO ACCURACY TRACKING OBJECTS ----
            if self.command_out_combos != [''] and command_outs_str not in self.command_out_combos:
                continue
            else:
                if self.is_pts_only:
                    print(showdown_bot_card.points - wotc_card.points, wotc_card.name, ('Me', showdown_bot_card.points),('WOTC', wotc_card.points)) 
                else:
                    print(wotc_card.name, ('Me', showdown_bot_card.chart.command, showdown_bot_card.chart.outs),('WOTC', wotc_card.chart.command, wotc_card.chart.outs))
            
            accuracy, categorical_accuracy, categorical_above_below = showdown_bot_card.accuracy_against_wotc(wotc_card_dict=wotc_card_dict, is_pts_only=self.is_pts_only)
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
                for position in showdown_bot_card.positions_and_defense.keys():
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
                perfect_match_players.append(wotc_card.name)
            
            # CARD IS MATCH FOR COMMAND-OUTS
            is_command_match = categorical_accuracy['command-outs'] == 1.0
            if is_command_match:
                category_accuracies_for_command_matches.append(categorical_accuracy)
                command_match_players.append(wotc_card.name)
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

    def __parse_player_card_categories_for_accuracy(self,wotc_card: ShowdownPlayerCard, is_pitcher:bool):
        """Creates dictionary of WOTC card output for only the categories used to calculate
        card accuracy.

        Args:
          wotc_card: Showdown Card from WOTC
          is_pitcher: Boolean for whether the player is a pitcher.
        Returns:
          Dict of player attributes used in accuracy comparison.
        """
            
        wotc_card_dict = {
            'command-outs': '{}-{}'.format(int(wotc_card.chart.command),int(wotc_card.chart.outs)),
        }

        # IF TESTING FOR POINTS
        if self.is_pts_only:
            wotc_card_dict['points'] = wotc_card.points
            return wotc_card_dict

        if not self.is_only_command_outs_accuracy:
            categories = [ChartCategory._1B, ChartCategory._2B, ChartCategory.BB, ChartCategory.FB, ChartCategory.GB, ChartCategory.HR, ChartCategory.SO,]
            categories += [ChartCategory.PU] if is_pitcher else [ChartCategory._1B_PLUS, ChartCategory._3B,]
            wotc_card_dict.update({category.value.lower(): wotc_card.chart.values.get(category) for category in categories})
            if not is_pitcher:
                wotc_card_dict.update({
                    'spd': wotc_card.speed.speed,
                    'defense': list(wotc_card.positions_and_defense.values())[0]
                })

            wotc_card_dict.update({
                'onbase_perc': wotc_card.projected.get('onbase_perc', 0),
                'slugging_perc': wotc_card.projected.get('slugging_perc', 0),
            })
                        
        # REMOVE EXCLUDED CATEGORIES
        if self.ignore_volatile_categories:
            if not is_pitcher:
                wotc_card_dict['1b'] = wotc_card_dict['1b'] + wotc_card_dict['1b+']
            excluded_categories = ['so', 'gb', 'fb', '1b+', 'pu']
            
                
            for category in excluded_categories:
                if category in wotc_card_dict.keys():
                    del wotc_card_dict[category]
        return wotc_card_dict
