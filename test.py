from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown_bot.showdown_player_card import ShowdownPlayerCard
from mlb_showdown_bot.enums.edition import Edition
from mlb_showdown_bot.enums.sets import Set
from termcolor import colored
from time import sleep

if __name__ == "__main__":
    
    # DEFINE INPUTS
    inputs_to_test = [
        {'name': 'Juan Encarnacion', 'year': '2007', 'edition': Edition.NONE.value},
        {'name': 'Walter Johnson', 'year': '1908', 'edition': Edition.NONE.value},
        {'name': 'Manny Ramirez (LAD)', 'year': '2008', 'edition': Edition.NONE.value},
        {'name': 'Mike Piazza (FLA)', 'year': '1997', 'edition': Edition.NONE.value},
        {'name': 'Aroldis Chapman (NYY)', 'year': '2016', 'edition': Edition.NONE.value},
        {'name': 'Derek Jeter', 'year': '2006+2014+2008', 'edition': Edition.SUPER_SEASON.value},
        {'name': 'Old Hoss Radbourn', 'year': '1885-1889', 'edition': Edition.NONE.value},
        {'name': 'Gary Carter', 'year': '1981+1988', 'edition': Edition.NONE.value},
        {'name': 'Bartolo Colon (Hitter)', 'year': '2016', 'edition': Edition.NONE.value},
        {'name': 'Shohei Ohtani (Pitcher)', 'year': '2021', 'edition': Edition.NONE.value},
        {'name': 'Michael Lorenzen (Pitcher)', 'year': '2019', 'edition': Edition.NONE.value},
        {'name': 'wittwh01', 'year': '1924', 'edition': Edition.NONE.value},
        {'name': 'Josh Gibson ', 'year': '1939-1944', 'edition': Edition.NONE.value},
        {'name': 'Satchel Paige', 'year': '1941+1965', 'edition': Edition.NONE.value},
        {'name': 'Mark Kotsay', 'year': '1998-2000', 'edition': Edition.NONE.value},
        {'name': 'Bert Blyleven', 'year': '1988', 'edition': Edition.NATIONALITY.value},
        {'name': 'Bret Boone', 'year': '2001', 'edition': Edition.SUPER_SEASON.value},
        {'name': 'Bob Gibson', 'year': '1968', 'edition': Edition.COOPERSTOWN_COLLECTION.value},
    ]
    num_tests = len(inputs_to_test)

    # TEST EACH PLAYER IN EACH SET
    failures = 0
    error_messages = []
    for player_inputs in inputs_to_test:
        result = 'SUCCESS'
        try:
            sleep(5)
            name = player_inputs['name']
            year = player_inputs['year']
            edition = player_inputs['edition']
            # GET PLAYER DATA
            scraper = BaseballReferenceScraper(name=name,year=year)
            statline = scraper.player_statline()
            for set in Set:
                # CREATE SHOWDOWN CARD 
                showdown = ShowdownPlayerCard(
                    name=name,
                    year=year,
                    stats=statline,
                    set=set.value,
                    edition=edition,
                    print_to_cli=False
                )
                showdown.card_image()
                if showdown.img_loading_error:
                    result = 'FAILED'
                    failures += 1
                    error_messages.append(f'{name}-{set.value}: {showdown.img_loading_error}')
        except Exception as e:
            result = 'FAILED'
            failures += 1
            error_messages.append(f'{name}-{set.value}: {str(e)}')
        print(colored(f'{name}: {result}', 'red' if result == 'FAILED' else 'green'))

    # PRINT RESULT
    pct_success = round((num_tests - failures) / num_tests * 100,2)
    print(f"-- SUCCESS RATE: {pct_success}%--")
    if len(error_messages) > 0:
        print(error_messages)
