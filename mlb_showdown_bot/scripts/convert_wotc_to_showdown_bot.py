import argparse
import pandas as pd
import sys
import json
from math import isnan
from pprint import pprint
import os
from pathlib import Path

sys.path.append('..')
from wotc_player_cards import WotcPlayerCardSet, Set

parser = argparse.ArgumentParser(description="Convert Original WOTC MLB Showdown Card Data to Showdown Bot Cards.")
parser.add_argument('-s','--sets', type=str, help='Sets as comma delimited list. Example: -s "2000,2001,2002"', default='2000,2001,2002,2003,2004,2005')
args = parser.parse_args()

wotc_set = WotcPlayerCardSet(sets=[Set(s) for s in args.sets.split(',')])
wotc_set.export_to_local_file()