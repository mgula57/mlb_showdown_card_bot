# *********************************************************
# GRAB LIST OF NICKNAMES FROM BREF AND STORE IN A CSV FILE
# *********************************************************

import argparse
import os
import cloudscraper
from bs4 import BeautifulSoup
from pprint import pprint
import pandas as pd
from pathlib import Path
import unidecode


parser = argparse.ArgumentParser(description="Grab list of nicknames from bref and store in a csv file.")
args = parser.parse_args()

def fetch_data(url:str) -> BeautifulSoup:

    scraper = cloudscraper.create_scraper()
    html = scraper.get(url)
    html = html.text.replace("<!--","")
    soup = BeautifulSoup(html, "lxml")

    return soup

def extract_player_nicknames(soup: BeautifulSoup) -> list[dict]:

    # PARSE SOUP OBJECT
    nicknames_div = soup.find('div', attrs={'id': 'content', 'role': 'main'})
    players_div = nicknames_div.find('div', attrs={'id': 'div_players'})
    players_list = players_div.find_all('p')

    # PARSE PLAYER DATA
    final_data = []
    for player_soup_row in players_list:
        player_data = {}
        
        # EXTRACT BREF ID AND NAME
        href_soup = player_soup_row.find('a')
        if href_soup:
            player_data['name'] = unidecode.unidecode(href_soup.get_text())
            href_text = href_soup['href']
            if href_text:
                player_data['bref_id'] = href_text.split('/')[-1].split('.shtml')[0]
        
        # EXTRACT NICKNAMES
        nicknames_raw = unidecode.unidecode(player_soup_row.get_text()) # EX: "Henry Aaron - Hammer,Hammerin' Hank,Bad Henry"
        nicknames_isolated: str = nicknames_raw.split(' - ', 1)[1] # EX: "Hammer,Hammerin' Hank,Bad Henry"
        nicknames_list = [nn.strip() for nn in nicknames_isolated.split(',')]
        player_data['nicknames'] = nicknames_list

        if len(player_data['bref_id']) == 0:
            print(player_soup_row)
        final_data.append(player_data)
    
    return final_data

def export_as_csv(data:dict) -> None:
    df = pd.DataFrame.from_records(data,index=None)
    
    nickname_columns = ['nickname1', 'nickname2', 'nickname3', 'nickname4', 'nickname5', 'nickname6',]
    df[nickname_columns] = pd.DataFrame(df.nicknames.tolist(), index= None)

    parent_path = Path(os.path.dirname(__file__)).parent
    export_path = os.path.join(parent_path, 'mlb_showdown_bot', 'nicknames.csv')
    
    df.to_csv(export_path, index=False)

# GET WEBSITE DATA
url = 'https://www.baseball-reference.com/friv/baseball-player-nicknames.shtml'
soup = fetch_data(url)
nickname_data = extract_player_nicknames(soup)
export_as_csv(nickname_data)
    