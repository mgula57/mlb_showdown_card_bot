"""Who makes a game's decisions: the seam between the play loop and whoever is managing each club.

`Game.simulate` asks its controller at each point where a manager would act: whether to change
pitchers, whether to pinch hit, and (for a game people play) when to roll each die. `AutoController`, the default, gives
the answers the sim always has, so seasons, takeovers and Faceoffs are unchanged by this seam. A game
two people play passes a controller that answers from their recorded actions instead
(`core/simulation/live_game.py`), and the engine stays the one engine for every kind of game.
"""

from enum import Enum
from typing import TYPE_CHECKING, Optional

from .inning import Inning
from .player import SimPitcher, SimPlayer

if TYPE_CHECKING:
    from .team import SimTeam


class RollKind(str, Enum):
    """A die a person rolls in a played game. The defense rolls the pitch and every throw on the
    bases (a runner stealing, a runner sent for an extra base); the offense rolls the swing."""

    PITCH = "pitch"
    SWING = "swing"
    STEAL = "steal"
    ADVANCE = "advance"


class GameController:
    """Answers the play loop's decisions. The base class is the sim's own manager (`AutoController`).

    Every hook runs at a fixed point in the loop, and a controller must answer from what it's given
    and its own inputs alone, never from the game's `rng`. The same seed and the same answers then
    always replay the same game, which is what lets a played game be rebuilt from its seed and its
    list of actions.
    """

    def applies_fatigue(self, team: 'SimTeam') -> bool:
        """Whether `team`'s pitcher, left in past his IP, loses control for it
        (`SimPitcher.fatigue_penalty`). Only for a club a person manages: the sim's manager pulls
        tired pitchers itself and sometimes lets a dominant starter run long on purpose."""
        return False

    def choose_pitcher(self, team: 'SimTeam', suggested: Optional[SimPitcher], inning: Inning) -> Optional[SimPitcher]:
        """The pitcher to bring in before the next plate appearance, or None to stay with the
        current one. `suggested` is the sim manager's own call (None when it would stay)."""
        return suggested

    def choose_pinch_hitter(self, team: 'SimTeam', due_up: SimPlayer, inning: Inning) -> Optional[SimPlayer]:
        """A bench player to bat for `due_up`, or None to let him hit. The sim's manager never pinch hits."""
        return None

    def before_roll(self, kind: RollKind, team: 'SimTeam', inning: Inning) -> None:
        """Called just before `team` rolls `kind`. A played game stops here until that player rolls."""
        return None


class AutoController(GameController):
    """The sim's own manager, for both clubs."""


AUTO_CONTROLLER = AutoController()
