from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

from ..core.database.postgres_db import PostgresDB
from ..core.card.utils.shared_functions import convert_year_string_to_list

stats_bp = Blueprint('stats', __name__)

_ranges_cache: dict[str, tuple[dict, datetime]] = {}
_RANGES_CACHE_TTL = timedelta(hours=24)


@stats_bp.route('/stats/ranges', methods=['GET'])
def get_stat_ranges():
    season_param = request.args.get('season', type=str)
    player_type = request.args.get('player_type', '').upper()
    pitcher_role_raw = request.args.get('pitcher_role', '').upper() or None
    pitcher_role = pitcher_role_raw if pitcher_role_raw in ('SP', 'RP') else None
    if not season_param or player_type not in ('HITTER', 'PITCHER'):
        return jsonify({'error': 'season (int) and player_type (HITTER|PITCHER) are required'}), 400

    cache_key = f"{season_param}:{player_type}:{pitcher_role}"
    cached = _ranges_cache.get(cache_key)
    if cached:
        data, ts = cached
        if datetime.now() - ts < _RANGES_CACHE_TTL:
            return jsonify(data), 200

    try:
        season = str(season_param).strip().replace(',', '+')  # Ensure season string is + delimited for conversion
        season = convert_year_string_to_list(season)
        db = PostgresDB()
        ranges = db.get_season_stat_ranges(seasons=season, player_type=player_type, pitcher_role=pitcher_role)
        db.close_connection()

        payload = {'season': season, 'player_type': player_type, 'pitcher_role': pitcher_role, 'ranges': ranges}
        _ranges_cache[cache_key] = (payload, datetime.now())
        return jsonify(payload), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
