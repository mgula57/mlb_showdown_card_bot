import argparse
from tests.tests import analyze_baseline_weights

parser = argparse.ArgumentParser(description="Test accuracy of Showdown Bot set compared to original WOC set")
parser.add_argument('-c','--context', help='The showdown set meta to use (2000-2005)', default='2000')
parser.add_argument('-t','--type', help='Choose either Hitter or Pitcher to test',default='Hitter')
parser.add_argument('-cb','--is_current_baseline', action='store_true', help='Set to True to test for accuracy of current baseline weights, otherwise iterates through all possible weights')
parser.add_argument('-ex','--exclude_volatile', action='store_true', help='Set to True to leave out categories such as out results and 1b+ from tests')
parser.add_argument('-pts','--only_pts', action='store_true', help='Set to True to only test for point value.')
parser.add_argument('-p','--positions', help='Choose to filter by certain positions', default='', type=str)
parser.add_argument('-uw','--use_wotc', action='store_true', help='Use WOTC Command/Out combos')
parser.add_argument('-co','--command_outs', help='Filter to only certain Command-Outs combinations. Enter like "10-5,..."', default='', type=str)


args = parser.parse_args()

if __name__ == "__main__":
    # TEST SET ACCURACY
    analyze_baseline_weights(context=int(args.context), 
                             type=args.type, 
                             is_testing_current_baseline=args.is_current_baseline,
                             ignore_volatile_categories=args.exclude_volatile,
                             is_pts_only=args.only_pts,
                             position_filters=[str(item) for item in args.positions.split(',')],
                             use_wotc_command_outs=args.use_wotc,
                             command_out_combos=[str(item) for item in args.command_outs.split(',')])