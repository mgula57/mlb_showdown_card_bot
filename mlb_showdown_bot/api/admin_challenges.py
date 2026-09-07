"""Admin-only CRUD for Team Challenge templates, plus on-demand instance generation and
rotation. Gated server-side by the admin allowlist (`require_admin`). The frontend surfaces
this in an admin panel above the challenge list; the same operations are available from the
`showdown_bot challenges` CLI.
"""

import traceback

from flask import Blueprint, jsonify, request

from ..core.database.postgres_db import PostgresDB
from ..core.simulation.challenge_generator import (
    MIN_ROSTER_SIZE,
    ChallengeCategory,
    ChallengeError,
    ChallengeGenerator,
    GoalType,
    build_goal_value,
    validate_year_pool,
)
from .user_settings import require_admin

admin_challenges_bp = Blueprint('admin_challenges', __name__)


def _template_fields(payload: dict, *, partial: bool) -> dict:
    """Validate a create (partial=False) or update (partial=True) payload into a column dict
    ready for `create_challenge_template` / `update_challenge_template`. Raises ChallengeError
    with a client-facing message."""
    fields: dict = {}
    present = payload.__contains__

    def want(key: str) -> bool:
        return not partial or present(key)

    if want('slug'):
        slug = (payload.get('slug') or '').strip()
        if not slug:
            raise ChallengeError("slug is required")
        fields['slug'] = slug
    if want('title'):
        title = (payload.get('title') or '').strip()
        if not title:
            raise ChallengeError("title is required")
        fields['title'] = title
    if want('description'):
        fields['description'] = (payload.get('description') or '').strip()

    # goal_type + its goal_value dependents travel together: if any of the three is in the
    # payload, re-derive goal_value so an edit can't leave it stale.
    if present('goal_type') or present('min_wins') or present('beat_team_abbr') or not partial:
        raw_goal = payload.get('goal_type')
        try:
            goal_type = GoalType(raw_goal) if raw_goal is not None else None
        except ValueError:
            raise ChallengeError(f"invalid goal_type '{raw_goal}'")
        if goal_type is None:
            raise ChallengeError("goal_type is required")
        fields['goal_type'] = goal_type.value
        fields['goal_value'] = build_goal_value(goal_type, payload.get('min_wins'), payload.get('beat_team_abbr'))

    if want('category'):
        raw_cat = payload.get('category') or ChallengeCategory.THEMED.value
        try:
            fields['category'] = ChallengeCategory(raw_cat).value
        except ValueError:
            raise ChallengeError(f"invalid category '{raw_cat}'")

    if want('pts_limit'):
        pts = payload.get('pts_limit')
        fields['pts_limit'] = int(pts) if pts not in (None, '') else None
    if want('roster_size'):
        roster = int(payload.get('roster_size') or 25)
        if roster < MIN_ROSTER_SIZE:
            raise ChallengeError(f"roster_size must be at least {MIN_ROSTER_SIZE}")
        fields['roster_size'] = roster

    if want('year_pool'):
        year_pool = (payload.get('year_pool') or 'any').strip()
        validate_year_pool(year_pool)
        fields['year_pool'] = year_pool
    if want('replaces_pool'):
        fields['replaces_pool'] = (payload.get('replaces_pool') or 'any').strip()

    if want('player_filters'):
        pf = payload.get('player_filters')
        if pf in (None, '', {}):
            fields['player_filters'] = None
        elif isinstance(pf, dict):
            fields['player_filters'] = pf
        else:
            raise ChallengeError("player_filters must be a JSON object or null")

    if want('active'):
        fields['active'] = bool(payload.get('active', True))

    return fields


@admin_challenges_bp.route('/admin/challenges', methods=['GET'])
@require_admin
def list_challenges():
    """Every template (with rotation status) plus the instances currently live."""
    try:
        with PostgresDB() as db:
            templates = db.list_challenge_templates()
            live_instances = db.fetch_active_challenges(user_id=None)
        return jsonify({'templates': templates, 'live_instances': live_instances}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_challenges_bp.route('/admin/challenges/templates', methods=['POST'])
@require_admin
def create_challenge_template():
    try:
        payload = request.get_json(silent=True) or {}
        fields = _template_fields(payload, partial=False)
        with PostgresDB() as db:
            template_id = db.create_challenge_template(
                slug=fields['slug'], title=fields['title'], description=fields['description'],
                goal_type=fields['goal_type'], goal_value=fields['goal_value'],
                pts_limit=fields.get('pts_limit'), year_pool=fields.get('year_pool', 'any'),
                replaces_pool=fields.get('replaces_pool', 'any'), active=fields.get('active', True),
                player_filters=fields.get('player_filters'), category=fields.get('category', 'themed'),
                roster_size=fields.get('roster_size', 25),
            )
            template = db.get_challenge_template(template_id)
        return jsonify(template), 201
    except ChallengeError as exc:
        return jsonify({'error': str(exc)}), exc.status
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_challenges_bp.route('/admin/challenges/templates/<template_id>', methods=['PUT'])
@require_admin
def update_challenge_template(template_id: str):
    try:
        payload = request.get_json(silent=True) or {}
        fields = _template_fields(payload, partial=True)
        with PostgresDB() as db:
            template = db.update_challenge_template(template_id, fields)
        if template is None:
            return jsonify({'error': 'Template not found'}), 404
        return jsonify(template), 200
    except ChallengeError as exc:
        return jsonify({'error': str(exc)}), exc.status
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_challenges_bp.route('/admin/challenges/templates/<template_id>', methods=['DELETE'])
@require_admin
def delete_challenge_template(template_id: str):
    try:
        with PostgresDB() as db:
            result = db.delete_challenge_template(template_id)
        if result == 'not_found':
            return jsonify({'error': 'Template not found'}), 404
        if result == 'in_use':
            return jsonify({'error': 'A live instance still uses this template — deactivate it instead.'}), 409
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_challenges_bp.route('/admin/challenges/templates/<template_id>/instance', methods=['POST'])
@require_admin
def generate_challenge_instance(template_id: str):
    """Force one live instance for this template now, outside the category rotation. Body:
    {force?: bool}."""
    try:
        force = bool((request.get_json(silent=True) or {}).get('force'))
        with PostgresDB() as db:
            template = db.get_challenge_template(template_id)
            if template is None:
                return jsonify({'error': 'Template not found'}), 404
            result = ChallengeGenerator(db).instance_from_template(template, force=force)
        return jsonify({
            'instance_id': result.instance_id, 'slug': result.slug,
            'year': result.year, 'replaces_abbr': result.replaces_abbr,
        }), 201
    except ChallengeError as exc:
        return jsonify({'error': str(exc)}), exc.status
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@admin_challenges_bp.route('/admin/challenges/rotate', methods=['POST'])
@require_admin
def rotate_challenges():
    """Run the weekly rotation on demand: prune old expired instances, then fill every category
    with no live challenge from its least-recently-used active template."""
    try:
        with PostgresDB() as db:
            report = ChallengeGenerator(db).rotate()
        return jsonify({
            'pruned': report.pruned,
            'created': [
                {'instance_id': r.instance_id, 'slug': r.slug, 'year': r.year, 'replaces_abbr': r.replaces_abbr}
                for r in report.created
            ],
            'skipped': report.skipped,
        }), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
