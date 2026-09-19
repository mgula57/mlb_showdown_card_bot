"""Refresh league_averages_hitter.csv / league_averages_pitcher.csv, and MLB_SEASON_AVGS in
core/data/mlb_season_averages.py, from Baseball Reference.

Source tables:
    https://www.baseball-reference.com/leagues/majors/bat.shtml               -> table#teams_standard_batting_totals (season totals)
                                                                               -> table#teams_standard_batting        (per-game rates)
    https://www.baseball-reference.com/leagues/majors/pitch.shtml             -> table#teams_standard_pitching_totals (season totals)
                                                                               -> table#teams_standard_pitching        (per-game rates)
    https://www.baseball-reference.com/leagues/majors/{year}-ratio-pitching.shtml -> table#teams_ratio_pitching tfoot (league-wide GO/AO, IF/FB)

Usage:
    python update_league_averages.py [--year YEAR] [--type hitter|pitcher|both] [--skip-season-averages]
"""
import argparse
import csv
import os
import re
from datetime import date

import cloudscraper
from bs4 import BeautifulSoup

REAL_STATS_DIR = os.path.dirname(os.path.abspath(__file__))
SEASON_AVERAGES_PATH = os.path.normpath(os.path.join(REAL_STATS_DIR, '..', '..', 'data', 'mlb_season_averages.py'))

# CSV column name -> Baseball Reference `data-stat` key, in the exact order the CSVs use.
HITTER_COLUMNS = {
    'Year': 'year_ID', 'Tms': 'teams', '#Bat': 'batters_used', 'BatAge': 'age_bat',
    'R/G': 'runs_per_game', 'G': 'G', 'PA': 'PA', 'AB': 'AB', 'R': 'R', 'H': 'H',
    '1B': '1B', '2B': '2B', '3B': '3B', 'HR': 'HR', 'RBI': 'RBI', 'SB': 'SB', 'CS': 'CS',
    'BB': 'BB', 'SO': 'SO', 'BA': 'batting_avg', 'OBP': 'onbase_perc', 'SLG': 'slugging_perc',
    'OPS': 'onbase_plus_slugging', 'TB': 'TB', 'GDP': 'GIDP', 'HBP': 'HBP', 'SH': 'SH',
    'SF': 'SF', 'IBB': 'IBB', 'BIP': 'bip',
}
PITCHER_COLUMNS = {
    'Year': 'year_ID', 'Tms': 'teams', '#P': 'pitchers_used', 'PAge': 'age_pit',
    'R/G': 'runs_per_game', 'ERA': 'earned_run_avg', 'G': 'G', 'GF': 'GF', 'CG': 'CG',
    'SHO': 'SHO', 'tSho': 'SHO_team', 'SV': 'SV', 'IP': 'IP', 'H': 'H', 'R': 'R', 'ER': 'ER',
    'HR': 'HR', 'BB': 'BB', 'IBB': 'IBB', 'SO': 'SO', 'HBP': 'HBP', 'BK': 'BK', 'WP': 'WP',
    'BF': 'batters_faced', 'WHIP': 'whip', 'BAbip': 'batting_avg_bip', 'H9': 'hits_per_nine',
    'HR9': 'home_runs_per_nine', 'BB9': 'bases_on_balls_per_nine', 'SO9': 'strikeouts_per_nine',
    'E': 'E_def',
}
BREF_PAGES = {
    'hitter': ('https://www.baseball-reference.com/leagues/majors/bat.shtml', 'teams_standard_batting_totals', HITTER_COLUMNS),
    'pitcher': ('https://www.baseball-reference.com/leagues/majors/pitch.shtml', 'teams_standard_pitching_totals', PITCHER_COLUMNS),
}

# MLB_SEASON_AVGS holds PER-GAME rates (not season totals) for hitting and pitching combined into
# one dict per year, keyed the same as the CSVs above but sourced from BREF's *rate* tables
# (teams_standard_batting / teams_standard_pitching, not their _totals siblings).
SEASON_AVG_HITTER_COLUMNS = {
    '#Bat': 'batters_used', '1B': '1B', '2B': '2B', '3B': '3B', 'AB': 'AB', 'BA': 'batting_avg',
    'BB': 'BB', 'BIP': 'bip', 'BatAge': 'age_bat', 'CS': 'CS', 'G': 'G', 'GDP': 'GIDP', 'H': 'H',
    'HBP': 'HBP', 'HR': 'HR', 'IBB': 'IBB', 'OBP': 'onbase_perc', 'OPS': 'onbase_plus_slugging',
    'PA': 'PA', 'R': 'R', 'R/G': 'runs_per_game', 'RBI': 'RBI', 'SB': 'SB', 'SF': 'SF', 'SH': 'SH',
    'SLG': 'slugging_perc', 'SO': 'SO', 'TB': 'TB', 'Tms': 'teams',
}
SEASON_AVG_PITCHER_COLUMNS = {
    'ERA': 'earned_run_avg', 'SO9': 'strikeouts_per_nine', 'WHIP': 'whip',
}
SEASON_AVG_RATE_PAGES = {
    'hitter': ('https://www.baseball-reference.com/leagues/majors/bat.shtml', 'teams_standard_batting', SEASON_AVG_HITTER_COLUMNS),
    'pitcher': ('https://www.baseball-reference.com/leagues/majors/pitch.shtml', 'teams_standard_pitching', SEASON_AVG_PITCHER_COLUMNS),
}
# GO/AO and IF/FB aren't on the rate/totals pages above; BREF publishes the league-wide average
# for these in the `tfoot` summary row of the per-team ratio table, one page per year.
SEASON_AVG_RATIO_COLUMNS = {'GO/AO': 'go_ao_ratio', 'IF/FB': 'infield_fb_perc'}
SEASON_AVG_RATIO_URL = 'https://www.baseball-reference.com/leagues/majors/{year}-ratio-pitching.shtml'
SEASON_AVG_RATIO_TABLE_ID = 'teams_ratio_pitching'


class LeagueAveragesUpdater:
    """Scrapes Baseball Reference's year-by-year league totals tables and syncs them into real_stats/*.csv."""

    def __init__(self) -> None:
        self.scraper = cloudscraper.create_scraper()

    def update(self, player_type: str, year: int) -> None:
        url, table_id, columns = BREF_PAGES[player_type]
        row = self.__row_for_year(url=url, table_id=table_id, columns=columns, year=year)
        if row is None:
            print(f"WARNING: no {player_type} row found for {year} on {url}")
            return
        self.__upsert_row(player_type=player_type, row=row)
        print(f"Updated {player_type} league averages for {year}")

    def __row_for_year(self, url: str, table_id: str, columns: dict[str, str], year: int) -> dict[str, str] | None:
        # BREF's year-by-year tables are hidden inside HTML comments; strip them to expose the markup.
        html = self.scraper.get(url, timeout=(8, 22)).text.replace('<!--', '').replace('-->', '')
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table', attrs={'id': table_id})
        for tr in table.find('tbody').find_all('tr'):
            cells = {c.get('data-stat'): c.text.strip() for c in tr.find_all(['th', 'td'])}
            if cells.get('year_ID') == str(year):
                return {csv_col: cells.get(bref_key, '') for csv_col, bref_key in columns.items()}
        return None

    def __upsert_row(self, player_type: str, row: dict[str, str]) -> None:
        csv_path = os.path.join(REAL_STATS_DIR, f'league_averages_{player_type}.csv')
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)
            existing_rows = [r for r in reader if r]

        new_row = [row.get(col, '') for col in header]

        for i, existing_row in enumerate(existing_rows):
            if existing_row[0] == new_row[0]:
                existing_rows[i] = new_row
                break
        else:
            # Rows are sorted newest-year-first; insert just before the first older year.
            insert_at = next((i for i, r in enumerate(existing_rows) if int(r[0]) < int(new_row[0])), len(existing_rows))
            existing_rows.insert(insert_at, new_row)

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(existing_rows)

    def update_season_averages(self, year: int) -> None:
        row: dict[str, str] = {}
        for url, table_id, columns in SEASON_AVG_RATE_PAGES.values():
            page_row = self.__row_for_year(url=url, table_id=table_id, columns=columns, year=year)
            if page_row is None:
                print(f"WARNING: no season-average rate row found for {year} on {url}")
                return
            row.update(page_row)

        ratio_row = self.__ratio_averages_for_year(year=year)
        if ratio_row is None:
            print(f"WARNING: no GO/AO or IF/FB league average found for {year}")
        else:
            row.update(ratio_row)

        numeric_row: dict[str, float | None] = {
            key: (None if value in (None, '') else float(value)) for key, value in row.items()
        }
        self.__upsert_season_average(year=year, row=numeric_row)
        print(f"Updated MLB_SEASON_AVGS for {year}")

    def __ratio_averages_for_year(self, year: int) -> dict[str, str] | None:
        url = SEASON_AVG_RATIO_URL.format(year=year)
        html = self.scraper.get(url, timeout=(8, 22)).text.replace('<!--', '').replace('-->', '')
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table', attrs={'id': SEASON_AVG_RATIO_TABLE_ID})
        if table is None:
            return None
        tfoot = table.find('tfoot')
        if tfoot is None:
            return None
        cells = {c.get('data-stat'): c.text.strip() for c in tfoot.find_all(['th', 'td'])}
        row: dict[str, str] = {}
        for stat_key, bref_key in SEASON_AVG_RATIO_COLUMNS.items():
            raw = cells.get(bref_key, '')
            row[stat_key] = raw[:-1] if raw.endswith('%') else raw
        row['IF/FB'] = str(float(row['IF/FB']) / 100) if row.get('IF/FB') else ''
        return row

    def __upsert_season_average(self, year: int, row: dict[str, float | None]) -> None:
        with open(SEASON_AVERAGES_PATH, encoding='utf-8') as f:
            content = f.read()

        entry_pattern = re.compile(rf'^{year}: \{{.*?\}},\n', re.DOTALL | re.MULTILINE)
        existing_match = entry_pattern.search(content)

        entry_text = self.__format_season_average_entry(year=year, row=row)

        if existing_match:
            content = content[:existing_match.start()] + entry_text + content[existing_match.end():]
        else:
            # New years are always appended after the last (highest) existing year.
            last_entry = None
            for last_entry in re.finditer(r'^(?P<year>\d{4}): \{.*?\},\n', content, re.DOTALL | re.MULTILINE):
                pass
            if last_entry is None or int(last_entry.group('year')) >= year:
                raise ValueError(f"Cannot place a new MLB_SEASON_AVGS entry for {year}; expected it to be the newest year.")
            content = content[:last_entry.end()] + entry_text + content[last_entry.end():]

        with open(SEASON_AVERAGES_PATH, 'w', encoding='utf-8') as f:
            f.write(content)

    def __format_season_average_entry(self, year: int, row: dict[str, float | None]) -> str:
        sorted_items = sorted(row.items())
        lines = [f"'{key}': {value if value is None else repr(value)}" for key, value in sorted_items]
        body = ',\n        '.join(lines)
        return f"{year}: {{{body}}},\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Update MLB league average data from Baseball Reference")
    parser.add_argument('--year', type=int, default=date.today().year, help="Season year to fetch (default: current year)")
    parser.add_argument('--type', choices=['hitter', 'pitcher', 'both'], default='both')
    parser.add_argument('--skip-season-averages', action='store_true', help="Don't also update MLB_SEASON_AVGS in core/data/mlb_season_averages.py")
    args = parser.parse_args()

    player_types = ['hitter', 'pitcher'] if args.type == 'both' else [args.type]
    updater = LeagueAveragesUpdater()
    for player_type in player_types:
        updater.update(player_type=player_type, year=args.year)

    if not args.skip_season_averages:
        updater.update_season_averages(year=args.year)


if __name__ == '__main__':
    main()
