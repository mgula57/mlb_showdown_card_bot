---
name: update-league-averages
description: Refresh league_averages_hitter.csv, league_averages_pitcher.csv, and MLB_SEASON_AVGS (core/data/mlb_season_averages.py) with the latest MLB season stats scraped from Baseball Reference. Use when asked to update, refresh, or sync league averages, or to pull the latest year of league stats into the sim's real-stats or era-adjustment reference data.
---

# Update League Averages

Three files hold year-by-year MLB league reference data, all fed by the same Baseball Reference
pages but different tables on them:

- `mlb_showdown_bot/core/simulation/real_stats/league_averages_hitter.csv` and
  `league_averages_pitcher.csv` — season **totals**, read by `load_real_league_avgs()` in
  `mlb_showdown_bot/core/simulation/stats.py` to benchmark simulation accuracy against real life.
- `mlb_showdown_bot/core/data/mlb_season_averages.py` (`MLB_SEASON_AVGS`) — per-game **rates**,
  hitting and pitching combined into one dict per year, read by `chart.py`'s era-adjustment logic
  to scale card charts to the offensive/pitching environment of a given year.

Source tables:

- Hitters: https://www.baseball-reference.com/leagues/majors/bat.shtml
  - `teams_standard_batting_totals` → the two CSVs' season totals
  - `teams_standard_batting` → `MLB_SEASON_AVGS`'s per-game rates
- Pitchers: https://www.baseball-reference.com/leagues/majors/pitch.shtml
  - `teams_standard_pitching_totals` → the pitcher CSV's season totals
  - `teams_standard_pitching` → `MLB_SEASON_AVGS`'s ERA/WHIP/SO9
- `MLB_SEASON_AVGS`'s `GO/AO` and `IF/FB` come from a separate, year-specific page:
  https://www.baseball-reference.com/leagues/majors/{year}-ratio-pitching.shtml
  → table `teams_ratio_pitching`'s `tfoot` row (the league-wide average across all teams;
  `go_ao_ratio` and `infield_fb_perc`, the latter a percentage converted to a decimal).

## How to update

Run the bundled script from the repo root:

```bash
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py
```

This updates all three files for the current year: upserting the row in each CSV (replacing it
in place if the year already exists — useful for refreshing an in-progress season — or inserting
it if new), and doing the same for the `MLB_SEASON_AVGS` entry (new years are appended after the
current last/highest year; it doesn't support back-filling arbitrary past years).

Options:

```bash
# Specific year
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --year 2025

# Only one player type's CSV (still also updates MLB_SEASON_AVGS, since that needs both)
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --type hitter

# Skip MLB_SEASON_AVGS, only touch the CSVs
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --skip-season-averages
```

## Notes

- Uses `cloudscraper` (not plain `requests`) because Baseball Reference blocks generic HTTP
  clients — same pattern used elsewhere in this repo's scrapers
  (`core/archive/player_stats_archive.py`, `core/card/stats/baseball_ref_scraper.py`).
- Baseball Reference's tables are wrapped in HTML comments; the script strips `<!--`/`-->`
  before parsing, matching the existing scraper convention.
- After running, diff the changed files (`git diff`) to sanity-check the new/updated rows before
  committing.
