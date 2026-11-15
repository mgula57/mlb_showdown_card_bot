"""What a live game is for, and what happens when it ends.

A live game knows nothing about the feature that made it. Each feature built on live games registers
a context `kind`; a game carries that kind (and an optional `context_ref`), and when its final out is
stored the context's `on_final` runs on the same transaction, so the feature's own record of the result
can never disagree with the game's.

'open' games are for nothing but themselves. A Faceoff is one user of live games ('faceoff'); a
league fixture or anything else would be another.
"""

from typing import TYPE_CHECKING

from ..database.postgres_db import PostgresDB
from .faceoff import FaceoffGameResult, FaceoffResult, FaceoffSide, faceoff_snapshot
from .live_game import LiveSide
from .matchup import MatchupClub

if TYPE_CHECKING:
    from .live_game import LiveMatchState


class LiveGameContext:
    """'open': a game for nothing but itself, whose result lives only on the game."""

    kind = 'open'

    def on_final(self, cur, row: dict, state: 'LiveMatchState') -> None:
        """Record a finished game, on the transaction that stores its final out. `row` is the
        stored game (`internal.live_game`), `state` the game as it ended."""
        return None


class FaceoffLiveContext(LiveGameContext):
    """A Faceoff played by hand: one game, the challenger away and the challenged team home, the
    same seats an instant Faceoff gives them. At the final out it's stored as a Faceoff like any
    other, and the game points at it through `context_ref`."""

    kind = 'faceoff'
    SEATS = {FaceoffSide.CHALLENGER: LiveSide.AWAY, FaceoffSide.OPPONENT: LiveSide.HOME}

    def result(self, row: dict, state: 'LiveMatchState') -> tuple[FaceoffResult, bool]:
        """The Faceoff this game makes, and whether both teams are one user's."""
        entrants = {side: MatchupClub(**row['setup'][seat.value]['club']) for side, seat in self.SEATS.items()}
        winner = next(side for side, seat in self.SEATS.items() if seat == state.winner_side)
        result = FaceoffResult(
            best_of=1,
            seed=int(row['seed']),
            challenger=faceoff_snapshot(entrants[FaceoffSide.CHALLENGER]),
            opponent=faceoff_snapshot(entrants[FaceoffSide.OPPONENT]),
            challenger_wins=int(winner == FaceoffSide.CHALLENGER),
            opponent_wins=int(winner == FaceoffSide.OPPONENT),
            winner_side=winner,
            games=[FaceoffGameResult(game_number=1, home_side=FaceoffSide.OPPONENT, game=state.game)],
        )
        owners = {entrant.team.user_id for entrant in entrants.values()}
        return result, len(owners) == 1 and None not in owners

    def on_final(self, cur, row: dict, state: 'LiveMatchState') -> None:
        result, is_own_matchup = self.result(row, state)
        faceoff_id = PostgresDB.insert_sim_faceoff(cur, user_id=row['created_by'], result=result.model_dump(mode='json'), is_own_matchup=is_own_matchup)
        cur.execute("UPDATE internal.live_game SET context_ref = %s WHERE live_game_id = %s::uuid", (faceoff_id, row['live_game_id']))


LIVE_GAME_CONTEXTS: dict[str, LiveGameContext] = {context.kind: context for context in (LiveGameContext(), FaceoffLiveContext())}
