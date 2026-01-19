import typer
from pprint import pprint
from prettytable import PrettyTable

from ...core.mlb_stats_api.clients.people_client import PeopleClient

app = typer.Typer()

@app.command("free_agents")
def free_agents(
    season: int = typer.Option(..., "--season", "-s", help="Season year to get free agents for."),
):
    """Fetch free agent players for a given season from MLB Stats API"""
    print(f"Fetching free agents for season {season}...")
    people_client = PeopleClient()
    free_agents_list = people_client.get_free_agents(season=season)
    
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

    