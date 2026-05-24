from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

from ..core.database.postgres_db import PostgresDB

stats_bp = Blueprint('stats', __name__)

_ranges_cache: dict[str, tuple[dict, datetime]] = {}
_RANGES_CACHE_TTL = timedelta(hours=24)


@stats_bp.route('/stats/ranges', methods=['GET'])
def get_stat_ranges():
    season = request.args.get('season', type=int)
    player_type = request.args.get('player_type', '').upper()
    print(f"Received request for stat ranges with season={season} and player_type={player_type}")
    if not season or player_type not in ('HITTER', 'PITCHER'):
        return jsonify({'error': 'season (int) and player_type (HITTER|PITCHER) are required'}), 400

    cache_key = f"{season}:{player_type}"
    cached = _ranges_cache.get(cache_key)
    if cached:
        data, ts = cached
        if datetime.now() - ts < _RANGES_CACHE_TTL:
            return jsonify(data), 200

    try:
        db = PostgresDB()
        ranges = db.get_season_stat_ranges(season=season, player_type=player_type)
        db.close_connection()

        payload = {'season': season, 'player_type': player_type, 'ranges': ranges}
        _ranges_cache[cache_key] = (payload, datetime.now())
        return jsonify(payload), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
