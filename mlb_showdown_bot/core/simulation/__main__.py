import argparse
import csv
import json
import warnings
from datetime import datetime

from dotenv import load_dotenv

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from ..card.team_builder.team import Team as BuilderTeam
from .models import PostseasonFormat, SeasonSimulationConfig
from .reporting import SeasonReport
from .season import Season

load_dotenv()
warnings.simplefilter(action='ignore', category=UserWarning)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an MLB Showdown Simulation")
    parser.add_argument('-y','--year', help='The year to use.', type=int, required=True)
    parser.add_argument('-s', '--set', help='The showdown set to use.', default='2000')
    parser.add_argument('-gl', '--show_game_log', action='store_true', help='Print Game Log Details to CLI')
    parser.add_argument('-std', '--show_standings', action='store_true', help='Show team standings')
    parser.add_argument('-top', '--show_top_players', action='store_true', help='Show the top performing pitchers/hitters.')
    parser.add_argument('-ps', '--simulate_postseason', action='store_true', help='Simulate through the postseason.')
    parser.add_argument('-psf', '--postseason_format', help='Postseason Format. By default will use the format used in the era.', default=PostseasonFormat.DYNAMIC.value)
    parser.add_argument('-real', '--show_real_life_comparison', action='store_true', help='Show Comparison to actual MLB results')
    parser.add_argument('-ol', '--show_outliers', action='store_true', help='Show Top + and - outliers compared to MLB Results')
    parser.add_argument('-tm','--team_stats_list', help='Optional team list to show stats for. Do multiple teams by adding a comma, defaults to empty list', default='', required=False)
    parser.add_argument('-n', '--num_games', help='Number of game simulations to run', type=int, default=None)
    parser.add_argument('-pct', '--pct_games', help='Pct of game simulations to run', type=float, default=None)
    parser.add_argument('-sd', '--seed', help='Random seed for reproducible sims', type=int, default=None)
    parser.add_argument('-t', '--tournament', help='Tournament name (requires --teams_file)', default=None)
    parser.add_argument('-tf', '--teams_file', help='Path to a JSON file with a list of team_builder Team payloads for tournament mode', default=None)
    parser.add_argument('-tg', '--tournament_games', help='Number of round robin games in tournament mode', type=int, default=None)
    parser.add_argument('-ex', '--export_data', action='store_true', help='Export player stats to CSV')
    parser.add_argument('-js', '--json_path', help='Write the full simulation result to a JSON file', default=None)
    parser.add_argument('-inj', '--enable_injuries', action='store_true', help='Enable random injuries, IL stints, and callups (real-season teams only)')
    parser.add_argument('-injs', '--injury_severity', help="Scales every player's injury hazard. 0.0 disables injuries even with --enable_injuries.", type=float, default=1.0)
    parser.add_argument('-tx', '--show_transactions', action='store_true', help='Show the injury/callup transaction log')
    parser.add_argument('-ars', '--active_roster_size', help='Active roster size for real-season teams', type=int, default=26)
    parser.add_argument('-frs', '--full_roster_size', help='Full (active + reserve) roster size for real-season teams', type=int, default=40)
    return parser.parse_args()


def main():
    """ Executed when running as a script """

    args = parse_args()

    custom_teams = []
    if args.teams_file:
        with open(args.teams_file) as f:
            payloads = json.load(f)
        custom_teams = [BuilderTeam(**payload) for payload in payloads]

    config = SeasonSimulationConfig(
        year=args.year,
        set=args.set,
        pct_of_games=args.pct_games,
        games_limit=args.num_games,
        simulate_postseason=args.simulate_postseason,
        postseason_format=PostseasonFormat(args.postseason_format),
        seed=args.seed,
        custom_teams=custom_teams,
        tournament_name=args.tournament,
        tournament_games=args.tournament_games,
        include_game_logs=args.show_game_log,
        enable_injuries=args.enable_injuries,
        injury_severity_multiplier=args.injury_severity,
        active_roster_size=args.active_roster_size,
        full_roster_size=args.full_roster_size,
    )

    # WIRE CLI PROGRESS + GAME LOG + SETUP STATUS OUTPUT INTO THE PRINT-FREE CORE
    progress_bar_holder = {}
    def progress(games_completed: int, total_games: int) -> None:
        if tqdm:
            if 'bar' not in progress_bar_holder:
                progress_bar_holder['bar'] = tqdm(total=total_games, desc="SIMULATING GAMES", unit="game")
            progress_bar_holder['bar'].update(1)
        elif games_completed % 100 == 0 or games_completed == total_games:
            print(f"  {games_completed}/{total_games} GAMES", end='\r')

    def status(message: str) -> None:
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f"[{timestamp}] {message}"
        if tqdm:
            tqdm.write(line)
        else:
            print(line)

    print(f"\n---- SETUP: {args.year} {args.set} -----")
    season = Season(config=config)
    result = season.simulate(
        progress_callback=progress,
        log_callback=print if args.show_game_log else None,
        status_callback=status,
    )
    if 'bar' in progress_bar_holder:
        progress_bar_holder['bar'].close()

    report = SeasonReport(result=result)
    report.print_summary()

    if args.show_standings:
        report.print_standings()
    if args.show_transactions:
        report.print_transactions()
    if args.show_top_players:
        report.print_top_players()
    if args.show_real_life_comparison:
        report.print_real_life_comparison()
    if args.show_outliers:
        report.print_outliers()
    team_stats_list = args.team_stats_list.replace(' ', '').split(',') if len(args.team_stats_list) else []
    if team_stats_list:
        report.print_team_stats(teams=team_stats_list)
    if args.simulate_postseason:
        report.print_postseason_bracket()

    if args.json_path:
        with open(args.json_path, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"WROTE RESULT JSON TO {args.json_path}")

    if args.export_data:
        file_name = f"season_{config.year}_set_{config.set.value}.csv"
        derived_keys = ['ba', 'obp', 'slg', 'ops', 'whip', 'era', 'so9']
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
        print(f"WROTE PLAYER STATS TO {file_name}")

    report.print_runtime()


if __name__ == "__main__":
    main()
