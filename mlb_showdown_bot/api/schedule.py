
from flask import Blueprint, jsonify, request
from ..core.mlb_stats_api import MLBStatsAPI, RosterTypeEnum, SportEnum

from ..core.database.postgres_db import PostgresDB

schedule_bp = Blueprint('schedule', __name__)

_mlb_stats_api = MLBStatsAPI(cache_ttl=10)

@schedule_bp.route('/schedule', methods=["GET"])
def fetch_schedule():
    """Fetch list of seasons from the database"""
    try:
        sport_id = request.args.get('sport_id', default=1, type=int)
        season = request.args.get('season', default=None, type=str)
        if not season:
            return jsonify({'error': 'Missing required parameter: season'}), 400
        league_ids = request.args.get('league_id', default=None, type=str)
        league_id_list = [int(league_id.strip()) for league_id in league_ids.split(',')] if league_ids else None
        date = request.args.get('date', default=None, type=str)
        tz_name = request.args.get('tz_name', default='America/New_York', type=str)
        probable_pitchers = request.args.get('include_probable_pitchers', default='true', type=str).lower() == 'true'
        include_linescore = request.args.get('include_linescore', default='false', type=str).lower() == 'true'
        include_decisions = request.args.get('include_decisions', default='false', type=str).lower() == 'true'

        schedule = _mlb_stats_api.games.get_schedule(
            sport_id=sport_id,
            season=season,
            league_ids=league_id_list,
            date=date,
            includeProbablePitchers=probable_pitchers,
            tz_name=tz_name,
            include_linescore=include_linescore,
            include_decisions=include_decisions,
        )
        
        # ADD TEAM COLORS IF SPORT IS MLB (SPORT_ID 1)
        if schedule and sport_id == SportEnum.MLB.value:
            schedule.add_team_colors()
        
        schedule_data = schedule.model_dump() if schedule else None
        return jsonify({'schedule': schedule_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/game/<int:game_pk>/boxscore', methods=["GET"])
def fetch_game_boxscore(game_pk: int):
    """Fetch full boxscore for a single game."""
    try:
        boxscore = _mlb_stats_api.games.get_game_boxscore(game_pk)
        return jsonify(boxscore), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500