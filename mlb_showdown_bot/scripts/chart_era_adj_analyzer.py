import os, sys
from pathlib import Path
from prettytable import PrettyTable
sys.path.append(os.path.join(Path(os.path.join(os.path.dirname(__file__))).parent))
from showdown_player_card import Era, Chart, PlayerType, Set

import argparse
parser = argparse.ArgumentParser(description="Analyze weights for era adjustments")
parser.add_argument('-s','--set', type=str, help='Sets to test (ex: 2000, 2001, 2005)', default='2005')
parser.add_argument('-t','--types', type=str, help='Types to test (PITCHER, HITTER))', default='PITCHER,HITTER')
args = parser.parse_args()

def extract_values_from_chart(chart:Chart, attributes:list[str]) -> list[str]:
    row: list[str] = []
    for column in attributes:
        if column in non_value_columns:
            row.append(str(round(getattr(chart, column.lower()), 2)))
        else:
            row.append(str(round(chart.values[column], 3)))

    # CREATE TOTAL VALUE
    row.append(str(round(sum([c for c in chart.values.values()]))))

    return row

types = [PlayerType(t.title()) for t in args.types.split(',')]
set = Set(args.set)
non_value_columns = ['OBP_ADJUSTMENT_FACTOR', 'COMMAND', 'OUTS',]
for type in types:

    
    wotc_baseline_chart = set.wotc_baseline_chart(type)
    chart_columns = non_value_columns + [c.value for c in wotc_baseline_chart.values.keys()]

    # DEFINE ATTRIBUTES FOR TYPE
    chart_tbl = PrettyTable(field_names=['SET', 'TYPE', 'ERA'] + chart_columns + ['TOTAL'])

    for era in Era:
        era_chart = wotc_baseline_chart.model_copy()
        era_chart.era = era.value
        era_chart.adjust_for_era(era = era, year_list=era.year_range)
        table_row = [set.value, type.value, era.value.replace("ERA", "")] + extract_values_from_chart(era_chart, chart_columns)
        chart_tbl.add_row(table_row)

    chart_tbl.add_row([set.value, type.value, 'WOTC'] + extract_values_from_chart(wotc_baseline_chart, chart_columns))

    print(chart_tbl)