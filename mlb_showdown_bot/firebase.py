import firebase_admin
import simplejson
import json
import os
from pprint import pprint
from firebase_admin import credentials
from firebase_admin import db
from pathlib import Path

# MY PACKAGES
try:
    # ASSUME THIS IS A SUBMODULE IN A PACKAGE
    from .showdown_player_card_generator import ShowdownPlayerCardGenerator
    from .version import __version__
except ImportError:
    # USE LOCAL IMPORT 
    from showdown_player_card_generator import ShowdownPlayerCardGenerator
    from version import __version__

class Firebase:

# ------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------

    def __init__(self, load_creds=True):
        """ Default initializer """

        self.version = __version__
        self.version_json_safe = '-'.join(__version__.split('.')[:2])
        self.destination_card_output = 'card_output'
        self.json_safe_replacements_dict = {
            'LF/RF': 'LF-RF',
            'GO/AO': 'GO-AO',
            'IF/FB': 'IF-FB',
            'IP/GS': 'IP-GS',
            'real_stats': 'projected',
        }
        if load_creds:
            self.creds = self.__get_creds()

    def __get_creds(self) -> firebase_admin.App:
        """Check local env var for firebase creds. Initializes app if creds exist.

        Args:
          None

        Returns:
          Firebase instance currently running.
        """

        # LOAD CREDS FROM ENV VAR
        FIREBASE_CREDS_STR = os.getenv('FIREBASE_CREDS')
        FIREBASE_URL_STR = os.getenv('FIREBASE_URL')
        if not FIREBASE_CREDS_STR or not FIREBASE_URL_STR:
            # IF NO CREDS, RETURN NONE
            print("CREDS NOT AVAILABLE")
            return None

        # CREDS ENV FOUND, PROCEED
        FIREBASE_CREDS_STR = FIREBASE_CREDS_STR.replace("\'", "\"")
        FIREBASE_CREDS_JSON = json.loads(FIREBASE_CREDS_STR)
        cred = credentials.Certificate(FIREBASE_CREDS_JSON)
        running_app = firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_URL_STR
        })
        return running_app
    
    def close_session(self):
        """Delete the initialized firebase app instance.

        Args:
          None

        Returns:
          None
        """
        if self.creds:
            firebase_admin.delete_app(self.creds)

# ------------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------------

    def query(self, bref_id: str, year: str, context: str, expansion: str, is_variable_speed_00_01: False, disable: bool = False) -> dict:
        """Query cached data for player's card.

        Looks for unique ID (Version + Bref Id + Year + Context)

        Args:
          bref_id: Baseball Reference Player ID (ex: ohtansh01)
          year: Year for stats (ex: 2022)
          context: Showdown Bot Set type (ex: 2022-CLASSIC)
          expansion: Expansion within a set (ex: Trading Deadline, Pennant Run, Final, etc)

        Returns:
          Python dict object with player's showdown card data
        """

        # CHECK FOR CREDS
        filter_for_var_spd = context in ['2000','2001'] and is_variable_speed_00_01
        if not self.creds or filter_for_var_spd or disable:
            # NO CREDS
            return None

        bref_id_json_safe = self.__bref_id_json_safe(bref_id)
        ref = db.reference(f'{self.destination_card_output}/{self.version_json_safe}/{context}/{year}/{expansion}/{bref_id_json_safe}')

        # READ THE DATA AT THE POSTS REFERENCE (THIS IS A BLOCKING OPERATION)
        data = ref.get()
        return data

    def upload(self, context: str, year: str, expansion: str, data: dict, remove_existing=True):
        """Clean and upload data to firebase.

        Args:
          year: Year for stats (ex: 2022)
          context: Showdown Bot Set type (ex: 2022-CLASSIC)
          expansion: Expansion within a set (ex: Trading Deadline, Pennant Run, Final, etc)
          data: Dictionary with player data for upload. 
                Key = player ID, value = player data dictionary
          remove_existing: Optionally remove existing context + year data

        Returns:
          None
        """

        # CHECK FOR CREDS
        if not self.creds:
            # NO CREDS
            return None
        
        # MAKE DICT JSON COMPLIANT
        player_dict_final = self.__clean_data_for_json_upload(data)

        # SAVE TO DATABASE        
        ref = db.reference(f"/{self.destination_card_output}/{self.version_json_safe}/{context}/{year}/{expansion}")
        if remove_existing:
            ref.delete()
        ref.set(player_dict_final)

    def download_all_data(self) -> dict:
        """Download all data from Showdown Library

        Args:
          None

        Returns:
          Python dict object with data from showdown library
        """

        # CHECK FOR CREDS
        if not self.creds:
            # NO CREDS
            return None

        ref = db.reference(f'{self.destination_card_output}/{self.version_json_safe}/')

        # READ THE DATA AT THE POSTS REFERENCE (THIS IS A BLOCKING OPERATION)
        data = ref.get()
        return data

# ------------------------------------------------------------------------
# PARSING
# ------------------------------------------------------------------------

    def load_showdown_card(self, ignore_showdown_library: bool, bref_id: str, year: str, context: str, expansion, player_image_path, player_image_url, is_cooperstown, is_super_season, is_rookie_season, is_all_star_game, is_holiday, offset, set_number, add_image_border, is_dark_mode, is_variable_speed_00_01, is_foil, team_override, set_year_plus_one, pitcher_override, hitter_override, is_running_in_flask) -> ShowdownPlayerCardGenerator:
        """Load cached player showdown data from database.

        Args:
          ignore_showdown_library: Manual override to not query database.
          bref_id: Baseball Reference Player ID (ex: ohtansh01)
          year: Year for stats (ex: 2022)
          context: Showdown Bot Set type (ex: 2022-CLASSIC)

        Returns:
          Showdown Card Object
        """
        
        # UPDATE BREF ID FOR ANY OVERRIDES
        for typ in [pitcher_override, hitter_override]:
          bref_id += f' {typ.lower()}' if typ else ''

        # GRAB DATA FROM FIREBASE IF IT EXISTS
        is_offset = offset != 0
        is_disabled = ignore_showdown_library or is_offset or team_override
        cached_data = self.query(
          bref_id=bref_id, 
          year=year, 
          context=context, 
          expansion='FINAL', # TODO: UPDATE IN 2023 FOR LIVE CARDS
          is_variable_speed_00_01=is_variable_speed_00_01,
          disable=is_disabled,
        )
        if not cached_data:
            return None

        # RENAME KEYS
        cached_data = self.update_keys_for_player_data(data=cached_data,is_expansion=True)
        
        # ADD EMPTY VALUES WHERE NEEDED
        attr_to_fill = {
            'icons': [],
            'positions_and_real_life_ratings': {}
        }
        for attr, value_to_fill in attr_to_fill.items():
            if attr not in cached_data.keys():
                cached_data[attr] = value_to_fill

        # UPDATE LF-RF -> LF/RF
        nested_keys_with_defense = ['positions_and_defense', 'rank', 'pct_rank']
        for key in nested_keys_with_defense:
          if key in cached_data.keys():
              values_updated = {}
              for position, value in cached_data[key].items():
                  position_updated = position.replace('-','/')
                  values_updated[position_updated] = value
              cached_data[key] = values_updated

        # SET ATTRIBUTES OF THE CLASS FROM CACHE
        showdown = ShowdownPlayerCardGenerator(
            name=bref_id, 
            year=year, 
            stats={}, 
            context=context, 
            run_stats=False,
            expansion=expansion,
            player_image_path=player_image_path,
            player_image_url=player_image_url,
            is_cooperstown=is_cooperstown,
            is_super_season=is_super_season,
            is_rookie_season=is_rookie_season,
            is_all_star_game=is_all_star_game,
            is_holiday=is_holiday,
            offset=offset,
            set_number=set_number,
            add_image_border=add_image_border,
            is_dark_mode=is_dark_mode,
            is_variable_speed_00_01=is_variable_speed_00_01,
            is_foil=is_foil,
            set_year_plus_one=set_year_plus_one,
            is_running_in_flask=is_running_in_flask,
            source='Showdown Library'
        )
        ignore_keys_list = ['has_custom_set_number', 'set_number', 'expansion', 'is_variable_speed_00_01','is_cooperstown','is_super_season','is_rookie_season','is_all_star_game','is_holiday']
        for k,v in cached_data.items():
            if k not in ignore_keys_list:
                setattr(showdown,k,v)
        
        return showdown

    def __clean_data_for_json_upload(self, input: dict) -> dict:
        """Convert Python dict to proper JSON value.

        Remove special keys that are not JSON safe.
        Ex: ".", "/", etc

        Args:
          input: Dictionary with non-json safe data.

        Returns:
          Dictionary with cleaned data
        """

        # REMOVE NAN, NESTED NON-JSON PROOF KEYS
        # EX: REPLACE 'LF/RF' -> 'LF-RF'
        json_removing_nan = simplejson.dumps(input, ignore_nan=True)
        for i, j in self.json_safe_replacements_dict.items():
            json_removing_nan = json_removing_nan.replace(i, j)
        
        # REMOVE NON-JSON PROOF KEYS
        # EX: REPLACE '/' -> '-'
        player_dict = json.loads(json_removing_nan)
        player_dict_final = {}
        for player_id, player_data in player_dict.items():
            player_id_safe = self.__bref_id_json_safe(player_id)
            player_dict_final[player_id_safe] = self.update_keys_for_player_data(data=player_data, is_expansion=False)

        return player_dict_final

    def __bref_id_json_safe(self, bref_id) -> str:
        """Remove '.' from bref_id in order to be json compliant.

        Replaces '.' with '@'
        Ex: "surhob.01" -> "surhob@01"

        Args:
          bref_id: Baseball Reference Player ID (ex: ohtansh01)

        Returns:
          Updated string replacing '.' with '@'
        """

        return bref_id.replace('.', '@')

    def update_keys_for_player_data(self, data: dict, is_expansion: bool = False) -> dict:
        """Update all keys within player data.

        Args:
          data: player data dictionary.
          is_expansion: If true, reverses the dictionary mapping.

        Returns:
          Altered player data with new keys.
        """

        data_cleaned = {}
        keys_w_lvl_2 = ['cht', 'chtr', 'prj', 'sts', 'rnk', 'p_rnk'] if is_expansion else ['chart', 'chart_ranges', 'projected', 'stats', 'rank', 'pct_rank']
        for k,v in data.items():
            key_renamed = self.rename_json_key(key=k, is_expansion=is_expansion)
            if k in keys_w_lvl_2:
                updated_v = {}
                for k1,v1 in data[k].items():
                    key1_renamed = self.rename_json_key(key=k1, is_expansion=is_expansion)
                    updated_v[key1_renamed] = v1
                data_cleaned[key_renamed] = updated_v
            else:
                data_cleaned[key_renamed] = v
        
        return data_cleaned

    def rename_json_key(self, key: str, is_expansion: bool = False):
        """Reduce or expand json key name. 

        Done to help reduce size of json in firebase

        Args:
          key: key value to be updated.
          is_expansion: If true, reverses the dictionary mapping.

        Returns:
          Altered key value
        """
        mapping = {
            "add_year_container": "ayc",
            "ba_points": "p_ba",
            "bref_id": "br_id",
            "bref_url": "br_url",
            "chart": "cht",
            "chart_ranges": "chtr",
            "1b Range": "r_1b",
            "1b+ Range": "r_1b+",
            "2b Range": "r_2b",
            "3b Range": "r_3b",
            "bb Range": "r_bb",
            "fb Range": "r_fb",
            "gb Range": "r_gb",
            "hr Range": "r_hr",
            "so Range": "r_so",
            "context": "ctx",
            "context_year": "ctx_yr",
            "defense1": "df1",
            "defense2": "df2",
            "defense3": "df3",
            "defense_points": "p_df",
            "expansion": "exps",
            "hand": "hnd",
            "hand_throw": "hndt",
            "has_icons": "icn",
            "hr_points": "p_hr",
            "icon_points": "p_icn",
            "image_name": "img_n",
            "img_folder_id": "img_fid",
            "img_bordered_folder_id": "img_bfid",
            "img_dark_folder_id": "img_dfid",
            "img_dark_bordered_folder_id": "img_dbfid",
            "img_bordered_id": "img_bid",
            "img_dark_bordered_id": "img_dbid",
            "img_dark_id": "img_did",
            "ip": "ip",
            "is_all_star_game": "asg",
            "is_automated_image": "auti",
            "is_classic": "clsc",
            "is_cooperstown": "cc",
            "is_expanded": "exd",
            "is_foil": 'fl',
            "is_full_career": "fc",
            "is_holiday": "hol",
            "is_img": "img",
            "is_multi_year": "my",
            "is_pitcher": "ptcr",
            "is_rookie_season": "rs",
            "is_stats_estimate": "se",
            "is_super_season": "ss",
            "is_variable_speed_00_01": "vs",
            "name": "nm",
            "obp_points": "p_obp",
            "points": "pt",
            "points_bonus": "p_bn",
            "points_command_out_multiplier": "p_com",
            "points_normalizer": "p_nrml",
            "position1": "p1",
            "position2": "p2",
            "position3": "p3",
            "positions_and_defense": "p_n_d",
            "positions_and_real_life_ratings": "p_n_rl",
            "projected": "prj",
            "1b_per_650_pa": "prj_1b",
            "2b_per_650_pa": "prj_2b",
            "3b_per_650_pa": "prj_3b",
            "batting_avg": "ba",
            "bb_per_650_pa": "prj_bb",
            "h_per_650_pa": "prj_h",
            "hr_per_650_pa": "prj_hr",
            "onbase_perc": "obp",
            "onbase_plus_slugging": "ops",
            "onbase_plus_slugging_plus": "ops+",
            "slugging_perc": "slg",
            "so_per_650_pa": "prj_so",
            "set_number": "sn",
            "slg_points": "p_slg",
            "spd_ip_points": "p_sip",
            "speed": "spd",
            "speed_letter": "spdl",
            "Position1": "po1",
            "Position2": "po2",
            "Position3": "po3",
            "Position4": "po4",
            "Position5": "po5",
            "Position6": "po6",
            "Position7": "po7",
            "Position8": "po8",
            "Position9": "po9",
            "Position10": "po10",
            "award_summary": "awd",
            "stats": "sts",
            "gPosition1": "gP1",
            "gPosition2": "gP2",
            "gPosition3": "gP3",
            "gPosition4": "gP4",
            "gPosition5": "gP5",
            "gPosition6": "gP6",
            "gPosition7": "gP7",
            "gPosition8": "gP8",
            "gPosition9": "gP9",
            "gPosition10": "gP10",
            "tzPosition1": "tzP1",
            "tzPosition2": "tzP2",
            "tzPosition3": "tzP3",
            "tzPosition4": "tzP4",
            "tzPosition5": "tzP5",
            "tzPosition6": "tzP6",
            "tzPosition7": "tzP7",
            "tzPosition8": "tzP8",
            "tzPosition9": "tzP9",
            "tzPosition10": "tzP10",
            "drsPosition1": "drsp1",
            "drsPosition2": "drsp2",
            "drsPosition3": "drsp3",
            "drsPosition4": "drsp4",
            "drsPosition5": "drsp5",
            "drsPosition6": "drsp6",
            "drsPosition7": "drsp7",
            "drsPosition8": "drsp8",
            "drsPosition9": "drsp9",
            "drsPosition10": "drsp10",
            "is_above_hr_threshold": "t_hr",
            "is_above_sb_threshold": "t_sb",
            "is_above_so_threshold": "t_so",
            "is_above_w_threshold": "t_w",
            "is_hr_leader": "l_hr",
            "is_rookie": "rk",
            "is_sb_leader": "sb",
            "outs_above_avg": "otaa",
            "pos_season": "poss",
            "sprint_speed": "spts",
            "team_ID": "tmid",
            "type": "tp",
            "year_ID": "yrid",
            "years_played": "yrp",
            "stats_version": "stv",
            "style": "sty",
            "team": "tm",
            "top_command_out_combinations": "tcoc",
            "type_override": "tpo",
            "version": "v",
            "year": "yr",
            "year_list": "yrl",
            "rank": "rnk",
            "pct_rank": "p_rnk",
        }

        if is_expansion:
            # REVERSE THE DICT MAPPING
            mapping = {v: k for k, v in mapping.items()}

        key = key.replace('.','').replace('/','')
        if key not in mapping.keys():
            # RETURN ORIGINAL VALUE
            return key
        
        return mapping[key]