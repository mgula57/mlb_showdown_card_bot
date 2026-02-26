"""MLB Stats API - Sync-only implementation for all use cases"""

from .clients.teams_client import TeamsClient, Team, Roster, RosterTypeEnum
from .clients.people_client import PeopleClient
from .clients.leagues_client import LeaguesClient
from .clients.seasons_client import SeasonsClient
from .clients.sports_client import SportsClient, SportEnum
from .models.person import Player
from typing import Optional
import logging
import time
import os
from datetime import datetime

import requests_cache
from prettytable import PrettyTable

from ..card.stats.stats_period import StatsPeriod

# Logging
logger = logging.getLogger(__name__)

class MLBStatsAPI:
    """MLB Stats API client for all operations"""
    
    def __init__(
        self,
        use_persistent_cache: bool = False,
        cache_ttl_seconds: int = 60 * 60 * 24,
        cache_name: Optional[str] = None,
        **config,
    ):
        if use_persistent_cache:
            default_cache = os.path.expanduser("~/Library/Caches/mlb_showdown_card_bot/mlb_stats_cache")
            session = requests_cache.CachedSession(
                cache_name=cache_name or default_cache,
                backend="sqlite",
                expire_after=cache_ttl_seconds,
                allowable_methods=("GET",),
            )
            config.setdefault("session", session)

            # Avoid double-caching: use persistent HTTP cache for CLI runs.
            config.setdefault("use_cache", False)

        self.leagues = LeaguesClient(**config)
        self.people = PeopleClient(**config)
        self.teams = TeamsClient(**config)
        self.seasons = SeasonsClient(**config)
        self.sports = SportsClient(**config)

    # -------------------------
    # PLAYER SEARCH + BUILD
    # -------------------------

    def build_full_player_from_search(self, search_name: str, stats_period: StatsPeriod) -> Player:

        # Search for the player by name
        player_search_results = self.people.search_players(name=search_name)

        # If no results found, return None
        if not player_search_results or len(player_search_results) == 0:
            logger.warning(f"No players found for name: {search_name}")
            return None

        # Fetch full player details using the player ID
        player = self.people.get_player(player_id=player_search_results[0].id, stats_period=stats_period)

        return player
    

    # -------------------------
    # HISTORICAL ROSTER FETCHING
    # -------------------------

    def fetch_wbc_players_by_year(self) -> list[dict]:
        """Fetches all players who participated in the WBC for a given year"""
        
        # Get the WBC league
        wbc_league = self.leagues.get_league(abbreviation="WBC", sport_id=SportEnum.INTERNATIONAL.value)

        if not wbc_league:
            print("WBC league not found.")
            return []
        
        # Get each season for the WBC
        current_year = datetime.now().year
        wbc_seasons = [2006, 2009, 2013, 2017, 2023, 2026] + ( [] if current_year < 2029 else list(range(2029, current_year + 1, 3))) # Add future seasons every 3 years until current year
        all_players: list[dict] = []

        season_progress: dict[int, dict[str, int | str]] = {
            season: {"teams": 0, "players_added": 0, "status": "PENDING", "teams_source": "-"}
            for season in wbc_seasons
        }
        team_loading_rows: list[list] = []
        last_rendered_lines = 0

        def colorize_status(status: str) -> str:
            normalized = status.upper()
            if normalized.startswith("ERROR"):
                return f"\033[31m{status}\033[0m"
            if normalized in {"DONE", "OK"}:
                return f"\033[32m{status}\033[0m"
            if normalized in {"LOADING", "PENDING"}:
                return f"\033[33m{status}\033[0m"
            if normalized == "DONE*":
                return f"\033[33m{status}\033[0m"
            return status

        def colorize_source(source: str) -> str:
            normalized = source.upper()
            if normalized == "LIVE":
                return f"\033[32m{source}\033[0m"
            if normalized == "REQUESTS_CACHE":
                return f"\033[36m{source}\033[0m"
            if normalized == "MEMORY":
                return f"\033[35m{source}\033[0m"
            return source

        def render_progress_tables() -> None:
            nonlocal last_rendered_lines
            season_summary_table = PrettyTable(field_names=["Season", "Teams", "Players Added", "Status", "Teams Source"])
            team_loading_table = PrettyTable(field_names=["Season", "Team", "Abbr", "Players Added", "Status", "Source"])

            for season in wbc_seasons:
                progress = season_progress[season]
                season_summary_table.add_row([
                    season,
                    progress["teams"],
                    progress["players_added"],
                    colorize_status(str(progress["status"])),
                    colorize_source(str(progress["teams_source"])),
                ])

            for row in team_loading_rows:
                row_copy = list(row)
                row_copy[4] = colorize_status(str(row_copy[4]))
                row_copy[5] = colorize_source(str(row_copy[5]))
                team_loading_table.add_row(row_copy)

            output = "\n".join([
                "WBC Player Load Progress",
                "",
                str(season_summary_table),
                str(team_loading_table),
            ])

            if last_rendered_lines > 0:
                print(f"\033[{last_rendered_lines}A", end="")
            print("\033[J", end="")
            print(output)
            last_rendered_lines = output.count("\n") + 1

        render_progress_tables()

        for season in wbc_seasons:
            season_players_added = 0
            season_had_errors = False

            # Get Rosters for each season
            try:
                wbc_teams: list[Team] = self.teams.get_teams(season=season, league_id=wbc_league.id)
                season_progress[season]["teams"] = len(wbc_teams)
                season_progress[season]["status"] = "LOADING"
                season_progress[season]["teams_source"] = getattr(self.teams, "last_response_cache_layer", "UNKNOWN")
                render_progress_tables()
            except Exception as e:
                season_progress[season]["status"] = "ERROR"
                season_progress[season]["teams_source"] = "ERROR"
                team_loading_rows.append([season, "N/A", "N/A", 0, f"ERROR: {e}", "-"])
                render_progress_tables()
                continue

            for team in wbc_teams:
                last_source = None
                try:
                    roster = self.teams.get_team_roster(team_id=team.id, season=season, roster_type=RosterTypeEnum.ACTIVE)
                    players_added_for_team = 0
                    for player in roster.roster:
                        player_info = {
                            'player_id': player.person.id,
                            'full_name': player.person.full_name,
                            'team': team.abbreviation,
                            'season': season,
                        }
                        all_players.append(player_info)
                        players_added_for_team += 1

                    season_players_added += players_added_for_team
                    last_source = getattr(self.teams, "last_response_cache_layer", "UNKNOWN")
                    team_loading_rows.append([
                        season,
                        team.name,
                        team.abbreviation or "N/A",
                        players_added_for_team,
                        "OK",
                        last_source,
                    ])
                    
                except Exception as e:
                    season_had_errors = True
                    team_loading_rows.append([
                        season,
                        team.name,
                        team.abbreviation or "N/A",
                        0,
                        "ERROR",
                        last_source,
                    ])
                finally:
                    season_progress[season]["players_added"] = season_players_added
                    render_progress_tables()

                if last_source and last_source != 'REQUESTS_CACHE':
                    time.sleep(1) # Sleep to avoid hitting rate limits if not pulling from cache

            season_progress[season]["status"] = "DONE*" if season_had_errors else "DONE"
            season_progress[season]["players_added"] = season_players_added
            render_progress_tables()
        
        return all_players
        

__all__ = [
    'MLBStatsAPI', 
    'Player',
    'Team',
    'Roster',
    'RosterTypeEnum',
    'SportEnum',
]