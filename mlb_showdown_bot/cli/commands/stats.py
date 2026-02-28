import typer
from prettytable import PrettyTable

from ...core.data.replacement_season_averages import get_replacement_hitting_avgs, get_replacement_pitching_avgs

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


@app.command("replacement")
def replacement(
	year: list[int] = typer.Option([], "--year", "-y", help="One or more seasons. Repeat option for multiple years."),
	years: str | None = typer.Option(None, "--years", "-ys", help="Comma-separated years (e.g. 2022,2023,2024)."),
	pa: float = typer.Option(600.0, "--pa", "-pa", help="PA basis for replacement gap (e.g. 600 or 400)."),
	runs_below_avg: float = typer.Option(20.0, "--runs_below_avg", "-rba", help="Runs below average on the given PA basis."),
	role: str = typer.Option("both", "--role", "-role", help="Role to display: hitter, pitcher, or both."),
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

	role_normalized = role.strip().lower()
	if role_normalized not in {"hitter", "pitcher", "both"}:
		typer.echo("Invalid --role. Use one of: hitter, pitcher, both.")
		raise typer.Exit(code=1)

	show_hitter = role_normalized in {"hitter", "both"}
	show_pitcher = role_normalized in {"pitcher", "both"}

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
				hitter_stats = get_replacement_hitting_avgs(
					year=season_year,
					runs_below_avg=runs_below_avg,
					pa_basis=pa,
				)
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

		if show_pitcher:
			try:
				pitcher_stats = get_replacement_pitching_avgs(
					year=season_year,
					runs_above_avg=runs_below_avg,
					pa_basis=pa,
				)
			except (KeyError, ValueError) as error:
				typer.echo(f"Skipping pitcher {season_year}: {error}")
			else:
				pitcher_table.add_row([
					season_year,
					pa,
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

	if len(hitter_table.rows) == 0 and len(pitcher_table.rows) == 0:
		typer.echo("No rows to display.")
		raise typer.Exit(code=1)

	if show_hitter and len(hitter_table.rows) > 0:
		typer.echo("\nHITTER REPLACEMENT")
		typer.echo(hitter_table)

	if show_pitcher and len(pitcher_table.rows) > 0:
		typer.echo("\nPITCHER REPLACEMENT")
		typer.echo(pitcher_table)

