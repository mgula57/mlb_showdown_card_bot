import threading
import traceback
from datetime import datetime, timedelta

from flask import Blueprint, g, jsonify, request

from ..core.card.sets import Set
from ..core.card.team_builder.team import BULLPEN_ROLES, FIELD_POSITIONS, ROTATION_ROLES, Team as BuilderTeam
from ..core.database.postgres_db import PostgresDB
from ..core.simulation.models import SeasonSimulationConfig
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

# Progress fires once per game - 2437 times a season. Writing each one would be thousands of
# round trips for a bar the user reads a few times a second.
_PROGRESS_WRITE_INTERVAL = timedelta(seconds=1)

_SEASONS_CACHE_TTL = timedelta(hours=12)
_seasons_cache: dict[str, tuple[list, datetime]] = {}

# Seasons the archive has full card coverage for. Before 1977 the card pool is Negro Leagues
# plus a 16-team MLB whose franchise relocations (BRO/BSN/NYG/PHA/SLB) are not mapped yet, so
# the schedule cannot be joined to cards - see Team.for_year.
_EARLIEST_SEASON = 1977


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

        try:
            year = int(payload.get('year'))
        except (TypeError, ValueError):
            return jsonify({'error': 'year is required'}), 400
        if year < _EARLIEST_SEASON:
            return jsonify({'error': f'Seasons before {_EARLIEST_SEASON} cannot be simulated yet.'}), 400

        try:
            showdown_set = Set(str(payload.get('set') or '2000'))
        except ValueError:
            return jsonify({'error': f"unknown set '{payload.get('set')}'"}), 400

        with PostgresDB() as db:
            row = db.get_team(team_id, g.user_id)
            if row is None:
                return jsonify({'error': 'team not found'}), 404
            if db.count_running_sim_jobs(g.user_id) > 0:
                return jsonify({'error': 'You already have a simulation running. Wait for it to finish.'}), 429

            team = BuilderTeam.from_db_row(row)
            roster_error = _roster_error(team)
            if roster_error:
                return jsonify({'error': roster_error}), 422

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
            job_id = db.create_sim_job(
                user_id=g.user_id,
                team_id=team_id,
                # THE BUILDER TEAM IS DROPPED FROM THE STORED CONFIG - IT IS A FULL ROSTER THE
                # TEAM ITSELF ALREADY HOLDS, AND ONLY THE SETUP ECHO IS NEEDED FOR DISPLAY.
                config={'year': year, 'set': showdown_set.value, 'replaces': replaces, 'seed': payload.get('seed'),
                        'team_name': team.name, 'team_abbreviation': team.abbreviation},
            )

        if not _sim_slots.acquire(blocking=False):
            with PostgresDB() as db:
                db.finish_sim_job(job_id, error='The simulator is busy right now. Try again in a minute.')
            return jsonify({'error': 'The simulator is busy right now. Try again in a minute.'}), 429

        try:
            threading.Thread(
                target=_run_sim_job, args=(job_id, config, replaces, g.user_id, team_id),
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


def _run_sim_job(job_id: str, config: SeasonSimulationConfig, team_abbr: str, user_id: str | None = None, team_id: str | None = None) -> None:
    """Run one simulation to completion and record the result.

    Runs in a background thread with its own DB connections - it must never share the one the
    request used, and the progress writer needs one separate from the simulation's own reads.
    """
    try:
        last_write = datetime.min

        def write_progress(phase: str | None = None, completed: int | None = None, total: int | None = None) -> None:
            try:
                with PostgresDB() as progress_db:
                    progress_db.update_sim_job_progress(job_id, phase=phase, games_completed=completed, games_total=total)
            except Exception:
                pass  # PROGRESS IS COSMETIC - NEVER LET IT KILL THE RUN

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

        write_progress(phase='Building results')
        summary = SeasonSummaryBuilder(result=result, team_abbr=team_abbr).build()
        # DROP THE ~6 MB RESULT BEFORE THE WRITE - ONLY THE PROJECTION IS PERSISTED.
        del result

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
            )
            db.finish_sim_job(job_id)

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

@sim_bp.route('/sim/leaderboard', methods=['GET'])
def get_sim_leaderboard():
    """Played seasons ranked by wins, one row per team (its best run), newest season first.

    Unauthenticated callers see public teams only; a signed-in user additionally sees their own
    private results and has their rows flagged.
    """
    try:
        user_id = optional_user_id()
        year = request.args.get('year', type=int)
        limit = min(request.args.get('limit', default=25, type=int), 100)

        rows = []
        with PostgresDB() as db:
            rows = db.fetch_sim_leaderboard(user_id=user_id, year=year, per_season_limit=limit)

        # Rows arrive ordered by (year DESC, rank ASC), so seasons group in a single pass.
        seasons: list[dict] = []
        for row in rows:
            if not seasons or seasons[-1]['year'] != row['year']:
                seasons.append({'year': row['year'], 'entries': [], 'has_own_entry': False})
            seasons[-1]['entries'].append(row)
            if row.get('is_own'):
                seasons[-1]['has_own_entry'] = True

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
