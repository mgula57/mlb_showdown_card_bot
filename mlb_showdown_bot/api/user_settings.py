import os
import traceback
from functools import wraps

import jwt
from jwt.algorithms import ECAlgorithm
from flask import Blueprint, g, jsonify, request

from ..core.database.postgres_db import PostgresDB

user_settings_bp = Blueprint('user_settings', __name__)


def require_auth(f):
    """Validate Supabase JWT in Authorization header, set g.user_id on success.

    Supports both ES256 (P-256, set SUPABASE_JWT_PUBLIC_KEY) and
    HS256 (set SUPABASE_JWT_SECRET) — auto-detected from the token header.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing Authorization header'}), 401
        token = auth_header.split(' ', 1)[1].strip()

        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as exc:
            return jsonify({'error': f'Malformed token: {exc}'}), 401

        alg = unverified_header.get('alg', '')

        if alg == 'ES256':
            raw_key = os.getenv('SUPABASE_JWT_PUBLIC_KEY', '')
            if not raw_key:
                return jsonify({'error': 'Server misconfiguration: SUPABASE_JWT_PUBLIC_KEY not set'}), 500
            try:
                key = ECAlgorithm.from_jwk(raw_key)
            except Exception as exc:
                return jsonify({'error': f'Invalid SUPABASE_JWT_PUBLIC_KEY: {exc}'}), 500
            algorithms = ['ES256']
        elif alg == 'HS256':
            key = os.getenv('SUPABASE_JWT_SECRET', '')
            if not key:
                return jsonify({'error': 'Server misconfiguration: SUPABASE_JWT_SECRET not set'}), 500
            algorithms = ['HS256']
        else:
            return jsonify({'error': f'Unsupported JWT algorithm: {alg}'}), 401

        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=algorithms,
                audience='authenticated',
                options={'verify_exp': True},
            )
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError as exc:
            return jsonify({'error': f'Invalid token: {exc}'}), 401

        user_id = payload.get('sub')
        if not user_id:
            return jsonify({'error': 'Token missing sub claim'}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated


def optional_user_id() -> str | None:
    """Return the verified user_id from the JWT if present and valid, else None.

    Use this on endpoints that work anonymously but want to attribute actions
    to a logged-in user. Never trust user_id from the request body/params.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1].strip()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        return None

    alg = unverified_header.get('alg', '')
    try:
        if alg == 'ES256':
            raw_key = os.getenv('SUPABASE_JWT_PUBLIC_KEY', '')
            if not raw_key:
                return None
            key = ECAlgorithm.from_jwk(raw_key)
            algorithms = ['ES256']
        elif alg == 'HS256':
            key = os.getenv('SUPABASE_JWT_SECRET', '')
            if not key:
                return None
            algorithms = ['HS256']
        else:
            return None

        payload = jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience='authenticated',
            options={'verify_exp': True},
        )
        return payload.get('sub') or None
    except jwt.InvalidTokenError:
        return None


@user_settings_bp.route('/user/settings', methods=['GET'])
@require_auth
def get_user_settings():
    try:
        db = PostgresDB()
        settings = db.get_user_settings(g.user_id)
        db.close_connection()
        return jsonify(settings or {}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@user_settings_bp.route('/user/settings', methods=['PUT'])
@require_auth
def upsert_user_settings():
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        db = PostgresDB()
        db.upsert_user_settings(g.user_id, payload)
        db.close_connection()
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
