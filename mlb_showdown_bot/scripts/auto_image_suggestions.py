import argparse
import os
import cloudscraper
from bs4 import BeautifulSoup
from pprint import pprint

parser = argparse.ArgumentParser(description="Search baseball reference for best auto images to add.")
parser.add_argument('-hof','--hof', action='store_true', help='Only Hall of Fame Players', required=False)
parser.add_argument('-p', '--page', help='BRef Page to use. Either season or career.', required=False, type=str, default='career')
args = parser.parse_args()

def fetch_table_data(url:str, table_id:str, bref_id_field_substring:str=None, use_header_for_col_names:bool=False) -> list[dict]:
    
    scraper = cloudscraper.create_scraper()
    html = scraper.get(url)
    html = html.text.replace("<!--","")
    soup = BeautifulSoup(html, "lxml")

    # TABLE
    soup_hof_table = soup.find('table', attrs={"id": table_id})

    # ROWS
    rows = soup_hof_table.find_all('tr')

    all_data = []
    header_columns = []
    for row in rows:
        data = {}
        if bref_id_field_substring:
            href_objects = row.find_all('a')
            for href_object in href_objects:
                href = href_object['href']
                if bref_id_field_substring in href:
                    data['bref_id'] = href.split('/')[-1].split('.shtml')[0]

        if use_header_for_col_names:
            headers = row.find_all('th')
            for col in headers:
                header_columns.append(col.get_text())

        columns = row.find_all('td')
        if use_header_for_col_names:
            for index, column in enumerate(columns):
                column_name = header_columns[index]
                data[column_name] = column.get_text().replace(u'\xa0', u' ')
        else:
            for column in columns:
                column_name = column['data-stat']
                data[column_name] = column.get_text().replace(u'\xa0', u' ')
        
        all_data.append(data)

    return all_data

def fetch_war(page:str) -> list[dict]:
    return fetch_table_data(url=f'https://www.baseball-reference.com/leaders/WAR_{page}.shtml', table_id=f"leader_standard_WAR", bref_id_field_substring='players/', use_header_for_col_names=True)

def fetch_hof_list() -> list[dict]:

    hof_data = fetch_table_data(url='https://www.baseball-reference.com/awards/hof.shtml', table_id='hof', bref_id_field_substring='players')
    
    all_hof_data = [p for p in hof_data if p.get('category_hof','') == 'Player']

    return all_hof_data

def fetch_image_file_list() -> list[str]:
    file_names = []
    for _, _, files in os.walk('/Users/matthewgula/My Drive/MLB Showdown Assets/MLB Showdown Player Images/Universal'):
        for name in files:
            file_names.append(name)
    return file_names

def bref_ids_with_image() -> list[str]:
    return list(set([img.split('(')[1].split(')')[0] for img in fetch_image_file_list() if '(' in img]))

all_hofs = fetch_hof_list()
bref_ids_w_image = bref_ids_with_image()
hof_bref_ids = [hof['bref_id'] for hof in all_hofs]
hof_no_img = [hof for hof in sorted(all_hofs, key=lambda p: p['votes_pct']) if hof['bref_id'] not in bref_ids_w_image]

war_dicts = fetch_war(page=args.page)
sort_column = 'Wins Above Replacement'
war_dicts_sorted = sorted(war_dicts, key=lambda d: float(d.get(sort_column, 0)), reverse=True)

for player_dict in war_dicts_sorted:
    try:
        bref_id = player_dict.get('bref_id', 'abc')
        if bref_id not in bref_ids_w_image and (bref_id in hof_bref_ids if args.hof else True):
            print(player_dict['Player (yrs, age)'], player_dict[sort_column])

    except:
        continue
