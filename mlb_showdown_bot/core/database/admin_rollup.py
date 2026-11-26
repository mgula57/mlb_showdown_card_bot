"""Nightly rollup of the admin dashboard's counts, so it stops scanning the raw logs on every load.

Two tables, one row per UTC day:
- `internal.metrics_daily_activity`: actions per (day, feature, user). Anonymous actions roll up
  into one row per feature with `user_id = ''`. Distinct users over any window come from here.
- `internal.metrics_daily_builds`: card builds per (day, dimension, value), with failed and
  anonymous counts, for every `BUILD_DIMENSIONS` entry.

The rollup and the dashboard use the same SELECTs (`activity_select` / `builds_select`): the job
writes them for finished days, and the dashboard reads the tables up to the last rolled-up day and
runs the SELECT live for anything after it (today, or days a failed run missed). A missed night
never shows as a gap, it's just slower until the next run.

Run by `showdown_bot database rollup_admin_metrics` (`.github/workflows/rollup_admin_metrics.yml`).
"""

from datetime import date, timedelta

from psycopg2 import sql

from .admin_sources import BUILD_DIMENSIONS, FEATURE_SOURCES
from .postgres_db import PostgresDB


class AdminRollup:
    ACTIVITY_TABLE = sql.Identifier('internal', 'metrics_daily_activity')
    BUILDS_TABLE = sql.Identifier('internal', 'metrics_daily_builds')

    def __init__(self, db: PostgresDB):
        self.db = db

    # -- shared SELECTs ------------------------------------------------------

    @staticmethod
    def activity_select(from_day: sql.Composable, to_day: sql.Composable) -> sql.Composed:
        """(day, feature, user_id, actions) for actions on `from_day`..`to_day`, inclusive."""
        parts = []
        for source in FEATURE_SOURCES:
            parts.append(source.select(
                sql.SQL("{key} AS feature, coalesce({user}::text, '') AS user_id, ({t})::date AS day").format(
                    key=sql.Literal(source.key), user=source.user, t=source.time,
                ),
                source.time_between(from_day, to_day),
            ))
        return sql.SQL("""
            SELECT day, feature, user_id, count(*)::int AS actions
            FROM ({union}) a
            GROUP BY day, feature, user_id
        """).format(union=sql.SQL(" UNION ALL ").join(parts))

    @staticmethod
    def builds_select(from_day: sql.Composable, to_day: sql.Composable) -> sql.Composed:
        """(day, dimension, value, builds, failed, anonymous_builds) for builds on `from_day`..`to_day`,
        inclusive. One scan: each build fans out to one row per dimension through a lateral VALUES list."""
        values = sql.SQL(", ").join(
            sql.SQL("({}, {})").format(
                sql.Literal(dimension.key),
                sql.SQL(f"({dimension.expr})::text" if dimension.sparse else f"coalesce(nullif(({dimension.expr})::text, ''), 'None')"),
            )
            for dimension in BUILD_DIMENSIONS
        )
        return sql.SQL("""
            SELECT created_on::date AS day, d.dimension, d.value,
                   count(*)::int                                 AS builds,
                   count(error)::int                             AS failed,
                   count(*) FILTER (WHERE user_id IS NULL)::int  AS anonymous_builds
            FROM internal.log_custom_card_bot
            CROSS JOIN LATERAL (VALUES {values}) AS d(dimension, value)
            WHERE created_on >= ({start})::timestamp AND created_on < (({end}) + 1)::timestamp
              AND d.value IS NOT NULL
            GROUP BY 1, 2, 3
        """).format(values=values, start=from_day, end=to_day)

    @classmethod
    def with_live_tail(cls, name: str, start_day: sql.Composable) -> sql.Composed:
        """CTEs exposing `<name>` (`activity` or `builds`) from `start_day` through today: the
        rollup table up to its last day, then the live SELECT for the days after it."""
        table, select, columns = {
            'activity': (cls.ACTIVITY_TABLE, cls.activity_select, "day, feature, user_id, actions"),
            'builds': (cls.BUILDS_TABLE, cls.builds_select, "day, dimension, value, builds, failed, anonymous_builds"),
        }[name]
        bounds = sql.Identifier(f"{name}_rolled_up_through")
        last_day = sql.SQL("(SELECT last_day FROM {})").format(bounds)
        return sql.SQL("""
            {bounds} AS (
                SELECT greatest(coalesce(max(day), {start} - 1), {start} - 1) AS last_day FROM {table}
            ),
            {name} AS (
                SELECT {columns} FROM {table} WHERE day >= {start} AND day <= {last_day}
                UNION ALL
                {live}
            )
        """).format(
            bounds=bounds, name=sql.Identifier(name), table=table, start=start_day,
            columns=sql.SQL(columns), last_day=last_day,
            live=select(sql.SQL("{} + 1").format(last_day), sql.SQL("current_date")),
        )

    # -- job ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        statements = [
            sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    day date NOT NULL,
                    feature text NOT NULL,
                    user_id text NOT NULL DEFAULT '',
                    actions integer NOT NULL,
                    PRIMARY KEY (day, feature, user_id)
                )
            """).format(self.ACTIVITY_TABLE),
            sql.SQL("CREATE INDEX IF NOT EXISTS metrics_daily_activity_user_idx ON {} (user_id, day) WHERE user_id <> ''").format(self.ACTIVITY_TABLE),
            sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    day date NOT NULL,
                    dimension text NOT NULL,
                    value text NOT NULL,
                    builds integer NOT NULL,
                    failed integer NOT NULL,
                    anonymous_builds integer NOT NULL,
                    PRIMARY KEY (day, dimension, value)
                )
            """).format(self.BUILDS_TABLE),
        ]
        with self.db.connection.cursor() as cur:
            for statement in statements:
                cur.execute(statement)
        self.db.connection.commit()

    def refresh(self, from_day: date, to_day: date, chunk_days: int = 7) -> None:
        """Recompute `from_day`..`to_day` (inclusive), replacing whatever was there, a chunk of days per
        transaction. Safe to re-run: late rows from the previous day are picked up by overlapping runs."""
        self.ensure_tables()
        params_start, params_end = sql.Placeholder('from_day'), sql.Placeholder('to_day')
        chunk_start = from_day
        while chunk_start <= to_day:
            chunk_end = min(chunk_start + timedelta(days=chunk_days - 1), to_day)
            params = {'from_day': chunk_start, 'to_day': chunk_end}
            try:
                with self.db.connection.cursor() as cur:
                    for table, select in ((self.ACTIVITY_TABLE, self.activity_select), (self.BUILDS_TABLE, self.builds_select)):
                        cur.execute(sql.SQL("DELETE FROM {} WHERE day BETWEEN %(from_day)s AND %(to_day)s").format(table), params)
                        cur.execute(sql.SQL("INSERT INTO {} {}").format(table, select(params_start, params_end)), params)
                self.db.connection.commit()
            except Exception:
                self.db.connection.rollback()
                raise
            print(f"Rolled up {chunk_start} to {chunk_end}")
            chunk_start = chunk_end + timedelta(days=1)
