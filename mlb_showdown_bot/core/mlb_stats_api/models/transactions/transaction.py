from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TransactionTypeEnum(str, Enum):
    """The MLB `typeCode`s the app reads. The API returns ~20 others (assignments, options,
    status changes, number changes...), which are roster churn rather than player movement."""

    TRADE = "TR"
    SIGNED_FREE_AGENT = "SFA"
    DECLARED_FREE_AGENCY = "DFA"  # "elected free agency" - not Designated for Assignment, which is DES
    CLAIMED_OFF_WAIVERS = "CLW"


class TransactionPerson(BaseModel):
    id: int
    full_name: Optional[str] = Field(None, alias='fullName')

    model_config = {'populate_by_name': True}


class TransactionTeam(BaseModel):
    id: int
    name: Optional[str] = None


class Transaction(BaseModel):
    """One row of GET /transactions.

    A trade comes back as one row per leg, every leg sharing the trade's `id`; a leg with no
    `person` is the cash / player-to-be-named side. A free-agent signing has no `from_team`, and
    an elected-free-agency row puts the club the player *left* in `to_team`.
    """

    id: int
    person: Optional[TransactionPerson] = None
    from_team: Optional[TransactionTeam] = Field(None, alias='fromTeam')
    to_team: Optional[TransactionTeam] = Field(None, alias='toTeam')
    date: Optional[str] = None
    effective_date: Optional[str] = Field(None, alias='effectiveDate')
    type_code: Optional[str] = Field(None, alias='typeCode')
    type_desc: Optional[str] = Field(None, alias='typeDesc')
    description: Optional[str] = None

    model_config = {'populate_by_name': True}

    @property
    def is_minor_league_deal(self) -> bool:
        """MLB only marks a minor-league contract in the description text."""
        return 'minor league contract' in (self.description or '').lower()
