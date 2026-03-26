import typer
from pprint import pprint
from prettytable import PrettyTable

from ...core.mlb_stats_api import MLBStatsAPI
from ...core.database.postgres_db import PostgresDB
from ...core.mlb_stats_api.models.leagues.league import SportEnum
from ...core.mlb_stats_api.models.teams.team import Team
from ...core.mlb_stats_api.models.teams.roster import RosterTypeEnum
from ...core.mlb_stats_api.models.games.schedule import Schedule

app = typer.Typer()

_mlb_api = MLBStatsAPI(use_persistent_cache=True)
_mlb_api_no_cache = MLBStatsAPI(use_persistent_cache=False)

@app.command("free_agents")
def free_agents(
    season: int = typer.Option(..., "--season", "-s", help="Season year to get free agents for."),
):
    """Fetch free agent players for a given season from MLB Stats API"""
    print(f"Fetching free agents for season {season}...")
    
    free_agents_list = _mlb_api.people.get_free_agents(season=season)
    
    print(f"Found {len(free_agents_list)} free agents for season {season}:")
    table = PrettyTable()
    table.field_names = ["Player", "Original Team", "New Team", "Signed", "Notes", "Sort Order"]
    for fa in free_agents_list[:25]: # Limit output to first 100 for brevity
        table.add_row([
            fa.player.full_name,
            fa.original_team.name if fa.original_team else '-',
            fa.new_team.name if fa.new_team else '-',
            fa.date_signed or "-",
            fa.notes if fa.notes else '-',
            fa.sort_order if fa.sort_order is not None else 9999
        ])
    print(table)

@app.command("season")
def season(
    season: int = typer.Option(..., "--season", "-s", help="Season year to get free agents for."),
    sport_id: int = typer.Option(1, "--sport_id", "-sp", help="MLB sport ID. Default is 1 (Major League Baseball)."),
    abbreviations: str = typer.Option(None, "--abbreviations", "-abbr", help="League abbreviation to filter standings by (e.g. AL, NL)")
):
    """Fetch season info from MLB Stats API"""

    is_mlb = sport_id == SportEnum.MLB

    abbreviations = [abbr.strip() for abbr in abbreviations.split(',')] if abbreviations else None
    if abbreviations is None and is_mlb:
        abbreviations = ['AL', 'NL']  # Default to AL and NL for MLB if no abbreviations provided
    
    leagues = _mlb_api.leagues.get_leagues(seasons=[season], sport_id=sport_id, abbreviations=abbreviations)
    
@app.command("roster")
def roster(
    team_id: int = typer.Option(None, "--team_id", "-t", help="Team ID to fetch roster for."),
    sport_id: int = typer.Option(1, "--sport_id", "-sp", help="MLB sport ID. Default is 1 (Major League Baseball)."),
    abbreviation: str = typer.Option(None, "--abbreviation", "-abbr", help="Team abbreviation to fetch roster for (e.g. NYY for New York Yankees)."),
    roster_type: str = typer.Option("active", "--roster_type", "-rt", help="Roster type to fetch (e.g. active, 40Man, fullSeason, etc.)"),
    season: int = typer.Option(None, "--season", "-s", help="Season year to filter teams by (required if using abbreviation)."),
    pull_showdown_card_data: bool = typer.Option(False, "--pull_card_data", "-cards", help="Optionally pull showdown card data for players in the roster."),
    showdown_set: str = typer.Option("2000", "--showdown_set", "-ss", help="Showdown set to pull card data for if --pull_card_data is enabled.")
):
    """Fetch team roster from MLB Stats API"""

    try:
        roster_type_enum = RosterTypeEnum(roster_type)
    except ValueError:
        print(f"Invalid roster type: {roster_type}. Valid options are: {[rt.value for rt in RosterTypeEnum]}")
        return

    # Search for team is abbreviation provided
    if not team_id and abbreviation:
        team: Team = _mlb_api.teams.find_team_for_abbreviation(abbreviation=abbreviation, sport_id=sport_id, season=season)
        team_id = team.id

    # Fetch roster for team ID
    roster = _mlb_api.teams.get_team_roster(team_id=team_id, season=season, roster_type=roster_type_enum)
    print(f"Roster for team ID {team_id} ({roster.roster_type}):")
    
    # Get showdown card data for players in roster if option enabled
    if pull_showdown_card_data and roster.roster and len(roster.roster) > 0:
        # Initialize database connection
        db = PostgresDB()
        roster = db.add_showdown_cards_to_mlb_api_roster(roster=roster, showdown_set=showdown_set, season=season, sport_id=sport_id)
        
        # CREATE TABLE
        table = PrettyTable()
        table.field_names = ["Player", "Position", "Set", "Year", "MLB Team", "PTS"]
        for roster_slot in roster.roster:
            card = roster_slot.person.showdown_card_data
            table.add_row([
                roster_slot.person.full_name,
                card.positions_and_defense_string if card else roster_slot.position.abbreviation,
                showdown_set,
                card.year if card else "-",
                card.team.value if card else "-",
                card.points if card else "-"
            ])
        print(table)
        
@app.command("teams")
def teams(
    sport_id: int = typer.Option(1, "--sport_id", "-sp", help="MLB sport ID. Default is 1 (Major League Baseball)."),
    season: int = typer.Option(None, "--season", "-s", help="Season year to filter teams by."),
    active: bool = typer.Option(False, "--active", "-a", help="Whether to only include active teams."),
):
    """Fetch teams from MLB Stats API"""

    teams = _mlb_api.teams.get_teams(sport_id=sport_id, season=season, onlyActive=active)
    print(f"Teams for sport ID {sport_id} and season {season}:")
    table = PrettyTable()
    table.field_names = ["Team ID", "Team Name", "Abbreviation", "League", "Division", "League ID"]
    for team in teams:
        table.add_row([
            team.id,
            team.name,
            team.abbreviation,
            team.league.name if team.league else '-',
            team.division.name if team.division else '-',
            team.league.id if team.league else '-',
        ])
    print(table)

@app.command("schedule")
def schedule(
    sport_id: int = typer.Option(1, "--sport_id", "-sp", help="MLB sport ID. Default is 1 (Major League Baseball)."),
    season: int = typer.Option(None, "--season", "-s", help="Season year to filter schedule by."),
    date: str = typer.Option(None, "--date", "-d", help="Specific date to filter schedule by (YYYY-MM-DD)."),
    league_ids: str = typer.Option(None, "--league_ids", "-l", help="Comma-separated list of League IDs to filter schedule by."),
):
    """Fetch game schedule from MLB Stats API"""

    league_id_list = [int(league_id.strip()) for league_id in league_ids.split(',')] if league_ids else None
    schedule = _mlb_api_no_cache.games.get_schedule(sport_id=sport_id, season=season, date=date, league_ids=league_id_list)
    table = PrettyTable()
    table.field_names = ["Game PK", "Date", "Home Team", "Away Team", "Venue"]
    if schedule.dates:
        for day in schedule.dates:
            if day.games:
                for game in day.games:
                    table.add_row([
                        game.game_pk,
                        game.game_date,
                        game.teams.home.team.name if game.teams and game.teams.home and game.teams.home.team else '-',
                        game.teams.away.team.name if game.teams and game.teams.away and game.teams.away.team else '-',
                        game.venue.name if game.venue else '-',
                    ])
    print(table)

@app.command("cards")
def cards(
    mlb_ids: str = typer.Option(..., "--mlb_ids", "-ids", help="Comma-separated list of MLB player IDs to fetch showdown card data for."),
    is_wbc: bool = typer.Option(False, "--wbc", "-wbc", help="Whether the player IDs are for WBC players (defaults to MLB players)."),
    season: int = typer.Option(None, "--season", "-s", help="Season year to filter showdown cards by (required if --wbc is enabled)."),
    showdown_set: str = typer.Option("2000", "--showdown_set", "-ss", help="Showdown set to pull card data for."),
):
    """Fetch showdown card data for all players in a given season's rosters"""

    # Initialize database connection
    db = PostgresDB()
    mlb_id_list = [int(id.strip()) for id in mlb_ids.split(',')]
    cards_data = db.fetch_cards_by_mlb_id(mlb_ids=mlb_id_list, is_wbc=is_wbc, season=season, showdown_set=showdown_set)
    table = PrettyTable()
    table.field_names = ["MLB ID", "Player Name", "Team", "Position", "Card Year", "Card Set", "PTS"]
    for card in cards_data.values():
        table.add_row([
            card.mlb_id,
            card.name,
            card.team,
            card.positions_and_defense_string,
            card.year,
            card.set.value,
            card.points
        ])
    print(table)
    