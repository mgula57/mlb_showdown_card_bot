# Database Tables

All table management lives in [`postgres_db.py`](postgres_db.py).

---

## Public Schema

### `player_season_stats`

The central stats archive. One row per player-season (keyed by a composite string ID like `2023-troutmi01` or `2023-troutmi01-(sea)`). Card generation reads from here instead of re-scraping Baseball Reference for historical seasons.

| Column | Type | Notes |
|--------|------|-------|
| `id` | varchar(100) PK | `{year}-{bref_id}[-{team_override}][-{type_override}][-{historical_date}]` |
| `year` | int | Season year |
| `bref_id` | varchar(10) | Baseball Reference player ID |
| `mlb_id` | int | MLB Stats API player ID |
| `historical_date` | text | For snapshot/historical cards |
| `name` | varchar(48) | Player name |
| `player_type` | varchar(10) | `HITTER` or `PITCHER` |
| `player_type_override` | varchar(10) | e.g. `(hitter)` or `(pitcher)` for two-way players |
| `is_two_way` | boolean | True for two-way players like Ohtani |
| `primary_positions` | text[] | Primary position(s) |
| `secondary_positions` | text[] | Secondary position(s) |
| `g` / `gs` | int | Games played / Games started |
| `pa` | int | Plate appearances (hitters) |
| `ip` | float | Innings pitched (pitchers) |
| `lg_id` | varchar(10) | League ID (e.g. `AL`, `NL`, `NNL`) |
| `team_id` | varchar(10) | Primary team abbreviation |
| `team_id_list` | text[] | All teams if multi-team season |
| `team_games_played_dict` | jsonb | Games played per team |
| `team_override` | varchar(8) | User-specified team filter |
| `stats` | jsonb | Full raw stats dict from scraper |
| `war` | double precision | WAR (top-level, for quick queries) |
| `stats_modified_date` | timestamp | When `stats` was last updated |
| `created_date` / `modified_date` | timestamp | Row audit timestamps |

#### `card_bot`

Denormalized explore table that powers the Explore page. Rebuilt incrementally by `build_card_bot_view()` — it joins `player_season_stats` with `internal.dim_card` plus team/image dimensions. Supports the full filter/sort/paginate API in `fetch_card_list()`.

Primary key: `(id, showdown_set, showdown_bot_version)`

Key column groups:

| Group | Columns |
|-------|---------|
| Identifiers | `id`, `year`, `bref_id`, `mlb_id`, `name` |
| Player info | `player_type`, `player_type_override`, `is_two_way` |
| Positions | `primary_positions`, `secondary_positions`, `positions_list`, `positions_and_defense`, `positions_and_defense_string` |
| Game counts | `g`, `gs`, `pa`, `real_ip` |
| League/team | `lg_id`, `team_id`, `team_id_list`, `organization`, `league`, `team`, `color_primary`, `color_secondary` |
| Card attributes | `showdown_set`, `showdown_bot_version`, `expansion`, `edition`, `set_number`, `points`, `points_estimated` |
| Chart | `command`, `outs`, `is_pitcher`, `is_chart_outlier`, `chart_ranges`, `chart_values` |
| Speed/IP | `speed`, `speed_letter`, `speed_full`, `speed_or_ip`, `ip` |
| Real stats | `real_bwar`, `real_earned_run_avg`, `real_onbase_plus_slugging`, `real_hr`, `real_sb`, etc. |
| Awards/flags | `awards_list`, `icons_list`, `is_hof`, `is_small_sample_size`, `is_errata` |
| Images | `image_match_type`, `image_ids` |
| Timestamps | `stats_modified_date`, `card_modified_date`, `updated_at` |

#### `card_wotc`

Wizards of the Coast (official) card data. Loaded via `upload_wotc_card_data()`. Similar shape to `card_bot` but stores the full `ShowdownPlayerCard` object as `card_data` jsonb alongside flattened columns. Cleared and reloaded on each upload.

#### `card_wbc`

World Baseball Classic card data. Same structure as `card_bot` with WBC-specific columns (`wbc_season`, `wbc_team`, `wbc_team_id`).

#### `player_search` (materialized view)

Lightweight player search index built from `player_season_stats`. Used in the custom card builder's player search. Unique index on `(bref_id, year, player_type_override)`.

| Column | Notes |
|--------|-------|
| `name` | Lowercased, unaccented, periods removed |
| `year` | Season year |
| `bref_id` | Baseball Reference ID |
| `team` | Team abbreviation |
| `player_type_override` | Two-way override if applicable |
| `is_hof` | Hall of Fame flag |
| `award_summary` | Raw award string (e.g. `AS,MVP-1`) |
| `bwar` | Career bWAR as float |

#### `team_search` (materialized view)

Team hierarchy used for the Explore page team filter. Built from `card_bot`. Returns one row per `(organization, league, team)` with `min_year`, `max_year`, and card count.

---

## `internal` Schema

#### `internal.dim_card`

Normalized card data store. One row per `(player_id, showdown_set, version)`. `player_id` is `{year}-{bref_id_or_mlb_id}[-{type_override}]`. The `card_data` jsonb column holds the full serialized `ShowdownPlayerCard`.

| Column | Notes |
|--------|-------|
| `id` | `{player_id}-{showdown_set}` |
| `player_id` | `{year}-{bref_id}` or `{year}-{mlb_id}` |
| `showdown_set` | e.g. `2000`, `CLASSIC` |
| `version` | Bot version string |
| `card_data` | Full `ShowdownPlayerCard` as jsonb |
| `created_date` / `modified_date` | Audit timestamps |

#### `internal.dim_player_id_map`

Lookup table mapping Baseball Reference IDs to MLB Stats API IDs and Fangraphs IDs. Loaded via `update_player_id_table()` (rip-and-replace). Used to resolve `mlb_id` → `bref_id` when fetching cards for a live roster.

| Column | Notes |
|--------|-------|
| `bref_id` PK | Baseball Reference ID |
| `mlb_id` | MLB Stats API ID (unique index) |
| `fangraphs_id` | Fangraphs ID |
| `name_first` / `name_last` | Player name |
| `mlb_first_year` / `mlb_last_year` | Career span |

#### `internal.dim_team_years` (materialized view)

Distinct `(organization, league, team, year)` combinations derived from `player_season_stats`. Powers the league/team hierarchy filter on the Explore page. Unique index on `(team, year)`.

#### `internal.dim_auto_image`

Index of auto-generated player card images sourced from Google Drive. Loaded via `build_auto_image_table()`. Each row represents one player-year-team combination with Google Drive file IDs for the `BG` (background) and `CUT` (cutout) variants.

| Column | Notes |
|--------|-------|
| `year` | Season year as string |
| `player_id` | bref_id or mlb_id |
| `player_name` | Display name |
| `team_id` | Team abbreviation |
| `player_type_override` | `(hitter)` / `(pitcher)` if applicable |
| `is_postseason` | Postseason image flag |
| `is_wbc` | WBC image flag |
| `image_ids` | jsonb `{"BG": "<gdrive_id>", "CUT": "<gdrive_id>"}` |
| `image_modified_date` | Last modified date from Google Drive |

#### `internal.user_settings`

Per-user preferences. One row per Supabase user UUID.

| Column | Notes |
|--------|-------|
| `user_id` PK | Supabase auth UUID |
| `theme` | `light`, `dark`, or `system` |
| `showdown_set` | Default set for the card builder |
| `custom_card_form_settings` | jsonb of saved form defaults |
| `starred_teams` | jsonb array of starred team IDs |
| `avatar_url` | Profile image URL |

#### `internal.log_custom_card_bot`

Audit log of every card generation request submitted through the web UI. One row per submission, including both successful cards and errors. Powers the user gallery.

Key columns: `name`, `year`, `set`, `bref_id`, `team`, `edition`, `expansion`, `era`, `data_source`, `image_source`, `card_load_time`, `scraper_load_time`, `error`, `error_for_user`, `user_inputs` (jsonb of raw form values), `card_result` (jsonb snapshot of the generated card), `storage_path`, `thumbnail_storage_path`, `user_id`, `is_hidden`.

#### `internal.log_player_search`

Audit log of player search queries from the Explore page.

| Column | Notes |
|--------|-------|
| `filters` | jsonb of search filters applied |
| `result_count` | Number of results returned |
| `error` | Error message if the query failed |

#### `internal.log_card_image_generation`

Audit log of card image render events (e.g. re-rendering a stored card).

| Column | Notes |
|--------|-------|
| `card_id` | ID of the card rendered |
| `error` | Error if render failed |

#### `internal.log_card_id_lookup`

Audit log of card ID resolution requests (e.g. fetching a card by ID from an external source).

| Column | Notes |
|--------|-------|
| `card_id` | Card ID looked up |
| `source` | Caller identifier |
| `error` | Error if lookup failed |

---

## Data Flow Summary

```
Baseball Reference / MLB Stats API
        ↓
  player_season_stats          ← stats archive
        ↓
  internal.dim_card            ← generated card data
        ↓
  card_bot                     ← denormalized explore table
        ↓
  player_search / team_search  ← lightweight search views
```
