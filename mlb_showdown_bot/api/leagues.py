"""Leagues: create/join a league over a card pool of Release Builder editions, draft teams, and
play seasons of simulated games.

Thin routes over `core/league` (draft rules, bot picks, the season runner) and the league methods
on `PostgresDB`.
Every route needs a signed-in user; everything past the join-code preview needs membership.
"""

import random
import threading
import time
import traceback
from dataclasses import dataclass
from datetime import date, datetime
from functools import wraps
from typing import Optional

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError

from ..core.database.postgres_db import PostgresDB
from ..core.league import (
    DraftConflict, DraftError, LeagueDraft, LeagueRosterMove, LeagueSeasonError, LeagueSeasonRunner, LeagueSettings, SeasonConfig,
    SimTarget,
)
from ..core.supabase.realtime_broadcast import RealtimeBroadcaster
from .sim import _sim_slots
from .user_settings import require_auth
from .utils.join_code import JoinCode
from .utils.profanity_filter import ProfanityFilter

leagues_bp = Blueprint('leagues', __name__)

_MAX_EDITIONS = 10
_LEAGUE_NAME_MAX = 80
_DISPLAY_NAME_MAX = 40


class _ApiError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _json_errors(route):
    """Turn `_ApiError` / draft errors into JSON responses, and anything else into a logged 500."""
    @wraps(route)
    def wrapped(*args, **kwargs):
        try:
            return route(*args, **kwargs)
        except _ApiError as exc:
            return jsonify({'error': str(exc)}), exc.status
        except DraftConflict as exc:
            return jsonify({'error': str(exc)}), 409
        except (DraftError, LeagueSeasonError) as exc:
            return jsonify({'error': str(exc)}), 400
        except Exception as exc:
            traceback.print_exc()
            return jsonify({'error': str(exc)}), 500
    return wrapped


def _jsonable(value):
    """Dates to ISO strings, recursively, so every league payload serializes the same way."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _clean_name(value, field: str, max_length: int) -> str:
    name = str(value or '').strip()
    if not name:
        raise _ApiError(f"{field} is required")
    if len(name) > max_length:
        raise _ApiError(f"{field} must be {max_length} characters or fewer")
    if ProfanityFilter.contains_profanity(name):
        raise _ApiError(f"{field} contains language that is not allowed")
    return name


def _display_name(db: PostgresDB, requested) -> str:
    """The name a member shows under: what they asked for, else their profile username."""
    if requested:
        return _clean_name(requested, 'Display name', _DISPLAY_NAME_MAX)
    return (db.get_profile_username(g.user_id) or 'Member')[:_DISPLAY_NAME_MAX]


def _parse_settings(raw: dict) -> LeagueSettings:
    try:
        return LeagueSettings(**raw)
    except ValidationError as exc:
        raise _ApiError('; '.join(err['msg'] for err in exc.errors()))


@dataclass
class _LeagueContext:
    """One league as the signed-in caller sees it."""

    league: dict
    members: list[dict]

    @property
    def my_member(self) -> Optional[dict]:
        return next((m for m in self.members if m.get('user_id') == g.user_id), None)

    @property
    def is_commissioner(self) -> bool:
        return self.league['commissioner_user_id'] == g.user_id

    @property
    def settings(self) -> LeagueSettings:
        return LeagueSettings(**(self.league.get('settings') or {}))

    @classmethod
    def load(cls, db: PostgresDB, league_id: str, require_member: bool = True, require_commissioner: bool = False) -> '_LeagueContext':
        league = db.get_league(league_id)
        if league is None:
            raise _ApiError('League not found', 404)
        context = cls(league=league, members=db.get_league_members(league_id))
        if require_member and context.my_member is None:
            raise _ApiError('You are not a member of this league', 403)
        if require_commissioner and not context.is_commissioner:
            raise _ApiError('Only the commissioner can do that', 403)
        return context

    def season(self, db: PostgresDB, season_number: Optional[int] = None) -> dict:
        season = db.get_league_season(self.league['league_id'], season_number)
        if season is None:
            raise _ApiError('Season not found', 404)
        return season

    def payload(self, db: PostgresDB) -> dict:
        season = db.get_league_season(self.league['league_id'])
        my_member = self.my_member
        return _jsonable({
            'league': self.league,
            'members': self.members,
            'season': season,
            'teams': db.get_league_teams(season['season_id']) if season else [],
            'my_member_id': my_member['member_id'] if my_member else None,
            'is_commissioner': self.is_commissioner,
        })


def _draft_payload(context: _LeagueContext, draft: LeagueDraft) -> dict:
    my_member = context.my_member
    return _jsonable({
        'season': draft.season,
        'draft': draft.state(viewer_member_id=my_member['member_id'] if my_member else None),
    })


def _draft_changed_payload(context: _LeagueContext, draft: LeagueDraft) -> dict:
    """`_draft_payload` after a change to the board, pinging open draft rooms to refetch."""
    RealtimeBroadcaster().league_draft_changed(context.league['league_id'], draft.season['season_number'])
    return _draft_payload(context, draft)


# ----------------------------------------------------------
# MARK: - LEAGUES
# ----------------------------------------------------------

@leagues_bp.route('/leagues', methods=['POST'])
@require_auth
@_json_errors
def create_league():
    """Create a league over one or more editions. The caller becomes commissioner and member 1."""
    payload = request.get_json(silent=True) or {}
    name = _clean_name(payload.get('name'), 'League name', _LEAGUE_NAME_MAX)
    settings = _parse_settings(payload.get('settings') or {})

    edition_ids = list(dict.fromkeys(str(e) for e in (payload.get('edition_ids') or []) if e))
    if not edition_ids:
        raise _ApiError('Pick at least one edition for the card pool')
    if len(edition_ids) > _MAX_EDITIONS:
        raise _ApiError(f'A league can use up to {_MAX_EDITIONS} editions')

    with PostgresDB() as db:
        editions = db.get_league_edition_summaries(edition_ids, g.user_id)
        if len(editions) != len(edition_ids):
            raise _ApiError('One or more editions were not found, or are private drafts you do not own', 404)
        showdown_sets = {s for edition in editions for s in (edition.get('showdown_sets') or [])}
        if len(showdown_sets) != 1:
            raise _ApiError('Every edition in a league must use the same Showdown set')
        card_count = sum(edition['card_count'] or 0 for edition in editions)
        needed = settings.roster_size * settings.team_count
        if card_count < needed:
            raise _ApiError(f'These editions have {card_count} cards; {settings.team_count} teams of {settings.roster_size} need {needed}')

        join_code = JoinCode.generate(db.is_league_join_code_taken)
        if join_code is None:
            raise _ApiError('Could not generate a join code. Try again.', 500)
        league_id = db.create_league(
            commissioner_user_id=g.user_id,
            commissioner_display_name=_display_name(db, payload.get('display_name')),
            name=name,
            join_code=join_code,
            showdown_set=showdown_sets.pop(),
            edition_ids=edition_ids,
            settings=settings.model_dump(),
        )
        return jsonify(_LeagueContext.load(db, league_id).payload(db)), 201


@leagues_bp.route('/leagues/mine', methods=['GET'])
@require_auth
@_json_errors
def list_my_leagues():
    with PostgresDB() as db:
        return jsonify(_jsonable(db.list_user_leagues(g.user_id))), 200


@leagues_bp.route('/leagues/code/<code>', methods=['GET'])
@require_auth
@_json_errors
def preview_league(code: str):
    """What a join code leads to, shown before joining: name, card pool, seats taken."""
    with PostgresDB() as db:
        league = db.get_league_by_code(JoinCode.normalize(code))
        if league is None:
            raise _ApiError('League not found', 404)
        members = db.get_league_members(league['league_id'])
        settings = LeagueSettings(**(league.get('settings') or {}))
        return jsonify(_jsonable({
            'league_id': league['league_id'],
            'name': league['name'],
            'status': league['status'],
            'showdown_set': league['showdown_set'],
            'team_count': settings.team_count,
            'member_count': len(members),
            'commissioner_name': next((m['display_name'] for m in members if m['user_id'] == league['commissioner_user_id']), None),
            'is_member': any(m['user_id'] == g.user_id for m in members),
        })), 200


@leagues_bp.route('/leagues/join/<code>', methods=['POST'])
@require_auth
@_json_errors
def join_league(code: str):
    payload = request.get_json(silent=True) or {}
    with PostgresDB() as db:
        league = db.get_league_by_code(JoinCode.normalize(code))
        if league is None:
            raise _ApiError('League not found', 404)
        context = _LeagueContext.load(db, league['league_id'], require_member=False)
        if context.my_member is None:
            added = db.add_league_members(
                league['league_id'], [(g.user_id, _display_name(db, payload.get('display_name')))],
                max_members=context.settings.team_count,
            )
            if added is None:
                raise _ApiError('This league is full or has already started', 409)
            context = _LeagueContext.load(db, league['league_id'])
        return jsonify(context.payload(db)), 200


@leagues_bp.route('/leagues/<league_id>', methods=['GET'])
@require_auth
@_json_errors
def get_league(league_id: str):
    """League, members, latest season and its teams. Polled by the league page."""
    with PostgresDB() as db:
        return jsonify(_LeagueContext.load(db, league_id).payload(db)), 200


@leagues_bp.route('/leagues/<league_id>', methods=['PATCH'])
@require_auth
@_json_errors
def update_league(league_id: str):
    """Rename the league anytime; change its settings only before the first draft."""
    payload = request.get_json(silent=True) or {}
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id, require_commissioner=True)
        name = _clean_name(payload['name'], 'League name', _LEAGUE_NAME_MAX) if 'name' in payload else None
        settings = None
        if payload.get('settings'):
            if context.league['status'] != 'open':
                raise _ApiError('Settings are locked once the first draft starts', 409)
            merged = _parse_settings({**(context.league.get('settings') or {}), **payload['settings']})
            if merged.team_count < len(context.members):
                raise _ApiError(f'The league already has {len(context.members)} members')
            settings = merged.model_dump()
        db.update_league(league_id, name=name, settings=settings)
        return jsonify(_LeagueContext.load(db, league_id).payload(db)), 200


@leagues_bp.route('/leagues/<league_id>/bots', methods=['POST'])
@require_auth
@_json_errors
def add_bots(league_id: str):
    """Fill `count` empty seats (default: all of them) with bot teams."""
    payload = request.get_json(silent=True) or {}
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id, require_commissioner=True)
        open_seats = context.settings.team_count - len(context.members)
        count = int(payload.get('count') or open_seats)
        if count < 1 or count > open_seats:
            raise _ApiError(f'There {"is" if open_seats == 1 else "are"} {open_seats} open seat{"" if open_seats == 1 else "s"}')
        bot_count = sum(1 for m in context.members if m.get('user_id') is None)
        bots = [(None, f'Bot {bot_count + i + 1}') for i in range(count)]
        if db.add_league_members(league_id, bots, max_members=context.settings.team_count) is None:
            raise _ApiError('This league is full or has already started', 409)
        return jsonify(_LeagueContext.load(db, league_id).payload(db)), 200


@leagues_bp.route('/leagues/<league_id>/members/<member_id>', methods=['DELETE'])
@require_auth
@_json_errors
def remove_member(league_id: str, member_id: str):
    """The commissioner removes a member, or a member leaves - only before the first draft."""
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id)
        member = next((m for m in context.members if m['member_id'] == member_id), None)
        if member is None:
            raise _ApiError('Member not found', 404)
        if member.get('user_id') == context.league['commissioner_user_id']:
            raise _ApiError('The commissioner can\'t leave their own league', 409)
        if not context.is_commissioner and member.get('user_id') != g.user_id:
            raise _ApiError('Only the commissioner can remove other members', 403)
        if not db.remove_league_member(league_id, member_id):
            raise _ApiError('Members can only leave before the draft starts', 409)
        return jsonify(_LeagueContext.load(db, league_id, require_member=False).payload(db)), 200


# ----------------------------------------------------------
# MARK: - DRAFT
# ----------------------------------------------------------

@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/draft/start', methods=['POST'])
@require_auth
@_json_errors
def start_draft(league_id: str, season_number: int):
    """Start season `season_number`'s draft: set the order (random, or the commissioner's
    `order` of member ids), create every member's team, and make any opening bot picks."""
    payload = request.get_json(silent=True) or {}
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id, require_commissioner=True)
        latest = db.get_league_season(league_id)
        expected = (latest['season_number'] + 1) if latest else 1
        if season_number != expected:
            raise _ApiError(f'The next season to start is season {expected}', 409)
        if latest and latest['status'] != 'complete':
            raise _ApiError(f'Season {latest["season_number"]} is still in progress', 409)

        manual_order = payload.get('order') if context.settings.draft_order_mode == 'manual' else None
        season_id = LeagueDraft.start(db, context.league, context.members, season_number, manual_order=manual_order)
        if latest:  # A REDRAFT KEEPS LAST SEASON'S SCHEDULE AND POSTSEASON SETTINGS
            db.update_league_season_config(season_id, latest.get('config') or {})
        draft = LeagueDraft(db, context.league, context.season(db, season_number))
        draft.run_bot_picks()
        return jsonify(_draft_changed_payload(context, draft)), 201


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/draft', methods=['GET'])
@require_auth
@_json_errors
def get_draft(league_id: str, season_number: int):
    """The draft board - refetched by the draft room and the Big Board on each Realtime ping (and a slow poll)."""
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id)
        draft = LeagueDraft(db, context.league, context.season(db, season_number))
        return jsonify(_draft_payload(context, draft)), 200


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/draft/pick', methods=['POST'])
@require_auth
@_json_errors
def make_pick(league_id: str, season_number: int):
    """Draft `release_card_id` (into `roster_position`, if given) for the team on the clock, or
    `auto: true` to let the bot pick (the commissioner's way past a stalled seat). Bot seats then
    pick until a human is up."""
    payload = request.get_json(silent=True) or {}
    release_card_id = None if payload.get('auto') else payload.get('release_card_id')
    roster_position = None if payload.get('auto') else payload.get('roster_position')
    if not release_card_id and not payload.get('auto'):
        raise _ApiError('release_card_id is required')
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id)
        draft = LeagueDraft(db, context.league, context.season(db, season_number))
        draft.make_pick(context.my_member['member_id'], context.is_commissioner, release_card_id, roster_position)
        draft.run_bot_picks()
        return jsonify(_draft_changed_payload(context, draft)), 200


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/roster/move', methods=['POST'])
@require_auth
@_json_errors
def move_roster_player(league_id: str, season_number: int):
    """Move one of my drafted players `release_card_id` into the open `to_position`, or swap it
    with `swap_with_card_id`. Works mid-draft (the team builder's roster save doesn't) and
    returns the draft board."""
    payload = request.get_json(silent=True) or {}
    release_card_id = payload.get('release_card_id')
    to_position = payload.get('to_position')
    swap_with_card_id = payload.get('swap_with_card_id')
    if not release_card_id or not (to_position or swap_with_card_id):
        raise _ApiError('release_card_id and to_position or swap_with_card_id are required')
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id)
        season = context.season(db, season_number)
        team = next((t for t in db.get_league_teams(season['season_id']) if t['member_id'] == context.my_member['member_id']), None)
        if team is None:
            raise _ApiError("You don't have a team this season", 404)
        LeagueRosterMove(db, context.league, season, team).move(release_card_id, str(to_position or ''), swap_with_card_id)
        return jsonify(_draft_changed_payload(context, LeagueDraft(db, context.league, season))), 200


# ----------------------------------------------------------
# MARK: - SEASONS
# ----------------------------------------------------------

def _season_payload(context: _LeagueContext, db: PostgresDB, season: dict) -> dict:
    return _jsonable({
        'season': season,
        'teams': db.get_league_teams(season['season_id']),
        'is_commissioner': context.is_commissioner,
    })


class _LeagueSimJob:
    """Plays one sim chunk in a background thread with its own DB connection, reporting progress
    on the season row (throttled) so the league page can poll it. Shares the MLB sims' per-worker
    slot so a league chunk and a full MLB season never compete for the same dyno's CPU."""

    PROGRESS_WRITE_INTERVAL_SECONDS = 1.0

    def __init__(self, league: dict, season: dict, target: SimTarget) -> None:
        self.league = league
        self.season = season
        self.target = target

    def start(self) -> None:
        threading.Thread(target=self._run, name=f"league-sim-{self.season['season_id'][:8]}", daemon=True).start()

    def _run(self) -> None:
        season_id = self.season['season_id']
        try:
            with PostgresDB() as db:
                last_write = 0.0

                def progress(games_played: int) -> None:
                    nonlocal last_write
                    now = time.monotonic()
                    if now - last_write >= self.PROGRESS_WRITE_INTERVAL_SECONDS:
                        db.update_league_season_job_progress(season_id, games_played)
                        last_write = now

                LeagueSeasonRunner(db, self.league, self.season).run(self.target, progress_callback=progress)
        except LeagueSeasonError as exc:
            self._fail(season_id, str(exc))
        except Exception as exc:
            traceback.print_exc()
            self._fail(season_id, f"The sim failed: {exc}")
        finally:
            _sim_slots.release()

    @staticmethod
    def _fail(season_id: str, message: str) -> None:
        with PostgresDB() as db:
            db.fail_league_season_job(season_id, message)


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>', methods=['GET'])
@require_auth
@_json_errors
def get_season(league_id: str, season_number: int):
    """A season's status, config, sim progress, and summary (standings, leaders, postseason,
    awards). Polled by the league page while a chunk runs."""
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id)
        return jsonify(_season_payload(context, db, context.season(db, season_number))), 200


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/config', methods=['PUT'])
@require_auth
@_json_errors
def update_season_config(league_id: str, season_number: int):
    """Games per team and the postseason bracket - settable until the regular season starts."""
    payload = request.get_json(silent=True) or {}
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id, require_commissioner=True)
        season = context.season(db, season_number)
        try:
            config = SeasonConfig(**payload)
        except ValidationError as exc:
            raise _ApiError('; '.join(err['msg'] for err in exc.errors()))
        team_count = len(db.get_league_teams(season['season_id']))
        if config.postseason.teams > team_count:
            raise _ApiError(f'A {config.postseason.teams}-team postseason needs at least {config.postseason.teams} teams; this league has {team_count}')
        if not db.update_league_season_config(season['season_id'], config.model_dump()):
            raise _ApiError('The schedule is locked once the season starts', 409)
        return jsonify(_season_payload(context, db, context.season(db, season_number))), 200


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/start', methods=['POST'])
@require_auth
@_json_errors
def start_season(league_id: str, season_number: int):
    """`setup` -> `regular`: write the schedule. Every lineup and rotation must be filled."""
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id, require_commissioner=True)
        season = context.season(db, season_number)
        LeagueSeasonRunner(db, context.league, season).start()
        return jsonify(_season_payload(context, db, context.season(db, season_number))), 200


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/sim', methods=['POST'])
@require_auth
@_json_errors
def sim_season(league_id: str, season_number: int):
    """Play a chunk in the background: `{"until": "day" | "week" | "regular_end" | "round" |
    "postseason_end"}`. Returns at once with the season marked running; poll the season route."""
    payload = request.get_json(silent=True) or {}
    try:
        target = SimTarget(payload.get('until'))
    except ValueError:
        raise _ApiError(f"until must be one of: {', '.join(t.value for t in SimTarget)}")
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id, require_commissioner=True)
        season = context.season(db, season_number)
        runner = LeagueSeasonRunner(db, context.league, season)
        if season['status'] not in ('regular', 'postseason'):
            raise _ApiError("This season isn't being played", 409)
        runner.validate_rosters()
        if not _sim_slots.acquire(blocking=False):
            raise _ApiError('The simulator is busy - try again in a minute', 503)
        try:
            if not db.claim_league_season_job(season['season_id'], runner.games_remaining(target)):
                raise _ApiError('Games are already being simulated for this season', 409)
            _LeagueSimJob(context.league, season, target).start()
        except BaseException:
            _sim_slots.release()
            raise
        return jsonify(_season_payload(context, db, context.season(db, season_number))), 202


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/games', methods=['GET'])
@require_auth
@_json_errors
def list_season_games(league_id: str, season_number: int):
    """The schedule and results, optionally for one `day` or one `team` (schedule key)."""
    day = request.args.get('day', type=int)
    team = request.args.get('team')
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id)
        season = context.season(db, season_number)
        return jsonify(_jsonable(db.get_league_games(season['season_id'], day=day, team_key=team))), 200


@leagues_bp.route('/leagues/<league_id>/seasons/<int:season_number>/games/<int:game_index>', methods=['GET'])
@require_auth
@_json_errors
def get_season_game(league_id: str, season_number: int, game_index: int):
    """One game with its linescore and box scores."""
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id)
        game = db.get_league_game(context.season(db, season_number)['season_id'], game_index)
        if game is None:
            raise _ApiError('Game not found', 404)
        return jsonify(_jsonable(game)), 200


@leagues_bp.route('/leagues/<league_id>/seasons/run_it_back', methods=['POST'])
@require_auth
@_json_errors
def run_it_back(league_id: str):
    """Start the next season with the same teams: rosters, lineups and frozen cards carry over,
    straight to `setup`. (To redraft instead, start the next season's draft.)"""
    with PostgresDB() as db:
        context = _LeagueContext.load(db, league_id, require_commissioner=True)
        latest = db.get_league_season(league_id)
        if latest is None or latest['status'] != 'complete':
            raise _ApiError('Finish the current season first', 409)
        new_season_id = db.copy_league_season(
            league_id, latest['season_id'], latest['season_number'] + 1, seed=random.SystemRandom().getrandbits(62),
        )
        if new_season_id is None:
            raise _ApiError('The next season has already started', 409)
        return jsonify(_season_payload(context, db, context.season(db, latest['season_number'] + 1))), 201


@leagues_bp.route('/leagues/<league_id>/history', methods=['GET'])
@require_auth
@_json_errors
def league_history(league_id: str):
    """Every season, newest first: champion, awards, status."""
    with PostgresDB() as db:
        _LeagueContext.load(db, league_id)
        return jsonify(_jsonable(db.get_league_history(league_id))), 200
