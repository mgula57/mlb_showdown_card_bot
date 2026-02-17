import typer
from pprint import pprint
from prettytable import PrettyTable

from ...core.mlb_stats_api import MLBStatsAPI
from ...core.card.stats.normalized_player_stats import Datasource
from ...core.database.postgres_db import PostgresDB
from ...core.mlb_stats_api.models.leagues.league import SportEnum
from ...core.mlb_stats_api.models.teams.team import Team
from ...core.mlb_stats_api.models.teams.roster import Roster, RosterTypeEnum

app = typer.Typer()

@app.command("free_agents")
def free_agents(
    season: int = typer.Option(..., "--season", "-s", help="Season year to get free agents for."),
):
    """Fetch free agent players for a given season from MLB Stats API"""
    print(f"Fetching free agents for season {season}...")
    
    mlb_api = MLBStatsAPI()
    free_agents_list = mlb_api.people.get_free_agents(season=season)
    
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

    mlb_api = MLBStatsAPI()
    is_mlb = sport_id == SportEnum.MLB

    abbreviations = [abbr.strip() for abbr in abbreviations.split(',')] if abbreviations else None
    if abbreviations is None and is_mlb:
        abbreviations = ['AL', 'NL']  # Default to AL and NL for MLB if no abbreviations provided
    
    leagues = mlb_api.leagues.get_leagues(seasons=[season], sport_id=sport_id, abbreviations=abbreviations)
    
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

    mlb_api = MLBStatsAPI()

    try:
        roster_type_enum = RosterTypeEnum(roster_type)
    except ValueError:
        print(f"Invalid roster type: {roster_type}. Valid options are: {[rt.value for rt in RosterTypeEnum]}")
        return

    # Search for team is abbreviation provided
    if not team_id and abbreviation:
        team: Team = mlb_api.teams.find_team_for_abbreviation(abbreviation=abbreviation, sport_id=sport_id, season=season)
        team_id = team.id

    # Fetch roster for team ID
    roster = mlb_api.teams.get_team_roster(team_id=team_id, roster_type=roster_type_enum)
    print(f"Roster for team ID {team_id} ({roster.roster_type}):")
    
    # Get showdown card data for players in roster if option enabled
    if pull_showdown_card_data and roster.roster and len(roster.roster) > 0:
        if not showdown_set:
            print("Showdown set is required to pull card data. Please provide a showdown set using the --showdown_set option.")
            return
        
        if not season:
            print("Season year is required to pull card data. Please provide a season year using the --season option.")
            return
        

        # If WBC season, use prior season's showdown set for card data
        year = season
        if sport_id == SportEnum.INTERNATIONAL:
            year = season - 1

        print("\nPulling showdown card data for players in roster...")
        mlb_player_ids = [f"{year}-{slot.person.id}" for slot in roster.roster]
        db = PostgresDB()

        showdown_card_data = db.fetch_cards_for_player_ids(player_ids=mlb_player_ids, showdown_set=showdown_set, source=Datasource.MLB_API)
        if len(showdown_card_data) == 0:
            print("No showdown card data found for players in roster.")
        
        # CREATE TABLE
        table = PrettyTable()
        table.field_names = ["Player", "Position", "Set", "Year", "MLB Team", "PTS"]
        for roster_slot in roster.roster:
            card = showdown_card_data.get(f"{year}-{roster_slot.person.id}")
            table.add_row([
                roster_slot.person.full_name,
                card.positions_and_defense_string if card else roster_slot.position.abbreviation,
                showdown_set,
                card.year if card else "-",
                card.team.value if card else "-",
                card.points if card else "-"
            ])
        print(table)
        