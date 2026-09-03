import traceback

from flask import Blueprint, g, jsonify, request

from ..core.database.postgres_db import PostgresDB
from ..core.card.team_builder.team import Team, DEFAULT_LINEUP_NAME
from ..core.card.team_builder.autofill import BUCKET_QUERY_FILTERS, autofill_team
from ..core.supabase import SupabaseClientManager, upload_to_supabase
from .user_settings import require_auth, optional_user_id
from .utils.file_upload import process_uploaded_file, cleanup_uploaded_file

user_teams_bp = Blueprint('user_teams', __name__)

TEAM_LOGO_BUCKET = 'team_logos'


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


@user_teams_bp.route('/user/teams/<team_id>/logo', methods=['POST'])
@require_auth
def upload_team_logo(team_id: str):
    file = request.files.get('logo')
    if not file or file.filename == '':
        return jsonify({'error': 'No logo file provided'}), 400

    uploaded_file_data = None
    try:
        uploaded_file_data = process_uploaded_file(file)
        ext = uploaded_file_data['filename'].rsplit('.', 1)[-1].lower()
        destination_path = f'{team_id}/logo.{ext}'

        upload_result = upload_to_supabase(
            bucket_name=TEAM_LOGO_BUCKET,
            file_path=uploaded_file_data['path'],
            destination_path=destination_path,
        )
        if not upload_result.get('success'):
            return jsonify({'error': upload_result.get('error') or 'Failed to upload logo'}), 500

        logo_url = SupabaseClientManager().get_public_url(TEAM_LOGO_BUCKET, destination_path)

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

            def _fetch_bucket(bucket_filters: dict) -> list[dict]:
                """Fetch stratified candidate pool across price bands (10-800 pts).
                Ensures representation at all budget levels. Cheap tier (10-100) prioritizes
                position players to improve bench fill success.
                """
                merged_all: list[dict] = []
                seen_ids: set[str] = set()

                # Price bands with card limits per band. Cheaper tiers get more cards
                # to ensure autofill has options when budget-constrained.
                price_bands = [
                    {'min': 10,  'max': 100,  'limit': 100, 'player_type': 'HITTER'},  # Cheap tier: max options for bench fill
                    {'min': 10,  'max': 100,  'limit': 50, 'positions_list': ['STARTER']},  # Cheap tier: options for bullpen
                    
                    {'min': 100, 'max': 200,  'limit': 150},  # Low-mid tier
                    {'min': 200, 'max': 350,  'limit': 150},  # Mid tier (avg ~250)
                    {'min': 350, 'max': 550,  'limit': 100},  # High-mid tier
                    {'min': 550, 'max': 1000,  'limit': 80},   # Premium tier (sparse)
                ]

                for source in card_sources:
                    base = {**bucket_filters, **active_filters, 'source': source}
                    # An explicit showdown_set override from the caller wins; otherwise use the
                    # sets this team allows for this source (empty = no set restriction).
                    if 'showdown_set' not in base:
                        source_sets = team.sets_for_source(source)
                        if source_sets:
                            base['showdown_set'] = source_sets

                    # Fetch from each price band. Cheap tier (10-100 pts) gets more cards
                    # to ensure bench has affordable options when filling.
                    # No sort needed — autofill's _sort_candidates() handles shuffling per strategy.
                    for band in price_bands:
                        filters = {
                            **base,
                            'min_points': band['min'],
                            'max_points': band['max'],
                            'limit': band['limit'],
                            'sort_by': 'random()',
                        }

                        if band.get('player_type', None):
                            filters['player_type'] = band['player_type']

                        if band.get('positions_list', None):
                            filters['positions_list'] = band['positions_list']

                        cards = db.fetch_card_list(filters=filters) or []
                        for c in cards:
                            if c['card_id'] not in seen_ids:
                                c['_card_source'] = source
                                merged_all.append(c)
                                seen_ids.add(c['card_id'])

                return merged_all

            # Fetch candidate pools for each bucket via stratified sampling across price bands.
            # Cheap tier (10-100 pts) gets 150 cards to ensure bench fill has affordable options.
            # This approach ensures representation at all price levels and gives autofill variety.
            candidates_by_bucket: dict[str, list[dict]] = {
                bucket: _fetch_bucket(bucket_filters)
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
        with PostgresDB() as db:
            teams = db.get_public_teams(source=source, limit=limit, offset=offset, q=q)
        return jsonify(teams), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
