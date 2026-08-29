import json
import random
import string
import threading
import traceback
from datetime import date, datetime, timedelta

from flask import Blueprint, g, jsonify, request

from ..core.card.sets import Set
from ..core.card.team_builder.player_filters import PlayerFilterSet
from ..core.card.team_builder.team import BULLPEN_ROLES, FIELD_POSITIONS, ROTATION_ROLES, Team as BuilderTeam
from ..core.database.postgres_db import PostgresDB
from ..core.simulation.mlb_game import MLBGameLineupSlot, MLBGameSetup, MLBGameSimulator, MLBGameTeamSetup
from ..core.simulation.models import GameStuckError, PostseasonFormat, PostseasonRound, SeasonSimulationConfig
from ..core.simulation.season import Season
from ..core.simulation.summary import SeasonSummaryBuilder
from ..core.simulation.takeover import TakeoverOptions
from .user_settings import optional_user_id, require_auth

sim_bp = Blueprint('sim', __name__)

# A season sim costs ~9s of CPU on top of ~15s of I/O. Gunicorn runs three sync workers, so
# letting these pile up would starve the request path. Two at a time per worker, and one
# in-flight job per user.
_MAX_CONCURRENT_SIMS = 2
_sim_slots = threading.BoundedSemaphore(_MAX_CONCURRENT_SIMS)


class SimCancelled(Exception):
    """Raised inside a `Season.simulate()` callback when the job's row has been cancelled out
    from under the worker thread. Propagates uncaught through `simulate()` to `_run_sim_job`."""

# Progress fires once per game - 2437 times a season. Writing each one would be thousands of
# round trips for a bar the user reads a few times a second.
_PROGRESS_WRITE_INTERVAL = timedelta(seconds=1)

_SEASONS_CACHE_TTL = timedelta(hours=12)
_seasons_cache: dict[str, tuple[list, datetime]] = {}

# Seasons the archive has full card coverage for. Before 1977 the card pool is Negro Leagues
# plus a 16-team MLB whose franchise relocations (BRO/BSN/NYG/PHA/SLB) are not mapped yet, so
# the schedule cannot be joined to cards - see Team.for_year.
_EARLIEST_SEASON = 1975


# ----------------------------------------------------------
# MARK: - SETUP OPTIONS
# ----------------------------------------------------------

@sim_bp.route('/sim/seasons', methods=['GET'])
def get_sim_seasons():
    """Seasons that can be simulated, newest first."""
    try:
        latest = datetime.now().year
        seasons = list(range(latest, _EARLIEST_SEASON - 1, -1))
        return jsonify({'seasons': seasons}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/seasons/<int:year>/teams', methods=['GET'])
def get_sim_season_teams(year: int):
    """Clubs available to take over that season, worst real record first."""
    try:
        cache_key = str(year)
        cached = _seasons_cache.get(cache_key)
        if cached and datetime.now() - cached[1] < _SEASONS_CACHE_TTL:
            return jsonify({'teams': cached[0], 'default': cached[0][0]['abbreviation'] if cached[0] else None}), 200

        options = TakeoverOptions(year=year)
        teams = [club.model_dump() for club in options.clubs]
        _seasons_cache[cache_key] = (teams, datetime.now())
        return jsonify({'teams': teams, 'default': options.default_abbr}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


# ----------------------------------------------------------
# MARK: - RUNNING A SIM
# ----------------------------------------------------------

def _roster_error(team: BuilderTeam) -> str | None:
    """Reject a roster the sim cannot field, before a job is ever queued.

    Mirrors the drafting thresholds the team list uses (`_compute_is_drafting`), but only the
    parts the simulation actually depends on: a full defensive alignment and at least one arm
    in each pitching role.
    """
    positions = {slot.roster_position.upper() for slot in team.roster}
    # DH IS OPTIONAL - WITHOUT ONE THE STARTING PITCHER TAKES THE NINTH SPOT INSTEAD.
    missing = [p for p in FIELD_POSITIONS if p != 'DH' and p not in positions]
    if missing:
        return f"Your team is missing a player at {', '.join(missing)}."
    if not any(p in ROTATION_ROLES for p in positions):
        return 'Your team needs at least one starting pitcher.'
    if not any(p in BULLPEN_ROLES for p in positions):
        return 'Your team needs at least one relief pitcher.'
    return None


@sim_bp.route('/sim/season', methods=['POST'])
@require_auth
def start_season_sim():
    """Queue a season takeover simulation. Returns a job id to poll."""
    try:
        payload = request.get_json(silent=True) or {}
        team_id = payload.get('team_id')
        if not team_id:
            return jsonify({'error': 'team_id is required'}), 400

        # A CHALLENGE INSTANCE IS THE SOURCE OF TRUTH FOR year/replaces/pts_limit WHEN PRESENT -
        # NEVER THE CLIENT-SUPPLIED year/replaces, SO A USER CAN'T LAUNCH A "SMALL BUDGET"
        # CHALLENGE WITH A TEAM THAT DOESN'T ACTUALLY FIT IT.
        challenge_instance_id = payload.get('challenge_instance_id')

        try:
            showdown_set = Set(str(payload.get('set') or '2000'))
        except ValueError:
            return jsonify({'error': f"unknown set '{payload.get('set')}'"}), 400

        with PostgresDB() as db:
            challenge = db.get_challenge_instance(challenge_instance_id) if challenge_instance_id else None
            if challenge_instance_id and (challenge is None or challenge['expires_at'] <= datetime.now()):
                return jsonify({'error': 'This challenge is no longer active.'}), 400

            if challenge is not None:
                year = challenge['year']
            else:
                try:
                    year = int(payload.get('year'))
                except (TypeError, ValueError):
                    return jsonify({'error': 'year is required'}), 400
            if year < _EARLIEST_SEASON:
                return jsonify({'error': f'Seasons before {_EARLIEST_SEASON} cannot be simulated yet.'}), 400

            row = db.get_team(team_id, g.user_id)
            if row is None:
                return jsonify({'error': 'team not found'}), 404
            # CAPTURED REGARDLESS OF WHETHER THIS IS A CHALLENGE RUN - POWERS THE WINS-PER-POINT
            # LEADERBOARD SORT FOR EVERY PLAYED SEASON.
            roster_points = row.get('total_points') or 0

            if challenge is not None and challenge['pts_limit'] is not None and roster_points > challenge['pts_limit']:
                return jsonify({
                    'error': f"This team costs {roster_points} pts, over the {challenge['pts_limit']} pt challenge limit.",
                }), 422

            # CHECKED AGAINST THE ROSTER'S ACTUAL CARDS, NEVER AGAINST team.player_filters - THAT
            # FIELD IS ONLY A PICKER/AUTOFILL DEFAULT AND IS FREELY USER-EDITABLE AFTER CREATION,
            # SO IT CANNOT BE TRUSTED AS PROOF THE ROSTER STILL COMPLIES.
            if challenge is not None and challenge.get('player_filters'):
                filter_set = PlayerFilterSet(filters=challenge['player_filters'])
                violation = next(
                    (reason for slot in row.get('roster', []) if (reason := filter_set.ineligible_reason(slot)) is not None),
                    None,
                )
                if violation:
                    return jsonify({
                        'error': f"This team doesn't meet the challenge's player requirements: {violation}.",
                    }), 422

            active = db.get_active_sim_job(g.user_id)
            if active:
                # THE BLOCKING JOB CAN BELONG TO A DIFFERENT TEAM - THE CAP IS PER-USER, NOT
                # PER-TEAM - SO THE CALLER NEEDS ITS OWN team_id TO LINK TO IT, NOT THIS ONE'S.
                return jsonify({
                    'error': 'You already have a simulation running. Wait for it to finish.',
                    'job_id': active['job_id'],
                    'team_id': active['team_id'],
                }), 429

        team = BuilderTeam.from_db_row(row)
        roster_error = _roster_error(team)
        if roster_error:
            return jsonify({'error': roster_error}), 422

        if challenge is not None:
            # RESOLVED AND VALIDATED ALREADY AT GENERATION TIME - NOT RE-DERIVED FROM ANYTHING
            # THE CLIENT SENT.
            replaces = challenge['replaces_abbr']
        else:
            # NO DB CONNECTION HELD HERE - THIS HITS THE MLB STATS API (UP TO ~90S WORST CASE WITH
            # RETRIES) AND MUST NOT SIT ON A POOLED CONNECTION WHILE IT DOES.
            try:
                replaces = TakeoverOptions(year=year).resolve(payload.get('replaces'))
            except ValueError as exc:
                return jsonify({'error': str(exc)}), 400
            if replaces is None:
                return jsonify({'error': f'No club data available for {year}.'}), 400

        config = SeasonSimulationConfig(
            year=year,
            set=showdown_set,
            simulate_postseason=True,
            seed=payload.get('seed'),
            takeover_team=team,
            takeover_replaces_abbr=replaces,
        )
        with PostgresDB() as db:
            job_id = db.create_sim_job(
                user_id=g.user_id,
                team_id=team_id,
                # THE BUILDER TEAM IS DROPPED FROM THE STORED CONFIG - IT IS A FULL ROSTER THE
                # TEAM ITSELF ALREADY HOLDS, AND ONLY THE SETUP ECHO IS NEEDED FOR DISPLAY.
                config={'year': year, 'set': showdown_set.value, 'replaces': replaces, 'seed': payload.get('seed'),
                        'team_name': team.name, 'team_abbreviation': team.abbreviation,
                        'challenge_instance_id': challenge['instance_id'] if challenge is not None else None},
            )

        if not _sim_slots.acquire(blocking=False):
            with PostgresDB() as db:
                db.finish_sim_job(job_id, error='The simulator is busy right now. Try again in a minute.')
            return jsonify({'error': 'The simulator is busy right now. Try again in a minute.'}), 429

        try:
            threading.Thread(
                target=_run_sim_job, args=(job_id, config, replaces, g.user_id, team_id),
                kwargs={'roster_points': roster_points, 'challenge': challenge},
                name=f'sim-{job_id[:8]}', daemon=True,
            ).start()
        except Exception:
            # THE WORKER RELEASES THE SLOT IN ITS OWN `finally`, SO IT IS ONLY OURS TO RELEASE
            # WHEN IT NEVER STARTED.
            _sim_slots.release()
            raise

        return jsonify({'job_id': job_id, 'status': 'queued', 'replaces': replaces}), 202

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


# GAMES_LIMIT BELOW THIS PRODUCES A SEASON SO SHORT THE STANDINGS/AWARDS SCREENS ARE MEANINGLESS.
_MIN_GAMES_LIMIT = 20
_MAX_INJURY_SEVERITY = 3.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _parse_engine_settings(payload: dict) -> dict:
    """Parses the engine settings shared by a solo open sim and a sim lobby's creation payload:
    year, set, postseason toggle/format, schedule length, injuries, and rest-of-season projection
    options. Raises ValueError (callers turn this into a 400) for anything malformed.

    Returns a dict with typed values (`showdown_set: Set`, `postseason_format: PostseasonFormat`,
    `resume_as_of_date: date | None`), NOT ready to hand to `SeasonSimulationConfig` directly -
    callers still need to add `year`/`set`/`takeovers`.
    """
    try:
        year = int(payload.get('year'))
    except (TypeError, ValueError):
        raise ValueError('year is required')
    if year < _EARLIEST_SEASON:
        raise ValueError(f'Seasons before {_EARLIEST_SEASON} cannot be simulated yet.')

    try:
        showdown_set = Set(str(payload.get('set') or '2000'))
    except ValueError:
        raise ValueError(f"unknown set '{payload.get('set')}'")

    try:
        postseason_format = PostseasonFormat(str(payload.get('postseason_format') or PostseasonFormat.DYNAMIC.value))
    except ValueError:
        raise ValueError(f"unknown postseason format '{payload.get('postseason_format')}'")

    games_limit = payload.get('games_limit')
    if games_limit is not None:
        try:
            games_limit = max(int(games_limit), _MIN_GAMES_LIMIT)
        except (TypeError, ValueError):
            raise ValueError('games_limit must be a number')

    pct_of_games = payload.get('pct_of_games')
    if pct_of_games is not None:
        try:
            pct_of_games = _clamp(float(pct_of_games), 0.05, 1.0)
        except (TypeError, ValueError):
            raise ValueError('pct_of_games must be a number')

    injury_severity_multiplier = _clamp(float(payload.get('injury_severity_multiplier') or 1.0), 0.0, _MAX_INJURY_SEVERITY)

    # REST-OF-SEASON PROJECTION. PRESENCE OF resume_as_of_date IS THE TOGGLE - AN EMPTY/NULL
    # VALUE MEANS A PLAIN FULL-SEASON SIM, THE DEFAULT.
    raw_resume_date = payload.get('resume_as_of_date')
    resume_from_real_season = bool(raw_resume_date)
    resume_as_of_date = None
    if raw_resume_date:
        try:
            resume_as_of_date = date.fromisoformat(str(raw_resume_date))
        except ValueError:
            raise ValueError(f"invalid resume_as_of_date '{raw_resume_date}' - use YYYY-MM-DD")

    # ONLY MEANINGFUL ALONGSIDE resume_as_of_date - THE ENGINE ITSELF GATES ON BOTH
    # (`config.resume_from_real_season and config.merge_real_stats`), SO A STRAY
    # merge_real_stats=True WITH NO RESUME DATE IS SILENTLY A NO-OP RATHER THAN AN ERROR.
    merge_real_stats = resume_from_real_season and bool(payload.get('merge_real_stats'))

    return {
        'year': year, 'showdown_set': showdown_set, 'postseason_format': postseason_format,
        'games_limit': games_limit, 'pct_of_games': pct_of_games,
        'enable_injuries': bool(payload.get('enable_injuries')),
        'injury_severity_multiplier': injury_severity_multiplier,
        'seed': payload.get('seed'), 'simulate_postseason': payload.get('simulate_postseason', True),
        'resume_from_real_season': resume_from_real_season, 'resume_as_of_date': resume_as_of_date,
        'merge_real_stats': merge_real_stats,
    }


def _settings_to_stored_config(settings: dict) -> dict:
    """JSON-serializable echo of `_parse_engine_settings`'s output, storable on `sim_lobby.config`
    - the inverse of `_config_kwargs_from_stored`, which rebuilds a `SeasonSimulationConfig` from
    this at start time. `year`/`showdown_set` are dropped since `sim_lobby` already carries them
    as their own columns.
    """
    return {
        'seed': settings['seed'], 'games_limit': settings['games_limit'], 'pct_of_games': settings['pct_of_games'],
        'enable_injuries': settings['enable_injuries'], 'injury_severity_multiplier': settings['injury_severity_multiplier'],
        'simulate_postseason': settings['simulate_postseason'], 'postseason_format': settings['postseason_format'].value,
        'resume_from_real_season': settings['resume_from_real_season'],
        'resume_as_of_date': settings['resume_as_of_date'].isoformat() if settings['resume_as_of_date'] else None,
        'merge_real_stats': settings['merge_real_stats'],
    }


def _config_kwargs_from_stored(stored: dict) -> dict:
    """Inverse of `_settings_to_stored_config` - rebuilds `SeasonSimulationConfig` kwargs (minus
    `year`/`set`/`takeovers`, which the caller supplies separately) from a lobby's stored config."""
    resume_as_of_date = date.fromisoformat(stored['resume_as_of_date']) if stored.get('resume_as_of_date') else None
    return {
        'seed': stored.get('seed'), 'games_limit': stored.get('games_limit'), 'pct_of_games': stored.get('pct_of_games'),
        'enable_injuries': bool(stored.get('enable_injuries')),
        'injury_severity_multiplier': stored.get('injury_severity_multiplier', 1.0),
        'simulate_postseason': stored.get('simulate_postseason', True),
        'postseason_format': PostseasonFormat(stored.get('postseason_format', PostseasonFormat.DYNAMIC.value)),
        'resume_from_real_season': bool(stored.get('resume_from_real_season')),
        'resume_as_of_date': resume_as_of_date,
        'merge_real_stats': bool(stored.get('merge_real_stats')),
    }


def _launch_open_sim_job(
    user_id: str, config: SeasonSimulationConfig, focus_abbr: str | None, job_config_echo: dict,
) -> tuple[str | None, tuple[dict, int] | None]:
    """Creates the `sim_job` row and starts the worker thread - the shared tail of a solo open sim
    and a lobby's start, once each has its own `SeasonSimulationConfig` ready.

    Returns `(job_id, None)` on success, or `(None, (json_body, status_code))` on failure (the
    simulator is at capacity) - the caller re-raises that as its own response.
    """
    with PostgresDB() as db:
        job_id = db.create_sim_job(user_id=user_id, team_id=None, config=job_config_echo)

    if not _sim_slots.acquire(blocking=False):
        with PostgresDB() as db:
            db.finish_sim_job(job_id, error='The simulator is busy right now. Try again in a minute.')
        return None, ({'error': 'The simulator is busy right now. Try again in a minute.'}, 429)

    try:
        threading.Thread(
            target=_run_sim_job, args=(job_id, config, focus_abbr, user_id, None),
            name=f'sim-{job_id[:8]}', daemon=True,
        ).start()
    except Exception:
        # THE WORKER RELEASES THE SLOT IN ITS OWN `finally`, SO IT IS ONLY OURS TO RELEASE
        # WHEN IT NEVER STARTED.
        _sim_slots.release()
        raise

    return job_id, None


class _RequestError(Exception):
    """A validation failure that already knows its HTTP status - lets a helper called from
    several routes raise the right status code without the caller having to guess from message
    text. Callers catch this and `return jsonify({'error': str(exc)}), exc.status`.
    """
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _resolve_takeovers(raw_takeovers: list, requester_user_id: str, db: PostgresDB) -> list[tuple[BuilderTeam, str | None]]:
    """Validates ownership/roster completeness for each `{team_id, replaces}` entry (DB-bound,
    called with a connection already open). Returns `(team, requested_replaces)` rows - resolving
    `replaces` against the real season is an external MLB Stats API call that must NOT happen
    while holding a DB connection, so that step is left to the caller. Raises `_RequestError`
    with the appropriate status on any validation failure.
    """
    rows: list[tuple[BuilderTeam, str | None]] = []
    for entry in raw_takeovers:
        if not isinstance(entry, dict) or not entry.get('team_id'):
            raise _RequestError('each takeover needs a team_id', 400)
        row = db.get_team(entry['team_id'], requester_user_id)
        if row is None:
            raise _RequestError(f"team {entry['team_id']} not found", 404)
        team = BuilderTeam.from_db_row(row)
        roster_error = _roster_error(team)
        if roster_error:
            raise _RequestError(f"{team.name}: {roster_error}", 422)
        rows.append((team, entry.get('replaces')))
    return rows


@sim_bp.route('/sim/open_season', methods=['POST'])
@require_auth
def start_open_sim():
    """Queue an open sim: every club plays a season, with any number of clubs optionally taken
    over by one of the caller's own teams. Returns a job id to poll.

    Deliberately separate from `start_season_sim` - that route's challenge-instance, pts-budget
    and `PlayerFilterSet` validation belongs to a Team Challenge run and does not apply here.
    """
    try:
        payload = request.get_json(silent=True) or {}

        try:
            settings = _parse_engine_settings(payload)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        year, showdown_set = settings['year'], settings['showdown_set']

        raw_takeovers = payload.get('takeovers') or []
        if not isinstance(raw_takeovers, list):
            return jsonify({'error': 'takeovers must be a list'}), 400

        # DB-BOUND CHECKS FIRST, IN ONE SHORT-LIVED CONNECTION: THE PER-USER CAP, PLUS OWNERSHIP
        # AND ROSTER VALIDATION FOR EACH REQUESTED TAKEOVER (MIRRORING `start_season_sim`'s
        # SINGLE-TEAM CHECKS - NO PTS-BUDGET OR PlayerFilterSet CHECK, THOSE ARE CHALLENGE-ONLY).
        with PostgresDB() as db:
            active = db.get_active_sim_job(g.user_id)
            if active:
                return jsonify({
                    'error': 'You already have a simulation running. Wait for it to finish.',
                    'job_id': active['job_id'],
                    'team_id': active['team_id'],
                }), 429

            try:
                takeover_rows = _resolve_takeovers(raw_takeovers, g.user_id, db)
            except _RequestError as exc:
                return jsonify({'error': str(exc)}), exc.status

        # NO DB CONNECTION HELD DURING ANY OF THIS - EACH `TakeoverOptions` HITS THE MLB STATS API
        # (UP TO ~90S WORST CASE WITH RETRIES) AND MUST NOT SIT ON A POOLED CONNECTION WHILE IT
        # DOES. RESULTS ARE 12H-CACHED PER YEAR AT THE ROUTE LAYER, SO REPEAT REQUESTS ARE CHEAP.
        try:
            options = TakeoverOptions(year=year)
            takeover_teams: dict[str, BuilderTeam] = {}
            for team, requested_replaces in takeover_rows:
                replaces = options.resolve(requested_replaces)
                if replaces is None:
                    return jsonify({'error': f'No club data available for {year}.'}), 400
                if replaces in takeover_teams:
                    return jsonify({'error': f"'{replaces}' is being taken over more than once."}), 400
                takeover_teams[replaces] = team

            focus_abbr = payload.get('focus_abbr')
            if focus_abbr:
                focus_abbr = options.resolve(focus_abbr)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400

        config = SeasonSimulationConfig(
            year=year,
            set=showdown_set,
            takeovers=takeover_teams,
            **_config_kwargs_from_stored(_settings_to_stored_config(settings)),
            # NEVER ACCEPTED FROM THE CLIENT - 3.2 MB OF THE 6.1 MB RESULT, AND NOTHING ON THE
            # OPEN-SIM RESULT SCREEN READS THEM. SEE `start_season_sim`'s SAME OMISSION.
            include_game_logs=False,
            include_box_scores=False,
        )

        job_id, error = _launch_open_sim_job(
            user_id=g.user_id, config=config, focus_abbr=focus_abbr,
            # BUILDER TEAMS ARE DROPPED FROM THE STORED CONFIG - EACH IS A FULL ROSTER THE TEAM
            # ITSELF ALREADY HOLDS, AND ONLY THE SETUP ECHO IS NEEDED FOR DISPLAY.
            job_config_echo={
                'year': year, 'set': showdown_set.value, 'focus_abbr': focus_abbr,
                'takeovers': [{'replaces': abbr, 'team_name': team.name} for abbr, team in takeover_teams.items()],
                **_settings_to_stored_config(settings),
            },
        )
        if error:
            body, status = error
            return jsonify(body), status

        return jsonify({'job_id': job_id, 'status': 'queued', 'focus_abbr': focus_abbr}), 202

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


# ----------------------------------------------------------
# MARK: - SIM LOBBY (MULTIPLAYER)
# ----------------------------------------------------------
#
# Several users share one simulated season: each member follows a real club or takes it over with
# a team they built, the host starts it, and everyone reads the same result from their own club's
# perspective via `useClubSeason` on the frontend - no per-member sim runs, no per-member result
# rows. This is almost entirely lobby lifecycle around the open-sim machinery above, not new
# simulation logic. See `Season._build_season_teams`'s `all_takeovers` loop for how N takeovers in
# one run were already made to work before this existed.

# EXCLUDES VISUALLY AMBIGUOUS CHARACTERS (0/O, 1/I) SINCE A JOIN CODE IS READ ALOUD/TYPED BY HAND.
_JOIN_CODE_ALPHABET = ''.join(c for c in string.ascii_uppercase + string.digits if c not in 'O0I1')
_JOIN_CODE_LENGTH = 6


def _generate_unique_join_code(db: PostgresDB, attempts: int = 5) -> str:
    for _ in range(attempts):
        code = ''.join(random.choices(_JOIN_CODE_ALPHABET, k=_JOIN_CODE_LENGTH))
        if db.get_sim_lobby_by_code(code) is None:
            return code
    # ASTRONOMICALLY UNLIKELY AT ~30^6 COMBINATIONS - THIS IS A CIRCUIT BREAKER, NOT A REAL PATH.
    raise _RequestError('Could not generate a join code. Try again.', 500)


def _lobby_state_payload(db: PostgresDB, lobby: dict) -> dict:
    """Shared `{lobby, members, job}` response shape for the create/join/claim/leave/get routes.

    Lazily reconciles a 'running' lobby with its underlying `sim_job`: the worker thread that
    actually runs the sim has no idea it's running for a lobby (it just sees a job id), so this is
    the only place that link is ever followed. `sim_job` is owner-scoped to the host (whoever
    pressed start - see the "Job ownership" note on `/start` below), so the lookup must pass the
    host's id explicitly rather than the viewer's, or a non-host member would never see it resolve.
    """
    job = None
    if lobby['status'] == 'running' and lobby['job_id']:
        job = db.get_sim_job(lobby['job_id'], user_id=lobby['host_user_id'])
        if job and job['status'] in ('succeeded', 'failed', 'cancelled'):
            db.finish_sim_lobby(lobby['lobby_id'])
            lobby['status'] = 'finished'
    members = db.get_sim_lobby_members(lobby['lobby_id'])
    return {'lobby': lobby, 'members': members, 'job': job}


@sim_bp.route('/sim/lobby', methods=['POST'])
@require_auth
def create_sim_lobby():
    """Create a new open sim lobby other users can join by code. The host's engine settings
    (year, set, schedule length, injuries, rest-of-season projection, ...) are fixed at creation -
    the same options a solo open sim's setup form collects. Which clubs get taken over, and by
    whom, is decided by member claims later, at start time."""
    try:
        payload = request.get_json(silent=True) or {}
        try:
            settings = _parse_engine_settings(payload)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400

        with PostgresDB() as db:
            try:
                join_code = _generate_unique_join_code(db)
            except _RequestError as exc:
                return jsonify({'error': str(exc)}), exc.status
            lobby_id = db.create_sim_lobby(
                host_user_id=g.user_id, join_code=join_code, year=settings['year'],
                showdown_set=settings['showdown_set'].value, config=_settings_to_stored_config(settings),
            )
            lobby = db.get_sim_lobby(lobby_id)

        return jsonify(_lobby_state_payload(db, lobby)), 201

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/lobby/<code>/join', methods=['POST'])
def join_sim_lobby(code: str):
    """Resolves a join code to a lobby's current state. Doesn't create membership itself - claiming
    a club (`POST /sim/lobby/<id>/claim`) is the actual join action, so this works even signed out,
    same as browsing a challenge before deciding to take it on."""
    try:
        with PostgresDB() as db:
            lobby = db.get_sim_lobby_by_code(code.strip().upper())
            if lobby is None:
                return jsonify({'error': 'Lobby not found or expired.'}), 404
            return jsonify(_lobby_state_payload(db, lobby)), 200

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/lobby/<lobby_id>', methods=['GET'])
def get_sim_lobby(lobby_id: str):
    """Current lobby state - polled by every member's client (~2s) while waiting/running, the
    lobby's equivalent of a solo sim's job-progress poll."""
    try:
        with PostgresDB() as db:
            lobby = db.get_sim_lobby(lobby_id)
            if lobby is None:
                return jsonify({'error': 'Lobby not found or expired.'}), 404
            return jsonify(_lobby_state_payload(db, lobby)), 200

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/lobby/<lobby_id>/claim', methods=['POST'])
@require_auth
def claim_sim_lobby(lobby_id: str):
    """Claim (or change) a club in an open lobby - optionally with one of the caller's own teams
    (a takeover) or none (follow only). Re-validated for real at start time (roster completeness
    can drift after claiming, and the lobby can fill up around a slow claimant), so this is a
    best-effort check, not the final word."""
    try:
        payload = request.get_json(silent=True) or {}
        club_abbr = payload.get('club_abbr')
        if not club_abbr:
            return jsonify({'error': 'club_abbr is required'}), 400
        team_id = payload.get('team_id') or None

        with PostgresDB() as db:
            lobby = db.get_sim_lobby(lobby_id)
            if lobby is None:
                return jsonify({'error': 'Lobby not found or expired.'}), 404
            if lobby['status'] != 'open':
                return jsonify({'error': f"This lobby is {lobby['status']} and no longer accepting claims."}), 400

            if team_id:
                row = db.get_team(team_id, g.user_id)
                if row is None:
                    return jsonify({'error': 'team not found'}), 404
                team = BuilderTeam.from_db_row(row)
                roster_error = _roster_error(team)
                if roster_error:
                    return jsonify({'error': roster_error}), 422

        # NO DB CONNECTION HELD - SAME REASONING AS start_open_sim's TakeoverOptions CALL.
        try:
            resolved_abbr = TakeoverOptions(year=lobby['year']).resolve(club_abbr)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        if resolved_abbr is None:
            return jsonify({'error': f"No club data available for {lobby['year']}."}), 400

        with PostgresDB() as db:
            claimed = db.claim_sim_lobby_club(lobby_id, g.user_id, resolved_abbr, team_id)
            if not claimed:
                return jsonify({'error': f"'{resolved_abbr}' is already claimed by another player."}), 409
            lobby = db.get_sim_lobby(lobby_id)
            return jsonify(_lobby_state_payload(db, lobby)), 200

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/lobby/<lobby_id>/leave', methods=['POST'])
@require_auth
def leave_sim_lobby(lobby_id: str):
    """Drop the caller's own claim. The host can't leave their own lobby - there's no route to
    transfer or delete it, so that would strand it in a state nobody can ever start."""
    try:
        with PostgresDB() as db:
            lobby = db.get_sim_lobby(lobby_id)
            if lobby is None:
                return jsonify({'error': 'Lobby not found or expired.'}), 404
            if lobby['host_user_id'] == g.user_id:
                return jsonify({'error': "The host can't leave their own lobby."}), 400
            db.leave_sim_lobby(lobby_id, g.user_id)
            return jsonify(_lobby_state_payload(db, lobby)), 200

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/lobby/<lobby_id>/start', methods=['POST'])
@require_auth
def start_sim_lobby(lobby_id: str):
    """Host-only: build `takeovers` from every member's claim, launch the sim, and record which
    job the lobby is now watching.

    Job ownership: the job is created under the HOST's `user_id`, exactly like a solo open sim -
    so the per-user concurrency cap (`get_active_sim_job`) applies to the host for the run's
    duration, and every other member keeps their own independent cap untouched. A host who tries
    to start a personal sim while their lobby sim is running gets the same `SimAlreadyRunningError`
    → "view existing" path a solo run's cap already provides, for free.
    """
    try:
        with PostgresDB() as db:
            lobby = db.get_sim_lobby(lobby_id)
            if lobby is None:
                return jsonify({'error': 'Lobby not found or expired.'}), 404
            if lobby['host_user_id'] != g.user_id:
                return jsonify({'error': 'Only the host can start this lobby.'}), 403
            if lobby['status'] != 'open':
                return jsonify({'error': f"This lobby is already {lobby['status']}."}), 400

            active = db.get_active_sim_job(g.user_id)
            if active:
                return jsonify({
                    'error': 'You already have a simulation running. Wait for it to finish.',
                    'job_id': active['job_id'], 'team_id': active['team_id'],
                }), 429

            # RE-VALIDATED HERE, NOT JUST AT CLAIM TIME - A MEMBER'S TEAM CAN CHANGE (OR THE TEAM
            # ITSELF DISAPPEAR) BETWEEN CLAIMING AND THE HOST PRESSING START.
            members = db.get_sim_lobby_members(lobby_id)
            takeover_teams: dict[str, BuilderTeam] = {}
            for member in members:
                if not member['team_id']:
                    continue
                row = db.get_team(member['team_id'], member['user_id'])
                if row is None:
                    return jsonify({'error': f"{member['club_abbr']}'s team is no longer available."}), 422
                team = BuilderTeam.from_db_row(row)
                roster_error = _roster_error(team)
                if roster_error:
                    return jsonify({'error': f"{member['club_abbr']} ({team.name}): {roster_error}"}), 422
                takeover_teams[member['club_abbr']] = team

        config = SeasonSimulationConfig(
            year=lobby['year'],
            set=Set(lobby['showdown_set']),
            takeovers=takeover_teams,
            **_config_kwargs_from_stored(lobby['config'] or {}),
            include_game_logs=False,
            include_box_scores=False,
        )

        job_id, error = _launch_open_sim_job(
            user_id=g.user_id, config=config, focus_abbr=None,
            job_config_echo={
                'year': lobby['year'], 'set': lobby['showdown_set'], 'lobby_id': lobby_id,
                'takeovers': [{'replaces': abbr, 'team_name': team.name} for abbr, team in takeover_teams.items()],
                **(lobby['config'] or {}),
            },
        )
        if error:
            body, status = error
            return jsonify(body), status

        with PostgresDB() as db:
            db.set_sim_lobby_running(lobby_id, job_id)
            lobby = db.get_sim_lobby(lobby_id)
            return jsonify(_lobby_state_payload(db, lobby)), 202

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


def _friendly_phase(message: str) -> str | None:
    """Coarse user-facing stage for a `status_callback` message.

    The engine emits setup milestones and per-team roster warnings ("STL: 7 man(s) short of a
    40-man roster") down the same channel. Warnings are useful in the CLI but are noise in a
    progress bar, so anything unrecognized returns None and leaves the phase as it was.
    """
    text = message.lower()
    if 'postseason' in text:
        return 'Simulating the postseason'
    if text.startswith('simulating'):
        return 'Simulating games'
    if text.startswith('replacing'):
        return 'Setting up teams'
    if 'schedule' in text:
        return 'Building the schedule'
    if 'card' in text or 'player pool' in text:
        return 'Loading players'
    # PER-TEAM WARNINGS ALSO MENTION "ROSTER" - THEY ARE NOT A STAGE.
    if 'roster' in text and 'short' not in text:
        return 'Setting up teams'
    return None


def _challenge_passed(goal_type: str, goal_value: dict | None, team_season, won_pennant: bool) -> bool:
    """Evaluate a challenge's goal against the played season's result."""
    if goal_type == 'made_playoffs':
        return team_season.made_playoffs
    if goal_type == 'win_pennant':
        return won_pennant
    if goal_type == 'win_world_series':
        return team_season.is_champion
    if goal_type == 'min_wins':
        return team_season.wins >= (goal_value or {}).get('min_wins', 0)
    return False


def _run_sim_job(
    job_id: str, config: SeasonSimulationConfig, team_abbr: str | None, user_id: str | None = None, team_id: str | None = None,
    roster_points: int | None = None, challenge: dict | None = None,
) -> None:
    """Run one simulation to completion and record the result.

    Runs in a background thread with its own DB connections - it must never share the one the
    request used, and the progress writer needs one separate from the simulation's own reads.

    `team_abbr=None` is an open sim: `SeasonSummaryBuilder` covers every club instead of one, and
    `team_id`/`challenge`/`roster_points` are all naturally None/absent for this kind of run - a
    challenge is by definition scoped to one team's own attempt.
    """
    try:
        last_write = datetime.min

        def write_progress(phase: str | None = None, completed: int | None = None, total: int | None = None) -> None:
            try:
                with PostgresDB() as progress_db:
                    still_active = progress_db.update_sim_job_progress(job_id, phase=phase, games_completed=completed, games_total=total)
            except Exception:
                return  # PROGRESS IS COSMETIC - A WRITE FAILURE MUST NEVER KILL THE RUN
            # THE CANCELLATION CHECK MUST STAY OUTSIDE THE try/except ABOVE, OR THE BARE
            # `except Exception` WOULD SWALLOW THE RAISE AND CANCELLATION WOULD NEVER FIRE.
            if not still_active:
                raise SimCancelled()

        def on_progress(completed: int, total: int) -> None:
            nonlocal last_write
            now = datetime.now()
            if completed < total and now - last_write < _PROGRESS_WRITE_INTERVAL:
                return
            last_write = now
            write_progress(completed=completed, total=total)

        def on_status(message: str) -> None:
            phase = _friendly_phase(message)
            if phase:
                write_progress(phase=phase)

        write_progress(phase='Starting simulation')
        # `log_callback` STAYS UNSET: IT FIRES PER PLATE APPEARANCE (~185k TIMES) AND FORCES
        # GameLogEntry CONSTRUCTION EVEN WHEN THE LOG IS NEVER COLLECTED.
        result = Season(config=config).simulate(progress_callback=on_progress, status_callback=on_status)

        with PostgresDB() as check_db:
            # POSTSEASON HAS NO CALLBACK OF ITS OWN, SO A CANCEL DURING IT ONLY SURFACES HERE -
            # WITHOUT THIS, A CANCELLED RUN COULD STILL GET PERMANENTLY RECORDED BELOW.
            if check_db.is_sim_job_cancelled(job_id):
                return

        write_progress(phase='Building results')
        summary = SeasonSummaryBuilder(result=result, team_abbr=team_abbr).build()
        # DROP THE ~6 MB RESULT BEFORE THE WRITE - ONLY THE PROJECTION IS PERSISTED.
        del result

        challenge_result = None
        won_pennant = None
        if challenge is not None:
            won_pennant = any(
                series.round == PostseasonRound.CHAMPIONSHIP.value and series.winner == team_abbr
                for series in summary.postseason
            )
            passed = _challenge_passed(challenge['goal_type'], challenge['goal_value'], summary.team, won_pennant)
            challenge_result = 'passed' if passed else 'failed'

        payload = summary.model_dump(mode='json')
        with PostgresDB() as db:
            # The permanent record - written before the job is marked done, so a client that
            # sees "succeeded" can always find the season it points to. Unlike the old
            # leaderboard-only write, this is no longer best-effort: it is now the only place
            # the result is stored at all, so a failure here must fail the job, not just log.
            db.record_sim_season(
                job_id=job_id, user_id=user_id, team_id=team_id,
                team=config.takeover_team.model_dump(mode='json') if config.takeover_team else {},
                summary=payload,
                challenge_instance_id=challenge['instance_id'] if challenge is not None else None,
                challenge_result=challenge_result,
                won_pennant=won_pennant,
                roster_points=roster_points,
            )
            db.finish_sim_job(job_id)

    except SimCancelled:
        pass  # THE ROW IS ALREADY TERMINAL ('cancelled') - finish_sim_job WOULD BE A NO-OP
    except GameStuckError as exc:
        # A GAME THAT COULD NOT END. WITHOUT THIS GUARD THE WORKER WOULD SPIN UNTIL THE STALE-JOB
        # REAPER KILLED IT WITH A GENERIC "STOPPED RESPONDING". `exc.context` IS THE STRUCTURED
        # GAME STATE - LOGGED HERE, AND FOLDED INTO THE STORED ERROR SO THE JOB ROW EXPLAINS ITSELF.
        traceback.print_exc()
        print(f"sim job {job_id} stuck game context: {json.dumps(exc.context, default=str)}")
        try:
            with PostgresDB() as db:
                db.finish_sim_job(job_id, error=str(exc), error_context=exc.context)
        except Exception:
            traceback.print_exc()
    except Exception as exc:
        traceback.print_exc()
        try:
            with PostgresDB() as db:
                db.finish_sim_job(job_id, error=str(exc))
        except Exception:
            traceback.print_exc()
    finally:
        _sim_slots.release()


# ----------------------------------------------------------
# MARK: - POLLING
# ----------------------------------------------------------

@sim_bp.route('/sim/challenges', methods=['GET'])
def get_challenges():
    """Active challenge instances, joined to their template.

    Unauthenticated callers just see the list; a signed-in caller also gets their own best
    attempt (if any) at each instance.
    """
    try:
        user_id = optional_user_id()
        with PostgresDB() as db:
            challenges = db.fetch_active_challenges(user_id=user_id)
        return jsonify({'challenges': challenges}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/challenges/<instance_id>', methods=['GET'])
def get_challenge_instance_route(instance_id):
    """A single challenge instance, active or expired - the shareable, direct-link page for one
    challenge. Unlike `/sim/challenges`, this resolves regardless of expiration, so a link shared
    while an instance was live still explains itself after it rotates out.
    """
    try:
        user_id = optional_user_id()
        with PostgresDB() as db:
            instance = db.get_challenge_instance(instance_id, user_id=user_id)
        if not instance:
            return jsonify({'error': 'Challenge not found.'}), 404
        return jsonify({'challenge': instance}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/challenges/<instance_id>/eligible_teams', methods=['GET'])
@require_auth
def get_eligible_teams(instance_id):
    """Which of the caller's own teams could be used for this challenge right now - the same
    budget/drafting/player_filters checks `start_season_sim` enforces at launch, run ahead of time
    so the "use an existing team" picker doesn't offer a team that would just fail at launch.

    The full roster check (via `PlayerFilterSet`) only runs when the challenge actually restricts
    players, and only against teams that already clear the cheap budget/drafting filter - keeps
    this a handful of extra queries at most, not one per team the caller owns.
    """
    try:
        with PostgresDB() as db:
            challenge = db.get_challenge_instance(instance_id)
            if not challenge or challenge['expires_at'] <= datetime.now():
                return jsonify({'error': 'This challenge is no longer active.'}), 400

            candidates = [
                t for t in db.get_user_teams(g.user_id)
                if not t['is_drafting'] and (challenge['pts_limit'] is None or t['total_points'] <= challenge['pts_limit'])
            ]

            player_filters = challenge.get('player_filters')
            if not player_filters:
                return jsonify({'team_ids': [t['team_id'] for t in candidates]}), 200

            filter_set = PlayerFilterSet(filters=player_filters)
            eligible_ids = []
            for candidate in candidates:
                row = db.get_team(candidate['team_id'], g.user_id)
                if row and all(filter_set.matches(slot) for slot in row.get('roster', [])):
                    eligible_ids.append(candidate['team_id'])
        return jsonify({'team_ids': eligible_ids}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/leaderboard', methods=['GET'])
def get_sim_leaderboard():
    """Played seasons ranked by wins, split into groups within each season - one group for
    open-play runs, plus one group per challenge instance played that year - newest season first.
    Each group ranks its own entries independently, since comparing wins across different
    budgets/goals wouldn't mean anything.

    Unauthenticated callers see public teams only; a signed-in user additionally sees their own
    private results and has their rows flagged.
    """
    try:
        user_id = optional_user_id()
        year = request.args.get('year', type=int)
        limit = min(request.args.get('limit', default=25, type=int), 100)
        sort = request.args.get('sort', default='wins')

        rows = []
        with PostgresDB() as db:
            rows = db.fetch_sim_leaderboard(user_id=user_id, year=year, per_season_limit=limit, sort=sort)

        # Rows arrive ordered by (year DESC, open-play-first, challenge_title ASC, rank ASC), so
        # seasons and their groups both fall out in a single pass.
        seasons: list[dict] = []
        for row in rows:
            if not seasons or seasons[-1]['year'] != row['year']:
                seasons.append({'year': row['year'], 'has_own_entry': False, 'groups': []})
            season = seasons[-1]

            group_id = row['challenge_instance_id']
            groups = season['groups']
            if not groups or groups[-1]['challenge_instance_id'] != group_id:
                groups.append({
                    'challenge_instance_id': group_id,
                    'challenge_title': row.pop('challenge_title'),
                    'challenge_slug': row.pop('challenge_slug'),
                    'entries': [],
                })
            else:
                row.pop('challenge_title', None)
                row.pop('challenge_slug', None)
            groups[-1]['entries'].append(row)

            if row.get('is_own'):
                season['has_own_entry'] = True

        return jsonify({'seasons': seasons}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/history', methods=['GET'])
@require_auth
def get_sim_history():
    """The signed-in user's own played seasons, newest first - every run, not just the best."""
    try:
        limit = min(request.args.get('limit', default=100, type=int), 200)
        team_id = request.args.get('team_id')
        with PostgresDB() as db:
            seasons = db.fetch_user_sim_seasons(g.user_id, limit=limit, team_id=team_id)
        return jsonify({'seasons': seasons}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/teams/<team_id>/seasons', methods=['GET'])
def get_team_sim_seasons(team_id: str):
    """Every season played with this team, newest first, regardless of who ran it.

    A public team can be simulated by any signed-in user, not just its owner, so this can span
    multiple users. Unauthenticated callers see it when the team is public; the owner always can.
    """
    try:
        user_id = optional_user_id()
        limit = min(request.args.get('limit', default=10, type=int), 50)
        with PostgresDB() as db:
            seasons = db.fetch_team_sim_seasons(team_id, viewer_user_id=user_id, limit=limit)
        return jsonify({'seasons': seasons}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


# ----------------------------------------------------------
# MARK: - SIMULATING A REAL MLB GAME
# ----------------------------------------------------------

# The setup is a few seconds of MLB API calls plus a card lookup, and every viewer of the same
# game wants the identical answer. Short-lived because a live game's state moves constantly.
_GAME_SETUP_CACHE_TTL = timedelta(seconds=20)
_game_setup_cache: dict[str, tuple[dict, datetime]] = {}


def _game_setup(game_pk: int, showdown_set: Set) -> dict:
    """Cached `MLBGameSetup` payload for a game.

    A finished or not-yet-started game is stable, so it caches cleanly. A live game's start state
    changes with every pitch, but a 20 second window is well inside the ~30s the game page itself
    polls at, and a takeover always re-reads the live state at simulate time anyway.
    """

    cache_key = f"{game_pk}:{showdown_set.value}"
    cached = _game_setup_cache.get(cache_key)
    if cached and datetime.now() - cached[1] < _GAME_SETUP_CACHE_TTL:
        return cached[0]

    setup = MLBGameSimulator(game_pk=game_pk, showdown_set=showdown_set).build_setup()
    payload = setup.model_dump(mode='json')
    _game_setup_cache[cache_key] = (payload, datetime.now())
    return payload


@sim_bp.route('/sim/game/<int:game_pk>/setup', methods=['GET'])
def get_sim_game_setup(game_pk: int):
    """The lineups, rosters and (for a game in progress) mid-game state a simulation would use.

    Returned before anything is simulated so the client can show - and let the user edit - the
    lineup it is about to commit to.
    """
    try:
        try:
            showdown_set = Set(str(request.args.get('set') or '2000'))
        except ValueError:
            return jsonify({'error': f"unknown set '{request.args.get('set')}'"}), 400

        return jsonify(_game_setup(game_pk, showdown_set)), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


def _apply_lineup_overrides(setup: MLBGameSetup, payload: dict) -> None:
    """Replace a side's lineup and starter with the client's edits.

    Only ids are trusted from the client: the batting order and field position come from the
    request, but every player must already be in the setup's own pool, so a request can rearrange
    a game's participants and never invent one.
    """

    for side in ('away', 'home'):
        override = payload.get(side)
        if not isinstance(override, dict):
            continue
        team: MLBGameTeamSetup = getattr(setup, side)
        known = {option.player_id: option for option in team.position_players}

        lineup = override.get('lineup')
        if isinstance(lineup, list) and lineup:
            slots = []
            for order, entry in enumerate(lineup[:9], start=1):
                player_id = str(entry.get('player_id') if isinstance(entry, dict) else entry)
                option = known.get(player_id)
                if option is None:
                    raise ValueError(f"'{player_id}' is not available to {team.identity.abbreviation}.")
                position = (entry.get('position') if isinstance(entry, dict) else None) or option.position
                slots.append(MLBGameLineupSlot(
                    batting_order=order, player_id=player_id, name=option.name, position=position,
                ))
            if len(slots) != 9:
                raise ValueError(f"{team.identity.abbreviation} needs 9 batters, got {len(slots)}.")
            team.lineup = slots

        starter_id = override.get('starting_pitcher_id')
        if starter_id:
            starter_id = str(starter_id)
            if starter_id not in {option.player_id for option in team.bullpen}:
                raise ValueError(f"'{starter_id}' is not a pitcher available to {team.identity.abbreviation}.")
            team.starting_pitcher_id = starter_id


@sim_bp.route('/sim/game/<int:game_pk>', methods=['POST'])
@require_auth
def start_game_sim(game_pk: int):
    """Simulate one real MLB game and store the result.

    Synchronous, unlike a season sim: a single game is a few hundred plate appearances and runs in
    milliseconds. The `_sim_slots` semaphore is still held for the duration so a burst of these
    can't starve the season worker or the request path.
    """
    try:
        payload = request.get_json(silent=True) or {}

        try:
            showdown_set = Set(str(payload.get('set') or '2000'))
        except ValueError:
            return jsonify({'error': f"unknown set '{payload.get('set')}'"}), 400

        seed = payload.get('seed')
        if seed is not None:
            try:
                seed = int(seed)
            except (TypeError, ValueError):
                return jsonify({'error': 'seed must be an integer'}), 400

        if not _sim_slots.acquire(blocking=False):
            return jsonify({'error': 'The simulator is busy right now. Try again in a minute.'}), 429

        try:
            simulator = MLBGameSimulator(game_pk=game_pk, showdown_set=showdown_set)
            setup = simulator.build_setup()
            if setup.is_final:
                return jsonify({'error': 'This game is already over - there is nothing left to simulate.'}), 400

            try:
                _apply_lineup_overrides(setup, payload)
            except ValueError as exc:
                return jsonify({'error': str(exc)}), 400

            result = simulator.simulate(setup, seed=seed)
        finally:
            _sim_slots.release()

        result_payload = result.model_dump(mode='json')
        with PostgresDB() as db:
            sim_id = db.record_sim_game(user_id=g.user_id, result=result_payload)

        return jsonify({'sim_id': sim_id, 'result': result_payload}), 201

    except GameStuckError as exc:
        # THE GAME COULD NOT FINISH. NOTHING IS STORED IN `sim_game` (THAT TABLE ONLY HOLDS
        # COMPLETED GAMES) - THE STRUCTURED STATE IS LOGGED AND THE MESSAGE IS RETURNED SO THE
        # CLIENT CAN SHOW WHY.
        traceback.print_exc()
        print(f"stuck game sim (game_pk={game_pk}) context: {json.dumps(exc.context, default=str)}")
        return jsonify({'error': str(exc), 'context': exc.context}), 422

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/game/result/<sim_id>', methods=['GET'])
def get_sim_game(sim_id: str):
    """A stored simulated game. The durable, shareable identifier for one."""
    try:
        user_id = optional_user_id()
        with PostgresDB() as db:
            game = db.fetch_sim_game(sim_id, user_id)
        if game is None:
            return jsonify({'error': 'simulated game not found'}), 404
        return jsonify(game), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/game/<int:game_pk>/history', methods=['GET'])
def get_sim_game_history(game_pk: int):
    """Every stored simulation of one real game, newest first."""
    try:
        user_id = optional_user_id()
        limit = min(request.args.get('limit', default=10, type=int), 50)
        with PostgresDB() as db:
            games = db.fetch_sim_games_for_game(game_pk, user_id=user_id, limit=limit)
        return jsonify({'games': games}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/jobs/<job_id>', methods=['GET'])
@require_auth
def get_sim_job(job_id: str):
    """Poll a job's progress. Never carries the result - once it succeeds, fetch it from
    `/sim/season/<job_id>`, which is where it permanently lives."""
    try:
        with PostgresDB() as db:
            job = db.get_sim_job(job_id, g.user_id)
        if job is None:
            return jsonify({'error': 'job not found'}), 404
        return jsonify(job), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/jobs/active', methods=['GET'])
@require_auth
def get_active_sim_job():
    """The signed-in user's own in-flight job, if any - lets the client check without having to
    attempt a start first. At most one can ever exist; see `start_season_sim`'s 429."""
    try:
        with PostgresDB() as db:
            job = db.get_active_sim_job(g.user_id)
        return jsonify({'job': job}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/jobs/<job_id>/cancel', methods=['POST'])
@require_auth
def cancel_sim_job(job_id: str):
    """Cancel the signed-in user's own queued/running job.

    Flips the row to a terminal state immediately; the worker thread notices on its next
    progress write (see `_run_sim_job.write_progress`) and stops simulating, which also frees
    its `_sim_slots` permit.
    """
    try:
        with PostgresDB() as db:
            cancelled = db.cancel_sim_job(job_id, g.user_id)
        if not cancelled:
            return jsonify({'error': 'job not found'}), 404
        return jsonify({'status': 'cancelled'}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@sim_bp.route('/sim/season/<job_id>', methods=['GET'])
def get_sim_season(job_id: str):
    """A played season's full result, keyed by the job that produced it.

    This is the durable identifier - unlike the job row, which expires, the season record (and
    this URL) stay valid indefinitely, which is what lets the leaderboard and history link
    directly to a result. Visibility mirrors the leaderboard: public team, or the viewer's own.
    """
    try:
        user_id = optional_user_id()
        with PostgresDB() as db:
            season = db.fetch_sim_season(job_id, user_id)
        if season is None:
            return jsonify({'error': 'season not found'}), 404
        return jsonify(season), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
