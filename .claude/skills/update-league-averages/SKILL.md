---
name: update-league-averages
description: Refresh league_averages_hitter.csv and league_averages_pitcher.csv in mlb_showdown_bot/core/simulation/real_stats/ with the latest MLB season totals scraped from Baseball Reference. Use when asked to update, refresh, or sync league averages, or to pull the latest year of league stats into the sim's real-stats reference data.
---

# Update League Averages

`league_averages_hitter.csv` and `league_averages_pitcher.csv` in
`mlb_showdown_bot/core/simulation/real_stats/` are year-by-year MLB league totals, read by
`load_real_league_avgs()` in `mlb_showdown_bot/core/simulation/stats.py` to benchmark simulation
accuracy against real life.

They are sourced from Baseball Reference's year-by-year league totals tables:

- Hitters: https://www.baseball-reference.com/leagues/majors/bat.shtml → table `teams_standard_batting_totals`
- Pitchers: https://www.baseball-reference.com/leagues/majors/pitch.shtml → table `teams_standard_pitching_totals`

(Not the sibling `teams_standard_batting` / `teams_standard_pitching` tables on those pages —
those are per-game rate tables, not season totals.)

## How to update

Run the bundled script from the repo root:

```bash
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py
```

This fetches the current year for both hitters and pitchers and upserts that row in each CSV
(replacing the row in place if the year already exists — useful for refreshing an in-progress
season's totals — or inserting it in descending-year order if it's new).

Options:

```bash
# Specific year
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --year 2025

# Only one player type
python mlb_showdown_bot/core/simulation/real_stats/update_league_averages.py --type hitter
```

## Notes

- Uses `cloudscraper` (not plain `requests`) because Baseball Reference blocks generic HTTP
  clients — same pattern used elsewhere in this repo's scrapers
  (`core/archive/player_stats_archive.py`, `core/card/stats/baseball_ref_scraper.py`).
- Baseball Reference's tables are wrapped in HTML comments; the script strips `<!--`/`-->`
  before parsing, matching the existing scraper convention.
- After running, diff the CSVs (`git diff`) to sanity-check the new/updated row before committing.
