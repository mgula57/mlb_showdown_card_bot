import csv
import json
from datetime import datetime

import typer

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from ...core.card.team_builder.team import Team as BuilderTeam
from ...core.database.postgres_db import PostgresDB
from ...core.simulation.models import ManagerPreference, PostseasonFormat, SeasonSimulationConfig
from ...core.simulation.reporting import SeasonReport
from ...core.simulation.season import Season
from ...core.simulation.takeover import TakeoverOptions

app = typer.Typer()


@app.callback(invoke_without_command=True)
def sim_main(
    ctx: typer.Context,
    year: int = typer.Option(..., "--year", "-y", help="The year to use."),
    set: str = typer.Option("2000", "--set", "-s", help="The showdown set to use."),
    show_game_log: bool = typer.Option(False, "--show_game_log", "-gl", help="Print Game Log Details to CLI"),
    show_standings: bool = typer.Option(False, "--show_standings", "-std", help="Show team standings"),
    show_top_players: bool = typer.Option(False, "--show_top_players", "-top", help="Show the top performing pitchers/hitters."),
    simulate_postseason: bool = typer.Option(False, "--simulate_postseason", "-ps", help="Simulate through the postseason."),
    postseason_format: str = typer.Option(PostseasonFormat.DYNAMIC.value, "--postseason_format", "-psf", help="Postseason Format. By default will use the format used in the era."),
    show_real_life_comparison: bool = typer.Option(False, "--show_real_life_comparison", "-real", help="Show Comparison to actual MLB results"),
    show_outliers: bool = typer.Option(False, "--show_outliers", "-ol", help="Show Top + and - outliers compared to MLB Results"),
    team_stats_list: str = typer.Option("", "--team_stats_list", "-tm", help="Optional team list to show stats for. Do multiple teams by adding a comma, defaults to empty list"),
    num_games: int = typer.Option(None, "--num_games", "-n", help="Number of game simulations to run"),
    pct_games: float = typer.Option(None, "--pct_games", "-pct", help="Pct of game simulations to run"),
    seed: int = typer.Option(None, "--seed", "-sd", help="Random seed for reproducible sims"),
    tournament: str = typer.Option(None, "--tournament", "-t", help="Tournament name (requires --teams_file)"),
    teams_file: str = typer.Option(None, "--teams_file", "-tf", help="Path to a JSON file with a list of team_builder Team payloads for tournament mode"),
    tournament_games: int = typer.Option(None, "--tournament_games", "-tg", help="Number of round robin games in tournament mode"),
    takeover_team_id: str = typer.Option(None, "--takeover_team_id", "-to", help="Saved team_builder team UUID to drop into the season, replacing a real club"),
    takeover_replaces: str = typer.Option(None, "--takeover_replaces", "-tr", help="Abbreviation of the club the takeover team replaces (era-correct, e.g. TBD for 1998). Defaults to the season's worst team."),
    manager_steal: int = typer.Option(3, "--manager_steal", "-mst", min=1, max=5, help="Takeover team steal aggression, 1 (rarely runs) to 5 (runs constantly). 3 = neutral. Requires --takeover_team_id."),
    manager_baserunning: int = typer.Option(3, "--manager_baserunning", "-mbr", min=1, max=5, help="Takeover team extra-base aggression, 1 (station to station) to 5 (always taking the extra base). 3 = neutral."),
    manager_hook: int = typer.Option(3, "--manager_hook", "-mhk", min=1, max=5, help="Takeover team bullpen hook, 1 (quick hook) to 5 (slow hook). 3 = neutral."),
    manager_closer: int = typer.Option(3, "--manager_closer", "-mcl", min=1, max=5, help="Takeover team closer usage, 1 (save situations only) to 5 (earlier / non-save spots). 3 = neutral."),
    export_data: bool = typer.Option(False, "--export_data", "-ex", help="Export player stats to CSV"),
    json_path: str = typer.Option(None, "--json_path", "-js", help="Write the full simulation result to a JSON file"),
    enable_injuries: bool = typer.Option(False, "--enable_injuries", "-inj", help="Enable random injuries, IL stints, and callups (real-season teams only)"),
    injury_severity: float = typer.Option(1.0, "--injury_severity", "-injs", help="Scales every player's injury hazard. 0.0 disables injuries even with --enable_injuries."),
    show_transactions: bool = typer.Option(False, "--show_transactions", "-tx", help="Show the injury/callup transaction log"),
    active_roster_size: int = typer.Option(26, "--active_roster_size", "-ars", help="Active roster size for real-season teams"),
    full_roster_size: int = typer.Option(40, "--full_roster_size", "-frs", help="Full (active + reserve) roster size for real-season teams"),
):
    """Run an MLB Showdown season simulation."""
    if ctx.invoked_subcommand is not None:
        return

    custom_teams = []
    if teams_file:
        with open(teams_file) as f:
            payloads = json.load(f)
        custom_teams = [BuilderTeam(**payload) for payload in payloads]

    takeover_team = None
    takeover_replaces_abbr = None
    manager_preference = None
    if takeover_team_id:
        with PostgresDB() as db:
            row = db.get_team(takeover_team_id, None)
        if row is None:
            typer.echo(f"ERROR: team '{takeover_team_id}' not found or not public.")
            raise typer.Exit(code=1)
        takeover_team = BuilderTeam.from_db_row(row)
        takeover_replaces_abbr = TakeoverOptions(year=year).resolve(takeover_replaces)
        manager_preference = ManagerPreference(
            steal_aggression=manager_steal, baserunning_aggression=manager_baserunning,
            bullpen_hook=manager_hook, closer_usage=manager_closer,
        )
        typer.echo(f"TAKEOVER: '{takeover_team.name}' replaces {takeover_replaces_abbr} in {year}")
        if not manager_preference.is_neutral:
            typer.echo(f"MANAGER: {manager_preference.model_dump()}")

    config = SeasonSimulationConfig(
        year=year,
        set=set,
        pct_of_games=pct_games,
        games_limit=num_games,
        simulate_postseason=simulate_postseason,
        postseason_format=PostseasonFormat(postseason_format),
        seed=seed,
        custom_teams=custom_teams,
        tournament_name=tournament,
        tournament_games=tournament_games,
        takeover_team=takeover_team,
        takeover_replaces_abbr=takeover_replaces_abbr,
        manager_preference=manager_preference,
        include_game_logs=show_game_log,
        enable_injuries=enable_injuries,
        injury_severity_multiplier=injury_severity,
        active_roster_size=active_roster_size,
        full_roster_size=full_roster_size,
    )

    progress_bar_holder = {}
    def progress(games_completed: int, total_games: int) -> None:
        if tqdm:
            if 'bar' not in progress_bar_holder:
                progress_bar_holder['bar'] = tqdm(total=total_games, desc="SIMULATING GAMES", unit="game")
            progress_bar_holder['bar'].update(1)
        elif games_completed % 100 == 0 or games_completed == total_games:
            typer.echo(f"  {games_completed}/{total_games} GAMES", nl=False)

    def status(message: str) -> None:
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f"[{timestamp}] {message}"
        if tqdm:
            tqdm.write(line)
        else:
            typer.echo(line)

    typer.echo(f"\n---- SETUP: {year} {set} -----")
    season = Season(config=config)
    result = season.simulate(
        progress_callback=progress,
        log_callback=print if show_game_log else None,
        status_callback=status,
    )
    if 'bar' in progress_bar_holder:
        progress_bar_holder['bar'].close()

    report = SeasonReport(result=result)
    report.print_summary()

    if show_standings:
        report.print_standings()
    if show_transactions:
        report.print_transactions()
    if show_top_players:
        report.print_top_players()
    if show_real_life_comparison:
        report.print_real_life_comparison()
    if show_outliers:
        report.print_outliers()
    team_stats_list_parsed = team_stats_list.replace(' ', '').split(',') if len(team_stats_list) else []
    if team_stats_list_parsed:
        report.print_team_stats(teams=team_stats_list_parsed)
    if simulate_postseason:
        report.print_postseason_bracket()

    if json_path:
        with open(json_path, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        typer.echo(f"WROTE RESULT JSON TO {json_path}")

    if export_data:
        file_name = f"season_{config.year}_set_{config.set.value}.csv"
        derived_keys = ['ba', 'obp', 'slg', 'ops', 'whip', 'era', 'so9', 'advantage_pct', 'own_chart_out_pct']
        total_keys = sorted({key for stats in result.player_stats for key in stats.totals.keys()})
        with open(file_name, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'team', 'player_type', 'position', 'points', 'command'] + total_keys + derived_keys)
            for stats in result.player_stats:
                writer.writerow(
                    [stats.id, stats.name, stats.team, stats.player_type.value if stats.player_type else '', stats.position, stats.points, stats.command]
                    + [stats.totals.get(key, 0) for key in total_keys]
                    + [getattr(stats, key) for key in derived_keys]
                )
        typer.echo(f"WROTE PLAYER STATS TO {file_name}")

    report.print_runtime()
