from ..base_client import BaseMLBClient
from ..models.stats.award_recipient import AwardRecipient


class AwardsClient(BaseMLBClient):
    """Client for award recipient endpoints - inherits all base functionality"""

    def get_recipients(self, award_id: str, season: int) -> list[AwardRecipient]:
        """Get the recipient(s) of an award for a given season

        Args:
            award_id: MLB award ID (e.g. "ALMVP", "NLCY", "ALGG", "NLSS", "ALROY")
            season: Season year

        Returns:
            List of AwardRecipient. Empty if the award hasn't been announced yet for this season.
        """
        try:
            data = self._make_request(f'awards/{award_id}/recipients', params={'season': season})
            return [AwardRecipient(**recipient) for recipient in data.get('awards', [])]
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                return []
            raise
