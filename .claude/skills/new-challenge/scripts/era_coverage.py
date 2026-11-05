"""Report which Showdown Bot eras the existing challenge templates cover.

Read-only. Lists templates from the PROD (DATABASE_URL_ARCHIVE) and DEV (DATABASE_URL_LOGS)
databases and maps each template's effective year span onto `Era.year_range`.

Run from the repo root:  .venv/bin/python .claude/skills/new-challenge/scripts/era_coverage.py [--json]
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

from mlb_showdown_bot.core.card.sets import Era
from mlb_showdown_bot.core.simulation.challenge_generator import EARLIEST_SEASON

load_dotenv()

DATABASES = {"prod": "DATABASE_URL_ARCHIVE", "dev": "DATABASE_URL_LOGS"}
COLUMNS = "slug, title, category, goal_type, goal_value, pts_limit, year_pool, replaces_pool, player_filters, active"


@dataclass
class Template:
    env: str
    slug: str
    title: str
    category: str
    goal_type: str
    goal_value: dict | None
    pts_limit: int | None
    year_pool: str
    replaces_pool: str
    player_filters: dict | None
    active: bool

    @property
    def year_span(self) -> tuple[int, int]:
        """(low, high) of years an instance can land on, narrowed by min_year/max_year filters."""
        pool = self.year_pool
        if pool == "any":
            low, high = EARLIEST_SEASON, datetime.now().year
        elif pool.startswith("random_range:"):
            low, high = (int(b) for b in pool.removeprefix("random_range:").split(","))
        else:
            years = [int(y) for y in pool.split(",")]
            low, high = min(years), max(years)
        return max(low, EARLIEST_SEASON), high

    @property
    def eras(self) -> list[Era]:
        low, high = self.year_span
        return [era for era in Era if any(low <= y <= high for y in era.year_range)]

    @property
    def is_fixed_year(self) -> bool:
        low, high = self.year_span
        return low == high


def fetch_templates() -> list[Template]:
    templates: list[Template] = []
    for env, var in DATABASES.items():
        if not os.environ.get(var):
            print(f"# {var} not set, skipping {env}", file=sys.stderr)
            continue
        conn = psycopg2.connect(os.environ[var])
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT {COLUMNS} FROM internal.challenge_template ORDER BY category, slug")
            templates += [Template(env, *row) for row in cur.fetchall()]
        finally:
            conn.rollback()  # READ-ONLY; NEVER SET SESSION STATE ON THE POOLER
            conn.close()
    return templates


def main() -> None:
    templates = [t for t in fetch_templates() if t.active]
    if "--json" in sys.argv:
        print(json.dumps([t.__dict__ | {"eras": [e.name for e in t.eras]} for t in templates], indent=2, default=str))
        return

    print(f"{'ERA':<14}{'YEARS':<12}{'FIXED':>6}{'ROTATING':>9}   TEMPLATES (env:slug)")
    for era in Era:
        years = era.year_range
        if years[-1] < EARLIEST_SEASON:
            continue
        fixed = [t for t in templates if t.is_fixed_year and era in t.eras]
        rotating = [t for t in templates if not t.is_fixed_year and era in t.eras]
        names = ", ".join(f"{t.env}:{t.slug}" for t in fixed + rotating) or "-"
        print(f"{era.name:<14}{years[0]}-{years[-1]:<7}{len(fixed):>6}{len(rotating):>9}   {names}")

    print("\nCATEGORY x GOAL (active templates, prod+dev, deduped by slug)")
    seen: dict[str, Template] = {t.slug: t for t in templates}
    for t in sorted(seen.values(), key=lambda t: (t.category, t.slug)):
        print(f"  {t.category:<11}{t.goal_type:<18}{str(t.pts_limit or '-'):<6}{t.year_pool:<26}{t.slug}")


if __name__ == "__main__":
    main()
