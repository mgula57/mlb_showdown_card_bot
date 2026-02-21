from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from typing import List

from ..core.mlb_stats_api import MLBStatsAPI
from ..core.mlb_stats_api.models.leagues.league import League
from ..core.mlb_stats_api.models.leagues.standings import StandingsType

seasons_bp = Blueprint('seasons', __name__)

SEASONS_CACHE_TTL = timedelta(days=1)
_mlb_stats_api = MLBStatsAPI(cache_ttl=int(SEASONS_CACHE_TTL.total_seconds()))

@seasons_bp.route('/seasons/list', methods=["GET"])
def fetch_season_list():
    """Fetch list of seasons from the database"""
    try:
        season_list = _mlb_stats_api.seasons.get_seasons()
        seasons_data = [season.model_dump() for season in season_list]
        return jsonify({'seasons': seasons_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@seasons_bp.route('/seasons/<season_id>/sports', methods=["GET"])
def fetch_sports_for_season(season_id: str):
    """Fetch sports for a given season"""
    try:
        if not season_id:
            return jsonify({'error': 'Missing required parameter: season'}), 400
        
        sports = _mlb_stats_api.sports.get_sports(season_id=season_id)
        sports_data = [sport.model_dump() for sport in sports]
        return jsonify({'sports': sports_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@seasons_bp.route('/seasons/<season_id>/leagues', methods=["GET"])
def fetch_leagues_for_season(season_id: str):
    """Fetch leagues for a given season"""
    try:
        sport_id = request.args.get('sport_id', 1)  # Optional filter for sport_id
        if not season_id:
            return jsonify({'error': 'Missing required parameter: season'}), 400
        
        leagues = _mlb_stats_api.leagues.get_leagues(season=season_id, sport_id=sport_id, onlyActive=False)

        # Filter to only certain league abbreviations
        # NL, AL, WBC, NGL, ...
        # Only include GL and CL if the current date is between the `spring_start_date` and `spring_end_date` for the season
        filtered_leagues: List[League] = []
        for league in leagues:
            if league.has_showdown_cards:
                filtered_leagues.append(league)
            elif league.is_spring_league and league.season_date_info and league.season_date_info.is_currently_spring:
                filtered_leagues.append(league)

        filtered_leagues.sort(key=lambda x: x.sort_order if x.sort_order is not None else 0)  # Sort leagues by sort_order
        leagues_data = [league.model_dump() for league in filtered_leagues]
        return jsonify({'leagues': leagues_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@seasons_bp.route('/seasons/<season_id>/leagues/<league_id>/standings', methods=["GET"])
def fetch_standings(season_id: str, league_id: str):
    """Fetch standings for a given season and league"""
    try:        
        if not season_id or not league_id:
            return jsonify({'error': 'Missing required parameters: season and league'}), 400
        
        # IF LEAGUE ID IS CL OR GL, USE SPRING_TRAINING STANDINGS TYPE, OTHERWISE USE BY_DIVISION
        standings_type = StandingsType.SPRING_TRAINING if str(league_id) in ['114', '115'] else StandingsType.BY_DIVISION
        standings = _mlb_stats_api.leagues.get_standings(season=season_id, league_id=league_id, standings_type=standings_type)
        standings_data = [standing.model_dump() for standing in standings]
        return jsonify({'standings': standings_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500