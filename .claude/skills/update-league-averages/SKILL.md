---
name: update-league-averages
description: Refresh league_averages_hitter.csv, league_averages_pitcher.csv, MLB_SEASON_AVGS (core/data/mlb_season_averages.py), and FIP_CONSTANT (core/card/utils/showdown_constants.py) with the latest MLB season stats scraped from Baseball Reference. Use when asked to update, refresh, or sync league averages or the FIP constant, or to pull the latest year of league stats into the sim's real-stats or era-adjustment reference data.
---

# Update League Averages

Four places hold year-by-year MLB league reference data, all fed by the same Baseball Reference
pages but different tables on them:

- `mlb_showdown_bot/core/simulation/real_stats/league_averages_hitter.csv` and
  `league_averages_pitcher.csv` — season **totals**, read by `load_real_league_avgs()` in
  `mlb_showdown_bot/core/simulation/stats.py` to benchmark simulation accuracy against real life.
- `mlb_showdown_bot/core/data/mlb_season_averages.py` (`MLB_SEASON_AVGS`) — per-game **rates**,
  hitting and pitching combined into one dict per year, read by `chart.py`'s era-adjustment logic
  to scale card charts to the offensive/pitching environment of a given year.
- `mlb_showdown_bot/core/card/utils/showdown_constants.py` (`FIP_CONSTANT`) — the per-year FIP
  constant, read by `showdown_player_card.py` when it computes a pitcher's FIP.

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
- `FIP_CONSTANT` is computed from the same `teams_standard_pitching_totals` row as the pitcher
  CSV, using FanGraphs' formula: `lgERA - (13*HR + 3*(BB+HBP) - 2*SO) / IP`. The values originally
  came from the `cFIP` column of FanGraphs' Guts! page (https://www.fangraphs.com/guts.aspx?type=cn),
  but that page is Cloudflare-blocked for scripts. The derived value matches FanGraphs exactly for
  most historical years and is within about 0.005 for modern years, which doesn't change a FIP rounded to 2 decimals.

## How to update

Run the bundled script from the repo root:

```bash
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py
```

This updates all four for the current year: upserting the row in each CSV (replacing it
in place if the year already exists — useful for refreshing an in-progress season — or inserting
it if new), and doing the same for the `MLB_SEASON_AVGS` entry (new years are appended after the
current last/highest year; it doesn't support back-filling arbitrary past years). The
`FIP_CONSTANT` entry is upserted the same way: replaced in place (dropping any trailing comment
like `# TEMPORARY VALUE`) or inserted newest-first.

Options:

```bash
# Specific year
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --year 2025

# Only one player type's CSV (still also updates MLB_SEASON_AVGS, since that needs both)
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --type hitter

# Skip MLB_SEASON_AVGS, only touch the CSVs
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --skip-season-averages

# Skip FIP_CONSTANT
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --skip-fip-constant
```

## Notes

- Uses `cloudscraper` (not plain `requests`) because Baseball Reference blocks generic HTTP
  clients — same pattern used elsewhere in this repo's scrapers
  (`core/archive/player_stats_archive.py`, `core/card/stats/baseball_ref_scraper.py`).
- Baseball Reference's tables are wrapped in HTML comments; the script strips `<!--`/`-->`
  before parsing, matching the existing scraper convention. Each page is fetched once per run and
  reused across tables.
- After running, diff the changed files (`git diff`) to sanity-check the new/updated rows before
  committing.
