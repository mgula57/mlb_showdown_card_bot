from typing import Optional

from ..base_client import BaseMLBClient
from ..models.transactions.transaction import Transaction, TransactionTypeEnum


class TransactionsClient(BaseMLBClient):
    """Client for the transactions endpoint - inherits all base functionality"""

    def get_transactions(self, start_date: str, end_date: str, sport_id: int = 1, team_id: Optional[int] = None) -> list[Transaction]:
        """Every transaction between two dates (inclusive), oldest first.

        Args:
            start_date: YYYY-MM-DD.
            end_date: YYYY-MM-DD.
            sport_id: MLB API sport id (1 = MLB).
            team_id: Optional club filter. Matches either side of a move.
        """
        params = {'sportId': sport_id, 'startDate': start_date, 'endDate': end_date}
        if team_id:
            params['teamId'] = team_id
        data = self._make_request('transactions', params=params)
        return [Transaction(**row) for row in data.get('transactions', [])]


__all__ = ['TransactionsClient', 'Transaction', 'TransactionTypeEnum']
