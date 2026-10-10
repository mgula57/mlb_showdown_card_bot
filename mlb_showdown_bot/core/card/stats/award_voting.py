from enum import Enum
from typing import Optional

import cloudscraper
from bs4 import BeautifulSoup
from pydantic import BaseModel


class AwardVotingType(str, Enum):
    """Voted awards with placements published on BREF's yearly awards page"""

    MVP = "MVP"
    CYA = "CYA"
    ROY = "ROY"

    @property
    def accolade_key(self) -> Optional[str]:
        """Matching key in the bref accolades dict. ROY placements only live in award_summary on bref."""
        match self:
            case AwardVotingType.MVP: return 'mvp'
            case AwardVotingType.CYA: return 'cyyoung'
            case _: return None


class AwardVotingResult(BaseModel):
    """A single player's placement in an award vote (ex: 2025 AL MVP, 2nd, 80% share)"""

    season: int
    league: str
    award: AwardVotingType
    rank: int
    bref_id: str
    mlb_id: Optional[int] = None
    player_name: Optional[str] = None
    team: Optional[str] = None
    points_won: Optional[float] = None
    votes_first: Optional[float] = None
    share_pct: Optional[int] = None

    @property
    def id(self) -> str:
        return f"{self.season}-{self.league}{self.award.value}-{self.bref_id}"

    @property
    def award_summary_abbr(self) -> str:
        """Matches bref's award_summary format. Ex: 'MVP-2'"""
        return f"{self.award.value}-{self.rank}"

    @property
    def accolade_str(self) -> str:
        """Matches bref's accolade format. Ex: '2025 AL (2, 80%)'"""
        return f"{self.season} {self.league} ({self.rank}, {self.share_pct or 0}%)"


class BaseballReferenceAwardVotingScraper:
    """Scrapes MVP, Cy Young, and Rookie of the Year voting placements from Baseball Reference"""

    URL_TEMPLATE = "https://www.baseball-reference.com/awards/awards_{season}.shtml"
    LEAGUES = ['AL', 'NL']

    def __init__(self) -> None:
        self.scraper = cloudscraper.create_scraper()

    def fetch(self, season: int) -> list[AwardVotingResult]:
        """Fetch every voting placement for a season. Empty if voting hasn't been published yet.

        Raises:
            TimeoutError: BREF rate limited (429) or blocked (403) the request.
        """
        response = self.scraper.get(self.URL_TEMPLATE.format(season=season), timeout=(8, 22))
        if response.status_code == 404:
            return []
        if response.status_code in (403, 429):
            raise TimeoutError(f"{response.status_code} - Baseball Reference blocked the award voting request for {season}")
        response.raise_for_status()
        response.encoding = 'utf-8'

        # SOME BREF TABLES ARE HIDDEN INSIDE HTML COMMENTS
        soup = BeautifulSoup(response.text.replace('<!--', '').replace('-->', ''), 'lxml')

        results: list[AwardVotingResult] = []
        for award in AwardVotingType:
            for league in self.LEAGUES:
                table = soup.find('table', attrs={'id': f'{league}_{award.value}_voting'})
                if table is None or table.find('tbody') is None:
                    continue
                for tr in table.find('tbody').find_all('tr'):
                    result = self.__parse_row(tr=tr, season=season, league=league, award=award)
                    if result:
                        results.append(result)
        return results

    def __parse_row(self, tr: BeautifulSoup, season: int, league: str, award: AwardVotingType) -> Optional[AwardVotingResult]:
        cells = {c.get('data-stat'): c for c in tr.find_all(['th', 'td'])}
        player_cell = cells.get('player')
        bref_id = player_cell.get('data-append-csv') if player_cell else None
        try:
            rank = int(cells['rank'].text.strip())
        except (KeyError, ValueError):
            return None
        if not bref_id:
            return None

        def cell_float(stat: str) -> Optional[float]:
            try: return float(cells[stat].text.strip())
            except (KeyError, ValueError): return None

        try: share = int(cells['share'].text.strip().replace('%', ''))
        except (KeyError, ValueError): share = None

        return AwardVotingResult(
            season=season,
            league=league,
            award=award,
            rank=rank,
            bref_id=bref_id,
            player_name=player_cell.text.strip(),
            team=cells['team_ID'].text.strip() if 'team_ID' in cells else None,
            points_won=cell_float('points_won'),
            votes_first=cell_float('votes_first'),
            share_pct=share,
        )
