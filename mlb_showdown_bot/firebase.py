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
        firebase_admin.delete_app(self.creds)

# ------------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------------

    def query(self, bref_id: str, year: str, context: str) -> dict:
        """Query cached data for player's card.

        Looks for unique ID (Version + Bref Id + Year + Context)

        Args:
          bref_id: Baseball Reference Player ID (ex: ohtansh01)
          year: Year for stats (ex: 2022)
          context: Showdown Bot Set type (ex: 2022-CLASSIC)

        Returns:
          Python dict object with player's showdown card data
        """

        # CHECK FOR CREDS
        if not self.creds:
            # NO CREDS
            return None

        ref = db.reference(f'{self.destination_card_output}/{self.version_json_safe}/{context}/{year}/{bref_id}')

        # READ THE DATA AT THE POSTS REFERENCE (THIS IS A BLOCKING OPERATION)
        data = ref.get()
        return data

    def upload(self, context: str, year: str, data: dict, remove_existing=True):
        """Clean and upload data to firebase.

        Args:
          year: Year for stats (ex: 2022)
          context: Showdown Bot Set type (ex: 2022-CLASSIC)
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
        ref = db.reference(f"/{self.destination_card_output}/{self.version_json_safe}/{context}/{year}/")
        if remove_existing:
            ref.delete()
        ref.set(player_dict_final)

# ------------------------------------------------------------------------
# PARSING
# ------------------------------------------------------------------------

    def load_showdown_card(self, bref_id: str, year: str, context: str, expansion, player_image_path, player_image_url, is_cooperstown, is_super_season, is_rookie_season, is_all_star_game, is_holiday, offset, set_number, add_image_border, is_dark_mode, is_variable_speed_00_01, is_foil, is_running_in_flask) -> ShowdownPlayerCardGenerator:
        """Load cached player showdown data from database.

        Args:
          bref_id: Baseball Reference Player ID (ex: ohtansh01)
          year: Year for stats (ex: 2022)
          context: Showdown Bot Set type (ex: 2022-CLASSIC)

        Returns:
          Showdown Card Object
        """
        
        # GRAB DATA FROM FIREBASE IF IT EXISTS
        cached_data = self.query(bref_id=bref_id, year=year, context=context)
        if not cached_data:
            return None
        
        # ADD EMPTY VALUES WHERE NEEDED
        attr_to_fill = {
            'icons': [],
            'positions_and_real_life_ratings': {}
        }
        for attr, value_to_fill in attr_to_fill.items():
            if attr not in cached_data.keys():
                cached_data[attr] = value_to_fill

        # UPDATE LF-RF -> LF/RF
        if 'positions_and_defense' in cached_data.keys():
            positions_and_defense_updated = {}
            for position, value in cached_data['positions_and_defense'].items():
                position_updated = position.replace('-','/')
                positions_and_defense_updated[position_updated] = value
            cached_data['positions_and_defense'] = positions_and_defense_updated

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
            is_running_in_flask=is_running_in_flask
        )
        ignore_keys_list = ['has_custom_set_number', 'set_number', 'expansion']
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
            player_data_updated = {}
            for k,v in player_data.items():
                key_new = k.replace('.','').replace('/','')
                player_data_updated[key_new] = v
            player_dict_final[player_id] = player_data_updated
        
        return player_dict_final

        
