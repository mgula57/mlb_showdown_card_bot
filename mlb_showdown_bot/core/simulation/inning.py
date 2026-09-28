from pydantic import BaseModel, Field

from .runners import Runners


class Inning(BaseModel):

    inning: int
    is_top: bool = True
    outs: int = 0
    runs: int = 0
    runners: Runners = Field(default_factory=Runners)

    @property
    def summary_str(self) -> str:
        return f"{'TOP' if self.is_top else 'BOT'} {self.inning}, {self.outs} OUT {self.runners.base_squares_str()}"

    @property
    def pct_complete(self) -> float:
        return (self.outs / 3.0)

    @property
    def inning_num_full(self) -> float:
        return self.inning + self.pct_complete

    @property
    def is_played(self) -> bool:
        """False for a phantom half-inning appended after a walk-off (the game ends before it's
        ever batted). Exact because a genuinely played half-inning always ends with at least one
        out, run, or baserunner recorded."""
        return self.outs > 0 or self.runs > 0 or self.runners.count() > 0
