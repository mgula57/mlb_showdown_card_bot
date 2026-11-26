"""What the admin dashboard counts: every product action (`FEATURE_SOURCES`) and every
dimension a card build is broken down by (`BUILD_DIMENSIONS`). Shared by the nightly rollup
(`admin_rollup.py`) and the dashboard queries (`admin_metrics.py`), so adding a feature or a
breakdown is one entry here.
"""

from dataclasses import dataclass

from psycopg2 import sql


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

    def time_between(self, from_day: sql.Composable, to_day: sql.Composable | None = None) -> sql.Composed:
        """Filter on the time column for whole days `from_day`..`to_day` (inclusive; open-ended
        without `to_day`). The bounds are dates compared to the raw column: casting the column
        (`time`) would stop Postgres using its index and scan the whole log."""
        condition = sql.SQL("{t} >= ({start})").format(t=sql.Identifier(self.time_column), start=from_day)
        if to_day is None:
            return condition
        return condition + sql.SQL(" AND {t} < (({end}) + 1)").format(t=sql.Identifier(self.time_column), end=to_day)

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


# ------------------------------------------------------------------------
# MARK: BUILD DIMENSIONS
# ------------------------------------------------------------------------

_YEAR_BUCKET_SQL = """
    CASE
        WHEN upper(year) = 'CAREER' THEN 'Career'
        WHEN strpos(year, '+') > 0 THEN 'Year combo'
        WHEN year ~ '^\\d{4}-\\d{4}$' THEN 'Year range'
        WHEN year ~ '^\\d{4}$' THEN substr(year, 1, 3) || '0s'
        ELSE 'Other'
    END
"""

_IS_TRUE = "lower(user_inputs->>'{key}') IN ('true', '1')"


@dataclass(frozen=True)
class BuildDimension:
    """One way to split card builds, as an SQL expression over `internal.log_custom_card_bot`.

    Regular dimensions put every build in a bucket (missing values become 'None'). `sparse`
    ones only count builds where the expression isn't null: top players, and the on/off flags,
    which share the `flag` dimension with one value per flag."""
    key: str
    expr: str
    sparse: bool = False


BUILD_DIMENSIONS: tuple[BuildDimension, ...] = (
    BuildDimension('all', "''"),
    # Card settings. Failed builds have no card, so card columns fall back to the inputs where they can.
    BuildDimension('set', "coalesce(set, user_inputs->>'set')"),
    BuildDimension('expansion', "expansion"),
    BuildDimension('edition', "edition"),
    BuildDimension('image_parallel', "image_parallel"),
    BuildDimension('period', "coalesce(period, user_inputs->>'stats_period_type')"),
    BuildDimension('chart_version', "stats_offset::text"),
    BuildDimension('stat_normalizer', "coalesce(user_inputs->>'stat_normalizer', 'NONE')"),
    BuildDimension('image_source', "image_source"),
    BuildDimension('era', "era"),
    BuildDimension('league', "user_inputs->>'league'"),
    BuildDimension('year_bucket', _YEAR_BUCKET_SQL),
    BuildDimension('generation_source', "generation_source"),
    BuildDimension('version', "version"),
    # Where stats were loaded from (successful builds) vs the source that was asked for
    BuildDimension('data_source', "data_source"),
    BuildDimension('requested_source', "user_inputs->>'datasource'"),
    # From the built card
    BuildDimension('player_type', "CASE card_result->'chart'->>'is_pitcher' WHEN 'true' THEN 'Pitcher' WHEN 'false' THEN 'Hitter' END"),
    BuildDimension('points', "CASE WHEN card_result->>'points' ~ '^\\d+$' THEN (((card_result->>'points')::int / 50) * 50)::text END"),
    BuildDimension('player', "CASE WHEN error IS NULL AND bref_id IS NOT NULL THEN bref_id || '|' || coalesce(name, '') END", sparse=True),
    # On/off settings, successful builds only
    BuildDimension('flag', f"CASE WHEN error IS NULL AND {_IS_TRUE.format(key='randomize')} THEN 'shuffles' END", sparse=True),
    BuildDimension('flag', "CASE WHEN error IS NULL AND is_dark_mode THEN 'dark_mode' END", sparse=True),
    BuildDimension('flag', "CASE WHEN error IS NULL AND hide_team_logo THEN 'hide_team_logo' END", sparse=True),
    BuildDimension('flag', f"CASE WHEN error IS NULL AND {_IS_TRUE.format(key='is_bordered')} THEN 'bordered' END", sparse=True),
    BuildDimension('flag', "CASE WHEN error IS NULL AND image_source IN ('Upload', 'Link') THEN 'own_image' END", sparse=True),
    BuildDimension('flag', "CASE WHEN error IS NULL AND is_variable_spd_00_01 THEN 'variable_speed' END", sparse=True),
)
