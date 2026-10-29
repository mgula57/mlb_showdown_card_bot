"""Helpers for picking Home page Spotlight cards.

Read-only. Three subcommands:

  history                  Past spotlights in PROD (reason, date, players) so a theme isn't repeated.
  find '<filters json>'    Candidate cards from card_bot (PROD) via `PostgresDB.fetch_card_list`, deduped
                           to one row per card id. Filters use the Card Explorer keys, e.g.
                           '{"awards": ["MVP-1"], "lg_id": ["AL"], "min_year": 1980, "max_year": 1989}'.
  check <id,id,...> [--env dev|prod]
                           Which Showdown sets each id has in that env's internal.dim_card (the table
                           `publish_new_spotlight` copies card_data from). A missing set = no card there.

Run from the repo root:  .venv/bin/python .claude/skills/new-spotlight/scripts/spotlight_tools.py <cmd> ...
"""

import argparse
import json
from collections import defaultdict

from dotenv import load_dotenv

from mlb_showdown_bot.core.database.postgres_db import PostgresDB

load_dotenv(".env")

ALL_SETS = ['2000', '2001', '2002', '2003', '2004', '2005', 'CLASSIC', 'EXPANDED']
CANDIDATE_COLUMNS = ['id', 'name', 'year', 'team', 'lg_id', 'league', 'player_type', 'points', 'real_bwar', 'awards_list', 'is_hof']


class SpotlightTools:

    def __init__(self, env: str = 'prod') -> None:
        self.env = env
        self.db = PostgresDB(is_archive=env == 'prod')
        print(f"Using --env {env} ({self.db.env_var_name})")

    def history(self, limit: int) -> None:
        rows = self.db.execute_query(query="""
            SELECT spotlight_reason, max(spotlight_published_date)::date AS published,
                   array_agg(DISTINCT player_id) AS player_ids
            FROM public.card_spotlight
            GROUP BY spotlight_reason
            ORDER BY published DESC
            LIMIT %s
        """, filter_values=(limit,))
        for r in rows:
            print(f"{r['published']}  {r['spotlight_reason']}: {', '.join(r['player_ids'])}")

    def find(self, filters: dict, limit: int) -> None:
        # One set is enough to list candidates: card ids are shared across sets
        filters = {'showdown_set': '2001', 'sort_by': 'real_bwar', 'limit': limit, **filters}
        rows = self.db.fetch_card_list(filters=filters) or []
        seen: set[str] = set()
        for r in rows:
            if r['id'] in seen:
                continue
            seen.add(r['id'])
            print(json.dumps({c: r.get(c) for c in CANDIDATE_COLUMNS}, default=str))
        print(f"{len(seen)} candidates")

    def check(self, player_ids: list[str]) -> None:
        rows = self.db.execute_query(
            query="SELECT player_id, showdown_set FROM internal.dim_card WHERE player_id = ANY(%s)",
            filter_values=(player_ids,),
        )
        sets_by_id: dict[str, set[str]] = defaultdict(set)
        for r in rows:
            sets_by_id[r['player_id']].add(r['showdown_set'])
        for pid in player_ids:
            missing = [s for s in ALL_SETS if s not in sets_by_id[pid]]
            print(f"{pid}: {'OK' if not missing else 'MISSING ' + ', '.join(missing)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    p_history = sub.add_parser('history')
    p_history.add_argument('--limit', type=int, default=20)
    p_find = sub.add_parser('find')
    p_find.add_argument('filters', help='JSON dict of Card Explorer filters')
    p_find.add_argument('--limit', type=int, default=60)
    p_check = sub.add_parser('check')
    p_check.add_argument('player_ids', help='Comma-separated card ids, e.g. 1980-brettge01,2026-592885')
    p_check.add_argument('--env', default='prod', choices=['dev', 'prod'])
    args = parser.parse_args()

    match args.cmd:
        case 'history':
            SpotlightTools().history(args.limit)
        case 'find':
            SpotlightTools().find(json.loads(args.filters), args.limit)
        case 'check':
            SpotlightTools(args.env).check([p.strip() for p in args.player_ids.split(',') if p.strip()])
