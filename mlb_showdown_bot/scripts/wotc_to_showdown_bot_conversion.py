import argparse
import sys, os
from pathlib import Path
sys.path.append(os.path.join(Path(os.path.join(os.path.dirname(__file__))).parent))
from mlb_showdown_bot.core.wotc.wotc_player_cards import WotcPlayerCardSet, Set

parser = argparse.ArgumentParser(description="Convert Original WOTC MLB Showdown Card Data to Showdown Bot Cards.")
parser.add_argument('-s','--sets', type=str, help='Sets as comma delimited list. Example: -s "2000,2001,2002"', default='2000,2001,2002,2003,2004,2005')
args = parser.parse_args()

wotc_set = WotcPlayerCardSet(sets=[Set(s) for s in args.sets.split(',')])
wotc_set.export_to_local_file()