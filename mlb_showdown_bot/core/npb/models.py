from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel
from unidecode import unidecode
import re

from ..shared.hand import Hand


class NPBLeague(str, Enum):
    """The two NPB leagues. Values match Baseball Reference's register league codes."""

    CENTRAL = "JPCL"
    PACIFIC = "JPPL"

    @property
    def abbreviation(self) -> str:
        return 'CL' if self == NPBLeague.CENTRAL else 'PL'


class NPBName:
    """Name normalization shared by the player lookup and the cross-source (Fangraphs) matching.

    Romanization of Japanese names isn't consistent across sources ('Kondoh' vs 'Kondo', 'Ohtani' vs 'Otani',
    'Yuuki' vs 'Yuki'), and sources disagree on given/family name order, so the key collapses long vowels and
    sorts the name tokens.
    """

    _LONG_VOWELS: list[tuple[str, str]] = [('ou', 'o'), ('oh', 'o'), ('oo', 'o'), ('uu', 'u'), ('ei', 'e')]

    @classmethod
    def key(cls, name: str) -> str:
        tokens = re.sub(r'[^a-z ]', ' ', unidecode(name or '').lower()).split()
        normalized_tokens = []
        for token in tokens:
            for long_vowel, short_vowel in cls._LONG_VOWELS:
                token = token.replace(long_vowel, short_vowel)
            normalized_tokens.append(token)
        return ' '.join(sorted(normalized_tokens))


class NPBPlayerTeamSeason(BaseModel):
    """One player's stats for one NPB team in one season, as listed on that team's Baseball Reference register page.

    A player traded mid-season has one row per team. Pitchers that batted have both batting and pitching stats.
    """

    register_id: str                        # Baseball Reference register id (ex: 'muraka000mun')
    name: str
    season: int
    league: NPBLeague
    team: str                               # Team enum value when supported (ex: 'YAK'), otherwise the raw club name
    team_name: str                          # Club name as listed by the register (ex: 'Tokyo Yakult Swallows')
    age: Optional[int] = None
    bats: Optional[Hand] = None
    throws: Optional[Hand] = None

    batting: dict[str, Any] = {}
    pitching: dict[str, Any] = {}
    # {'SS': {'G': 120, 'PO': 180, 'A': 350, 'E': 9, 'DP': 70, 'fielding_perc': .983, 'rf_fld': 6.2}}
    # 'rf_fld' IS THE SYNTHETIC RUNS-SAVED RATING ADDED BY NPBSyntheticDefense
    fielding: dict[str, dict[str, Any]] = {}

    @property
    def id(self) -> str:
        return f"{self.season}-{self.register_id}-{self.team}"

    @property
    def name_key(self) -> str:
        return NPBName.key(self.name)

    @property
    def register_url(self) -> str:
        return f"https://www.baseball-reference.com/register/player.fcgi?id={self.register_id}"
