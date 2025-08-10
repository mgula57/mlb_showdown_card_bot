import requests
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
from pprint import pprint
import os

parser = argparse.ArgumentParser(description="Search baseball reference for best auto images to add.")
parser.add_argument('-t','--player_type', help='Player Type (Batting, Pitching)', type=str, required=False, default=None)
parser.add_argument('-yt', '--year_threshold', help='Optional year threshold. Only includes images that are <= the threshold.', required=False, type=int, default=None)
args = parser.parse_args()

def _try_convert_to_float(value: str) -> float | str:
    try:
        return float(value)
    except ValueError:
        return value

def fetch_image_file_list() -> list[str]:
    """Fetch the list of image files from the specified directory."""

    print("Fetching image file list...")
    file_names = []
    path = os.environ.get('AUTO_IMAGE_PATH', None)
    if not path:
        return []
    
    for _, _, files in os.walk(path):
        for name in files:
            file_names.append(name)

    print("Loaded", len(file_names), "image files from", path)
    return file_names

def load_html_file(path: str) -> BeautifulSoup:
    """Load an HTML file into BeautifulSoup."""
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    return BeautifulSoup(html, "html.parser")

def fetch_bref_player_stats(player_type: str) -> list:
    """
    Fetch player stats from Baseball Reference for a given player type.
    Caches results for type + day. Will use the local file if it exists and is not older than 1 day.

    Args:
        player_type (str): Type of player ('Batting' or 'Pitching').

    Returns:
        list: List of player stats dictionaries.
    """
    current_year = datetime.now().year
    current_date = datetime.now().strftime("%Y-%m-%d")
    output_path = f"cache/bref_{player_type.lower()}_stats_{current_date}.html"

    # Check if cached file exists and is not older than 1 day
    try:
        soup = load_html_file(output_path)
        print(f"Loaded cached data for {player_type} players from {output_path}")
    except FileNotFoundError:
        # If file doesn't exist, fetch from Baseball Reference
        print(f"Fetching data for {player_type} players from Baseball Reference...")
        
        
        url = f"https://www.baseball-reference.com/leagues/MLB/{current_year}-standard-{player_type.lower()}.shtml"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching data from {url}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")

        # Save the fetched data to cache
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(str(response.text))

    # Example: get first 5 player rows (adjust selectors)
    rows = soup.find("table", id=f"players_standard_{player_type.lower()}")
    if not rows:
        print(f"No players_standard_{player_type.lower()} table found.")
        return []
    rows = rows.find("tbody").find_all("tr")
    if not rows:
        print(f"No tbody rows found for {player_type} players.")
        return []
    
    # GET IMAGE NAMES
    image_list = fetch_image_file_list()
    
    data = []
    for r in rows:
        player_data: dict[str, any] = {}
        player_id: str = None
        cols = r.find_all("td")
        for col in cols:
            stat = col.get('data-stat', 'n/a')
            value = col.text.strip()
            player_data[stat] = _try_convert_to_float(value)
            if stat == 'name_display':
                # EXTRACT BREF ID
                a = col.find('a')
                if a:
                    player_id = a['href'].split('/')[-1].replace('.shtml', '')
                    player_data['bref_id'] = player_id

        # CHECK IF PLAYER IS IN IMAGE LIST
        team_id = player_data.get('team_name_abbr', None)
        if len(player_id or 'n/a') > 0 and team_id:
            images = [
                image for image in image_list 
                if player_id in image 
                    and (abs(int(image.split('-')[1]) - current_year) <= 1 if args.year_threshold is not None else True)
                ]    
            if len(images) > 0:
                continue  # Skip if player has an image
        else:
            continue

        data.append(player_data)
        

    # SORT BY BWAR DESC THAT DONT HAVE AN IMAGE
    war_stat = f'{player_type[:1].lower()}_war'
    data.sort(key=lambda x: 0 if len(str(x.get(war_stat, ''))) == 0 else x.get(war_stat, 0), reverse=True)

    for d in data[:10]:
        print(f"{d.get('name_display', 'Unknown')} | Team: {d.get('team_name_abbr', 'n/a')} | bWAR: {d.get(war_stat, 'n/a')}")
    return data

fetch_bref_player_stats(args.player_type)