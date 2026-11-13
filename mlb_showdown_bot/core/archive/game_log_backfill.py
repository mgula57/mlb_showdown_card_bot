import json
from dataclasses import dataclass, field
from time import sleep
from typing import Optional

from psycopg2 import sql

from ..database.postgres_db import PostgresDB
from ..card.stats.baseball_ref_scraper import BaseballReferenceScraper
from ..card.stats.stats_period import StatsPeriod, StatsPeriodType


@dataclass
class GameLogBackfillResult:
    """Running tally for a backfill run."""
    candidates: int = 0
    updated: int = 0
    failed: int = 0
    no_logs: int = 0
    requests: int = 0
    aborted_reason: Optional[str] = None
    failed_ids: list[str] = field(default_factory=list)


class GameLogBackfill:
    """Fills `stats.game_logs` and `stats.postseason_game_logs` on `player_season_stats` rows that were
    archived without them, by scraping only the Baseball Reference game log pages (not the whole player page).

    A key counts as present once it exists, even as `[]` (a player with no postseason games), so reruns only
    pick up rows that are still missing. Updates merge the keys into the existing `stats` JSONB and leave every
    other column, including `stats_modified_date`, untouched so downstream incremental card builds aren't triggered.

    Notes:
      - Baseball Reference postseason logs are career-wide (`year=0&post=1`) and filtered by year downstream,
        so they're fetched once per player per run and reused across that player's rows.
      - 2026+ seasons use the MLB API, not BREF, and are skipped.
    """

    FIRST_MLB_API_YEAR = 2026
    MAX_RATE_LIMIT_RETRIES = 3
    RATE_LIMIT_BACKOFF_SECONDS = 90.0
    MAX_CONSECUTIVE_FAILURES = 5

    def __init__(self, db: PostgresDB, delay: float = 4.0) -> None:
        self.db = db
        self.delay = delay
        self._postseason_cache: dict[tuple[str, str], list[dict]] = {}

# ------------------------------------------------------------------------
# COVERAGE
# ------------------------------------------------------------------------

    def coverage(self, years: list[int] = None, ignore_minimums: bool = False) -> list[dict]:
        """Per-year counts of qualifying rows, and how many have each game log key."""
        year_filter = sql.SQL("AND year = ANY(%s)") if years else sql.SQL("")
        query = sql.SQL("""
            SELECT year,
                count(*) AS total,
                count(*) FILTER (WHERE jsonb_typeof(stats->'game_logs') = 'array') AS has_game_logs,
                count(*) FILTER (WHERE jsonb_typeof(stats->'game_logs') = 'array' AND jsonb_array_length(stats->'game_logs') > 0) AS non_empty_game_logs,
                count(*) FILTER (WHERE jsonb_typeof(stats->'postseason_game_logs') = 'array') AS has_postseason,
                count(*) FILTER (WHERE jsonb_typeof(stats->'postseason_game_logs') = 'array' AND jsonb_array_length(stats->'postseason_game_logs') > 0) AS non_empty_postseason,
                count(*) FILTER (WHERE stats ? 'bref_id' IS NOT TRUE) AS no_stats
            FROM player_season_stats
            WHERE historical_date IS NULL
                {minimums}
                {year_filter}
            GROUP BY year
            ORDER BY year
        """).format(minimums=self._minimums_clause(ignore_minimums), year_filter=year_filter)
        return self.db.execute_query(query=query, filter_values=(years,) if years else None)

# ------------------------------------------------------------------------
# BACKFILL
# ------------------------------------------------------------------------

    def run(
        self,
        years: list[int],
        limit: Optional[int] = None,
        player_ids: list[str] = None,
        regular_season: bool = True,
        postseason: bool = True,
        force: bool = False,
        write_empty: bool = False,
        ignore_minimums: bool = False,
        dry_run: bool = False,
    ) -> GameLogBackfillResult:
        """Backfill rows for `years`.

        Args:
            years: Seasons to process. 2026+ are skipped (MLB API).
            limit: Max rows to process.
            player_ids: Restrict to these bref ids.
            regular_season / postseason: Which log keys to fill.
            force: Refetch even when the key already exists.
            write_empty: Store `[]` when a player with games has no regular season log rows. Off by default, since
                that is also what a blocked/changed page looks like and would mark the row done.
            ignore_minimums: Include players under 35 PA / 15 IP.
            dry_run: List what would be fetched without scraping or writing.
        """
        result = GameLogBackfillResult()
        years = [year for year in years if self._is_bref_year(year)]
        if not years:
            print("No BREF-sourced years to process (2026+ uses the MLB API).")
            return result

        rows = self._fetch_candidate_rows(years, player_ids, regular_season, postseason, force, ignore_minimums, limit)
        result.candidates = len(rows)
        print(f"{len(rows)} row(s) to backfill for {years}")
        if dry_run or not rows:
            return result

        consecutive_failures = 0
        for index, row in enumerate(rows, start=1):
            print(f"  {index}/{len(rows)}: {row['bref_id']} {row['year']} ({self._remaining_label(len(rows) - index, regular_season, postseason)})")
            try:
                update = self._scrape_row(row, regular_season, postseason, force, write_empty, result)
            except TimeoutError as error:
                print(f"    ✗ {error}")
                result.failed += 1
                result.failed_ids.append(row['id'])
                consecutive_failures += 1
                if consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    result.aborted_reason = f"{consecutive_failures} consecutive rate-limit/gateway failures. Rerun later; finished rows are saved."
                    break
                continue
            except Exception as error:
                print(f"    ✗ {type(error).__name__}: {error}")
                result.failed += 1
                result.failed_ids.append(row['id'])
                continue

            consecutive_failures = 0
            if update:
                self._write(row['id'], update)
                result.updated += 1
            else:
                result.no_logs += 1

        return result

    def _scrape_row(self, row: dict, regular_season: bool, postseason: bool, force: bool, write_empty: bool, result: GameLogBackfillResult) -> dict:
        """Fetch the missing log keys for one row. Returns the JSON to merge into `stats` (empty if nothing to write)."""
        player_type = row['effective_type']
        update: dict[str, list[dict]] = {}

        if regular_season and (force or not row['has_game_logs']):
            scraper = self._scraper(row)
            logs = self._with_backoff(lambda: scraper.game_log_list(type=player_type, years=[str(row['year'])], stats_period_type=StatsPeriodType.DATE_RANGE, reduce_size=True), result)
            if logs or write_empty or not (row['g'] or 0):
                update[StatsPeriodType.DATE_RANGE.stats_dict_key] = logs
            else:
                print("    ! no regular season log rows found, not writing (use --write_empty to store [])")

        # DON'T WRITE POSTSEASON IF THE REGULAR SEASON FETCH WAS SKIPPED AS SUSPECT
        regular_season_ok = not regular_season or StatsPeriodType.DATE_RANGE.stats_dict_key in update or row['has_game_logs'] and not force
        if postseason and (force or not row['has_postseason']) and regular_season_ok:
            update[StatsPeriodType.POSTSEASON.stats_dict_key] = self._postseason_logs(row, result)

        return update

    def _postseason_logs(self, row: dict, result: GameLogBackfillResult) -> list[dict]:
        cache_key = (row['bref_id'], row['effective_type'])
        if cache_key not in self._postseason_cache:
            scraper = self._scraper(row)
            self._postseason_cache[cache_key] = self._with_backoff(lambda: scraper.game_log_list(type=row['effective_type'], years=[str(row['year'])], stats_period_type=StatsPeriodType.POSTSEASON, reduce_size=True), result)
        return self._postseason_cache[cache_key]

    def _with_backoff(self, fetch, result: GameLogBackfillResult) -> list[dict]:
        """Run one BREF page fetch with a polite delay, retrying 429s after a long pause."""
        for attempt in range(self.MAX_RATE_LIMIT_RETRIES + 1):
            try:
                result.requests += 1
                logs = fetch()
                sleep(self.delay)
                return logs
            except TimeoutError as error:
                if attempt >= self.MAX_RATE_LIMIT_RETRIES or '429' not in str(error):
                    raise
                wait = self.RATE_LIMIT_BACKOFF_SECONDS * (attempt + 1)
                print(f"    rate limited, waiting {wait:.0f}s (retry {attempt + 1}/{self.MAX_RATE_LIMIT_RETRIES})")
                sleep(wait)

    @staticmethod
    def _scraper(row: dict) -> BaseballReferenceScraper:
        """A scraper used only for its game log page parser. Needs a bref id as the name so no search happens."""
        stats_period = StatsPeriod(type=StatsPeriodType.REGULAR_SEASON, year=str(row['year']))
        return BaseballReferenceScraper(stats_period=stats_period, name=row['bref_id'], year=str(row['year']), ignore_cache=True, ignore_archive=True)

# ------------------------------------------------------------------------
# DB
# ------------------------------------------------------------------------

    @staticmethod
    def _minimums_clause(ignore_minimums: bool) -> sql.SQL:
        return sql.SQL("") if ignore_minimums else sql.SQL("AND (pa >= 35 OR ip >= 15)")

    def _fetch_candidate_rows(self, years: list[int], player_ids: list[str], regular_season: bool, postseason: bool, force: bool, ignore_minimums: bool, limit: Optional[int]) -> list[dict]:
        missing_conditions = []
        if regular_season:
            missing_conditions.append("jsonb_typeof(stats->'game_logs') IS DISTINCT FROM 'array'")
        if postseason:
            missing_conditions.append("jsonb_typeof(stats->'postseason_game_logs') IS DISTINCT FROM 'array'")
        missing_clause = sql.SQL("") if force or not missing_conditions else sql.SQL("AND (" + " OR ".join(missing_conditions) + ")")

        values: list = [years]
        player_clause = sql.SQL("")
        if player_ids:
            player_clause = sql.SQL("AND bref_id = ANY(%s)")
            values.append(player_ids)
        limit_clause = sql.SQL("")
        if limit:
            limit_clause = sql.SQL("LIMIT %s")
            values.append(limit)

        query = sql.SQL("""
            SELECT id, year, bref_id, g,
                COALESCE(player_type_override, stats->>'type', player_type) AS effective_type,
                jsonb_typeof(stats->'game_logs') = 'array' AS has_game_logs,
                jsonb_typeof(stats->'postseason_game_logs') = 'array' AS has_postseason
            FROM player_season_stats
            WHERE year = ANY(%s)
                AND historical_date IS NULL
                AND stats ? 'bref_id'
                AND bref_id IS NOT NULL
                {minimums}
                {missing}
                {players}
            ORDER BY year DESC, war DESC NULLS LAST, id
            {limit}
        """).format(minimums=self._minimums_clause(ignore_minimums), missing=missing_clause, players=player_clause, limit=limit_clause)
        return self.db.execute_query(query=query, filter_values=tuple(values))

    def _write(self, row_id: str, update: dict) -> None:
        """Merge the new log keys into `stats` only."""
        with self.db.connection.cursor() as cursor:
            cursor.execute("UPDATE player_season_stats SET stats = stats || %s::jsonb WHERE id = %s", (json.dumps(update), row_id))
        self.db.connection.commit()

# ------------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------------

    @classmethod
    def _is_bref_year(cls, year: int) -> bool:
        if year >= cls.FIRST_MLB_API_YEAR:
            print(f"Skipping {year}: uses the MLB API, not Baseball Reference.")
            return False
        return True

    def _remaining_label(self, remaining_rows: int, regular_season: bool, postseason: bool) -> str:
        requests_per_row = int(regular_season) + int(postseason)
        minutes = round(remaining_rows * requests_per_row * (self.delay + 1.0) / 60.0, 1)
        return f"~{minutes} MINS LEFT" if minutes < 120 else f"~{round(minutes / 60.0, 1)} HOURS LEFT"
