import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from prettytable import PrettyTable

from ...core.database.postgres_db import PostgresDB, Set
from ...core.card.team_builder import Team, TeamSource, RosterToTeamConverter
from ...core.card.team_builder.autofill import BUCKET_QUERY_FILTERS, autofill_team
from ...core.mlb_stats_api import MLBStatsAPI
from ...core.mlb_stats_api.models.teams.team import TeamWithColors

app = typer.Typer()


@app.command("build-asg-roster")
def build_asg_roster(
    season: int = typer.Option(..., "--season", "-y", help="Season (year) of the All-Star Game to import"),
    sport_id: int = typer.Option(1, "--sport-id", help="MLB Stats API sport id (1 = MLB)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Print the roster without writing to DB"),
):
    """Populate internal.asg_roster for a season from the MLB Stats API (gameType=A).

    Fetches the season's All-Star Game participants (with starting positions, batting order, and
    starting pitcher) and writes them to the ASG roster lookup table used by the team builder.
    """
    api = MLBStatsAPI()
    typer.echo(f"Fetching {season} All-Star Game rosters from the MLB Stats API…")
    rows = api.games.get_all_star_rosters(season=season, sport_id=sport_id)
    if not rows:
        typer.echo(f"No All-Star Game found for season {season}.", err=True)
        raise typer.Exit(1)

    by_league: dict[str, int] = {}
    for r in rows:
        by_league[r['league']] = by_league.get(r['league'], 0) + 1
    typer.echo(f"Found {len(rows)} participants: " + ", ".join(f"{lg}={n}" for lg, n in sorted(by_league.items())))

    if dry_run:
        for r in sorted(rows, key=lambda x: (x['league'], not x['is_starter'], x.get('batting_order') or 99)):
            flags = []
            if r['is_starter']:
                flags.append(f"BO{r['batting_order']}")
            if r['is_starting_pitcher']:
                flags.append("SP")
            typer.echo(f"  [{r['league']}] {r['player_name']:<24} {r.get('position') or '?':<3} {' '.join(flags)}")
        typer.echo("Dry run — no changes written.")
        return

    db = PostgresDB()
    db.build_asg_roster_table()
    count = db.upsert_asg_roster_rows(season=season, sport_id=sport_id, rows=rows)
    db.close_connection()
    typer.echo(f"Done. Wrote {count} ASG roster row(s) for {season}.")


@app.command("build-historical")
def build_historical_teams(
    season: Optional[int] = typer.Option(None, "--season", "-y", help="Single season to process (overrides the range)"),
    start_season: int = typer.Option(1901, "--start-season", help="First season of the range to process"),
    end_season: int = typer.Option(datetime.now().year, "--end-season", help="Last season of the range to process"),
    sport_id: int = typer.Option(1, "--sport-id", help="MLB Stats API sport id (1 = MLB)"),
    showdown_set: str = typer.Option("EXPANDED", "--set", "-s", help="Reference set whose cards drive the playing-time sort"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Print each composed roster without writing to DB"),
    env: str = typer.Option("dev", "--env", "-e", help="Database environment: dev | prod"),
):
    """Pre-process historical team rosters into internal.dim_historical_team / dim_historical_roster.

    For each team in each season, composes the roster once via RosterToTeamConverter and stores
    the resulting slots keyed by mlb_id. Slots are set-agnostic — the underlying playing time is
    the same across sets — so --set only picks which set's cards are read to do the sorting.
    Storing the result turns the request-time path into a lookup instead of a recomposition.
    """
    try:
        showdown_set_enum = Set(showdown_set)
    except ValueError:
        typer.echo(f"Invalid set '{showdown_set}'. Valid options: {[s.value for s in Set]}", err=True)
        raise typer.Exit(1)

    seasons = [season] if season is not None else list(range(start_season, end_season + 1))
    seasons.sort(reverse=True)

    api = MLBStatsAPI()
    db = PostgresDB(is_archive=(env.lower() == "prod"))
    if not dry_run:
        db.build_historical_team_tables()

    total_teams = 0
    total_slots = 0
    for season_year in seasons:
        try:
            api_teams = api.teams.get_teams(season=season_year, sport_id=sport_id)
        except Exception as exc:
            typer.echo(f"  {season_year}: skipped — could not fetch teams ({exc})", err=True)
            continue

        season_teams = 0
        season_slots = 0
        for api_team in api_teams:
            team_with_colors = TeamWithColors(**api_team.model_dump())
            team_with_colors.load_colors_from_showdown_team()
            team_abbr = api_team.abbreviation or str(api_team.id)

            cards = db.fetch_team_season_card_pool(
                season=season_year,
                showdown_set=showdown_set_enum.value,
                team_id=api_team.id,
                team_abbr=team_abbr,
                sport_id=sport_id,
            )
            if not cards:
                continue

            composed = RosterToTeamConverter(
                cards=cards,
                team_id=f"mlb-{sport_id}-{api_team.id}-{season_year}-{showdown_set_enum.value}",
                name=api_team.name or team_abbr,
                abbreviation=team_abbr,
                season=season_year,
            ).build()

            # Slots are stored by (mlb_id, player_type) so any set's cards can be resolved against
            # them later — player_type keeps a two-way player's pitching and hitting slots distinct.
            mlb_id_by_card_id = {c.card_id: c.mlb_id for c in cards if c.card_id and c.mlb_id is not None}
            name_by_card_id = {c.card_id: c.name for c in cards if c.card_id}
            player_type_by_card_id = {c.card_id: c.player_type for c in cards if c.card_id}
            batting_order_by_card_id = {
                slot.card_id: slot.batting_order
                for lineup in composed.lineups for slot in lineup.slots
            }
            rows = [
                {
                    'mlb_id': mlb_id_by_card_id[slot.card_id],
                    'player_type': player_type_by_card_id.get(slot.card_id) or 'HITTER',
                    'player_name': name_by_card_id.get(slot.card_id),
                    'roster_position': slot.roster_position,
                    'batting_order': batting_order_by_card_id.get(slot.card_id),
                    'slot_order': i,
                }
                for i, slot in enumerate(composed.roster)
                if slot.card_id in mlb_id_by_card_id
            ]
            if not rows:
                continue

            if dry_run:
                typer.echo(f"\n  [{season_year}] {api_team.name} ({team_abbr}) — {len(rows)} slots")
                for row in rows:
                    order = f" #{row['batting_order']}" if row['batting_order'] else ""
                    typer.echo(f"    {row['roster_position']:<4}{order:<4} {row['player_name']}")
            else:
                db.upsert_historical_team({
                    'season': season_year,
                    'sport_id': sport_id,
                    'team_id': api_team.id,
                    'abbreviation': team_abbr,
                    'name': api_team.name,
                    'bref_team_id': api_team.bref_team,
                    'league_id': api_team.league.id if api_team.league else None,
                    'league_name': api_team.league.name if api_team.league else None,
                    'division_name': api_team.division.name if api_team.division else None,
                    'primary_color': team_with_colors.primary_color,
                    'secondary_color': team_with_colors.secondary_color,
                    'roster_count': len(rows),
                })
                db.upsert_historical_roster_rows(season=season_year, sport_id=sport_id, team_id=api_team.id, rows=rows)

            season_teams += 1
            season_slots += len(rows)

        typer.echo(f"{season_year}: {season_teams} team(s), {season_slots} slot(s)")
        total_teams += season_teams
        total_slots += season_slots

    db.close_connection()
    suffix = " (dry run — nothing written)" if dry_run else ""
    typer.echo(f"\nDone. {total_teams} team(s), {total_slots} roster slot(s) across {len(seasons)} season(s).{suffix}")


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


@app.command("build-tables")
def build_tables(
    env: str = typer.Option("dev", "--env", "-e", help="Database environment: dev | prod"),
):
    """Create/upgrade internal.user_teams and internal.team_collection."""
    db = PostgresDB(is_archive=env.lower() == "prod")
    db.build_user_teams_table()
    db.build_team_collection_table()
    db.close_connection()
    typer.echo("Done. user_teams + team_collection are ready.")


@app.command("collections")
def collections(
    action: str = typer.Argument("list", help="list | set | delete"),
    slug: Optional[str] = typer.Option(None, "--slug", help="Collection slug (required for set/delete)"),
    title: Optional[str] = typer.Option(None, "--title", help="Display title (set)"),
    description: Optional[str] = typer.Option(None, "--description", help="Blurb (set)"),
    emoji: Optional[str] = typer.Option(None, "--emoji", help="Cover emoji (set)"),
    sort_index: Optional[int] = typer.Option(None, "--sort-index", help="Ordering (set)"),
    hidden: bool = typer.Option(False, "--hidden", help="Mark not visible (set)"),
    env: str = typer.Option("dev", "--env", "-e", help="Database environment: dev | prod"),
):
    """Manage the curated team collections."""
    db = PostgresDB(is_archive=env.lower() == "prod")
    try:
        if action == "list":
            rows = db.get_team_collections(include_hidden=True)
            table = PrettyTable(["slug", "title", "sort", "visible", "teams"])
            table.align = "l"
            for r in rows:
                table.add_row([r["slug"], r["title"][:40], r["sort_index"],
                               "yes" if r["is_visible"] else "no", r["team_count"]])
            typer.echo(table)
        elif action == "set":
            if not slug or not title:
                typer.echo("--slug and --title are required for 'set'.", err=True)
                raise typer.Exit(1)
            row = db.upsert_team_collection(
                slug.lower(), title=title, description=description, cover_emoji=emoji,
                sort_index=sort_index, is_visible=not hidden,
            )
            typer.echo(f"Upserted collection '{row['slug']}'.")
        elif action == "delete":
            if not slug:
                typer.echo("--slug is required for 'delete'.", err=True)
                raise typer.Exit(1)
            result = db.delete_team_collection(slug.lower())
            typer.echo({"in_use": "Refused — collection still has teams.",
                        "deleted": f"Deleted '{slug}'.", None: "No such collection."}[result])
        else:
            typer.echo(f"Unknown action '{action}'. Use list | set | delete.", err=True)
            raise typer.Exit(1)
    finally:
        db.close_connection()


@app.command("import")
def import_curated(
    file: Path = typer.Option(..., "--file", "-f", help="JSON file: { collection, teams: [...] }"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Resolve + report, write nothing"),
    env: str = typer.Option("dev", "--env", "-e", help="Database environment: dev | prod"),
):
    """Bulk-import curated ('official') teams from a JSON file, resolving player names to WOTC cards.

    File shape:
      {
        "collection": {"slug": "showdown-league-s1", "title": "...", "cover_emoji": "🏆"},
        "teams": [
          {
            "name": "Gary Quinn", "abbreviation": "GQ",
            "primary_color": "rgb(...)", "secondary_color": "rgb(...)",
            "subtitle": "1996 Champion", "credit": "Built by Gary Quinn",
            "strategy_deck": {"Great Throw": 3, "Insult To Injury": 2},
            "players": {
              "lineup":   [{"name": "Derek Jeter", "position": "SS", "order": 2, "set": "2002"}],
              "rotation": [{"name": "Barry Zito", "set": "2003"}],
              "bullpen":  [{"name": "John Franco"}],
              "bench":    [{"name": "Mike Bordick"}]
            }
          }
        ]
      }
    Each player may carry "set" / "year" / "team" hints or an explicit "card_id" override.
    """
    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)
    try:
        doc = json.loads(file.read_text())
    except json.JSONDecodeError as exc:
        typer.echo(f"Error parsing JSON: {exc}", err=True)
        raise typer.Exit(1)

    coll = doc.get("collection") or {}
    coll_slug = (coll.get("slug") or "").strip().lower()
    if not coll_slug:
        typer.echo("Error: collection.slug is required.", err=True)
        raise typer.Exit(1)

    db = PostgresDB(is_archive=env.lower() == "prod")

    def _resolve(entry: dict) -> tuple[Optional[str], str]:
        """(card_id, status) — status in OK / OVERRIDE / AMBIGUOUS / MISSING."""
        if entry.get("card_id"):
            return entry["card_id"], "OVERRIDE"
        cands = db.resolve_wotc_card(
            entry["name"], showdown_set=entry.get("set"),
            year=entry.get("year"), team=entry.get("team"),
        )
        if not cands:
            return None, "MISSING"
        if len(cands) > 1 and cands[0]["match_rank"] == cands[1]["match_rank"] \
                and cands[0]["points"] == cands[1]["points"]:
            return cands[0]["card_id"], "AMBIGUOUS"
        return cands[0]["card_id"], "OK"

    report = PrettyTable(["team", "bucket", "player", "status", "card_id"])
    report.align = "l"
    teams_payload: list[dict] = []
    problems = 0

    for t in doc.get("teams", []):
        team_slug = (t.get("abbreviation") or t.get("name") or "team").strip().lower().replace(" ", "-")
        roster: list[dict] = []
        ln_slots: list[dict] = []
        sp_i = 0
        for bucket in ("lineup", "rotation", "bullpen", "bench"):
            for entry in (t.get("players", {}).get(bucket) or []):
                card_id, status = _resolve(entry)
                if status in ("MISSING", "AMBIGUOUS"):
                    problems += 1
                report.add_row([t.get("name"), bucket, entry.get("name"), status, card_id or "—"])
                if not card_id:
                    continue
                if bucket == "rotation":
                    sp_i += 1
                    pos = f"SP{sp_i}"
                elif bucket == "lineup":
                    pos = entry.get("position") or "DH"
                    if entry.get("order"):
                        ln_slots.append({"card_id": card_id, "card_source": "WOTC",
                                         "batting_order": entry["order"]})
                else:
                    pos = "BE" if bucket == "bench" else "RP"
                roster.append({
                    "card_id": card_id, "card_source": "WOTC",
                    "roster_position": pos, "draft_order": None, "pick_source": "IMPORTED",
                })
        num_bench = sum(1 for r in roster if r["roster_position"] == "BE")
        num_bull = sum(1 for r in roster if r["roster_position"] in ("RP", "CL"))
        num_sp = sum(1 for r in roster if r["roster_position"].startswith("SP"))
        # Deterministic id so re-running the import upserts rather than duplicating.
        team_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"showdown-team:{coll_slug}:{team_slug}"))
        teams_payload.append({
            "team_id": team_uuid,
            "name": t["name"],
            "abbreviation": t.get("abbreviation") or t["name"][:5],
            "primary_color": t.get("primary_color") or "rgb(0,0,0)",
            "secondary_color": t.get("secondary_color") or "rgb(255,255,255)",
            "source": TeamSource.OFFICIAL.value,
            "is_public": True,
            "roster_size": len(roster),
            "min_bench": num_bench,
            "min_bullpen": num_bull,
            "num_starters": max(num_sp, 1),
            "bench_pts_multiplier": PostgresDB._HISTORICAL_BENCH_PTS_MULTIPLIER,
            "collection_slug": coll_slug,
            "subtitle": t.get("subtitle"),
            "credit": t.get("credit"),
            "collection_sort_index": t.get("sort_index"),
            "strategy_deck": t.get("strategy_deck") or {},
            "roster": roster,
            "lineups": [{"name": "Imported", "slots": ln_slots}] if ln_slots else [],
        })

    typer.echo(report)
    typer.echo(f"\n{len(teams_payload)} team(s), {problems} unresolved/ambiguous player(s).")

    if dry_run:
        typer.echo("Dry run — nothing written.")
        db.close_connection()
        return
    if problems:
        typer.confirm(f"{problems} player(s) could not be resolved cleanly. Import anyway?", abort=True)

    db.build_user_teams_table()
    db.build_team_collection_table()
    db.upsert_team_collection(
        coll_slug, title=coll.get("title") or coll_slug, description=coll.get("description"),
        cover_emoji=coll.get("cover_emoji"), sort_index=coll.get("sort_index"),
        is_visible=coll.get("is_visible", True),
    )
    for payload in teams_payload:
        tid = db.admin_upsert_team(payload)
        typer.echo(f"  Upserted {payload['name']} → {tid}")
    db.close_connection()
    typer.echo("Done.")


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
