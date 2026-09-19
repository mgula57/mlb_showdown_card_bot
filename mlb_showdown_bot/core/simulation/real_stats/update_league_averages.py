"""Refresh league_averages_hitter.csv / league_averages_pitcher.csv from Baseball Reference.

Source tables:
    https://www.baseball-reference.com/leagues/majors/bat.shtml   -> table#teams_standard_batting_totals
    https://www.baseball-reference.com/leagues/majors/pitch.shtml -> table#teams_standard_pitching_totals

Usage:
    python update_league_averages.py [--year YEAR] [--type hitter|pitcher|both]
"""
import argparse
import csv
import os
from datetime import date

import cloudscraper
from bs4 import BeautifulSoup

REAL_STATS_DIR = os.path.dirname(os.path.abspath(__file__))

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Update MLB league average CSVs from Baseball Reference")
    parser.add_argument('--year', type=int, default=date.today().year, help="Season year to fetch (default: current year)")
    parser.add_argument('--type', choices=['hitter', 'pitcher', 'both'], default='both')
    args = parser.parse_args()

    player_types = ['hitter', 'pitcher'] if args.type == 'both' else [args.type]
    updater = LeagueAveragesUpdater()
    for player_type in player_types:
        updater.update(player_type=player_type, year=args.year)


if __name__ == '__main__':
    main()
