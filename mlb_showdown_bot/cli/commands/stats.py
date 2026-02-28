import typer
from prettytable import PrettyTable

from ...core.data.replacement_season_averages import (
    get_replacement_hitting_avgs,
    get_replacement_pitching_avgs,
    convert_replacement_stats_to_pa_basis,
    build_replacement_level_stats_for_card,
    Position,
)
from ...core.card.showdown_player_card import ShowdownPlayerCard
from ...core.card.stats.stats_period import StatsPeriod

app = typer.Typer()


def _parse_years_input(years: list[int], years_csv: str | None) -> list[int]:
    parsed_years = list(years)
    if years_csv:
        for value in years_csv.split(","):
            cleaned = value.strip()
            if not cleaned:
                continue
            parsed_years.append(int(cleaned))
    return sorted(set(parsed_years))

def _print_replacement_card(stats: dict, season_year: int, role: str, pa: float, card_set: str) -> None:
    card_name = f"Replacement {role.title()} {season_year}"
    type = "Pitcher" if role == "pitcher" else "Hitter"
    positions = None if role == "pitcher" else [Position._2B, Position.LF]  # Default to DH for hitters, unless positions are specified
    card_stats = build_replacement_level_stats_for_card(original_stats=stats, year=season_year, player_type=type, pa_basis=pa, positions=positions)
    ShowdownPlayerCard(
        name=card_name,
        year=str(season_year),
        set=card_set,
        era="DYNAMIC",
        stats_period=StatsPeriod(year=str(season_year)),
        stats=card_stats,
        print_to_cli=True,
    )


@app.command("replacement")
def replacement(
    year: list[int] = typer.Option([], "--year", "-y", help="One or more seasons. Repeat option for multiple years."),
    years: str | None = typer.Option(None, "--years", "-ys", help="Comma-separated years (e.g. 2022,2023,2024)."),
    pa: float = typer.Option(600.0, "--pa", "-pa", help="PA basis for replacement gap (e.g. 600 or 400)."),
    runs_below_avg: float = typer.Option(20.0, "--runs_below_avg", "-rba", help="Runs below average on the given PA basis."),
    role: str = typer.Option("both", "--role", "-role", help="Role to display: hitter, pitcher, or both."),
    show_cards: bool = typer.Option(False, "--show_cards", "-sc", help="Whether to show example replacement-level cards for each season."),
    card_set: str = typer.Option("2000", "--card_set", "-cs", help="Showdown set to use when printing replacement cards (e.g. 2000-2005, CLASSIC, EXPANDED)."),
):
    """Show replacement-level season averages in a PrettyTable."""

    try:
        selected_years = _parse_years_input(years=year, years_csv=years)
    except ValueError:
        typer.echo("Invalid --years value. Use comma-separated integers only.")
        raise typer.Exit(code=1)

    if not selected_years:
        typer.echo("Please provide at least one year via --year/-y or --years/-ys.")
        raise typer.Exit(code=1)

    if pa <= 0:
        typer.echo("--pa must be greater than 0.")
        raise typer.Exit(code=1)
    
    pitcher_pa = pa / 2.25 if role == "both" else pa  # If showing both, use a lower PA basis for pitchers to reflect typical IP/PA ratio

    role_normalized = role.strip().lower()
    if role_normalized not in {"hitter", "pitcher", "both"}:
        typer.echo("Invalid --role. Use one of: hitter, pitcher, both.")
        raise typer.Exit(code=1)

    show_hitter = role_normalized in {"hitter", "both"}
    show_pitcher = role_normalized in {"pitcher", "both"}
    hitter_card_payloads: list[tuple[int, dict]] = []
    pitcher_card_payloads: list[tuple[int, dict]] = []

    hitter_table = PrettyTable()
    hitter_table.field_names = [
        "Year",
        "PA Basis",
        "Runs Below Avg",
        "OBP",
        "SLG",
        "OPS",
        "BA",
        "R/G",
        "1B",
        "2B",
        "3B",
        "HR",
        "BB",
        "SO",
    ]

    pitcher_table = PrettyTable()
    pitcher_table.field_names = [
        "Year",
        "PA Basis",
        "Runs Above Avg",
        "ERA",
        "WHIP",
        "SO9",
        "OBP",
        "SLG",
        "OPS",
        "BA",
        "R/G",
        "1B",
        "2B",
        "3B",
        "HR",
        "BB",
        "SO",
    ]
    for season_year in selected_years:
        if show_hitter:
            try:
                hitter_stats_600 = get_replacement_hitting_avgs(
                    year=season_year,
                    runs_below_avg=runs_below_avg,
                )
                hitter_stats = convert_replacement_stats_to_pa_basis(stats=hitter_stats_600, pa_basis=pa)
            except (KeyError, ValueError) as error:
                typer.echo(f"Skipping hitter {season_year}: {error}")
            else:
                hitter_table.add_row([
                    season_year,
                    pa,
                    runs_below_avg,
                    hitter_stats.get("OBP", "-"),
                    hitter_stats.get("SLG", "-"),
                    hitter_stats.get("OPS", "-"),
                    hitter_stats.get("BA", "-"),
                    hitter_stats.get("R/G", "-"),
                    hitter_stats.get("1B", "-"),
                    hitter_stats.get("2B", "-"),
                    hitter_stats.get("3B", "-"),
                    hitter_stats.get("HR", "-"),
                    hitter_stats.get("BB", "-"),
                    hitter_stats.get("SO", "-"),
                ])
                if show_cards:
                    hitter_card_payloads.append((season_year, hitter_stats))

        if show_pitcher:
            try:
                pitcher_stats_600 = get_replacement_pitching_avgs(
                    year=season_year,
                    runs_above_avg=runs_below_avg,
                )
                
                pitcher_stats = convert_replacement_stats_to_pa_basis(stats=pitcher_stats_600, pa_basis=pitcher_pa)  # Convert hitting PA basis to pitching IP basis (roughly)
                
            except (KeyError, ValueError) as error:
                typer.echo(f"Skipping pitcher {season_year}: {error}")
            else:
                pitcher_table.add_row([
                    season_year,
                    pitcher_pa,
                    runs_below_avg,
                    pitcher_stats.get("ERA", "-"),
                    pitcher_stats.get("WHIP", "-"),
                    pitcher_stats.get("SO9", "-"),
                    pitcher_stats.get("OBP", "-"),
                    pitcher_stats.get("SLG", "-"),
                    pitcher_stats.get("OPS", "-"),
                    pitcher_stats.get("BA", "-"),
                    pitcher_stats.get("R/G", "-"),
                    pitcher_stats.get("1B", "-"),
                    pitcher_stats.get("2B", "-"),
                    pitcher_stats.get("3B", "-"),
                    pitcher_stats.get("HR", "-"),
                    pitcher_stats.get("BB", "-"),
                    pitcher_stats.get("SO", "-"),
                ])
                if show_cards:
                    pitcher_card_payloads.append((season_year, pitcher_stats))

    if len(hitter_table.rows) == 0 and len(pitcher_table.rows) == 0:
        typer.echo("No rows to display.")
        raise typer.Exit(code=1)

    if show_hitter and len(hitter_table.rows) > 0:
        typer.echo("\nHITTER REPLACEMENT")
        typer.echo(hitter_table)

    if show_pitcher and len(pitcher_table.rows) > 0:
        typer.echo("\nPITCHER REPLACEMENT")
        typer.echo(pitcher_table)

    if show_cards:
        if show_hitter and hitter_card_payloads:
            typer.echo("\nHITTER REPLACEMENT CARDS")
            for season_year, hitter_stats in hitter_card_payloads:
                typer.echo(f"\n{season_year} Replacement Hitter Card")
                try:
                    _print_replacement_card(stats=hitter_stats, season_year=season_year, role="hitter", pa=pa, card_set=card_set)
                except Exception as error:
                    typer.echo(f"Failed to print hitter card for {season_year}: {error}")

        if show_pitcher and pitcher_card_payloads:
            typer.echo("\nPITCHER REPLACEMENT CARDS")
            for season_year, pitcher_stats in pitcher_card_payloads:
                typer.echo(f"\n{season_year} Replacement Pitcher Card")
                try:
                    _print_replacement_card(stats=pitcher_stats, season_year=season_year, role="pitcher", pa=pitcher_pa, card_set=card_set)
                except Exception as error:
                    typer.echo(f"Failed to print pitcher card for {season_year}: {error}")

