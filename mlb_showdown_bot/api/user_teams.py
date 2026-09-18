import traceback
from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, request

from ..core.database.postgres_db import PostgresDB
from ..core.card.team_builder.team import Team, DEFAULT_LINEUP_NAME
from ..core.card.team_builder.autofill import BUCKET_QUERY_FILTERS, autofill_team, fetch_stratified_candidates
from ..core.supabase import SupabaseClientManager, upload_to_supabase
from .user_settings import require_auth, optional_user_id
from .utils.file_upload import process_uploaded_file, cleanup_uploaded_file

user_teams_bp = Blueprint('user_teams', __name__)

TEAM_LOGO_BUCKET = 'team_logos'

# Only JPG/PNG are accepted for team logos. `jpeg` is normalized to `jpg` so a
# team never ends up with two logo objects that differ only by that spelling.
TEAM_LOGO_EXTENSIONS = {'jpg': 'jpg', 'jpeg': 'jpg', 'png': 'png'}


def _delete_team_logo_files(team_id: str, keep: str | None = None) -> None:
    """Delete stored logo objects for a team, optionally keeping one path.

    Logos are stored as `<team_id>/logo.<ext>`. When someone replaces a PNG with a
    JPG (or vice versa) the old object would otherwise be orphaned in the bucket and,
    depending on CDN caching, keep shadowing the new one. Best-effort — failures here
    must not block the upload/removal that triggered the cleanup.
    """
    try:
        manager = SupabaseClientManager()
        for item in manager.list_files(TEAM_LOGO_BUCKET, team_id) or []:
            name = item.get('name') or ''
            if not name.startswith('logo.'):
                continue
            path = f'{team_id}/{name}'
            if path != keep:
                manager.delete_file(TEAM_LOGO_BUCKET, path)
    except Exception:
        traceback.print_exc()


def normalize_lineups(payload: dict) -> str | None:
    """Validate and normalize payload['lineups'] in place. Returns an error message, or None.

    Only user-created lineups are stored — the computed 'Default' is dropped. Slots must
    reference cards on the roster and carry a unique batting order in 1-9.
    """
    lineups = payload.get('lineups')
    if lineups is None:
        return None
    if not isinstance(lineups, list):
        return 'lineups must be a list'

    roster_card_ids = {
        slot.get('card_id')
        for slot in (payload.get('roster') or [])
        if isinstance(slot, dict)
    }

    normalized = []
    for lineup in lineups:
        if not isinstance(lineup, dict):
            return 'each lineup must be an object'
        if (lineup.get('name') or '').strip() == DEFAULT_LINEUP_NAME:
            continue  # computed on read, never stored

        slots = lineup.get('slots') or []
        orders = set()
        for slot in slots:
            if not isinstance(slot, dict) or not slot.get('card_id'):
                return 'each lineup slot needs a card_id'
            # Only enforce roster membership when the roster is part of this same payload;
            # a lineup-only update is validated against the roster already in the DB on read.
            if roster_card_ids and slot['card_id'] not in roster_card_ids:
                return f"lineup '{lineup.get('name')}' references {slot['card_id']}, which is not on the roster"
            order = slot.get('batting_order')
            if not isinstance(order, int) or not 1 <= order <= 9:
                return f"batting_order must be an integer 1-9, got {order!r}"
            if order in orders:
                return f"lineup '{lineup.get('name')}' has duplicate batting_order {order}"
            orders.add(order)

        normalized.append({'name': lineup.get('name'), 'slots': slots})

    payload['lineups'] = normalized
    return None


@user_teams_bp.route('/user/teams', methods=['GET'])
@require_auth
def get_user_teams():
    try:
        with PostgresDB() as db:
            teams = db.get_user_teams(g.user_id)
        return jsonify(teams), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams', methods=['POST'])
@require_auth
def create_team():
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        if not payload.get('name') or not payload.get('abbreviation'):
            return jsonify({'error': 'name and abbreviation are required'}), 400
        error = normalize_lineups(payload)
        if error:
            return jsonify({'error': error}), 400
        with PostgresDB() as db:
            team_id = db.create_team(g.user_id, payload)
            team = db.get_team(team_id, g.user_id)
        return jsonify(team), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>', methods=['GET'])
def get_team(team_id: str):
    try:
        user_id = optional_user_id()
        with PostgresDB() as db:
            team = db.get_team(team_id, user_id)
        if team is None:
            return jsonify({'error': 'Team not found'}), 404
        return jsonify(team), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>', methods=['PUT'])
@require_auth
def update_team(team_id: str):
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        error = normalize_lineups(payload)
        if error:
            return jsonify({'error': error}), 400
        with PostgresDB() as db:
            updated = db.update_team(team_id, g.user_id, payload)
            if not updated:
                return jsonify({'error': 'Team not found or not owned by user'}), 404
            team = db.get_team(team_id, g.user_id)
        return jsonify(team), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>', methods=['DELETE'])
@require_auth
def delete_team(team_id: str):
    try:
        with PostgresDB() as db:
            deleted = db.delete_team(team_id, g.user_id)
        if not deleted:
            return jsonify({'error': 'Team not found or not owned by user'}), 404
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>/like', methods=['POST'])
@require_auth
def like_team(team_id: str):
    try:
        with PostgresDB() as db:
            result = db.toggle_team_like(team_id, g.user_id)
        if result is None:
            return jsonify({'error': 'Team not found'}), 404
        return jsonify(result), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>/view', methods=['POST'])
def record_team_view(team_id: str):
    try:
        user_id = optional_user_id()
        with PostgresDB() as db:
            team = db.get_team(team_id, user_id)
            if team is None:
                return jsonify({'error': 'Team not found'}), 404
            # Skip counting the owner's own views. An anonymous viewer is never the owner,
            # so this only ever skips when the caller is signed in as the team's owner.
            if user_id is not None and team.get('user_id') == user_id:
                return jsonify({'counted': False}), 200
            db.record_team_view(team_id)
        return jsonify({'counted': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>/logo', methods=['POST'])
@require_auth
def upload_team_logo(team_id: str):
    file = request.files.get('logo')
    if not file or file.filename == '':
        return jsonify({'error': 'No logo file provided'}), 400

    raw_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    # Fall back to the MIME type when the filename carries no usable extension.
    mime_ext = (file.mimetype or '').lower().removeprefix('image/').replace('jpeg', 'jpg')
    ext = TEAM_LOGO_EXTENSIONS.get(raw_ext) or TEAM_LOGO_EXTENSIONS.get(mime_ext)
    if ext is None:
        return jsonify({'error': 'Logo must be a JPG or PNG image'}), 400

    uploaded_file_data = None
    try:
        uploaded_file_data = process_uploaded_file(file)
        destination_path = f'{team_id}/logo.{ext}'

        upload_result = upload_to_supabase(
            bucket_name=TEAM_LOGO_BUCKET,
            file_path=uploaded_file_data['path'],
            destination_path=destination_path,
            overwrite=True,
            content_type='image/png' if ext == 'png' else 'image/jpeg',
        )
        if not upload_result.get('success'):
            return jsonify({'error': upload_result.get('error') or 'Failed to upload logo'}), 500

        # Drop any prior logo stored under a different extension so the replacement
        # fully takes over.
        _delete_team_logo_files(team_id, keep=destination_path)

        base_url = (SupabaseClientManager().get_public_url(TEAM_LOGO_BUCKET, destination_path) or '').split('?')[0]
        # Cache-bust: overwriting keeps the same URL, so browsers/CDN would otherwise serve the old image.
        logo_url = f'{base_url}?v={int(datetime.now(timezone.utc).timestamp())}'

        with PostgresDB() as db:
            updated = db.update_team(team_id, g.user_id, {'logo_url': logo_url})
            if not updated:
                return jsonify({'error': 'Team not found or not owned by user'}), 404
            team = db.get_team(team_id, g.user_id)
        return jsonify(team), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
    finally:
        if uploaded_file_data:
            cleanup_uploaded_file(uploaded_file_data)


@user_teams_bp.route('/user/teams/<team_id>/logo', methods=['DELETE'])
@require_auth
def delete_team_logo(team_id: str):
    try:
        with PostgresDB() as db:
            updated = db.update_team(team_id, g.user_id, {'logo_url': None})
            if not updated:
                return jsonify({'error': 'Team not found or not owned by user'}), 404
            team = db.get_team(team_id, g.user_id)
        _delete_team_logo_files(team_id)
        return jsonify(team), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>/autofill', methods=['POST'])
@require_auth
def autofill_team_route(team_id: str):
    try:
        payload = request.get_json(silent=True) or {}
        pts_distribution      = payload.get('pts_distribution', {})
        pitching_strategy     = payload.get('pitching_strategy', None)
        hitting_strategy      = payload.get('hitting_strategy', None)
        defense_strategy      = payload.get('defense_strategy', None)
        catcher_defense_strategy = payload.get('catcher_defense_strategy', None)
        active_filters        = payload.get('active_filters', {})
        replace_existing      = bool(payload.get('replace_existing', False))

        pts_target = payload.get('pts_target')
        if pts_target is not None:
            try:
                pts_target = int(pts_target)
            except (TypeError, ValueError):
                return jsonify({'error': 'pts_target must be a number'}), 400

        with PostgresDB() as db:
            team_row = db.get_team(team_id, g.user_id)
            if team_row is None:
                return jsonify({'error': 'Team not found or access denied'}), 404

            team = Team.from_db_row(team_row) if isinstance(team_row, dict) else team_row

            # "Replace existing" wipes the current roster before filling, so autofill drafts a
            # clean team against the full budget instead of topping up around manual picks. Only
            # the in-memory Team is cleared here — the wipe is persisted when the frontend saves
            # the returned roster.
            if replace_existing:
                team.roster = []
                team.rotation = []
                team.lineups = []

            if not team.pts_limit and not pts_target:
                return jsonify({'error': 'Team must have a points limit set, or a target must be provided, to use autofill'}), 400

            # Build the base filter set from the team's stored constraints so that
            # autofill always respects player_filters regardless of what the frontend
            # sends.  Payload active_filters are merged last so the UI can add
            # session-level overrides (e.g. a one-time set filter).  Set restrictions are
            # applied per source below, since each source has its own allowed sets.
            team_filters: dict = {}
            if team.player_filters:
                team_filters.update(team.player_filters)
            # Payload overrides come last
            team_filters.update(active_filters)
            active_filters = team_filters

            # Determine which card sources to query.  Default to BOT; if the team
            # explicitly allows only WOTC cards use that source instead.
            card_sources: list[str] = [s.upper() for s in (team.allowed_card_sources or [])]
            if not card_sources:
                card_sources = ['BOT']

            # An explicit showdown_set override from the caller wins; otherwise each source uses
            # the sets this team allows for it (empty = no set restriction).
            sets_by_source = {source: team.sets_for_source(source) for source in card_sources}

            # Fetch candidate pools for each bucket via stratified sampling across price bands.
            # Cheap tier (10-100 pts) gets the most cards to ensure bench fill has affordable
            # options. This approach ensures representation at all price levels and gives
            # autofill variety. No sort needed — autofill's _sort_candidates() handles
            # shuffling per strategy.
            candidates_by_bucket: dict[str, list[dict]] = {
                bucket: fetch_stratified_candidates(db, bucket_filters, active_filters, card_sources, sets_by_source)
                for bucket, bucket_filters in BUCKET_QUERY_FILTERS.items()
            }

        result = autofill_team(
            team=team,
            candidates_by_bucket=candidates_by_bucket,
            pts_distribution=pts_distribution,
            pitching_strategy=pitching_strategy,
            hitting_strategy=hitting_strategy,
            defense_strategy=defense_strategy,
            catcher_defense_strategy=catcher_defense_strategy,
            pts_target=pts_target,
        )

        if isinstance(result, tuple):
            # (None, error_message) returned
            return jsonify({
                'error': 'autofill_failed',
                'message': result[1],
            }), 422

        return jsonify(result), 200

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/teams/public', methods=['GET'])
def get_public_teams():
    try:
        source = request.args.get('source')
        limit = min(request.args.get('limit', 50, type=int), 200)
        offset = request.args.get('offset', 0, type=int)
        q = request.args.get('q') or None
        collection = request.args.get('collection') or None
        user_id = optional_user_id()
        with PostgresDB() as db:
            teams = db.get_public_teams(
                source=source, limit=limit, offset=offset, q=q, collection=collection,
                user_id=user_id,
            )
        return jsonify(teams), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


# In-memory cache for the public collections list — small, changes rarely.
_collections_cache: dict[str, tuple] = {}
_COLLECTIONS_TTL = timedelta(minutes=5)


@user_teams_bp.route('/teams/collections', methods=['GET'])
def get_team_collections():
    """Visible curated collections, each with its published teams as lightweight summaries."""
    try:
        cached = _collections_cache.get('all')
        if cached and datetime.now(timezone.utc) - cached[1] < _COLLECTIONS_TTL:
            return jsonify(cached[0]), 200
        with PostgresDB() as db:
            collections = db.get_team_collections(include_hidden=False)
            for c in collections:
                c['teams'] = db.get_public_teams(source='official', collection=c['slug'], limit=100)
        _collections_cache['all'] = (collections, datetime.now(timezone.utc))
        return jsonify(collections), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
