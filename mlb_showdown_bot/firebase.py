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
        }
        if load_creds:
            self.creds = self.__get_creds()

    def __get_creds(self):
        """Check local env var for creds.

        Args:
          None

        Returns:
          String of output text for player info + stats
        """

        # LOAD CREDS FROM ENV VAR
        FIREBASE_CREDS_STR = os.getenv('FIREBASE_CREDS')
        if not FIREBASE_CREDS_STR:
            # IF NO CREDS, RETURN NONE
            print("CREDS NOT AVAILABLE")
            return None

        # CREDS ENV FOUND, PROCEED
        FIREBASE_CREDS_STR = FIREBASE_CREDS_STR.replace("\'", "\"")
        FIREBASE_CREDS_JSON = json.loads(FIREBASE_CREDS_STR)
        cred = credentials.Certificate(FIREBASE_CREDS_JSON)
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://showdown-bot-315820-default-rtdb.firebaseio.com"
        })
        return cred

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

        ref = db.reference(f'{self.destination_card_output}/{self.version_json_safe}/{bref_id}-{year}-{context}')

        # READ THE DATA AT THE POSTS REFERENCE (THIS IS A BLOCKING OPERATION)
        data = ref.get()
        return data

    def upload(self, data: dict):
        """Clean and upload data to firebase.

        Args:
          data: Dictionary with player data for upload. 
                Key = player ID, value = player data dictionary

        Returns:
          None
        """

        # CHECK FOR CREDS
        if not self.creds:
            # NO CREDS
            return None
        
        # MAKE DICT JSON COMPLIANT
        player_dict_final = self.__clean_data_for_json_upload(data)

        # ADD TO DATABASE
        final_data = {
            self.destination_card_output: {
                self.version_json_safe: player_dict_final
            }
        }

        ref = db.reference("/")
        ref.delete()
        ref.set(final_data)

# ------------------------------------------------------------------------
# PARSING
# ------------------------------------------------------------------------

    def load_showdown_card(self, bref_id: str, year: str, context: str) -> ShowdownPlayerCardGenerator:
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

        # ADD EMPTY LISTS
        list_attr_to_fill = ['icons']
        for attr in list_attr_to_fill:
            if attr not in cached_data.keys():
                cached_data[attr] = []

        # SET ATTRIBUTES OF THE CLASS FROM CACHE
        showdown = ShowdownPlayerCardGenerator(name=bref_id, year=year, stats={}, context=context, run_stats=False)
        for k,v in cached_data.items():
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

        
