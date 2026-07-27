from datetime import datetime, timedelta, timezone
import pprint
from flask import Blueprint, jsonify, request
from typing import List, Optional

from ..core.mlb_stats_api import MLBStatsAPI, RosterTypeEnum
from ..core.mlb_stats_api.models.leagues.league import League
from ..core.mlb_stats_api.models.leagues.standings import StandingsType
from ..core.mlb_stats_api.models.stats.enums import PlayerPoolEnum, StatGroupEnum, LeaderLeaderStatEnum
from ..core.database.postgres_db import PostgresDB, Set as ShowdownSet
from ..core.card.team_builder import RosterToTeamConverter, StoredRosterToTeamConverter, TeamSource

seasons_bp = Blueprint('seasons', __name__)

SEASONS_CACHE_TTL = timedelta(hours=1)
_mlb_stats_api = MLBStatsAPI(cache_ttl=int(SEASONS_CACHE_TTL.total_seconds()))

STANDINGS_CACHE_TTL = timedelta(hours=12)
_standings_cache: dict[str, tuple[list, datetime]] = {}

SHOWDOWN_TEAM_CACHE_TTL = timedelta(hours=1)
_showdown_team_cache: dict[str, tuple[dict, datetime]] = {}

HISTORICAL_TEAMS_CACHE_TTL = timedelta(hours=6)
_historical_teams_cache: dict[str, tuple[dict, datetime]] = {}

AWARDS_CACHE_TTL = timedelta(hours=24)
_awards_cache: dict[str, tuple[dict, datetime]] = {}
AWARD_TYPES = ['MVP', 'CY', 'ROY', 'GG', 'SS']
AWARD_LEAGUES = ['AL', 'NL']

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
        
        # Showdown Set is passed in for PTS context
        showdown_set = request.args.get('showdown_set', None)  # Default to 2000

        cache_key = f"{season_id}:{league_id}:{showdown_set}"
        cached = _standings_cache.get(cache_key)
        if cached and datetime.now() - cached[1] < STANDINGS_CACHE_TTL:
            return jsonify({'standings': cached[0]}), 200

        # IF LEAGUE ID IS CL OR GL, USE SPRING_TRAINING STANDINGS TYPE, OTHERWISE USE BY_DIVISION
        standings_type = StandingsType.SPRING_TRAINING if str(league_id) in ['114', '115'] else StandingsType.BY_DIVISION
        standings = _mlb_stats_api.leagues.get_standings(season=season_id, league_id=league_id, standings_type=standings_type)
        if showdown_set:
            with PostgresDB() as db:
                standings = db.add_points_to_mlb_api_standings(standings, showdown_set=showdown_set)

        standings_data = [standing.model_dump() for standing in standings]
        _standings_cache[cache_key] = (standings_data, datetime.now())
        return jsonify({'standings': standings_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@seasons_bp.route('/seasons/<season_id>/teams/<team_id>/roster', methods=["GET"])
def fetch_roster(season_id: str, team_id: str):
    """Fetch single roster for a given season and team"""
    try:        
        if not season_id or not team_id:
            return jsonify({'error': 'Missing required parameters: season and team'}), 400
        
        roster_type_str = request.args.get('roster_type', 'active')  # Default to active roster
        try:
            roster_type = RosterTypeEnum(roster_type_str)
        except ValueError:
            return jsonify({'error': f'Invalid roster_type: {roster_type_str}. Valid options are: {[rt.value for rt in RosterTypeEnum]}'}), 400
        
        showdown_set = request.args.get('showdown_set', None)  # Optional showdown set parameter for pulling card data
        if showdown_set:
            try:
                showdown_set_enum = ShowdownSet(showdown_set)
            except ValueError:
                return jsonify({'error': f'Invalid showdown_set: {showdown_set}. Valid options are: {[s.value for s in ShowdownSet]}'}), 400
        
        sport_id = request.args.get('sport_id', 1)  # Optional sport_id parameter for pulling card data, default to MLB
        team_abbr = request.args.get('team_abbr', None)  # Optional team abbreviation for pulling card data, e.g. NYY for New York Yankees

        roster = _mlb_stats_api.teams.get_team_roster(team_id=team_id, season=season_id, roster_type=roster_type)
        if showdown_set:
            with PostgresDB() as db:
                roster = db.add_showdown_cards_to_mlb_api_roster(roster=roster, showdown_set=showdown_set_enum.value, season=season_id, sport_id=sport_id, team_abbr=team_abbr)
        roster_data = roster.model_dump(mode='json', exclude_none=True) if roster else None

        return jsonify({'roster': roster_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@seasons_bp.route('/seasons/historical/teams', methods=["GET"])
def fetch_historical_teams():
    """List pre-processed historical teams for the Team Builder's Historical tab.

    Reads internal.dim_historical_team, so no MLB Stats API calls are made and no roster is
    composed on the fly. Rows come back in the same TeamSummary shape as /teams/public, with
    `total_points` and `top_players` scoped to the requested Showdown set.

    Query params: showdown_set, season (one season's shelf), q (search across all seasons),
    sport_id, limit, offset.
    """
    try:
        showdown_set = request.args.get('showdown_set', ShowdownSet._2000.value)
        try:
            showdown_set_enum = ShowdownSet(showdown_set)
        except ValueError:
            return jsonify({'error': f'Invalid showdown_set: {showdown_set}. Valid options are: {[s.value for s in ShowdownSet]}'}), 400

        season = request.args.get('season', None, type=int)
        query = (request.args.get('q', '') or '').strip() or None
        sport_id = request.args.get('sport_id', 1, type=int)
        limit = min(request.args.get('limit', 60, type=int), 200)
        offset = request.args.get('offset', 0, type=int)

        cache_key = f"{showdown_set_enum.value}:{sport_id}:{season}:{query}:{limit}:{offset}"
        cached = _historical_teams_cache.get(cache_key)
        if cached and datetime.now() - cached[1] < HISTORICAL_TEAMS_CACHE_TTL:
            return jsonify(cached[0]), 200

        with PostgresDB() as db:
            teams = db.fetch_historical_teams(
                showdown_set=showdown_set_enum.value,
                season=season,
                q=query,
                sport_id=sport_id,
                limit=limit,
                offset=offset,
            )
            seasons = db.fetch_historical_seasons(sport_id=sport_id)

        payload = {'teams': teams, 'seasons': seasons}
        _historical_teams_cache[cache_key] = (payload, datetime.now())
        return jsonify(payload), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@seasons_bp.route('/seasons/<season_id>/teams/<team_id>/showdown_team', methods=["GET"])
def fetch_showdown_team(season_id: str, team_id: str):
    """Construct a team builder Team from the season's roster + card archive data.

    Prefers the pre-processed slots in internal.dim_historical_roster (a lookup), and falls
    back to composing the roster on the fly for any team the CLI backfill hasn't covered.
    """
    try:
        if not season_id or not team_id:
            return jsonify({'error': 'Missing required parameters: season and team'}), 400

        try:
            season = int(season_id)
        except ValueError:
            return jsonify({'error': f'Invalid season: {season_id}'}), 400

        showdown_set = request.args.get('showdown_set', ShowdownSet._2000.value)
        try:
            showdown_set_enum = ShowdownSet(showdown_set)
        except ValueError:
            return jsonify({'error': f'Invalid showdown_set: {showdown_set}. Valid options are: {[s.value for s in ShowdownSet]}'}), 400

        sport_id = request.args.get('sport_id', 1, type=int)
        team_abbr = request.args.get('team_abbr', None)
        team_name = request.args.get('team_name', None)

        cache_key = f"{season_id}:{team_id}:{sport_id}:{showdown_set_enum.value}"
        cached = _showdown_team_cache.get(cache_key)
        if cached and datetime.now() - cached[1] < SHOWDOWN_TEAM_CACHE_TTL:
            return jsonify({'team': cached[0]}), 200

        synthetic_team_id = f"mlb-{sport_id}-{team_id}-{season_id}-{showdown_set_enum.value}"

        with PostgresDB() as db:
            stored_cards, stored_slots = db.fetch_historical_team_card_pool(
                season=season,
                showdown_set=showdown_set_enum.value,
                team_id=int(team_id),
                sport_id=sport_id,
            )
            if stored_slots:
                # Pre-processed: identity is stored too, so a cold link needs no client-side resolution.
                identity = db.fetch_historical_team(season=season, team_id=int(team_id), sport_id=sport_id) or {}
                builder = StoredRosterToTeamConverter(
                    cards=stored_cards,
                    meta_rows=stored_slots,
                    team_id=synthetic_team_id,
                    name=identity.get('name') or team_name or team_abbr or f"Team {team_id}",
                    abbreviation=identity.get('abbreviation') or team_abbr or str(team_id),
                    primary_color=identity.get('primary_color'),
                    secondary_color=identity.get('secondary_color'),
                )
            else:
                cards = db.fetch_team_season_card_pool(
                    season=season,
                    showdown_set=showdown_set_enum.value,
                    team_id=int(team_id),
                    team_abbr=team_abbr,
                    sport_id=sport_id,
                )
                builder = RosterToTeamConverter(
                    cards=cards,
                    team_id=synthetic_team_id,
                    name=team_name or team_abbr or f"Team {team_id}",
                    abbreviation=team_abbr or str(team_id),
                    season=season,
                )

        team_data = builder.build_api_dict()
        _showdown_team_cache[cache_key] = (team_data, datetime.now())
        return jsonify({'team': team_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@seasons_bp.route('/seasons/asg', methods=["GET"])
def fetch_asg_seasons():
    """List the (season, league) All-Star teams available from the asg_roster lookup table."""
    try:
        with PostgresDB() as db:
            rows = db.fetch_asg_seasons()
        return jsonify({'asg_teams': rows}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@seasons_bp.route('/seasons/<season_id>/asg/<league>/showdown_team', methods=["GET"])
def fetch_asg_showdown_team(season_id: str, league: str):
    """Construct a read-only team builder Team for a season's AL/NL All-Star roster.

    Sources participants (and their real starting positions / batting order / starting pitcher)
    from the internal.asg_roster lookup table, then composes them into a Showdown team via the
    shared RosterToTeamConverter.
    """
    try:
        try:
            season = int(season_id)
        except ValueError:
            return jsonify({'error': f'Invalid season: {season_id}'}), 400

        league = league.upper()

        showdown_set = request.args.get('showdown_set', ShowdownSet._2000.value)
        try:
            showdown_set_enum = ShowdownSet(showdown_set)
        except ValueError:
            return jsonify({'error': f'Invalid showdown_set: {showdown_set}. Valid options are: {[s.value for s in ShowdownSet]}'}), 400

        sport_id = request.args.get('sport_id', 1, type=int)

        cache_key = f"asg:{season_id}:{league}:{sport_id}:{showdown_set_enum.value}"
        cached = _showdown_team_cache.get(cache_key)
        if cached and datetime.now() - cached[1] < SHOWDOWN_TEAM_CACHE_TTL:
            return jsonify({'team': cached[0]}), 200

        with PostgresDB() as db:
            cards, meta_rows = db.fetch_asg_card_pool(
                season=season,
                showdown_set=showdown_set_enum.value,
                league=league,
                sport_id=sport_id,
            )

        if not cards:
            return jsonify({'error': f'No All-Star roster data for {season} {league}'}), 404

        # Build card_id-keyed overrides so the composed team reflects the real ASG starters.
        mlb_id_to_card_id = {c.mlb_id: c.card_id for c in cards if c.mlb_id is not None and c.card_id}
        forced_positions: dict[str, str] = {}
        forced_batting_order: dict[str, int] = {}
        forced_starting_pitcher_id = None
        for r in meta_rows:
            card_id = mlb_id_to_card_id.get(r.get('mlb_id'))
            if not card_id:
                continue
            if r.get('is_starter') and r.get('position') and r['position'] != 'P':
                forced_positions[card_id] = r['position']
                if r.get('batting_order'):
                    forced_batting_order[card_id] = r['batting_order']
            if r.get('is_starting_pitcher'):
                forced_starting_pitcher_id = card_id

        builder = RosterToTeamConverter(
            cards=cards,
            team_id=f"asg-{season_id}-{league}-{showdown_set_enum.value}",
            name=f"{season_id} {league} All-Stars",
            abbreviation=league,
            season=season,
            source=TeamSource.ASG,
            forced_positions=forced_positions,
            forced_batting_order=forced_batting_order,
            forced_starting_pitcher_id=forced_starting_pitcher_id,
        )
        team_data = builder.build_api_dict()
        _showdown_team_cache[cache_key] = (team_data, datetime.now())
        return jsonify({'team': team_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@seasons_bp.route('/seasons/<season_id>/teams', methods=["GET"])
def fetch_teams_for_season(season_id: str):
    """Fetch teams for a given season"""
    try:
        if not season_id:
            return jsonify({'error': 'Missing required parameter: season'}), 400
        
        sport_id = request.args.get('sport_id', 1)  # Optional filter for sport_id
        league_id = request.args.get('league_id', None)  # Optional filter for league_id

        teams = _mlb_stats_api.teams.get_teams(season=season_id, sport_id=sport_id, league_id=league_id)
        teams_data = [team.model_dump() for team in teams]
        return jsonify({'teams': teams_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@seasons_bp.route('/seasons/<season_id>/leaders', methods=["GET"])
def fetch_leaders_for_season(season_id: str):
    """Fetch stat leaders for a given season, with optional filters for category, stat group, and player pool"""
    try:
        if not season_id:
            return jsonify({'error': 'Missing required parameter: season'}), 400

        sport_id = request.args.get('sport_id', 1)
        categories_str = request.args.get('categories', None)
        stat_groups_str = request.args.get('stat_groups', None)
        player_pool_str = request.args.get('player_pool', None)
        limit = request.args.get('limit', None)
        days_back = request.args.get('days_back', None)

        category_enums = [LeaderLeaderStatEnum(category.strip()) for category in categories_str.split(',')] if categories_str else None
        stat_group_enums = [StatGroupEnum(stat_group.strip()) for stat_group in stat_groups_str.split(',')] if stat_groups_str else None
        player_pool_enum = PlayerPoolEnum(player_pool_str.strip()) if player_pool_str else None

        leaders_groups = _mlb_stats_api.stats.get_leaders(
            sport_id=sport_id,
            season=season_id,
            categories=category_enums,
            statGroups=stat_group_enums,
            playerPool=player_pool_enum,
            limit=int(limit) if limit else None,
            days_back=int(days_back) if days_back else None
        )
        leaders_data = [group.model_dump() for group in leaders_groups]
        final_data = {'leaders': leaders_data}

        return jsonify(final_data), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@seasons_bp.route('/seasons/<season_id>/awards', methods=["GET"])
def fetch_awards_for_season(season_id: str):
    """Fetch MVP, Cy Young, Rookie of the Year, Gold Glove, and Silver Slugger winners for a season, split by league"""
    try:
        if not season_id:
            return jsonify({'error': 'Missing required parameter: season'}), 400

        try:
            season = int(season_id)
        except ValueError:
            return jsonify({'error': f'Invalid season: {season_id}'}), 400

        cache_key = season_id
        cached = _awards_cache.get(cache_key)
        if cached and datetime.now() - cached[1] < AWARDS_CACHE_TTL:
            return jsonify({'awards': cached[0]}), 200

        awards_data: dict[str, dict[str, list | None]] = {award_type: {} for award_type in AWARD_TYPES}
        for award_type in AWARD_TYPES:
            for league in AWARD_LEAGUES:
                recipients = _mlb_stats_api.awards.get_recipients(award_id=f"{league}{award_type}", season=season)
                recipients_data = [recipient.model_dump(mode='json') for recipient in recipients]
                if award_type in ('GG', 'SS'):
                    awards_data[award_type][league] = recipients_data
                else:
                    awards_data[award_type][league] = recipients_data[0] if recipients_data else None

        _awards_cache[cache_key] = (awards_data, datetime.now())
        return jsonify({'awards': awards_data}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500