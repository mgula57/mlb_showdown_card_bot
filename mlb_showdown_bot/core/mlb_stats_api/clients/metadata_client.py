from pprint import pprint

from ..base_client import BaseMLBClient
from ..models.metadata.metadata import SituationCode
from typing import Optional, List

class MetadataClient(BaseMLBClient):
    """Client for metadata related endpoints - inherits all base functionality"""

    def get_situation_codes(self) -> List[SituationCode]:
        """Get list of situation codes (ex: Home/Away, vs LHP/RHP, etc)"""

        try:
            data: List[dict] = self._make_request('situationCodes') # THIS ENDPOINT RETURNS AS LIST, NOT DICT
            if not data:
                return []
            situation_code_objects = [SituationCode(**code) for code in data]
            situation_code_objects.sort(key=lambda s: s.sort_order, reverse=False)
            return situation_code_objects
        except Exception as e:
            if "404" in str(e):
                raise Exception(f"Situation codes not found")
            raise