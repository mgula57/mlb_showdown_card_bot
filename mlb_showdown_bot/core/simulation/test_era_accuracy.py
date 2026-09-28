import argparse

from dotenv import load_dotenv
from prettytable import PrettyTable

from mlb_showdown_bot.core.card.sets import Era
from mlb_showdown_bot.core.simulation.models import SeasonSimulationConfig
from mlb_showdown_bot.core.simulation.season import Season
from mlb_showdown_bot.core.simulation.stats import StatCategory
from mlb_showdown_bot.core.shared.player_position import PlayerType

load_dotenv()

# PARSE ARGS FROM COMMAND LINE
parser = argparse.ArgumentParser(description="Compare sim league averages vs real MLB results across an era")
parser.add_argument('-e','--era', help='Era to test for', required=True)
parser.add_argument('-s', '--set', help='The showdown set to use.', default='2000', required=True)
parser.add_argument('-sd', '--seed', help='Random seed', type=int, default=None)
args = parser.parse_args()

CATEGORIES = [
    StatCategory.PA, StatCategory.BA, StatCategory.OBP, StatCategory.SLG, StatCategory.OPS,
    StatCategory.BB, StatCategory.HITS, StatCategory.DOUBLES, StatCategory.TRIPLES,
    StatCategory.HOMERUNS, StatCategory.SO,
]

tbl = PrettyTable(field_names=['SEASON'] + [category.abbreviation for category in CATEGORIES])

era = Era(args.era)
for year in era.year_range:
    print(year)
    config = SeasonSimulationConfig(year=year, set=args.set, simulate_postseason=False, seed=args.seed)
    result = Season(config=config).simulate()

    sim_stats = result.league_totals[PlayerType.HITTER.value]
    real_stats = result.real_league_averages.get(PlayerType.HITTER.value)
    tbl.add_row([f"{year}-SIM"] + [sim_stats.stat(category, combine_1b_and_1b_plus=True) for category in CATEGORIES])
    if real_stats:
        tbl.add_row([f"{year}-REAL"] + [real_stats.stat(category, combine_1b_and_1b_plus=True) for category in CATEGORIES], divider=True)

print(tbl)
