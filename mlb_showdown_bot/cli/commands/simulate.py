import typer
from typing import Optional

app = typer.Typer()

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@app.callback(invoke_without_command=True)
def simulate(
    ctx: typer.Context,

    # Team selection — pick one: demo OR real teams
    demo: bool = typer.Option(False, "--demo", help="Use built-in demo cards (no API required)."),
    away: Optional[str] = typer.Option(None, "--away", help="Away team abbreviation (e.g. NYY). Requires --year."),
    home: Optional[str] = typer.Option(None, "--home", help="Home team abbreviation (e.g. BOS). Requires --year."),
    year: Optional[int] = typer.Option(None, "--year", help="Season year for card generation."),

    # Game settings
    games: int = typer.Option(1, "--games", "-g", help="Number of games to simulate."),
    set_name: str = typer.Option("EXPANDED", "--set", "-s", help="Showdown set: EXPANDED, CLASSIC, 2003, 2004, 2005 …"),
    innings: int = typer.Option(9, "--innings", "-i", help="Innings per game."),
    mistake_pitch: bool = typer.Option(False, "--mistake-pitch", "-mp", help="Enable mistake pitch rule (d24 chart roll)."),
    stolen_base_cap: Optional[int] = typer.Option(None, "--sb-cap", help="Max stolen bases per player per game."),
    fatigue_outs: Optional[int] = typer.Option(18, "--fatigue", "-f", help="Hook starter after this many outs (default 18 = 6 IP). 0 = no limit."),

    # Output
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show per-inning line score for each game."),
):
    """Simulate one or more MLB Showdown games and display results.

    Examples:\n
      showdown_bot simulate --demo\n
      showdown_bot simulate --demo --games 100\n
      showdown_bot simulate --away NYY --home BOS --year 2025\n
      showdown_bot simulate --demo --mistake-pitch --innings 7\n
    """
    if ctx.invoked_subcommand is not None:
        return
    from ...core.card.sets import Set
    from ...core.simulation import ShowdownGame, SimulationRuleset
    from ...core.simulation.team import ShowdownTeam

    # --- Validate args ---
    if not demo and (away is None or home is None):
        typer.echo("Error: provide --demo OR both --away and --home (with --year).", err=True)
        raise typer.Exit(1)
    if not demo and year is None:
        typer.echo("Error: --year is required when specifying --away / --home.", err=True)
        raise typer.Exit(1)

    # --- Build ruleset ---
    try:
        game_set = Set(set_name)
    except ValueError:
        valid = ", ".join(s.value for s in Set)
        typer.echo(f"Error: unknown set '{set_name}'. Valid options: {valid}", err=True)
        raise typer.Exit(1)

    ruleset = SimulationRuleset(
        game_set=game_set,
        innings=innings,
        mistake_pitch=mistake_pitch,
        stolen_base_cap=stolen_base_cap,
        starter_fatigue_outs=fatigue_outs if fatigue_outs else None,
    )

    # --- Build teams ---
    if demo:
        away_team, home_team = _build_demo_teams()
        away_name, home_name = "Yankees All-Stars", "Red Sox All-Stars"
    else:
        typer.echo(f"Building team cards for {away.upper()} and {home.upper()} ({year}) …")
        away_team, home_team = _build_real_teams(away, home, year, game_set)
        away_name = away_team.name if isinstance(away_team, ShowdownTeam) else away.upper()
        home_name = home_team.name if isinstance(home_team, ShowdownTeam) else home.upper()

    # --- Run simulation(s) ---
    results = []
    for i in range(games):
        if games > 1 and (i + 1) % 10 == 0:
            typer.echo(f"  … {i + 1}/{games} games completed")
        game = ShowdownGame.new(away=away_team, home=home_team, ruleset=ruleset)
        results.append(game.simulate_to_end())

    # --- Display ---
    W = 52
    sep = "=" * W
    div = "-" * W

    if games == 1:
        r = results[0]
        _print_box_score(r, away_name, home_name, ruleset, W, sep, div, verbose=verbose)
    else:
        _print_series_summary(results, away_name, home_name, ruleset, games, W, sep, div, verbose=verbose)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_box_score(r, away_name, home_name, ruleset, W, sep, div, verbose=False):
    from ...core.card.chart import ChartCategory

    typer.echo()
    typer.echo(sep)
    typer.echo(f"  {away_name} @ {home_name}")
    _print_ruleset_line(ruleset)
    typer.echo(f"  FINAL:  {away_name} {r.away_score},  {home_name} {r.home_score}  "
               f"({'AWAY' if r.winner == 'away' else 'HOME' if r.winner == 'home' else 'TIE'} wins)")
    typer.echo(sep)

    # Line score
    away_inn = r.score_by_inning(is_away=True)
    home_inn = r.score_by_inning(is_away=False)
    n = max(len(away_inn), len(home_inn))
    away_hits = sum(h.hits for h in r.innings if h.is_top)
    home_hits = sum(h.hits for h in r.innings if not h.is_top)

    hdr = f"  {'TEAM':<24}" + "".join(f"{i+1:>3}" for i in range(n)) + f"  {'R':>3}{'H':>4}"
    typer.echo()
    typer.echo(hdr)
    typer.echo(div)
    typer.echo(f"  {away_name:<24}" + "".join(f"{x:>3}" for x in away_inn) + f"  {r.away_score:>3}{away_hits:>4}")
    typer.echo(f"  {home_name:<24}" + "".join(f"{x:>3}" for x in home_inn) + f"  {r.home_score:>3}{home_hits:>4}")

    # Batting
    for box, team_name in [(r.away_box, away_name), (r.home_box, home_name)]:
        batters = [p for p in box if p.outs_recorded is None]
        if not batters:
            continue
        typer.echo()
        typer.echo(f"  {team_name} — Batting")
        typer.echo(div)
        typer.echo(f"  {'Player':<22} {'AB':>3} {'H':>3} {'2B':>3} {'3B':>3} {'HR':>3} {'BB':>3} {'K':>3} {'RBI':>3} {'SB':>3}")
        typer.echo(div)
        for p in sorted(batters, key=lambda x: x.ab, reverse=True):
            typer.echo(
                f"  {p.name:<22} {p.ab:>3} {p.hits:>3} {p.doubles:>3} "
                f"{p.triples:>3} {p.home_runs:>3} {p.walks:>3} {p.strikeouts:>3} "
                f"{p.rbi:>3} {p.stolen_bases:>3}"
            )

    # Pitching
    for box, team_name in [(r.away_box, away_name), (r.home_box, home_name)]:
        pitchers = [p for p in box if p.outs_recorded is not None]
        if not pitchers:
            continue
        typer.echo()
        typer.echo(f"  {team_name} — Pitching")
        typer.echo(div)
        typer.echo(f"  {'Player':<22} {'IP':>5} {'R':>4} {'BB':>4} {'K':>4}")
        typer.echo(div)
        for p in pitchers:
            typer.echo(
                f"  {p.name:<22} {p.innings_pitched or 0.0:>5.1f} "
                f"{p.runs_allowed:>4} {p.pitcher_walks:>4} {p.pitcher_strikeouts:>4}"
            )

    typer.echo()
    typer.echo(sep)
    typer.echo()


def _print_series_summary(results, away_name, home_name, ruleset, games, W, sep, div, verbose=False):
    away_wins = sum(1 for r in results if r.winner == 'away')
    home_wins = sum(1 for r in results if r.winner == 'home')
    ties = games - away_wins - home_wins

    away_runs = [r.away_score for r in results]
    home_runs = [r.home_score for r in results]
    avg_away = sum(away_runs) / games
    avg_home = sum(home_runs) / games

    typer.echo()
    typer.echo(sep)
    typer.echo(f"  {away_name} @ {home_name}  — {games}-game series")
    _print_ruleset_line(ruleset)
    typer.echo(sep)
    typer.echo()

    # Win record
    typer.echo(f"  {'Team':<26} {'W':>4} {'L':>4} {'T':>4}  {'Win%':>6}  {'Avg R':>6}")
    typer.echo(div)
    typer.echo(f"  {away_name:<26} {away_wins:>4} {home_wins:>4} {ties:>4}  {away_wins/games:>6.3f}  {avg_away:>6.2f}")
    typer.echo(f"  {home_name:<26} {home_wins:>4} {away_wins:>4} {ties:>4}  {home_wins/games:>6.3f}  {avg_home:>6.2f}")
    typer.echo()

    # Score distribution
    _print_run_distribution("Away", away_runs, div)
    typer.echo()
    _print_run_distribution("Home", home_runs, div)

    if verbose:
        typer.echo()
        typer.echo(f"  {'#':>4}  {'Away':>6}  {'Home':>6}  Winner")
        typer.echo(div)
        for i, r in enumerate(results, 1):
            winner_label = "AWAY" if r.winner == "away" else "HOME" if r.winner == "home" else "TIE "
            typer.echo(f"  {i:>4}  {r.away_score:>6}  {r.home_score:>6}  {winner_label}")

    typer.echo()
    typer.echo(sep)
    typer.echo()


def _print_run_distribution(label: str, run_list: list[int], div: str):
    from collections import Counter
    counts = Counter(run_list)
    max_runs = max(run_list)
    typer.echo(f"  {label} runs distribution:")
    typer.echo(div)
    for r in range(max_runs + 1):
        n = counts.get(r, 0)
        pct = n / len(run_list)
        bar = "█" * int(pct * 30)
        typer.echo(f"  {r:>3} runs: {n:>4}x  {pct:>5.1%}  {bar}")


def _print_ruleset_line(ruleset):
    parts = [f"Set: {ruleset.game_set.value}", f"Innings: {ruleset.innings}"]
    if ruleset.starter_fatigue_outs is not None:
        parts.append(f"Fatigue: {ruleset.starter_fatigue_outs} outs")
    if ruleset.mistake_pitch:
        parts.append("Mistake Pitch: ON")
    if ruleset.stolen_base_cap is not None:
        parts.append(f"SB Cap: {ruleset.stolen_base_cap}")
    typer.echo(f"  {' | '.join(parts)}")


# ---------------------------------------------------------------------------
# Team builders
# ---------------------------------------------------------------------------

def _build_demo_teams():
    """Build two teams from minimal mock cards — no API or stats required."""
    from ...core.card.chart import Chart, ChartCategory
    from ...core.card.showdown_player_card import ShowdownPlayerCard
    from ...core.shared.player_position import PlayerSubType, PlayerType

    CC = ChartCategory

    # ---------------------------------------------------------------
    # Chart templates — all 20 slots filled, tuned for realistic
    # EXPANDED-set scoring (~6-10 runs/team/game).
    # Pitcher charts: ~80% outs; hitter charts vary by profile.
    # ---------------------------------------------------------------

    def _starter_chart(command):
        """Good starter: 80% outs, 1 BB, 3 hits (no HR)."""
        results = {
            1: CC.PU,
            2: CC.SO, 3: CC.SO, 4: CC.SO, 5: CC.SO,
            6: CC.GB, 7: CC.GB, 8: CC.GB, 9: CC.GB, 10: CC.GB, 11: CC.GB,
            12: CC.FB, 13: CC.FB, 14: CC.FB, 15: CC.FB, 16: CC.FB,
            17: CC.BB,
            18: CC._1B, 19: CC._1B,
            20: CC._2B,
        }  # outs=16, BB=1, hits=3
        return _build_chart(command, is_pitcher=True, results=results)

    def _reliever_chart(command):
        """Closer: 80% outs, heavier on Ks, 1 BB, 3 hits."""
        results = {
            1: CC.SO, 2: CC.SO, 3: CC.SO, 4: CC.SO, 5: CC.SO, 6: CC.SO,
            7: CC.GB, 8: CC.GB, 9: CC.GB, 10: CC.GB, 11: CC.GB,
            12: CC.FB, 13: CC.FB, 14: CC.FB, 15: CC.FB,
            16: CC.BB,
            17: CC._1B, 18: CC._1B, 19: CC._1B,
            20: CC._2B,
        }  # outs=16, BB=1, hits=4
        return _build_chart(command, is_pitcher=True, results=results)

    def _contact_chart(command):
        """Contact hitter: high 1B, 1 HR, few strikeouts."""
        results = {
            1: CC.SO, 2: CC.SO, 3: CC.SO,
            4: CC.GB, 5: CC.GB,
            6: CC.FB, 7: CC.FB,
            8: CC.BB, 9: CC.BB, 10: CC.BB,
            11: CC._1B, 12: CC._1B, 13: CC._1B, 14: CC._1B, 15: CC._1B, 16: CC._1B,
            17: CC._2B, 18: CC._2B,
            19: CC._3B,
            20: CC.HR,
        }  # outs=7, BB=3, hits=10
        return _build_chart(command, is_pitcher=False, results=results)

    def _balanced_chart(command):
        """Average hitter: balanced mix, 1 HR."""
        results = {
            1: CC.SO, 2: CC.SO, 3: CC.SO, 4: CC.SO,
            5: CC.GB, 6: CC.GB,
            7: CC.FB, 8: CC.FB, 9: CC.FB,
            10: CC.BB, 11: CC.BB,
            12: CC._1B, 13: CC._1B, 14: CC._1B, 15: CC._1B, 16: CC._1B,
            17: CC._1B_PLUS,
            18: CC._2B, 19: CC._2B,
            20: CC.HR,
        }  # outs=9, BB=2, hits=9
        return _build_chart(command, is_pitcher=False, results=results)

    def _power_chart(command):
        """Power hitter: more extra bases, 2 HR."""
        results = {
            1: CC.SO, 2: CC.SO, 3: CC.SO,
            4: CC.GB, 5: CC.GB,
            6: CC.FB, 7: CC.FB,
            8: CC.BB, 9: CC.BB, 10: CC.BB,
            11: CC._1B, 12: CC._1B, 13: CC._1B, 14: CC._1B,
            15: CC._1B_PLUS,
            16: CC._2B, 17: CC._2B, 18: CC._2B,
            19: CC.HR, 20: CC.HR,
        }  # outs=7, BB=3, hits=10
        return _build_chart(command, is_pitcher=False, results=results)

    def _slugger_chart(command):
        """Cleanup slugger: fewer 1B, 3 HR, lots of XBH."""
        results = {
            1: CC.SO, 2: CC.SO, 3: CC.SO,
            4: CC.GB,
            5: CC.FB, 6: CC.FB,
            7: CC.BB, 8: CC.BB, 9: CC.BB,
            10: CC._1B, 11: CC._1B, 12: CC._1B,
            13: CC._1B_PLUS,
            14: CC._2B, 15: CC._2B, 16: CC._2B, 17: CC._2B,
            18: CC.HR, 19: CC.HR, 20: CC.HR,
        }  # outs=6, BB=3, hits=11
        return _build_chart(command, is_pitcher=False, results=results)

    def _build_chart(command, is_pitcher, results):
        c = object.__new__(Chart)
        c.__dict__.update({'command': command, 'is_pitcher': is_pitcher, 'results': results})
        c.__pydantic_fields_set__ = frozenset({'command', 'is_pitcher', 'results'})
        c.__pydantic_extra__ = None
        c.__pydantic_private__ = None
        return c

    def _card(name, ptype, subtype, chart):
        card = object.__new__(ShowdownPlayerCard)
        card.__dict__.update({'name': name, 'player_type': ptype, 'player_sub_type': subtype, 'chart': chart})
        card.__pydantic_fields_set__ = frozenset({'name', 'player_type', 'player_sub_type', 'chart'})
        card.__pydantic_extra__ = None
        card.__pydantic_private__ = None
        return card

    P, H = PlayerType.PITCHER, PlayerType.HITTER
    SP, RP, POS = PlayerSubType.STARTING_PITCHER, PlayerSubType.RELIEF_PITCHER, PlayerSubType.POSITION_PLAYER

    away = [
        # Pitchers first: starter, then reliever
        _card("G. Cole",       P, SP,  _starter_chart(5)),
        _card("A. Holmes",     P, RP,  _reliever_chart(5)),
        # Batting order
        _card("D. Jeter",      H, POS, _contact_chart(9)),
        _card("B. Ruth",       H, POS, _slugger_chart(10)),
        _card("L. Gehrig",     H, POS, _slugger_chart(10)),
        _card("A. Rodriguez",  H, POS, _power_chart(10)),
        _card("M. Mantle",     H, POS, _power_chart(9)),
        _card("Y. Berra",      H, POS, _balanced_chart(8)),
        _card("R. Jackson",    H, POS, _power_chart(9)),
        _card("P. O'Neill",    H, POS, _contact_chart(9)),
        _card("W. Ford",       H, POS, _balanced_chart(7)),
    ]
    home = [
        _card("P. Martinez",   P, SP,  _starter_chart(6)),
        _card("K. Foulke",     P, RP,  _reliever_chart(5)),
        _card("T. Williams",   H, POS, _slugger_chart(11)),
        _card("D. Ortiz",      H, POS, _slugger_chart(10)),
        _card("C. Yastrzemski",H, POS, _power_chart(9)),
        _card("M. Ramirez",    H, POS, _power_chart(10)),
        _card("J. Ramirez",    H, POS, _balanced_chart(9)),
        _card("N. Garciaparra",H, POS, _contact_chart(9)),
        _card("J. Damon",      H, POS, _contact_chart(8)),
        _card("J. Varitek",    H, POS, _balanced_chart(8)),
        _card("R. Clemens",    H, POS, _balanced_chart(7)),
    ]
    return away, home


def _build_real_teams(away_abbr: str, home_abbr: str, year: int, game_set):
    from ...core.card.sets import Era
    from ...core.mlb_stats_api import TeamsClient
    from ...core.simulation.team_builder import build_showdown_team

    era = Era.PITCH_CLOCK  # sensible default for recent seasons

    client = TeamsClient()
    away_info = client.find_team_for_abbreviation(away_abbr)
    home_info = client.find_team_for_abbreviation(home_abbr)

    if not away_info:
        typer.echo(f"Error: team '{away_abbr}' not found.", err=True)
        raise typer.Exit(1)
    if not home_info:
        typer.echo(f"Error: team '{home_abbr}' not found.", err=True)
        raise typer.Exit(1)

    typer.echo(f"  Generating cards for {away_info.name} …")
    away_team = build_showdown_team(team_id=away_info.id, season=year, game_set=game_set, era=era)
    typer.echo(f"  Generating cards for {home_info.name} …")
    home_team = build_showdown_team(team_id=home_info.id, season=year, game_set=game_set, era=era)

    typer.echo(f"  {away_team.name}: {len(away_team.batting_order)} batters, {len(away_team.rotation)} pitchers")
    typer.echo(f"  {home_team.name}: {len(home_team.batting_order)} batters, {len(home_team.rotation)} pitchers")

    return away_team, home_team
