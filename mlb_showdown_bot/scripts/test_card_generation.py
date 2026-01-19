"""
Test script for validating card generation across different players, years, and sets.
"""

from time import sleep
from termcolor import colored

from mlb_showdown_bot.core.card.card_generation import generate_card
from mlb_showdown_bot.core.card.showdown_player_card import ShowdownPlayerCard, Edition, Set, StatsPeriodType, StatsPeriod


# Test cases covering various player scenarios
TEST_CASES = [
    {'name': 'Juan Encarnacion', 'year': '2007', 'edition': Edition.NONE.value},
    {'name': 'Walter Johnson', 'year': '1908', 'edition': Edition.NONE.value},
    {'name': 'Manny Ramirez (LAD)', 'year': '2008', 'edition': Edition.NONE.value},
    {'name': 'Mike Piazza (FLA)', 'year': '1998', 'edition': Edition.NONE.value},
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
    {'name': 'Jackie Robinson', 'year': 'CAREER', 'edition': Edition.NONE.value},
    {'name': 'Willie Mays', 'year': 'CAREER', 'edition': Edition.NONE.value},
    {
        'name': 'Jesse Winker',
        'year': '2024',
        'edition': Edition.NONE.value,
        'stats_period_type': StatsPeriodType.DATE_RANGE.value,
        'start_date': '2024-04-01',
        'end_date': '2024-04-30'
    },
]


def create_stats_period(player_inputs: dict) -> StatsPeriod:
    """Create StatsPeriod object from player inputs."""
    return StatsPeriod(
        type=player_inputs.get('stats_period_type', StatsPeriodType.REGULAR_SEASON),
        year=player_inputs['year'],
        start_date=player_inputs.get('start_date'),
        end_date=player_inputs.get('end_date'),
        split=player_inputs.get('split')
    )


def test_player_card(player_inputs: dict, set_value: str) -> tuple[str, str | None]:
    """
    Test card generation for a single player and set.
    
    Returns:
        Tuple of (result, error_message)
    """
    name = player_inputs['name']
    stats_period = create_stats_period(player_inputs)
    
    try:
        result = generate_card(set=set_value, **player_inputs)

        if result.get('error', None):
            return 'FAILED', f"{name}-{set_value}: {result['error']}"
        
        return 'SUCCESS', None
        
    except Exception as e:
        return 'FAILED', f'{name}-{set_value}: {str(e)}'


def run_tests(test_cases: list[dict] = None, sleep_seconds: int = 0, skip_images: bool = False) -> None:
    """
    Run card generation tests for all players across all sets.
    
    Args:
        test_cases: List of player input dictionaries
        sleep_seconds: Seconds to sleep between tests (to avoid rate limiting)
        skip_images: Whether to skip image generation tests
    """
    if test_cases is None:
        test_cases = TEST_CASES

    failures = 0
    error_messages = []
    total_tests = len(test_cases) * len(Set)

    output_folder_path = None
    if not skip_images:
        output_folder_path = 'test_output_images'
    
    print(f"Running {len(test_cases)} players across {len(Set)} sets ({total_tests} total tests)...\n")
    
    for player_inputs in test_cases:
        name = player_inputs['name']
        player_inputs['output_folder_path'] = output_folder_path
        
        for set_enum in Set:
            result, error = test_player_card(player_inputs, set_enum.value)
            
            if result == 'FAILED':
                failures += 1
                error_messages.append(error)
            
            # Print result
            color = 'red' if result == 'FAILED' else 'green'
            print(colored(f'{name} ({set_enum.value}): {result}', color))
            
            # Sleep to avoid rate limiting
            if sleep_seconds > 0:
                sleep(sleep_seconds)
    
    # Print summary
    success_rate = round((total_tests - failures) / total_tests * 100, 2)
    print(f"\n{'='*50}")
    print(f"SUCCESS RATE: {success_rate}% ({total_tests - failures}/{total_tests})")
    print(f"{'='*50}\n")
    
    if error_messages:
        print("ERRORS:")
        for error in error_messages:
            print(f"  - {error}")


if __name__ == "__main__":
    run_tests(TEST_CASES)
