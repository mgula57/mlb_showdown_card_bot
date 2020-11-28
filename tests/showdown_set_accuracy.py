
import pandas as pd
from time import sleep
import os
from pathlib import Path
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown_bot.showdown_player_card_generator import ShowdownPlayerCardGenerator
import mlb_showdown_bot.showdown_constants as sc

class ShowdownSetAccuracy:

# ------------------------------------------------------------------------
# INIT

    def __init__(self, context, real_player_stats_cache, wotc_card_outputs, command_control_combo=None, is_only_command_outs_accuracy=False, ignore_volatile_categories=False, is_pts_only=False):
        self.context = context
        self.real_player_stats_cache = real_player_stats_cache
        self.wotc_card_outputs = wotc_card_outputs
        self.command_control_combo = command_control_combo
        self.is_only_command_outs_accuracy = is_only_command_outs_accuracy
        self.ignore_volatile_categories = ignore_volatile_categories
        self.is_pts_only = is_pts_only

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
        category_accuracies = []
        category_above_below_list = []
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
                    scraper = BaseballReferenceScraper(wotc_player_card.Name,self.context-1)
                    real_player_stats = scraper.player_statline()
                    real_player_stats['NameAndYear'] = name_year_string
                    self.real_player_stats_cache = self.real_player_stats_cache.append(pd.DataFrame.from_records([real_player_stats]), sort=False)
                    sleep(10) # DO NOT WANT TO MAKE TOO MANY QUICK REQUESTS TO BASEBALL REFERENCE
                except:
                    continue

            my_player_card = ShowdownPlayerCardGenerator(wotc_player_card.Name,str(self.context-1),real_player_stats,str(self.context),test_numbers=self.command_control_combo)
            wotc_player_card_dict = self.__parse_player_card_categories_for_accuracy(wotc_player_card=wotc_player_card, is_pitcher=my_player_card.is_pitcher)

            accuracy, categorical_accuracy, categorical_above_below = my_player_card.accuracy_against_wotc(wotc_card_dict=wotc_player_card_dict, is_pts_only=self.is_pts_only)
            sum_of_card_accuracy += accuracy
            num_perfect_match += 1 if accuracy == 1 else 0
            category_accuracies.append(categorical_accuracy)
            category_above_below_list.append(categorical_above_below)

        # CALC CATEGORICAL ACCURACY ACROSS PLAYERS
        categories_summarized = {}
        for category in category_accuracies[0].keys():
            categories_summarized[category] = round(sum(player[category] for player in category_accuracies) / len(category_accuracies),4)

        # CALC CATEGORICAL ACCURACY ACROSS PLAYERS
        categories_above_below_summarized = {}
        for category in category_above_below_list[0].keys():
            category_dict = {}
            for above_or_below in ['above', 'below']:
                category_dict[above_or_below] = sum(player[category][above_or_below] for player in category_above_below_list)
            categories_above_below_summarized[category] = category_dict

        # STORE NEWLY CACHED PLAYERS IF ANY
        cache_destination_path = os.path.join(Path(os.path.dirname(__file__)),'cache','player_cache.csv')
        self.real_player_stats_cache.to_csv(cache_destination_path, index= False)

        return sum_of_card_accuracy, num_perfect_match, categories_summarized, categories_above_below_summarized

    def __parse_player_card_categories_for_accuracy(self,wotc_player_card,is_pitcher):
        """Creates dictionary of WOTC card output for only the categories used to calculate
        card accuracy.

        Args:
          wotc_player_card: Pandas DataFrame row for WOTC official player card.
          is_pitcher: Boolean for whether the player is a pitcher.
        Returns:
          Dict of player attributes used in accuracy comparison.
        """

        # IF TESTING FOR POINTS
        if self.is_pts_only:
            return { 'points': int(wotc_player_card['PTS']) }
            
        wotc_player_card_dict = {
            'command-outs': '{}-{}'.format(int(wotc_player_card.OnbaseOrControl),int(wotc_player_card.OUTS))
        }
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
                    '3b': int(wotc_player_card['3B']) if int(wotc_player_card['3B']) < 21 else 0,
                })
        
        # REMOVE EXCLUDED CATEGORIES
        if self.ignore_volatile_categories:
            type_specific_category = 'pu' if is_pitcher else '1b+'
            excluded_categories = [type_specific_category, 'so', 'gb', 'fb']
            for category in excluded_categories:
                del wotc_player_card_dict[category]
        return wotc_player_card_dict
