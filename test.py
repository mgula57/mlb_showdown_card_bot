from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown_bot.showdown_player_card import ShowdownPlayerCard
import mlb_showdown_bot.showdown_constants as sc
from termcolor import colored
from time import sleep

if __name__ == "__main__":
    
    # DEFINE INPUTS
    inputs_to_test = [
        {'name': 'Juan Encarnacion', 'year': '2007', 'edition': sc.Edition.NONE.value},
        {'name': 'Walter Johnson', 'year': '1908', 'edition': sc.Edition.NONE.value},
        {'name': 'Manny Ramirez (LAD)', 'year': '2008', 'edition': sc.Edition.NONE.value},
        {'name': 'Mike Piazza (FLA)', 'year': '1997', 'edition': sc.Edition.NONE.value},
        {'name': 'Aroldis Chapman (NYY)', 'year': '2016', 'edition': sc.Edition.NONE.value},
        {'name': 'Derek Jeter', 'year': '2006+2014+2008', 'edition': sc.Edition.NONE.value},
        {'name': 'Old Hoss Radbourn', 'year': '1885-1889', 'edition': sc.Edition.NONE.value},
        {'name': 'Gary Carter', 'year': '1981+1988', 'edition': sc.Edition.NONE.value},
        {'name': 'Bartolo Colon (Hitter)', 'year': '2016', 'edition': sc.Edition.NONE.value},
        {'name': 'Shohei Ohtani (Pitcher)', 'year': '2021', 'edition': sc.Edition.NONE.value},
        {'name': 'Michael Lorenzen (Pitcher)', 'year': '2019', 'edition': sc.Edition.NONE.value},
        {'name': 'wittwh01', 'year': '1924', 'edition': sc.Edition.NONE.value},
        {'name': 'Josh Gibson ', 'year': '1939-1944', 'edition': sc.Edition.NONE.value},
        {'name': 'Satchel Paige', 'year': '1941+1965', 'edition': sc.Edition.NONE.value},
        {'name': 'Mark Kotsay', 'year': '1998-2000', 'edition': sc.Edition.NONE.value},
        {'name': 'Bert Blyleven', 'year': '1988', 'edition': sc.Edition.NATIONALITY.value},
        {'name': 'Bret Boone', 'year': '2001', 'edition': sc.Edition.SUPER_SEASON.value},
        {'name': 'Bob Gibson', 'year': '1968', 'edition': sc.Edition.COOPERSTOWN_COLLECTION.value},
    ]
    num_tests = len(inputs_to_test)
    sets = ['2000','2001','2002','2003','2004','2005',sc.CLASSIC_SET,sc.EXPANDED_SET]

    # TEST EACH PLAYER IN EACH SET
    failures = 0
    error_messages = []
    for player_inputs in inputs_to_test:
        result = 'SUCCESS'
        try:
            sleep(3)
            name = player_inputs['name']
            year = player_inputs['year']
            edition = player_inputs['edition']
            # GET PLAYER DATA
            scraper = BaseballReferenceScraper(name=name,year=year)
            statline = scraper.player_statline()
            for set in sets:
                # CREATE SHOWDOWN CARD 
                showdown = ShowdownPlayerCard(
                    name=name,
                    year=year,
                    stats=statline,
                    context=set,
                    edition=edition,
                    print_to_cli=False
                )
                showdown.card_image()
        except Exception as e:
            result = 'FAILED'
            failures += 1
            error_messages.append(f'{name}-{set}: {str(e)}')
        print(colored(f'{name}: {result}', 'red' if result == 'FAILED' else 'green'))

    # PRINT RESULT
    pct_success = round((num_tests - failures) / num_tests * 100,2)
    print(f"-- SUCCESS RATE: {pct_success}%--")
    if len(error_messages) > 0:
        print(error_messages)
