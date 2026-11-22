"""Read-only analytics for the admin dashboard (`/admin`).

Everything here is derived from tables the app already writes: the request logs
(`internal.log_*`), each feature's own tables (releases, teams, sims, comments, ...) and
Supabase's `auth.users`. Each feature is described once in `FEATURE_SOURCES`, and every
cross-feature query (overview, user list, user detail) is generated from that registry, so
adding a feature to the dashboard is one entry there.

Timestamps are bucketed by UTC day (the database's session time zone).
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Optional

from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from .postgres_db import PostgresDB


# ------------------------------------------------------------------------
# MARK: FEATURE REGISTRY
# ------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatureSource:
    """One countable user action, read from the table that records it.

    `detail_sql` and `where_sql` are trusted SQL fragments over the table's own columns
    (static strings defined below, never user input)."""
    key: str
    label: str
    area: str
    action: str
    schema: str
    table: str
    user_column: str
    time_column: str
    detail_sql: str = "NULL"
    where_sql: str = "TRUE"
    # High-volume sources (page views) would crowd everything else out of a user's activity timeline
    in_timeline: bool = True

    def select(self, columns: sql.Composable, extra_where: sql.Composable = sql.SQL("TRUE")) -> sql.Composed:
        """`SELECT <columns> FROM <table> WHERE <where_sql> AND <extra_where>`, where the
        columns can reference `{user}`, `{time}` and `{detail}` placeholders."""
        return sql.SQL("SELECT {columns} FROM {table} WHERE ({where}) AND ({extra})").format(
            columns=columns,
            table=sql.Identifier(self.schema, self.table),
            where=sql.SQL(self.where_sql),
            extra=extra_where,
        )

    @property
    def user(self) -> sql.Identifier:
        return sql.Identifier(self.user_column)

    @property
    def time(self) -> sql.Composed:
        # Mixed timestamp / timestamptz columns, normalized so UNIONs line up
        return sql.SQL("{}::timestamptz").format(sql.Identifier(self.time_column))

    @property
    def detail(self) -> sql.SQL:
        return sql.SQL(self.detail_sql)


def _event_source(key: str, label: str, area: str, action: str, event: str, detail_sql: str = "NULL", in_timeline: bool = True) -> FeatureSource:
    """A source backed by `internal.log_event` rows of one event (see `api/events.py`)."""
    return FeatureSource(key, label, area, action, 'internal', 'log_event', 'user_id', 'created_at',
                         detail_sql=detail_sql, where_sql=f"event = '{event}'", in_timeline=in_timeline)


FEATURE_SOURCES: tuple[FeatureSource, ...] = (
    # Site
    _event_source('page_views', 'Page views', 'Site', 'Viewed a page', 'page_view', detail_sql="route", in_timeline=False),
    _event_source('sessions', 'Sessions', 'Site', 'Started a session', 'session_start',
                  detail_sql="concat_ws(' · ', properties->>'device', coalesce(properties->>'referrer_host', 'direct'))"),
    _event_source('sign_ins', 'Sign-ins', 'Site', 'Signed in', 'sign_in', detail_sql="properties->>'provider'"),
    # Cards
    FeatureSource('card_builds', 'Card Builder', 'Cards', 'Built a card', 'internal', 'log_custom_card_bot', 'user_id', 'created_on',
                  detail_sql="concat_ws(' · ', concat_ws(' ', name, year), set, CASE WHEN error IS NOT NULL THEN 'failed' END)"),
    FeatureSource('card_searches', 'Card Explorer searches', 'Cards', 'Searched cards', 'internal', 'log_player_search', 'user_id', 'timestamp'),
    FeatureSource('card_views', 'Card opens', 'Cards', 'Opened a card', 'internal', 'log_card_id_lookup', 'user_id', 'timestamp',
                  detail_sql="concat_ws(' · ', card_id, source)"),
    FeatureSource('card_images', 'Card image renders', 'Cards', 'Rendered a card image', 'internal', 'log_card_image_generation', 'user_id', 'timestamp',
                  detail_sql="card_id"),
    _event_source('open_in_builder', 'Open in Builder', 'Cards', 'Opened a card in the builder', 'open_in_builder',
                  detail_sql="properties->>'set'"),
    FeatureSource('image_libraries', 'Image libraries', 'Cards', 'Connected an image library', 'internal', 'user_image_libraries', 'owner_user_id', 'created_at',
                  detail_sql="name"),
    # Release Builder
    FeatureSource('releases_created', 'Releases created', 'Release Builder', 'Created a release', 'internal', 'releases', 'created_by', 'created_at',
                  detail_sql="name"),
    FeatureSource('releases_published', 'Releases published', 'Release Builder', 'Published a release', 'internal', 'releases', 'created_by', 'published_at',
                  detail_sql="name", where_sql="published_at IS NOT NULL"),
    FeatureSource('release_image_jobs', 'Release image runs', 'Release Builder', 'Rendered release images', 'internal', 'release_image_jobs', 'user_id', 'created_at',
                  detail_sql="status"),
    _event_source('release_zip_downloads', 'Zip downloads', 'Release Builder', 'Downloaded an edition zip', 'release_zip_download',
                  detail_sql="concat(properties->>'card_count', ' cards')"),
    # Teams & Sims
    FeatureSource('teams_created', 'Teams created', 'Teams & Sims', 'Created a team', 'internal', 'user_teams', 'user_id', 'created_at',
                  detail_sql="name"),
    FeatureSource('season_sims', 'Season sims', 'Teams & Sims', 'Simulated a season', 'internal', 'sim_job', 'user_id', 'created_at',
                  detail_sql="status"),
    FeatureSource('game_sims', 'Game sims', 'Teams & Sims', 'Simulated a game', 'internal', 'sim_game', 'user_id', 'created_at',
                  detail_sql="concat(away_abbr, ' @ ', home_abbr, ' · ', season)"),
    FeatureSource('faceoffs', 'Faceoffs', 'Teams & Sims', 'Ran a faceoff', 'internal', 'sim_faceoff', 'user_id', 'created_at',
                  detail_sql="concat('Best of ', best_of)"),
    FeatureSource('live_games', 'Live games hosted', 'Teams & Sims', 'Hosted a live game', 'internal', 'sim_lobby', 'host_user_id', 'created_at',
                  detail_sql="status"),
    # Community
    FeatureSource('comments', 'Comments', 'Community', 'Commented', 'internal', 'comments', 'user_id', 'created_at',
                  detail_sql="subject_type"),
    FeatureSource('release_likes', 'Release likes', 'Community', 'Liked a release', 'internal', 'release_likes', 'user_id', 'created_at'),
    FeatureSource('release_saves', 'Release saves', 'Community', 'Saved a release', 'internal', 'release_saves', 'user_id', 'created_at'),
    FeatureSource('team_likes', 'Team likes', 'Community', 'Liked a team', 'internal', 'user_team_likes', 'user_id', 'created_at'),
)

FEATURES_BY_KEY = {source.key: source for source in FEATURE_SOURCES}

ALLOWED_PERIOD_DAYS = (7, 30, 90, 365)
DEFAULT_PERIOD_DAYS = 30


def clamp_period_days(raw: Any) -> int:
    """The request's `days` if it's one of the supported windows, else the default."""
    try:
        days = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_PERIOD_DAYS
    return days if days in ALLOWED_PERIOD_DAYS else DEFAULT_PERIOD_DAYS


# ------------------------------------------------------------------------
# MARK: ERROR SIGNATURES
# ------------------------------------------------------------------------

class ErrorSignature:
    """Collapses a logged build error into a stable group key by stripping the parts that
    vary per request (player names, years, ids), so one bug shows up as one row."""

    _RULES: tuple[tuple[re.Pattern, str], ...] = (
        (re.compile(r"^Cannot Find BRef Page for .+ in .+$", re.I), "Cannot Find BRef Page for {player} in {year}"),
        (re.compile(r"^Player not found in MLB API with name: .*", re.I), "Player not found in MLB API with name: {player} …"),
        # Pydantic: "1 validation error for Model\nfield\n  Value error, ..." -> model, field and message kind
        (re.compile(r"^\d+ validation errors? for (\w+)\n([\w.]+)\n\s*([^,\[]+).*", re.S), r"Validation error for \1.\2: \3"),
    )
    _NUMBER = re.compile(r"\d+(\.\d+)?")
    _WHITESPACE = re.compile(r"\s+")

    @classmethod
    def of(cls, error: Optional[str]) -> str:
        text = (error or '').strip()
        if not text:
            return 'Unknown error'
        for pattern, replacement in cls._RULES:
            if pattern.match(text):
                text = pattern.sub(replacement, text)
                break
        text = cls._NUMBER.sub('#', text)
        return cls._WHITESPACE.sub(' ', text).strip()


# ------------------------------------------------------------------------
# MARK: METRICS
# ------------------------------------------------------------------------

# Successful builds only: what users actually came away with
_YEAR_BUCKET_SQL = """
    CASE
        WHEN upper(year) = 'CAREER' THEN 'Career'
        WHEN strpos(year, '+') > 0 THEN 'Year combo'
        WHEN year ~ '^\\d{4}-\\d{4}$' THEN 'Year range'
        WHEN year ~ '^\\d{4}$' THEN substr(year, 1, 3) || '0s'
        ELSE 'Other'
    END
"""

# Dimensions for the Card Trends breakdowns: key -> SQL expression over log_custom_card_bot
_TREND_DIMENSIONS: dict[str, str] = {
    'set': "set",
    'expansion': "expansion",
    'edition': "edition",
    'image_parallel': "image_parallel",
    'period': "coalesce(period, user_inputs->>'stats_period_type')",
    'chart_version': "stats_offset::text",
    'stat_normalizer': "coalesce(user_inputs->>'stat_normalizer', 'NONE')",
    'image_source': "image_source",
    'era': "era",
    'data_source': "data_source",
    'league': "user_inputs->>'league'",
    'year_bucket': _YEAR_BUCKET_SQL,
    'generation_source': "generation_source",
}

# Dimensions for the failure-rate breakdowns. Failed rows have no card, so these read the inputs.
_FAILURE_DIMENSIONS: dict[str, str] = {
    'set': "coalesce(set, user_inputs->>'set')",
    'period': "user_inputs->>'stats_period_type'",
    # The requested source; successful rows' `data_source` is where stats were actually loaded from
    'data_source': "user_inputs->>'datasource'",
    'version': "version",
    'year_bucket': _YEAR_BUCKET_SQL,
    'generation_source': "generation_source",
}


class AdminMetrics:
    """Builds the admin dashboard payloads. Read-only; borrows one pooled connection."""

    def __init__(self, db: PostgresDB, days: int = DEFAULT_PERIOD_DAYS):
        self.db = db
        self.days = days

    # -- helpers ------------------------------------------------------------

    def _query(self, query: sql.Composable, params: Optional[dict] = None) -> list[dict]:
        """Run a read query and return JSON-ready rows. Unlike `PostgresDB.execute_query`, this
        raises on SQL errors (after rolling back) so a broken query surfaces as an error instead
        of an empty dashboard."""
        params = {'days': self.days, **(params or {})}
        try:
            with self.db.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = [self._jsonable(dict(row)) for row in cur.fetchall()]
            self.db.connection.rollback()  # end the read transaction; nothing was written
            return rows
        except Exception:
            self.db.connection.rollback()
            raise

    @staticmethod
    def _jsonable(row: dict) -> dict:
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                row[key] = value.isoformat()
            elif isinstance(value, Decimal):
                row[key] = float(value)
        return row

    @staticmethod
    def _window(alias_time: sql.Composable, periods: int = 1) -> sql.Composed:
        """`time >= now() - days * periods`. Two periods covers the comparison window too."""
        return sql.SQL("{t} >= now() - make_interval(days => %(days)s * {n})").format(t=alias_time, n=sql.Literal(periods))

    @staticmethod
    def _union(parts: Iterable[sql.Composable]) -> sql.Composed:
        return sql.SQL(" UNION ALL ").join(parts)

    def _activity_union(self, periods: int = 1, user_id: Optional[str] = None, signed_in_only: bool = False,
                        with_detail: bool = False, per_source_limit: Optional[int] = None) -> sql.Composed:
        """Every feature's actions as rows of (feature, user_id, at[, detail]). With `with_detail`
        (the activity timeline), sources marked `in_timeline=False` are left out."""
        parts = []
        for source in FEATURE_SOURCES:
            if with_detail and not source.in_timeline:
                continue
            columns = [sql.Literal(source.key) + sql.SQL(" AS feature"),
                       sql.SQL("{}::text AS user_id").format(source.user),
                       source.time + sql.SQL(" AS at")]
            if with_detail:
                columns.append(sql.SQL("({})::text AS detail").format(source.detail))
            conditions = [self._window(source.time, periods) if periods else sql.SQL("TRUE")]
            if user_id is not None:
                conditions.append(sql.SQL("{}::text = %(user_id)s").format(source.user))
            elif signed_in_only:
                conditions.append(sql.SQL("{} IS NOT NULL").format(source.user))
            select = source.select(sql.SQL(", ").join(columns), sql.SQL(" AND ").join(conditions))
            if per_source_limit:
                select = sql.SQL("({} ORDER BY at DESC LIMIT {})").format(select, sql.Literal(per_source_limit))
            parts.append(select)
        return self._union(parts)

    # -- overview -----------------------------------------------------------

    def overview(self) -> dict:
        """Headline numbers vs the previous period, a daily series, and usage per feature."""
        builds = self._query(sql.SQL("""
            SELECT
                count(*) FILTER (WHERE cur)                                         AS builds,
                count(*) FILTER (WHERE NOT cur)                                     AS previous_builds,
                count(*) FILTER (WHERE cur AND error IS NOT NULL)                   AS failed,
                count(*) FILTER (WHERE NOT cur AND error IS NOT NULL)               AS previous_failed,
                count(*) FILTER (WHERE cur AND user_id IS NULL)                     AS anonymous_builds,
                count(*) FILTER (WHERE NOT cur AND user_id IS NULL)                 AS previous_anonymous_builds,
                count(DISTINCT user_id) FILTER (WHERE cur)                          AS signed_in_builders,
                count(DISTINCT user_id) FILTER (WHERE NOT cur)                      AS previous_signed_in_builders
            FROM (
                SELECT error, user_id, created_on >= now() - make_interval(days => %(days)s) AS cur
                FROM internal.log_custom_card_bot
                WHERE created_on >= now() - make_interval(days => %(days)s * 2)
            ) b
        """))[0]

        accounts = self._query(sql.SQL("""
            SELECT
                count(*)                                                                                AS total_accounts,
                count(*) FILTER (WHERE created_at >= now() - make_interval(days => %(days)s))           AS signups,
                count(*) FILTER (WHERE created_at <  now() - make_interval(days => %(days)s)
                                   AND created_at >= now() - make_interval(days => %(days)s * 2))       AS previous_signups,
                count(*) FILTER (WHERE last_sign_in_at >= now() - make_interval(days => %(days)s))      AS signed_in
            FROM auth.users
        """))[0]

        activity = self._activity_union(periods=2, signed_in_only=True)
        active = self._query(sql.SQL("""
            SELECT
                count(DISTINCT user_id) FILTER (WHERE at >= now() - make_interval(days => %(days)s)) AS active_accounts,
                count(DISTINCT user_id) FILTER (WHERE at <  now() - make_interval(days => %(days)s)) AS previous_active_accounts
            FROM ({activity}) a
        """).format(activity=activity))[0]

        daily = self._query(sql.SQL("""
            WITH days AS (
                SELECT generate_series((now() - make_interval(days => %(days)s - 1))::date, now()::date, '1 day')::date AS day
            ),
            builds AS (
                SELECT created_on::date AS day, count(*) AS builds, count(*) FILTER (WHERE error IS NOT NULL) AS failed,
                       count(*) FILTER (WHERE user_id IS NULL) AS anonymous_builds
                FROM internal.log_custom_card_bot
                WHERE created_on >= now() - make_interval(days => %(days)s)
                GROUP BY 1
            ),
            signups AS (
                SELECT created_at::date AS day, count(*) AS signups
                FROM auth.users WHERE created_at >= now() - make_interval(days => %(days)s)
                GROUP BY 1
            ),
            active AS (
                SELECT at::date AS day, count(DISTINCT user_id) AS active_accounts
                FROM ({activity}) a
                GROUP BY 1
            )
            SELECT d.day AS date,
                   coalesce(b.builds, 0) AS builds, coalesce(b.failed, 0) AS failed,
                   coalesce(b.anonymous_builds, 0) AS anonymous_builds,
                   coalesce(s.signups, 0) AS signups, coalesce(a.active_accounts, 0) AS active_accounts
            FROM days d
            LEFT JOIN builds b USING (day)
            LEFT JOIN signups s USING (day)
            LEFT JOIN active a USING (day)
            ORDER BY d.day
        """).format(activity=self._activity_union(periods=1, signed_in_only=True)))

        feature_parts = [
            source.select(
                sql.SQL("""
                    {key} AS feature,
                    count(*) FILTER (WHERE {t} >= now() - make_interval(days => %(days)s))                       AS actions,
                    count(*) FILTER (WHERE {t} <  now() - make_interval(days => %(days)s))                       AS previous_actions,
                    count(DISTINCT {u}) FILTER (WHERE {t} >= now() - make_interval(days => %(days)s))            AS users,
                    count(DISTINCT {u}) FILTER (WHERE {t} <  now() - make_interval(days => %(days)s))            AS previous_users,
                    count(*) FILTER (WHERE {u} IS NULL AND {t} >= now() - make_interval(days => %(days)s))       AS anonymous_actions
                """).format(key=sql.Literal(source.key), t=source.time, u=source.user),
                self._window(source.time, periods=2),
            )
            for source in FEATURE_SOURCES
        ]
        feature_rows = {row['feature']: row for row in self._query(self._union(feature_parts))}

        return {
            'days': self.days,
            'builds': builds,
            'visitors': self._visitors(),
            'accounts': {**accounts, **active},
            'daily': daily,
            'features': [
                {'key': source.key, 'label': source.label, 'area': source.area, **feature_rows.get(source.key, {})}
                for source in FEATURE_SOURCES
            ],
        }

    def _visitors(self) -> dict:
        """Visitors (distinct browser ids), sessions and sign-ins from `internal.log_event`, plus
        where sessions came from and which parts of the site get viewed. Only covers the time since
        event logging shipped (`tracked_since`)."""
        totals = self._query(sql.SQL("""
            SELECT
                count(DISTINCT anon_id) FILTER (WHERE cur)                                  AS visitors,
                count(DISTINCT anon_id) FILTER (WHERE NOT cur)                              AS previous_visitors,
                count(DISTINCT anon_id) FILTER (WHERE cur AND user_id IS NOT NULL)          AS signed_in_visitors,
                count(*) FILTER (WHERE cur AND event = 'session_start')                     AS sessions,
                count(*) FILTER (WHERE NOT cur AND event = 'session_start')                 AS previous_sessions,
                count(*) FILTER (WHERE cur AND event = 'sign_in')                           AS sign_ins,
                count(*) FILTER (WHERE NOT cur AND event = 'sign_in')                       AS previous_sign_ins,
                count(*) FILTER (WHERE cur AND event = 'page_view')                         AS page_views,
                (SELECT min(created_at) FROM internal.log_event)                            AS tracked_since
            FROM (
                SELECT event, anon_id, user_id, created_at >= now() - make_interval(days => %(days)s) AS cur
                FROM internal.log_event
                WHERE created_at >= now() - make_interval(days => %(days)s * 2)
            ) e
        """))[0]
        daily = self._query(sql.SQL("""
            WITH days AS (
                SELECT generate_series((now() - make_interval(days => %(days)s - 1))::date, now()::date, '1 day')::date AS day
            )
            SELECT d.day AS date,
                   count(DISTINCT e.anon_id)                              AS visitors,
                   count(e.id) FILTER (WHERE e.event = 'session_start')   AS sessions,
                   count(e.id) FILTER (WHERE e.event = 'sign_in')         AS sign_ins
            FROM days d
            LEFT JOIN internal.log_event e
              ON e.created_at::date = d.day AND e.created_at >= now() - make_interval(days => %(days)s)
            GROUP BY d.day ORDER BY d.day
        """))
        sections = self._query(sql.SQL("""
            SELECT '/' || split_part(route, '/', 2) AS label, count(*) AS count, count(DISTINCT anon_id) AS visitors
            FROM internal.log_event
            WHERE event = 'page_view' AND created_at >= now() - make_interval(days => %(days)s)
            GROUP BY 1 ORDER BY 2 DESC LIMIT 15
        """))
        sessions_by = {
            key: self._query(sql.SQL("""
                SELECT coalesce({expr}, {fallback}) AS label, count(*) AS count
                FROM internal.log_event
                WHERE event = 'session_start' AND created_at >= now() - make_interval(days => %(days)s)
                GROUP BY 1 ORDER BY 2 DESC LIMIT 10
            """).format(expr=sql.SQL(expr), fallback=sql.Literal(fallback)))
            for key, expr, fallback in (
                ('referrers', "properties->>'referrer_host'", 'Direct'),
                ('devices', "properties->>'device'", 'Unknown'),
                ('campaigns', "nullif(concat_ws(' / ', properties->>'utm_source', properties->>'utm_campaign'), '')", 'None'),
            )
        }
        return {'totals': totals, 'daily': daily, 'sections': sections, **sessions_by}

    # -- builder failures ---------------------------------------------------

    def _breakdowns(self, dimensions: dict[str, str], select_sql: str, where_sql: str, limit: int = 15) -> dict[str, list[dict]]:
        """One scan, many GROUP BYs: each dimension's buckets with `select_sql`'s aggregates,
        biggest first."""
        keys = list(dimensions)
        dim_columns = sql.SQL(", ").join(
            sql.SQL("({}) AS {}").format(sql.SQL(expr), sql.Identifier(key)) for key, expr in dimensions.items()
        )
        grouping_sets = sql.SQL(", ").join(sql.SQL("({})").format(sql.Identifier(key)) for key in keys)
        rows = self._query(sql.SQL("""
            WITH src AS (
                SELECT {dims}, error, user_id FROM internal.log_custom_card_bot
                WHERE created_on >= now() - make_interval(days => %(days)s) AND ({where})
            )
            SELECT {grouping} AS grouping_id, {key_columns}, {aggregates}
            FROM src GROUP BY GROUPING SETS ({sets})
        """).format(
            dims=dim_columns,
            where=sql.SQL(where_sql),
            grouping=sql.SQL("GROUPING({})").format(sql.SQL(", ").join(sql.Identifier(k) for k in keys)),
            key_columns=sql.SQL(", ").join(sql.Identifier(k) for k in keys),
            aggregates=sql.SQL(select_sql),
            sets=grouping_sets,
        ))
        # GROUPING() sets a bit per column left out of the set, first column = highest bit
        out: dict[str, list[dict]] = {key: [] for key in keys}
        for row in rows:
            for index, key in enumerate(keys):
                bit = 1 << (len(keys) - 1 - index)
                if not row['grouping_id'] & bit:
                    aggregates = {k: v for k, v in row.items() if k not in keys and k != 'grouping_id'}
                    out[key].append({'label': row[key] if row[key] not in (None, '') else 'None', **aggregates})
                    break
        for key in keys:
            out[key].sort(key=lambda r: r.get('count', 0), reverse=True)
            out[key] = out[key][:limit]
        return out

    def failures(self) -> dict:
        """Failure rate over time, failures grouped by signature, rate by input, and the latest failures."""
        daily = self._query(sql.SQL("""
            WITH days AS (
                SELECT generate_series((now() - make_interval(days => %(days)s - 1))::date, now()::date, '1 day')::date AS day
            )
            SELECT d.day AS date, count(l.id) AS builds, count(l.error) AS failed
            FROM days d
            LEFT JOIN internal.log_custom_card_bot l
              ON l.created_on::date = d.day AND l.created_on >= now() - make_interval(days => %(days)s)
            GROUP BY d.day ORDER BY d.day
        """))

        failed_rows = self._query(sql.SQL("""
            SELECT l.id, l.created_on, l.error, l.error_for_user, l.user_id, l.version,
                   l.error_type, l.error_stage, l.error_detail, l.generation_source, l.request_duration,
                   l.name, l.year, coalesce(l.set, l.user_inputs->>'set') AS set,
                   l.user_inputs->>'stats_period_type' AS period,
                   l.user_inputs->>'datasource' AS data_source,
                   u.email
            FROM internal.log_custom_card_bot l
            LEFT JOIN auth.users u ON u.id::text = l.user_id
            WHERE l.created_on >= now() - make_interval(days => %(days)s) AND l.error IS NOT NULL
            ORDER BY l.created_on DESC
        """))

        groups: dict[str, dict] = {}
        for row in failed_rows:
            signature = ErrorSignature.of(row['error'])
            group = groups.setdefault(signature, {
                'signature': signature, 'count': 0, 'user_ids': set(), 'anonymous': 0,
                'first_seen': row['created_on'], 'last_seen': row['created_on'],
                'versions': set(), 'sample_error': row['error'], 'sample_error_for_user': row['error_for_user'],
                'shown_raw': 0, 'sample_ids': [], 'stages': {}, 'error_types': set(), 'sample_detail': None,
            })
            group['count'] += 1
            if row['user_id']:
                group['user_ids'].add(row['user_id'])
            else:
                group['anonymous'] += 1
            group['first_seen'] = min(group['first_seen'], row['created_on'])
            group['last_seen'] = max(group['last_seen'], row['created_on'])
            if row['version']:
                group['versions'].add(row['version'])
            # The user saw the raw exception text: an unhandled error, not a friendly message
            if (row['error_for_user'] or '') == (row['error'] or ''):
                group['shown_raw'] += 1
            if len(group['sample_ids']) < 5:
                group['sample_ids'].append(row['id'])
            # Rows are newest first, so this keeps the latest traceback
            if row['error_detail'] and not group['sample_detail']:
                group['sample_detail'] = row['error_detail']
            if row['error_type']:
                group['error_types'].add(row['error_type'])
            if row['error_stage']:
                group['stages'][row['error_stage']] = group['stages'].get(row['error_stage'], 0) + 1

        grouped = sorted(groups.values(), key=lambda g: g['count'], reverse=True)
        for group in grouped:
            group['users'] = len(group.pop('user_ids'))
            group['versions'] = sorted(group['versions'], reverse=True)
            group['error_types'] = sorted(group['error_types'])

        breakdowns = self._breakdowns(
            _FAILURE_DIMENSIONS,
            select_sql="count(*) AS count, count(error) AS failed",
            where_sql="TRUE",
        )
        for buckets in breakdowns.values():
            for bucket in buckets:
                bucket['failure_rate'] = bucket['failed'] / bucket['count'] if bucket['count'] else 0
            buckets.sort(key=lambda b: b['failed'], reverse=True)

        def count_failures_by(key: str) -> list[dict]:
            counts: dict[str, int] = {}
            for row in failed_rows:
                label = row[key] or 'Not recorded'
                counts[label] = counts.get(label, 0) + 1
            return [{'label': label, 'count': count} for label, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)]

        # Builds that never reached the server's log: the browser reported them (see api/events.py)
        client_errors = self._query(sql.SQL("""
            SELECT e.created_at, e.properties->>'message' AS message, e.properties->>'generation_source' AS generation_source,
                   e.user_id, u.email
            FROM internal.log_event e
            LEFT JOIN auth.users u ON u.id::text = e.user_id
            WHERE e.event = 'builder_client_error' AND e.created_at >= now() - make_interval(days => %(days)s)
            ORDER BY e.created_at DESC
        """))

        total_builds = sum(day['builds'] for day in daily)
        for row in failed_rows:
            row.pop('error_detail', None)  # tracebacks travel once per group, not per row
        return {
            'days': self.days,
            'totals': {
                'builds': total_builds,
                'failed': len(failed_rows),
                'shown_raw': sum(g['shown_raw'] for g in grouped),
                'signatures': len(grouped),
                'client_errors': len(client_errors),
            },
            'by_stage': count_failures_by('error_stage'),
            'by_type': count_failures_by('error_type'),
            'client_errors': client_errors[:50],
            'daily': daily,
            'groups': grouped,
            'breakdowns': breakdowns,
            'recent': failed_rows[:100],
        }

    # -- card trends --------------------------------------------------------

    def card_trends(self) -> dict:
        """What people build: share of successful builds by each setting, top players, and builds per day by set."""
        breakdowns = self._breakdowns(
            _TREND_DIMENSIONS,
            select_sql="count(*) AS count, count(DISTINCT user_id) AS users",
            where_sql="error IS NULL",
            limit=20,
        )
        flags = self._query(sql.SQL("""
            SELECT
                count(*)                                                            AS builds,
                count(*) FILTER (WHERE lower(user_inputs->>'randomize') IN ('true', '1'))        AS shuffles,
                count(*) FILTER (WHERE is_dark_mode)                                AS dark_mode,
                count(*) FILTER (WHERE hide_team_logo)                              AS hide_team_logo,
                count(*) FILTER (WHERE lower(user_inputs->>'is_bordered') IN ('true', '1'))      AS bordered,
                count(*) FILTER (WHERE image_source IN ('Upload', 'Link'))                     AS own_image,
                count(*) FILTER (WHERE is_variable_spd_00_01)                       AS variable_speed
            FROM internal.log_custom_card_bot
            WHERE created_on >= now() - make_interval(days => %(days)s) AND error IS NULL
        """))[0]
        top_players = self._query(sql.SQL("""
            SELECT bref_id, max(name) AS name, count(*) AS count, count(DISTINCT user_id) AS users,
                   count(*) FILTER (WHERE lower(user_inputs->>'randomize') IN ('true', '1')) AS shuffles
            FROM internal.log_custom_card_bot
            WHERE created_on >= now() - make_interval(days => %(days)s) AND error IS NULL AND bref_id IS NOT NULL
            GROUP BY bref_id ORDER BY count(*) DESC LIMIT 25
        """))
        daily_by_set = self._query(sql.SQL("""
            SELECT created_on::date AS date, set, count(*) AS count
            FROM internal.log_custom_card_bot
            WHERE created_on >= now() - make_interval(days => %(days)s) AND error IS NULL
            GROUP BY 1, 2 ORDER BY 1
        """))
        return {
            'days': self.days,
            'flags': flags,
            'breakdowns': breakdowns,
            'top_players': top_players,
            'daily_by_set': daily_by_set,
        }

    # -- users ----------------------------------------------------------------

    def users(self) -> dict:
        """Every account with its activity in the period, most active first."""
        rows = self._query(sql.SQL("""
            WITH activity AS ({activity})
            SELECT u.id::text AS user_id, u.email, p.username,
                   u.raw_app_meta_data->>'provider' AS provider,
                   u.created_at, u.last_sign_in_at,
                   count(a.at)                                                AS actions,
                   count(a.at) FILTER (WHERE a.feature = 'card_builds')       AS builds,
                   count(DISTINCT a.feature)                                  AS features_used,
                   max(a.at)                                                  AS last_active_at
            FROM auth.users u
            LEFT JOIN public.profiles p ON p.id = u.id
            LEFT JOIN activity a ON a.user_id = u.id::text
            GROUP BY u.id, u.email, p.username, u.raw_app_meta_data, u.created_at, u.last_sign_in_at
            ORDER BY count(a.at) DESC, u.last_sign_in_at DESC NULLS LAST
        """).format(activity=self._activity_union(periods=1, signed_in_only=True)))
        return {'days': self.days, 'users': rows}

    def user_detail(self, user_id: str) -> Optional[dict]:
        """One account: profile, per-feature totals (all time and in the period), daily activity,
        a recent activity timeline and recent card builds."""
        profile = self._query(sql.SQL("""
            SELECT u.id::text AS user_id, u.email, p.username, p.avatar_url,
                   u.raw_app_meta_data->>'provider' AS provider,
                   u.created_at, u.last_sign_in_at
            FROM auth.users u LEFT JOIN public.profiles p ON p.id = u.id
            WHERE u.id::text = %(user_id)s
        """), {'user_id': user_id})
        if not profile:
            return None

        params = {'user_id': user_id}
        totals = {row['feature']: row for row in self._query(sql.SQL("""
            SELECT feature, count(*) AS all_time,
                   count(*) FILTER (WHERE at >= now() - make_interval(days => %(days)s)) AS period,
                   min(at) AS first_at, max(at) AS last_at
            FROM ({activity}) a GROUP BY feature
        """).format(activity=self._activity_union(periods=0, user_id=user_id)), params)}

        daily = self._query(sql.SQL("""
            WITH days AS (
                SELECT generate_series((now() - make_interval(days => %(days)s - 1))::date, now()::date, '1 day')::date AS day
            )
            SELECT d.day AS date, count(a.at) AS actions
            FROM days d LEFT JOIN ({activity}) a ON a.at::date = d.day
            GROUP BY d.day ORDER BY d.day
        """).format(activity=self._activity_union(periods=1, user_id=user_id)), params)

        timeline = self._query(sql.SQL("""
            SELECT feature, at, detail FROM ({activity}) a ORDER BY at DESC LIMIT 60
        """).format(activity=self._activity_union(periods=0, user_id=user_id, with_detail=True, per_source_limit=60)), params)
        for event in timeline:
            source = FEATURES_BY_KEY[event['feature']]
            event['action'] = source.action
            event['area'] = source.area

        recent_builds = self._query(sql.SQL("""
            SELECT id, created_on, name, year, coalesce(set, user_inputs->>'set') AS set, expansion, edition,
                   image_parallel, coalesce(period, user_inputs->>'stats_period_type') AS period,
                   error, error_for_user
            FROM internal.log_custom_card_bot
            WHERE user_id = %(user_id)s
            ORDER BY created_on DESC LIMIT 25
        """), params)

        return {
            'days': self.days,
            'profile': profile[0],
            'features': [
                {'key': source.key, 'label': source.label, 'area': source.area,
                 **totals.get(source.key, {'all_time': 0, 'period': 0, 'first_at': None, 'last_at': None})}
                for source in FEATURE_SOURCES
            ],
            'daily': daily,
            'timeline': timeline,
            'recent_builds': recent_builds,
        }
