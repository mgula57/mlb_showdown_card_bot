"""Read-only analytics for the admin dashboard (`/admin`).

Counts come from the nightly rollup (`admin_rollup.py`) plus a live pass over the days it hasn't
covered yet, so loads stay fast however long the period. Detail that needs raw rows (grouped
failures, visitors, one account's timeline) reads the logs directly, over small slices.

What gets counted is defined once in `admin_sources.py`. Periods are whole UTC days ending today.
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from .admin_rollup import AdminRollup
from .admin_sources import FEATURE_SOURCES, FEATURES_BY_KEY
from .postgres_db import PostgresDB

ALLOWED_PERIOD_DAYS = (7, 30, 90, 365)
DEFAULT_PERIOD_DAYS = 30

# First day of the current period, and of the current + previous periods (for comparisons)
_PERIOD_START = sql.SQL("(current_date - (%(days)s - 1))")
_COMPARISON_START = sql.SQL("(current_date - (%(days)s * 2 - 1))")
# Raw-log filter for the current period, matching the rollup's whole-day windows
_RAW_PERIOD_START = sql.SQL("(current_date - (%(days)s - 1))::timestamp")


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

# Dimensions each tab breaks builds down by
TREND_DIMENSIONS = (
    'set', 'expansion', 'edition', 'image_parallel', 'period', 'chart_version', 'stat_normalizer',
    'image_source', 'era', 'data_source', 'league', 'year_bucket', 'generation_source', 'player_type', 'points',
)
FAILURE_DIMENSIONS = ('set', 'period', 'requested_source', 'version', 'year_bucket', 'generation_source')


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
    def _with(*names: str, start: sql.Composable = _COMPARISON_START) -> sql.Composed:
        """`WITH` clause exposing the rolled-up `activity` and/or `builds` rows from `start` through today."""
        return sql.SQL("WITH ") + sql.SQL(", ").join(AdminRollup.with_live_tail(name, start) for name in names)

    @staticmethod
    def _period_days() -> sql.SQL:
        return sql.SQL("SELECT generate_series(current_date - (%(days)s - 1), current_date, '1 day')::date AS day")

    def _build_buckets(self) -> dict[str, dict[str, dict]]:
        """Builds in the current period per dimension and value: {dimension: {value: {builds, failed}}}."""
        rows = self._query(self._with('builds', start=_PERIOD_START) + sql.SQL("""
            SELECT dimension, value, sum(builds)::int AS builds, sum(failed)::int AS failed
            FROM builds GROUP BY dimension, value
        """))
        out: dict[str, dict[str, dict]] = {}
        for row in rows:
            out.setdefault(row['dimension'], {})[row['value']] = {'builds': row['builds'], 'failed': row['failed']}
        return out

    @staticmethod
    def _activity_union(user_id: str, recent_only: bool, with_detail: bool = False, per_source_limit: Optional[int] = None) -> sql.Composed:
        """One account's raw actions across every feature, as (feature, at[, detail])."""
        parts = []
        for source in FEATURE_SOURCES:
            if with_detail and not source.in_timeline:
                continue
            columns = [sql.Literal(source.key) + sql.SQL(" AS feature"), source.time + sql.SQL(" AS at")]
            if with_detail:
                columns.append(sql.SQL("({})::text AS detail").format(source.detail))
            conditions = [sql.SQL("{}::text = %(user_id)s").format(source.user)]
            if recent_only:
                conditions.append(sql.SQL("{} >= ({})::timestamptz").format(source.time, _PERIOD_START))
            select = source.select(sql.SQL(", ").join(columns), sql.SQL(" AND ").join(conditions))
            if per_source_limit:
                select = sql.SQL("({} ORDER BY at DESC LIMIT {})").format(select, sql.Literal(per_source_limit))
            parts.append(select)
        return sql.SQL(" UNION ALL ").join(parts)

    # -- overview -----------------------------------------------------------

    def overview(self) -> dict:
        """Headline numbers vs the previous period, a daily series, and usage per feature."""
        current = sql.SQL("day >= {}").format(_PERIOD_START)
        builds = self._query(self._with('builds') + sql.SQL("""
            SELECT
                coalesce(sum(builds) FILTER (WHERE {cur}), 0)::int                AS builds,
                coalesce(sum(builds) FILTER (WHERE NOT {cur}), 0)::int            AS previous_builds,
                coalesce(sum(failed) FILTER (WHERE {cur}), 0)::int                AS failed,
                coalesce(sum(failed) FILTER (WHERE NOT {cur}), 0)::int            AS previous_failed,
                coalesce(sum(anonymous_builds) FILTER (WHERE {cur}), 0)::int      AS anonymous_builds,
                coalesce(sum(anonymous_builds) FILTER (WHERE NOT {cur}), 0)::int  AS previous_anonymous_builds
            FROM builds WHERE dimension = 'all'
        """).format(cur=current))[0]

        active = self._query(self._with('activity') + sql.SQL("""
            SELECT
                count(DISTINCT user_id) FILTER (WHERE {cur})                                  AS active_accounts,
                count(DISTINCT user_id) FILTER (WHERE NOT {cur})                              AS previous_active_accounts,
                count(DISTINCT user_id) FILTER (WHERE {cur} AND feature = 'card_builds')      AS signed_in_builders,
                count(DISTINCT user_id) FILTER (WHERE NOT {cur} AND feature = 'card_builds')  AS previous_signed_in_builders
            FROM activity WHERE user_id <> ''
        """).format(cur=current))[0]
        builds['signed_in_builders'] = active.pop('signed_in_builders')
        builds['previous_signed_in_builders'] = active.pop('previous_signed_in_builders')

        accounts = self._query(sql.SQL("""
            SELECT
                count(*)                                                                     AS total_accounts,
                count(*) FILTER (WHERE created_at >= {cur}::timestamptz)                     AS signups,
                count(*) FILTER (WHERE created_at <  {cur}::timestamptz
                                   AND created_at >= {prev}::timestamptz)                    AS previous_signups,
                count(*) FILTER (WHERE last_sign_in_at >= {cur}::timestamptz)                AS signed_in
            FROM auth.users
        """).format(cur=_PERIOD_START, prev=_COMPARISON_START))[0]

        daily = self._query(self._with('builds', 'activity', start=_PERIOD_START) + sql.SQL(""",
            days AS ({days}),
            daily_builds AS (
                SELECT day, sum(builds) AS builds, sum(failed) AS failed, sum(anonymous_builds) AS anonymous_builds
                FROM builds WHERE dimension = 'all' GROUP BY day
            ),
            daily_active AS (
                SELECT day, count(DISTINCT user_id) AS active_accounts FROM activity WHERE user_id <> '' GROUP BY day
            ),
            signups AS (
                SELECT created_at::date AS day, count(*) AS signups
                FROM auth.users WHERE created_at >= {start}::timestamptz GROUP BY 1
            )
            SELECT d.day AS date,
                   coalesce(b.builds, 0)::int AS builds, coalesce(b.failed, 0)::int AS failed,
                   coalesce(b.anonymous_builds, 0)::int AS anonymous_builds,
                   coalesce(s.signups, 0)::int AS signups, coalesce(a.active_accounts, 0)::int AS active_accounts
            FROM days d
            LEFT JOIN daily_builds b USING (day)
            LEFT JOIN daily_active a USING (day)
            LEFT JOIN signups s USING (day)
            ORDER BY d.day
        """).format(days=self._period_days(), start=_PERIOD_START))

        feature_rows = {row['feature']: row for row in self._query(self._with('activity') + sql.SQL("""
            SELECT feature,
                   coalesce(sum(actions) FILTER (WHERE {cur}), 0)::int                          AS actions,
                   coalesce(sum(actions) FILTER (WHERE NOT {cur}), 0)::int                      AS previous_actions,
                   count(DISTINCT nullif(user_id, '')) FILTER (WHERE {cur})                     AS users,
                   count(DISTINCT nullif(user_id, '')) FILTER (WHERE NOT {cur})                 AS previous_users,
                   coalesce(sum(actions) FILTER (WHERE {cur} AND user_id = ''), 0)::int         AS anonymous_actions
            FROM activity GROUP BY feature
        """).format(cur=current))}

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
        params = dict(cur=_RAW_PERIOD_START, prev=sql.SQL("(current_date - (%(days)s * 2 - 1))::timestamp"))
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
                SELECT event, anon_id, user_id, created_at >= {cur} AS cur
                FROM internal.log_event
                WHERE created_at >= {prev}
            ) e
        """).format(**params))[0]
        daily = self._query(sql.SQL("""
            WITH days AS ({days})
            SELECT d.day AS date,
                   count(DISTINCT e.anon_id)                              AS visitors,
                   count(e.id) FILTER (WHERE e.event = 'session_start')   AS sessions,
                   count(e.id) FILTER (WHERE e.event = 'sign_in')         AS sign_ins
            FROM days d
            LEFT JOIN internal.log_event e ON e.created_at::date = d.day AND e.created_at >= {cur}
            GROUP BY d.day ORDER BY d.day
        """).format(days=self._period_days(), **params))
        sections = self._query(sql.SQL("""
            SELECT '/' || split_part(route, '/', 2) AS label, count(*) AS count, count(DISTINCT anon_id) AS visitors
            FROM internal.log_event
            WHERE event = 'page_view' AND created_at >= {cur}
            GROUP BY 1 ORDER BY 2 DESC LIMIT 15
        """).format(**params))
        sessions_by = {
            key: self._query(sql.SQL("""
                SELECT coalesce({expr}, {fallback}) AS label, count(*) AS count
                FROM internal.log_event
                WHERE event = 'session_start' AND created_at >= {cur}
                GROUP BY 1 ORDER BY 2 DESC LIMIT 10
            """).format(expr=sql.SQL(expr), fallback=sql.Literal(fallback), **params))
            for key, expr, fallback in (
                ('referrers', "properties->>'referrer_host'", 'Direct'),
                ('devices', "properties->>'device'", 'Unknown'),
                ('campaigns', "nullif(concat_ws(' / ', properties->>'utm_source', properties->>'utm_campaign'), '')", 'None'),
            )
        }
        return {'totals': totals, 'daily': daily, 'sections': sections, **sessions_by}

    # -- builder failures ---------------------------------------------------

    def _daily_builds(self) -> list[dict]:
        return self._query(self._with('builds', start=_PERIOD_START) + sql.SQL(""",
            days AS ({days})
            SELECT d.day AS date, coalesce(sum(b.builds), 0)::int AS builds, coalesce(sum(b.failed), 0)::int AS failed
            FROM days d LEFT JOIN builds b ON b.day = d.day AND b.dimension = 'all'
            GROUP BY d.day ORDER BY d.day
        """).format(days=self._period_days()))

    def failures(self) -> dict:
        """Failure rate over time, failures grouped by signature, rate by input, and the latest failures."""
        daily = self._daily_builds()

        failed_rows = self._query(sql.SQL("""
            SELECT l.id, l.created_on, l.error, l.error_for_user, l.user_id, l.version,
                   l.error_type, l.error_stage, l.error_detail, l.generation_source, l.request_duration,
                   l.name, l.year, coalesce(l.set, l.user_inputs->>'set') AS set,
                   l.user_inputs->>'stats_period_type' AS period,
                   l.user_inputs->>'datasource' AS data_source,
                   u.email
            FROM internal.log_custom_card_bot l
            LEFT JOIN auth.users u ON u.id::text = l.user_id
            WHERE l.created_on >= {start} AND l.error IS NOT NULL
            ORDER BY l.created_on DESC
        """).format(start=_RAW_PERIOD_START))

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

        buckets = self._build_buckets()
        breakdowns = {
            dimension: sorted(
                ({'label': value, 'count': b['builds'], 'failed': b['failed'],
                  'failure_rate': b['failed'] / b['builds'] if b['builds'] else 0}
                 for value, b in buckets.get(dimension, {}).items() if b['failed']),
                key=lambda bucket: bucket['failed'], reverse=True,
            )[:15]
            for dimension in FAILURE_DIMENSIONS
        }

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
            WHERE e.event = 'builder_client_error' AND e.created_at >= {start}
            ORDER BY e.created_at DESC
        """).format(start=_RAW_PERIOD_START))

        for row in failed_rows:
            row.pop('error_detail', None)  # tracebacks travel once per group, not per row
        return {
            'days': self.days,
            'totals': {
                'builds': sum(day['builds'] for day in daily),
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
        """What people build: successful builds by each setting, top players, and builds per day by set."""
        buckets = self._build_buckets()

        def successful(dimension: str) -> dict[str, int]:
            return {value: b['builds'] - b['failed'] for value, b in buckets.get(dimension, {}).items() if b['builds'] > b['failed']}

        breakdowns = {
            dimension: sorted(({'label': value, 'count': count} for value, count in successful(dimension).items()),
                              key=lambda bucket: bucket['count'], reverse=True)[:20]
            for dimension in TREND_DIMENSIONS
        }
        # Points read best in point order, not by size
        breakdowns['points'] = sorted(
            ({'label': value, 'count': count} for value, count in successful('points').items() if value.isdigit()),
            key=lambda bucket: int(bucket['label']),
        )

        flags = {'builds': successful('all').get('None', 0) + successful('all').get('', 0)}
        flags.update({flag: buckets.get('flag', {}).get(flag, {}).get('builds', 0)
                      for flag in ('shuffles', 'dark_mode', 'hide_team_logo', 'bordered', 'own_image', 'variable_speed')})

        # 'player' values are "bref_id|name"; a player's name can vary between builds, so keep the most built one
        players: dict[str, dict] = {}
        for value, count in successful('player').items():
            bref_id, _, name = value.partition('|')
            player = players.setdefault(bref_id, {'bref_id': bref_id, 'name': name, 'count': 0, 'top_name_count': 0})
            player['count'] += count
            if count > player['top_name_count']:
                player['name'], player['top_name_count'] = name, count
        top_players = [{k: v for k, v in p.items() if k != 'top_name_count'}
                       for p in sorted(players.values(), key=lambda p: p['count'], reverse=True)[:25]]

        daily_by_set = self._query(self._with('builds', start=_PERIOD_START) + sql.SQL("""
            SELECT day AS date, value AS set, sum(builds - failed)::int AS count
            FROM builds WHERE dimension = 'set'
            GROUP BY 1, 2 HAVING sum(builds - failed) > 0 ORDER BY 1
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
        rows = self._query(self._with('activity', start=_PERIOD_START) + sql.SQL(""",
            per_user AS (
                SELECT user_id,
                       sum(actions)::int                                            AS actions,
                       coalesce(sum(actions) FILTER (WHERE feature = 'card_builds'), 0)::int AS builds,
                       count(DISTINCT feature)                                      AS features_used,
                       max(day)                                                     AS last_active_at
                FROM activity WHERE user_id <> '' GROUP BY user_id
            )
            SELECT u.id::text AS user_id, u.email, p.username,
                   u.raw_app_meta_data->>'provider' AS provider,
                   u.created_at, u.last_sign_in_at,
                   coalesce(a.actions, 0) AS actions, coalesce(a.builds, 0) AS builds,
                   coalesce(a.features_used, 0) AS features_used, a.last_active_at
            FROM auth.users u
            LEFT JOIN public.profiles p ON p.id = u.id
            LEFT JOIN per_user a ON a.user_id = u.id::text
            ORDER BY coalesce(a.actions, 0) DESC, u.last_sign_in_at DESC NULLS LAST
        """))
        return {'days': self.days, 'users': rows}

    def user_detail(self, user_id: str) -> Optional[dict]:
        """One account: profile, per-feature totals (all time and in the period), daily activity,
        a recent activity timeline and recent card builds. Reads the raw logs (indexed by user)."""
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
                   count(*) FILTER (WHERE at >= {start}::timestamptz) AS period,
                   min(at) AS first_at, max(at) AS last_at
            FROM ({activity}) a GROUP BY feature
        """).format(start=_PERIOD_START, activity=self._activity_union(user_id, recent_only=False)), params)}

        daily = self._query(sql.SQL("""
            WITH days AS ({days})
            SELECT d.day AS date, count(a.at) AS actions
            FROM days d LEFT JOIN ({activity}) a ON a.at::date = d.day
            GROUP BY d.day ORDER BY d.day
        """).format(days=self._period_days(), activity=self._activity_union(user_id, recent_only=True)), params)

        timeline = self._query(sql.SQL("""
            SELECT feature, at, detail FROM ({activity}) a ORDER BY at DESC LIMIT 60
        """).format(activity=self._activity_union(user_id, recent_only=False, with_detail=True, per_source_limit=60)), params)
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
