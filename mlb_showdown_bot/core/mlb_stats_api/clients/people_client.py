"""Player and person-related API endpoints"""

from pprint import pprint
from time import sleep
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..base_client import BaseMLBClient
from ..models.person import Players, Player, FreeAgent, StatTypeEnum
from ..models.leagues.league import LeagueListEnum
from ...card.stats.stats_period import StatsPeriod, StatsPeriodYearType, PlayerType
import json

_PLAYER_FIELDS = [
    # People root and identity
    'people', 'id', 'fullName', 'batSide', 'description', 'pitchHand',
    'primaryPosition', 'code', 'abbreviation', 'type',
    'rookieSeasons',
    # Cross-reference IDs (for Fangraphs ID lookup)
    'xrefIds', 'xrefId', 'xrefType',
    # Awards (id/name drive computed properties; season scopes them)
    'awards', 'name', 'season',
    # Stats envelope
    'stats', 'displayName', 'group', 'splits', 'stat',
    # Split context metadata
    'sport', 'split', 'date', 'game', 'gamePk',
    # Team + league (team.abbreviation, team.league.abbreviation)
    'team', 'league',
]

_STAT_KEYS = [
    # Hitting counting stats
    'atBats', 'baseOnBalls', 'caughtStealing', 'doubles', 'gamesPlayed',
    'gamesStarted', 'groundIntoDoublePlay', 'hitByPitch', 'hits', 'homeRuns',
    'intentionalWalks', 'plateAppearances', 'rbi', 'runs', 'sacBunts',
    'sacFlies', 'stolenBases', 'strikeOuts', 'totalBases', 'triples',
    # Pitching counting stats
    'battersFaced', 'earnedRuns', 'era', 'groundOutsToAirouts', 'hitBatsmen',
    'inningsPitched', 'losses', 'saves', 'wins', 'whip', 'gamesPitched',
    # IF/FB batted ball components (pitcher advanced)
    'popOuts', 'popHits', 'flyOuts', 'flyHits', 'lineOuts', 'lineHits',
    # Fielding
    'position',
    # Rate / slashline
    'avg', 'slg', 'obp', 'ops',
    # Sabermetrics
    'war', 'wRcPlus',
]

class PeopleClient(BaseMLBClient):
    """Client for person/player related endpoints - inherits all base functionality"""

    # -----------------------
    # STANDARD PLAYERS
    # -----------------------

    def search_players(self, name: str, active_status: str = 'both', limit: int = 25, seasons: Optional[List[int]] = None, league_list: Optional[LeagueListEnum] = None, hydrations: Optional[List[str]] = None, response_fields_list: Optional[List[str]] = None) -> List[Player]:
        """Search for players by name"""
        params = {
            'names': name,
            'activeStatus': active_status,
            'limit': limit
        }
        if len(name) == 0:
            del params['names']  # API does not like empty string for name search, so we will remove the parameter to search all players (filtered by activeStatus and seasons if provided)
        if seasons:
            params['seasons'] = ','.join(map(str, seasons))
        if response_fields_list:
            params['fields'] = ','.join(response_fields_list + ['people']) # Ensure 'people' is always included in the response for proper parsing into Player objects
        if hydrations:
            params['hydrate'] = ','.join(hydrations)
        if league_list:
            params['leagueListId'] = league_list.value
        # Uses base client's _make_request with caching and rate limiting
        data = self._make_request('people/search', params)
        return [Player(**player_data) for player_data in data.get('people', [])]

    def get_player(self, player_id: int, primary_position: str = None, stats_period: StatsPeriod = None, include_stats: bool = True, league_list: Optional[LeagueListEnum] = None) -> Player:
        """Get player information by ID

        Args:
            player_id: MLB player ID
            primary_position: Optional primary position abbreviation for the player (e.g. 'P' for pitcher, 'OF' for outfielder). This can help with context-specific stats.
            stats_period: Optional StatsPeriod object for context-specific data
            include_stats: Whether to include basic stats in the response
            league_list: Optional LeagueListEnum for specifying league context
        
        Returns:
            Person object with player details
        """
        hydrations = [
            'currentTeam',
            'rookieSeasons',
            'awards',
            'xrefId',
        ]
        seasons: Optional[List[int]] = []
        player_type = stats_period.player_type_for_mlb_api(primary_position) if stats_period else (PlayerType.PITCHER if primary_position and primary_position.upper() == 'P' else PlayerType.HITTER)
        types: Optional[List[StatTypeEnum]] = None
        if include_stats:
            hydrations.extend([
                'team(league)',
            ])
            
            is_non_mlb = league_list and 'milb' in league_list.value.lower()
            types: list[StatTypeEnum] = [
            
            ] if is_non_mlb else [
                StatTypeEnum.SABERMETRICS,
                StatTypeEnum.RANKINGS_BY_YEAR,
            ]
            if stats_period:
                match stats_period.year_type:
                    case StatsPeriodYearType.SINGLE_YEAR:
                        seasons = [stats_period.year_int]
                        if is_non_mlb:
                            types.extend([StatTypeEnum.STATS_SINGLE_SEASON])
                        else:
                            types.extend([StatTypeEnum.STATS_SINGLE_SEASON, StatTypeEnum.STATS_SINGLE_SEASON_ADVANCED, StatTypeEnum.GAME_LOG])
                    case StatsPeriodYearType.FULL_CAREER:
                        types.extend([StatTypeEnum.CAREER, StatTypeEnum.CAREER_ADVANCED])
                    case StatsPeriodYearType.MULTI_YEAR:
                        seasons = stats_period.year_list
                        types.extend([StatTypeEnum.STATS_SINGLE_SEASON, StatTypeEnum.STATS_SINGLE_SEASON_ADVANCED])

                if player_type.is_pitcher and not is_non_mlb:
                    types.append(StatTypeEnum.STAT_SPLITS)

        try:
            players = self.get_players(
                player_ids=[player_id],
                include_stats=include_stats,
                type=player_type, 
                seasons=seasons, 
                league_list=league_list,
                stat_types=types if types else None,
                limit_hydrated_fields=True
            )
            if len(players.players) > 0:
                return players.players[0]
            else:
                raise ValueError(f"No player found with ID {player_id}")
        except Exception as e:
            print(f"Error fetching player with ID {player_id}: {e}")
            raise e

    def get_players(self, player_ids: List[int], include_stats: bool = False, type: Optional[PlayerType] = None, seasons: Optional[List[int]] = None, league_list: Optional[LeagueListEnum] = None, stat_types: Optional[List[StatTypeEnum]] = None, limit_hydrated_fields: Optional[bool] = False) -> Players:
        """Get multiple players by their IDs. Results in a Players object which contains a list of Player objects.
        
        Args:
            player_ids: List of MLB player IDs
            include_stats: Whether to include stats in the response (defaults to False for performance when fetching multiple players)
            type: Optional PlayerType to help determine which stats to include if include_stats is True (e.g. pitcher vs hitter)
            seasons: Optional list of seasons to include stats for if include_stats is True
            league_list: Optional LeagueListEnum for specifying league context (e.g. MiLB vs MLB) if include_stats is True
            stat_types: Optional list of StatTypeEnum to specify which stat types to include if include_stats is True

        Returns:
            Players object containing a list of Player objects
        """

        # MLB API allows up to 10 player IDs per request, so we will chunk the request into multiple calls if needed.
        player_id_chunks = [player_ids[i:i + 10] for i in range(0, len(player_ids), 10)]
        all_players: list[Player] = []
        for index, chunk in enumerate(player_id_chunks):

            params = {
                'personIds': ",".join([str(pid) for pid in chunk]),
            }
            hydrations = [
                'currentTeam',
                'rookieSeasons',
                'awards',
                'xrefId',
            ]
            if include_stats:
                
                # Defaults
                hydrations.append('team(league)')

                # Add seasons
                if seasons:
                    seasons_list_str = ",".join([str(season) for season in seasons])
                    seasons_hydration = f",seasons=[{seasons_list_str}]" if len(seasons) > 0 else ""

                stat_types = stat_types if stat_types else ([StatTypeEnum.SABERMETRICS] if league_list and 'milb' in league_list.value.lower() else [StatTypeEnum.SABERMETRICS, StatTypeEnum.RANKINGS_BY_YEAR])
                pitcher_stat_groups = ['pitching', 'fielding']
                hitter_stat_groups = ['hitting', 'fielding']
                league_list_hydration = f",leagueListId={league_list.value}" if league_list else ""
                is_milb = league_list and 'milb' in league_list.value.lower()
                pitcher_sit_codes = '' if is_milb else ',sitCodes=[sp,rp]'
                if type:
                    match type:
                        case PlayerType.PITCHER:
                            hydrations.append(f'stats(team(league),group=[{",".join(pitcher_stat_groups)}],type=[{",".join([st.value for st in stat_types])}]{seasons_hydration}{league_list_hydration}{pitcher_sit_codes})')
                        case PlayerType.HITTER:
                            hydrations.append(f'stats(team(league),group=[{",".join(hitter_stat_groups)}],type=[{",".join([st.value for st in stat_types])}]{seasons_hydration}{league_list_hydration})')
                else:
                    unique_groups = set(pitcher_stat_groups + hitter_stat_groups)
                    hydrations.append(f'stats(team(league),group=[{",".join(unique_groups)}],type=[{",".join([st.value for st in stat_types])}]{seasons_hydration}{league_list_hydration}{pitcher_sit_codes})')

                if limit_hydrated_fields:
                    params['fields'] = ','.join(_PLAYER_FIELDS + _STAT_KEYS)

            params['hydrate'] = ','.join(hydrations)
            data = self._make_request('people', params)
            
            all_players.extend(data.get('people', []))

            if index > 0:  # Add a short delay between requests to avoid hitting rate limits
                sleep(0.15)

        return Players(people=all_players)

    # -----------------------
    # FREE AGENTS
    # -----------------------
    def get_free_agents(self, season: int) -> List[FreeAgent]:
        """Get list of free agent players for a given season"""
        params = {
            'season': season,
            'hydrate': 'team,person',
        }
        data = self._make_request('people/freeAgents', params)
        free_agent_list = data.get('freeAgents', [])

        free_agent_objects = [FreeAgent(**fa_data) for fa_data in free_agent_list]
                
        return sorted(free_agent_objects, key=lambda fa: (fa.sort_order if fa.sort_order is not None else 9999, fa.date_signed or datetime.max.date()))
