import json
import sys
from pathlib import Path
from typing import Optional

import typer
from prettytable import PrettyTable

from ...core.database.postgres_db import PostgresDB
from ...core.card.team_builder import Team, TeamSource
from ...core.card.team_builder.autofill import BUCKET_QUERY_FILTERS, autofill_team

app = typer.Typer()


@app.command("upload")
def upload_teams(
    file: Path = typer.Option(..., "--file", "-f", help="Path to JSON file containing a list of team objects"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Validate and print teams without writing to DB"),
):
    """Bulk import official or ASG teams from a JSON file."""
    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        raw = json.loads(file.read_text())
    except json.JSONDecodeError as exc:
        typer.echo(f"Error parsing JSON: {exc}", err=True)
        raise typer.Exit(1)

    if not isinstance(raw, list):
        typer.echo("Error: JSON file must contain a list of team objects", err=True)
        raise typer.Exit(1)

    teams: list[Team] = []
    for i, entry in enumerate(raw):
        try:
            teams.append(Team(**entry))
        except Exception as exc:
            typer.echo(f"Error parsing team at index {i}: {exc}", err=True)
            raise typer.Exit(1)

    typer.echo(f"Parsed {len(teams)} team(s).")

    if dry_run:
        for t in teams:
            typer.echo(f"  [{t.source.value}] {t.name} ({t.abbreviation})  roster={len(t.roster)}")
        typer.echo("Dry run — no changes written.")
        return

    db = PostgresDB()
    db.build_user_teams_table()
    uploaded = 0
    for t in teams:
        payload = t.to_db_dict()
        if t.team_id:
            payload['team_id'] = t.team_id
        team_id = db.admin_upsert_team(payload)
        typer.echo(f"  Upserted: {t.name} ({t.abbreviation}) → {team_id}")
        uploaded += 1
    db.close_connection()
    typer.echo(f"Done. {uploaded} team(s) uploaded.")


@app.command("list")
def list_teams(
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source: user | official | asg"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max teams to display"),
):
    """List public teams in the database."""
    db = PostgresDB()
    teams = db.get_public_teams(source=source, limit=limit)
    db.close_connection()

    if not teams:
        typer.echo("No teams found.")
        return

    table = PrettyTable(["team_id", "name", "abbrev", "source", "sets", "roster"])
    table.align = "l"
    for t in teams:
        table.add_row([
            t['team_id'][:8] + "...",
            t['name'][:40],
            t['abbreviation'],
            t['source'],
            ','.join(t.get('allowed_sets') or []) or '—',
            len(t.get('roster') or []),
        ])
    typer.echo(table)


_AUTOFILL_PRESETS = {
    'balanced':       {'offense': 0.52, 'rotation': 0.28, 'bullpen': 0.19, 'bench': 0.01},
    'ace-heavy':      {'offense': 0.42, 'rotation': 0.38, 'bullpen': 0.18, 'bench': 0.02},
    'power-lineup':   {'offense': 0.57, 'rotation': 0.25, 'bullpen': 0.17, 'bench': 0.01},
    'lights-out-pen': {'offense': 0.47, 'rotation': 0.25, 'bullpen': 0.27, 'bench': 0.01},
}


@app.command("autofill")
def test_autofill(
    pts_limit: int = typer.Option(5000,       "--pts-limit",  "-p", help="Team points limit"),
    showdown_set: str = typer.Option("EXPANDED", "--set",    "-s", help="Showdown set (e.g. EXPANDED, CLASSIC)"),
    starters: int  = typer.Option(4,          "--starters",        help="Number of rotation starters"),
    bench: int     = typer.Option(2,          "--bench",           help="Minimum bench slots"),
    bullpen: int   = typer.Option(5,          "--bullpen",         help="Minimum bullpen slots"),
    preset: str    = typer.Option("balanced", "--preset",    "-r",
                                  help=f"Points preset: {', '.join(_AUTOFILL_PRESETS)}"),
    pitching: Optional[str] = typer.Option(None, "--pitching",
                                           help="high_control | groundball | no_doubles | strikeout"),
    hitting: Optional[str]  = typer.Option(None, "--hitting",
                                           help="high_ob | speed | slug | contact"),
    runs: int = typer.Option(1, "--runs", help="Number of independent autofill runs to compare"),
):
    """Test the autofill algorithm locally — no DB writes, results printed as tables."""
    if preset not in _AUTOFILL_PRESETS:
        typer.echo(f"Unknown preset '{preset}'. Choose from: {', '.join(_AUTOFILL_PRESETS)}", err=True)
        raise typer.Exit(1)

    pts_distribution = _AUTOFILL_PRESETS[preset]
    active_filters   = {'showdown_set': [showdown_set]}

    typer.echo(f"\nAutofill test — pts_limit={pts_limit}  set={showdown_set}  preset={preset}")
    typer.echo(f"  pitching={pitching or 'balanced'}  hitting={hitting or 'balanced'}")
    typer.echo(f"  starters={starters}  bench={bench}  bullpen={bullpen}  runs={runs}\n")

    team = Team(
        name='Test Team', abbreviation='TEST',
        pts_limit=pts_limit,
        roster_size=9 + starters + bench + bullpen,
        num_starters=starters,
        min_bench=bench,
        min_bullpen=bullpen,
        allowed_sets=[showdown_set],
        source=TeamSource.USER,
    )

    typer.echo("Fetching candidate pools…", nl=False)
    db = PostgresDB()
    candidates_by_bucket: dict[str, list[dict]] = {}
    for bucket, bucket_filters in BUCKET_QUERY_FILTERS.items():
        base = {**bucket_filters, **active_filters}
        main = db.fetch_card_list(filters={**base, 'limit': 500, 'sort_by': 'points', 'sort_direction': 'desc'}) or []
        floor = db.fetch_card_list(filters={**base, 'max_points': 150, 'limit': 200, 'sort_by': 'points', 'sort_direction': 'desc'}) or []
        seen = {c['card_id'] for c in main}
        candidates_by_bucket[bucket] = main + [c for c in floor if c['card_id'] not in seen]

    cardmap: dict[str, dict] = {c['card_id']: c for cards in candidates_by_bucket.values() for c in cards}
    db.close_connection()
    counts = {b: len(v) for b, v in candidates_by_bucket.items()}
    typer.echo(f" done.  {counts}\n")

    def _card(cid: str) -> dict:
        return cardmap.get(cid, {})

    def _pts(cid: str) -> int:
        return _card(cid).get('points') or 0

    def _name(cid: str) -> str:
        c = _card(cid)
        year = c.get('year', '')
        n = (c.get('name') or cid)[:22]
        return f"{n} ({year})" if year else n

    def _pos(cid: str) -> str:
        return (_card(cid).get('positions_and_defense_string') or _card(cid).get('player_type') or '')[:18]

    for run in range(1, runs + 1):
        if runs > 1:
            typer.echo(f"── Run {run} of {runs} {'─' * 40}")

        result = autofill_team(
            team=team,
            candidates_by_bucket=candidates_by_bucket,
            pts_distribution=pts_distribution,
            pitching_strategy=pitching,
            hitting_strategy=hitting,
        )

        if result is None:
            typer.echo("✗  Autofill failed after max attempts. Try a higher pts_limit or different preset.")
            continue

        roster   = result['roster']
        lineups  = result['lineups']
        rotation = result['rotation']
        lineup_slots   = lineups[0]['slots'] if lineups else []
        rotation_slots = [r for r in rotation if r['role'].startswith('SP')]
        bullpen_slots  = [r for r in rotation if not r['role'].startswith('SP')]
        bench_slots    = [s for s in roster if s['roster_position'] == 'BE']

        def _section_table(title: str, rows: list[tuple], target: int) -> None:
            total = sum(r[1] for r in rows)
            t = PrettyTable(['Slot', 'Name', 'Pts', 'Position', 'Detail'])
            t.align = 'l'
            t.align['Pts'] = 'r'
            for slot, pts_val, name_val, pos_val, detail_val in rows:
                t.add_row([slot, name_val, pts_val, pos_val, detail_val])
            t.add_row(['', '', '', '', ''])
            t.add_row(['TOTAL', '', total, '', f"target {target}  Δ {total - target:+d}"])
            typer.echo(f"\n{title}")
            typer.echo(t)

        def _pitcher_detail(cid: str) -> str:
            c = _card(cid)
            return f"IP:{c.get('ip','?')}  CMD:{c.get('command','?')}/{c.get('outs','?')}"

        _section_table(
            'LINEUP',
            [(s['field_position'], _pts(s['card_id']), _name(s['card_id']), _pos(s['card_id']), '') for s in lineup_slots],
            round(pts_limit * pts_distribution['offense']),
        )
        _section_table(
            'ROTATION',
            [(r['role'], _pts(r['card_id']), _name(r['card_id']), _pos(r['card_id']), _pitcher_detail(r['card_id'])) for r in rotation_slots],
            round(pts_limit * pts_distribution['rotation']),
        )
        _section_table(
            'BULLPEN',
            [(r['role'], _pts(r['card_id']), _name(r['card_id']), _pos(r['card_id']), _pitcher_detail(r['card_id'])) for r in bullpen_slots],
            round(pts_limit * pts_distribution['bullpen']),
        )
        _section_table(
            'BENCH',
            [('BE', _pts(s['card_id']), _name(s['card_id']), _pos(s['card_id']), '') for s in bench_slots],
            round(pts_limit * pts_distribution['bench']),
        )

        grand_total = sum(_pts(s['card_id']) for s in lineup_slots + bench_slots) + \
                      sum(_pts(r['card_id']) for r in rotation)
        typer.echo(f"\n  Grand total: {grand_total} / {pts_limit} pts  (Δ {grand_total - pts_limit:+d})\n")


@app.command("delete")
def delete_team(
    team_id: str = typer.Option(..., "--team-id", help="UUID of the team to delete"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete a team by ID (admin use — no ownership check)."""
    if not confirm:
        typer.confirm(f"Delete team {team_id}?", abort=True)
    db = PostgresDB()
    with db.connection.cursor() as cur:
        cur.execute("DELETE FROM internal.user_teams WHERE team_id = %s", (team_id,))
        deleted = cur.rowcount
    db.close_connection()
    if deleted:
        typer.echo(f"Deleted team {team_id}.")
    else:
        typer.echo(f"No team found with ID {team_id}.", err=True)
        raise typer.Exit(1)
