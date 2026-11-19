"""A game people play by hand: each seat manages one club, rolls its dice and makes its moves.

What the game is for lives outside it. Two friends, a league fixture, one of your teams against a
club from baseball history: each is a live game between two clubs (any `MatchupClub`), with each
seat played by a person or by the sim. A seat the sim plays is on autopilot from the first pitch
and can't be taken off it.

Nothing about a game in progress is stored but its setup (both clubs, frozen when the game was
created, and a seed) and the ordered list of what each player did. `LiveMatch.replay` rebuilds the
game from those every time, running the same engine as every other sim with a `ScriptedController`
that answers from the action list and stops at the first roll nobody has made yet. A replay is a
few milliseconds for a full game, survives any restart, and can't drift from what was played.

The server's random number generator decides every die. A player's Roll only says "go", so no
client can choose a number.

Turn order, per plate appearance: the defense rolls the pitch, then the offense rolls the swing.
A throw on the bases is the defense's roll too: a runner stealing goes on the pitch, so the defense
throws before the pitch is shown, and a runner sent for an extra base after the ball is in play
waits on the defense's throw before the plate appearance ends.
A pitching change or a pinch hitter is never a turn of its own. Either club can queue one at any
time, and it applies at the next point it can:
  - a pitching change before that club's next pitch roll is resolved (so on its own pitch turn,
    before the roll that's about to be made);
  - a pinch hitter when the batter he's named for next comes up, provided that batter isn't
    already at the plate.
Autopilot hands a side's decisions to the sim's own manager, from the point it's switched on.
In a game with every roll by hand (`LiveMatchSettings.every_roll_by_hand`, every game opened since
it was added) a side on autopilot, the sim's seat included, still waits for each of its rolls, and
any player seated in the game makes them, so every die on the field is thrown from a button.
"""

from datetime import date, datetime, timedelta, timezone
from enum import Enum
from random import Random
from typing import Optional

from pydantic import BaseModel

from ..card.showdown_player_card import ShowdownPlayerCard
from .controller import GameController, RollKind
from .game import Game
from .inning import Inning
from .matchup import MatchupClub, MatchupError, build_club, play_game, setup_game
from .models import GameLogEntry, GameResult
from .player import SimPitcher, SimPlayer
from .stats import StatCategory, real_card_id
from .team import SimTeam


class LiveMatchError(MatchupError):
    """An action that can't be taken now. The message is safe to show the player."""


class LiveSide(str, Enum):
    AWAY = 'away'
    HOME = 'home'

    @property
    def other(self) -> 'LiveSide':
        return LiveSide.HOME if self == LiveSide.AWAY else LiveSide.AWAY

    @property
    def schedule_key(self) -> str:
        """The name the club in this seat plays under in the engine (see `build_club`)."""
        return self.value.upper()


class LiveActionKind(str, Enum):
    ROLL = 'roll'
    PITCHING_CHANGE = 'pitching_change'
    PINCH_HIT = 'pinch_hit'
    AUTOPILOT = 'autopilot'


class LiveAction(BaseModel):
    """One thing a player did, in the order it happened. Card ids are bare (as the client knows them)."""

    side: LiveSide
    kind: LiveActionKind
    roll: Optional[RollKind] = None
    # PITCHING_CHANGE: THE RELIEVER COMING IN. PINCH_HIT: THE BENCH PLAYER GOING UP.
    player_id: Optional[str] = None
    # PINCH_HIT: THE LINEUP PLAYER HE BATS FOR.
    for_player_id: Optional[str] = None
    # AUTOPILOT: ON OR OFF.
    enabled: Optional[bool] = None
    # AUTOPILOT: SWITCHED ON BY THE IDLE TIMER RATHER THAN THE PLAYER.
    by_timeout: bool = False


class LiveMatchSettings(BaseModel):
    """Chosen when the game is created."""

    # A SIDE THAT HASN'T MOVED FOR THIS LONG WHILE IT'S ITS TURN GOES ON AUTOPILOT. NONE TURNS THE
    # TIMER OFF, FOR A GAME PLAYED A TURN AT A TIME OVER HOURS OR DAYS.
    idle_autopilot_minutes: Optional[int] = None
    # EVERY ROLL WAITS FOR A PLAYER, A SIDE ON AUTOPILOT'S TOO (ANY SEATED PLAYER ROLLS FOR IT). OFF
    # FOR GAMES STORED BEFORE IT, WHOSE ACTIONS HAVE NO ROLLS FOR THOSE SIDES.
    every_roll_by_hand: bool = False


class PendingRoll(BaseModel):
    """The roll the game is waiting on."""

    side: LiveSide
    roll: RollKind
    # SET ONCE THE PLATE APPEARANCE HAS STARTED (EVERY ROLL BUT THE PITCH): THE MATCHUP IS LOCKED IN.
    pitcher_id: Optional[str] = None
    hitter_id: Optional[str] = None
    # THE DICE ALREADY ROLLED IN THIS PLATE APPEARANCE, ONCE THEY HAVE BEEN.
    pitch_roll: Optional[int] = None
    pitch_result: Optional[str] = None
    swing_roll: Optional[int] = None
    # A THROW (STEAL, ADVANCE): THE RUNNER, THE BASE HE'S LEAVING, AND THE TEST - OUT WHEN
    # `defense` + THE ROLL > `target` (HIS SPEED WITH THE BASE'S BONUS).
    runner_id: Optional[str] = None
    runner: Optional[str] = None
    base: Optional[int] = None
    defense: Optional[int] = None
    target: Optional[int] = None


class LiveSideState(BaseModel):
    """What one club can do right now, for its manager's controls."""

    side: LiveSide
    autopilot: bool
    pitcher_id: str
    # CONTROL LOST TO FATIGUE ON THE NEXT PITCH (`SimPitcher.fatigue_penalty`).
    pitcher_fatigue: int = 0
    # WHETHER THE SIM'S MANAGER WOULD PULL HIM NOW. A HINT, NEVER FORCED ON A PERSON.
    pitcher_is_tired: bool = False
    available_reliever_ids: list[str] = []
    bench_ids: list[str] = []
    # BATTING ORDER, CURRENT OCCUPANT OF EACH SLOT.
    lineup_ids: list[str] = []
    due_up_id: str
    # THE BATTER LOCKED IN AT THE PLATE, WHO CAN NO LONGER BE PINCH HIT FOR.
    at_bat_id: Optional[str] = None
    queued: list[LiveAction] = []


class LiveSituation(BaseModel):
    """Where the game stands between plays: the half-inning being played and its outs."""

    inning: int
    is_top: bool
    outs: int = 0


class LiveMatchState(BaseModel):
    seq: int
    game: GameResult
    is_final: bool = False
    winner_side: Optional[LiveSide] = None
    pending: Optional[PendingRoll] = None
    # THE PLATE APPEARANCE THE GAME STOPPED IN THE MIDDLE OF, AS FAR AS IT'S GOT (A STEAL, A SWING),
    # WHILE IT WAITS ON A LATER ROLL IN IT. NOT IN `game.log`, WHICH HOLDS FINISHED PLAYS ONLY.
    play_in_progress: Optional[GameLogEntry] = None
    situation: Optional[LiveSituation] = None
    # EVERY PLAYER ON BOTH CLUBS, BARE CARD ID TO NAME, SO THE CLIENT CAN NAME WHO'S UP OR WARMING
    # UP BEFORE THE CARDS HAVE LOADED.
    player_names: dict[str, str] = {}
    sides: dict[LiveSide, LiveSideState] = {}


class _AwaitingRoll(Exception):
    def __init__(self, pending: PendingRoll) -> None:
        super().__init__(f'awaiting {pending.side.value} {pending.roll.value}')
        self.pending = pending


class ScriptedController(GameController):
    """Answers the engine from the players' recorded actions, and stops the game at the first roll
    that hasn't been made. Non-roll actions are read as the game reaches them and wait in a queue
    per side until they apply."""

    def applies_fatigue(self, team: SimTeam) -> bool:
        # A CLUB ON AUTOPILOT IS THE SIM'S TO MANAGE, SO IT PLAYS BY THE SIM'S RULES.
        return not self.autopilot[self._side(team)]

    def __init__(
        self, actions: list[LiveAction], side_for_team: dict[int, LiveSide], sim_sides: frozenset[LiveSide] = frozenset(),
        every_roll_by_hand: bool = False,
    ) -> None:
        self._actions = actions
        self._every_roll_by_hand = every_roll_by_hand
        self._next = 0
        self._side_for_team = side_for_team
        self.autopilot = {side: side in sim_sides for side in LiveSide}
        self.queued: dict[LiveSide, list[LiveAction]] = {side: [] for side in LiveSide}

    def _side(self, team: SimTeam) -> LiveSide:
        return self._side_for_team[id(team)]

    def _drain(self) -> None:
        """Read every action up to the next roll."""
        while self._next < len(self._actions) and self._actions[self._next].kind != LiveActionKind.ROLL:
            action = self._actions[self._next]
            self._next += 1
            if action.kind == LiveActionKind.AUTOPILOT:
                self.autopilot[action.side] = bool(action.enabled)
            else:
                self.queued[action.side].append(action)

    def _pop(self, side: LiveSide, kind: LiveActionKind, for_player_id: Optional[str] = None) -> Optional[LiveAction]:
        for action in self.queued[side]:
            if action.kind == kind and (for_player_id is None or action.for_player_id == for_player_id):
                self.queued[side].remove(action)
                return action
        return None

    @property
    def consumed(self) -> int:
        return self._next

    def choose_pitcher(self, team: SimTeam, suggested: Optional[SimPitcher], inning: Inning) -> Optional[SimPitcher]:
        side = self._side(team)
        self._drain()
        change = self._pop(side, LiveActionKind.PITCHING_CHANGE)
        if change is not None:
            pitcher = next((p for p in team.available_relievers() if real_card_id(p.id) == change.player_id), None)
            if pitcher is None:
                raise LiveMatchError('That reliever is no longer available.')
            return pitcher
        return suggested if self.autopilot[side] else None

    def choose_pinch_hitter(self, team: SimTeam, due_up: SimPlayer, inning: Inning) -> Optional[SimPlayer]:
        side = self._side(team)
        self._drain()
        sub = self._pop(side, LiveActionKind.PINCH_HIT, for_player_id=real_card_id(due_up.id))
        if sub is None:
            return None
        player = next((p for p in team.bench_hitters() if real_card_id(p.id) == sub.player_id), None)
        if player is None:
            raise LiveMatchError('That pinch hitter is no longer available.')
        return player

    def before_roll(self, kind: RollKind, team: SimTeam, inning: Inning) -> None:
        side = self._side(team)
        self._drain()
        if self.autopilot[side] and not self._every_roll_by_hand:
            return
        if self._next < len(self._actions):
            action = self._actions[self._next]
            if action.side != side or action.roll != kind:
                raise LiveMatchError(f"It's not {action.side.value}'s {action.roll.value if action.roll else 'roll'}.")
            self._next += 1
            return
        raise _AwaitingRoll(PendingRoll(side=side, roll=kind))


class LiveMatch:
    """One live game between two frozen clubs. Built fresh for every request; holds no game state."""

    def __init__(
        self, clubs: dict[LiveSide, MatchupClub], seed: int,
        cards: dict[LiveSide, dict[str, ShowdownPlayerCard]],
        sim_sides: frozenset[LiveSide] = frozenset(),
        every_roll_by_hand: bool = False,
    ) -> None:
        self.clubs = clubs
        self.seed = seed
        self.cards = cards
        # SEATS THE SIM PLAYS: ON AUTOPILOT FROM THE FIRST PITCH. WAITED ON ONLY FOR ITS ROLLS, AND
        # ONLY WITH `every_roll_by_hand`.
        self.sim_sides = frozenset(sim_sides)
        self.every_roll_by_hand = every_roll_by_hand

    # ------------------------------------------------------------------
    # REPLAY
    # ------------------------------------------------------------------

    def replay(self, actions: list[LiveAction]) -> LiveMatchState:
        """Rebuild the game from its actions, up to the roll it's waiting on or the final out."""
        teams = {side: build_club(self.clubs[side], self.cards[side], schedule_key=side.schedule_key) for side in LiveSide}
        game = setup_game(home=teams[LiveSide.HOME], away=teams[LiveSide.AWAY])
        controller = ScriptedController(actions, side_for_team={id(team): side for side, team in teams.items()}, sim_sides=self.sim_sides,
            every_roll_by_hand=self.every_roll_by_hand,
        )

        pending: Optional[PendingRoll] = None
        try:
            play_game(game, Random(self.seed), controller)
        except _AwaitingRoll as waiting:
            pending = waiting.pending
        if controller.consumed < len(actions) and any(a.kind == LiveActionKind.ROLL for a in actions[controller.consumed:]):
            raise LiveMatchError('The game ended before every roll was used.')

        at_bat = self._locked_matchup(game, pending)
        play_in_progress: Optional[GameLogEntry] = None
        if pending is not None and at_bat is not None:
            pa = game.current_plate_appearance
            update = {'pitcher_id': real_card_id(pa.pitcher.id), 'hitter_id': real_card_id(pa.hitter.id)}
            if not pa.pitch.is_empty():
                update.update(pitch_roll=pa.pitch.roll, pitch_result=pa.pitch.result.value)
            if not pa.swing.is_empty():
                update['swing_roll'] = pa.swing.roll
            if pa.awaiting_throw is not None:
                throw = pa.awaiting_throw
                update.update(runner_id=real_card_id(throw.runner.id), runner=throw.runner.name, base=throw.base, defense=throw.defense, target=throw.target)
            pending = pending.model_copy(update=update)
            play_in_progress = self._play_in_progress(game)

        result = game.as_result().model_copy(update={'date': date.today()})
        if not game.is_game_over:
            # `as_result` only fills the score, box scores and team identities in at the final out.
            result = result.model_copy(update={
                'home_team_identity': game.home_team.identity,
                'away_team_identity': game.away_team.identity,
                'home_score': int(game.home_team.current_game_stats.stat(StatCategory.RUNS_SCORED)),
                'away_score': int(game.away_team.current_game_stats.stat(StatCategory.RUNS_SCORED)),
                'home_box_score': game._build_team_box_score(game.home_team),
                'away_box_score': game._build_team_box_score(game.away_team),
            })

        return LiveMatchState(
            seq=len(actions),
            game=result,
            is_final=game.is_game_over,
            winner_side=(LiveSide.HOME if game.winning_team is teams[LiveSide.HOME] else LiveSide.AWAY) if game.is_game_over else None,
            pending=pending,
            play_in_progress=play_in_progress,
            situation=None if game.is_game_over else LiveSituation(
                inning=game.innings[-1].inning, is_top=game.innings[-1].is_top, outs=game.innings[-1].outs,
            ),
            player_names={real_card_id(p.id): p.name for team in teams.values() for p in (team.position_players + team.rotation.players + team.bullpen.players)},
            sides={
                side: self._side_state(side, teams[side], game, controller, at_bat if side == self._batting_side(game) else None)
                for side in LiveSide
            },
        )

    @staticmethod
    def _locked_matchup(game: Game, pending: Optional[PendingRoll]) -> Optional[SimPlayer]:
        """The batter at the plate while the game waits on a roll in his plate appearance (anything
        after the pitch roll that opens it), else None."""
        if pending is None or pending.roll == RollKind.PITCH or game.current_plate_appearance is None:
            return None
        return game.current_plate_appearance.hitter

    @staticmethod
    def _batting_side(game: Game) -> LiveSide:
        return LiveSide.AWAY if game.innings[-1].is_top else LiveSide.HOME

    @classmethod
    def _play_in_progress(cls, game: Game) -> Optional[GameLogEntry]:
        """The plate appearance the game is stopped in, as a log line counting what's happened in it
        so far, or None while nothing has (waiting on a steal throw before anything else)."""
        pa = game.current_plate_appearance
        if pa.bases_snapshot_after_steal is None and pa.swing.is_empty():
            return None
        inning = game.innings[-1]
        runs = {side: int(game.home_team.current_game_stats.stat(StatCategory.RUNS_SCORED) if side == LiveSide.HOME else game.away_team.current_game_stats.stat(StatCategory.RUNS_SCORED)) for side in LiveSide}
        runs[cls._batting_side(game)] += int(pa.runs_scored)
        return game.log_entry(pa, inning=inning, outs=inning.outs + pa.outs, away_score=runs[LiveSide.AWAY], home_score=runs[LiveSide.HOME])

    @staticmethod
    def _side_state(side: LiveSide, club: SimTeam, game: Game, controller: ScriptedController, at_bat: Optional[SimPlayer]) -> LiveSideState:
        inning = game.innings[-1]
        pitcher = club.current_pitcher()
        hitter = at_bat if at_bat is not None else club.current_hitter(game=game)
        return LiveSideState(
            side=side,
            autopilot=controller.autopilot[side],
            pitcher_id=real_card_id(pitcher.id),
            pitcher_fatigue=pitcher.fatigue_penalty(inning),
            # NO RNG: THE HINT MUST NOT DRAW FROM THE GAME'S DICE, AND WITHOUT IT THERE'S NO
            # "DOMINANT STARTER STAYS IN" EXTENSION, SO IT SAYS TIRED AS SOON AS HE IS.
            pitcher_is_tired=pitcher.is_tired(inning=inning, ip_adjustment=club.manager.hook_ip_adjustment),
            available_reliever_ids=[real_card_id(p.id) for p in club.available_relievers()],
            bench_ids=[real_card_id(p.id) for p in club.bench_hitters()],
            lineup_ids=[real_card_id(p.id) for p in club.batting_order],
            due_up_id=real_card_id(hitter.id),
            at_bat_id=real_card_id(at_bat.id) if at_bat is not None else None,
            queued=controller.queued[side],
        )

    # ------------------------------------------------------------------
    # MOVES
    # ------------------------------------------------------------------

    def apply(self, actions: list[LiveAction], action: LiveAction) -> LiveMatchState:
        """Check `action` against the game as it stands, then return the game with it applied."""
        state = self.replay(actions)
        self.validate(state, action)
        return self.replay([*actions, action])

    def validate(self, state: LiveMatchState, action: LiveAction) -> None:
        if state.is_final:
            raise LiveMatchError('This game is over.')
        if action.side in self.sim_sides and action.kind != LiveActionKind.ROLL:
            raise LiveMatchError('The sim manages that club.')
        mine = state.sides[action.side]
        queued_ids = {a.player_id for a in mine.queued}

        if action.kind == LiveActionKind.ROLL:
            if state.pending is None or state.pending.side != action.side or state.pending.roll != action.roll:
                raise LiveMatchError("It's not your roll.")
        elif action.kind == LiveActionKind.PITCHING_CHANGE:
            if action.player_id not in mine.available_reliever_ids or action.player_id in queued_ids:
                raise LiveMatchError('That reliever is not available.')
            if any(a.kind == LiveActionKind.PITCHING_CHANGE for a in mine.queued):
                raise LiveMatchError('A pitching change is already on the way.')
        elif action.kind == LiveActionKind.PINCH_HIT:
            if action.player_id not in mine.bench_ids or action.player_id in queued_ids:
                raise LiveMatchError('That player is not available to pinch hit.')
            if action.for_player_id not in mine.lineup_ids:
                raise LiveMatchError('That batter is not in the lineup.')
            if action.for_player_id == mine.at_bat_id:
                raise LiveMatchError('He is already at the plate.')
            if any(a.kind == LiveActionKind.PINCH_HIT and a.for_player_id == action.for_player_id for a in mine.queued):
                raise LiveMatchError('A pinch hitter is already set for him.')
        elif action.kind == LiveActionKind.AUTOPILOT:
            if action.enabled is None or bool(action.enabled) == mine.autopilot:
                raise LiveMatchError('Autopilot is already set that way.')

    @staticmethod
    def idle_autopilot_action(state: LiveMatchState, settings: LiveMatchSettings, last_action_at: datetime, now: Optional[datetime] = None) -> Optional[LiveAction]:
        """The autopilot switch the idle timer owes the side being waited on, if its time is up."""
        if settings.idle_autopilot_minutes is None or state.is_final or state.pending is None:
            return None
        # ALREADY ON AUTOPILOT, IT'S WAITING ON A PLAYER TO ROLL FOR IT.
        if state.sides[state.pending.side].autopilot:
            return None
        now = now or datetime.now(timezone.utc)
        if now - last_action_at < timedelta(minutes=settings.idle_autopilot_minutes):
            return None
        return LiveAction(side=state.pending.side, kind=LiveActionKind.AUTOPILOT, enabled=True, by_timeout=True)

