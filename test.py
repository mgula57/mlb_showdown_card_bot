from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper
from mlb_showdown_bot.showdown_player_card_generator import ShowdownPlayerCardGenerator
from termcolor import colored

if __name__ == "__main__":
    
    # DEFINE INPUTS
    inputs_to_test = [
        {'name': 'Juan Encarnacion', 'year': '2007',},
        {'name': 'Walter Johnson', 'year': '1908',},
        {'name': 'Manny Ramirez (LAD)', 'year': '2008',},
        {'name': 'Mike Piazza (FLA)', 'year': '1997',},
        {'name': 'Aroldis Chapman (NYY)', 'year': '2016',},
        {'name': 'Derek Jeter', 'year': '2006+2014+2008',},
        {'name': 'Old Hoss Radbourn', 'year': '1885-1889',},
        {'name': 'Gary Carter', 'year': '1981+1988',},
        {'name': 'Bartolo Colon (Hitter)', 'year': '2016',},
        {'name': 'Shohei Ohtani (Pitcher)', 'year': '2021',},
        {'name': 'Michael Lorenzen (Pitcher)', 'year': '2019',},
        {'name': 'wittwh01', 'year': '1924',},
        {'name': 'Josh Gibson ', 'year': '1939-1944',},
        {'name': 'Satchel Paige', 'year': '1941+1965',},
    ]
    num_tests = len(inputs_to_test)
    sets = ['2000','2001','2002','2003','2004','2005','2022-CLASSIC','2022-EXPANDED']

    # TEST EACH PLAYER IN EACH SET
    failures = 0
    error_messages = []
    for player_inputs in inputs_to_test:
        result = 'SUCCESS'
        try:
            name = player_inputs['name']
            year = player_inputs['year']
            # GET PLAYER DATA
            scraper = BaseballReferenceScraper(name=name,year=year)
            statline = scraper.player_statline()
            for set in sets:
                # CREATE SHOWDOWN CARD 
                showdown = ShowdownPlayerCardGenerator(
                    name=name,
                    year=year,
                    stats=statline,
                    context=set,
                    print_to_cli=False
                )
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
