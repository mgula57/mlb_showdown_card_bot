from datetime import timedelta
from flask import Blueprint, jsonify

from ..core.mlb_stats_api import MLBStatsAPI

metadata_bp = Blueprint('metadata', __name__)

_SPLITS_CACHE_TTL = timedelta(hours=24)
_mlb_stats_api = MLBStatsAPI(cache_ttl=int(_SPLITS_CACHE_TTL.total_seconds()))


@metadata_bp.route('/metadata/splits', methods=['GET'])
def fetch_splits():
    try:
        codes = _mlb_stats_api.metadata.get_situation_codes()
        splits = [c.model_dump() for c in codes]
        return jsonify({'splits': splits}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
