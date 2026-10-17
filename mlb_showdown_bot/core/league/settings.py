from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from ..card.team_builder.autofill import OFFENSE_POSITIONS
from ..card.team_builder.team import MAX_STARTERS


class LuxuryTax(BaseModel):
    """Turns the league's points cap into a soft cap: picks may go over it, and every team pays
    `buy_in` plus a tax on the points it ends up over the cap. The cost formula lives in the
    frontend (`luxuryTaxCost` in components/leagues/draft/draftView.ts)."""

    buy_in: int = Field(default=50, ge=0)
    type: Literal['linear', 'exponential'] = 'linear'


class LeagueSettings(BaseModel):
    """Rules a league's commissioner sets before the first draft. Stored as `league.settings`."""

    team_count: int = Field(default=8, ge=2, le=12)
    roster_size: int = Field(default=20, ge=len(OFFENSE_POSITIONS) + 1, le=40)
    min_bench: int = Field(default=2, ge=0)
    min_bullpen: int = Field(default=5, ge=0)
    num_starters: int = Field(default=4, ge=1, le=MAX_STARTERS)
    pts_cap: Optional[int] = Field(default=None, ge=1)  # NONE = NO CAP
    luxury_tax: Optional[LuxuryTax] = None  # NONE = NO TAX; NEEDS pts_cap
    draft_order_mode: Literal['random', 'manual'] = 'random'

    @property
    def hard_minimum(self) -> int:
        """Slots every roster must fill: the 9 lineup spots, the rotation, and the bench and
        bullpen minimums. Anything past this up to `roster_size` is the drafter's choice."""
        return len(OFFENSE_POSITIONS) + self.num_starters + self.min_bench + self.min_bullpen

    @property
    def hard_cap(self) -> Optional[int]:
        """The cap picks can't go over: `pts_cap`, unless a luxury tax lets teams pay to exceed it."""
        return None if self.luxury_tax else self.pts_cap

    @model_validator(mode='after')
    def _luxury_tax_needs_cap(self) -> 'LeagueSettings':
        if self.luxury_tax and not self.pts_cap:
            raise ValueError("A luxury tax needs a points cap to tax teams over")
        return self

    @model_validator(mode='after')
    def _roster_fits_minimums(self) -> 'LeagueSettings':
        if self.hard_minimum > self.roster_size:
            raise ValueError(
                f"Roster size {self.roster_size} is smaller than the {self.hard_minimum} slots the lineup, "
                f"rotation, bench and bullpen minimums need"
            )
        return self
