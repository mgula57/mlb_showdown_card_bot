"""Routes for live games: games people play by hand, a turn at a time.

A live game has two seats, away and home. Each holds any club the Team Builder can show (one of your
teams, someone's public team, a historical MLB club, an Era Roster, or a club picked at random from
baseball history), and each is played by a person or by the sim. Whoever creates the game takes
one seat; the other is the sim's, theirs too, or left open for whoever opens the invite link,
who may be asked to bring their own team.

What a game is for is its context (`core/simulation/live_contexts.py`). Games from these routes are
'open' (for nothing but themselves); a feature built on live games, like a Faceoff played by hand,
creates its games with its own context, which records the result when the final out lands.

Every request rebuilds the game from its stored actions (`LiveMatch.replay`), so there's no game
state to keep in a worker. After each action the server broadcasts the new `seq` on the Supabase
Realtime channel `live-game:<id>`; clients refetch on that signal and poll as a fallback.
"""

import os
import random
import secrets
import traceback
from typing import Literal, Optional, Union

import requests
from flask import Blueprint, g, jsonify, request
from pydantic import BaseModel, ValidationError

from ..core.card.showdown_player_card import ShowdownPlayerCard
from ..core.card.team_builder.synthetic_teams import SyntheticTeamError, SyntheticTeams
from ..core.card.team_builder.team import Team as BuilderTeam
from ..core.database.postgres_db import PostgresDB
from ..core.simulation.live_game import LiveAction, LiveActionKind, LiveMatch, LiveMatchError, LiveMatchSettings, LiveMatchState, LiveSide
from ..core.simulation.live_card_images import LiveCardImages
from ..core.simulation.live_contexts import LIVE_GAME_CONTEXTS as _CONTEXTS, LiveGameContext
from ..core.simulation.matchup import MatchupClub, MatchupError
from ..core.simulation.models import GameStuckError
from ..core.simulation.team import SimTeam
from .image_libraries import UserImageLibraries
from .sim import _faceoff_team_row, _is_uuid, _parse_manager_preference, _RequestError, _roster_error
from .user_settings import optional_user_id, require_auth

live_games_bp = Blueprint('live_games', __name__)

# THE IDLE TIMER CHOICES OFFERED WHEN A GAME IS CREATED. NONE (THE DEFAULT) IS "TAKE YOUR TIME".
_IDLE_AUTOPILOT_CHOICES = (None, 2, 5, 15, 60)
_OPEN_INVITES_PER_USER = int(os.environ.get('LIVE_GAME_OPEN_INVITES', 10))
_DEFAULT_SHOWDOWN_SET = '2000'


# ----------------------------------------------------------------------
# CLUBS
# ----------------------------------------------------------------------

class TeamRef(BaseModel):
    """Which club takes a seat.

    saved: a Team Builder team (`team_id`), yours or a public one.
    historical: an MLB club's roster for one `season` (`team_id` is the MLB team id).
    era: a current MLB club's Era Roster (`era` key, `team_id` the MLB team id).
    random_historical: any historical club, optionally from one `season`; stored as the historical
        club it landed on.
    """

    kind: Literal['saved', 'historical', 'era', 'random_historical']
    team_id: Optional[Union[str, int]] = None
    season: Optional[int] = None
    sport_id: int = 1
    era: Optional[str] = None


class LiveClubResolver:
    """Turns a `TeamRef` into a club ready to take a seat, with every card frozen as it is now."""

    def __init__(self, db: PostgresDB, user_id: str, showdown_set: str = _DEFAULT_SHOWDOWN_SET) -> None:
        self.db = db
        self.user_id = user_id
        self.showdown_set = showdown_set

    def team(self, ref: TeamRef) -> tuple[TeamRef, BuilderTeam, int]:
        """The club `ref` names, the concrete ref it resolved to, and its points."""
        try:
            if ref.kind == 'saved':
                row = _faceoff_team_row(self.db, ref.team_id, self.user_id)
                return ref, BuilderTeam.from_db_row(row), int(row.get('total_points') or 0)
            if ref.kind == 'random_historical':
                pick = self.db.fetch_random_historical_team(sport_id=ref.sport_id, season=ref.season)
                if pick is None:
                    raise _RequestError("There's no historical team to pick from.", 404)
                ref = TeamRef(kind='historical', season=int(pick['season']), team_id=int(pick['team_id']), sport_id=int(pick['sport_id']))
            if ref.kind == 'historical':
                if ref.season is None or ref.team_id is None:
                    raise _RequestError('A historical team needs a season and a team.', 400)
                data = SyntheticTeams.historical(season=ref.season, team_id=int(ref.team_id), sport_id=ref.sport_id, showdown_set=self.showdown_set)
            else:
                if ref.team_id is None:
                    raise _RequestError('An era team needs a team.', 400)
                data = SyntheticTeams.era(team_id=int(ref.team_id), era_key=ref.era or 'ALL_TIME', sport_id=ref.sport_id, showdown_set=self.showdown_set)
        except (SyntheticTeamError, ValueError) as exc:
            raise _RequestError(str(exc), 400) from exc
        team = SyntheticTeams.as_team(data)
        roster_error = _roster_error(team)
        if roster_error:
            raise _RequestError(f"{team.name}: {roster_error}", 422)
        return ref, team, int(data.get('total_points') or 0)

    def seat(self, ref: TeamRef, starter_card_id: Optional[str] = None, manager: Optional[dict] = None) -> tuple[TeamRef, dict]:
        """A seat's frozen setup: its club (team, starter, manager), branding and every card."""
        ref, team, total_points = self.team(ref)
        club = MatchupClub(team=team, total_points=total_points, starter_card_id=starter_card_id, manager=_parse_manager_preference(manager))
        cards = self.db.fetch_cards_for_roster_slots(slots=team.roster, strip_diagnostics=True)
        if any(slot.card_id not in cards for slot in team.roster):
            raise _RequestError(f"{team.name} has a card that can no longer be loaded.", 422)
        return ref, {
            'club': club.model_dump(mode='json'),
            'identity': SimTeam.builder_team_identity(team).model_dump(mode='json'),
            'cards': {card_id: card.model_dump(mode='json') for card_id, card in cards.items()},
        }


# ----------------------------------------------------------------------
# SESSION
# ----------------------------------------------------------------------

class LiveGameSession:
    """One stored live game, loaded for a request: its row, its actions and the rebuilt match."""

    def __init__(self, db: PostgresDB, row: dict) -> None:
        self.db = db
        self.row = row
        self.settings = LiveMatchSettings(**(row.get('settings') or {}))
        self.context = _CONTEXTS.get(row.get('context_kind') or 'open', _CONTEXTS['open'])
        self.is_started = row['status'] not in ('invited', 'cancelled')
        self.actions = [LiveAction(**a) for a in db.fetch_live_game_actions(row['live_game_id'])] if self.is_started else []
        self.match = self.build_match(row) if self.is_started else None

    @classmethod
    def load(cls, db: PostgresDB, live_game_id: str) -> Optional['LiveGameSession']:
        row = db.fetch_live_game(live_game_id=live_game_id) if _is_uuid(live_game_id) else None
        return cls(db, row) if row else None

    @staticmethod
    def build_match(row: dict) -> LiveMatch:
        setup = row['setup']
        settings = LiveMatchSettings(**(row.get('settings') or {}))
        return LiveMatch(
            clubs={side: MatchupClub(**setup[side.value]['club']) for side in LiveSide},
            cards={side: {card_id: ShowdownPlayerCard(**data) for card_id, data in setup[side.value]['cards'].items()} for side in LiveSide},
            seed=int(row['seed']),
            sim_sides=frozenset(side for side in LiveSide if row.get(f'{side.value}_controller') == 'sim'),
            every_roll_by_hand=settings.every_roll_by_hand,
        )

    def sides_for(self, user_id: Optional[str]) -> list[LiveSide]:
        """The seats this user plays: none for a spectator, both for someone playing themselves."""
        return [side for side in LiveSide if user_id and self.row.get(f'{side.value}_user_id') == user_id]

    def open_side(self) -> Optional[LiveSide]:
        """The seat still waiting for whoever opens the invite."""
        return next((side for side in LiveSide if self.row.get(f'{side.value}_controller') == 'human' and not self.row.get(f'{side.value}_user_id')), None)

    def state(self) -> LiveMatchState:
        """The game as it stands, after switching on any autopilot the idle timer owes."""
        state = self.match.replay(self.actions)
        owed = LiveMatch.idle_autopilot_action(state, self.settings, self.row['last_action_at'])
        if owed is not None:
            state = self._commit(owed, user_id=None, expected_state=state) or self.match.replay(self.actions)
        return state

    def act(self, action: LiveAction, user_id: str, expected_seq: int) -> LiveMatchState:
        if self.row['status'] != 'active':
            raise LiveMatchError('This game is not being played.')
        mine = self.sides_for(user_id)
        if not mine:
            raise _RequestError("That's not your team.", 403)
        if expected_seq != len(self.actions):
            raise _RequestError('The game moved on. Refresh and try again.', 409)
        state = self.match.replay(self.actions)
        # A SIDE ON AUTOPILOT (THE SIM'S SEAT, OR AN IDLE PLAYER'S) HAS ITS DICE ROLLED BY ANY PLAYER IN THE GAME.
        rolls_for_autopilot = action.kind == LiveActionKind.ROLL and state.sides[action.side].autopilot
        if action.side not in mine and not rolls_for_autopilot:
            raise _RequestError("That's not your team.", 403)
        new_state = self._commit(action, user_id=user_id, expected_state=state)
        if new_state is None:
            raise _RequestError('The game moved on. Refresh and try again.', 409)
        return new_state

    def _commit(self, action: LiveAction, user_id: Optional[str], expected_state: LiveMatchState) -> Optional[LiveMatchState]:
        """Validate, store and broadcast one action. None if another action landed first."""
        self.match.validate(expected_state, action)
        new_state = self.match.replay([*self.actions, action])
        final = {
            'result': new_state.game.model_dump(mode='json'),
            'winner_side': new_state.winner_side.value if new_state.winner_side else None,
        } if new_state.is_final else None
        stored = self.db.append_live_game_action(
            live_game_id=self.row['live_game_id'], expected_seq=len(self.actions), user_id=user_id,
            action=action.model_dump(mode='json'),
            pending_side=new_state.pending.side.value if new_state.pending else None,
            final=final,
            on_final=(lambda cur: self.context.on_final(cur, self.row, new_state)) if final else None,
        )
        if not stored:
            return None
        self.actions.append(action)
        _broadcast_seq(self.row['live_game_id'], new_state.seq)
        return new_state

    def seat_payload(self, side: LiveSide, user_id: Optional[str]) -> dict:
        row = self.row
        return {
            'controller': row.get(f'{side.value}_controller'),
            'identity': (row['setup'].get(side.value) or {}).get('identity'),
            'is_mine': side in self.sides_for(user_id),
            # A PERSON'S SEAT NOBODY HAS TAKEN YET.
            'is_open': side == self.open_side(),
        }

    def payload(self, user_id: Optional[str], state: Optional[LiveMatchState] = None) -> dict:
        """What the client gets: the game's public fields, its seats, the viewer's seats and play."""
        row = self.row
        is_creator = user_id is not None and row.get('created_by') == user_id
        return {
            'live_game_id': row['live_game_id'],
            'status': 'final' if state is not None and state.is_final else row['status'],
            'context': {'kind': row.get('context_kind'), 'ref': row.get('context_ref')},
            'settings': self.settings.model_dump(mode='json'),
            'seats': {side.value: self.seat_payload(side, user_id) for side in LiveSide},
            'my_sides': [side.value for side in self.sides_for(user_id)],
            # ONLY THE CREATOR NEEDS THE CODE, TO SHARE IT AGAIN WHILE THE INVITE IS OPEN.
            'invite_code': row['invite_code'] if is_creator and row['status'] == 'invited' else None,
            'is_creator': is_creator,
            'last_action_at': row['last_action_at'].isoformat() if row.get('last_action_at') else None,
            'state': state.model_dump(mode='json') if state is not None else None,
        }


def _start(row: dict, setup: dict) -> tuple[int, Optional[str]]:
    """Seed a game whose seats are all filled and build it once, so a roster the engine can't field
    fails before the game starts rather than on the first roll. Returns (seed, first side up)."""
    seed = random.randrange(2 ** 31)
    first = LiveGameSession.build_match({**row, 'setup': setup, 'seed': seed}).replay([])
    return seed, first.pending.side.value if first.pending else None


def open_live_game(
    db: PostgresDB, created_by: str, seats: dict, setup: dict, settings: Optional[dict] = None,
    invite_code: Optional[str] = None, context_kind: str = 'open', context_ref: Optional[str] = None,
) -> str:
    """Store a new live game for any feature: the routes below for 'open' games, a Faceoff played
    by hand, a league fixture. A game with every seat filled and no invite out starts at once.

    Args:
      seats: Per side ('away', 'home'): `controller` ('human' or 'sim'), `user_id`, `team_ref`.
      setup: Per filled side: `LiveClubResolver.seat`'s frozen club.
    """
    if context_kind not in _CONTEXTS:
        raise ValueError(f"Unknown live game context: {context_kind}")
    # EVERY GAME OPENED NOW THROWS EVERY DIE FROM A BUTTON, THE SIM'S SEAT INCLUDED.
    settings = LiveMatchSettings(**(settings or {})).model_copy(update={'every_roll_by_hand': True}).model_dump(mode='json')
    seed, pending_side = None, None
    if invite_code is None:
        seed, pending_side = _start({'settings': settings, **{f'{side}_controller': seat['controller'] for side, seat in seats.items()}}, setup)
    return db.create_live_game(
        created_by=created_by, seats=seats, setup=setup, settings=settings,
        invite_code=invite_code, context_kind=context_kind, context_ref=context_ref, seed=seed, pending_side=pending_side,
    )


def _broadcast_seq(live_game_id: str, seq: int) -> None:
    """Tell anyone watching that the game moved. Best effort: clients also poll."""
    url, key = os.getenv('SUPABASE_URL', '').rstrip('/'), os.getenv('SUPABASE_KEY')
    if not url or not key:
        return
    try:
        requests.post(
            f"{url}/realtime/v1/api/broadcast",
            headers={'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'messages': [{'topic': f'live-game:{live_game_id}', 'event': 'seq', 'payload': {'seq': seq}}]},
            timeout=2,
        )
    except requests.RequestException:
        traceback.print_exc()


def _error_response(exc: Exception):
    if isinstance(exc, _RequestError):
        return jsonify({'error': str(exc)}), exc.status
    if isinstance(exc, (MatchupError, ValidationError, ValueError)):
        return jsonify({'error': str(exc)}), 400
    if isinstance(exc, GameStuckError):
        traceback.print_exc()
        return jsonify({'error': str(exc), 'context': exc.context}), 422
    traceback.print_exc()
    return jsonify({'error': str(exc)}), 500


# ----------------------------------------------------------------------
# CREATE / INVITE
# ----------------------------------------------------------------------

class _SeatRequest(BaseModel):
    team: Optional[TeamRef] = None
    starter_card_id: Optional[str] = None
    manager: Optional[dict] = None


class _OpponentRequest(_SeatRequest):
    # 'invite': whoever opens the link plays it (bringing their own team when `team` is left out).
    # 'sim': the sim plays it. 'me': the creator plays both seats.
    controller: Literal['invite', 'sim', 'me'] = 'invite'


class _CreateRequest(_SeatRequest):
    my_side: LiveSide = LiveSide.AWAY
    opponent: _OpponentRequest = _OpponentRequest()
    idle_autopilot_minutes: Optional[int] = None
    showdown_set: str = _DEFAULT_SHOWDOWN_SET


@live_games_bp.route('/sim/live', methods=['POST'])
@require_auth
def create_live_game():
    """Start a game with any club in the creator's seat and the other seat played by the sim, by
    the creator too, or by whoever the invite link goes to."""
    try:
        body = _CreateRequest(**(request.get_json(silent=True) or {}))
        if body.idle_autopilot_minutes not in _IDLE_AUTOPILOT_CHOICES:
            return jsonify({'error': f"idle_autopilot_minutes must be one of {list(_IDLE_AUTOPILOT_CHOICES)}"}), 400
        if body.team is None:
            return jsonify({'error': 'Pick a team to play.'}), 400
        opponent = body.opponent
        if opponent.team is None and opponent.controller != 'invite':
            return jsonify({'error': 'Pick a team for the other side.'}), 400

        mine, theirs = body.my_side, body.my_side.other
        settings = LiveMatchSettings(idle_autopilot_minutes=body.idle_autopilot_minutes).model_dump(mode='json')
        with PostgresDB() as db:
            if opponent.controller == 'invite':
                open_invites = [row for row in db.fetch_live_games_for_user(g.user_id, limit=50) if row['status'] == 'invited']
                if len(open_invites) >= _OPEN_INVITES_PER_USER:
                    return jsonify({'error': 'You have a lot of open invites. Cancel one first.'}), 429

            resolver = LiveClubResolver(db, g.user_id, body.showdown_set)
            my_ref, my_setup = resolver.seat(body.team, body.starter_card_id, body.manager)
            setup = {mine.value: my_setup}
            their_ref = None
            if opponent.team is not None:
                their_ref, setup[theirs.value] = resolver.seat(opponent.team, opponent.starter_card_id, opponent.manager)
                if my_ref.kind == 'saved' and their_ref.kind == 'saved' and str(my_ref.team_id) == str(their_ref.team_id):
                    return jsonify({'error': 'Pick a different team for the other side.'}), 400

            seats = {
                mine.value: {'controller': 'human', 'user_id': g.user_id, 'team_ref': my_ref.model_dump(mode='json')},
                theirs.value: {
                    'controller': 'sim' if opponent.controller == 'sim' else 'human',
                    'user_id': g.user_id if opponent.controller == 'me' else None,
                    'team_ref': their_ref.model_dump(mode='json') if their_ref else None,
                },
            }
            invite_code = secrets.token_urlsafe(9) if opponent.controller == 'invite' else None
            live_game_id = open_live_game(db, g.user_id, seats, setup, settings=settings, invite_code=invite_code)
        return jsonify({'live_game_id': live_game_id, 'invite_code': invite_code}), 201
    except Exception as exc:
        return _error_response(exc)


@live_games_bp.route('/sim/live/invite/<invite_code>', methods=['GET'])
def get_live_game_invite(invite_code: str):
    """What the accept screen shows: the seat on offer, the club in it (or that you bring your own),
    who you'd face, and how the game is paced."""
    try:
        with PostgresDB() as db:
            row = db.fetch_live_game(invite_code=invite_code)
            if row is None or row['status'] == 'cancelled':
                return jsonify({'error': 'Invite not found'}), 404
            session = LiveGameSession(db, row)
        open_side = session.open_side()
        user_id = optional_user_id()
        return jsonify({
            'live_game_id': row['live_game_id'],
            'status': row['status'],
            'open_side': open_side.value if open_side else None,
            'seats': {side.value: session.seat_payload(side, user_id) for side in LiveSide},
            # NULL: THE INVITEE BRINGS THEIR OWN TEAM.
            'open_seat_team_ref': row.get(f'{open_side.value}_team_ref') if open_side else None,
            'settings': row['settings'],
            'is_mine': row['created_by'] == user_id,
        }), 200
    except Exception as exc:
        return _error_response(exc)


class _AcceptRequest(_SeatRequest):
    showdown_set: str = _DEFAULT_SHOWDOWN_SET


@live_games_bp.route('/sim/live/invite/<invite_code>/accept', methods=['POST'])
@require_auth
def accept_live_game(invite_code: str):
    """Take the open seat, which starts the game. Brings a team when the seat doesn't have one;
    either way the invitee picks their own starter and manager."""
    try:
        body = _AcceptRequest(**(request.get_json(silent=True) or {}))
        with PostgresDB() as db:
            row = db.fetch_live_game(invite_code=invite_code)
            if row is None or row['status'] != 'invited':
                return jsonify({'error': 'This invite is no longer open.'}), 410
            session = LiveGameSession(db, row)
            side = session.open_side()
            if side is None:
                return jsonify({'error': 'This invite is no longer open.'}), 410

            setup = dict(row['setup'])
            team_ref = None
            if side.value in setup:
                # THE CREATOR PICKED THIS SEAT'S CLUB; ITS STARTER AND MANAGER ARE THE INVITEE'S CALL.
                club = MatchupClub(**setup[side.value]['club'])
                club = club.model_copy(update={'starter_card_id': body.starter_card_id or club.starter_card_id, 'manager': _parse_manager_preference(body.manager) or club.manager})
                setup[side.value] = {**setup[side.value], 'club': club.model_dump(mode='json')}
            else:
                if body.team is None:
                    return jsonify({'error': 'Pick a team to play.'}), 400
                ref, setup[side.value] = LiveClubResolver(db, g.user_id, body.showdown_set).seat(body.team, body.starter_card_id, body.manager)
                other_ref = row.get(f'{side.other.value}_team_ref') or {}
                if ref.kind == 'saved' and other_ref.get('kind') == 'saved' and str(other_ref.get('team_id')) == str(ref.team_id):
                    return jsonify({'error': 'Pick a different team to face.'}), 400
                team_ref = ref.model_dump(mode='json')

            seed, pending_side = _start(row, setup)
            started = db.accept_live_game(
                live_game_id=row['live_game_id'], side=side.value, user_id=g.user_id, seed=seed, pending_side=pending_side,
                side_setup=setup[side.value], team_ref=team_ref,
            )
        if not started:
            return jsonify({'error': 'Someone else took this seat first.'}), 409
        _broadcast_seq(row['live_game_id'], 0)
        return jsonify({'live_game_id': row['live_game_id']}), 200
    except Exception as exc:
        return _error_response(exc)


@live_games_bp.route('/sim/live/<live_game_id>/cancel', methods=['POST'])
@require_auth
def cancel_live_game(live_game_id: str):
    try:
        with PostgresDB() as db:
            cancelled = _is_uuid(live_game_id) and db.cancel_live_game(live_game_id, g.user_id)
        if not cancelled:
            return jsonify({'error': 'Only an open invite of yours can be cancelled.'}), 400
        return jsonify({'cancelled': True}), 200
    except Exception as exc:
        return _error_response(exc)


# ----------------------------------------------------------------------
# PLAY
# ----------------------------------------------------------------------

@live_games_bp.route('/sim/live/<live_game_id>', methods=['GET'])
def get_live_game(live_game_id: str):
    """The game as it stands. Anyone with the link can watch. `?since=<seq>` answers
    `{"unchanged": true}` when nothing has happened, so polling stays cheap."""
    try:
        user_id = optional_user_id()
        since = request.args.get('since', type=int)
        with PostgresDB() as db:
            session = LiveGameSession.load(db, live_game_id)
            if session is None or session.row['status'] == 'cancelled':
                return jsonify({'error': 'Game not found'}), 404
            if session.match is None:
                return jsonify(session.payload(user_id)), 200
            # THE IDLE TIMER CAN STILL MOVE A GAME WHOSE SEQ MATCHES, SO ONLY SKIP THE REPLAY WHEN IT'S OFF.
            if since is not None and since == session.row['seq'] and session.settings.idle_autopilot_minutes is None:
                return jsonify({'unchanged': True, 'seq': since}), 200
            return jsonify(session.payload(user_id, session.state())), 200
    except Exception as exc:
        return _error_response(exc)


@live_games_bp.route('/sim/live/<live_game_id>/actions', methods=['POST'])
@require_auth
def post_live_game_action(live_game_id: str):
    """One move: `{"expected_seq": n, "action": {...LiveAction}}`. Returns the game after it."""
    try:
        payload = request.get_json(silent=True) or {}
        action = LiveAction(**(payload.get('action') or {}))
        expected_seq = payload.get('expected_seq')
        if not isinstance(expected_seq, int):
            return jsonify({'error': 'expected_seq is required'}), 400
        with PostgresDB() as db:
            session = LiveGameSession.load(db, live_game_id)
            if session is None:
                return jsonify({'error': 'Game not found'}), 404
            state = session.act(action, user_id=g.user_id, expected_seq=expected_seq)
            return jsonify(session.payload(g.user_id, state)), 200
    except Exception as exc:
        return _error_response(exc)


def _frozen_cards(live_game_id: str) -> Optional[dict[str, dict]]:
    """Every card's data in a game, as frozen when its seats were filled, keyed by card id. None
    when there's no such game (or it was cancelled)."""
    with PostgresDB() as db:
        row = db.fetch_live_game(live_game_id=live_game_id) if _is_uuid(live_game_id) else None
    if row is None or row['status'] == 'cancelled':
        return None
    return {card_id: data for seat in row['setup'].values() for card_id, data in (seat.get('cards') or {}).items()}


@live_games_bp.route('/sim/live/<live_game_id>/cards', methods=['GET'])
def get_live_game_cards(live_game_id: str):
    """Every card in the game, as frozen when its seats were filled, keyed by card id."""
    try:
        cards = _frozen_cards(live_game_id)
        if cards is None:
            return jsonify({'error': 'Game not found'}), 404
        return jsonify({'cards': {card_id: ShowdownPlayerCard(**data).as_json() for card_id, data in cards.items()}}), 200
    except Exception as exc:
        return _error_response(exc)


@live_games_bp.route('/sim/live/<live_game_id>/cards/<card_id>/image', methods=['GET'])
def get_live_game_card_image(live_game_id: str, card_id: str):
    """One of the game's cards as a rendered image, with the viewer's image libraries, plus where
    each chart result and the command sit on it. Rendered the first time anyone asks (a few seconds), then stored."""
    try:
        data = (_frozen_cards(live_game_id) or {}).get(card_id)
        if data is None:
            return jsonify({'error': 'Card not found'}), 404
        images = LiveCardImages(UserImageLibraries.for_card_build(optional_user_id()))
        return jsonify(images.image_json(ShowdownPlayerCard(**data))), 200
    except Exception as exc:
        return _error_response(exc)


@live_games_bp.route('/sim/live/mine', methods=['GET'])
@require_auth
def get_my_live_games():
    """The user's live games, with whose turn it is, most recently played first."""
    try:
        with PostgresDB() as db:
            rows = db.fetch_live_games_for_user(g.user_id, context_kind=request.args.get('context'))
        games = []
        for row in rows:
            sides = [side.value for side in LiveSide if row.get(f'{side.value}_user_id') == g.user_id]
            games.append({
                'live_game_id': row['live_game_id'],
                'status': row['status'],
                'context': {'kind': row.get('context_kind'), 'ref': row.get('context_ref')},
                'identities': {'away': row.get('away_identity'), 'home': row.get('home_identity')},
                'controllers': {'away': row.get('away_controller'), 'home': row.get('home_controller')},
                'my_sides': sides,
                # THE SIM'S ROLLS ARE THE PLAYER'S TO MAKE TOO.
                'is_my_turn': row['status'] == 'active' and bool(sides) and (
                    row.get('pending_side') in sides or row.get(f"{row.get('pending_side')}_controller") == 'sim'
                ),
                'winner_side': row.get('winner_side'),
                'invite_code': row['invite_code'] if row['status'] == 'invited' and row.get('created_by') == g.user_id else None,
                'last_action_at': row['last_action_at'].isoformat() if row.get('last_action_at') else None,
            })
        return jsonify({'games': games}), 200
    except Exception as exc:
        return _error_response(exc)
