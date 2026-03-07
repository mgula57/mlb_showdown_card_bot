
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
        league_id = request.args.get('league_id', default=None, type=int)
        date = request.args.get('date', default=None, type=str)
        tz_name = request.args.get('tz_name', default='America/New_York', type=str)
        probable_pitchers = request.args.get('include_probable_pitchers', default='true', type=str).lower() == 'true'
        include_linescore = request.args.get('include_linescore', default='false', type=str).lower() == 'true'
        include_decisions = request.args.get('include_decisions', default='false', type=str).lower() == 'true'

        schedule = _mlb_stats_api.games.get_schedule(
            sport_id=sport_id,
            season=season,
            league_id=league_id,
            date=date,
            includeProbablePitchers=probable_pitchers,
            tz_name=tz_name,
            include_linescore=include_linescore,
            include_decisions=include_decisions,
        )
        
        # ADD PROBABLE PITCHERS TO SCHEDULE RESPONSE
        if schedule and probable_pitchers:
            db = PostgresDB()
            showdown_set = request.args.get('showdown_set', default='2000', type=str)
            is_wbc = sport_id == SportEnum.INTERNATIONAL.value # SPORT_ID 51
            schedule = db.add_player_cards_to_game_schedule(
                schedule, 
                showdown_set=showdown_set, 
                is_wbc=is_wbc,
                season=int(season)
            )
        
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