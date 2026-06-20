import traceback

from flask import Blueprint, g, jsonify, request

from ..core.database.postgres_db import PostgresDB
from ..core.card.team_builder.team import Team
from ..core.card.team_builder.autofill import BUCKET_QUERY_FILTERS, autofill_team
from .user_settings import require_auth, optional_user_id

user_teams_bp = Blueprint('user_teams', __name__)


@user_teams_bp.route('/user/teams', methods=['GET'])
@require_auth
def get_user_teams():
    try:
        db = PostgresDB()
        teams = db.get_user_teams(g.user_id)
        db.close_connection()
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
        db = PostgresDB()
        team_id = db.create_team(g.user_id, payload)
        team = db.get_team(team_id, g.user_id)
        db.close_connection()
        return jsonify(team), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>', methods=['GET'])
def get_team(team_id: str):
    try:
        user_id = optional_user_id()
        db = PostgresDB()
        team = db.get_team(team_id, user_id)
        db.close_connection()
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
        db = PostgresDB()
        updated = db.update_team(team_id, g.user_id, payload)
        if not updated:
            db.close_connection()
            return jsonify({'error': 'Team not found or not owned by user'}), 404
        team = db.get_team(team_id, g.user_id)
        db.close_connection()
        return jsonify(team), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>', methods=['DELETE'])
@require_auth
def delete_team(team_id: str):
    try:
        db = PostgresDB()
        deleted = db.delete_team(team_id, g.user_id)
        db.close_connection()
        if not deleted:
            return jsonify({'error': 'Team not found or not owned by user'}), 404
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_teams_bp.route('/user/teams/<team_id>/autofill', methods=['POST'])
@require_auth
def autofill_team_route(team_id: str):
    try:
        payload = request.get_json(silent=True) or {}
        pts_distribution  = payload.get('pts_distribution', {})
        pitching_strategy = payload.get('pitching_strategy', None)
        hitting_strategy  = payload.get('hitting_strategy', None)
        active_filters    = payload.get('active_filters', {})

        db = PostgresDB()
        team_row = db.get_team(team_id, g.user_id)
        if team_row is None:
            db.close_connection()
            return jsonify({'error': 'Team not found or access denied'}), 404

        team = Team.from_db_row(team_row) if isinstance(team_row, dict) else team_row

        if not team.pts_limit:
            db.close_connection()
            return jsonify({'error': 'Team must have a points limit set to use autofill'}), 400

        # Fetch candidate pools for each bucket.
        # Two passes per bucket: main pool (top 500 by points) + a low-point
        # supplement (max 150 pts, 200 cards) so cheap budget-filler options
        # always exist regardless of how the main pool skews high.
        candidates_by_bucket: dict[str, list[dict]] = {}
        for bucket, bucket_filters in BUCKET_QUERY_FILTERS.items():
            base = {**bucket_filters, **active_filters}

            main = db.fetch_card_list(filters={
                **base,
                'limit': 500,
                'sort_by': 'points',
                'sort_direction': 'desc',
            }) or []

            budget_floor = db.fetch_card_list(filters={
                **base,
                'max_points': 150,
                'limit': 200,
                'sort_by': 'points',
                'sort_direction': 'desc',
            }) or []

            # Merge, preserving main-pool order; append any budget_floor cards
            # not already present (dedup by card_id)
            seen = {c['card_id'] for c in main}
            merged = main + [c for c in budget_floor if c['card_id'] not in seen]
            candidates_by_bucket[bucket] = merged

        db.close_connection()

        result = autofill_team(
            team=team,
            candidates_by_bucket=candidates_by_bucket,
            pts_distribution=pts_distribution,
            pitching_strategy=pitching_strategy,
            hitting_strategy=hitting_strategy,
        )

        if result is None:
            return jsonify({
                'error': 'autofill_failed',
                'message': "Couldn't complete roster with current selections and budget. Try adjusting your targets or filters.",
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
        db = PostgresDB()
        teams = db.get_public_teams(source=source, limit=limit, offset=offset)
        db.close_connection()
        return jsonify(teams), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
