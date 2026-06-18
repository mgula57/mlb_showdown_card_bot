import json
import sys
from pathlib import Path
from typing import Optional

import typer
from prettytable import PrettyTable

from ...core.database.postgres_db import PostgresDB
from ...core.card.team_builder import Team, TeamSource

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

    table = PrettyTable(["team_id", "name", "abbrev", "source", "set", "roster"])
    table.align = "l"
    for t in teams:
        table.add_row([
            t['team_id'][:8] + "...",
            t['name'][:40],
            t['abbreviation'],
            t['source'],
            t['showdown_set'],
            len(t.get('roster') or []),
        ])
    typer.echo(table)


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
