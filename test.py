import argparse
from mlb_showdown.tests import analyze

parser = argparse.ArgumentParser(description="Test accuracy of Showdown Bot set compared to original WOC set")
parser.add_argument('-c','--context', help='The showdown set meta to use (2000-2005)', default='2000')
parser.add_argument('-t','--type', help='Choose either Hitter or Pitcher to test',default='Hitter')
parser.add_argument('-cb','--is_current_baseline', action='store_true', help='Set to True to test for accuracy of current baseline weights, otherwise iterates through all possible weights')
args = parser.parse_args()

if __name__ == "__main__":
    # TEST SET ACCURACY
    analyze(context=int(args.context), 
            type=args.type, 
            is_testing_current_baseline=args.is_current_baseline)