from enum import Enum

# -------------------------------------------
# SHOWDOWN_CONSTANTS.PY
#   - FILE TO STORE ALL WEIGHTS / STATIC VALUES
#     NEEDED TO GENERATE PLAYER CARDS
# -------------------------------------------

"""
SET STYLES
"""
EXPANDED_SET = 'EXPANDED'
CLASSIC_SET = 'CLASSIC'
EXPANDED_SETS = ['2002','2003','2004','2005',EXPANDED_SET,]
CLASSIC_SETS = ['2000','2001',CLASSIC_SET,]
SETS_HAS_ICONS = ['2003','2004','2005',CLASSIC_SET,EXPANDED_SET,]
CLASSIC_AND_EXPANDED_SETS = [EXPANDED_SET, CLASSIC_SET]

"""
ERAS
"""
ERA_PRE_1900 = "PRE 1900 ERA"
ERA_DEAD_BALL = "DEAD BALL ERA"
ERA_LIVE_BALL = "LIVE BALL ERA"
ERA_INTEGRATION = "INTEGRATION ERA"
ERA_EXPANSION = "EXPANSION ERA"
ERA_FREE_AGENCY = "FREE AGENCY ERA"
ERA_STEROID = "STEROID ERA"
ERA_POST_STEROID = "POST STEROID ERA"
ERA_STATCAST = "STATCAST ERA"
ERA_PITCH_CLOCK = "PITCH CLOCK ERA"
ERA_YEAR_RANGE = {
    ERA_PRE_1900: list(range(1884, 1900)),
    ERA_DEAD_BALL: list(range(1900, 1920)),
    ERA_LIVE_BALL: list(range(1920, 1942)),
    ERA_INTEGRATION: list(range(1942, 1961)),
    ERA_EXPANSION: list(range(1961, 1977)),
    ERA_FREE_AGENCY: list(range(1977, 1994)),
    ERA_STEROID: list(range(1994, 2010)),
    ERA_POST_STEROID: list(range(2010, 2015)),
    ERA_STATCAST: list(range(2015, 2023)),
    ERA_PITCH_CLOCK: list(range(2023, 2025)),
}

"""
SPEED AND FIELDING
  - MIN AND MAX USED IN PERCENTILE CALCULATIONS
  - ** STOLEN BASES MINIMUM IS NEGATIVE JUST TO BALANCE OUT PERCENTILE RANGE
"""
SPRINT_SPEED_KEY = 'SPRINT SPEED'
STOLEN_BASES_KEY = 'STOLEN BASES'
SPEED_METRIC_MAX = {
    SPRINT_SPEED_KEY: 31,
    STOLEN_BASES_KEY: 26,
}
SPEED_METRIC_MIN = {
    SPRINT_SPEED_KEY: 23,
    STOLEN_BASES_KEY: -25,
}
SPEED_METRIC_WEIGHT = {
    SPRINT_SPEED_KEY: 0.60,
    STOLEN_BASES_KEY: 0.40,
}
SB_OUTLIER_SPEED_CUTOFF = 21
SPEED_METRIC_WEIGHT_SB_OUTLIERS = {
    SPRINT_SPEED_KEY: 0.25,
    STOLEN_BASES_KEY: 0.75,
}
SPEED_METRIC_MULTIPLIER = {
    SPRINT_SPEED_KEY: {
        '2000': 1.0,
        '2001': 1.0,
        '2002': 1.0,
        '2003': 1.0,
        '2004': 1.0,
        '2005': 1.0,
        CLASSIC_SET: 1.0,
        EXPANDED_SET: 1.0,
    },
    STOLEN_BASES_KEY: {
        '2000': 1.21,
        '2001': 1.22,
        '2002': 1.2,
        '2003': 0.95,
        '2004': 0.98,
        '2005': 1.0,
        CLASSIC_SET: 1.0,
        EXPANDED_SET: 1.0,
    },
}
STOLEN_BASES_PER_650_PA_THRESHOLD_MAX = {
    '2000': 100,
    '2001': 100,
    '2002': 100,
    '2003': 100,
    '2004': 100,
    '2005': 100,
    CLASSIC_SET: 100,
    EXPANDED_SET: 100,
}
SPEED_ERA_MULTIPLIER = {
    ERA_PRE_1900: 0.80,
    ERA_DEAD_BALL: 0.80,
    ERA_LIVE_BALL: 1.0,
    ERA_INTEGRATION: 1.0,
    ERA_EXPANSION: 1.0,
    ERA_FREE_AGENCY: 1.0,
    ERA_STEROID: 1.0,
    ERA_POST_STEROID: 1.0,
    ERA_STATCAST: 1.0,
    ERA_PITCH_CLOCK: 0.99,
}
SPEED_METRIC_TOP_PERCENTILE = {
    SPRINT_SPEED_KEY: 25.0,
    STOLEN_BASES_KEY: 18.0,
}
MAX_IN_GAME_SPD = {
    '2000': 28,
    '2001': 28,
    '2002': 28,
    '2003': 28,
    '2004': 28,
    '2005': 28,
    CLASSIC_SET: 28,
    EXPANDED_SET: 28,
}
MIN_IN_GAME_SPD = {
    '2000': 8,
    '2001': 8,
    '2002': 8,
    '2003': 8,
    '2004': 8,
    '2005': 8,
    CLASSIC_SET: 8,
    EXPANDED_SET: 8,
}
SPEED_C_CUTOFF = {
    '2000': 12,
    '2001': 12,
    '2002': 13,
    '2003': 12,
    '2004': 12,
    '2005': 12,
    CLASSIC_SET: 12,
    EXPANDED_SET: 12,
}

MIN_SABER_FIELDING = {
    'oaa': -16,
    'drs': -20,
    'tzr': -18,
    'dWAR': -2.5
}
MAX_SABER_FIELDING = {
    'oaa': 16,
    'drs': 20,
    'tzr': 18,
    'dWAR': 2.5
}
# FOR 1B, USE A STATIC CUTOFFS INSTEAD OF RANGE
FIRST_BASE_PLUS_2_CUTOFF = {
    'oaa': 13,
    'drs': 17,
    'tzr': 15,
    'dWAR': 0.8
}
FIRST_BASE_PLUS_1_CUTOFF = {
    'oaa': 2,
    'drs': 4,
    'tzr': 4,
    'dWAR': -0.25
}
# -1 1B DEFENSE ONLY APPLIES TO 2022 SET AND BEYOND
FIRST_BASE_MINUS_1_CUTOFF = {
    'oaa': -5,
    'drs': -5,
    'tzr': -5,
    'dWAR': -1.0
}
# REDUCES OUTLIERS IN OOA BY REDUCING VALUES OVER THE DEFENSE MAXIMUM
OAA_OVER_MAX_MULTIPLIER = 0.5
# MINIMUM REQUIRED GAMES PLAYED AT A POSITION TO QUALIFY
NUMBER_OF_GAMES_DEFENSE = 7 
PCT_OF_GAMES_DEFENSE = 0.15
PCT_OF_GAMES_DEFENSE_MULTI_YEAR = 0.25
STARTING_PITCHER_PCT_GAMES_STARTED = 0.40
CLOSER_MIN_SAVES_REQUIRED = 10
NUM_POSITION_SLOTS = {
    '2000': 2,
    '2001': 2,
    '2002': 2,
    '2003': 2,
    '2004': 2,
    '2005': 2,
    CLASSIC_SET: 3,
    EXPANDED_SET: 3,
}
POSITIONS_ALLOWED_COMBINATIONS = {
    '2B': ['SS','3B',],
    '3B': ['SS','2B',],
    'SS': ['2B','3B',]
}
INFIELD_PLUS_ONE_REQUIREMENT = 6
POSITION_ORDERING = {
    'C': 11,
    'CA': 10,
    '1B': 9,
    '2B': 8,
    '3B': 7,
    'SS': 6,
    'LF/RF': 5,
    'CF': 4,
    'OF': 3,
    'IF': 2,
    'STARTER': 1,
    'RELIEVER': 1,
    'CLOSER': 1,
}
TEMPLATE_COLOR_0405 = {
    'Pitcher': 'BLUE',
    'Hitter': 'GREEN',
}

# MULTIPLIER TO MATCH PU WITH ORIGINAL SETS
PU_MULTIPLIER = {
    '2000': 2.25,
    '2001': 2.5,
    '2002': 2.8,
    '2003': 2.2,
    '2004': 2.05,
    '2005': 2.4,
    CLASSIC_SET: 2.5,
    EXPANDED_SET: 2.4,
}
PU_MULTIPLIER_1988 = 0.5 # PU WERE SKEWED IN 1988, REDUCE THEIR % BY 40%
# THIS GB MULTIPLIER IS A MORE SIMPLE MODE OF ADJUSTMENT.
# REPLACE HAVING DEFAULT GB AND FB FOR OPPONENT CHART
GB_MULTIPLIER = {
    'hitter': {
        '2000': {            
            ERA_PRE_1900: 1.10,
            ERA_DEAD_BALL: 1.10,
            ERA_LIVE_BALL: 1.10,
            ERA_INTEGRATION: 1.05,
            ERA_EXPANSION: 1.05,
            ERA_FREE_AGENCY: 1.05,
            ERA_STEROID: 1.00,
            ERA_POST_STEROID: 1.00,
            ERA_STATCAST: 0.95,
            ERA_PITCH_CLOCK: 0.95,
        },
        '2001': {
            ERA_PRE_1900: 1.20,
            ERA_DEAD_BALL: 1.20,
            ERA_LIVE_BALL: 1.15,
            ERA_INTEGRATION: 1.15,
            ERA_EXPANSION: 1.15,
            ERA_FREE_AGENCY: 1.15,
            ERA_STEROID: 1.11,
            ERA_POST_STEROID: 1.05,
            ERA_STATCAST: 1.00,
            ERA_PITCH_CLOCK: 1.00,
        },
        '2002': {
            ERA_PRE_1900: 1.20,
            ERA_DEAD_BALL: 1.20,
            ERA_LIVE_BALL: 1.15,
            ERA_INTEGRATION: 1.15,
            ERA_EXPANSION: 1.15,
            ERA_FREE_AGENCY: 1.15,
            ERA_STEROID: 1.15,
            ERA_POST_STEROID: 1.10,
            ERA_STATCAST: 1.05,
            ERA_PITCH_CLOCK: 1.05,
        },
        '2003': {
            ERA_PRE_1900: 1.20,
            ERA_DEAD_BALL: 1.20,
            ERA_LIVE_BALL: 1.20,
            ERA_INTEGRATION: 1.15,
            ERA_EXPANSION: 1.15,
            ERA_FREE_AGENCY: 1.15,
            ERA_STEROID: 1.12,
            ERA_POST_STEROID: 1.10,
            ERA_STATCAST: 1.05,
            ERA_PITCH_CLOCK: 1.05,
        },
        '2004': {
            ERA_PRE_1900: 1.20,
            ERA_DEAD_BALL: 1.20,
            ERA_LIVE_BALL: 1.20,
            ERA_INTEGRATION: 1.15,
            ERA_EXPANSION: 1.15,
            ERA_FREE_AGENCY: 1.15,
            ERA_STEROID: 1.10,
            ERA_POST_STEROID: 1.05,
            ERA_STATCAST: 1.00,
            ERA_PITCH_CLOCK: 1.00,
        },
        '2005': {
            ERA_PRE_1900: 1.20,
            ERA_DEAD_BALL: 1.20,
            ERA_LIVE_BALL: 1.20,
            ERA_INTEGRATION: 1.15,
            ERA_EXPANSION: 1.15,
            ERA_FREE_AGENCY: 1.15,
            ERA_STEROID: 1.10,
            ERA_POST_STEROID: 1.05,
            ERA_STATCAST: 1.00,
            ERA_PITCH_CLOCK: 1.05,
        },
        CLASSIC_SET: {
            ERA_PRE_1900: 1.10,
            ERA_DEAD_BALL: 1.10,
            ERA_LIVE_BALL: 1.10,
            ERA_INTEGRATION: 1.05,
            ERA_EXPANSION: 1.05,
            ERA_FREE_AGENCY: 1.05,
            ERA_STEROID: 1.00,
            ERA_POST_STEROID: 0.95,
            ERA_STATCAST: 0.90,
            ERA_PITCH_CLOCK: 0.90,
        },
        EXPANDED_SET: {
            ERA_PRE_1900: 1.10,
            ERA_DEAD_BALL: 1.10,
            ERA_LIVE_BALL: 1.10,
            ERA_INTEGRATION: 1.05,
            ERA_EXPANSION: 1.05,
            ERA_FREE_AGENCY: 1.05,
            ERA_STEROID: 1.00,
            ERA_POST_STEROID: 0.95,
            ERA_STATCAST: 0.90,
            ERA_PITCH_CLOCK: 0.90,
        },
    },
    'pitcher': {
        '2000': {
            ERA_PRE_1900: 1.05,
            ERA_DEAD_BALL: 1.05,
            ERA_LIVE_BALL: 1.05,
            ERA_INTEGRATION: 1.00,
            ERA_EXPANSION: 1.00,
            ERA_FREE_AGENCY: 1.00,
            ERA_STEROID: 0.85,
            ERA_POST_STEROID: 0.85,
            ERA_STATCAST: 0.82,
            ERA_PITCH_CLOCK: 0.82,
        },
        '2001': {
            ERA_PRE_1900: 1.05,
            ERA_DEAD_BALL: 1.05,
            ERA_LIVE_BALL: 1.05,
            ERA_INTEGRATION: 1.00,
            ERA_EXPANSION: 1.00,
            ERA_FREE_AGENCY: 1.00,
            ERA_STEROID: 0.93,
            ERA_POST_STEROID: 0.90,
            ERA_STATCAST: 0.85,
            ERA_PITCH_CLOCK: 0.85,
        },
        '2002': {
            ERA_PRE_1900: 1.05,
            ERA_DEAD_BALL: 1.05,
            ERA_LIVE_BALL: 1.05,
            ERA_INTEGRATION: 1.00,
            ERA_EXPANSION: 1.00,
            ERA_FREE_AGENCY: 1.00,
            ERA_STEROID: 0.91,
            ERA_POST_STEROID: 0.90,
            ERA_STATCAST: 0.85,
            ERA_PITCH_CLOCK: 0.85,
        },
        '2003': {
            ERA_PRE_1900: 1.15,
            ERA_DEAD_BALL: 1.15,
            ERA_LIVE_BALL: 1.15,
            ERA_INTEGRATION: 1.10,
            ERA_EXPANSION: 1.10,
            ERA_FREE_AGENCY: 1.10,
            ERA_STEROID: 1.05,
            ERA_POST_STEROID: 1.00,
            ERA_STATCAST: 0.95,
            ERA_PITCH_CLOCK: 0.95,
        },
        '2004': {
            ERA_PRE_1900: 1.15,
            ERA_DEAD_BALL: 1.15,
            ERA_LIVE_BALL: 1.15,
            ERA_INTEGRATION: 1.10,
            ERA_EXPANSION: 1.10,
            ERA_FREE_AGENCY: 1.10,
            ERA_STEROID: 1.05,
            ERA_POST_STEROID: 1.00,
            ERA_STATCAST: 0.95,
            ERA_PITCH_CLOCK: 0.95,
        },
        '2005': {
            ERA_PRE_1900: 1.15,
            ERA_DEAD_BALL: 1.15,
            ERA_LIVE_BALL: 1.15,
            ERA_INTEGRATION: 1.10,
            ERA_EXPANSION: 1.10,
            ERA_FREE_AGENCY: 1.10,
            ERA_STEROID: 1.05,
            ERA_POST_STEROID: 1.00,
            ERA_STATCAST: 0.95,
            ERA_PITCH_CLOCK: 0.95,
        },
        CLASSIC_SET: {
            ERA_PRE_1900: 1.10,
            ERA_DEAD_BALL: 1.10,
            ERA_LIVE_BALL: 1.10,
            ERA_INTEGRATION: 1.05,
            ERA_EXPANSION: 1.05,
            ERA_FREE_AGENCY: 1.05,
            ERA_STEROID: 1.00,
            ERA_POST_STEROID: 0.95,
            ERA_STATCAST: 0.90,
            ERA_PITCH_CLOCK: 0.90,
        },
        EXPANDED_SET: {
            ERA_PRE_1900: 1.10,
            ERA_DEAD_BALL: 1.10,
            ERA_LIVE_BALL: 1.10,
            ERA_INTEGRATION: 1.05,
            ERA_EXPANSION: 1.05,
            ERA_FREE_AGENCY: 1.05,
            ERA_STEROID: 1.00,
            ERA_POST_STEROID: 0.95,
            ERA_STATCAST: 0.90,
            ERA_PITCH_CLOCK: 0.90,
        },
    },
}

HR_ROUNDING_CUTOFF = {
    '2000': {
        ERA_PRE_1900: 0.75,
        ERA_DEAD_BALL: 0.75,
        ERA_LIVE_BALL: 0.75,
        ERA_INTEGRATION: 0.75,
        ERA_EXPANSION: 0.75,
        ERA_FREE_AGENCY: 0.75,
        ERA_STEROID: 0.85,
        ERA_POST_STEROID: 0.75,
        ERA_STATCAST: 0.70,
        ERA_PITCH_CLOCK: 0.70,
    },
    '2001': {
        ERA_PRE_1900: 0.75,
        ERA_DEAD_BALL: 0.75,
        ERA_LIVE_BALL: 0.75,
        ERA_INTEGRATION: 0.75,
        ERA_EXPANSION: 0.75,
        ERA_FREE_AGENCY: 0.75,
        ERA_STEROID: 0.85,
        ERA_POST_STEROID: 0.75,
        ERA_STATCAST: 0.70,
        ERA_PITCH_CLOCK: 0.70,
    },
    '2002': {
        ERA_PRE_1900: 0.75,
        ERA_DEAD_BALL: 0.75,
        ERA_LIVE_BALL: 0.75,
        ERA_INTEGRATION: 0.75,
        ERA_EXPANSION: 0.75,
        ERA_FREE_AGENCY: 0.75,
        ERA_STEROID: 0.85,
        ERA_POST_STEROID: 0.75,
        ERA_STATCAST: 0.70,
        ERA_PITCH_CLOCK: 0.70,
    },
    '2003': {
        ERA_PRE_1900: 0.75,
        ERA_DEAD_BALL: 0.75,
        ERA_LIVE_BALL: 0.75,
        ERA_INTEGRATION: 0.75,
        ERA_EXPANSION: 0.75,
        ERA_FREE_AGENCY: 0.75,
        ERA_STEROID: 0.85,
        ERA_POST_STEROID: 0.75,
        ERA_STATCAST: 0.70,
        ERA_PITCH_CLOCK: 0.70,
    },
    '2004': {
        ERA_PRE_1900: 0.75,
        ERA_DEAD_BALL: 0.75,
        ERA_LIVE_BALL: 0.75,
        ERA_INTEGRATION: 0.75,
        ERA_EXPANSION: 0.75,
        ERA_FREE_AGENCY: 0.75,
        ERA_STEROID: 0.85,
        ERA_POST_STEROID: 0.75,
        ERA_STATCAST: 0.70,
        ERA_PITCH_CLOCK: 0.70,
    },
    '2005': {
        ERA_PRE_1900: 0.75,
        ERA_DEAD_BALL: 0.75,
        ERA_LIVE_BALL: 0.75,
        ERA_INTEGRATION: 0.75,
        ERA_EXPANSION: 0.75,
        ERA_FREE_AGENCY: 0.75,
        ERA_STEROID: 0.85,
        ERA_POST_STEROID: 0.75,
        ERA_STATCAST: 0.70,
        ERA_PITCH_CLOCK: 0.70,
    },
    CLASSIC_SET: {
        ERA_PRE_1900: 0.75,
        ERA_DEAD_BALL: 0.75,
        ERA_LIVE_BALL: 0.75,
        ERA_INTEGRATION: 0.75,
        ERA_EXPANSION: 0.75,
        ERA_FREE_AGENCY: 0.75,
        ERA_STEROID: 0.85,
        ERA_POST_STEROID: 0.75,
        ERA_STATCAST: 0.70,
        ERA_PITCH_CLOCK: 0.70,
    },
    EXPANDED_SET: {
        ERA_PRE_1900: 0.75,
        ERA_DEAD_BALL: 0.75,
        ERA_LIVE_BALL: 0.75,
        ERA_INTEGRATION: 0.75,
        ERA_EXPANSION: 0.75,
        ERA_FREE_AGENCY: 0.75,
        ERA_STEROID: 0.85,
        ERA_POST_STEROID: 0.75,
        ERA_STATCAST: 0.70,
        ERA_PITCH_CLOCK: 0.70,
    },
}
"""
BASELINE PITCHER VALUES
NOTE: INDIVIDUAL RESULT CATEGORIES MAY NOT ADD UP TO 20 OR TOTAL OUTS.
      THIS IS BECAUSE NOT DOING SO HELPS ACCURACY AGAINST THE ORIGINAL SETS.
"""
BASELINE_PITCHER = {
    '2000': {
        ERA_PRE_1900: {
            'command': 3.0,
            'outs': 15.85,
            'so': 2.50,
            'bb': 1.40,
            '1b': 2.15,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.00,
        },
        ERA_DEAD_BALL: {
            'command': 3.0,
            'outs': 15.85,
            'so': 2.50,
            'bb': 1.40,
            '1b': 2.15,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.00,
        },
        ERA_LIVE_BALL: {
            'command': 3.10,
            'outs': 15.75,
            'so': 4.70,
            'bb': 1.46,
            '1b': 2.07,
            '2b': 0.67,
            '3b': 0.00,
            'hr': 0.05
        },
        ERA_INTEGRATION: {
            'command': 3.00,
            'outs': 15.90,
            'so': 3.80,
            'bb': 1.40,
            '1b': 2.20,
            '2b': 0.45,
            '3b': 0.00,
            'hr': 0.05,
        },
        ERA_EXPANSION: {
            'command': 3.10,
            'outs': 16.00,
            'so': 4.00,
            'bb': 1.35,
            '1b': 2.15,
            '2b': 0.45,
            '3b': 0.00,
            'hr': 0.05,
        },
        ERA_FREE_AGENCY: {
            'command': 3.00,
            'outs': 16.00,
            'so': 4.75,
            'bb': 1.40,
            '1b': 1.74,
            '2b': 0.67,
            '3b': 0.01,
            'hr': 0.07,
        },
        ERA_STEROID: {
            'command': 3.0,
            'outs': 15.75,
            'so': 4.5,
            'bb': 1.35,
            '1b': 1.95,
            '2b': 0.67,
            '3b': 0.00,
            'hr': 0.08
        },
        ERA_POST_STEROID: {
            'command': 3.00,
            'outs': 16.10,
            'so': 6.00,
            'bb': 1.40,
            '1b': 1.74,
            '2b': 0.65,
            '3b': 0.01,
            'hr': 0.10,
        },
        ERA_STATCAST: {
            'command': 3.25,
            'outs': 16.00,
            'so': 6.00,
            'bb': 1.35,
            '1b': 1.92,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.08,
        },
        ERA_PITCH_CLOCK: {
            'command': 3.24,
            'outs': 16.00,
            'so': 6.00,
            'bb': 1.35,
            '1b': 1.92,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.08,
        },
    },
    '2001': {
        ERA_PRE_1900: {
            'command': 3.0,
            'outs': 15.90,
            'so': 2.50,
            'bb': 1.30,
            '1b': 2.20,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.03,
        },
        ERA_DEAD_BALL: {
            'command': 3.0,
            'outs': 15.90,
            'so': 2.50,
            'bb': 1.30,
            '1b': 2.20,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.03,
        },
        ERA_LIVE_BALL: {
            'command': 3.05,
            'outs': 15.80,
            'so': 3.55,
            'bb': 1.41,
            '1b': 2.11,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.06,
        },
        ERA_INTEGRATION: {
            'command': 3.00,
            'outs': 15.80,
            'so': 3.40,
            'bb': 1.45,
            '1b': 2.11,
            '2b': 0.55,
            '3b': 0.01,
            'hr': 0.08,
        },
        ERA_EXPANSION: {
            'command': 3.1,
            'outs': 16.1,
            'so': 3.90,
            'bb': 1.40,
            '1b': 1.92,
            '2b': 0.50,
            '3b': 0.00,
            'hr': 0.08,
        },
        ERA_FREE_AGENCY: {
            'command': 3.00,
            'outs': 16.05,
            'so': 4.40,
            'bb': 1.35,
            '1b': 1.99,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.06,
        },
        ERA_STEROID: {
            'command': 3.0,
            'outs': 16.0,
            'so': 4.1,
            'bb': 1.35,
            '1b': 2.0,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.11,
        },
        ERA_POST_STEROID: {
            'command': 3.00,
            'outs': 16.1,
            'so': 6.00,
            'bb': 1.35,
            '1b': 1.79,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.11,
        },
        ERA_STATCAST: {
            'command': 3.3,
            'outs': 16.1,
            'so': 6.00,
            'bb': 1.35,
            '1b': 1.82,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.08,
        },
        ERA_PITCH_CLOCK: {
            'command': 3.3,
            'outs': 16.0,
            'so': 6.00,
            'bb': 1.35,
            '1b': 1.82,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.08,
        },
    },
    '2002': {
        ERA_PRE_1900: {
            'command': 3.5,
            'outs': 16.2,
            'so': 2.00,
            'bb': 1.15,
            '1b': 1.25,
            '2b': 0.43,
            '3b': 0.00,
            'hr': 0.02,
        },
        ERA_DEAD_BALL: {
            'command': 3.5,
            'outs': 16.2,
            'so': 2.00,
            'bb': 1.15,
            '1b': 1.25,
            '2b': 0.43,
            '3b': 0.00,
            'hr': 0.02,
        },
        ERA_LIVE_BALL: {
            'command': 3.00,
            'outs': 16.30,
            'so': 3.70,
            'bb': 1.54,
            '1b': 1.70,
            '2b': 0.40,
            '3b': 0.01,
            'hr': 0.05,
        },
        ERA_INTEGRATION: {
            'command': 3.10,
            'outs': 16.60,
            'so': 3.70,
            'bb': 1.35,
            '1b': 1.40,
            '2b': 0.37,
            '3b': 0.00,
            'hr': 0.08,
        },
        ERA_EXPANSION: {
            'command': 3.20,
            'outs': 16.80,
            'so': 4.00,
            'bb': 1.35,
            '1b': 1.40,
            '2b': 0.35,
            '3b': 0.00,
            'hr': 0.10,
        },
        ERA_FREE_AGENCY: {
            'command': 3.35,
            'outs': 16.65,
            'so': 3.90,
            'bb': 1.15,
            '1b': 1.61,
            '2b': 0.50,
            '3b': 0.00,
            'hr': 0.09,
        },
        ERA_STEROID: {
            'command': 3.3,
            'outs': 16.7,
            'so': 4.20,
            'bb': 1.05,
            '1b': 1.40,
            '2b': 0.51,
            '3b': 0.01,
            'hr': 0.13,
        },
        ERA_POST_STEROID: {
            'command': 3.3,
            'outs': 16.80,
            'so': 5.75,
            'bb': 1.10,
            '1b': 1.37,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.13,
        },
        ERA_STATCAST: {
            'command': 3.45,
            'outs': 16.90,
            'so': 5.75,
            'bb': 1.10,
            '1b': 1.35,
            '2b': 0.52,
            '3b': 0.00,
            'hr': 0.13,
        },
        ERA_PITCH_CLOCK: {
            'command': 3.45,
            'outs': 16.80,
            'so': 5.75,
            'bb': 1.10,
            '1b': 1.35,
            '2b': 0.52,
            '3b': 0.00,
            'hr': 0.13,
        },
    },
    '2003': {
        ERA_PRE_1900: {
            'command': 3.7,
            'outs': 16.0,
            'so': 2.00,
            'bb': 1.50,
            '1b': 1.88,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.02,
        },
        ERA_DEAD_BALL: {
            'command': 3.7,
            'outs': 16.0,
            'so': 2.00,
            'bb': 1.50,
            '1b': 1.88,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.02,
        },
        ERA_LIVE_BALL: {
            'command': 3.70,
            'outs': 15.70,
            'so': 2.70,
            'bb': 1.60,
            '1b': 2.15,
            '2b': 0.50,
            '3b': 0.00,
            'hr': 0.05,
        },
        ERA_INTEGRATION: {
            'command': 3.90,
            'outs': 15.90,
            'so': 3.00,
            'bb': 1.50,
            '1b': 2.05,
            '2b': 0.47,
            '3b': 0.01,
            'hr': 0.08,
        },
        ERA_EXPANSION: {
            'command': 4.00,
            'outs': 16.00,
            'so': 3.00,
            'bb': 1.45,
            '1b': 2.00,
            '2b': 0.45,
            '3b': 0.00,
            'hr': 0.10,
        },
        ERA_FREE_AGENCY: {
            'command': 3.95,
            'outs': 16.00,
            'so': 3.30,
            'bb': 1.32,
            '1b': 1.90,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.13,
        },
        ERA_STEROID: {
            'command': 3.9,
            'outs': 16.3,
            'so': 3.65,
            'bb': 1.2,
            '1b': 1.93,
            '2b': 0.54,
            '3b': 0.13,
            'hr': 0.28,
        },
        ERA_POST_STEROID: {
            'command': 4.15,
            'outs': 15.95,
            'so': 5.00,
            'bb': 1.25,
            '1b': 1.90,
            '2b': 0.70,
            '3b': 0.00,
            'hr': 0.20,
        },
        ERA_STATCAST: {
            'command': 4.25,
            'outs': 16.00,
            'so': 5.00,
            'bb': 1.25,
            '1b': 1.90,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.20,
        },
        ERA_PITCH_CLOCK: {
            'command': 4.23,
            'outs': 16.00,
            'so': 5.00,
            'bb': 1.25,
            '1b': 1.90,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.20,
        },
    },
    '2004': {
        ERA_PRE_1900: {
            'command': 3.60,
            'outs': 16.00,
            'so': 2.10,
            'bb': 1.65,
            '1b': 1.84,
            '2b': 0.48,
            '3b': 0.00,
            'hr': 0.03,
        },
        ERA_DEAD_BALL: {
            'command': 3.60,
            'outs': 16.00,
            'so': 2.10,
            'bb': 1.65,
            '1b': 1.84,
            '2b': 0.48,
            '3b': 0.00,
            'hr': 0.03,
        },
        ERA_LIVE_BALL: {
            'command': 3.50,
            'outs': 15.70,
            'so': 2.40,
            'bb': 1.42,
            '1b': 2.15,
            '2b': 0.67,
            '3b': 0.01,
            'hr': 0.05,
        },
        ERA_INTEGRATION: {
            'command': 3.80,
            'outs': 15.80,
            'so': 2.60,
            'bb': 1.30,
            '1b': 2.05,
            '2b': 0.64,
            '3b': 0.01,
            'hr': 0.10,
        },
        ERA_EXPANSION: {
            'command': 4.00,
            'outs': 15.95,
            'so': 3.00,
            'bb': 1.20,
            '1b': 2.05,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.10,
        },
        ERA_FREE_AGENCY: {
            'command': 3.70,
            'outs': 15.90,
            'so': 3.50,
            'bb': 1.20,
            '1b': 1.95,
            '2b': 0.75,
            '3b': 0.00,
            'hr': 0.10,
        },
        ERA_STEROID: {
            'command': 3.85,
            'outs': 16.35,
            'so': 4.0,
            'bb': 1.1,
            '1b': 2.1,
            '2b': 0.48,
            '3b': 0.09,
            'hr': 0.3,
        },
        ERA_POST_STEROID: {
            'command': 3.90,
            'outs': 16.00,
            'so': 4.90,
            'bb': 1.15,
            '1b': 1.90,
            '2b': 0.70,
            '3b': 0.00,
            'hr': 0.15,
        },
        ERA_STATCAST: {
            'command': 4.00,
            'outs': 16.00,
            'so': 5.50,
            'bb': 1.15,
            '1b': 1.95,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.20,
        },
        ERA_PITCH_CLOCK: {
            'command': 4.00,
            'outs': 15.95,
            'so': 5.50,
            'bb': 1.15,
            '1b': 1.95,
            '2b': 0.60,
            '3b': 0.00,
            'hr': 0.20,
        },
    },
    '2005': {
        ERA_PRE_1900: {
            'command': 3.9,
            'outs': 16.2,
            'so': 3.87,
            'bb': 1.25,
            '1b': 2.05,
            '2b': 0.50,
            '3b': 0.09,
            'hr': 0.33,
        },
        ERA_DEAD_BALL: {
            'command': 3.60,
            'outs': 16.10,
            'so': 2.10,
            'bb': 1.60,
            '1b': 1.78,
            '2b': 0.50,
            '3b': 0.00,
            'hr': 0.02,
        },
        ERA_LIVE_BALL: {
            'command': 3.50,
            'outs': 15.70,
            'so': 2.40,
            'bb': 1.42,
            '1b': 2.10,
            '2b': 0.72,
            '3b': 0.01,
            'hr': 0.05,
        },
        ERA_INTEGRATION: {
            'command': 3.80,
            'outs': 15.85,
            'so': 4.00,
            'bb': 1.50,
            '1b': 2.05,
            '2b': 0.50,
            '3b': 0.00,
            'hr': 0.10,
        },
        ERA_EXPANSION: {
            'command': 4.00,
            'outs': 15.85,
            'so': 4.00,
            'bb': 1.40,
            '1b': 2.20,
            '2b': 0.45,
            '3b': 0.00,
            'hr': 0.10,
        },
        ERA_FREE_AGENCY: {
            'command': 3.75,
            'outs': 15.90,
            'so': 3.35,
            'bb': 1.20,
            '1b': 2.10,
            '2b': 0.70,
            '3b': 0.00,
            'hr': 0.10,
        },
        ERA_STEROID: {
            'command': 3.9,
            'outs': 16.2,
            'so': 3.87,
            'bb': 1.25,
            '1b': 2.05,
            '2b': 0.50,
            '3b': 0.09,
            'hr': 0.33,
        },
        ERA_POST_STEROID: {
            'command': 4.00,
            'outs': 15.90,
            'so': 4.80,
            'bb': 1.15,
            '1b': 2.00,
            '2b': 0.70,
            '3b': 0.00,
            'hr': 0.15,
        },
        ERA_STATCAST: {
            'command': 4.15,
            'outs': 15.90,
            'so': 5.10,
            'bb': 1.15,
            '1b': 2.00,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.20,
        },
        ERA_PITCH_CLOCK: {
            'command': 4.10,
            'outs': 15.90,
            'so': 5.10,
            'bb': 1.15,
            '1b': 2.00,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.20,
        },
    },
    CLASSIC_SET: {
        ERA_PRE_1900: {
            'command': 3.3,
            'outs': 16.0,
            'so': 5.25,
            'bb': 1.35,
            '1b': 2.0,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.11,
        },
        ERA_DEAD_BALL: {
            'command': 3.20,
            'outs': 16.0,
            'so': 3.00,
            'bb': 1.35,
            '1b': 2.00,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.03,
        },
        ERA_LIVE_BALL: {
            'command': 2.99,
            'outs': 15.70,
            'so': 3.55,
            'bb': 1.43,
            '1b': 2.20,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.05,
        },
        ERA_INTEGRATION: {
            'command': 2.95,
            'outs': 15.90,
            'so': 3.30,
            'bb': 1.45,
            '1b': 2.05,
            '2b': 0.52,
            '3b': 0.02,
            'hr': 0.10,
        },
        ERA_EXPANSION: {
            'command': 3.05,
            'outs': 16.1,
            'so': 3.80,
            'bb': 1.40,
            '1b': 1.97,
            '2b': 0.42,
            '3b': 0.00,
            'hr': 0.11,
        },
        ERA_FREE_AGENCY: {
            'command': 3.05,
            'outs': 16.1,
            'so': 3.55,
            'bb': 1.24,
            '1b': 1.89,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.12,
        },
        ERA_STEROID: {
            'command': 3.3,
            'outs': 16.0,
            'so': 4.10,
            'bb': 1.35,
            '1b': 2.0,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.11,
        },
        ERA_POST_STEROID: {
            'command': 3.00,
            'outs': 16.1,
            'so': 4.95,
            'bb': 1.24,
            '1b': 1.90,
            '2b': 0.65,
            '3b': 0.00,
            'hr': 0.11,
        },
        ERA_STATCAST: {
            'command': 3.3,
            'outs': 16.1,
            'so': 5.25,
            'bb': 1.35,
            '1b': 2.0,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.11,
        },
        ERA_PITCH_CLOCK: {
            'command': 3.25,
            'outs': 16.1,
            'so': 5.25,
            'bb': 1.35,
            '1b': 2.0,
            '2b': 0.62,
            '3b': 0.00,
            'hr': 0.11,
        },
    },
    EXPANDED_SET: {
        ERA_PRE_1900: {
            'command': 4.2,
            'outs': 16.2,
            'so': 5.5,
            'bb': 1.25,
            '1b': 2.05,
            '2b': 0.50,
            '3b': 0.09,
            'hr': 0.33,
        },
        ERA_DEAD_BALL: {
            'command': 4.0,
            'outs': 15.8,
            'so': 2.30,
            'bb': 1.70,
            '1b': 1.83,
            '2b': 0.60,
            '3b': 0.03,
            'hr': 0.05,
        },
        ERA_LIVE_BALL: {
            'command': 3.60,
            'outs': 15.65,
            'so': 2.95,
            'bb': 1.56,
            '1b': 2.12,
            '2b': 0.58,
            '3b': 0.01,
            'hr': 0.08,
        },
        ERA_INTEGRATION: {
            'command': 3.90,
            'outs': 15.80,
            'so': 3.95,
            'bb': 1.50,
            '1b': 2.02,
            '2b': 0.49,
            '3b': 0.03,
            'hr': 0.16,
        },
        ERA_EXPANSION: {
            'command': 4.00,
            'outs': 15.90,
            'so': 3.95,
            'bb': 1.45,
            '1b': 2.15,
            '2b': 0.52,
            '3b': 0.00,
            'hr': 0.11,
        },
        ERA_FREE_AGENCY: {
            'command': 3.80,
            'outs': 16.05,
            'so': 4.00,
            'bb': 1.29,
            '1b': 2.02,
            '2b': 0.71,
            '3b': 0.00,
            'hr': 0.15,
        },
        ERA_STEROID: {
            'command': 4.2,
            'outs': 16.2,
            'so': 4.00,
            'bb': 1.25,
            '1b': 2.05,
            '2b': 0.50,
            '3b': 0.09,
            'hr': 0.33,
        },
        ERA_POST_STEROID: {
            'command': 4.0,
            'outs': 16.0,
            'so': 5.20,
            'bb': 1.25,
            '1b': 2.05,
            '2b': 0.71,
            '3b': 0.01,
            'hr': 0.20,
        },
        ERA_STATCAST: {
            'command': 4.2,
            'outs': 16.1,
            'so': 5.5,
            'bb': 1.25,
            '1b': 2.05,
            '2b': 0.71,
            '3b': 0.01,
            'hr': 0.20,
        },
        ERA_PITCH_CLOCK: {
            'command': 4.15,
            'outs': 16.1,
            'so': 5.5,
            'bb': 1.25,
            '1b': 2.05,
            '2b': 0.71,
            '3b': 0.01,
            'hr': 0.20,
        },
    },
}

"""
BASELINE HITTER VALUES
NOTE: INDIVIDUAL RESULT CATEGORIES MAY NOT ADD UP TO 20 OR TOTAL OUTS.
      THIS IS BECAUSE NOT DOING SO HELPS ACCURACY AGAINST THE ORIGINAL SETS.
"""
BASELINE_HITTER = {
    '2000': {
        ERA_PRE_1900: {
            'command': 7.6,
            'outs': 4.0,
            'so': 0.2,
            'bb': 3.00,
            '1b': 8.50,
            '1b+': 1.50,
            '2b': 1.50,
            '3b': 1.00,
            'hr': 0.50,
        },
        ERA_DEAD_BALL: {
            'command': 7.6,
            'outs': 4.0,
            'so': 0.2,
            'bb': 3.00,
            '1b': 8.50,
            '1b+': 1.50,
            '2b': 1.50,
            '3b': 1.00,
            'hr': 0.50,
        },
        ERA_LIVE_BALL: {
            'command': 7.77,
            'outs': 4.0,
            'so': 1.0,
            'bb': 4.3,
            '1b': 6.95,
            '1b+': 0.53,
            '2b': 1.94,
            '3b': 0.30,
            'hr': 1.98,
        },
        ERA_INTEGRATION: {
            'command': 7.45,
            'outs': 3.60,
            'so': 1.6,
            'bb': 4.45,
            '1b': 7.10,
            '1b+': 0.75,
            '2b': 1.90,
            '3b': 0.30,
            'hr': 1.90,
        },
        ERA_EXPANSION: {
            'command': 7.35,
            'outs': 3.85,
            'so': 2.0,
            'bb': 4.4,
            '1b': 6.75,
            '1b+': 0.75,
            '2b': 1.80,
            '3b': 0.30,
            'hr': 1.90,
        },
        ERA_FREE_AGENCY: {
            'command': 7.40,
            'outs': 4.10,
            'so': 1.00,
            'bb': 4.20,
            '1b': 6.85,
            '1b+': 0.70,
            '2b': 2.00,
            '3b': 0.40,
            'hr': 1.75,
        },
        ERA_STEROID: {
            'command': 7.7,
            'outs': 3.7,
            'so': 0.2,
            'bb': 4.4,
            '1b': 6.65,
            '1b+': 0.41,
            '2b': 1.94,
            '3b': 0.30,
            'hr': 1.98,
        },
        ERA_POST_STEROID: {
            'command': 7.25,
            'outs': 3.90,
            'so': 1.80,
            'bb': 4.4,
            '1b': 6.80,
            '1b+': 0.60,
            '2b': 2.00,
            '3b': 0.40,
            'hr': 1.90,
        },
        ERA_STATCAST: {
            'command': 7.2,
            'outs': 3.90,
            'so': 2.0,
            'bb': 4.4,
            '1b': 6.80,
            '1b+': 0.50,
            '2b': 2.00,
            '3b': 0.30,
            'hr': 2.10,
        },
        ERA_PITCH_CLOCK: {
            'command': 7.35,
            'outs': 3.90,
            'so': 2.0,
            'bb': 4.4,
            '1b': 6.60,
            '1b+': 0.60,
            '2b': 2.05,
            '3b': 0.30,
            'hr': 2.15,
        },
    },
    '2001': {
        ERA_PRE_1900: {
            'command': 7.6,
            'outs': 4.0,
            'so': 0.50,
            'bb': 3.10,
            '1b': 8.50,
            '1b+': 1.50,
            '2b': 1.50,
            '3b': 1.00,
            'hr': 0.50,
        },
        ERA_DEAD_BALL: {
            'command': 7.6,
            'outs': 4.0,
            'so': 0.50,
            'bb': 3.10,
            '1b': 8.50,
            '1b+': 1.50,
            '2b': 1.50,
            '3b': 1.00,
            'hr': 0.50,
        },
        ERA_LIVE_BALL: {
            'command': 7.75,
            'outs': 3.8,
            'so': 1.00,
            'bb': 4.55,
            '1b': 6.90,
            '1b+': 0.70,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 1.9,
        },
        ERA_INTEGRATION: {
            'command': 7.45,
            'outs': 3.90,
            'so': 1.90,
            'bb': 4.50,
            '1b': 7.20,
            '1b+': 0.70,
            '2b': 1.65,
            '3b': 0.2,
            'hr': 1.85,   
        },
        ERA_EXPANSION: {
            'command': 7.41,
            'outs': 4.15,
            'so': 2.00,
            'bb': 4.45,
            '1b': 6.90,
            '1b+': 0.70,
            '2b': 1.65,
            '3b': 0.2,
            'hr': 1.9,   
        },
        ERA_FREE_AGENCY: {
            'command': 7.55,
            'outs': 4.00,
            'so': 0.90,
            'bb': 4.35,
            '1b': 6.70,
            '1b+': 0.85,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 1.95,  
        },
        ERA_STEROID: {
            'command': 7.8,
            'outs': 3.9,
            'so': 1.31,
            'bb': 4.45,
            '1b': 6.7,
            '1b+': 0.63,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 2.0,
        },
        ERA_POST_STEROID: {
            'command': 7.4,
            'outs': 4.1,
            'so': 1.90,
            'bb': 4.35,
            '1b': 6.70,
            '1b+': 0.75,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 1.95,  
        },
        ERA_STATCAST: {
            'command': 7.3,
            'outs': 4.0,
            'so': 2.00,
            'bb': 4.45,
            '1b': 6.70,
            '1b+': 0.70,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 2.0,            
        },
        ERA_PITCH_CLOCK: {
            'command': 7.4,
            'outs': 4.0,
            'so': 2.00,
            'bb': 4.45,
            '1b': 6.40,
            '1b+': 0.75,
            '2b': 2.1,
            '3b': 0.2,
            'hr': 2.1,            
        },
    },
    '2002': {
        ERA_PRE_1900: {
            'command': 9.0,
            'outs': 6.0,
            'so': 0.75,
            'bb': 3.00,
            '1b': 7.75,
            '1b+': 1.00,
            '2b': 1.00,
            '3b': 0.75,
            'hr': 0.50,
        },
        ERA_DEAD_BALL: {
            'command': 9.25,
            'outs': 6.0,
            'so': 0.75,
            'bb': 3.25,
            '1b': 6.90,
            '1b+': 1.00,
            '2b': 1.35,
            '3b': 0.75,
            'hr': 0.75,
        },
        ERA_LIVE_BALL: {
            'command': 9.7,
            'outs': 6.0,
            'so': 1.00,
            'bb': 3.40,
            '1b': 6.20,
            '1b+': 0.70,
            '2b': 1.94,
            '3b': 0.26,
            'hr': 1.50,
        },
        ERA_INTEGRATION: {
            'command': 9.45,
            'outs': 6.00,
            'so': 1.00,
            'bb': 3.45,
            '1b': 6.52,
            '1b+': 0.65,
            '2b': 1.64,
            '3b': 0.24,
            'hr': 1.50,
        },
        ERA_EXPANSION: {
            'command': 9.30,
            'outs': 6.10,
            'so': 1.00,
            'bb': 3.40,
            '1b': 6.52,
            '1b+': 0.60,
            '2b': 1.64,
            '3b': 0.24,
            'hr': 1.50,
        },
        ERA_FREE_AGENCY: {
            'command': 9.4,
            'outs': 6.00,
            'so': 1.00,
            'bb': 3.30,
            '1b': 6.60,
            '1b+': 0.55,
            '2b': 2.00,
            '3b': 0.20,
            'hr': 1.35,
        },
        ERA_STEROID: {
            'command': 9.4,
            'outs': 6.0,
            'so': 2.09,
            'bb': 3.35,
            '1b': 6.0,
            '1b+': 0.2,
            '2b': 1.94,
            '3b': 0.24,
            'hr': 1.52,
        },
        ERA_POST_STEROID: {
            'command': 9.2,
            'outs': 6.10,
            'so': 2.30,
            'bb': 3.35,
            '1b': 6.41,
            '1b+': 0.40,
            '2b': 2.00,
            '3b': 0.24,
            'hr': 1.50,
        },
        ERA_STATCAST: {
            'command': 9.10,
            'outs': 6.00,
            'so': 2.50,
            'bb': 3.40,
            '1b': 6.52,
            '1b+': 0.30,
            '2b': 1.94,
            '3b': 0.24,
            'hr': 1.60,
        },
        ERA_PITCH_CLOCK: {
            'command': 9.20,
            'outs': 6.00,
            'so': 2.50,
            'bb': 3.40,
            '1b': 6.36,
            '1b+': 0.40,
            '2b': 2.00,
            '3b': 0.24,
            'hr': 1.60,
        },
    },
    '2003': {
        ERA_PRE_1900: {
            'command': 9.0,
            'outs': 6.0,
            'so': 0.50,
            'bb': 3.50,
            '1b': 6.60,
            '1b+': 1.00,
            '2b': 1.35,
            '3b': 0.80,
            'hr': 0.75,
        },
        ERA_DEAD_BALL: {
            'command': 9.0,
            'outs': 6.0,
            'so': 0.50,
            'bb': 3.50,
            '1b': 6.60,
            '1b+': 1.00,
            '2b': 1.35,
            '3b': 0.80,
            'hr': 0.75,
        },
        ERA_LIVE_BALL: {
            'command': 9.65,
            'outs': 6.05,
            'so': 1.10,
            'bb': 3.35,
            '1b': 6.40,
            '1b+': 0.70,
            '2b': 1.65,
            '3b': 0.35,
            'hr': 1.50,
        },
        ERA_INTEGRATION: {
            'command': 9.20,
            'outs': 6.00,
            'so': 1.90,
            'bb': 3.35,
            '1b': 6.40,
            '1b+': 0.70,
            '2b': 1.65,
            '3b': 0.35,
            'hr': 1.55,
        },
        ERA_EXPANSION: {
            'command': 8.95,
            'outs': 6.20,
            'so': 3.10,
            'bb': 3.20,
            '1b': 6.35,
            '1b+': 0.70,
            '2b': 1.55,
            '3b': 0.35,
            'hr': 1.65,
        },
        ERA_FREE_AGENCY: {
            'command': 9.10,
            'outs': 6.15,
            'so': 1.00,
            'bb': 2.90,
            '1b': 6.60,
            '1b+': 0.65,
            '2b': 1.60,
            '3b': 0.35,
            'hr': 1.75,
        },
        ERA_STEROID: {
            'command': 8.6,
            'outs': 7.2,
            'so': 2.1,
            'bb': 3.0,
            '1b': 6.57,
            '1b+': 0.28,
            '2b': 1.55,
            '3b': 0.32,
            'hr': 1.75,
        },
        ERA_POST_STEROID: {
            'command': 8.90,
            'outs': 6.40,
            'so': 3.00,
            'bb': 3.00,
            '1b': 6.20,
            '1b+': 0.50,
            '2b': 1.60,
            '3b': 0.30,
            'hr': 2.00,
        },
        ERA_STATCAST: {
            'command': 8.75,
            'outs': 6.30,
            'so': 3.30,
            'bb': 3.00,
            '1b': 6.30,
            '1b+': 0.55,
            '2b': 1.55,
            '3b': 0.30,
            'hr': 2.00,
        },
        ERA_PITCH_CLOCK: {
            'command': 8.85,
            'outs': 6.30,
            'so': 3.30,
            'bb': 3.00,
            '1b': 6.20,
            '1b+': 0.60,
            '2b': 1.60,
            '3b': 0.30,
            'hr': 2.00,
        },
    },
    '2004': {
        ERA_PRE_1900: {
            'command': 9.30,
            'outs': 7.00,
            'so': 0.50,
            'bb': 3.50,
            '1b': 5.70,
            '1b+': 0.85,
            '2b': 1.60,
            '3b': 0.75,
            'hr': 0.60,
        },
        ERA_DEAD_BALL: {
            'command': 9.30,
            'outs': 7.00,
            'so': 0.50,
            'bb': 3.50,
            '1b': 5.70,
            '1b+': 0.85,
            '2b': 1.60,
            '3b': 0.75,
            'hr': 0.60,
        },
        ERA_LIVE_BALL: {
            'command': 9.70,
            'outs': 6.50,
            'so': 1.70,
            'bb': 3.50,
            '1b': 6.30,
            '1b+': 0.75,
            '2b': 1.40,
            '3b': 0.15,
            'hr': 1.40,
        },
        ERA_INTEGRATION: {
            'command': 9.50,
            'outs': 6.80,
            'so': 2.00,
            'bb': 3.35,
            '1b': 6.20,
            '1b+': 0.70,
            '2b': 1.35,
            '3b': 0.15,
            'hr': 1.45,
        },
        ERA_EXPANSION: {
            'command': 9.35,
            'outs': 7.0,
            'so': 3.00,
            'bb': 3.30,
            '1b': 6.15,
            '1b+': 0.60,
            '2b': 1.30,
            '3b': 0.15,
            'hr': 1.50,
        },
        ERA_FREE_AGENCY: {
            'command': 9.35,
            'outs': 7.35,
            'so': 1.90,
            'bb': 3.30,
            '1b': 5.90,
            '1b+': 0.55,
            '2b': 1.50,
            '3b': 0.20,
            'hr': 1.50,
        },
        ERA_STEROID: {
            'command': 9.05,
            'outs': 7.5,
            'so': 2.3,
            'bb': 2.95,
            '1b': 6.59,
            '1b+': 0.12,
            '2b': 1.25,
            '3b': 0.17,
            'hr': 1.6,
        },
        ERA_POST_STEROID: {
            'command': 9.20,
            'outs': 7.2,
            'so': 2.40,
            'bb': 3.15,
            '1b': 5.90,
            '1b+': 0.45,
            '2b': 1.55,
            '3b': 0.15,
            'hr': 1.60,
        },
        ERA_STATCAST: {
            'command': 9.00,
            'outs': 7.2,
            'so': 3.00,
            'bb': 3.15,
            '1b': 6.00,
            '1b+': 0.40,
            '2b': 1.30,
            '3b': 0.15,
            'hr': 1.80,
        },
        ERA_PITCH_CLOCK: {
            'command': 9.15,
            'outs': 7.1,
            'so': 3.00,
            'bb': 3.15,
            '1b': 5.85,
            '1b+': 0.45,
            '2b': 1.40,
            '3b': 0.15,
            'hr': 1.80,
        },
    },
    '2005': {
        ERA_PRE_1900: {
            'command': 9.0,
            'outs': 7.3,
            'so': 2.4,
            'bb': 3.3,
            '1b': 6.0,
            '1b+': 0.12,
            '2b': 1.3,
            '3b': 0.19,
            'hr': 1.4,
        },
        ERA_DEAD_BALL: {
            'command': 9.35,
            'outs': 7.1,
            'so': 0.50,
            'bb': 3.55,
            '1b': 5.35,
            '1b+': 0.80,
            '2b': 1.65,
            '3b': 0.80,
            'hr': 0.70,
        },
        ERA_LIVE_BALL: {
            'command': 9.70,
            'outs': 6.55,
            'so': 1.00,
            'bb': 3.50,
            '1b': 6.20,
            '1b+': 0.75,
            '2b': 1.40,
            '3b': 0.15,
            'hr': 1.45,
        },
        ERA_INTEGRATION: {
            'command': 9.45,
            'outs': 6.75,
            'so': 1.00,
            'bb': 3.50,
            '1b': 6.05,
            '1b+': 0.55,
            '2b': 1.45,
            '3b': 0.15,
            'hr': 1.55,
        },
        ERA_EXPANSION: {
            'command': 9.35,
            'outs': 7.1,
            'so': 1.10,
            'bb': 3.35,
            '1b': 6.00,
            '1b+': 0.40,
            '2b': 1.35,
            '3b': 0.15,
            'hr': 1.65,
        },
        ERA_FREE_AGENCY: {
            'command': 9.40,
            'outs': 7.15,
            'so': 1.10,
            'bb': 3.35,
            '1b': 5.90,
            '1b+': 0.50,
            '2b': 1.45,
            '3b': 0.15,
            'hr': 1.50,
        },
        ERA_STEROID: {
            'command': 9.0,
            'outs': 7.3,
            'so': 2.4,
            'bb': 3.3,
            '1b': 6.0,
            '1b+': 0.12,
            '2b': 1.3,
            '3b': 0.19,
            'hr': 1.4,
        },
        ERA_POST_STEROID: {
            'command': 9.25,
            'outs': 7.00,
            'so': 2.50,
            'bb': 3.35,
            '1b': 5.90,
            '1b+': 0.50,
            '2b': 1.45,
            '3b': 0.15,
            'hr': 1.65,
        },
        ERA_STATCAST: {
            'command': 9.0,
            'outs': 7.0,
            'so': 3.05,
            'bb': 3.35,
            '1b': 6.00,
            '1b+': 0.40,
            '2b': 1.35,
            '3b': 0.15,
            'hr': 1.75,
        },
        ERA_PITCH_CLOCK: {
            'command': 9.1,
            'outs': 7.0,
            'so': 3.05,
            'bb': 3.35,
            '1b': 5.85,
            '1b+': 0.45,
            '2b': 1.45,
            '3b': 0.15,
            'hr': 1.75,
        },
    },
    CLASSIC_SET: {
        ERA_PRE_1900: {
            'command': 7.5,
            'outs': 4.0,
            'so': 2.0,
            'bb': 4.45,
            '1b': 6.7,
            '1b+': 0.63,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 2.0,
        },
        ERA_DEAD_BALL: {
            'command': 7.80,
            'outs': 4.05,
            'so': 0.65,
            'bb': 3.10,
            '1b': 8.55,
            '1b+': 1.40,
            '2b': 1.50,
            '3b': 1.00,
            'hr': 0.40,
        },
        ERA_LIVE_BALL: {
            'command': 7.75,
            'outs': 3.8,
            'so': 1.00,
            'bb': 4.55,
            '1b': 6.90,
            '1b+': 0.80,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 1.80,
        },
        ERA_INTEGRATION: {
            'command': 7.50,
            'outs': 3.95,
            'so': 2.00,
            'bb': 4.50,
            '1b': 7.10,
            '1b+': 0.85,
            '2b': 1.65,
            '3b': 0.20,
            'hr': 1.75,
        },
        ERA_EXPANSION: {
            'command': 7.42,
            'outs': 4.10,
            'so': 2.00,
            'bb': 4.45,
            '1b': 6.80,
            '1b+': 0.80,
            '2b': 1.75,
            '3b': 0.20,
            'hr': 1.85,
        },
        ERA_FREE_AGENCY: {
            'command': 7.60,
            'outs': 4.1,
            'so': 0.80,
            'bb': 4.40,
            '1b': 6.60,
            '1b+': 0.80,
            '2b': 2.00,
            '3b': 0.25,
            'hr': 1.75,
        },
        ERA_STEROID: {
            'command': 7.5,
            'outs': 4.0,
            'so': 2.0,
            'bb': 4.45,
            '1b': 6.7,
            '1b+': 0.63,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 2.0,
        },
        ERA_POST_STEROID: {
            'command': 7.45,
            'outs': 4.1,
            'so': 1.60,
            'bb': 4.40,
            '1b': 6.60,
            '1b+': 0.70,
            '2b': 2.00,
            '3b': 0.2,
            'hr': 2.0,
        },
        ERA_STATCAST: {
            'command': 7.3,
            'outs': 4.0,
            'so': 2.00,
            'bb': 4.45,
            '1b': 6.70,
            '1b+': 0.70,
            '2b': 1.95,
            '3b': 0.2,
            'hr': 2.0,
        },
        ERA_PITCH_CLOCK: {
            'command': 7.45,
            'outs': 4.0,
            'so': 2.00,
            'bb': 4.45,
            '1b': 6.55,
            '1b+': 0.75,
            '2b': 2.05,
            '3b': 0.2,
            'hr': 2.0,
        },
    },
    EXPANDED_SET: {
        ERA_PRE_1900: {
            'command': 9.5,
            'outs': 7.4,
            'so': 3.0,
            'bb': 3.3,
            '1b': 6.0,
            '1b+': 0.12,
            '2b': 1.3,
            '3b': 0.19,
            'hr': 1.4,
        },
        ERA_DEAD_BALL: {
            'command': 9.7,
            'outs': 7.0,
            'so': 0.50,
            'bb': 3.50,
            '1b': 5.75,
            '1b+': 0.80,
            '2b': 1.60,
            '3b': 0.75,
            'hr': 0.60,
        },
        ERA_LIVE_BALL: {
            'command': 9.85,
            'outs': 6.50,
            'so': 1.00,
            'bb': 3.50,
            '1b': 6.20,
            '1b+': 0.75,
            '2b': 1.50,
            '3b': 0.10,
            'hr': 1.45,
        },
        ERA_INTEGRATION: {
            'command': 9.5,
            'outs': 6.65,
            'so': 1.00,
            'bb': 3.45,
            '1b': 6.10,
            '1b+': 0.70,
            '2b': 1.45,
            '3b': 0.10,
            'hr': 1.55,
        },
        ERA_EXPANSION: {
            'command': 9.5,
            'outs': 6.9,
            'so': 1.30,
            'bb': 3.45,
            '1b': 6.05,
            '1b+': 0.70,
            '2b': 1.30,
            '3b': 0.10,
            'hr': 1.50,
        },
        ERA_FREE_AGENCY: {
            'command': 9.50,
            'outs': 7.15,
            'so': 2.50,
            'bb': 3.30,
            '1b': 5.98,
            '1b+': 0.50,
            '2b': 1.35,
            '3b': 0.12,
            'hr': 1.60,
        },
        ERA_STEROID: {
            'command': 9.5,
            'outs': 7.4,
            'so': 3.0,
            'bb': 3.3,
            '1b': 6.0,
            '1b+': 0.12,
            '2b': 1.3,
            '3b': 0.19,
            'hr': 1.4,
        },
        ERA_POST_STEROID: {
            'command': 9.35,
            'outs': 7.0,
            'so': 2.50,
            'bb': 3.30,
            '1b': 6.00,
            '1b+': 0.40,
            '2b': 1.35,
            '3b': 0.10,
            'hr': 1.65,
        },
        ERA_STATCAST: {
            'command': 9.2,
            'outs': 7.1,
            'so': 3.0,
            'bb': 3.35,
            '1b': 6.05,
            '1b+': 0.40,
            '2b': 1.30,
            '3b': 0.15,
            'hr': 1.65,
        },
        ERA_PITCH_CLOCK: {
            'command': 9.35,
            'outs': 7.0,
            'so': 3.0,
            'bb': 3.30,
            '1b': 6.00,
            '1b+': 0.40,
            '2b': 1.40,
            '3b': 0.15,
            'hr': 1.65,
        },
    },
}

"""
COMMAND COMBINATIONS
  - ONBASE/CONTROL AND OUT COMBINATIONS ALLOWED IN EACH SET
"""
OB_COMBOS = {
    '2000':[
        [4,5],
        [5,2],[5,3],[5,4],[5,5],
        [6,2],[6,3],[6,4],[6,5],
        [7,2],[7,3],[7,4],[7,5],
        [8,2],[8,3],[8,4],[8,5],
        [9,2],[9,3],[9,4],[9,5],
        [10,2],[10,3],[10,4],[10,5],
        [11,2],[11,3],
        [12,0],[12,2],[12,3]
    ],
    '2001':[
        [4,5],[4,6],
        [5,2],[5,3],[5,4],[5,5],[5,6],
        [6,2],[6,3],[6,4],[6,5],[6,6],
        [7,2],[7,3],[7,4],[7,5],[7,6],
        [8,2],[8,3],[8,4],[8,5],
        [9,2],[9,3],[9,4],[9,5],
        [10,2],[10,3],[10,4],
        [11,2],[11,3],
        [12,0],[12,2],[12,3]
    ],
    '2002':[
        [7,5],[7,6],[7,7],
        [8,5],[8,6],[8,7],[8,8],
        [9,5],[9,6],[9,7],
        [10,5],[10,6],[10,7],
        [11,5],[11,6],[11,7],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],[14,7],
        [15,6],[15,7],
        [16,3],[16,4],[16,5],[16,6],
    ],
    '2003':[
        [7,8],[7,10],
        [8,5],[8,6],[8,7],[8,8],[8,9],
        [9,5],[9,6],[9,7],[9,8],
        [10,5],[10,6],[10,7],
        [11,5],[11,6],[11,7],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,0],[14,2],[14,3],[14,5],[14,6],[14,7],
        [15,6],[15,7],
        [16,3],[16,4],[16,5],[16,6]
    ],
    '2004':[
        [7,8],[7,9],[7,10],[7,11],
        [8,7],[8,8],[8,9],[8,10],[8,11],
        [9,5],[9,6],[9,7],[9,8],[9,9],[9,10],[9,11],
        [10,5],[10,6],[10,7],[10,8],
        [11,5],[11,6],[11,7],[11,8],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],[14,7],
        [15,6],[15,7],
        [16,3],[16,4],[16,5],[16,6]
    ],
    '2005':[
        [7,8],[7,9],[7,10],[7,11],
        [8,7],[8,8],[8,9],[8,10],[8,11],
        [9,5],[9,6],[9,7],[9,8],[9,9],[9,10],[9,11],
        [10,5],[10,6],[10,7],[10,8],
        [11,5],[11,6],[11,7],[11,8],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],[14,7],
        [15,6],[15,7],
        [16,3],[16,4],[16,5],[16,6],
    ],
    CLASSIC_SET: [
        [4,5],[4,6],
        [5,2],[5,3],[5,4],[5,5],[5,6],
        [6,2],[6,3],[6,4],[6,5],[6,6],
        [7,3],[7,4],[7,5],[7,6],
        [8,3],[8,4],[8,5],[8,6],
        [9,3],[9,4],[9,5],[9,6],
        [10,2],[10,3],[10,4],[10,5],
        [11,2],[11,3],[11,4],[11,5],
        [12,0],[12,2],[12,3],[12,4],
    ],
    EXPANDED_SET: [
        [7,7],[7,8],[7,9],
        [8,5],[8,6],[8,7],[8,8],[8,9],[8,10],[8,11],
        [9,5],[9,6],[9,7],[9,8],[9,9],[9,10],[9,11],
        [10,5],[10,6],[10,7],[10,8],
        [11,5],[11,6],[11,7],[11,8],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],[14,7],
        [15,6],[15,7],[15,8],
        [16,3],[16,4],[16,5],[16,6],
    ],

}
CONTROL_COMBOS = {
    '2000':[
        [0,16],[0,17],[0,18],
        [2,15],[2,16],[2,18],
        [3,15],[3,16],[3,17],[3,18],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,15],[5,16],[5,17],[5,18],[5,19],
        [6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    '2001':[
        [0,17],[0,18],
        [1,17],[1,18],
        [2,16],[2,17],[2,18],
        [3,14],[3,15],[3,16],[3,17],[3,18],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,14],[5,15],[5,16],[5,17],[5,18],[5,19],
        [6,14],[6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    '2002':[
        [1,15],[1,16],[1,17],[1,18],
        [2,15],[2,16],[2,17],[2,18],[2,19],
        [3,15],[3,16],[3,17],[3,18],[3,19],
        [4,14],[4,15],[4,16],[4,17],[4,18],[4,19],
        [5,15],[5,16],[5,17],[5,18],
        [6,16],[6,17],[6,18],[6,20],
    ],
    '2003':[
        [1,15],[1,16],[1,18],
        [2,14],[2,15],[2,16],[2,18],
        [3,14],[3,15],[3,16],[3,17],[3,18],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,15],[5,16],[5,17],[5,18],
        [6,16],[6,17],[6,18],[6,20],
    ],
    '2004':[
        [1,13],[1,14],[1,15],[1,16],[1,18],[1,19],
        [2,14],[2,15],[2,16],[2,18],[2,19],
        [3,15],[3,16],[3,17],[3,18],[3,19],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,12],[5,14],[5,15],[5,16],[5,17],[5,18],[5,19],
        [6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    '2005':[
        [1,13],[1,14],[1,15],[1,16],[1,18],[1,19],
        [2,14],[2,15],[2,16],[2,18],[2,19],
        [3,15],[3,16],[3,17],[3,18],[3,19],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,12],[5,14],[5,15],[5,16],[5,17],[5,18],[5,19],
        [6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    CLASSIC_SET: [
        [0,17],[0,18],
        [1,17],[1,18],
        [1,16],[2,16],[2,17],[2,18],
        [3,14],[3,15],[3,16],[3,17],[3,18],[3,19],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,14],[5,15],[5,16],[5,17],[5,18],[5,19],
        [6,14],[6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    EXPANDED_SET: [
        [1,14],[1,15],[1,16],[1,17],[1,18],[1,19],
        [2,15],[2,16],[2,17],[2,18],[2,19],
        [3,15],[3,16],[3,17],[3,18],[3,19],
        [4,15],[4,16],[4,17],[4,18],[4,19],
        [5,14],[5,15],[5,16],[5,17],[5,18],[5,19],
        [6,14],[6,15],[6,16],[6,17],[6,18],[6,20],
    ],
}

COMMAND_ACCURACY_WEIGHTING = {
    '2000': {
        '7-2': 0.999,
        '8-2': 0.999,
        '9-2': 0.999,
        
        '2-18': 0.97,
    },
    '2001': {
        '7-2': 0.999,
        '8-2': 0.999,
        '9-2': 0.999,

        '1-18': 0.975,
        '2-18': 0.97,
        '3-18': 0.98,
        '4-18': 0.98,
    },
    '2002': {},
    '2003': {
        '1-18': 0.99,
        '2-18': 0.98,
        '3-17': 0.99,
        '3-18': 0.99,
        '4-18': 0.98,
    },
    '2004': {
        '1-18': 0.98,
        '1-19': 0.97,
        '2-18': 0.985,
        '2-19': 0.975,
        '3-17': 0.99,
        '3-18': 0.99,
        '3-19': 0.965,
        '4-15': 0.99,
        '4-18': 0.98,

        '10-8': 0.985,
        '11-8': 0.99,
    },
    '2005': {
        '1-18': 0.99,
        '1-19': 0.97,
        '2-18': 0.985,
        '2-19': 0.975,
        '3-17': 0.99,
        '3-18': 0.99,
        '3-19': 0.965,
        '4-15': 0.99,
        '4-18': 0.98,

        '10-8': 0.985,
        '11-8': 0.99,
    },
    CLASSIC_SET: {
        '3-19': 0.99,
        '2-18': 0.99,
        '1-18': 0.99,
    },
    EXPANDED_SET: {
        '3-19': 0.98,
        '3-18': 0.99,
        '2-18': 0.993,
        '1-18': 0.99,
        '2-19': 0.98,
        '1-19': 0.99,
    },
}

"""
MAX HITTER SO
  - MAXIMUM AMOUNT OF SO RESULTS FOR HITTERS IN EACH SET
  - REPRESENTS A "SOFT" CAP, OUTLIERS CAN STILL BE ABOVE THIS NUMBER
"""
HITTER_SO_RESULTS_SOFT_CAP = {
    '2000': 3,
    '2001': 3,
    '2002': 4,
    '2003': 3,
    '2004': 3,
    '2005': 3,
    CLASSIC_SET: 3,
    EXPANDED_SET: 3,
}

HITTER_SO_RESULTS_HARD_CAP = {
    '2000': 5,
    '2001': 6,
    '2002': 7,
    '2003': 6,
    '2004': 6,
    '2005': 6,
    CLASSIC_SET: 6,
    EXPANDED_SET: 6,
}

"""
HITTER SINGLE PLUS DENOMINATOR RANGE
  - DEFINES RANGE FOR 1B+ SCALER (SB-400PA / DENOMINATOR). 
    MIN IS APPLIED TO LOWEST OB, MAX IS APPLIED TO HIGHEST OB
"""
HITTER_SINGLE_PLUS_DENOMINATOR_RANGE = {
    '2000': {
        'min': 3.2,
        'max': 9.6
    },
    '2001': {
        'min': 3.2,
        'max': 9.6
    },
    '2002': {
        'min': 7.0,
        'max': 11.0
    },
    '2003': {
        'min': 6.0,
        'max': 10.5
    },
    '2004': {
        'min': 5.5,
        'max': 10.5
    },
    '2005': {
        'min': 5.5,
        'max': 9.75
    },
    CLASSIC_SET: {
        'min': 3.2,
        'max': 9.6
    },
    EXPANDED_SET: {
        'min': 5.5,
        'max': 9.75
    },
}

"""
CHART CATEGORY WEIGHTS
  - VALUE GIVEN TO EACH CATEGORY APPLIED TO DECISION MAKING FOR WHICH CHART IS MOST ACCURATE
"""
CHART_CATEGORY_WEIGHTS = {
    '2000': {
        'position_player': {
            'onbase_perc': 3.0,
            'slugging_perc': 1.0,
        },
        'starting_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        },
        'relief_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        }
    },
    '2001': {
        'position_player': {
            'onbase_perc': 3.0,
            'slugging_perc': 1.0,
        },
        'starting_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        },
        'relief_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        }
    },
    '2002': {
        'position_player': {
            'onbase_perc': 1.0,
        },
        'starting_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        },
        'relief_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        }
    },
    '2003': {
        'position_player': {
            'onbase_perc': 1.0,
        },
        'starting_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 3.0,
        },
        'relief_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 3.0,
        }
    },
    '2004': {
        'position_player': {
            'slugging_perc': 1.0,
            'onbase_perc': 4.0,
        },
        'starting_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 3.0,
        },
        'relief_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 3.0,
        }
    },
    '2005': {
        'position_player': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.5,
        },
        'starting_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 3.0,
        },
        'relief_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 3.0,
        }
    },
    CLASSIC_SET: {
        'position_player': {
            'onbase_perc': 1.5,
            'slugging_perc': 1.0,
        },
        'starting_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        },
        'relief_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        }
    },
    EXPANDED_SET: {
        'position_player': {
            'onbase_perc': 1.5,
            'slugging_perc': 1.0,
        },
        'starting_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        },
        'relief_pitcher': {
            'slugging_perc': 1.0,
            'onbase_perc': 2.0,
        }
    },
}

"""
POINT WEIGHTS
  - POINT VALUE GIVEN TO A PLAYER IN THE 100TH PERCENTILE FOR A CATEGORY
"""
POINT_GB_MIN_MAX = {
    'min': 0.3,
    'max': 0.5,
}
POINT_CATEGORY_WEIGHTS = {
    '2000': {
        'position_player': {
            'defense': 75,
            'speed': 75,
            'onbase': 200,
            'average': 40,
            'slugging': 165,
            'home_runs': 35
        },
        'starting_pitcher': {
            'ip': 105,
            'onbase': 485,
            'average': 55,
            'slugging': 210,
            'out_distribution': 30,
        },
        'relief_pitcher': {
            'ip': 0, # IP IS ADJUSTED ELSEWHERE
            'onbase': 110,
            'average': 20,
            'slugging': 90,
            'out_distribution': 20,
        }
    },
    '2001': {
        'position_player': {
            'defense': 65,
            'speed': 60,
            'onbase': 190,
            'average': 50,
            'slugging': 165,
            'home_runs': 45
        },
        'starting_pitcher': {
            'ip': 115,
            'onbase': 470,
            'average': 35,
            'slugging': 255,
            'out_distribution': 30,
        },
        'relief_pitcher': {
            'ip': 0, # IP IS ADJUSTED ELSEWHERE
            'onbase': 174,
            'average': 25,
            'slugging': 112,
            'out_distribution': 20,
        }
    },
    '2002': {
        'position_player': {
            'defense': 70,
            'speed': 65,
            'onbase': 170,
            'average': 40,
            'slugging': 160,
            'home_runs': 40
        },
        'starting_pitcher': {
            'ip': 100,
            'onbase': 330,
            'average': 45,
            'slugging': 280,
            'out_distribution': 20,
        },
        'relief_pitcher': {
            'ip': 0, # IP IS ADJUSTED ELSEWHERE
            'onbase': 100,
            'average': 20,
            'slugging': 85,
            'out_distribution': 10,
        }
    },
    '2003': {
        'position_player': {
            'defense': 60,
            'speed': 55,
            'onbase': 160,
            'average': 50,
            'slugging': 160,
            'home_runs': 60
        },
        'starting_pitcher': {
            'ip': 70,
            'onbase': 280,
            'average': 60,
            'slugging': 270,
            'out_distribution': 20,
        },
        'relief_pitcher': {
            'ip': 0, # IP IS ADJUSTED ELSEWHERE
            'onbase': 135,
            'average': 20,
            'slugging': 110,
            'out_distribution': 10,
        }
    },
    '2004': {
        'position_player': {
            'defense': 65,
            'speed': 60,
            'onbase': 155,
            'average': 60,
            'slugging': 150,
            'home_runs': 45
        },
        'starting_pitcher': {
            'ip': 70,
            'onbase': 295,
            'average': 50,
            'slugging': 150,
            'out_distribution': 30,
        },
        'relief_pitcher': {
            'ip': 0, # IP IS ADJUSTED ELSEWHERE
            'onbase': 115,
            'average': 20,
            'slugging': 105,
            'out_distribution': 20,
        }
    },
    '2005': {
        'position_player': {
            'defense': 65,
            'speed': 60,
            'onbase': 140,
            'average': 70,
            'slugging': 140,
            'home_runs': 50
        },
        'starting_pitcher': {
            'ip': 75,
            'onbase': 305,
            'average': 60,
            'slugging': 190,
            'out_distribution': 30,
        },
        'relief_pitcher': {
            'ip': 0, # IP IS ADJUSTED ELSEWHERE
            'onbase': 115,
            'average': 20,
            'slugging': 107,
            'out_distribution': 20,
        }
    },
    CLASSIC_SET: {
        'position_player': {
            'defense': 65,
            'speed': 75,
            'onbase': 220,
            'average': 70,
            'slugging': 180,
            'home_runs': 50
        },
        'starting_pitcher': {
            'ip': 110,
            'onbase': 425,
            'average': 35,
            'slugging': 230,
            'out_distribution': 30,
        },
        'relief_pitcher': {
            'ip': 0, # IP IS ADJUSTED ELSEWHERE
            'onbase': 150,
            'average': 25,
            'slugging': 100,
            'out_distribution': 20,
        }
    },
    EXPANDED_SET: {
        'position_player': {
            'defense': 65,
            'speed': 60,
            'onbase': 150,
            'average': 70,
            'slugging': 150,
            'home_runs': 50
        },
        'starting_pitcher': {
            'ip': 75,
            'onbase': 305,
            'average': 60,
            'slugging': 180,
            'out_distribution': 20,
        },
        'relief_pitcher': {
            'ip': 0, # IP IS ADJUSTED ELSEWHERE
            'onbase': 105,
            'average': 20,
            'slugging': 105,
            'out_distribution': 10,
        }
    },
}

"""
DEFENSIVE POINT MULTIPLIERS
  - MULTIPLY DEFENSIVE POINT TOTALS FOR GIVEN POSITION BY A SCALER
"""
POINTS_POSITIONAL_DEFENSE_MULTIPLIER = {
    '2000': {
        'C': 1.0,
        '1B': 0.25,
        '2B': 1.0,
        '3B': 1.0,
        'SS': 0.80, # SURPRISING, BUT ACCORDING TO WOTC TESTS ITS RIGHT
        'CF': 1.0,
        'OF': 0.89,
        'LF/RF': 0.75,
        'IF': 1.0,
    },
    '2001': {
        'C': 1.3,
        '1B': 0.5,
        '2B': 1.3,
        '3B': 1.0,
        'SS': 1.3,
        'CF': 1.1,
        'OF': 1.0,
        'LF/RF': 0.65,
        'IF': 1.0,
    },
    '2002': {
        'CA': 1.0,
        '1B': 0.5,
        '2B': 1.0,
        '3B': 1.0,
        'SS': 1.1,
        'CF': 1.0,
        'OF': 1.0,
        'LF/RF': 0.75,
        'IF': 1.0,
    },
    '2003': {
        'CA': 1.0,
        '1B': 0.5,
        '2B': 1.0,
        '3B': 1.0,
        'SS': 1.25,
        'CF': 1.0,
        'OF': 1.0,
        'LF/RF': 0.75,
        'IF': 1.0,
    },
    '2004': {
        'CA': 1.0,
        '1B': 0.5,
        '2B': 1.0,
        '3B': 1.0,
        'SS': 1.0,
        'CF': 1.0,
        'OF': 1.0,
        'LF/RF': 1.0,
        'IF': 1.0,
    },
    '2005': {
        'CA': 1.0,
        '1B': 0.5,
        '2B': 1.0,
        '3B': 1.0,
        'SS': 1.0,
        'CF': 1.0,
        'OF': 1.0,
        'LF/RF': 1.0,
        'IF': 1.0,
    },
    CLASSIC_SET: {
        'CA': 1.4,
        '1B': 0.5,
        '2B': 1.0,
        '3B': 1.0,
        'SS': 1.0,
        'CF': 1.0,
        'OF': 1.0,
        'LF/RF': 1.0,
        'IF': 1.0,
    },
    EXPANDED_SET: {
        'CA': 1.4,
        '1B': 0.5,
        '2B': 1.0,
        '3B': 1.0,
        'SS': 1.0,
        'CF': 1.0,
        'OF': 1.0,
        'LF/RF': 1.0,
        'IF': 1.0,
    },
}

"""
COMMAND OUT POINT MULTIPLIERS
  - MULTIPLY POINT TOTALS FOR GIVEN ONBASE/CONTROL - OUTS COMBINATION BY A SCALER
"""
POINTS_COMMAND_OUT_MULTIPLIER = {
    '2000': {
        '10-5': 1.15,
        '10-4': 1.08,
        '10-2': 0.95,
        '9-5': 1.08,
        '8-5': 1.06,
        '8-3': 0.90,
        '7-3': 0.90,

        '5-17': 0.97,
        '4-14': 1.1,
        '4-15': 1.06,
        '4-16': 0.98,
        '4-17': 0.925,
        '3-18': 0.90,
        '3-17': 0.97,
        '3-16': 0.97,
        '3-15': 1.1,
        '2-18': 0.92,
        
    },
    '2001': {
        '10-4': 1.05,
        '10-2': 0.96,
        '9-5': 1.05,
        '9-3': 0.925,
        '8-4': 0.925,
        '8-3': 0.90,
        '7-4': 0.90,
        '7-3': 0.90,

        '1-18': 0.90,
        '2-17': 0.92,
        '2-18': 0.92,
        '3-17': 0.85,
        '3-18': 0.92,
        '4-14': 1.15,
        '4-15': 1.15,
        '4-18': 0.95,
        '5-14': 1.25,
        '6-14': 1.05,
        '6-15': 1.05,
        '5-17': 0.99,
    },
    '2002': {
        '10-7': 0.85,

        '3-16': 1.25,
    },
    '2003': {
        '10-5': 1.12,

        '4-16': 0.94,
        '3-15': 1.3,
        '2-16': 1.25
    },
    '2004': {
        '9-6': 0.85,
        '9-7': 0.85,

        '6-16': 1.15,
        '3-17': 0.90,
        '4-17': 0.95,
        '2-18': 0.80,
        '3-18': 0.90,
        '1-19': 0.90,
        '2-19': 0.90,
        '3-19': 0.90,
    },
    '2005': {
        '9-5': 1.15,
        '9-6': 1.1,
        '9-7': 0.95,

        '2-18': 0.85,
        '3-15': 1.25,
        '3-16': 1.05,
        '3-17': 0.8,
        '3-18': 0.9,
        '4-17': 0.8,
        '5-17': 0.95,
        '6-16': 1.10,
        '6-17': 1.03,
        '1-19': 0.90,
        '2-19': 0.90,
        '3-19': 0.90,
    },
    CLASSIC_SET: {
        '10-4': 1.05,
        '10-2': 0.96,
        '9-5': 1.05,
        '9-3': 0.925,
        '8-4': 0.925,
        '8-3': 0.90,
        '7-4': 0.90,
        '7-3': 0.90,

        '1-18': 0.90,
        '2-17': 0.92,
        '2-18': 0.95,
        '3-17': 0.85,
        '3-18': 0.95,
        '4-14': 1.15,
        '4-15': 1.15,
        '5-14': 1.15,
        '6-14': 1.05,
        '6-15': 1.05,
    },
    EXPANDED_SET: {
        '9-5': 1.15,
        '9-6': 1.1,
        '9-7': 0.95,

        '1-18': 0.90,
        '2-18': 0.90,
        '3-17': 0.90,
        '3-18': 0.90,
        '4-17': 0.90,
        '1-19': 0.90,
        '2-19': 0.90,
        '3-19': 0.90,
    },
}


"""
POINTS_ALLOW_NEGATIVE
  - BOOLEAN FOR WHETHER THE SET PENALIZES BAD CATEGORIES BY GIVING NEGATIVE POINTS
"""
POINTS_ALLOW_NEGATIVE = {
    '2000': {
        'position_player': False,
        'starting_pitcher': False,
        'relief_pitcher': False,
    },
    '2001': {
        'position_player': True,
        'starting_pitcher': False,
        'relief_pitcher': False,
    },
    '2002': {
        'position_player': False,
        'starting_pitcher': False,
        'relief_pitcher': True,
    },
    '2003': {
        'position_player': True,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    '2004': {
        'position_player': True,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    '2005': {
        'position_player': True,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    CLASSIC_SET: {
        'position_player': True,
        'starting_pitcher': False,
        'relief_pitcher': False,
    },
    EXPANDED_SET: {
        'position_player': True,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
}

"""
POINTS_NORMALIZE_TOWARDS_MEDIAN
  - BOOLEAN FOR WHETHER THE SET NORMALIZES UPPER TEAR CARDS TOWARDS THE MEDIAN
"""
POINTS_NORMALIZE_TOWARDS_MEDIAN = {
    '2000': {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    '2001': {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    '2002': {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': False,
    },
    '2003': {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    '2004': {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    '2005': {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    CLASSIC_SET: {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    EXPANDED_SET: {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
}

"""
POINTS NORMALIZER MULTIPLIER
  - WHAT PCT TO MULTIPLY BY POINT VALUE FOR HIGHEST TIER PLAYERS (AT 800/400 PTS)
"""
POINTS_NORMALIZER_MULTIPLIER = {
    '2000': {
        'position_player': 0.70,
        'starting_pitcher': 0.75,
        'relief_pitcher': 0.55,
    },
    '2001': {
        'position_player': 0.65,
        'starting_pitcher': 0.70,
        'relief_pitcher': 0.72,
    },
    '2002': {
        'position_player': 0.85,
        'starting_pitcher': 0.85,
        'relief_pitcher': 0.85,
    },
    '2003': {
        'position_player': 0.85,
        'starting_pitcher': 0.72,
        'relief_pitcher': 0.70,
    },
    '2004': {
        'position_player': 0.65,
        'starting_pitcher': 0.80,
        'relief_pitcher': 0.675,
    },
    '2005': {
        'position_player': 0.65,
        'starting_pitcher': 0.78,
        'relief_pitcher': 0.74,
    },
    CLASSIC_SET: {
        'position_player': 0.65,
        'starting_pitcher': 0.70,
        'relief_pitcher': 0.72,
    },
    EXPANDED_SET: {
        'position_player': 0.65,
        'starting_pitcher': 0.80,
        'relief_pitcher': 0.77,
    },
}

"""
POINTS_NORMALIZER_RELIEVER_MULTIPLIER
  - WHAT TO MULTIPLY MEDIAN FOR POSITION PLAYER / STARTERS BY
"""
POINTS_NORMALIZER_RELIEVER_MULTIPLIER = {
    '2000': 2.0,
    '2001': 1.5,
    '2002': 2.0,
    '2003': 2.0,
    '2004': 2.0,
    '2005': 2.0,
    CLASSIC_SET: 1.5,
    EXPANDED_SET: 2.0,
}

"""
POINTS_RELIEVER_IP_MULTIPLIER
  - WHAT PERCENT OF POINTS TO GIVE FOR 2ND/3RD INNING OF RELIEF
"""
POINTS_RELIEVER_IP_MULTIPLIER = {
    '2000': {
        '2': 1.90,
        '3': 2.55,
    },
    '2001': {
        '2': 1.60,
        '3': 2.10,
    },
    '2002': {
        '2': 1.20,
        '3': 1.80,
    },
    '2003': {
        '2': 1.10,
        '3': 1.65,
    },
    '2004': {
        '2': 1.34,
        '3': 2.01,
    },
    '2005': {
        '2': 1.34,
        '3': 2.01,
    },
    CLASSIC_SET: {
        '2': 1.60,
        '3': 2.10,
    },
    EXPANDED_SET: {
        '2': 1.40,
        '3': 2.01,
    },
}


"""
POINT CATEGORY RANGES
  - MIN AND MAX VALUES FOR EACH CATEGORY USED TO PRODUCE POINT VALUE.
  - USED TO CALCULATE A PLAYER'S PERCENTILE IN THAT CATEGORY.
"""
ONBASE_PCT_RANGE = {
    '2000': {
        'starting_pitcher': {
            'min': 0.250,
            'max': 0.390
        },
        'relief_pitcher': {
            'min': 0.240,
            'max': 0.400
        },
        'position_player': {
            'min': 0.270,
            'max': 0.430
        }
    },
    '2001': {
        'starting_pitcher': {
            'min': 0.240,
            'max': 0.400
        },
        'relief_pitcher': {
            'min': 0.240,
            'max': 0.360
        },
        'position_player': {
            'min': 0.290,
            'max': 0.450
        }
    },
    '2002': {
        'starting_pitcher': {
            'min': 0.250,
            'max': 0.360
        },
        'relief_pitcher': {
            'min': 0.250,
            'max': 0.360
        },
        'position_player': {
            'min': 0.260,
            'max': 0.450
        }
    },
    '2003': {
        'starting_pitcher': {
            'min': 0.250,
            'max': 0.390
        },
        'relief_pitcher': {
            'min': 0.240,
            'max': 0.400
        },
        'position_player': {
            'min': 0.270,
            'max': 0.425
        }
    },
    '2004': {
        'starting_pitcher': {
            'min': 0.250,
            'max': 0.370
        },
        'relief_pitcher': {
            'min': 0.240,
            'max': 0.400
        },
        'position_player': {
            'min': 0.300,
            'max': 0.415
        }
    },
    '2005': {
        'starting_pitcher': {
            'min': 0.223,
            'max': 0.370
        },
        'relief_pitcher': {
            'min': 0.240,
            'max': 0.390
        },
        'position_player': {
            'min': 0.310,
            'max': 0.410
        }
    },
    CLASSIC_SET: {
        'starting_pitcher': {
            'min': 0.240,
            'max': 0.400
        },
        'relief_pitcher': {
            'min': 0.240,
            'max': 0.360
        },
        'position_player': {
            'min': 0.290,
            'max': 0.450
        }
    },
    EXPANDED_SET: {
        'starting_pitcher': {
            'min': 0.223,
            'max': 0.370
        },
        'relief_pitcher': {
            'min': 0.240,
            'max': 0.390
        },
        'position_player': {
            'min': 0.310,
            'max': 0.410
        }
    },
}
BATTING_AVG_RANGE = {
    '2000': {
        'starting_pitcher': {
            'min': 0.210,
            'max': 0.300
        },
        'relief_pitcher': {
            'min': 0.210,
            'max': 0.300
        },
        'position_player': {
            'min': 0.225,
            'max': 0.330
        }
    },
    '2001': {
        'starting_pitcher': {
            'min': 0.210,
            'max': 0.300
        },
        'relief_pitcher': {
            'min': 0.210,
            'max': 0.300
        },
        'position_player': {
            'min': 0.225,
            'max': 0.330
        }
    },
    '2002': {
        'starting_pitcher': {
            'min': 0.210,
            'max': 0.290
        },
        'relief_pitcher': {
            'min': 0.210,
            'max': 0.290
        },
        'position_player': {
            'min': 0.225,
            'max': 0.330
        }
    },
    '2003': {
        'starting_pitcher': {
            'min': 0.210,
            'max': 0.290
        },
        'relief_pitcher': {
            'min': 0.210,
            'max': 0.290
        },
        'position_player': {
            'min': 0.245,
            'max': 0.320
        }
    },
    '2004': {
        'starting_pitcher': {
            'min': 0.210,
            'max': 0.280
        },
        'relief_pitcher': {
            'min': 0.210,
            'max': 0.280
        },
        'position_player': {
            'min': 0.245,
            'max': 0.315
        }
    },
    '2005': {
        'starting_pitcher': {
            'min': 0.210,
            'max': 0.280
        },
        'relief_pitcher': {
            'min': 0.210,
            'max': 0.280
        },
        'position_player': {
            'min': 0.245,
            'max': 0.330
        }
    },
    CLASSIC_SET: {
        'starting_pitcher': {
            'min': 0.210,
            'max': 0.300
        },
        'relief_pitcher': {
            'min': 0.210,
            'max': 0.300
        },
        'position_player': {
            'min': 0.225,
            'max': 0.330
        }
    },
    EXPANDED_SET: {
        'starting_pitcher': {
            'min': 0.210,
            'max': 0.280
        },
        'relief_pitcher': {
            'min': 0.210,
            'max': 0.280
        },
        'position_player': {
            'min': 0.245,
            'max': 0.330
        }
    },
}
SLG_RANGE = {
    '2000': {
        'starting_pitcher': {
            'min': 0.350,
            'max': 0.500
        },
        'relief_pitcher': {
            'min': 0.330,
            'max': 0.530
        },
        'position_player': {
            'min': 0.350,
            'max': 0.550
        }
    },
    '2001': {
        'starting_pitcher': {
            'min': 0.340,
            'max': 0.500
        },
        'relief_pitcher': {
            'min': 0.345,
            'max': 0.500
        },
        'position_player': {
            'min': 0.350,
            'max': 0.545
        }
    },
    '2002': {
        'starting_pitcher': {
            'min': 0.340,
            'max': 0.490
        },
        'relief_pitcher': {
            'min': 0.330,
            'max': 0.445
        },
        'position_player': {
            'min': 0.360,
            'max': 0.550
        }
    },
    '2003': {
        'starting_pitcher': {
            'min': 0.350,
            'max': 0.470
        },
        'relief_pitcher': {
            'min': 0.330,
            'max': 0.500
        },
        'position_player': {
            'min': 0.360,
            'max': 0.550
        }
    },
    '2004': {
        'starting_pitcher': {
            'min': 0.340,
            'max': 0.470
        },
        'relief_pitcher': {
            'min': 0.330,
            'max': 0.475
        },
        'position_player': {
            'min': 0.380,
            'max': 0.545
        }
    },
    '2005': {
        'starting_pitcher': {
            'min': 0.335,
            'max': 0.475
        },
        'relief_pitcher': {
            'min': 0.330,
            'max': 0.480
        },
        'position_player': {
            'min': 0.380,
            'max': 0.545
        }
    },
    CLASSIC_SET: {
        'starting_pitcher': {
            'min': 0.340,
            'max': 0.500
        },
        'relief_pitcher': {
            'min': 0.345,
            'max': 0.500
        },
        'position_player': {
            'min': 0.350,
            'max': 0.545
        }
    },
    EXPANDED_SET: {
        'starting_pitcher': {
            'min': 0.335,
            'max': 0.475
        },
        'relief_pitcher': {
            'min': 0.330,
            'max': 0.480
        },
        'position_player': {
            'min': 0.375,
            'max': 0.545
        }
    },
}
SPEED_RANGE = {
    '2000': {
        'min': 10,
        'max': 20
    },
    '2001': {
        'min': 10,
        'max': 20
    },
    '2002': {
        'min': 10,
        'max': 20
    },
    '2003': {
        'min': 10,
        'max': 20
    },
    '2004': {
        'min': 10,
        'max': 20
    },
    '2005': {
        'min': 10,
        'max': 20
    },
    CLASSIC_SET: {
        'min': 10,
        'max': 20
    },
    EXPANDED_SET: {
        'min': 10,
        'max': 20
    },
}
IP_RANGE = {
    'starting_pitcher': {
        'min': 5,
        'max': 8
    },
    'relief_pitcher': {
        'min': 1,
        'max': 2
    }
}
HR_RANGE = {
    '2000': {
        'min': 10,
        'max': 35
    },
    '2001': {
        'min': 10,
        'max': 35
    },
    '2002': {
        'min': 10,
        'max': 35
    },
    '2003': {
        'min': 10,
        'max': 35
    },
    '2004': {
        'min': 10,
        'max': 35
    },
    '2005': {
        'min': 10,
        'max': 35
    },
    CLASSIC_SET: {
        'min': 10,
        'max': 35
    },
    EXPANDED_SET: {
        'min': 10,
        'max': 35
    },
}

"""
DEFENSIVE MAXIMUM
  - MAX VALUE POSSIBLE FOR IN-GAME DEFENSE AT EACH POSITION.
  - GIVEN TO PLAYER IN 100TH PERCENTILE IN THAT POSITION FOR TZR.
"""
POSITION_DEFENSE_RANGE = {
    '2000': {
        'C': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.0,
        'SS': 5.0,
        'LF': 2.0,
        'CF': 3.0,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.0,
        'LF/RF': 2.0,
        'DH': 0
    },
    '2001': {
        'C': 11.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.0,
        'SS': 5.0,
        'LF': 2.0,
        'CF': 3.0,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.0,
        'LF/RF': 2.0,
        'DH': 0
    },
    '2002': {
        'CA': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.0,
        'SS': 5.0,
        'LF': 2.0,
        'CF': 3.0,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.0,
        'LF/RF': 2.0,
        'DH': 0
    },
    '2003': {
        'CA': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.0,
        'SS': 5.0,
        'LF': 2.0,
        'CF': 3.0,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.0,
        'LF/RF': 2.0,
        'DH': 0
    },
    '2004': {
        'CA': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.0,
        'SS': 5.0,
        'LF': 2.0,
        'CF': 3.0,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.0,
        'LF/RF': 2.0,
        'DH': 0
    },
    '2005': {
        'CA': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.0,
        'SS': 5.0,
        'LF': 2.0,
        'CF': 3.0,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.0,
        'LF/RF': 2.0,
        'DH': 0
    },
    CLASSIC_SET: {
        'CA': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.5,
        'SS': 6.0,
        'LF': 2.0,
        'CF': 3.5,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.0,
        'LF/RF': 2.0,
        'DH': 0
    },
    EXPANDED_SET: {
        'CA': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.5,
        'SS': 6.0,
        'LF': 2.0,
        'CF': 3.5,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.0,
        'LF/RF': 2.0,
        'DH': 0
    },
}

"""
PLAYER EXCLUDED WHEN TESTING SET ACCURACY. MOSTLY DUE TO NOT HAVING 
STATS FOR PREVIOUS SEASON.
"""
EXCLUDED_PLAYERS_FOR_TESTING = {
    '2000': [
        'Brian L. Hunter',
        'Craig Wilson',
        'Chan Ho Park',
    ],
    '2001': [
        'Mark L. Johnson',
        'Alex S. Gonzalez',
        'Brian Anderson',
        'Jose Santiago',
        'Chan Ho Park',
    ],
    '2002': [
        'Chan Ho Park',
        'Alex S. Gonzalez',
    ],
    '2003': [

    ],
    '2004': [

    ],
    '2005': [
        'Wily MoPena',
        'Tim Spooneybarger',
        'Runelvys Hernandez',
        'Chan HoPark',
    ],
}

"""
TEST RANGES
  - RANGES TO USE WHEN DISCOVERING PLAYER BASELINES.
"""
TEST_COMMAND_RANGE_HITTER = {
    '2000': {
        'min': 7.5,
        'max': 8.3
    },
    '2001': {
        'min': 7.5,
        'max': 8.3
    },
    '2002': {
        'min': 9.0,
        'max': 10.3
    },
    '2003': {
        'min': 8.0,
        'max': 9.1
    },
    '2004': {
        'min': 8.4,
        'max': 9.5
    },
    '2005': {
        'min': 8.4,
        'max': 9.5
    }
}
TEST_OUT_RANGE_HITTER = {
    '2000': {
        'min': 3.4,
        'max': 4.3
    },
    '2001': {
        'min': 3.4,
        'max': 4.3
    },
    '2002': {
        'min': 5.9,
        'max': 7.1
    },
    '2003': {
        'min': 5.9,
        'max': 7.5
    },
    '2004': {
        'min': 6.0,
        'max': 7.5
    },
    '2005': {
        'min': 5.9,
        'max': 7.5
    }
}
TEST_COMMAND_RANGE_PITCHER = {
    '2000': {
        'min': 3.0,
        'max': 4.0
    },
    '2001': {
        'min': 3.0,
        'max': 3.7
    },
    '2002': {
        'min': 3.0,
        'max': 4.2
    },
    '2003': {
        'min': 3.0,
        'max': 4.5
    },
    '2004': {
        'min': 3.7,
        'max': 4.4
    },
    '2005': {
        'min': 3.8,
        'max': 4.3
    }
}
TEST_OUT_RANGE_PITCHER = {
    '2000': {
        'min': 15.0,
        'max': 16.2
    },
    '2001': {
        'min': 15.5,
        'max': 16.2
    },
    '2002': {
        'min': 15.7,
        'max': 17.2
    },
    '2003': {
        'min': 15.2,
        'max': 16.4
    },
    '2004': {
        'min': 15.0,
        'max': 17.5
    },
    '2005': {
        'min': 15.9,
        'max': 17.1
    }
}

# -------------------------------------------
# CARD IMAGE
# -------------------------------------------

""" COLOR HEX VALUES """
COLOR_WHITE = "#FFFFFF"
COLOR_BLACK = "#000000"
COLOR_RED = "#963219"
COLOR_GRAY = "#e4e3e3"

CONTEXTS_ELIGIBLE_FOR_YEAR_CONTAINER = ['2000', '2001', '2002', '2003']
CONTEXTS_ELIGIBLE_FOR_SET_YEAR_PLUS_ONE = ['2004','2005']

""" COORDINATES FOR IMAGE COMPONENTS """
IMAGE_LOCATIONS = {
    'team_logo': {
        '2000': (1200,1086),
        '2001': (78,1584),
        '2002': (80,1380),
        '2003': (1179,1074),
        '2004': (1161,1425),
        '2005': (1161,1425),
        '2022': (1161,1365),
    },
    'player_name': {
        '2000': (150,-1225),
        '2001': (105,0),
        '2002': (1275,0),
        '2003': (1365,0),
        '2004': (276,1605),
        '2005': (276,1605),
        '2022': (325,1575),
    },
    'player_name_small': {
        '2000': (165,-1225),
        '2001': (105,0),
        '2002': (1285,0),
        '2003': (1375,0),
        '2004': (276,1610),
        '2005': (276,1610),
        '2022': (300,1575),
    },
    'chart': {
        '2000p': (981,1335),
        '2000h': (981,1317),
        '2001p': (981,1335),
        '2001h': (981,1317),
        '2002': (948,1593),
        '2003': (981,1518),
        '2004': (0,1779),
        '2005': (0,1779),
        '2022': (40,1885),
    },
    'metadata': {
        '2000': (0,0),
        '2001': (0,0),
        '2002': (810,1605),
        '2003': (825,1530),
        '2004': (282,1710),
        '2005': (282,1710),
        '2022': (330,1670),
    },
    'set': {
        '2000': (129,2016),
        '2001': (129,2016),
        '2002': (60,1860),
        '2003': (93,1785),
        '2004': (1344,1911),
        '2005': (1344,1911),
        '2022': (1200,2020),
    },
    'year_container': {
        '2000': (1250,1865),
        '2001': (1250,1865),
        '2002': (60,2038),
        '2003': (482,1775),
    },
    'number': {
        '2002': (120,1785),
        '2003': (116,1785),
        '2004': (1191,1911),
        '2005': (1191,1911),
        '2022': (1000,2020),
    },
    'super_season': {
        '2000': (1200,900),
        '2001': (78,1584),
        '2002': (45,1113),
        '2003': (1041,786),
        '2004': (1071,1164),
        '2005': (1071,1164),
        '2022': (1071,1275),
    },
    'super_season_year_text': {
        '2000': (24,282),
        '2001': (24,282),
        '2002': (24,282),
        '2003': (24,282),
        '2004': (135,90),
        '2005': (135,90),
        '2022': (133,252),
    },
    'rookie_season': {
        '2000': (1200,1086),
        '2001': (1108,1040),
        '2002': (80,1360),
        '2003': (1085,1025),
        '2004': (1100,1400),
        '2005': (1100,1400),
        '2022': (1075,1340),
    },
    'rookie_season_year_text': {
        '2000': (40, 145),
        '2001': (40, 145),
        '2002': (40, 145),
        '2003': (40, 145),
        '2004': (40, 145),
        '2005': (40, 145),
        '2022': (40, 145),
    },
    'expansion': {
        '2000': (1287,1855),
        '2001': (1287,1855),
        '2002': (652,1770),
        '2003': (275,1782),
        '2004': (1060,1910),
        '2005': (1060,1910),
        '2022': (880,2010),
    },
    'command': {
        '2000': (0,0),
        '2001': (0,0),
        '2002': (0,0),
        '2003': (0,0),
        '2004': (0,0),
        '2005': (0,0),
        '2022': (80,1540),
    },
    'style': {
        '2022': (60,1992),
    },
    'bot_logo': {
        '2000': (1250,1945),
        '2001': (1250,1945),
        '2002': (62,1900),
        '2003': (655,1705),
        '2004': (1268,1965),
        '2005': (1268,1965),
        '2022': (1345,2000),
    },
}

""" LIST OF ICON IMAGE COORDINATES FOR EACH ICON INDEX """
ICON_LOCATIONS = {
    '2003': [(1005,1905), (1005,1830), (930,1905), (930,1830)],
    '2004': [(1050,1695), (1125,1695), (1200,1695), (1275,1695)],
    '2005': [(1050,1695), (1125,1695), (1200,1695), (1275,1695)],
    '2022': [(440,2005), (520,2005), (600,2005), (680,2005)],
}

""" WIDTH AND HEIGHT TUPLES FOR EACH IMAGE COMPONENT """
IMAGE_SIZES = {
    'team_logo': {
        '2000': (225,225),
        '2001': (255,255),
        '2002': (450,450),
        '2003': (270,270),
        '2004': (255,255),
        '2005': (255,255),
        '2022': (275,275),
    },
    'player_name': {
        '2000': (2100, 300),
        '2001': (1545, 300),
        '2002': (1395, 300),
        '2003': (3300, 300),
        '2004': (900, 300),
        '2005': (900, 300),
        '2022': (900, 300),
    },
    'super_season': {
        '2000': (312,480),
        '2001': (312,480),
        '2002': (468,720),
        '2003': (390,600),
        '2004': (339,522),
        '2005': (339,522),
        '2022': (380,380),
    },
    'rookie_season': {
        '2000': (273,273),
        '2001': (300,300),
        '2002': (575,575),
        '2003': (375,375),
        '2004': (339,339),
        '2005': (339,339),
        '2022': (380,380),
    },
    'bot_logo': {
        '2000': (150,150),
        '2001': (150,150),
        '2002': (145,145),
        '2003': (150,150),
        '2004': (130,130),
        '2005': (130,130),
        '2022': (100,100),
    },
}

""" WIDTH AND HEIGHT TUPLES FOR EACH TEXT IMAGE COMPONENT """
TEXT_SIZES = {
    'chart': {
        '2000': 148,
        '2001': 148,
        '2002': 117,
        '2003': 145,
        '2004': 144,
        '2005': 144,
        '2022': 158,
    },
    'chart_spacing': {
        '2000': 31,
        '2001': 31,
        '2002': 25,
        '2003': 26,
        '2004': 75,
        '2005': 75,
        '2022': 75,
    },
}

""" SCALING '00 CUTOUTS FOR DIFFERENT SETS """
CUTOUT_CUSTOM_SCALER = {
    '2000': 1.0,
    '2001': 1.0,
    '2002': 1.25,
    '2003': 1.2,
    '2004': 1.2,
    '2005': 1.2,
    '2022': 1.2,
}
CUTOUT_CUSTOM_COORDINATES = {
    '2000': (0,0),
    '2001': (0,0),
    '2002': (-340,-200),
    '2003': (-315,-350),
    '2004': (-200,-350),
    '2005': (-200,-350),
    '2022': (-200,-350),
}

NATIONALITY_COLORS = {
    'US': [
        (178, 34, 52, 255), # RED
        (60, 59, 110, 255), # BLUE
    ],
    'DO': [
        (206, 17, 38, 255), # RED
        (0, 45, 98, 255), # BLUE
    ],
    'VE': [
        (223, 179, 2, 255), # YELLOW
        (0, 36, 125, 255), # BLUE
        (207, 20, 43, 255), # RED
    ],
    'CU': [
        (0, 42, 143, 255), # BLUE
        (203, 21, 21, 255), # RED        
    ],
    'CA': [
        (234, 6, 25, 255), # RED        
    ],
    'MX': [
        (0, 103, 71, 255), # GREEN
        (205, 17, 39, 255), # RED
    ],
    'PR': [
        (60, 93, 170, 255), # BLUE
        (223, 28, 35, 255), # RED
    ],
    'PA': [
        (7, 35, 87, 255), # BLUE
        (218, 18, 26, 255), # RED
    ],
    'JP': [
        (188, 0, 45, 255), # RED
        (14, 25, 47, 255), # NAVY
    ],
    'GB': [
        (207, 20, 43, 255), # RED
        (0, 36, 125, 255), # NAVY
    ],
    'DE': [
        (0, 0, 0, 255), # BLACK
        (221, 0, 0, 255), # RED
        (255, 206, 0, 255), # YELLOW
    ],
    'AU': [
        (0, 0, 102, 255), # BLUE
        (205, 0, 1, 255), # RED
    ],
    'CO': [
        (202, 166, 17, 255), # YELLOW
        (1, 56, 147, 255), # BLUE
        (205, 17, 39, 255), # RED
    ],
    'KR': [
        (1, 67, 122, 255), # BLUE
        (219, 26, 50, 255), # RED
    ],
    'CW': [
        (1, 42, 126, 255), # BLUE
        (250, 232, 19, 255), # YELLOW
    ],
    'TW': [
        (237, 29, 36, 255), # RED
        (42, 48, 135, 255), # BLUE
    ],
    'NI': [
        (0, 101, 204, 255), # BLUE
    ],
    'NL': [
        (33, 70, 139, 255), # BLUE
        (174, 28, 40, 255), # RED
    ],
    'IT': [
        (0, 146, 71, 255), # GREEN
        (206, 43, 54, 255), # RED
    ],
    'CN': [
        (223, 40, 15, 255), # RED
        (255, 223, 0, 255), # YELLOW
    ],
    'CZ': [
        (215, 20, 26, 255), # RED
        (17, 69, 126, 255), # BLUE
    ],
    'IS': [
        (1, 55, 183, 255), # BLUE
    ],
}

NATIONALITY_TEMPLATE_COLOR = {
    'US': 'RED',
    'DO': 'RED',
    'VE': 'YELLOW',
    'CU': 'BLUE',
    'CA': 'RED',
    'MX': 'GREEN',
    'PR': 'BLUE',
    'PA': 'BLUE',
    'JP': 'RED',
    'GB': 'RED',
    'DE': 'RED',
    'AU': 'BLUE',
    'CO': 'YELLOW',
    'KR': 'BLUE',
    'CW': 'BLUE',
    'TW': 'RED',
    'NI': 'BLUE',
    'NL': 'BLUE',
    'IT': 'GREEN',
    'CN': 'RED',
    'CZ': 'RED',
    'IS': 'BLUE',
}

ALL_STAR_GAME_COLORS = {
    '2023': {
        'NL': (12, 44, 85, 255), # BLUE
        'AL': (2, 112, 113, 255), # GREEN
    },
}

G_DRIVE_PLAYER_IMAGE_FOLDERS = {
    '2000': '1InLYODKI0Fn9ddOLCv8mYPW-tiD29nPN',
    '2001': '1UmKhu_Mluj8Ijki1ruue54tqsqb40Ous',
    '2002': '1aBsjMq5YbcQz4zMZzpA_hKGbSO-nPc_K',
    '2003': '1HZwxyQ2WeZD132UyqfhZ9dXsvv1ab3W2',
    '2004': '1fKrf4wyA9SC7h8_8JhGNdHVhx8Orix5k',
    '2005': '1fKrf4wyA9SC7h8_8JhGNdHVhx8Orix5k',
    '2022': '1dqZjl5nIdyTPs_JXJq6TXBk02ClQMpky',
    'UNIVERSAL': '1htwN6r-9QNHJzg6Jq56dGXuJxD2QNaGv',
}

G_DRIVE_TEAM_BACKGROUND_FOLDERS = {
    '2000': '1PCLjUznKwkfIzcCiHz79J9z6b-jgE0w9',
    '2001': '1JxgfhicVJDNK1PJEiw4zFWa5nqlnx_p5',
}

"""
LEAGUE AVG PROJECTIONS
  - BASED ON 26 MAN ROSTERS PER YEAR
  - USED TO INFORM THE shOPS+ METRIC
"""

COMMAND_ADJUSTMENT_FACTOR_WEIGHT = 0.15

LEAGUE_AVG_PROJ_OBP = {
    "2000": {
        "1900": {
            "Hitter": 0.337,
            "Pitcher": 0.332
        },
        "1901": {
            "Hitter": 0.323,
            "Pitcher": 0.373
        },
        "1902": {
            "Hitter": 0.318,
            "Pitcher": 0.36
        },
        "1903": {
            "Hitter": 0.315,
            "Pitcher": 0.343
        },
        "1904": {
            "Hitter": 0.3,
            "Pitcher": 0.323
        },
        "1905": {
            "Hitter": 0.308,
            "Pitcher": 0.338
        },
        "1906": {
            "Hitter": 0.306,
            "Pitcher": 0.339
        },
        "1907": {
            "Hitter": 0.306,
            "Pitcher": 0.342
        },
        "1908": {
            "Hitter": 0.3,
            "Pitcher": 0.316
        },
        "1909": {
            "Hitter": 0.31,
            "Pitcher": 0.318
        },
        "1910": {
            "Hitter": 0.318,
            "Pitcher": 0.336
        },
        "1911": {
            "Hitter": 0.339,
            "Pitcher": 0.344
        },
        "1912": {
            "Hitter": 0.339,
            "Pitcher": 0.352
        },
        "1913": {
            "Hitter": 0.326,
            "Pitcher": 0.338
        },
        "1914": {
            "Hitter": 0.324,
            "Pitcher": 0.348
        },
        "1915": {
            "Hitter": 0.319,
            "Pitcher": 0.339
        },
        "1916": {
            "Hitter": 0.315,
            "Pitcher": 0.323
        },
        "1917": {
            "Hitter": 0.312,
            "Pitcher": 0.32
        },
        "1918": {
            "Hitter": 0.318,
            "Pitcher": 0.325
        },
        "1919": {
            "Hitter": 0.324,
            "Pitcher": 0.335
        },
        "1920": {
            "Hitter": 0.328,
            "Pitcher": 0.339
        },
        "1921": {
            "Hitter": 0.34,
            "Pitcher": 0.341
        },
        "1922": {
            "Hitter": 0.346,
            "Pitcher": 0.348
        },
        "1923": {
            "Hitter": 0.341,
            "Pitcher": 0.347
        },
        "1924": {
            "Hitter": 0.34,
            "Pitcher": 0.347
        },
        "1925": {
            "Hitter": 0.347,
            "Pitcher": 0.349
        },
        "1926": {
            "Hitter": 0.344,
            "Pitcher": 0.346
        },
        "1927": {
            "Hitter": 0.343,
            "Pitcher": 0.346
        },
        "1928": {
            "Hitter": 0.342,
            "Pitcher": 0.341
        },
        "1929": {
            "Hitter": 0.351,
            "Pitcher": 0.354
        },
        "1930": {
            "Hitter": 0.345,
            "Pitcher": 0.354
        },
        "1931": {
            "Hitter": 0.341,
            "Pitcher": 0.351
        },
        "1932": {
            "Hitter": 0.326,
            "Pitcher": 0.333
        },
        "1933": {
            "Hitter": 0.327,
            "Pitcher": 0.337
        },
        "1934": {
            "Hitter": 0.339,
            "Pitcher": 0.348
        },
        "1935": {
            "Hitter": 0.348,
            "Pitcher": 0.352
        },
        "1936": {
            "Hitter": 0.35,
            "Pitcher": 0.355
        },
        "1937": {
            "Hitter": 0.344,
            "Pitcher": 0.343
        },
        "1938": {
            "Hitter": 0.339,
            "Pitcher": 0.339
        },
        "1939": {
            "Hitter": 0.338,
            "Pitcher": 0.34
        },
        "1940": {
            "Hitter": 0.335,
            "Pitcher": 0.34
        },
        "1941": {
            "Hitter": 0.328,
            "Pitcher": 0.333
        },
        "1942": {
            "Hitter": 0.321,
            "Pitcher": 0.326
        },
        "1943": {
            "Hitter": 0.326,
            "Pitcher": 0.33
        },
        "1944": {
            "Hitter": 0.329,
            "Pitcher": 0.333
        },
        "1945": {
            "Hitter": 0.331,
            "Pitcher": 0.332
        },
        "1946": {
            "Hitter": 0.334,
            "Pitcher": 0.338
        },
        "1947": {
            "Hitter": 0.341,
            "Pitcher": 0.341
        },
        "1948": {
            "Hitter": 0.34,
            "Pitcher": 0.346
        },
        "1949": {
            "Hitter": 0.347,
            "Pitcher": 0.353
        },
        "1950": {
            "Hitter": 0.349,
            "Pitcher": 0.359
        },
        "1951": {
            "Hitter": 0.337,
            "Pitcher": 0.35
        },
        "1952": {
            "Hitter": 0.331,
            "Pitcher": 0.342
        },
        "1953": {
            "Hitter": 0.342,
            "Pitcher": 0.35
        },
        "1954": {
            "Hitter": 0.337,
            "Pitcher": 0.346
        },
        "1955": {
            "Hitter": 0.336,
            "Pitcher": 0.345
        },
        "1956": {
            "Hitter": 0.335,
            "Pitcher": 0.346
        },
        "1957": {
            "Hitter": 0.328,
            "Pitcher": 0.338
        },
        "1958": {
            "Hitter": 0.329,
            "Pitcher": 0.339
        },
        "1959": {
            "Hitter": 0.329,
            "Pitcher": 0.344
        },
        "1960": {
            "Hitter": 0.33,
            "Pitcher": 0.339
        },
        "1961": {
            "Hitter": 0.332,
            "Pitcher": 0.343
        },
        "1962": {
            "Hitter": 0.333,
            "Pitcher": 0.338
        },
        "1963": {
            "Hitter": 0.316,
            "Pitcher": 0.329
        },
        "1964": {
            "Hitter": 0.317,
            "Pitcher": 0.324
        },
        "1965": {
            "Hitter": 0.317,
            "Pitcher": 0.325
        },
        "1966": {
            "Hitter": 0.314,
            "Pitcher": 0.32
        },
        "1967": {
            "Hitter": 0.311,
            "Pitcher": 0.319
        },
        "1968": {
            "Hitter": 0.305,
            "Pitcher": 0.313
        },
        "1969": {
            "Hitter": 0.325,
            "Pitcher": 0.334
        },
        "1970": {
            "Hitter": 0.332,
            "Pitcher": 0.339
        },
        "1971": {
            "Hitter": 0.322,
            "Pitcher": 0.328
        },
        "1972": {
            "Hitter": 0.316,
            "Pitcher": 0.325
        },
        "1973": {
            "Hitter": 0.326,
            "Pitcher": 0.338
        },
        "1974": {
            "Hitter": 0.324,
            "Pitcher": 0.335
        },
        "1975": {
            "Hitter": 0.329,
            "Pitcher": 0.335
        },
        "1976": {
            "Hitter": 0.322,
            "Pitcher": 0.329
        },
        "1977": {
            "Hitter": 0.329,
            "Pitcher": 0.338
        },
        "1978": {
            "Hitter": 0.324,
            "Pitcher": 0.331
        },
        "1979": {
            "Hitter": 0.332,
            "Pitcher": 0.338
        },
        "1980": {
            "Hitter": 0.328,
            "Pitcher": 0.335
        },
        "1981": {
            "Hitter": 0.32,
            "Pitcher": 0.328
        },
        "1982": {
            "Hitter": 0.326,
            "Pitcher": 0.331
        },
        "1983": {
            "Hitter": 0.328,
            "Pitcher": 0.333
        },
        "1984": {
            "Hitter": 0.325,
            "Pitcher": 0.328
        },
        "1985": {
            "Hitter": 0.325,
            "Pitcher": 0.331
        },
        "1986": {
            "Hitter": 0.328,
            "Pitcher": 0.335
        },
        "1987": {
            "Hitter": 0.334,
            "Pitcher": 0.341
        },
        "1988": {
            "Hitter": 0.319,
            "Pitcher": 0.326
        },
        "1989": {
            "Hitter": 0.32,
            "Pitcher": 0.326
        },
        "1990": {
            "Hitter": 0.327,
            "Pitcher": 0.328
        },
        "1991": {
            "Hitter": 0.325,
            "Pitcher": 0.327
        },
        "1992": {
            "Hitter": 0.323,
            "Pitcher": 0.327
        },
        "1993": {
            "Hitter": 0.333,
            "Pitcher": 0.337
        },
        "1994": {
            "Hitter": 0.34,
            "Pitcher": 0.344
        },
        "1995": {
            "Hitter": 0.338,
            "Pitcher": 0.342
        },
        "1996": {
            "Hitter": 0.341,
            "Pitcher": 0.345
        },
        "1997": {
            "Hitter": 0.339,
            "Pitcher": 0.341
        },
        "1998": {
            "Hitter": 0.335,
            "Pitcher": 0.34
        },
        "1999": {
            "Hitter": 0.345,
            "Pitcher": 0.348
        },
        "2000": {
            "Hitter": 0.345,
            "Pitcher": 0.349
        },
        "2001": {
            "Hitter": 0.334,
            "Pitcher": 0.335
        },
        "2002": {
            "Hitter": 0.332,
            "Pitcher": 0.334
        },
        "2003": {
            "Hitter": 0.334,
            "Pitcher": 0.336
        },
        "2004": {
            "Hitter": 0.335,
            "Pitcher": 0.336
        },
        "2005": {
            "Hitter": 0.332,
            "Pitcher": 0.334
        },
        "2006": {
            "Hitter": 0.337,
            "Pitcher": 0.336
        },
        "2007": {
            "Hitter": 0.336,
            "Pitcher": 0.336
        },
        "2008": {
            "Hitter": 0.335,
            "Pitcher": 0.332
        },
        "2009": {
            "Hitter": 0.334,
            "Pitcher": 0.332
        },
        "2010": {
            "Hitter": 0.327,
            "Pitcher": 0.327
        },
        "2011": {
            "Hitter": 0.323,
            "Pitcher": 0.32
        },
        "2012": {
            "Hitter": 0.321,
            "Pitcher": 0.319
        },
        "2013": {
            "Hitter": 0.32,
            "Pitcher": 0.317
        },
        "2014": {
            "Hitter": 0.315,
            "Pitcher": 0.311
        },
        "2015": {
            "Hitter": 0.32,
            "Pitcher": 0.316
        },
        "2016": {
            "Hitter": 0.324,
            "Pitcher": 0.32
        },
        "2017": {
            "Hitter": 0.327,
            "Pitcher": 0.323
        },
        "2018": {
            "Hitter": 0.32,
            "Pitcher": 0.318
        },
        "2019": {
            "Hitter": 0.325,
            "Pitcher": 0.324
        },
        "2020": {
            "Hitter": 0.319,
            "Pitcher": 0.313
        },
        "2021": {
            "Hitter": 0.32,
            "Pitcher": 0.316
        },
        "2022": {
            "Hitter": 0.311,
            "Pitcher": 0.308
        }
    },
    "2001": {
        "1900": {
            "Hitter": 0.336,
            "Pitcher": 0.333
        },
        "1901": {
            "Hitter": 0.321,
            "Pitcher": 0.374
        },
        "1902": {
            "Hitter": 0.317,
            "Pitcher": 0.362
        },
        "1903": {
            "Hitter": 0.314,
            "Pitcher": 0.344
        },
        "1904": {
            "Hitter": 0.298,
            "Pitcher": 0.324
        },
        "1905": {
            "Hitter": 0.307,
            "Pitcher": 0.34
        },
        "1906": {
            "Hitter": 0.305,
            "Pitcher": 0.338
        },
        "1907": {
            "Hitter": 0.305,
            "Pitcher": 0.347
        },
        "1908": {
            "Hitter": 0.298,
            "Pitcher": 0.317
        },
        "1909": {
            "Hitter": 0.309,
            "Pitcher": 0.319
        },
        "1910": {
            "Hitter": 0.317,
            "Pitcher": 0.338
        },
        "1911": {
            "Hitter": 0.337,
            "Pitcher": 0.347
        },
        "1912": {
            "Hitter": 0.339,
            "Pitcher": 0.357
        },
        "1913": {
            "Hitter": 0.326,
            "Pitcher": 0.34
        },
        "1914": {
            "Hitter": 0.323,
            "Pitcher": 0.352
        },
        "1915": {
            "Hitter": 0.318,
            "Pitcher": 0.34
        },
        "1916": {
            "Hitter": 0.314,
            "Pitcher": 0.325
        },
        "1917": {
            "Hitter": 0.311,
            "Pitcher": 0.323
        },
        "1918": {
            "Hitter": 0.318,
            "Pitcher": 0.328
        },
        "1919": {
            "Hitter": 0.323,
            "Pitcher": 0.337
        },
        "1920": {
            "Hitter": 0.327,
            "Pitcher": 0.342
        },
        "1921": {
            "Hitter": 0.34,
            "Pitcher": 0.343
        },
        "1922": {
            "Hitter": 0.346,
            "Pitcher": 0.35
        },
        "1923": {
            "Hitter": 0.34,
            "Pitcher": 0.349
        },
        "1924": {
            "Hitter": 0.339,
            "Pitcher": 0.349
        },
        "1925": {
            "Hitter": 0.347,
            "Pitcher": 0.351
        },
        "1926": {
            "Hitter": 0.343,
            "Pitcher": 0.349
        },
        "1927": {
            "Hitter": 0.342,
            "Pitcher": 0.348
        },
        "1928": {
            "Hitter": 0.342,
            "Pitcher": 0.343
        },
        "1929": {
            "Hitter": 0.35,
            "Pitcher": 0.356
        },
        "1930": {
            "Hitter": 0.345,
            "Pitcher": 0.356
        },
        "1931": {
            "Hitter": 0.34,
            "Pitcher": 0.353
        },
        "1932": {
            "Hitter": 0.325,
            "Pitcher": 0.336
        },
        "1933": {
            "Hitter": 0.326,
            "Pitcher": 0.339
        },
        "1934": {
            "Hitter": 0.337,
            "Pitcher": 0.35
        },
        "1935": {
            "Hitter": 0.347,
            "Pitcher": 0.353
        },
        "1936": {
            "Hitter": 0.349,
            "Pitcher": 0.356
        },
        "1937": {
            "Hitter": 0.342,
            "Pitcher": 0.344
        },
        "1938": {
            "Hitter": 0.338,
            "Pitcher": 0.341
        },
        "1939": {
            "Hitter": 0.336,
            "Pitcher": 0.342
        },
        "1940": {
            "Hitter": 0.335,
            "Pitcher": 0.343
        },
        "1941": {
            "Hitter": 0.326,
            "Pitcher": 0.334
        },
        "1942": {
            "Hitter": 0.319,
            "Pitcher": 0.327
        },
        "1943": {
            "Hitter": 0.325,
            "Pitcher": 0.332
        },
        "1944": {
            "Hitter": 0.328,
            "Pitcher": 0.334
        },
        "1945": {
            "Hitter": 0.33,
            "Pitcher": 0.332
        },
        "1946": {
            "Hitter": 0.333,
            "Pitcher": 0.339
        },
        "1947": {
            "Hitter": 0.341,
            "Pitcher": 0.342
        },
        "1948": {
            "Hitter": 0.339,
            "Pitcher": 0.348
        },
        "1949": {
            "Hitter": 0.346,
            "Pitcher": 0.353
        },
        "1950": {
            "Hitter": 0.35,
            "Pitcher": 0.36
        },
        "1951": {
            "Hitter": 0.336,
            "Pitcher": 0.351
        },
        "1952": {
            "Hitter": 0.33,
            "Pitcher": 0.343
        },
        "1953": {
            "Hitter": 0.342,
            "Pitcher": 0.349
        },
        "1954": {
            "Hitter": 0.336,
            "Pitcher": 0.347
        },
        "1955": {
            "Hitter": 0.335,
            "Pitcher": 0.345
        },
        "1956": {
            "Hitter": 0.334,
            "Pitcher": 0.345
        },
        "1957": {
            "Hitter": 0.329,
            "Pitcher": 0.338
        },
        "1958": {
            "Hitter": 0.329,
            "Pitcher": 0.338
        },
        "1959": {
            "Hitter": 0.329,
            "Pitcher": 0.343
        },
        "1960": {
            "Hitter": 0.329,
            "Pitcher": 0.339
        },
        "1961": {
            "Hitter": 0.332,
            "Pitcher": 0.342
        },
        "1962": {
            "Hitter": 0.333,
            "Pitcher": 0.338
        },
        "1963": {
            "Hitter": 0.316,
            "Pitcher": 0.328
        },
        "1964": {
            "Hitter": 0.317,
            "Pitcher": 0.324
        },
        "1965": {
            "Hitter": 0.317,
            "Pitcher": 0.325
        },
        "1966": {
            "Hitter": 0.314,
            "Pitcher": 0.321
        },
        "1967": {
            "Hitter": 0.31,
            "Pitcher": 0.32
        },
        "1968": {
            "Hitter": 0.304,
            "Pitcher": 0.314
        },
        "1969": {
            "Hitter": 0.325,
            "Pitcher": 0.334
        },
        "1970": {
            "Hitter": 0.332,
            "Pitcher": 0.338
        },
        "1971": {
            "Hitter": 0.322,
            "Pitcher": 0.329
        },
        "1972": {
            "Hitter": 0.315,
            "Pitcher": 0.325
        },
        "1973": {
            "Hitter": 0.325,
            "Pitcher": 0.339
        },
        "1974": {
            "Hitter": 0.324,
            "Pitcher": 0.335
        },
        "1975": {
            "Hitter": 0.329,
            "Pitcher": 0.335
        },
        "1976": {
            "Hitter": 0.322,
            "Pitcher": 0.329
        },
        "1977": {
            "Hitter": 0.329,
            "Pitcher": 0.339
        },
        "1978": {
            "Hitter": 0.324,
            "Pitcher": 0.331
        },
        "1979": {
            "Hitter": 0.331,
            "Pitcher": 0.338
        },
        "1980": {
            "Hitter": 0.328,
            "Pitcher": 0.335
        },
        "1981": {
            "Hitter": 0.32,
            "Pitcher": 0.329
        },
        "1982": {
            "Hitter": 0.326,
            "Pitcher": 0.331
        },
        "1983": {
            "Hitter": 0.328,
            "Pitcher": 0.333
        },
        "1984": {
            "Hitter": 0.325,
            "Pitcher": 0.328
        },
        "1985": {
            "Hitter": 0.324,
            "Pitcher": 0.332
        },
        "1986": {
            "Hitter": 0.328,
            "Pitcher": 0.335
        },
        "1987": {
            "Hitter": 0.334,
            "Pitcher": 0.34
        },
        "1988": {
            "Hitter": 0.318,
            "Pitcher": 0.327
        },
        "1989": {
            "Hitter": 0.32,
            "Pitcher": 0.326
        },
        "1990": {
            "Hitter": 0.327,
            "Pitcher": 0.328
        },
        "1991": {
            "Hitter": 0.325,
            "Pitcher": 0.326
        },
        "1992": {
            "Hitter": 0.323,
            "Pitcher": 0.327
        },
        "1993": {
            "Hitter": 0.333,
            "Pitcher": 0.336
        },
        "1994": {
            "Hitter": 0.34,
            "Pitcher": 0.344
        },
        "1995": {
            "Hitter": 0.338,
            "Pitcher": 0.341
        },
        "1996": {
            "Hitter": 0.341,
            "Pitcher": 0.345
        },
        "1997": {
            "Hitter": 0.339,
            "Pitcher": 0.341
        },
        "1998": {
            "Hitter": 0.334,
            "Pitcher": 0.338
        },
        "1999": {
            "Hitter": 0.345,
            "Pitcher": 0.347
        },
        "2000": {
            "Hitter": 0.345,
            "Pitcher": 0.348
        },
        "2001": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "2002": {
            "Hitter": 0.332,
            "Pitcher": 0.333
        },
        "2003": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "2004": {
            "Hitter": 0.335,
            "Pitcher": 0.334
        },
        "2005": {
            "Hitter": 0.332,
            "Pitcher": 0.334
        },
        "2006": {
            "Hitter": 0.337,
            "Pitcher": 0.335
        },
        "2007": {
            "Hitter": 0.336,
            "Pitcher": 0.335
        },
        "2008": {
            "Hitter": 0.334,
            "Pitcher": 0.331
        },
        "2009": {
            "Hitter": 0.334,
            "Pitcher": 0.332
        },
        "2010": {
            "Hitter": 0.327,
            "Pitcher": 0.327
        },
        "2011": {
            "Hitter": 0.322,
            "Pitcher": 0.32
        },
        "2012": {
            "Hitter": 0.321,
            "Pitcher": 0.318
        },
        "2013": {
            "Hitter": 0.319,
            "Pitcher": 0.317
        },
        "2014": {
            "Hitter": 0.315,
            "Pitcher": 0.311
        },
        "2015": {
            "Hitter": 0.319,
            "Pitcher": 0.317
        },
        "2016": {
            "Hitter": 0.324,
            "Pitcher": 0.32
        },
        "2017": {
            "Hitter": 0.327,
            "Pitcher": 0.323
        },
        "2018": {
            "Hitter": 0.32,
            "Pitcher": 0.318
        },
        "2019": {
            "Hitter": 0.324,
            "Pitcher": 0.323
        },
        "2020": {
            "Hitter": 0.318,
            "Pitcher": 0.314
        },
        "2021": {
            "Hitter": 0.32,
            "Pitcher": 0.315
        },
        "2022": {
            "Hitter": 0.31,
            "Pitcher": 0.309
        }
    },
    "2002": {
        "1900": {
            "Hitter": 0.338,
            "Pitcher": 0.333
        },
        "1901": {
            "Hitter": 0.324,
            "Pitcher": 0.379
        },
        "1902": {
            "Hitter": 0.32,
            "Pitcher": 0.364
        },
        "1903": {
            "Hitter": 0.317,
            "Pitcher": 0.346
        },
        "1904": {
            "Hitter": 0.301,
            "Pitcher": 0.323
        },
        "1905": {
            "Hitter": 0.31,
            "Pitcher": 0.343
        },
        "1906": {
            "Hitter": 0.309,
            "Pitcher": 0.342
        },
        "1907": {
            "Hitter": 0.308,
            "Pitcher": 0.347
        },
        "1908": {
            "Hitter": 0.301,
            "Pitcher": 0.317
        },
        "1909": {
            "Hitter": 0.312,
            "Pitcher": 0.318
        },
        "1910": {
            "Hitter": 0.32,
            "Pitcher": 0.34
        },
        "1911": {
            "Hitter": 0.339,
            "Pitcher": 0.348
        },
        "1912": {
            "Hitter": 0.34,
            "Pitcher": 0.359
        },
        "1913": {
            "Hitter": 0.327,
            "Pitcher": 0.342
        },
        "1914": {
            "Hitter": 0.325,
            "Pitcher": 0.358
        },
        "1915": {
            "Hitter": 0.32,
            "Pitcher": 0.343
        },
        "1916": {
            "Hitter": 0.316,
            "Pitcher": 0.324
        },
        "1917": {
            "Hitter": 0.313,
            "Pitcher": 0.322
        },
        "1918": {
            "Hitter": 0.32,
            "Pitcher": 0.329
        },
        "1919": {
            "Hitter": 0.325,
            "Pitcher": 0.338
        },
        "1920": {
            "Hitter": 0.329,
            "Pitcher": 0.345
        },
        "1921": {
            "Hitter": 0.341,
            "Pitcher": 0.344
        },
        "1922": {
            "Hitter": 0.347,
            "Pitcher": 0.351
        },
        "1923": {
            "Hitter": 0.342,
            "Pitcher": 0.351
        },
        "1924": {
            "Hitter": 0.341,
            "Pitcher": 0.35
        },
        "1925": {
            "Hitter": 0.348,
            "Pitcher": 0.353
        },
        "1926": {
            "Hitter": 0.345,
            "Pitcher": 0.35
        },
        "1927": {
            "Hitter": 0.344,
            "Pitcher": 0.35
        },
        "1928": {
            "Hitter": 0.344,
            "Pitcher": 0.344
        },
        "1929": {
            "Hitter": 0.351,
            "Pitcher": 0.358
        },
        "1930": {
            "Hitter": 0.346,
            "Pitcher": 0.359
        },
        "1931": {
            "Hitter": 0.341,
            "Pitcher": 0.353
        },
        "1932": {
            "Hitter": 0.329,
            "Pitcher": 0.338
        },
        "1933": {
            "Hitter": 0.329,
            "Pitcher": 0.341
        },
        "1934": {
            "Hitter": 0.34,
            "Pitcher": 0.352
        },
        "1935": {
            "Hitter": 0.348,
            "Pitcher": 0.356
        },
        "1936": {
            "Hitter": 0.35,
            "Pitcher": 0.358
        },
        "1937": {
            "Hitter": 0.345,
            "Pitcher": 0.346
        },
        "1938": {
            "Hitter": 0.34,
            "Pitcher": 0.343
        },
        "1939": {
            "Hitter": 0.339,
            "Pitcher": 0.344
        },
        "1940": {
            "Hitter": 0.337,
            "Pitcher": 0.345
        },
        "1941": {
            "Hitter": 0.33,
            "Pitcher": 0.337
        },
        "1942": {
            "Hitter": 0.323,
            "Pitcher": 0.328
        },
        "1943": {
            "Hitter": 0.328,
            "Pitcher": 0.331
        },
        "1944": {
            "Hitter": 0.33,
            "Pitcher": 0.336
        },
        "1945": {
            "Hitter": 0.332,
            "Pitcher": 0.332
        },
        "1946": {
            "Hitter": 0.336,
            "Pitcher": 0.34
        },
        "1947": {
            "Hitter": 0.343,
            "Pitcher": 0.344
        },
        "1948": {
            "Hitter": 0.341,
            "Pitcher": 0.349
        },
        "1949": {
            "Hitter": 0.346,
            "Pitcher": 0.356
        },
        "1950": {
            "Hitter": 0.35,
            "Pitcher": 0.364
        },
        "1951": {
            "Hitter": 0.337,
            "Pitcher": 0.352
        },
        "1952": {
            "Hitter": 0.331,
            "Pitcher": 0.344
        },
        "1953": {
            "Hitter": 0.342,
            "Pitcher": 0.351
        },
        "1954": {
            "Hitter": 0.337,
            "Pitcher": 0.348
        },
        "1955": {
            "Hitter": 0.336,
            "Pitcher": 0.345
        },
        "1956": {
            "Hitter": 0.335,
            "Pitcher": 0.347
        },
        "1957": {
            "Hitter": 0.329,
            "Pitcher": 0.34
        },
        "1958": {
            "Hitter": 0.329,
            "Pitcher": 0.339
        },
        "1959": {
            "Hitter": 0.33,
            "Pitcher": 0.345
        },
        "1960": {
            "Hitter": 0.33,
            "Pitcher": 0.341
        },
        "1961": {
            "Hitter": 0.333,
            "Pitcher": 0.342
        },
        "1962": {
            "Hitter": 0.334,
            "Pitcher": 0.337
        },
        "1963": {
            "Hitter": 0.317,
            "Pitcher": 0.328
        },
        "1964": {
            "Hitter": 0.318,
            "Pitcher": 0.323
        },
        "1965": {
            "Hitter": 0.317,
            "Pitcher": 0.323
        },
        "1966": {
            "Hitter": 0.314,
            "Pitcher": 0.322
        },
        "1967": {
            "Hitter": 0.312,
            "Pitcher": 0.32
        },
        "1968": {
            "Hitter": 0.306,
            "Pitcher": 0.313
        },
        "1969": {
            "Hitter": 0.325,
            "Pitcher": 0.333
        },
        "1970": {
            "Hitter": 0.333,
            "Pitcher": 0.338
        },
        "1971": {
            "Hitter": 0.323,
            "Pitcher": 0.328
        },
        "1972": {
            "Hitter": 0.316,
            "Pitcher": 0.324
        },
        "1973": {
            "Hitter": 0.326,
            "Pitcher": 0.34
        },
        "1974": {
            "Hitter": 0.324,
            "Pitcher": 0.335
        },
        "1975": {
            "Hitter": 0.329,
            "Pitcher": 0.335
        },
        "1976": {
            "Hitter": 0.323,
            "Pitcher": 0.328
        },
        "1977": {
            "Hitter": 0.329,
            "Pitcher": 0.339
        },
        "1978": {
            "Hitter": 0.325,
            "Pitcher": 0.332
        },
        "1979": {
            "Hitter": 0.332,
            "Pitcher": 0.338
        },
        "1980": {
            "Hitter": 0.328,
            "Pitcher": 0.336
        },
        "1981": {
            "Hitter": 0.321,
            "Pitcher": 0.328
        },
        "1982": {
            "Hitter": 0.327,
            "Pitcher": 0.33
        },
        "1983": {
            "Hitter": 0.328,
            "Pitcher": 0.333
        },
        "1984": {
            "Hitter": 0.326,
            "Pitcher": 0.328
        },
        "1985": {
            "Hitter": 0.325,
            "Pitcher": 0.332
        },
        "1986": {
            "Hitter": 0.328,
            "Pitcher": 0.334
        },
        "1987": {
            "Hitter": 0.334,
            "Pitcher": 0.339
        },
        "1988": {
            "Hitter": 0.32,
            "Pitcher": 0.327
        },
        "1989": {
            "Hitter": 0.321,
            "Pitcher": 0.326
        },
        "1990": {
            "Hitter": 0.327,
            "Pitcher": 0.328
        },
        "1991": {
            "Hitter": 0.325,
            "Pitcher": 0.326
        },
        "1992": {
            "Hitter": 0.323,
            "Pitcher": 0.326
        },
        "1993": {
            "Hitter": 0.334,
            "Pitcher": 0.336
        },
        "1994": {
            "Hitter": 0.34,
            "Pitcher": 0.345
        },
        "1995": {
            "Hitter": 0.339,
            "Pitcher": 0.342
        },
        "1996": {
            "Hitter": 0.342,
            "Pitcher": 0.344
        },
        "1997": {
            "Hitter": 0.339,
            "Pitcher": 0.342
        },
        "1998": {
            "Hitter": 0.335,
            "Pitcher": 0.339
        },
        "1999": {
            "Hitter": 0.345,
            "Pitcher": 0.348
        },
        "2000": {
            "Hitter": 0.346,
            "Pitcher": 0.348
        },
        "2001": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "2002": {
            "Hitter": 0.333,
            "Pitcher": 0.332
        },
        "2003": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "2004": {
            "Hitter": 0.336,
            "Pitcher": 0.335
        },
        "2005": {
            "Hitter": 0.332,
            "Pitcher": 0.333
        },
        "2006": {
            "Hitter": 0.338,
            "Pitcher": 0.335
        },
        "2007": {
            "Hitter": 0.337,
            "Pitcher": 0.335
        },
        "2008": {
            "Hitter": 0.335,
            "Pitcher": 0.331
        },
        "2009": {
            "Hitter": 0.334,
            "Pitcher": 0.332
        },
        "2010": {
            "Hitter": 0.328,
            "Pitcher": 0.326
        },
        "2011": {
            "Hitter": 0.323,
            "Pitcher": 0.319
        },
        "2012": {
            "Hitter": 0.321,
            "Pitcher": 0.318
        },
        "2013": {
            "Hitter": 0.32,
            "Pitcher": 0.316
        },
        "2014": {
            "Hitter": 0.316,
            "Pitcher": 0.311
        },
        "2015": {
            "Hitter": 0.32,
            "Pitcher": 0.317
        },
        "2016": {
            "Hitter": 0.324,
            "Pitcher": 0.319
        },
        "2017": {
            "Hitter": 0.327,
            "Pitcher": 0.32
        },
        "2018": {
            "Hitter": 0.321,
            "Pitcher": 0.317
        },
        "2019": {
            "Hitter": 0.325,
            "Pitcher": 0.322
        },
        "2020": {
            "Hitter": 0.32,
            "Pitcher": 0.312
        },
        "2021": {
            "Hitter": 0.321,
            "Pitcher": 0.313
        },
        "2022": {
            "Hitter": 0.311,
            "Pitcher": 0.308
        }
    },
    "2003": {
        "1900": {
            "Hitter": 0.337,
            "Pitcher": 0.33
        },
        "1901": {
            "Hitter": 0.322,
            "Pitcher": 0.372
        },
        "1902": {
            "Hitter": 0.317,
            "Pitcher": 0.359
        },
        "1903": {
            "Hitter": 0.315,
            "Pitcher": 0.342
        },
        "1904": {
            "Hitter": 0.299,
            "Pitcher": 0.32
        },
        "1905": {
            "Hitter": 0.308,
            "Pitcher": 0.337
        },
        "1906": {
            "Hitter": 0.306,
            "Pitcher": 0.339
        },
        "1907": {
            "Hitter": 0.306,
            "Pitcher": 0.342
        },
        "1908": {
            "Hitter": 0.299,
            "Pitcher": 0.314
        },
        "1909": {
            "Hitter": 0.309,
            "Pitcher": 0.317
        },
        "1910": {
            "Hitter": 0.318,
            "Pitcher": 0.335
        },
        "1911": {
            "Hitter": 0.338,
            "Pitcher": 0.343
        },
        "1912": {
            "Hitter": 0.339,
            "Pitcher": 0.353
        },
        "1913": {
            "Hitter": 0.326,
            "Pitcher": 0.337
        },
        "1914": {
            "Hitter": 0.323,
            "Pitcher": 0.35
        },
        "1915": {
            "Hitter": 0.319,
            "Pitcher": 0.338
        },
        "1916": {
            "Hitter": 0.315,
            "Pitcher": 0.322
        },
        "1917": {
            "Hitter": 0.312,
            "Pitcher": 0.32
        },
        "1918": {
            "Hitter": 0.318,
            "Pitcher": 0.324
        },
        "1919": {
            "Hitter": 0.324,
            "Pitcher": 0.334
        },
        "1920": {
            "Hitter": 0.327,
            "Pitcher": 0.34
        },
        "1921": {
            "Hitter": 0.34,
            "Pitcher": 0.339
        },
        "1922": {
            "Hitter": 0.346,
            "Pitcher": 0.347
        },
        "1923": {
            "Hitter": 0.34,
            "Pitcher": 0.345
        },
        "1924": {
            "Hitter": 0.34,
            "Pitcher": 0.346
        },
        "1925": {
            "Hitter": 0.347,
            "Pitcher": 0.349
        },
        "1926": {
            "Hitter": 0.344,
            "Pitcher": 0.346
        },
        "1927": {
            "Hitter": 0.343,
            "Pitcher": 0.345
        },
        "1928": {
            "Hitter": 0.342,
            "Pitcher": 0.34
        },
        "1929": {
            "Hitter": 0.351,
            "Pitcher": 0.353
        },
        "1930": {
            "Hitter": 0.345,
            "Pitcher": 0.353
        },
        "1931": {
            "Hitter": 0.34,
            "Pitcher": 0.349
        },
        "1932": {
            "Hitter": 0.326,
            "Pitcher": 0.334
        },
        "1933": {
            "Hitter": 0.327,
            "Pitcher": 0.337
        },
        "1934": {
            "Hitter": 0.338,
            "Pitcher": 0.348
        },
        "1935": {
            "Hitter": 0.347,
            "Pitcher": 0.351
        },
        "1936": {
            "Hitter": 0.349,
            "Pitcher": 0.353
        },
        "1937": {
            "Hitter": 0.343,
            "Pitcher": 0.342
        },
        "1938": {
            "Hitter": 0.338,
            "Pitcher": 0.339
        },
        "1939": {
            "Hitter": 0.337,
            "Pitcher": 0.339
        },
        "1940": {
            "Hitter": 0.335,
            "Pitcher": 0.341
        },
        "1941": {
            "Hitter": 0.327,
            "Pitcher": 0.333
        },
        "1942": {
            "Hitter": 0.321,
            "Pitcher": 0.326
        },
        "1943": {
            "Hitter": 0.326,
            "Pitcher": 0.329
        },
        "1944": {
            "Hitter": 0.329,
            "Pitcher": 0.331
        },
        "1945": {
            "Hitter": 0.33,
            "Pitcher": 0.33
        },
        "1946": {
            "Hitter": 0.334,
            "Pitcher": 0.336
        },
        "1947": {
            "Hitter": 0.341,
            "Pitcher": 0.34
        },
        "1948": {
            "Hitter": 0.339,
            "Pitcher": 0.345
        },
        "1949": {
            "Hitter": 0.346,
            "Pitcher": 0.351
        },
        "1950": {
            "Hitter": 0.35,
            "Pitcher": 0.358
        },
        "1951": {
            "Hitter": 0.336,
            "Pitcher": 0.348
        },
        "1952": {
            "Hitter": 0.331,
            "Pitcher": 0.34
        },
        "1953": {
            "Hitter": 0.342,
            "Pitcher": 0.347
        },
        "1954": {
            "Hitter": 0.336,
            "Pitcher": 0.345
        },
        "1955": {
            "Hitter": 0.336,
            "Pitcher": 0.342
        },
        "1956": {
            "Hitter": 0.335,
            "Pitcher": 0.343
        },
        "1957": {
            "Hitter": 0.328,
            "Pitcher": 0.337
        },
        "1958": {
            "Hitter": 0.329,
            "Pitcher": 0.336
        },
        "1959": {
            "Hitter": 0.329,
            "Pitcher": 0.342
        },
        "1960": {
            "Hitter": 0.33,
            "Pitcher": 0.337
        },
        "1961": {
            "Hitter": 0.332,
            "Pitcher": 0.339
        },
        "1962": {
            "Hitter": 0.333,
            "Pitcher": 0.335
        },
        "1963": {
            "Hitter": 0.316,
            "Pitcher": 0.325
        },
        "1964": {
            "Hitter": 0.317,
            "Pitcher": 0.322
        },
        "1965": {
            "Hitter": 0.317,
            "Pitcher": 0.321
        },
        "1966": {
            "Hitter": 0.314,
            "Pitcher": 0.318
        },
        "1967": {
            "Hitter": 0.311,
            "Pitcher": 0.317
        },
        "1968": {
            "Hitter": 0.304,
            "Pitcher": 0.311
        },
        "1969": {
            "Hitter": 0.325,
            "Pitcher": 0.331
        },
        "1970": {
            "Hitter": 0.332,
            "Pitcher": 0.336
        },
        "1971": {
            "Hitter": 0.322,
            "Pitcher": 0.327
        },
        "1972": {
            "Hitter": 0.315,
            "Pitcher": 0.323
        },
        "1973": {
            "Hitter": 0.325,
            "Pitcher": 0.336
        },
        "1974": {
            "Hitter": 0.324,
            "Pitcher": 0.333
        },
        "1975": {
            "Hitter": 0.329,
            "Pitcher": 0.332
        },
        "1976": {
            "Hitter": 0.322,
            "Pitcher": 0.327
        },
        "1977": {
            "Hitter": 0.329,
            "Pitcher": 0.337
        },
        "1978": {
            "Hitter": 0.325,
            "Pitcher": 0.329
        },
        "1979": {
            "Hitter": 0.332,
            "Pitcher": 0.336
        },
        "1980": {
            "Hitter": 0.328,
            "Pitcher": 0.333
        },
        "1981": {
            "Hitter": 0.32,
            "Pitcher": 0.326
        },
        "1982": {
            "Hitter": 0.326,
            "Pitcher": 0.328
        },
        "1983": {
            "Hitter": 0.328,
            "Pitcher": 0.331
        },
        "1984": {
            "Hitter": 0.325,
            "Pitcher": 0.326
        },
        "1985": {
            "Hitter": 0.325,
            "Pitcher": 0.329
        },
        "1986": {
            "Hitter": 0.328,
            "Pitcher": 0.333
        },
        "1987": {
            "Hitter": 0.333,
            "Pitcher": 0.338
        },
        "1988": {
            "Hitter": 0.319,
            "Pitcher": 0.324
        },
        "1989": {
            "Hitter": 0.32,
            "Pitcher": 0.324
        },
        "1990": {
            "Hitter": 0.327,
            "Pitcher": 0.325
        },
        "1991": {
            "Hitter": 0.325,
            "Pitcher": 0.324
        },
        "1992": {
            "Hitter": 0.323,
            "Pitcher": 0.325
        },
        "1993": {
            "Hitter": 0.333,
            "Pitcher": 0.334
        },
        "1994": {
            "Hitter": 0.34,
            "Pitcher": 0.343
        },
        "1995": {
            "Hitter": 0.338,
            "Pitcher": 0.34
        },
        "1996": {
            "Hitter": 0.342,
            "Pitcher": 0.342
        },
        "1997": {
            "Hitter": 0.338,
            "Pitcher": 0.339
        },
        "1998": {
            "Hitter": 0.335,
            "Pitcher": 0.336
        },
        "1999": {
            "Hitter": 0.345,
            "Pitcher": 0.345
        },
        "2000": {
            "Hitter": 0.345,
            "Pitcher": 0.346
        },
        "2001": {
            "Hitter": 0.334,
            "Pitcher": 0.333
        },
        "2002": {
            "Hitter": 0.332,
            "Pitcher": 0.331
        },
        "2003": {
            "Hitter": 0.334,
            "Pitcher": 0.333
        },
        "2004": {
            "Hitter": 0.335,
            "Pitcher": 0.334
        },
        "2005": {
            "Hitter": 0.332,
            "Pitcher": 0.331
        },
        "2006": {
            "Hitter": 0.338,
            "Pitcher": 0.334
        },
        "2007": {
            "Hitter": 0.337,
            "Pitcher": 0.333
        },
        "2008": {
            "Hitter": 0.335,
            "Pitcher": 0.329
        },
        "2009": {
            "Hitter": 0.334,
            "Pitcher": 0.33
        },
        "2010": {
            "Hitter": 0.327,
            "Pitcher": 0.324
        },
        "2011": {
            "Hitter": 0.322,
            "Pitcher": 0.318
        },
        "2012": {
            "Hitter": 0.32,
            "Pitcher": 0.316
        },
        "2013": {
            "Hitter": 0.32,
            "Pitcher": 0.314
        },
        "2014": {
            "Hitter": 0.315,
            "Pitcher": 0.309
        },
        "2015": {
            "Hitter": 0.319,
            "Pitcher": 0.315
        },
        "2016": {
            "Hitter": 0.324,
            "Pitcher": 0.317
        },
        "2017": {
            "Hitter": 0.327,
            "Pitcher": 0.321
        },
        "2018": {
            "Hitter": 0.32,
            "Pitcher": 0.316
        },
        "2019": {
            "Hitter": 0.325,
            "Pitcher": 0.321
        },
        "2020": {
            "Hitter": 0.319,
            "Pitcher": 0.31
        },
        "2021": {
            "Hitter": 0.32,
            "Pitcher": 0.313
        },
        "2022": {
            "Hitter": 0.31,
            "Pitcher": 0.306
        }
    },
    "2004": {
        "1900": {
            "Hitter": 0.339,
            "Pitcher": 0.333
        },
        "1901": {
            "Hitter": 0.328,
            "Pitcher": 0.382
        },
        "1902": {
            "Hitter": 0.323,
            "Pitcher": 0.366
        },
        "1903": {
            "Hitter": 0.32,
            "Pitcher": 0.347
        },
        "1904": {
            "Hitter": 0.307,
            "Pitcher": 0.324
        },
        "1905": {
            "Hitter": 0.314,
            "Pitcher": 0.345
        },
        "1906": {
            "Hitter": 0.313,
            "Pitcher": 0.343
        },
        "1907": {
            "Hitter": 0.311,
            "Pitcher": 0.351
        },
        "1908": {
            "Hitter": 0.305,
            "Pitcher": 0.32
        },
        "1909": {
            "Hitter": 0.314,
            "Pitcher": 0.32
        },
        "1910": {
            "Hitter": 0.322,
            "Pitcher": 0.341
        },
        "1911": {
            "Hitter": 0.34,
            "Pitcher": 0.351
        },
        "1912": {
            "Hitter": 0.341,
            "Pitcher": 0.364
        },
        "1913": {
            "Hitter": 0.328,
            "Pitcher": 0.344
        },
        "1914": {
            "Hitter": 0.325,
            "Pitcher": 0.364
        },
        "1915": {
            "Hitter": 0.322,
            "Pitcher": 0.346
        },
        "1916": {
            "Hitter": 0.317,
            "Pitcher": 0.325
        },
        "1917": {
            "Hitter": 0.315,
            "Pitcher": 0.323
        },
        "1918": {
            "Hitter": 0.322,
            "Pitcher": 0.332
        },
        "1919": {
            "Hitter": 0.327,
            "Pitcher": 0.341
        },
        "1920": {
            "Hitter": 0.331,
            "Pitcher": 0.345
        },
        "1921": {
            "Hitter": 0.343,
            "Pitcher": 0.346
        },
        "1922": {
            "Hitter": 0.347,
            "Pitcher": 0.353
        },
        "1923": {
            "Hitter": 0.343,
            "Pitcher": 0.353
        },
        "1924": {
            "Hitter": 0.343,
            "Pitcher": 0.352
        },
        "1925": {
            "Hitter": 0.35,
            "Pitcher": 0.355
        },
        "1926": {
            "Hitter": 0.347,
            "Pitcher": 0.352
        },
        "1927": {
            "Hitter": 0.345,
            "Pitcher": 0.351
        },
        "1928": {
            "Hitter": 0.345,
            "Pitcher": 0.344
        },
        "1929": {
            "Hitter": 0.353,
            "Pitcher": 0.36
        },
        "1930": {
            "Hitter": 0.347,
            "Pitcher": 0.361
        },
        "1931": {
            "Hitter": 0.342,
            "Pitcher": 0.355
        },
        "1932": {
            "Hitter": 0.331,
            "Pitcher": 0.338
        },
        "1933": {
            "Hitter": 0.331,
            "Pitcher": 0.341
        },
        "1934": {
            "Hitter": 0.342,
            "Pitcher": 0.352
        },
        "1935": {
            "Hitter": 0.348,
            "Pitcher": 0.356
        },
        "1936": {
            "Hitter": 0.352,
            "Pitcher": 0.36
        },
        "1937": {
            "Hitter": 0.346,
            "Pitcher": 0.346
        },
        "1938": {
            "Hitter": 0.341,
            "Pitcher": 0.344
        },
        "1939": {
            "Hitter": 0.341,
            "Pitcher": 0.345
        },
        "1940": {
            "Hitter": 0.339,
            "Pitcher": 0.347
        },
        "1941": {
            "Hitter": 0.332,
            "Pitcher": 0.337
        },
        "1942": {
            "Hitter": 0.326,
            "Pitcher": 0.33
        },
        "1943": {
            "Hitter": 0.329,
            "Pitcher": 0.332
        },
        "1944": {
            "Hitter": 0.332,
            "Pitcher": 0.337
        },
        "1945": {
            "Hitter": 0.334,
            "Pitcher": 0.333
        },
        "1946": {
            "Hitter": 0.337,
            "Pitcher": 0.341
        },
        "1947": {
            "Hitter": 0.343,
            "Pitcher": 0.344
        },
        "1948": {
            "Hitter": 0.343,
            "Pitcher": 0.349
        },
        "1949": {
            "Hitter": 0.347,
            "Pitcher": 0.356
        },
        "1950": {
            "Hitter": 0.35,
            "Pitcher": 0.364
        },
        "1951": {
            "Hitter": 0.337,
            "Pitcher": 0.355
        },
        "1952": {
            "Hitter": 0.333,
            "Pitcher": 0.344
        },
        "1953": {
            "Hitter": 0.342,
            "Pitcher": 0.352
        },
        "1954": {
            "Hitter": 0.338,
            "Pitcher": 0.349
        },
        "1955": {
            "Hitter": 0.337,
            "Pitcher": 0.344
        },
        "1956": {
            "Hitter": 0.335,
            "Pitcher": 0.347
        },
        "1957": {
            "Hitter": 0.329,
            "Pitcher": 0.338
        },
        "1958": {
            "Hitter": 0.329,
            "Pitcher": 0.338
        },
        "1959": {
            "Hitter": 0.33,
            "Pitcher": 0.345
        },
        "1960": {
            "Hitter": 0.33,
            "Pitcher": 0.341
        },
        "1961": {
            "Hitter": 0.334,
            "Pitcher": 0.342
        },
        "1962": {
            "Hitter": 0.334,
            "Pitcher": 0.338
        },
        "1963": {
            "Hitter": 0.318,
            "Pitcher": 0.328
        },
        "1964": {
            "Hitter": 0.319,
            "Pitcher": 0.322
        },
        "1965": {
            "Hitter": 0.319,
            "Pitcher": 0.323
        },
        "1966": {
            "Hitter": 0.316,
            "Pitcher": 0.321
        },
        "1967": {
            "Hitter": 0.314,
            "Pitcher": 0.32
        },
        "1968": {
            "Hitter": 0.309,
            "Pitcher": 0.313
        },
        "1969": {
            "Hitter": 0.327,
            "Pitcher": 0.334
        },
        "1970": {
            "Hitter": 0.333,
            "Pitcher": 0.337
        },
        "1971": {
            "Hitter": 0.324,
            "Pitcher": 0.328
        },
        "1972": {
            "Hitter": 0.318,
            "Pitcher": 0.325
        },
        "1973": {
            "Hitter": 0.328,
            "Pitcher": 0.339
        },
        "1974": {
            "Hitter": 0.325,
            "Pitcher": 0.335
        },
        "1975": {
            "Hitter": 0.33,
            "Pitcher": 0.335
        },
        "1976": {
            "Hitter": 0.323,
            "Pitcher": 0.328
        },
        "1977": {
            "Hitter": 0.331,
            "Pitcher": 0.339
        },
        "1978": {
            "Hitter": 0.325,
            "Pitcher": 0.331
        },
        "1979": {
            "Hitter": 0.333,
            "Pitcher": 0.337
        },
        "1980": {
            "Hitter": 0.329,
            "Pitcher": 0.334
        },
        "1981": {
            "Hitter": 0.323,
            "Pitcher": 0.328
        },
        "1982": {
            "Hitter": 0.327,
            "Pitcher": 0.33
        },
        "1983": {
            "Hitter": 0.329,
            "Pitcher": 0.332
        },
        "1984": {
            "Hitter": 0.327,
            "Pitcher": 0.328
        },
        "1985": {
            "Hitter": 0.326,
            "Pitcher": 0.331
        },
        "1986": {
            "Hitter": 0.329,
            "Pitcher": 0.334
        },
        "1987": {
            "Hitter": 0.334,
            "Pitcher": 0.339
        },
        "1988": {
            "Hitter": 0.321,
            "Pitcher": 0.327
        },
        "1989": {
            "Hitter": 0.322,
            "Pitcher": 0.325
        },
        "1990": {
            "Hitter": 0.328,
            "Pitcher": 0.326
        },
        "1991": {
            "Hitter": 0.326,
            "Pitcher": 0.325
        },
        "1992": {
            "Hitter": 0.324,
            "Pitcher": 0.325
        },
        "1993": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "1994": {
            "Hitter": 0.34,
            "Pitcher": 0.344
        },
        "1995": {
            "Hitter": 0.339,
            "Pitcher": 0.341
        },
        "1996": {
            "Hitter": 0.342,
            "Pitcher": 0.344
        },
        "1997": {
            "Hitter": 0.339,
            "Pitcher": 0.341
        },
        "1998": {
            "Hitter": 0.336,
            "Pitcher": 0.338
        },
        "1999": {
            "Hitter": 0.345,
            "Pitcher": 0.347
        },
        "2000": {
            "Hitter": 0.346,
            "Pitcher": 0.347
        },
        "2001": {
            "Hitter": 0.335,
            "Pitcher": 0.333
        },
        "2002": {
            "Hitter": 0.333,
            "Pitcher": 0.331
        },
        "2003": {
            "Hitter": 0.334,
            "Pitcher": 0.333
        },
        "2004": {
            "Hitter": 0.336,
            "Pitcher": 0.334
        },
        "2005": {
            "Hitter": 0.332,
            "Pitcher": 0.332
        },
        "2006": {
            "Hitter": 0.338,
            "Pitcher": 0.334
        },
        "2007": {
            "Hitter": 0.337,
            "Pitcher": 0.334
        },
        "2008": {
            "Hitter": 0.335,
            "Pitcher": 0.329
        },
        "2009": {
            "Hitter": 0.334,
            "Pitcher": 0.33
        },
        "2010": {
            "Hitter": 0.328,
            "Pitcher": 0.325
        },
        "2011": {
            "Hitter": 0.324,
            "Pitcher": 0.318
        },
        "2012": {
            "Hitter": 0.322,
            "Pitcher": 0.316
        },
        "2013": {
            "Hitter": 0.321,
            "Pitcher": 0.314
        },
        "2014": {
            "Hitter": 0.317,
            "Pitcher": 0.309
        },
        "2015": {
            "Hitter": 0.321,
            "Pitcher": 0.315
        },
        "2016": {
            "Hitter": 0.324,
            "Pitcher": 0.318
        },
        "2017": {
            "Hitter": 0.328,
            "Pitcher": 0.321
        },
        "2018": {
            "Hitter": 0.322,
            "Pitcher": 0.316
        },
        "2019": {
            "Hitter": 0.326,
            "Pitcher": 0.321
        },
        "2020": {
            "Hitter": 0.324,
            "Pitcher": 0.311
        },
        "2021": {
            "Hitter": 0.322,
            "Pitcher": 0.313
        },
        "2022": {
            "Hitter": 0.313,
            "Pitcher": 0.306
        }
    },
    "2005": {
        "1900": {
            "Hitter": 0.338,
            "Pitcher": 0.333
        },
        "1901": {
            "Hitter": 0.325,
            "Pitcher": 0.378
        },
        "1902": {
            "Hitter": 0.32,
            "Pitcher": 0.363
        },
        "1903": {
            "Hitter": 0.317,
            "Pitcher": 0.346
        },
        "1904": {
            "Hitter": 0.301,
            "Pitcher": 0.324
        },
        "1905": {
            "Hitter": 0.31,
            "Pitcher": 0.342
        },
        "1906": {
            "Hitter": 0.309,
            "Pitcher": 0.34
        },
        "1907": {
            "Hitter": 0.308,
            "Pitcher": 0.348
        },
        "1908": {
            "Hitter": 0.301,
            "Pitcher": 0.317
        },
        "1909": {
            "Hitter": 0.312,
            "Pitcher": 0.318
        },
        "1910": {
            "Hitter": 0.32,
            "Pitcher": 0.339
        },
        "1911": {
            "Hitter": 0.339,
            "Pitcher": 0.346
        },
        "1912": {
            "Hitter": 0.34,
            "Pitcher": 0.357
        },
        "1913": {
            "Hitter": 0.327,
            "Pitcher": 0.342
        },
        "1914": {
            "Hitter": 0.324,
            "Pitcher": 0.356
        },
        "1915": {
            "Hitter": 0.32,
            "Pitcher": 0.343
        },
        "1916": {
            "Hitter": 0.316,
            "Pitcher": 0.323
        },
        "1917": {
            "Hitter": 0.314,
            "Pitcher": 0.322
        },
        "1918": {
            "Hitter": 0.32,
            "Pitcher": 0.329
        },
        "1919": {
            "Hitter": 0.325,
            "Pitcher": 0.337
        },
        "1920": {
            "Hitter": 0.329,
            "Pitcher": 0.343
        },
        "1921": {
            "Hitter": 0.341,
            "Pitcher": 0.344
        },
        "1922": {
            "Hitter": 0.347,
            "Pitcher": 0.351
        },
        "1923": {
            "Hitter": 0.342,
            "Pitcher": 0.351
        },
        "1924": {
            "Hitter": 0.341,
            "Pitcher": 0.35
        },
        "1925": {
            "Hitter": 0.348,
            "Pitcher": 0.352
        },
        "1926": {
            "Hitter": 0.345,
            "Pitcher": 0.35
        },
        "1927": {
            "Hitter": 0.345,
            "Pitcher": 0.35
        },
        "1928": {
            "Hitter": 0.344,
            "Pitcher": 0.344
        },
        "1929": {
            "Hitter": 0.352,
            "Pitcher": 0.358
        },
        "1930": {
            "Hitter": 0.346,
            "Pitcher": 0.358
        },
        "1931": {
            "Hitter": 0.341,
            "Pitcher": 0.354
        },
        "1932": {
            "Hitter": 0.329,
            "Pitcher": 0.337
        },
        "1933": {
            "Hitter": 0.329,
            "Pitcher": 0.34
        },
        "1934": {
            "Hitter": 0.34,
            "Pitcher": 0.351
        },
        "1935": {
            "Hitter": 0.348,
            "Pitcher": 0.355
        },
        "1936": {
            "Hitter": 0.351,
            "Pitcher": 0.357
        },
        "1937": {
            "Hitter": 0.344,
            "Pitcher": 0.345
        },
        "1938": {
            "Hitter": 0.34,
            "Pitcher": 0.343
        },
        "1939": {
            "Hitter": 0.339,
            "Pitcher": 0.343
        },
        "1940": {
            "Hitter": 0.337,
            "Pitcher": 0.345
        },
        "1941": {
            "Hitter": 0.33,
            "Pitcher": 0.336
        },
        "1942": {
            "Hitter": 0.323,
            "Pitcher": 0.328
        },
        "1943": {
            "Hitter": 0.328,
            "Pitcher": 0.331
        },
        "1944": {
            "Hitter": 0.33,
            "Pitcher": 0.336
        },
        "1945": {
            "Hitter": 0.332,
            "Pitcher": 0.333
        },
        "1946": {
            "Hitter": 0.336,
            "Pitcher": 0.34
        },
        "1947": {
            "Hitter": 0.343,
            "Pitcher": 0.343
        },
        "1948": {
            "Hitter": 0.341,
            "Pitcher": 0.348
        },
        "1949": {
            "Hitter": 0.347,
            "Pitcher": 0.355
        },
        "1950": {
            "Hitter": 0.349,
            "Pitcher": 0.362
        },
        "1951": {
            "Hitter": 0.337,
            "Pitcher": 0.352
        },
        "1952": {
            "Hitter": 0.331,
            "Pitcher": 0.343
        },
        "1953": {
            "Hitter": 0.342,
            "Pitcher": 0.35
        },
        "1954": {
            "Hitter": 0.337,
            "Pitcher": 0.348
        },
        "1955": {
            "Hitter": 0.336,
            "Pitcher": 0.345
        },
        "1956": {
            "Hitter": 0.335,
            "Pitcher": 0.346
        },
        "1957": {
            "Hitter": 0.329,
            "Pitcher": 0.338
        },
        "1958": {
            "Hitter": 0.329,
            "Pitcher": 0.339
        },
        "1959": {
            "Hitter": 0.329,
            "Pitcher": 0.344
        },
        "1960": {
            "Hitter": 0.33,
            "Pitcher": 0.34
        },
        "1961": {
            "Hitter": 0.333,
            "Pitcher": 0.342
        },
        "1962": {
            "Hitter": 0.334,
            "Pitcher": 0.337
        },
        "1963": {
            "Hitter": 0.317,
            "Pitcher": 0.328
        },
        "1964": {
            "Hitter": 0.318,
            "Pitcher": 0.323
        },
        "1965": {
            "Hitter": 0.317,
            "Pitcher": 0.323
        },
        "1966": {
            "Hitter": 0.315,
            "Pitcher": 0.32
        },
        "1967": {
            "Hitter": 0.312,
            "Pitcher": 0.32
        },
        "1968": {
            "Hitter": 0.306,
            "Pitcher": 0.313
        },
        "1969": {
            "Hitter": 0.325,
            "Pitcher": 0.334
        },
        "1970": {
            "Hitter": 0.332,
            "Pitcher": 0.337
        },
        "1971": {
            "Hitter": 0.323,
            "Pitcher": 0.329
        },
        "1972": {
            "Hitter": 0.316,
            "Pitcher": 0.325
        },
        "1973": {
            "Hitter": 0.326,
            "Pitcher": 0.339
        },
        "1974": {
            "Hitter": 0.324,
            "Pitcher": 0.335
        },
        "1975": {
            "Hitter": 0.33,
            "Pitcher": 0.335
        },
        "1976": {
            "Hitter": 0.322,
            "Pitcher": 0.328
        },
        "1977": {
            "Hitter": 0.33,
            "Pitcher": 0.338
        },
        "1978": {
            "Hitter": 0.324,
            "Pitcher": 0.332
        },
        "1979": {
            "Hitter": 0.332,
            "Pitcher": 0.338
        },
        "1980": {
            "Hitter": 0.328,
            "Pitcher": 0.335
        },
        "1981": {
            "Hitter": 0.321,
            "Pitcher": 0.328
        },
        "1982": {
            "Hitter": 0.327,
            "Pitcher": 0.33
        },
        "1983": {
            "Hitter": 0.328,
            "Pitcher": 0.333
        },
        "1984": {
            "Hitter": 0.326,
            "Pitcher": 0.328
        },
        "1985": {
            "Hitter": 0.325,
            "Pitcher": 0.332
        },
        "1986": {
            "Hitter": 0.328,
            "Pitcher": 0.335
        },
        "1987": {
            "Hitter": 0.334,
            "Pitcher": 0.339
        },
        "1988": {
            "Hitter": 0.32,
            "Pitcher": 0.327
        },
        "1989": {
            "Hitter": 0.321,
            "Pitcher": 0.326
        },
        "1990": {
            "Hitter": 0.327,
            "Pitcher": 0.327
        },
        "1991": {
            "Hitter": 0.326,
            "Pitcher": 0.325
        },
        "1992": {
            "Hitter": 0.323,
            "Pitcher": 0.327
        },
        "1993": {
            "Hitter": 0.333,
            "Pitcher": 0.335
        },
        "1994": {
            "Hitter": 0.34,
            "Pitcher": 0.345
        },
        "1995": {
            "Hitter": 0.339,
            "Pitcher": 0.341
        },
        "1996": {
            "Hitter": 0.342,
            "Pitcher": 0.344
        },
        "1997": {
            "Hitter": 0.339,
            "Pitcher": 0.341
        },
        "1998": {
            "Hitter": 0.335,
            "Pitcher": 0.338
        },
        "1999": {
            "Hitter": 0.345,
            "Pitcher": 0.347
        },
        "2000": {
            "Hitter": 0.345,
            "Pitcher": 0.348
        },
        "2001": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "2002": {
            "Hitter": 0.332,
            "Pitcher": 0.332
        },
        "2003": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "2004": {
            "Hitter": 0.335,
            "Pitcher": 0.335
        },
        "2005": {
            "Hitter": 0.332,
            "Pitcher": 0.332
        },
        "2006": {
            "Hitter": 0.337,
            "Pitcher": 0.334
        },
        "2007": {
            "Hitter": 0.337,
            "Pitcher": 0.334
        },
        "2008": {
            "Hitter": 0.335,
            "Pitcher": 0.331
        },
        "2009": {
            "Hitter": 0.334,
            "Pitcher": 0.331
        },
        "2010": {
            "Hitter": 0.328,
            "Pitcher": 0.326
        },
        "2011": {
            "Hitter": 0.323,
            "Pitcher": 0.319
        },
        "2012": {
            "Hitter": 0.321,
            "Pitcher": 0.317
        },
        "2013": {
            "Hitter": 0.32,
            "Pitcher": 0.315
        },
        "2014": {
            "Hitter": 0.316,
            "Pitcher": 0.31
        },
        "2015": {
            "Hitter": 0.32,
            "Pitcher": 0.316
        },
        "2016": {
            "Hitter": 0.324,
            "Pitcher": 0.319
        },
        "2017": {
            "Hitter": 0.327,
            "Pitcher": 0.321
        },
        "2018": {
            "Hitter": 0.32,
            "Pitcher": 0.317
        },
        "2019": {
            "Hitter": 0.325,
            "Pitcher": 0.322
        },
        "2020": {
            "Hitter": 0.321,
            "Pitcher": 0.311
        },
        "2021": {
            "Hitter": 0.321,
            "Pitcher": 0.313
        },
        "2022": {
            "Hitter": 0.311,
            "Pitcher": 0.308
        }
    },
    CLASSIC_SET: {
        "1900": {
            "Hitter": 0.335,
            "Pitcher": 0.332
        },
        "1901": {
            "Hitter": 0.32,
            "Pitcher": 0.373
        },
        "1902": {
            "Hitter": 0.315,
            "Pitcher": 0.36
        },
        "1903": {
            "Hitter": 0.311,
            "Pitcher": 0.343
        },
        "1904": {
            "Hitter": 0.296,
            "Pitcher": 0.323
        },
        "1905": {
            "Hitter": 0.305,
            "Pitcher": 0.339
        },
        "1906": {
            "Hitter": 0.303,
            "Pitcher": 0.339
        },
        "1907": {
            "Hitter": 0.303,
            "Pitcher": 0.345
        },
        "1908": {
            "Hitter": 0.296,
            "Pitcher": 0.317
        },
        "1909": {
            "Hitter": 0.306,
            "Pitcher": 0.319
        },
        "1910": {
            "Hitter": 0.315,
            "Pitcher": 0.339
        },
        "1911": {
            "Hitter": 0.336,
            "Pitcher": 0.347
        },
        "1912": {
            "Hitter": 0.337,
            "Pitcher": 0.355
        },
        "1913": {
            "Hitter": 0.324,
            "Pitcher": 0.339
        },
        "1914": {
            "Hitter": 0.321,
            "Pitcher": 0.349
        },
        "1915": {
            "Hitter": 0.317,
            "Pitcher": 0.339
        },
        "1916": {
            "Hitter": 0.312,
            "Pitcher": 0.323
        },
        "1917": {
            "Hitter": 0.309,
            "Pitcher": 0.322
        },
        "1918": {
            "Hitter": 0.315,
            "Pitcher": 0.326
        },
        "1919": {
            "Hitter": 0.321,
            "Pitcher": 0.335
        },
        "1920": {
            "Hitter": 0.325,
            "Pitcher": 0.34
        },
        "1921": {
            "Hitter": 0.338,
            "Pitcher": 0.341
        },
        "1922": {
            "Hitter": 0.344,
            "Pitcher": 0.348
        },
        "1923": {
            "Hitter": 0.339,
            "Pitcher": 0.346
        },
        "1924": {
            "Hitter": 0.338,
            "Pitcher": 0.348
        },
        "1925": {
            "Hitter": 0.345,
            "Pitcher": 0.349
        },
        "1926": {
            "Hitter": 0.342,
            "Pitcher": 0.347
        },
        "1927": {
            "Hitter": 0.341,
            "Pitcher": 0.346
        },
        "1928": {
            "Hitter": 0.341,
            "Pitcher": 0.34
        },
        "1929": {
            "Hitter": 0.35,
            "Pitcher": 0.354
        },
        "1930": {
            "Hitter": 0.343,
            "Pitcher": 0.354
        },
        "1931": {
            "Hitter": 0.339,
            "Pitcher": 0.35
        },
        "1932": {
            "Hitter": 0.323,
            "Pitcher": 0.334
        },
        "1933": {
            "Hitter": 0.324,
            "Pitcher": 0.338
        },
        "1934": {
            "Hitter": 0.335,
            "Pitcher": 0.349
        },
        "1935": {
            "Hitter": 0.346,
            "Pitcher": 0.352
        },
        "1936": {
            "Hitter": 0.348,
            "Pitcher": 0.354
        },
        "1937": {
            "Hitter": 0.341,
            "Pitcher": 0.342
        },
        "1938": {
            "Hitter": 0.336,
            "Pitcher": 0.34
        },
        "1939": {
            "Hitter": 0.335,
            "Pitcher": 0.339
        },
        "1940": {
            "Hitter": 0.332,
            "Pitcher": 0.341
        },
        "1941": {
            "Hitter": 0.324,
            "Pitcher": 0.334
        },
        "1942": {
            "Hitter": 0.318,
            "Pitcher": 0.327
        },
        "1943": {
            "Hitter": 0.323,
            "Pitcher": 0.331
        },
        "1944": {
            "Hitter": 0.326,
            "Pitcher": 0.334
        },
        "1945": {
            "Hitter": 0.328,
            "Pitcher": 0.332
        },
        "1946": {
            "Hitter": 0.331,
            "Pitcher": 0.337
        },
        "1947": {
            "Hitter": 0.338,
            "Pitcher": 0.341
        },
        "1948": {
            "Hitter": 0.337,
            "Pitcher": 0.346
        },
        "1949": {
            "Hitter": 0.345,
            "Pitcher": 0.351
        },
        "1950": {
            "Hitter": 0.349,
            "Pitcher": 0.357
        },
        "1951": {
            "Hitter": 0.335,
            "Pitcher": 0.348
        },
        "1952": {
            "Hitter": 0.33,
            "Pitcher": 0.34
        },
        "1953": {
            "Hitter": 0.341,
            "Pitcher": 0.347
        },
        "1954": {
            "Hitter": 0.336,
            "Pitcher": 0.344
        },
        "1955": {
            "Hitter": 0.335,
            "Pitcher": 0.341
        },
        "1956": {
            "Hitter": 0.334,
            "Pitcher": 0.343
        },
        "1957": {
            "Hitter": 0.328,
            "Pitcher": 0.337
        },
        "1958": {
            "Hitter": 0.329,
            "Pitcher": 0.337
        },
        "1959": {
            "Hitter": 0.329,
            "Pitcher": 0.341
        },
        "1960": {
            "Hitter": 0.329,
            "Pitcher": 0.337
        },
        "1961": {
            "Hitter": 0.331,
            "Pitcher": 0.34
        },
        "1962": {
            "Hitter": 0.333,
            "Pitcher": 0.335
        },
        "1963": {
            "Hitter": 0.315,
            "Pitcher": 0.326
        },
        "1964": {
            "Hitter": 0.316,
            "Pitcher": 0.321
        },
        "1965": {
            "Hitter": 0.316,
            "Pitcher": 0.321
        },
        "1966": {
            "Hitter": 0.313,
            "Pitcher": 0.319
        },
        "1967": {
            "Hitter": 0.31,
            "Pitcher": 0.318
        },
        "1968": {
            "Hitter": 0.303,
            "Pitcher": 0.313
        },
        "1969": {
            "Hitter": 0.325,
            "Pitcher": 0.332
        },
        "1970": {
            "Hitter": 0.332,
            "Pitcher": 0.336
        },
        "1971": {
            "Hitter": 0.321,
            "Pitcher": 0.327
        },
        "1972": {
            "Hitter": 0.314,
            "Pitcher": 0.324
        },
        "1973": {
            "Hitter": 0.325,
            "Pitcher": 0.336
        },
        "1974": {
            "Hitter": 0.323,
            "Pitcher": 0.334
        },
        "1975": {
            "Hitter": 0.329,
            "Pitcher": 0.333
        },
        "1976": {
            "Hitter": 0.322,
            "Pitcher": 0.327
        },
        "1977": {
            "Hitter": 0.329,
            "Pitcher": 0.337
        },
        "1978": {
            "Hitter": 0.324,
            "Pitcher": 0.33
        },
        "1979": {
            "Hitter": 0.331,
            "Pitcher": 0.337
        },
        "1980": {
            "Hitter": 0.328,
            "Pitcher": 0.333
        },
        "1981": {
            "Hitter": 0.319,
            "Pitcher": 0.327
        },
        "1982": {
            "Hitter": 0.326,
            "Pitcher": 0.329
        },
        "1983": {
            "Hitter": 0.327,
            "Pitcher": 0.331
        },
        "1984": {
            "Hitter": 0.325,
            "Pitcher": 0.328
        },
        "1985": {
            "Hitter": 0.325,
            "Pitcher": 0.33
        },
        "1986": {
            "Hitter": 0.327,
            "Pitcher": 0.334
        },
        "1987": {
            "Hitter": 0.333,
            "Pitcher": 0.338
        },
        "1988": {
            "Hitter": 0.318,
            "Pitcher": 0.326
        },
        "1989": {
            "Hitter": 0.32,
            "Pitcher": 0.325
        },
        "1990": {
            "Hitter": 0.326,
            "Pitcher": 0.328
        },
        "1991": {
            "Hitter": 0.325,
            "Pitcher": 0.325
        },
        "1992": {
            "Hitter": 0.323,
            "Pitcher": 0.326
        },
        "1993": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "1994": {
            "Hitter": 0.339,
            "Pitcher": 0.342
        },
        "1995": {
            "Hitter": 0.338,
            "Pitcher": 0.339
        },
        "1996": {
            "Hitter": 0.341,
            "Pitcher": 0.342
        },
        "1997": {
            "Hitter": 0.339,
            "Pitcher": 0.339
        },
        "1998": {
            "Hitter": 0.334,
            "Pitcher": 0.337
        },
        "1999": {
            "Hitter": 0.346,
            "Pitcher": 0.346
        },
        "2000": {
            "Hitter": 0.346,
            "Pitcher": 0.346
        },
        "2001": {
            "Hitter": 0.334,
            "Pitcher": 0.332
        },
        "2002": {
            "Hitter": 0.332,
            "Pitcher": 0.331
        },
        "2003": {
            "Hitter": 0.334,
            "Pitcher": 0.333
        },
        "2004": {
            "Hitter": 0.335,
            "Pitcher": 0.334
        },
        "2005": {
            "Hitter": 0.332,
            "Pitcher": 0.331
        },
        "2006": {
            "Hitter": 0.338,
            "Pitcher": 0.333
        },
        "2007": {
            "Hitter": 0.336,
            "Pitcher": 0.334
        },
        "2008": {
            "Hitter": 0.335,
            "Pitcher": 0.329
        },
        "2009": {
            "Hitter": 0.334,
            "Pitcher": 0.331
        },
        "2010": {
            "Hitter": 0.326,
            "Pitcher": 0.325
        },
        "2011": {
            "Hitter": 0.322,
            "Pitcher": 0.318
        },
        "2012": {
            "Hitter": 0.32,
            "Pitcher": 0.317
        },
        "2013": {
            "Hitter": 0.319,
            "Pitcher": 0.315
        },
        "2014": {
            "Hitter": 0.315,
            "Pitcher": 0.311
        },
        "2015": {
            "Hitter": 0.319,
            "Pitcher": 0.315
        },
        "2016": {
            "Hitter": 0.323,
            "Pitcher": 0.318
        },
        "2017": {
            "Hitter": 0.327,
            "Pitcher": 0.321
        },
        "2018": {
            "Hitter": 0.32,
            "Pitcher": 0.316
        },
        "2019": {
            "Hitter": 0.325,
            "Pitcher": 0.321
        },
        "2020": {
            "Hitter": 0.317,
            "Pitcher": 0.311
        },
        "2021": {
            "Hitter": 0.321,
            "Pitcher": 0.313
        },
        "2022": {
            "Hitter": 0.311,
            "Pitcher": 0.307
        }
    },
    EXPANDED_SET: {
        "1900": {
            "Hitter": 0.335,
            "Pitcher": 0.33
        },
        "1901": {
            "Hitter": 0.319,
            "Pitcher": 0.376
        },
        "1902": {
            "Hitter": 0.315,
            "Pitcher": 0.362
        },
        "1903": {
            "Hitter": 0.313,
            "Pitcher": 0.344
        },
        "1904": {
            "Hitter": 0.296,
            "Pitcher": 0.323
        },
        "1905": {
            "Hitter": 0.305,
            "Pitcher": 0.342
        },
        "1906": {
            "Hitter": 0.303,
            "Pitcher": 0.34
        },
        "1907": {
            "Hitter": 0.302,
            "Pitcher": 0.348
        },
        "1908": {
            "Hitter": 0.295,
            "Pitcher": 0.317
        },
        "1909": {
            "Hitter": 0.306,
            "Pitcher": 0.318
        },
        "1910": {
            "Hitter": 0.315,
            "Pitcher": 0.337
        },
        "1911": {
            "Hitter": 0.334,
            "Pitcher": 0.345
        },
        "1912": {
            "Hitter": 0.335,
            "Pitcher": 0.358
        },
        "1913": {
            "Hitter": 0.323,
            "Pitcher": 0.341
        },
        "1914": {
            "Hitter": 0.32,
            "Pitcher": 0.356
        },
        "1915": {
            "Hitter": 0.316,
            "Pitcher": 0.341
        },
        "1916": {
            "Hitter": 0.312,
            "Pitcher": 0.324
        },
        "1917": {
            "Hitter": 0.309,
            "Pitcher": 0.32
        },
        "1918": {
            "Hitter": 0.314,
            "Pitcher": 0.328
        },
        "1919": {
            "Hitter": 0.32,
            "Pitcher": 0.335
        },
        "1920": {
            "Hitter": 0.324,
            "Pitcher": 0.344
        },
        "1921": {
            "Hitter": 0.337,
            "Pitcher": 0.342
        },
        "1922": {
            "Hitter": 0.343,
            "Pitcher": 0.348
        },
        "1923": {
            "Hitter": 0.338,
            "Pitcher": 0.35
        },
        "1924": {
            "Hitter": 0.337,
            "Pitcher": 0.348
        },
        "1925": {
            "Hitter": 0.345,
            "Pitcher": 0.351
        },
        "1926": {
            "Hitter": 0.341,
            "Pitcher": 0.35
        },
        "1927": {
            "Hitter": 0.34,
            "Pitcher": 0.349
        },
        "1928": {
            "Hitter": 0.339,
            "Pitcher": 0.343
        },
        "1929": {
            "Hitter": 0.348,
            "Pitcher": 0.356
        },
        "1930": {
            "Hitter": 0.343,
            "Pitcher": 0.358
        },
        "1931": {
            "Hitter": 0.338,
            "Pitcher": 0.353
        },
        "1932": {
            "Hitter": 0.324,
            "Pitcher": 0.337
        },
        "1933": {
            "Hitter": 0.324,
            "Pitcher": 0.339
        },
        "1934": {
            "Hitter": 0.336,
            "Pitcher": 0.35
        },
        "1935": {
            "Hitter": 0.345,
            "Pitcher": 0.354
        },
        "1936": {
            "Hitter": 0.348,
            "Pitcher": 0.356
        },
        "1937": {
            "Hitter": 0.34,
            "Pitcher": 0.346
        },
        "1938": {
            "Hitter": 0.335,
            "Pitcher": 0.342
        },
        "1939": {
            "Hitter": 0.335,
            "Pitcher": 0.342
        },
        "1940": {
            "Hitter": 0.333,
            "Pitcher": 0.343
        },
        "1941": {
            "Hitter": 0.325,
            "Pitcher": 0.336
        },
        "1942": {
            "Hitter": 0.318,
            "Pitcher": 0.327
        },
        "1943": {
            "Hitter": 0.323,
            "Pitcher": 0.33
        },
        "1944": {
            "Hitter": 0.326,
            "Pitcher": 0.334
        },
        "1945": {
            "Hitter": 0.328,
            "Pitcher": 0.33
        },
        "1946": {
            "Hitter": 0.331,
            "Pitcher": 0.338
        },
        "1947": {
            "Hitter": 0.339,
            "Pitcher": 0.343
        },
        "1948": {
            "Hitter": 0.337,
            "Pitcher": 0.348
        },
        "1949": {
            "Hitter": 0.344,
            "Pitcher": 0.353
        },
        "1950": {
            "Hitter": 0.347,
            "Pitcher": 0.362
        },
        "1951": {
            "Hitter": 0.334,
            "Pitcher": 0.35
        },
        "1952": {
            "Hitter": 0.329,
            "Pitcher": 0.343
        },
        "1953": {
            "Hitter": 0.34,
            "Pitcher": 0.35
        },
        "1954": {
            "Hitter": 0.335,
            "Pitcher": 0.347
        },
        "1955": {
            "Hitter": 0.334,
            "Pitcher": 0.344
        },
        "1956": {
            "Hitter": 0.333,
            "Pitcher": 0.346
        },
        "1957": {
            "Hitter": 0.326,
            "Pitcher": 0.337
        },
        "1958": {
            "Hitter": 0.326,
            "Pitcher": 0.339
        },
        "1959": {
            "Hitter": 0.327,
            "Pitcher": 0.344
        },
        "1960": {
            "Hitter": 0.327,
            "Pitcher": 0.339
        },
        "1961": {
            "Hitter": 0.33,
            "Pitcher": 0.341
        },
        "1962": {
            "Hitter": 0.331,
            "Pitcher": 0.336
        },
        "1963": {
            "Hitter": 0.314,
            "Pitcher": 0.327
        },
        "1964": {
            "Hitter": 0.315,
            "Pitcher": 0.323
        },
        "1965": {
            "Hitter": 0.315,
            "Pitcher": 0.323
        },
        "1966": {
            "Hitter": 0.312,
            "Pitcher": 0.32
        },
        "1967": {
            "Hitter": 0.309,
            "Pitcher": 0.319
        },
        "1968": {
            "Hitter": 0.303,
            "Pitcher": 0.313
        },
        "1969": {
            "Hitter": 0.323,
            "Pitcher": 0.333
        },
        "1970": {
            "Hitter": 0.331,
            "Pitcher": 0.336
        },
        "1971": {
            "Hitter": 0.32,
            "Pitcher": 0.328
        },
        "1972": {
            "Hitter": 0.313,
            "Pitcher": 0.324
        },
        "1973": {
            "Hitter": 0.323,
            "Pitcher": 0.338
        },
        "1974": {
            "Hitter": 0.322,
            "Pitcher": 0.334
        },
        "1975": {
            "Hitter": 0.327,
            "Pitcher": 0.334
        },
        "1976": {
            "Hitter": 0.32,
            "Pitcher": 0.327
        },
        "1977": {
            "Hitter": 0.327,
            "Pitcher": 0.338
        },
        "1978": {
            "Hitter": 0.323,
            "Pitcher": 0.331
        },
        "1979": {
            "Hitter": 0.33,
            "Pitcher": 0.337
        },
        "1980": {
            "Hitter": 0.326,
            "Pitcher": 0.335
        },
        "1981": {
            "Hitter": 0.318,
            "Pitcher": 0.327
        },
        "1982": {
            "Hitter": 0.324,
            "Pitcher": 0.329
        },
        "1983": {
            "Hitter": 0.326,
            "Pitcher": 0.332
        },
        "1984": {
            "Hitter": 0.323,
            "Pitcher": 0.327
        },
        "1985": {
            "Hitter": 0.323,
            "Pitcher": 0.331
        },
        "1986": {
            "Hitter": 0.326,
            "Pitcher": 0.334
        },
        "1987": {
            "Hitter": 0.332,
            "Pitcher": 0.338
        },
        "1988": {
            "Hitter": 0.317,
            "Pitcher": 0.325
        },
        "1989": {
            "Hitter": 0.318,
            "Pitcher": 0.325
        },
        "1990": {
            "Hitter": 0.325,
            "Pitcher": 0.326
        },
        "1991": {
            "Hitter": 0.323,
            "Pitcher": 0.325
        },
        "1992": {
            "Hitter": 0.321,
            "Pitcher": 0.325
        },
        "1993": {
            "Hitter": 0.331,
            "Pitcher": 0.335
        },
        "1994": {
            "Hitter": 0.338,
            "Pitcher": 0.344
        },
        "1995": {
            "Hitter": 0.337,
            "Pitcher": 0.341
        },
        "1996": {
            "Hitter": 0.34,
            "Pitcher": 0.343
        },
        "1997": {
            "Hitter": 0.336,
            "Pitcher": 0.341
        },
        "1998": {
            "Hitter": 0.333,
            "Pitcher": 0.337
        },
        "1999": {
            "Hitter": 0.344,
            "Pitcher": 0.347
        },
        "2000": {
            "Hitter": 0.344,
            "Pitcher": 0.346
        },
        "2001": {
            "Hitter": 0.333,
            "Pitcher": 0.333
        },
        "2002": {
            "Hitter": 0.331,
            "Pitcher": 0.331
        },
        "2003": {
            "Hitter": 0.332,
            "Pitcher": 0.333
        },
        "2004": {
            "Hitter": 0.334,
            "Pitcher": 0.334
        },
        "2005": {
            "Hitter": 0.33,
            "Pitcher": 0.332
        },
        "2006": {
            "Hitter": 0.336,
            "Pitcher": 0.334
        },
        "2007": {
            "Hitter": 0.335,
            "Pitcher": 0.334
        },
        "2008": {
            "Hitter": 0.333,
            "Pitcher": 0.33
        },
        "2009": {
            "Hitter": 0.332,
            "Pitcher": 0.33
        },
        "2010": {
            "Hitter": 0.325,
            "Pitcher": 0.325
        },
        "2011": {
            "Hitter": 0.321,
            "Pitcher": 0.318
        },
        "2012": {
            "Hitter": 0.319,
            "Pitcher": 0.316
        },
        "2013": {
            "Hitter": 0.317,
            "Pitcher": 0.315
        },
        "2014": {
            "Hitter": 0.314,
            "Pitcher": 0.309
        },
        "2015": {
            "Hitter": 0.318,
            "Pitcher": 0.315
        },
        "2016": {
            "Hitter": 0.322,
            "Pitcher": 0.317
        },
        "2017": {
            "Hitter": 0.326,
            "Pitcher": 0.32
        },
        "2018": {
            "Hitter": 0.319,
            "Pitcher": 0.316
        },
        "2019": {
            "Hitter": 0.323,
            "Pitcher": 0.321
        },
        "2020": {
            "Hitter": 0.317,
            "Pitcher": 0.311
        },
        "2021": {
            "Hitter": 0.319,
            "Pitcher": 0.313
        },
        "2022": {
            "Hitter": 0.309,
            "Pitcher": 0.307
        }
    }
}

LEAGUE_AVG_PROJ_SLG = {
    "2000": {
        "1900": {
            "Hitter": 0.355,
            "Pitcher": 0.363
        },
        "1901": {
            "Hitter": 0.348,
            "Pitcher": 0.418
        },
        "1902": {
            "Hitter": 0.334,
            "Pitcher": 0.394
        },
        "1903": {
            "Hitter": 0.334,
            "Pitcher": 0.366
        },
        "1904": {
            "Hitter": 0.314,
            "Pitcher": 0.338
        },
        "1905": {
            "Hitter": 0.316,
            "Pitcher": 0.357
        },
        "1906": {
            "Hitter": 0.311,
            "Pitcher": 0.354
        },
        "1907": {
            "Hitter": 0.309,
            "Pitcher": 0.35
        },
        "1908": {
            "Hitter": 0.304,
            "Pitcher": 0.308
        },
        "1909": {
            "Hitter": 0.311,
            "Pitcher": 0.31
        },
        "1910": {
            "Hitter": 0.322,
            "Pitcher": 0.332
        },
        "1911": {
            "Hitter": 0.352,
            "Pitcher": 0.343
        },
        "1912": {
            "Hitter": 0.356,
            "Pitcher": 0.363
        },
        "1913": {
            "Hitter": 0.34,
            "Pitcher": 0.333
        },
        "1914": {
            "Hitter": 0.334,
            "Pitcher": 0.36
        },
        "1915": {
            "Hitter": 0.323,
            "Pitcher": 0.353
        },
        "1916": {
            "Hitter": 0.324,
            "Pitcher": 0.324
        },
        "1917": {
            "Hitter": 0.318,
            "Pitcher": 0.328
        },
        "1918": {
            "Hitter": 0.325,
            "Pitcher": 0.344
        },
        "1919": {
            "Hitter": 0.344,
            "Pitcher": 0.358
        },
        "1920": {
            "Hitter": 0.346,
            "Pitcher": 0.377
        },
        "1921": {
            "Hitter": 0.376,
            "Pitcher": 0.38
        },
        "1922": {
            "Hitter": 0.386,
            "Pitcher": 0.394
        },
        "1923": {
            "Hitter": 0.379,
            "Pitcher": 0.39
        },
        "1924": {
            "Hitter": 0.374,
            "Pitcher": 0.399
        },
        "1925": {
            "Hitter": 0.397,
            "Pitcher": 0.405
        },
        "1926": {
            "Hitter": 0.379,
            "Pitcher": 0.398
        },
        "1927": {
            "Hitter": 0.38,
            "Pitcher": 0.402
        },
        "1928": {
            "Hitter": 0.385,
            "Pitcher": 0.397
        },
        "1929": {
            "Hitter": 0.399,
            "Pitcher": 0.418
        },
        "1930": {
            "Hitter": 0.404,
            "Pitcher": 0.423
        },
        "1931": {
            "Hitter": 0.378,
            "Pitcher": 0.409
        },
        "1932": {
            "Hitter": 0.36,
            "Pitcher": 0.381
        },
        "1933": {
            "Hitter": 0.37,
            "Pitcher": 0.388
        },
        "1934": {
            "Hitter": 0.375,
            "Pitcher": 0.407
        },
        "1935": {
            "Hitter": 0.395,
            "Pitcher": 0.414
        },
        "1936": {
            "Hitter": 0.393,
            "Pitcher": 0.409
        },
        "1937": {
            "Hitter": 0.392,
            "Pitcher": 0.399
        },
        "1938": {
            "Hitter": 0.377,
            "Pitcher": 0.39
        },
        "1939": {
            "Hitter": 0.377,
            "Pitcher": 0.39
        },
        "1940": {
            "Hitter": 0.374,
            "Pitcher": 0.391
        },
        "1941": {
            "Hitter": 0.358,
            "Pitcher": 0.365
        },
        "1942": {
            "Hitter": 0.339,
            "Pitcher": 0.346
        },
        "1943": {
            "Hitter": 0.344,
            "Pitcher": 0.356
        },
        "1944": {
            "Hitter": 0.35,
            "Pitcher": 0.36
        },
        "1945": {
            "Hitter": 0.356,
            "Pitcher": 0.355
        },
        "1946": {
            "Hitter": 0.357,
            "Pitcher": 0.371
        },
        "1947": {
            "Hitter": 0.371,
            "Pitcher": 0.38
        },
        "1948": {
            "Hitter": 0.371,
            "Pitcher": 0.381
        },
        "1949": {
            "Hitter": 0.377,
            "Pitcher": 0.387
        },
        "1950": {
            "Hitter": 0.397,
            "Pitcher": 0.402
        },
        "1951": {
            "Hitter": 0.378,
            "Pitcher": 0.397
        },
        "1952": {
            "Hitter": 0.37,
            "Pitcher": 0.388
        },
        "1953": {
            "Hitter": 0.396,
            "Pitcher": 0.397
        },
        "1954": {
            "Hitter": 0.382,
            "Pitcher": 0.391
        },
        "1955": {
            "Hitter": 0.389,
            "Pitcher": 0.386
        },
        "1956": {
            "Hitter": 0.391,
            "Pitcher": 0.392
        },
        "1957": {
            "Hitter": 0.385,
            "Pitcher": 0.38
        },
        "1958": {
            "Hitter": 0.391,
            "Pitcher": 0.392
        },
        "1959": {
            "Hitter": 0.389,
            "Pitcher": 0.402
        },
        "1960": {
            "Hitter": 0.385,
            "Pitcher": 0.382
        },
        "1961": {
            "Hitter": 0.394,
            "Pitcher": 0.391
        },
        "1962": {
            "Hitter": 0.389,
            "Pitcher": 0.381
        },
        "1963": {
            "Hitter": 0.369,
            "Pitcher": 0.373
        },
        "1964": {
            "Hitter": 0.37,
            "Pitcher": 0.371
        },
        "1965": {
            "Hitter": 0.365,
            "Pitcher": 0.369
        },
        "1966": {
            "Hitter": 0.367,
            "Pitcher": 0.361
        },
        "1967": {
            "Hitter": 0.349,
            "Pitcher": 0.358
        },
        "1968": {
            "Hitter": 0.337,
            "Pitcher": 0.343
        },
        "1969": {
            "Hitter": 0.363,
            "Pitcher": 0.371
        },
        "1970": {
            "Hitter": 0.381,
            "Pitcher": 0.382
        },
        "1971": {
            "Hitter": 0.359,
            "Pitcher": 0.364
        },
        "1972": {
            "Hitter": 0.348,
            "Pitcher": 0.359
        },
        "1973": {
            "Hitter": 0.366,
            "Pitcher": 0.377
        },
        "1974": {
            "Hitter": 0.357,
            "Pitcher": 0.374
        },
        "1975": {
            "Hitter": 0.364,
            "Pitcher": 0.372
        },
        "1976": {
            "Hitter": 0.35,
            "Pitcher": 0.361
        },
        "1977": {
            "Hitter": 0.386,
            "Pitcher": 0.393
        },
        "1978": {
            "Hitter": 0.365,
            "Pitcher": 0.375
        },
        "1979": {
            "Hitter": 0.385,
            "Pitcher": 0.387
        },
        "1980": {
            "Hitter": 0.378,
            "Pitcher": 0.384
        },
        "1981": {
            "Hitter": 0.357,
            "Pitcher": 0.365
        },
        "1982": {
            "Hitter": 0.376,
            "Pitcher": 0.38
        },
        "1983": {
            "Hitter": 0.378,
            "Pitcher": 0.392
        },
        "1984": {
            "Hitter": 0.372,
            "Pitcher": 0.376
        },
        "1985": {
            "Hitter": 0.378,
            "Pitcher": 0.386
        },
        "1986": {
            "Hitter": 0.384,
            "Pitcher": 0.381
        },
        "1987": {
            "Hitter": 0.402,
            "Pitcher": 0.398
        },
        "1988": {
            "Hitter": 0.364,
            "Pitcher": 0.371
        },
        "1989": {
            "Hitter": 0.364,
            "Pitcher": 0.373
        },
        "1990": {
            "Hitter": 0.375,
            "Pitcher": 0.369
        },
        "1991": {
            "Hitter": 0.371,
            "Pitcher": 0.369
        },
        "1992": {
            "Hitter": 0.365,
            "Pitcher": 0.367
        },
        "1993": {
            "Hitter": 0.391,
            "Pitcher": 0.385
        },
        "1994": {
            "Hitter": 0.41,
            "Pitcher": 0.405
        },
        "1995": {
            "Hitter": 0.402,
            "Pitcher": 0.397
        },
        "1996": {
            "Hitter": 0.413,
            "Pitcher": 0.403
        },
        "1997": {
            "Hitter": 0.405,
            "Pitcher": 0.397
        },
        "1998": {
            "Hitter": 0.402,
            "Pitcher": 0.399
        },
        "1999": {
            "Hitter": 0.418,
            "Pitcher": 0.408
        },
        "2000": {
            "Hitter": 0.423,
            "Pitcher": 0.41
        },
        "2001": {
            "Hitter": 0.413,
            "Pitcher": 0.397
        },
        "2002": {
            "Hitter": 0.402,
            "Pitcher": 0.389
        },
        "2003": {
            "Hitter": 0.409,
            "Pitcher": 0.392
        },
        "2004": {
            "Hitter": 0.415,
            "Pitcher": 0.394
        },
        "2005": {
            "Hitter": 0.408,
            "Pitcher": 0.391
        },
        "2006": {
            "Hitter": 0.419,
            "Pitcher": 0.396
        },
        "2007": {
            "Hitter": 0.407,
            "Pitcher": 0.391
        },
        "2008": {
            "Hitter": 0.404,
            "Pitcher": 0.385
        },
        "2009": {
            "Hitter": 0.405,
            "Pitcher": 0.383
        },
        "2010": {
            "Hitter": 0.39,
            "Pitcher": 0.376
        },
        "2011": {
            "Hitter": 0.387,
            "Pitcher": 0.367
        },
        "2012": {
            "Hitter": 0.395,
            "Pitcher": 0.368
        },
        "2013": {
            "Hitter": 0.386,
            "Pitcher": 0.365
        },
        "2014": {
            "Hitter": 0.375,
            "Pitcher": 0.357
        },
        "2015": {
            "Hitter": 0.395,
            "Pitcher": 0.37
        },
        "2016": {
            "Hitter": 0.405,
            "Pitcher": 0.377
        },
        "2017": {
            "Hitter": 0.415,
            "Pitcher": 0.382
        },
        "2018": {
            "Hitter": 0.398,
            "Pitcher": 0.37
        },
        "2019": {
            "Hitter": 0.425,
            "Pitcher": 0.392
        },
        "2020": {
            "Hitter": 0.399,
            "Pitcher": 0.37
        },
        "2021": {
            "Hitter": 0.401,
            "Pitcher": 0.367
        },
        "2022": {
            "Hitter": 0.379,
            "Pitcher": 0.352
        }
    },
    "2001": {
        "1900": {
            "Hitter": 0.365,
            "Pitcher": 0.36
        },
        "1901": {
            "Hitter": 0.358,
            "Pitcher": 0.413
        },
        "1902": {
            "Hitter": 0.346,
            "Pitcher": 0.391
        },
        "1903": {
            "Hitter": 0.348,
            "Pitcher": 0.363
        },
        "1904": {
            "Hitter": 0.326,
            "Pitcher": 0.336
        },
        "1905": {
            "Hitter": 0.329,
            "Pitcher": 0.355
        },
        "1906": {
            "Hitter": 0.324,
            "Pitcher": 0.348
        },
        "1907": {
            "Hitter": 0.322,
            "Pitcher": 0.349
        },
        "1908": {
            "Hitter": 0.316,
            "Pitcher": 0.304
        },
        "1909": {
            "Hitter": 0.324,
            "Pitcher": 0.304
        },
        "1910": {
            "Hitter": 0.335,
            "Pitcher": 0.329
        },
        "1911": {
            "Hitter": 0.364,
            "Pitcher": 0.341
        },
        "1912": {
            "Hitter": 0.368,
            "Pitcher": 0.358
        },
        "1913": {
            "Hitter": 0.353,
            "Pitcher": 0.33
        },
        "1914": {
            "Hitter": 0.347,
            "Pitcher": 0.357
        },
        "1915": {
            "Hitter": 0.336,
            "Pitcher": 0.352
        },
        "1916": {
            "Hitter": 0.337,
            "Pitcher": 0.323
        },
        "1917": {
            "Hitter": 0.33,
            "Pitcher": 0.328
        },
        "1918": {
            "Hitter": 0.337,
            "Pitcher": 0.341
        },
        "1919": {
            "Hitter": 0.356,
            "Pitcher": 0.356
        },
        "1920": {
            "Hitter": 0.359,
            "Pitcher": 0.375
        },
        "1921": {
            "Hitter": 0.389,
            "Pitcher": 0.381
        },
        "1922": {
            "Hitter": 0.399,
            "Pitcher": 0.391
        },
        "1923": {
            "Hitter": 0.393,
            "Pitcher": 0.39
        },
        "1924": {
            "Hitter": 0.387,
            "Pitcher": 0.398
        },
        "1925": {
            "Hitter": 0.41,
            "Pitcher": 0.404
        },
        "1926": {
            "Hitter": 0.39,
            "Pitcher": 0.398
        },
        "1927": {
            "Hitter": 0.391,
            "Pitcher": 0.402
        },
        "1928": {
            "Hitter": 0.397,
            "Pitcher": 0.399
        },
        "1929": {
            "Hitter": 0.41,
            "Pitcher": 0.42
        },
        "1930": {
            "Hitter": 0.416,
            "Pitcher": 0.423
        },
        "1931": {
            "Hitter": 0.391,
            "Pitcher": 0.409
        },
        "1932": {
            "Hitter": 0.373,
            "Pitcher": 0.381
        },
        "1933": {
            "Hitter": 0.382,
            "Pitcher": 0.389
        },
        "1934": {
            "Hitter": 0.386,
            "Pitcher": 0.408
        },
        "1935": {
            "Hitter": 0.405,
            "Pitcher": 0.414
        },
        "1936": {
            "Hitter": 0.403,
            "Pitcher": 0.408
        },
        "1937": {
            "Hitter": 0.403,
            "Pitcher": 0.399
        },
        "1938": {
            "Hitter": 0.387,
            "Pitcher": 0.391
        },
        "1939": {
            "Hitter": 0.389,
            "Pitcher": 0.39
        },
        "1940": {
            "Hitter": 0.386,
            "Pitcher": 0.392
        },
        "1941": {
            "Hitter": 0.369,
            "Pitcher": 0.363
        },
        "1942": {
            "Hitter": 0.349,
            "Pitcher": 0.347
        },
        "1943": {
            "Hitter": 0.357,
            "Pitcher": 0.356
        },
        "1944": {
            "Hitter": 0.362,
            "Pitcher": 0.358
        },
        "1945": {
            "Hitter": 0.368,
            "Pitcher": 0.354
        },
        "1946": {
            "Hitter": 0.369,
            "Pitcher": 0.37
        },
        "1947": {
            "Hitter": 0.383,
            "Pitcher": 0.381
        },
        "1948": {
            "Hitter": 0.382,
            "Pitcher": 0.38
        },
        "1949": {
            "Hitter": 0.389,
            "Pitcher": 0.389
        },
        "1950": {
            "Hitter": 0.41,
            "Pitcher": 0.404
        },
        "1951": {
            "Hitter": 0.39,
            "Pitcher": 0.397
        },
        "1952": {
            "Hitter": 0.38,
            "Pitcher": 0.388
        },
        "1953": {
            "Hitter": 0.407,
            "Pitcher": 0.398
        },
        "1954": {
            "Hitter": 0.394,
            "Pitcher": 0.393
        },
        "1955": {
            "Hitter": 0.4,
            "Pitcher": 0.388
        },
        "1956": {
            "Hitter": 0.4,
            "Pitcher": 0.392
        },
        "1957": {
            "Hitter": 0.398,
            "Pitcher": 0.386
        },
        "1958": {
            "Hitter": 0.403,
            "Pitcher": 0.396
        },
        "1959": {
            "Hitter": 0.4,
            "Pitcher": 0.402
        },
        "1960": {
            "Hitter": 0.396,
            "Pitcher": 0.387
        },
        "1961": {
            "Hitter": 0.407,
            "Pitcher": 0.392
        },
        "1962": {
            "Hitter": 0.399,
            "Pitcher": 0.384
        },
        "1963": {
            "Hitter": 0.381,
            "Pitcher": 0.374
        },
        "1964": {
            "Hitter": 0.384,
            "Pitcher": 0.372
        },
        "1965": {
            "Hitter": 0.377,
            "Pitcher": 0.369
        },
        "1966": {
            "Hitter": 0.379,
            "Pitcher": 0.362
        },
        "1967": {
            "Hitter": 0.362,
            "Pitcher": 0.36
        },
        "1968": {
            "Hitter": 0.348,
            "Pitcher": 0.344
        },
        "1969": {
            "Hitter": 0.374,
            "Pitcher": 0.372
        },
        "1970": {
            "Hitter": 0.393,
            "Pitcher": 0.385
        },
        "1971": {
            "Hitter": 0.37,
            "Pitcher": 0.366
        },
        "1972": {
            "Hitter": 0.359,
            "Pitcher": 0.357
        },
        "1973": {
            "Hitter": 0.378,
            "Pitcher": 0.378
        },
        "1974": {
            "Hitter": 0.37,
            "Pitcher": 0.375
        },
        "1975": {
            "Hitter": 0.377,
            "Pitcher": 0.372
        },
        "1976": {
            "Hitter": 0.363,
            "Pitcher": 0.361
        },
        "1977": {
            "Hitter": 0.398,
            "Pitcher": 0.397
        },
        "1978": {
            "Hitter": 0.377,
            "Pitcher": 0.378
        },
        "1979": {
            "Hitter": 0.396,
            "Pitcher": 0.389
        },
        "1980": {
            "Hitter": 0.39,
            "Pitcher": 0.387
        },
        "1981": {
            "Hitter": 0.368,
            "Pitcher": 0.366
        },
        "1982": {
            "Hitter": 0.389,
            "Pitcher": 0.381
        },
        "1983": {
            "Hitter": 0.391,
            "Pitcher": 0.394
        },
        "1984": {
            "Hitter": 0.384,
            "Pitcher": 0.377
        },
        "1985": {
            "Hitter": 0.391,
            "Pitcher": 0.388
        },
        "1986": {
            "Hitter": 0.396,
            "Pitcher": 0.383
        },
        "1987": {
            "Hitter": 0.415,
            "Pitcher": 0.398
        },
        "1988": {
            "Hitter": 0.376,
            "Pitcher": 0.372
        },
        "1989": {
            "Hitter": 0.376,
            "Pitcher": 0.374
        },
        "1990": {
            "Hitter": 0.386,
            "Pitcher": 0.372
        },
        "1991": {
            "Hitter": 0.385,
            "Pitcher": 0.371
        },
        "1992": {
            "Hitter": 0.377,
            "Pitcher": 0.369
        },
        "1993": {
            "Hitter": 0.404,
            "Pitcher": 0.386
        },
        "1994": {
            "Hitter": 0.423,
            "Pitcher": 0.408
        },
        "1995": {
            "Hitter": 0.414,
            "Pitcher": 0.397
        },
        "1996": {
            "Hitter": 0.424,
            "Pitcher": 0.406
        },
        "1997": {
            "Hitter": 0.417,
            "Pitcher": 0.4
        },
        "1998": {
            "Hitter": 0.413,
            "Pitcher": 0.4
        },
        "1999": {
            "Hitter": 0.43,
            "Pitcher": 0.411
        },
        "2000": {
            "Hitter": 0.434,
            "Pitcher": 0.41
        },
        "2001": {
            "Hitter": 0.425,
            "Pitcher": 0.4
        },
        "2002": {
            "Hitter": 0.413,
            "Pitcher": 0.39
        },
        "2003": {
            "Hitter": 0.421,
            "Pitcher": 0.392
        },
        "2004": {
            "Hitter": 0.426,
            "Pitcher": 0.397
        },
        "2005": {
            "Hitter": 0.419,
            "Pitcher": 0.392
        },
        "2006": {
            "Hitter": 0.431,
            "Pitcher": 0.399
        },
        "2007": {
            "Hitter": 0.419,
            "Pitcher": 0.393
        },
        "2008": {
            "Hitter": 0.417,
            "Pitcher": 0.388
        },
        "2009": {
            "Hitter": 0.417,
            "Pitcher": 0.385
        },
        "2010": {
            "Hitter": 0.404,
            "Pitcher": 0.378
        },
        "2011": {
            "Hitter": 0.399,
            "Pitcher": 0.369
        },
        "2012": {
            "Hitter": 0.409,
            "Pitcher": 0.37
        },
        "2013": {
            "Hitter": 0.398,
            "Pitcher": 0.366
        },
        "2014": {
            "Hitter": 0.386,
            "Pitcher": 0.359
        },
        "2015": {
            "Hitter": 0.406,
            "Pitcher": 0.371
        },
        "2016": {
            "Hitter": 0.416,
            "Pitcher": 0.381
        },
        "2017": {
            "Hitter": 0.427,
            "Pitcher": 0.384
        },
        "2018": {
            "Hitter": 0.41,
            "Pitcher": 0.373
        },
        "2019": {
            "Hitter": 0.435,
            "Pitcher": 0.397
        },
        "2020": {
            "Hitter": 0.411,
            "Pitcher": 0.37
        },
        "2021": {
            "Hitter": 0.412,
            "Pitcher": 0.368
        },
        "2022": {
            "Hitter": 0.391,
            "Pitcher": 0.355
        }
    },
    "2002": {
        "1900": {
            "Hitter": 0.354,
            "Pitcher": 0.366
        },
        "1901": {
            "Hitter": 0.352,
            "Pitcher": 0.419
        },
        "1902": {
            "Hitter": 0.338,
            "Pitcher": 0.403
        },
        "1903": {
            "Hitter": 0.341,
            "Pitcher": 0.375
        },
        "1904": {
            "Hitter": 0.32,
            "Pitcher": 0.344
        },
        "1905": {
            "Hitter": 0.32,
            "Pitcher": 0.367
        },
        "1906": {
            "Hitter": 0.319,
            "Pitcher": 0.364
        },
        "1907": {
            "Hitter": 0.312,
            "Pitcher": 0.362
        },
        "1908": {
            "Hitter": 0.308,
            "Pitcher": 0.33
        },
        "1909": {
            "Hitter": 0.314,
            "Pitcher": 0.326
        },
        "1910": {
            "Hitter": 0.324,
            "Pitcher": 0.355
        },
        "1911": {
            "Hitter": 0.354,
            "Pitcher": 0.361
        },
        "1912": {
            "Hitter": 0.358,
            "Pitcher": 0.388
        },
        "1913": {
            "Hitter": 0.344,
            "Pitcher": 0.356
        },
        "1914": {
            "Hitter": 0.336,
            "Pitcher": 0.377
        },
        "1915": {
            "Hitter": 0.328,
            "Pitcher": 0.366
        },
        "1916": {
            "Hitter": 0.327,
            "Pitcher": 0.336
        },
        "1917": {
            "Hitter": 0.321,
            "Pitcher": 0.339
        },
        "1918": {
            "Hitter": 0.327,
            "Pitcher": 0.352
        },
        "1919": {
            "Hitter": 0.349,
            "Pitcher": 0.365
        },
        "1920": {
            "Hitter": 0.348,
            "Pitcher": 0.382
        },
        "1921": {
            "Hitter": 0.379,
            "Pitcher": 0.391
        },
        "1922": {
            "Hitter": 0.391,
            "Pitcher": 0.399
        },
        "1923": {
            "Hitter": 0.383,
            "Pitcher": 0.394
        },
        "1924": {
            "Hitter": 0.379,
            "Pitcher": 0.405
        },
        "1925": {
            "Hitter": 0.4,
            "Pitcher": 0.411
        },
        "1926": {
            "Hitter": 0.379,
            "Pitcher": 0.403
        },
        "1927": {
            "Hitter": 0.381,
            "Pitcher": 0.408
        },
        "1928": {
            "Hitter": 0.391,
            "Pitcher": 0.404
        },
        "1929": {
            "Hitter": 0.399,
            "Pitcher": 0.422
        },
        "1930": {
            "Hitter": 0.407,
            "Pitcher": 0.431
        },
        "1931": {
            "Hitter": 0.382,
            "Pitcher": 0.412
        },
        "1932": {
            "Hitter": 0.363,
            "Pitcher": 0.39
        },
        "1933": {
            "Hitter": 0.374,
            "Pitcher": 0.393
        },
        "1934": {
            "Hitter": 0.378,
            "Pitcher": 0.412
        },
        "1935": {
            "Hitter": 0.398,
            "Pitcher": 0.421
        },
        "1936": {
            "Hitter": 0.394,
            "Pitcher": 0.414
        },
        "1937": {
            "Hitter": 0.393,
            "Pitcher": 0.404
        },
        "1938": {
            "Hitter": 0.379,
            "Pitcher": 0.397
        },
        "1939": {
            "Hitter": 0.382,
            "Pitcher": 0.397
        },
        "1940": {
            "Hitter": 0.376,
            "Pitcher": 0.397
        },
        "1941": {
            "Hitter": 0.361,
            "Pitcher": 0.372
        },
        "1942": {
            "Hitter": 0.342,
            "Pitcher": 0.355
        },
        "1943": {
            "Hitter": 0.346,
            "Pitcher": 0.362
        },
        "1944": {
            "Hitter": 0.354,
            "Pitcher": 0.368
        },
        "1945": {
            "Hitter": 0.357,
            "Pitcher": 0.361
        },
        "1946": {
            "Hitter": 0.358,
            "Pitcher": 0.379
        },
        "1947": {
            "Hitter": 0.371,
            "Pitcher": 0.386
        },
        "1948": {
            "Hitter": 0.373,
            "Pitcher": 0.388
        },
        "1949": {
            "Hitter": 0.377,
            "Pitcher": 0.394
        },
        "1950": {
            "Hitter": 0.396,
            "Pitcher": 0.409
        },
        "1951": {
            "Hitter": 0.38,
            "Pitcher": 0.402
        },
        "1952": {
            "Hitter": 0.368,
            "Pitcher": 0.392
        },
        "1953": {
            "Hitter": 0.398,
            "Pitcher": 0.401
        },
        "1954": {
            "Hitter": 0.382,
            "Pitcher": 0.398
        },
        "1955": {
            "Hitter": 0.389,
            "Pitcher": 0.392
        },
        "1956": {
            "Hitter": 0.389,
            "Pitcher": 0.395
        },
        "1957": {
            "Hitter": 0.385,
            "Pitcher": 0.389
        },
        "1958": {
            "Hitter": 0.389,
            "Pitcher": 0.4
        },
        "1959": {
            "Hitter": 0.386,
            "Pitcher": 0.405
        },
        "1960": {
            "Hitter": 0.385,
            "Pitcher": 0.39
        },
        "1961": {
            "Hitter": 0.39,
            "Pitcher": 0.398
        },
        "1962": {
            "Hitter": 0.387,
            "Pitcher": 0.386
        },
        "1963": {
            "Hitter": 0.368,
            "Pitcher": 0.381
        },
        "1964": {
            "Hitter": 0.372,
            "Pitcher": 0.375
        },
        "1965": {
            "Hitter": 0.367,
            "Pitcher": 0.374
        },
        "1966": {
            "Hitter": 0.367,
            "Pitcher": 0.371
        },
        "1967": {
            "Hitter": 0.35,
            "Pitcher": 0.368
        },
        "1968": {
            "Hitter": 0.338,
            "Pitcher": 0.35
        },
        "1969": {
            "Hitter": 0.363,
            "Pitcher": 0.378
        },
        "1970": {
            "Hitter": 0.38,
            "Pitcher": 0.389
        },
        "1971": {
            "Hitter": 0.359,
            "Pitcher": 0.37
        },
        "1972": {
            "Hitter": 0.349,
            "Pitcher": 0.364
        },
        "1973": {
            "Hitter": 0.366,
            "Pitcher": 0.385
        },
        "1974": {
            "Hitter": 0.358,
            "Pitcher": 0.379
        },
        "1975": {
            "Hitter": 0.365,
            "Pitcher": 0.376
        },
        "1976": {
            "Hitter": 0.35,
            "Pitcher": 0.365
        },
        "1977": {
            "Hitter": 0.387,
            "Pitcher": 0.399
        },
        "1978": {
            "Hitter": 0.364,
            "Pitcher": 0.378
        },
        "1979": {
            "Hitter": 0.383,
            "Pitcher": 0.391
        },
        "1980": {
            "Hitter": 0.378,
            "Pitcher": 0.388
        },
        "1981": {
            "Hitter": 0.359,
            "Pitcher": 0.37
        },
        "1982": {
            "Hitter": 0.377,
            "Pitcher": 0.383
        },
        "1983": {
            "Hitter": 0.378,
            "Pitcher": 0.398
        },
        "1984": {
            "Hitter": 0.374,
            "Pitcher": 0.382
        },
        "1985": {
            "Hitter": 0.379,
            "Pitcher": 0.39
        },
        "1986": {
            "Hitter": 0.383,
            "Pitcher": 0.386
        },
        "1987": {
            "Hitter": 0.403,
            "Pitcher": 0.399
        },
        "1988": {
            "Hitter": 0.366,
            "Pitcher": 0.378
        },
        "1989": {
            "Hitter": 0.365,
            "Pitcher": 0.379
        },
        "1990": {
            "Hitter": 0.374,
            "Pitcher": 0.377
        },
        "1991": {
            "Hitter": 0.374,
            "Pitcher": 0.374
        },
        "1992": {
            "Hitter": 0.366,
            "Pitcher": 0.369
        },
        "1993": {
            "Hitter": 0.39,
            "Pitcher": 0.387
        },
        "1994": {
            "Hitter": 0.41,
            "Pitcher": 0.408
        },
        "1995": {
            "Hitter": 0.403,
            "Pitcher": 0.4
        },
        "1996": {
            "Hitter": 0.411,
            "Pitcher": 0.404
        },
        "1997": {
            "Hitter": 0.404,
            "Pitcher": 0.402
        },
        "1998": {
            "Hitter": 0.403,
            "Pitcher": 0.402
        },
        "1999": {
            "Hitter": 0.417,
            "Pitcher": 0.409
        },
        "2000": {
            "Hitter": 0.423,
            "Pitcher": 0.41
        },
        "2001": {
            "Hitter": 0.411,
            "Pitcher": 0.401
        },
        "2002": {
            "Hitter": 0.404,
            "Pitcher": 0.39
        },
        "2003": {
            "Hitter": 0.409,
            "Pitcher": 0.395
        },
        "2004": {
            "Hitter": 0.415,
            "Pitcher": 0.398
        },
        "2005": {
            "Hitter": 0.406,
            "Pitcher": 0.394
        },
        "2006": {
            "Hitter": 0.422,
            "Pitcher": 0.398
        },
        "2007": {
            "Hitter": 0.407,
            "Pitcher": 0.395
        },
        "2008": {
            "Hitter": 0.405,
            "Pitcher": 0.39
        },
        "2009": {
            "Hitter": 0.405,
            "Pitcher": 0.388
        },
        "2010": {
            "Hitter": 0.391,
            "Pitcher": 0.38
        },
        "2011": {
            "Hitter": 0.388,
            "Pitcher": 0.372
        },
        "2012": {
            "Hitter": 0.397,
            "Pitcher": 0.374
        },
        "2013": {
            "Hitter": 0.387,
            "Pitcher": 0.369
        },
        "2014": {
            "Hitter": 0.376,
            "Pitcher": 0.361
        },
        "2015": {
            "Hitter": 0.394,
            "Pitcher": 0.376
        },
        "2016": {
            "Hitter": 0.405,
            "Pitcher": 0.381
        },
        "2017": {
            "Hitter": 0.416,
            "Pitcher": 0.385
        },
        "2018": {
            "Hitter": 0.398,
            "Pitcher": 0.376
        },
        "2019": {
            "Hitter": 0.425,
            "Pitcher": 0.396
        },
        "2020": {
            "Hitter": 0.401,
            "Pitcher": 0.376
        },
        "2021": {
            "Hitter": 0.402,
            "Pitcher": 0.372
        },
        "2022": {
            "Hitter": 0.378,
            "Pitcher": 0.361
        }
    },
    "2003": {
        "1900": {
            "Hitter": 0.392,
            "Pitcher": 0.385
        },
        "1901": {
            "Hitter": 0.389,
            "Pitcher": 0.433
        },
        "1902": {
            "Hitter": 0.374,
            "Pitcher": 0.417
        },
        "1903": {
            "Hitter": 0.377,
            "Pitcher": 0.387
        },
        "1904": {
            "Hitter": 0.357,
            "Pitcher": 0.355
        },
        "1905": {
            "Hitter": 0.359,
            "Pitcher": 0.377
        },
        "1906": {
            "Hitter": 0.355,
            "Pitcher": 0.373
        },
        "1907": {
            "Hitter": 0.353,
            "Pitcher": 0.375
        },
        "1908": {
            "Hitter": 0.347,
            "Pitcher": 0.338
        },
        "1909": {
            "Hitter": 0.354,
            "Pitcher": 0.338
        },
        "1910": {
            "Hitter": 0.364,
            "Pitcher": 0.361
        },
        "1911": {
            "Hitter": 0.392,
            "Pitcher": 0.367
        },
        "1912": {
            "Hitter": 0.394,
            "Pitcher": 0.39
        },
        "1913": {
            "Hitter": 0.378,
            "Pitcher": 0.361
        },
        "1914": {
            "Hitter": 0.373,
            "Pitcher": 0.378
        },
        "1915": {
            "Hitter": 0.366,
            "Pitcher": 0.374
        },
        "1916": {
            "Hitter": 0.365,
            "Pitcher": 0.346
        },
        "1917": {
            "Hitter": 0.36,
            "Pitcher": 0.349
        },
        "1918": {
            "Hitter": 0.365,
            "Pitcher": 0.364
        },
        "1919": {
            "Hitter": 0.384,
            "Pitcher": 0.374
        },
        "1920": {
            "Hitter": 0.384,
            "Pitcher": 0.394
        },
        "1921": {
            "Hitter": 0.413,
            "Pitcher": 0.399
        },
        "1922": {
            "Hitter": 0.42,
            "Pitcher": 0.411
        },
        "1923": {
            "Hitter": 0.416,
            "Pitcher": 0.405
        },
        "1924": {
            "Hitter": 0.41,
            "Pitcher": 0.42
        },
        "1925": {
            "Hitter": 0.43,
            "Pitcher": 0.424
        },
        "1926": {
            "Hitter": 0.413,
            "Pitcher": 0.416
        },
        "1927": {
            "Hitter": 0.413,
            "Pitcher": 0.422
        },
        "1928": {
            "Hitter": 0.422,
            "Pitcher": 0.415
        },
        "1929": {
            "Hitter": 0.431,
            "Pitcher": 0.435
        },
        "1930": {
            "Hitter": 0.435,
            "Pitcher": 0.445
        },
        "1931": {
            "Hitter": 0.414,
            "Pitcher": 0.424
        },
        "1932": {
            "Hitter": 0.397,
            "Pitcher": 0.403
        },
        "1933": {
            "Hitter": 0.404,
            "Pitcher": 0.407
        },
        "1934": {
            "Hitter": 0.407,
            "Pitcher": 0.427
        },
        "1935": {
            "Hitter": 0.426,
            "Pitcher": 0.431
        },
        "1936": {
            "Hitter": 0.423,
            "Pitcher": 0.428
        },
        "1937": {
            "Hitter": 0.424,
            "Pitcher": 0.415
        },
        "1938": {
            "Hitter": 0.412,
            "Pitcher": 0.407
        },
        "1939": {
            "Hitter": 0.412,
            "Pitcher": 0.41
        },
        "1940": {
            "Hitter": 0.407,
            "Pitcher": 0.41
        },
        "1941": {
            "Hitter": 0.392,
            "Pitcher": 0.383
        },
        "1942": {
            "Hitter": 0.376,
            "Pitcher": 0.369
        },
        "1943": {
            "Hitter": 0.382,
            "Pitcher": 0.377
        },
        "1944": {
            "Hitter": 0.388,
            "Pitcher": 0.379
        },
        "1945": {
            "Hitter": 0.39,
            "Pitcher": 0.375
        },
        "1946": {
            "Hitter": 0.392,
            "Pitcher": 0.387
        },
        "1947": {
            "Hitter": 0.402,
            "Pitcher": 0.397
        },
        "1948": {
            "Hitter": 0.404,
            "Pitcher": 0.399
        },
        "1949": {
            "Hitter": 0.408,
            "Pitcher": 0.404
        },
        "1950": {
            "Hitter": 0.421,
            "Pitcher": 0.419
        },
        "1951": {
            "Hitter": 0.406,
            "Pitcher": 0.41
        },
        "1952": {
            "Hitter": 0.398,
            "Pitcher": 0.401
        },
        "1953": {
            "Hitter": 0.423,
            "Pitcher": 0.41
        },
        "1954": {
            "Hitter": 0.407,
            "Pitcher": 0.405
        },
        "1955": {
            "Hitter": 0.414,
            "Pitcher": 0.399
        },
        "1956": {
            "Hitter": 0.417,
            "Pitcher": 0.404
        },
        "1957": {
            "Hitter": 0.412,
            "Pitcher": 0.396
        },
        "1958": {
            "Hitter": 0.419,
            "Pitcher": 0.407
        },
        "1959": {
            "Hitter": 0.417,
            "Pitcher": 0.416
        },
        "1960": {
            "Hitter": 0.414,
            "Pitcher": 0.398
        },
        "1961": {
            "Hitter": 0.419,
            "Pitcher": 0.405
        },
        "1962": {
            "Hitter": 0.414,
            "Pitcher": 0.394
        },
        "1963": {
            "Hitter": 0.398,
            "Pitcher": 0.387
        },
        "1964": {
            "Hitter": 0.401,
            "Pitcher": 0.383
        },
        "1965": {
            "Hitter": 0.396,
            "Pitcher": 0.379
        },
        "1966": {
            "Hitter": 0.396,
            "Pitcher": 0.375
        },
        "1967": {
            "Hitter": 0.38,
            "Pitcher": 0.374
        },
        "1968": {
            "Hitter": 0.367,
            "Pitcher": 0.356
        },
        "1969": {
            "Hitter": 0.392,
            "Pitcher": 0.384
        },
        "1970": {
            "Hitter": 0.41,
            "Pitcher": 0.397
        },
        "1971": {
            "Hitter": 0.389,
            "Pitcher": 0.38
        },
        "1972": {
            "Hitter": 0.379,
            "Pitcher": 0.373
        },
        "1973": {
            "Hitter": 0.397,
            "Pitcher": 0.391
        },
        "1974": {
            "Hitter": 0.389,
            "Pitcher": 0.388
        },
        "1975": {
            "Hitter": 0.395,
            "Pitcher": 0.386
        },
        "1976": {
            "Hitter": 0.383,
            "Pitcher": 0.377
        },
        "1977": {
            "Hitter": 0.416,
            "Pitcher": 0.409
        },
        "1978": {
            "Hitter": 0.395,
            "Pitcher": 0.391
        },
        "1979": {
            "Hitter": 0.415,
            "Pitcher": 0.403
        },
        "1980": {
            "Hitter": 0.407,
            "Pitcher": 0.401
        },
        "1981": {
            "Hitter": 0.391,
            "Pitcher": 0.382
        },
        "1982": {
            "Hitter": 0.408,
            "Pitcher": 0.394
        },
        "1983": {
            "Hitter": 0.408,
            "Pitcher": 0.408
        },
        "1984": {
            "Hitter": 0.404,
            "Pitcher": 0.391
        },
        "1985": {
            "Hitter": 0.41,
            "Pitcher": 0.4
        },
        "1986": {
            "Hitter": 0.413,
            "Pitcher": 0.398
        },
        "1987": {
            "Hitter": 0.432,
            "Pitcher": 0.411
        },
        "1988": {
            "Hitter": 0.397,
            "Pitcher": 0.387
        },
        "1989": {
            "Hitter": 0.394,
            "Pitcher": 0.387
        },
        "1990": {
            "Hitter": 0.403,
            "Pitcher": 0.385
        },
        "1991": {
            "Hitter": 0.404,
            "Pitcher": 0.382
        },
        "1992": {
            "Hitter": 0.395,
            "Pitcher": 0.38
        },
        "1993": {
            "Hitter": 0.422,
            "Pitcher": 0.399
        },
        "1994": {
            "Hitter": 0.44,
            "Pitcher": 0.419
        },
        "1995": {
            "Hitter": 0.433,
            "Pitcher": 0.41
        },
        "1996": {
            "Hitter": 0.441,
            "Pitcher": 0.416
        },
        "1997": {
            "Hitter": 0.432,
            "Pitcher": 0.413
        },
        "1998": {
            "Hitter": 0.433,
            "Pitcher": 0.413
        },
        "1999": {
            "Hitter": 0.448,
            "Pitcher": 0.42
        },
        "2000": {
            "Hitter": 0.45,
            "Pitcher": 0.423
        },
        "2001": {
            "Hitter": 0.44,
            "Pitcher": 0.411
        },
        "2002": {
            "Hitter": 0.433,
            "Pitcher": 0.402
        },
        "2003": {
            "Hitter": 0.438,
            "Pitcher": 0.407
        },
        "2004": {
            "Hitter": 0.443,
            "Pitcher": 0.409
        },
        "2005": {
            "Hitter": 0.436,
            "Pitcher": 0.404
        },
        "2006": {
            "Hitter": 0.449,
            "Pitcher": 0.409
        },
        "2007": {
            "Hitter": 0.437,
            "Pitcher": 0.406
        },
        "2008": {
            "Hitter": 0.435,
            "Pitcher": 0.399
        },
        "2009": {
            "Hitter": 0.435,
            "Pitcher": 0.398
        },
        "2010": {
            "Hitter": 0.421,
            "Pitcher": 0.391
        },
        "2011": {
            "Hitter": 0.418,
            "Pitcher": 0.381
        },
        "2012": {
            "Hitter": 0.425,
            "Pitcher": 0.382
        },
        "2013": {
            "Hitter": 0.417,
            "Pitcher": 0.378
        },
        "2014": {
            "Hitter": 0.406,
            "Pitcher": 0.371
        },
        "2015": {
            "Hitter": 0.424,
            "Pitcher": 0.382
        },
        "2016": {
            "Hitter": 0.435,
            "Pitcher": 0.388
        },
        "2017": {
            "Hitter": 0.445,
            "Pitcher": 0.394
        },
        "2018": {
            "Hitter": 0.427,
            "Pitcher": 0.385
        },
        "2019": {
            "Hitter": 0.455,
            "Pitcher": 0.401
        },
        "2020": {
            "Hitter": 0.432,
            "Pitcher": 0.378
        },
        "2021": {
            "Hitter": 0.432,
            "Pitcher": 0.377
        },
        "2022": {
            "Hitter": 0.409,
            "Pitcher": 0.367
        }
    },
    "2004": {
        "1900": {
            "Hitter": 0.394,
            "Pitcher": 0.376
        },
        "1901": {
            "Hitter": 0.396,
            "Pitcher": 0.436
        },
        "1902": {
            "Hitter": 0.379,
            "Pitcher": 0.416
        },
        "1903": {
            "Hitter": 0.383,
            "Pitcher": 0.387
        },
        "1904": {
            "Hitter": 0.366,
            "Pitcher": 0.353
        },
        "1905": {
            "Hitter": 0.365,
            "Pitcher": 0.373
        },
        "1906": {
            "Hitter": 0.362,
            "Pitcher": 0.365
        },
        "1907": {
            "Hitter": 0.358,
            "Pitcher": 0.369
        },
        "1908": {
            "Hitter": 0.352,
            "Pitcher": 0.33
        },
        "1909": {
            "Hitter": 0.359,
            "Pitcher": 0.327
        },
        "1910": {
            "Hitter": 0.367,
            "Pitcher": 0.353
        },
        "1911": {
            "Hitter": 0.394,
            "Pitcher": 0.368
        },
        "1912": {
            "Hitter": 0.397,
            "Pitcher": 0.392
        },
        "1913": {
            "Hitter": 0.381,
            "Pitcher": 0.359
        },
        "1914": {
            "Hitter": 0.376,
            "Pitcher": 0.384
        },
        "1915": {
            "Hitter": 0.37,
            "Pitcher": 0.374
        },
        "1916": {
            "Hitter": 0.368,
            "Pitcher": 0.341
        },
        "1917": {
            "Hitter": 0.364,
            "Pitcher": 0.343
        },
        "1918": {
            "Hitter": 0.369,
            "Pitcher": 0.355
        },
        "1919": {
            "Hitter": 0.388,
            "Pitcher": 0.375
        },
        "1920": {
            "Hitter": 0.388,
            "Pitcher": 0.393
        },
        "1921": {
            "Hitter": 0.415,
            "Pitcher": 0.4
        },
        "1922": {
            "Hitter": 0.422,
            "Pitcher": 0.41
        },
        "1923": {
            "Hitter": 0.416,
            "Pitcher": 0.406
        },
        "1924": {
            "Hitter": 0.413,
            "Pitcher": 0.416
        },
        "1925": {
            "Hitter": 0.432,
            "Pitcher": 0.423
        },
        "1926": {
            "Hitter": 0.414,
            "Pitcher": 0.411
        },
        "1927": {
            "Hitter": 0.416,
            "Pitcher": 0.421
        },
        "1928": {
            "Hitter": 0.424,
            "Pitcher": 0.413
        },
        "1929": {
            "Hitter": 0.431,
            "Pitcher": 0.435
        },
        "1930": {
            "Hitter": 0.437,
            "Pitcher": 0.445
        },
        "1931": {
            "Hitter": 0.415,
            "Pitcher": 0.422
        },
        "1932": {
            "Hitter": 0.402,
            "Pitcher": 0.4
        },
        "1933": {
            "Hitter": 0.409,
            "Pitcher": 0.401
        },
        "1934": {
            "Hitter": 0.41,
            "Pitcher": 0.425
        },
        "1935": {
            "Hitter": 0.428,
            "Pitcher": 0.427
        },
        "1936": {
            "Hitter": 0.425,
            "Pitcher": 0.427
        },
        "1937": {
            "Hitter": 0.425,
            "Pitcher": 0.415
        },
        "1938": {
            "Hitter": 0.412,
            "Pitcher": 0.408
        },
        "1939": {
            "Hitter": 0.414,
            "Pitcher": 0.406
        },
        "1940": {
            "Hitter": 0.412,
            "Pitcher": 0.409
        },
        "1941": {
            "Hitter": 0.397,
            "Pitcher": 0.38
        },
        "1942": {
            "Hitter": 0.38,
            "Pitcher": 0.365
        },
        "1943": {
            "Hitter": 0.384,
            "Pitcher": 0.371
        },
        "1944": {
            "Hitter": 0.39,
            "Pitcher": 0.375
        },
        "1945": {
            "Hitter": 0.393,
            "Pitcher": 0.371
        },
        "1946": {
            "Hitter": 0.394,
            "Pitcher": 0.385
        },
        "1947": {
            "Hitter": 0.403,
            "Pitcher": 0.396
        },
        "1948": {
            "Hitter": 0.405,
            "Pitcher": 0.398
        },
        "1949": {
            "Hitter": 0.406,
            "Pitcher": 0.405
        },
        "1950": {
            "Hitter": 0.422,
            "Pitcher": 0.419
        },
        "1951": {
            "Hitter": 0.405,
            "Pitcher": 0.414
        },
        "1952": {
            "Hitter": 0.397,
            "Pitcher": 0.399
        },
        "1953": {
            "Hitter": 0.423,
            "Pitcher": 0.409
        },
        "1954": {
            "Hitter": 0.408,
            "Pitcher": 0.405
        },
        "1955": {
            "Hitter": 0.413,
            "Pitcher": 0.396
        },
        "1956": {
            "Hitter": 0.414,
            "Pitcher": 0.402
        },
        "1957": {
            "Hitter": 0.413,
            "Pitcher": 0.394
        },
        "1958": {
            "Hitter": 0.418,
            "Pitcher": 0.404
        },
        "1959": {
            "Hitter": 0.415,
            "Pitcher": 0.415
        },
        "1960": {
            "Hitter": 0.413,
            "Pitcher": 0.393
        },
        "1961": {
            "Hitter": 0.419,
            "Pitcher": 0.402
        },
        "1962": {
            "Hitter": 0.413,
            "Pitcher": 0.393
        },
        "1963": {
            "Hitter": 0.398,
            "Pitcher": 0.386
        },
        "1964": {
            "Hitter": 0.401,
            "Pitcher": 0.381
        },
        "1965": {
            "Hitter": 0.395,
            "Pitcher": 0.375
        },
        "1966": {
            "Hitter": 0.396,
            "Pitcher": 0.373
        },
        "1967": {
            "Hitter": 0.382,
            "Pitcher": 0.373
        },
        "1968": {
            "Hitter": 0.371,
            "Pitcher": 0.354
        },
        "1969": {
            "Hitter": 0.394,
            "Pitcher": 0.381
        },
        "1970": {
            "Hitter": 0.41,
            "Pitcher": 0.392
        },
        "1971": {
            "Hitter": 0.39,
            "Pitcher": 0.376
        },
        "1972": {
            "Hitter": 0.38,
            "Pitcher": 0.372
        },
        "1973": {
            "Hitter": 0.396,
            "Pitcher": 0.39
        },
        "1974": {
            "Hitter": 0.388,
            "Pitcher": 0.386
        },
        "1975": {
            "Hitter": 0.394,
            "Pitcher": 0.385
        },
        "1976": {
            "Hitter": 0.383,
            "Pitcher": 0.377
        },
        "1977": {
            "Hitter": 0.417,
            "Pitcher": 0.405
        },
        "1978": {
            "Hitter": 0.395,
            "Pitcher": 0.388
        },
        "1979": {
            "Hitter": 0.413,
            "Pitcher": 0.4
        },
        "1980": {
            "Hitter": 0.407,
            "Pitcher": 0.396
        },
        "1981": {
            "Hitter": 0.392,
            "Pitcher": 0.378
        },
        "1982": {
            "Hitter": 0.406,
            "Pitcher": 0.391
        },
        "1983": {
            "Hitter": 0.408,
            "Pitcher": 0.404
        },
        "1984": {
            "Hitter": 0.404,
            "Pitcher": 0.389
        },
        "1985": {
            "Hitter": 0.409,
            "Pitcher": 0.396
        },
        "1986": {
            "Hitter": 0.412,
            "Pitcher": 0.394
        },
        "1987": {
            "Hitter": 0.43,
            "Pitcher": 0.407
        },
        "1988": {
            "Hitter": 0.397,
            "Pitcher": 0.385
        },
        "1989": {
            "Hitter": 0.395,
            "Pitcher": 0.383
        },
        "1990": {
            "Hitter": 0.403,
            "Pitcher": 0.38
        },
        "1991": {
            "Hitter": 0.402,
            "Pitcher": 0.379
        },
        "1992": {
            "Hitter": 0.395,
            "Pitcher": 0.377
        },
        "1993": {
            "Hitter": 0.421,
            "Pitcher": 0.394
        },
        "1994": {
            "Hitter": 0.439,
            "Pitcher": 0.415
        },
        "1995": {
            "Hitter": 0.431,
            "Pitcher": 0.407
        },
        "1996": {
            "Hitter": 0.44,
            "Pitcher": 0.413
        },
        "1997": {
            "Hitter": 0.432,
            "Pitcher": 0.409
        },
        "1998": {
            "Hitter": 0.432,
            "Pitcher": 0.408
        },
        "1999": {
            "Hitter": 0.445,
            "Pitcher": 0.418
        },
        "2000": {
            "Hitter": 0.449,
            "Pitcher": 0.417
        },
        "2001": {
            "Hitter": 0.438,
            "Pitcher": 0.405
        },
        "2002": {
            "Hitter": 0.431,
            "Pitcher": 0.397
        },
        "2003": {
            "Hitter": 0.435,
            "Pitcher": 0.401
        },
        "2004": {
            "Hitter": 0.441,
            "Pitcher": 0.403
        },
        "2005": {
            "Hitter": 0.433,
            "Pitcher": 0.399
        },
        "2006": {
            "Hitter": 0.447,
            "Pitcher": 0.404
        },
        "2007": {
            "Hitter": 0.435,
            "Pitcher": 0.4
        },
        "2008": {
            "Hitter": 0.432,
            "Pitcher": 0.395
        },
        "2009": {
            "Hitter": 0.432,
            "Pitcher": 0.394
        },
        "2010": {
            "Hitter": 0.421,
            "Pitcher": 0.386
        },
        "2011": {
            "Hitter": 0.418,
            "Pitcher": 0.376
        },
        "2012": {
            "Hitter": 0.425,
            "Pitcher": 0.376
        },
        "2013": {
            "Hitter": 0.416,
            "Pitcher": 0.373
        },
        "2014": {
            "Hitter": 0.406,
            "Pitcher": 0.366
        },
        "2015": {
            "Hitter": 0.422,
            "Pitcher": 0.378
        },
        "2016": {
            "Hitter": 0.432,
            "Pitcher": 0.385
        },
        "2017": {
            "Hitter": 0.441,
            "Pitcher": 0.389
        },
        "2018": {
            "Hitter": 0.426,
            "Pitcher": 0.381
        },
        "2019": {
            "Hitter": 0.454,
            "Pitcher": 0.396
        },
        "2020": {
            "Hitter": 0.434,
            "Pitcher": 0.376
        },
        "2021": {
            "Hitter": 0.43,
            "Pitcher": 0.374
        },
        "2022": {
            "Hitter": 0.408,
            "Pitcher": 0.362
        }
    },
    "2005": {
        "1900": {
            "Hitter": 0.399,
            "Pitcher": 0.378
        },
        "1901": {
            "Hitter": 0.397,
            "Pitcher": 0.422
        },
        "1902": {
            "Hitter": 0.38,
            "Pitcher": 0.406
        },
        "1903": {
            "Hitter": 0.384,
            "Pitcher": 0.377
        },
        "1904": {
            "Hitter": 0.363,
            "Pitcher": 0.347
        },
        "1905": {
            "Hitter": 0.366,
            "Pitcher": 0.366
        },
        "1906": {
            "Hitter": 0.363,
            "Pitcher": 0.36
        },
        "1907": {
            "Hitter": 0.359,
            "Pitcher": 0.364
        },
        "1908": {
            "Hitter": 0.353,
            "Pitcher": 0.32
        },
        "1909": {
            "Hitter": 0.361,
            "Pitcher": 0.316
        },
        "1910": {
            "Hitter": 0.37,
            "Pitcher": 0.347
        },
        "1911": {
            "Hitter": 0.398,
            "Pitcher": 0.359
        },
        "1912": {
            "Hitter": 0.401,
            "Pitcher": 0.38
        },
        "1913": {
            "Hitter": 0.386,
            "Pitcher": 0.348
        },
        "1914": {
            "Hitter": 0.379,
            "Pitcher": 0.366
        },
        "1915": {
            "Hitter": 0.373,
            "Pitcher": 0.368
        },
        "1916": {
            "Hitter": 0.371,
            "Pitcher": 0.332
        },
        "1917": {
            "Hitter": 0.368,
            "Pitcher": 0.338
        },
        "1918": {
            "Hitter": 0.371,
            "Pitcher": 0.352
        },
        "1919": {
            "Hitter": 0.391,
            "Pitcher": 0.365
        },
        "1920": {
            "Hitter": 0.391,
            "Pitcher": 0.383
        },
        "1921": {
            "Hitter": 0.417,
            "Pitcher": 0.392
        },
        "1922": {
            "Hitter": 0.427,
            "Pitcher": 0.399
        },
        "1923": {
            "Hitter": 0.42,
            "Pitcher": 0.399
        },
        "1924": {
            "Hitter": 0.416,
            "Pitcher": 0.408
        },
        "1925": {
            "Hitter": 0.435,
            "Pitcher": 0.416
        },
        "1926": {
            "Hitter": 0.418,
            "Pitcher": 0.405
        },
        "1927": {
            "Hitter": 0.42,
            "Pitcher": 0.41
        },
        "1928": {
            "Hitter": 0.428,
            "Pitcher": 0.403
        },
        "1929": {
            "Hitter": 0.434,
            "Pitcher": 0.426
        },
        "1930": {
            "Hitter": 0.44,
            "Pitcher": 0.429
        },
        "1931": {
            "Hitter": 0.419,
            "Pitcher": 0.413
        },
        "1932": {
            "Hitter": 0.403,
            "Pitcher": 0.391
        },
        "1933": {
            "Hitter": 0.411,
            "Pitcher": 0.395
        },
        "1934": {
            "Hitter": 0.413,
            "Pitcher": 0.413
        },
        "1935": {
            "Hitter": 0.431,
            "Pitcher": 0.419
        },
        "1936": {
            "Hitter": 0.428,
            "Pitcher": 0.417
        },
        "1937": {
            "Hitter": 0.428,
            "Pitcher": 0.404
        },
        "1938": {
            "Hitter": 0.415,
            "Pitcher": 0.399
        },
        "1939": {
            "Hitter": 0.416,
            "Pitcher": 0.401
        },
        "1940": {
            "Hitter": 0.412,
            "Pitcher": 0.397
        },
        "1941": {
            "Hitter": 0.398,
            "Pitcher": 0.371
        },
        "1942": {
            "Hitter": 0.382,
            "Pitcher": 0.355
        },
        "1943": {
            "Hitter": 0.386,
            "Pitcher": 0.365
        },
        "1944": {
            "Hitter": 0.393,
            "Pitcher": 0.369
        },
        "1945": {
            "Hitter": 0.396,
            "Pitcher": 0.366
        },
        "1946": {
            "Hitter": 0.397,
            "Pitcher": 0.378
        },
        "1947": {
            "Hitter": 0.406,
            "Pitcher": 0.386
        },
        "1948": {
            "Hitter": 0.41,
            "Pitcher": 0.39
        },
        "1949": {
            "Hitter": 0.408,
            "Pitcher": 0.389
        },
        "1950": {
            "Hitter": 0.425,
            "Pitcher": 0.401
        },
        "1951": {
            "Hitter": 0.409,
            "Pitcher": 0.402
        },
        "1952": {
            "Hitter": 0.4,
            "Pitcher": 0.386
        },
        "1953": {
            "Hitter": 0.426,
            "Pitcher": 0.397
        },
        "1954": {
            "Hitter": 0.411,
            "Pitcher": 0.388
        },
        "1955": {
            "Hitter": 0.416,
            "Pitcher": 0.382
        },
        "1956": {
            "Hitter": 0.419,
            "Pitcher": 0.387
        },
        "1957": {
            "Hitter": 0.413,
            "Pitcher": 0.38
        },
        "1958": {
            "Hitter": 0.421,
            "Pitcher": 0.393
        },
        "1959": {
            "Hitter": 0.418,
            "Pitcher": 0.397
        },
        "1960": {
            "Hitter": 0.414,
            "Pitcher": 0.381
        },
        "1961": {
            "Hitter": 0.422,
            "Pitcher": 0.387
        },
        "1962": {
            "Hitter": 0.416,
            "Pitcher": 0.378
        },
        "1963": {
            "Hitter": 0.4,
            "Pitcher": 0.373
        },
        "1964": {
            "Hitter": 0.402,
            "Pitcher": 0.365
        },
        "1965": {
            "Hitter": 0.398,
            "Pitcher": 0.365
        },
        "1966": {
            "Hitter": 0.398,
            "Pitcher": 0.357
        },
        "1967": {
            "Hitter": 0.382,
            "Pitcher": 0.361
        },
        "1968": {
            "Hitter": 0.371,
            "Pitcher": 0.344
        },
        "1969": {
            "Hitter": 0.395,
            "Pitcher": 0.372
        },
        "1970": {
            "Hitter": 0.412,
            "Pitcher": 0.38
        },
        "1971": {
            "Hitter": 0.392,
            "Pitcher": 0.364
        },
        "1972": {
            "Hitter": 0.381,
            "Pitcher": 0.36
        },
        "1973": {
            "Hitter": 0.397,
            "Pitcher": 0.377
        },
        "1974": {
            "Hitter": 0.391,
            "Pitcher": 0.375
        },
        "1975": {
            "Hitter": 0.397,
            "Pitcher": 0.371
        },
        "1976": {
            "Hitter": 0.385,
            "Pitcher": 0.366
        },
        "1977": {
            "Hitter": 0.417,
            "Pitcher": 0.391
        },
        "1978": {
            "Hitter": 0.396,
            "Pitcher": 0.376
        },
        "1979": {
            "Hitter": 0.416,
            "Pitcher": 0.387
        },
        "1980": {
            "Hitter": 0.408,
            "Pitcher": 0.385
        },
        "1981": {
            "Hitter": 0.393,
            "Pitcher": 0.366
        },
        "1982": {
            "Hitter": 0.411,
            "Pitcher": 0.378
        },
        "1983": {
            "Hitter": 0.411,
            "Pitcher": 0.391
        },
        "1984": {
            "Hitter": 0.406,
            "Pitcher": 0.377
        },
        "1985": {
            "Hitter": 0.413,
            "Pitcher": 0.384
        },
        "1986": {
            "Hitter": 0.414,
            "Pitcher": 0.381
        },
        "1987": {
            "Hitter": 0.432,
            "Pitcher": 0.392
        },
        "1988": {
            "Hitter": 0.397,
            "Pitcher": 0.373
        },
        "1989": {
            "Hitter": 0.396,
            "Pitcher": 0.373
        },
        "1990": {
            "Hitter": 0.406,
            "Pitcher": 0.369
        },
        "1991": {
            "Hitter": 0.405,
            "Pitcher": 0.367
        },
        "1992": {
            "Hitter": 0.397,
            "Pitcher": 0.367
        },
        "1993": {
            "Hitter": 0.422,
            "Pitcher": 0.382
        },
        "1994": {
            "Hitter": 0.442,
            "Pitcher": 0.401
        },
        "1995": {
            "Hitter": 0.434,
            "Pitcher": 0.393
        },
        "1996": {
            "Hitter": 0.441,
            "Pitcher": 0.397
        },
        "1997": {
            "Hitter": 0.434,
            "Pitcher": 0.393
        },
        "1998": {
            "Hitter": 0.434,
            "Pitcher": 0.394
        },
        "1999": {
            "Hitter": 0.449,
            "Pitcher": 0.401
        },
        "2000": {
            "Hitter": 0.451,
            "Pitcher": 0.401
        },
        "2001": {
            "Hitter": 0.441,
            "Pitcher": 0.39
        },
        "2002": {
            "Hitter": 0.433,
            "Pitcher": 0.382
        },
        "2003": {
            "Hitter": 0.438,
            "Pitcher": 0.384
        },
        "2004": {
            "Hitter": 0.444,
            "Pitcher": 0.388
        },
        "2005": {
            "Hitter": 0.437,
            "Pitcher": 0.385
        },
        "2006": {
            "Hitter": 0.448,
            "Pitcher": 0.389
        },
        "2007": {
            "Hitter": 0.437,
            "Pitcher": 0.385
        },
        "2008": {
            "Hitter": 0.435,
            "Pitcher": 0.381
        },
        "2009": {
            "Hitter": 0.436,
            "Pitcher": 0.378
        },
        "2010": {
            "Hitter": 0.422,
            "Pitcher": 0.372
        },
        "2011": {
            "Hitter": 0.419,
            "Pitcher": 0.365
        },
        "2012": {
            "Hitter": 0.426,
            "Pitcher": 0.364
        },
        "2013": {
            "Hitter": 0.418,
            "Pitcher": 0.36
        },
        "2014": {
            "Hitter": 0.407,
            "Pitcher": 0.355
        },
        "2015": {
            "Hitter": 0.424,
            "Pitcher": 0.365
        },
        "2016": {
            "Hitter": 0.434,
            "Pitcher": 0.371
        },
        "2017": {
            "Hitter": 0.443,
            "Pitcher": 0.375
        },
        "2018": {
            "Hitter": 0.426,
            "Pitcher": 0.367
        },
        "2019": {
            "Hitter": 0.456,
            "Pitcher": 0.383
        },
        "2020": {
            "Hitter": 0.432,
            "Pitcher": 0.363
        },
        "2021": {
            "Hitter": 0.432,
            "Pitcher": 0.359
        },
        "2022": {
            "Hitter": 0.409,
            "Pitcher": 0.349
        }
    },
    CLASSIC_SET: {
        "1900": {
            "Hitter": 0.362,
            "Pitcher": 0.358
        },
        "1901": {
            "Hitter": 0.357,
            "Pitcher": 0.412
        },
        "1902": {
            "Hitter": 0.343,
            "Pitcher": 0.389
        },
        "1903": {
            "Hitter": 0.344,
            "Pitcher": 0.361
        },
        "1904": {
            "Hitter": 0.324,
            "Pitcher": 0.339
        },
        "1905": {
            "Hitter": 0.326,
            "Pitcher": 0.351
        },
        "1906": {
            "Hitter": 0.321,
            "Pitcher": 0.348
        },
        "1907": {
            "Hitter": 0.319,
            "Pitcher": 0.344
        },
        "1908": {
            "Hitter": 0.312,
            "Pitcher": 0.305
        },
        "1909": {
            "Hitter": 0.319,
            "Pitcher": 0.303
        },
        "1910": {
            "Hitter": 0.331,
            "Pitcher": 0.327
        },
        "1911": {
            "Hitter": 0.363,
            "Pitcher": 0.338
        },
        "1912": {
            "Hitter": 0.366,
            "Pitcher": 0.356
        },
        "1913": {
            "Hitter": 0.35,
            "Pitcher": 0.328
        },
        "1914": {
            "Hitter": 0.343,
            "Pitcher": 0.353
        },
        "1915": {
            "Hitter": 0.333,
            "Pitcher": 0.348
        },
        "1916": {
            "Hitter": 0.333,
            "Pitcher": 0.324
        },
        "1917": {
            "Hitter": 0.327,
            "Pitcher": 0.324
        },
        "1918": {
            "Hitter": 0.332,
            "Pitcher": 0.338
        },
        "1919": {
            "Hitter": 0.353,
            "Pitcher": 0.35
        },
        "1920": {
            "Hitter": 0.356,
            "Pitcher": 0.372
        },
        "1921": {
            "Hitter": 0.386,
            "Pitcher": 0.379
        },
        "1922": {
            "Hitter": 0.397,
            "Pitcher": 0.391
        },
        "1923": {
            "Hitter": 0.389,
            "Pitcher": 0.387
        },
        "1924": {
            "Hitter": 0.385,
            "Pitcher": 0.398
        },
        "1925": {
            "Hitter": 0.408,
            "Pitcher": 0.401
        },
        "1926": {
            "Hitter": 0.388,
            "Pitcher": 0.395
        },
        "1927": {
            "Hitter": 0.389,
            "Pitcher": 0.401
        },
        "1928": {
            "Hitter": 0.396,
            "Pitcher": 0.398
        },
        "1929": {
            "Hitter": 0.408,
            "Pitcher": 0.418
        },
        "1930": {
            "Hitter": 0.414,
            "Pitcher": 0.423
        },
        "1931": {
            "Hitter": 0.388,
            "Pitcher": 0.403
        },
        "1932": {
            "Hitter": 0.368,
            "Pitcher": 0.378
        },
        "1933": {
            "Hitter": 0.379,
            "Pitcher": 0.386
        },
        "1934": {
            "Hitter": 0.384,
            "Pitcher": 0.406
        },
        "1935": {
            "Hitter": 0.404,
            "Pitcher": 0.411
        },
        "1936": {
            "Hitter": 0.401,
            "Pitcher": 0.407
        },
        "1937": {
            "Hitter": 0.401,
            "Pitcher": 0.397
        },
        "1938": {
            "Hitter": 0.384,
            "Pitcher": 0.389
        },
        "1939": {
            "Hitter": 0.387,
            "Pitcher": 0.389
        },
        "1940": {
            "Hitter": 0.383,
            "Pitcher": 0.39
        },
        "1941": {
            "Hitter": 0.366,
            "Pitcher": 0.364
        },
        "1942": {
            "Hitter": 0.347,
            "Pitcher": 0.347
        },
        "1943": {
            "Hitter": 0.353,
            "Pitcher": 0.353
        },
        "1944": {
            "Hitter": 0.359,
            "Pitcher": 0.358
        },
        "1945": {
            "Hitter": 0.364,
            "Pitcher": 0.352
        },
        "1946": {
            "Hitter": 0.366,
            "Pitcher": 0.369
        },
        "1947": {
            "Hitter": 0.379,
            "Pitcher": 0.379
        },
        "1948": {
            "Hitter": 0.379,
            "Pitcher": 0.38
        },
        "1949": {
            "Hitter": 0.388,
            "Pitcher": 0.386
        },
        "1950": {
            "Hitter": 0.407,
            "Pitcher": 0.405
        },
        "1951": {
            "Hitter": 0.387,
            "Pitcher": 0.398
        },
        "1952": {
            "Hitter": 0.378,
            "Pitcher": 0.387
        },
        "1953": {
            "Hitter": 0.406,
            "Pitcher": 0.4
        },
        "1954": {
            "Hitter": 0.393,
            "Pitcher": 0.396
        },
        "1955": {
            "Hitter": 0.401,
            "Pitcher": 0.393
        },
        "1956": {
            "Hitter": 0.401,
            "Pitcher": 0.395
        },
        "1957": {
            "Hitter": 0.397,
            "Pitcher": 0.389
        },
        "1958": {
            "Hitter": 0.402,
            "Pitcher": 0.4
        },
        "1959": {
            "Hitter": 0.4,
            "Pitcher": 0.408
        },
        "1960": {
            "Hitter": 0.396,
            "Pitcher": 0.389
        },
        "1961": {
            "Hitter": 0.404,
            "Pitcher": 0.396
        },
        "1962": {
            "Hitter": 0.398,
            "Pitcher": 0.388
        },
        "1963": {
            "Hitter": 0.38,
            "Pitcher": 0.379
        },
        "1964": {
            "Hitter": 0.382,
            "Pitcher": 0.377
        },
        "1965": {
            "Hitter": 0.377,
            "Pitcher": 0.376
        },
        "1966": {
            "Hitter": 0.378,
            "Pitcher": 0.367
        },
        "1967": {
            "Hitter": 0.36,
            "Pitcher": 0.365
        },
        "1968": {
            "Hitter": 0.347,
            "Pitcher": 0.347
        },
        "1969": {
            "Hitter": 0.375,
            "Pitcher": 0.376
        },
        "1970": {
            "Hitter": 0.393,
            "Pitcher": 0.388
        },
        "1971": {
            "Hitter": 0.371,
            "Pitcher": 0.368
        },
        "1972": {
            "Hitter": 0.359,
            "Pitcher": 0.363
        },
        "1973": {
            "Hitter": 0.378,
            "Pitcher": 0.384
        },
        "1974": {
            "Hitter": 0.37,
            "Pitcher": 0.377
        },
        "1975": {
            "Hitter": 0.377,
            "Pitcher": 0.374
        },
        "1976": {
            "Hitter": 0.363,
            "Pitcher": 0.363
        },
        "1977": {
            "Hitter": 0.398,
            "Pitcher": 0.402
        },
        "1978": {
            "Hitter": 0.377,
            "Pitcher": 0.378
        },
        "1979": {
            "Hitter": 0.396,
            "Pitcher": 0.392
        },
        "1980": {
            "Hitter": 0.39,
            "Pitcher": 0.388
        },
        "1981": {
            "Hitter": 0.368,
            "Pitcher": 0.369
        },
        "1982": {
            "Hitter": 0.389,
            "Pitcher": 0.385
        },
        "1983": {
            "Hitter": 0.391,
            "Pitcher": 0.398
        },
        "1984": {
            "Hitter": 0.384,
            "Pitcher": 0.383
        },
        "1985": {
            "Hitter": 0.391,
            "Pitcher": 0.392
        },
        "1986": {
            "Hitter": 0.395,
            "Pitcher": 0.389
        },
        "1987": {
            "Hitter": 0.416,
            "Pitcher": 0.406
        },
        "1988": {
            "Hitter": 0.377,
            "Pitcher": 0.379
        },
        "1989": {
            "Hitter": 0.376,
            "Pitcher": 0.376
        },
        "1990": {
            "Hitter": 0.386,
            "Pitcher": 0.376
        },
        "1991": {
            "Hitter": 0.386,
            "Pitcher": 0.375
        },
        "1992": {
            "Hitter": 0.377,
            "Pitcher": 0.371
        },
        "1993": {
            "Hitter": 0.405,
            "Pitcher": 0.39
        },
        "1994": {
            "Hitter": 0.423,
            "Pitcher": 0.411
        },
        "1995": {
            "Hitter": 0.415,
            "Pitcher": 0.401
        },
        "1996": {
            "Hitter": 0.425,
            "Pitcher": 0.411
        },
        "1997": {
            "Hitter": 0.418,
            "Pitcher": 0.406
        },
        "1998": {
            "Hitter": 0.415,
            "Pitcher": 0.406
        },
        "1999": {
            "Hitter": 0.431,
            "Pitcher": 0.413
        },
        "2000": {
            "Hitter": 0.436,
            "Pitcher": 0.418
        },
        "2001": {
            "Hitter": 0.425,
            "Pitcher": 0.408
        },
        "2002": {
            "Hitter": 0.416,
            "Pitcher": 0.397
        },
        "2003": {
            "Hitter": 0.422,
            "Pitcher": 0.4
        },
        "2004": {
            "Hitter": 0.427,
            "Pitcher": 0.407
        },
        "2005": {
            "Hitter": 0.42,
            "Pitcher": 0.4
        },
        "2006": {
            "Hitter": 0.433,
            "Pitcher": 0.406
        },
        "2007": {
            "Hitter": 0.42,
            "Pitcher": 0.4
        },
        "2008": {
            "Hitter": 0.416,
            "Pitcher": 0.393
        },
        "2009": {
            "Hitter": 0.418,
            "Pitcher": 0.394
        },
        "2010": {
            "Hitter": 0.404,
            "Pitcher": 0.383
        },
        "2011": {
            "Hitter": 0.4,
            "Pitcher": 0.375
        },
        "2012": {
            "Hitter": 0.408,
            "Pitcher": 0.377
        },
        "2013": {
            "Hitter": 0.399,
            "Pitcher": 0.374
        },
        "2014": {
            "Hitter": 0.387,
            "Pitcher": 0.364
        },
        "2015": {
            "Hitter": 0.407,
            "Pitcher": 0.378
        },
        "2016": {
            "Hitter": 0.417,
            "Pitcher": 0.39
        },
        "2017": {
            "Hitter": 0.428,
            "Pitcher": 0.398
        },
        "2018": {
            "Hitter": 0.411,
            "Pitcher": 0.383
        },
        "2019": {
            "Hitter": 0.438,
            "Pitcher": 0.408
        },
        "2020": {
            "Hitter": 0.409,
            "Pitcher": 0.379
        },
        "2021": {
            "Hitter": 0.413,
            "Pitcher": 0.379
        },
        "2022": {
            "Hitter": 0.391,
            "Pitcher": 0.363
        }
    },
    EXPANDED_SET: {
        "1900": {
            "Hitter": 0.39,
            "Pitcher": 0.373
        },
        "1901": {
            "Hitter": 0.387,
            "Pitcher": 0.424
        },
        "1902": {
            "Hitter": 0.372,
            "Pitcher": 0.407
        },
        "1903": {
            "Hitter": 0.376,
            "Pitcher": 0.38
        },
        "1904": {
            "Hitter": 0.356,
            "Pitcher": 0.349
        },
        "1905": {
            "Hitter": 0.357,
            "Pitcher": 0.369
        },
        "1906": {
            "Hitter": 0.354,
            "Pitcher": 0.361
        },
        "1907": {
            "Hitter": 0.351,
            "Pitcher": 0.367
        },
        "1908": {
            "Hitter": 0.346,
            "Pitcher": 0.322
        },
        "1909": {
            "Hitter": 0.352,
            "Pitcher": 0.322
        },
        "1910": {
            "Hitter": 0.361,
            "Pitcher": 0.35
        },
        "1911": {
            "Hitter": 0.388,
            "Pitcher": 0.362
        },
        "1912": {
            "Hitter": 0.392,
            "Pitcher": 0.386
        },
        "1913": {
            "Hitter": 0.376,
            "Pitcher": 0.35
        },
        "1914": {
            "Hitter": 0.37,
            "Pitcher": 0.373
        },
        "1915": {
            "Hitter": 0.364,
            "Pitcher": 0.365
        },
        "1916": {
            "Hitter": 0.364,
            "Pitcher": 0.339
        },
        "1917": {
            "Hitter": 0.359,
            "Pitcher": 0.339
        },
        "1918": {
            "Hitter": 0.362,
            "Pitcher": 0.356
        },
        "1919": {
            "Hitter": 0.381,
            "Pitcher": 0.365
        },
        "1920": {
            "Hitter": 0.383,
            "Pitcher": 0.388
        },
        "1921": {
            "Hitter": 0.409,
            "Pitcher": 0.395
        },
        "1922": {
            "Hitter": 0.418,
            "Pitcher": 0.403
        },
        "1923": {
            "Hitter": 0.412,
            "Pitcher": 0.4
        },
        "1924": {
            "Hitter": 0.407,
            "Pitcher": 0.411
        },
        "1925": {
            "Hitter": 0.427,
            "Pitcher": 0.419
        },
        "1926": {
            "Hitter": 0.409,
            "Pitcher": 0.412
        },
        "1927": {
            "Hitter": 0.411,
            "Pitcher": 0.413
        },
        "1928": {
            "Hitter": 0.418,
            "Pitcher": 0.408
        },
        "1929": {
            "Hitter": 0.426,
            "Pitcher": 0.429
        },
        "1930": {
            "Hitter": 0.432,
            "Pitcher": 0.437
        },
        "1931": {
            "Hitter": 0.41,
            "Pitcher": 0.42
        },
        "1932": {
            "Hitter": 0.394,
            "Pitcher": 0.397
        },
        "1933": {
            "Hitter": 0.402,
            "Pitcher": 0.399
        },
        "1934": {
            "Hitter": 0.404,
            "Pitcher": 0.419
        },
        "1935": {
            "Hitter": 0.423,
            "Pitcher": 0.424
        },
        "1936": {
            "Hitter": 0.42,
            "Pitcher": 0.422
        },
        "1937": {
            "Hitter": 0.42,
            "Pitcher": 0.41
        },
        "1938": {
            "Hitter": 0.407,
            "Pitcher": 0.403
        },
        "1939": {
            "Hitter": 0.408,
            "Pitcher": 0.406
        },
        "1940": {
            "Hitter": 0.405,
            "Pitcher": 0.402
        },
        "1941": {
            "Hitter": 0.39,
            "Pitcher": 0.376
        },
        "1942": {
            "Hitter": 0.374,
            "Pitcher": 0.361
        },
        "1943": {
            "Hitter": 0.378,
            "Pitcher": 0.366
        },
        "1944": {
            "Hitter": 0.385,
            "Pitcher": 0.373
        },
        "1945": {
            "Hitter": 0.388,
            "Pitcher": 0.367
        },
        "1946": {
            "Hitter": 0.388,
            "Pitcher": 0.382
        },
        "1947": {
            "Hitter": 0.398,
            "Pitcher": 0.395
        },
        "1948": {
            "Hitter": 0.399,
            "Pitcher": 0.396
        },
        "1949": {
            "Hitter": 0.401,
            "Pitcher": 0.397
        },
        "1950": {
            "Hitter": 0.418,
            "Pitcher": 0.413
        },
        "1951": {
            "Hitter": 0.402,
            "Pitcher": 0.408
        },
        "1952": {
            "Hitter": 0.391,
            "Pitcher": 0.397
        },
        "1953": {
            "Hitter": 0.418,
            "Pitcher": 0.408
        },
        "1954": {
            "Hitter": 0.404,
            "Pitcher": 0.401
        },
        "1955": {
            "Hitter": 0.411,
            "Pitcher": 0.395
        },
        "1956": {
            "Hitter": 0.411,
            "Pitcher": 0.402
        },
        "1957": {
            "Hitter": 0.407,
            "Pitcher": 0.392
        },
        "1958": {
            "Hitter": 0.412,
            "Pitcher": 0.405
        },
        "1959": {
            "Hitter": 0.411,
            "Pitcher": 0.409
        },
        "1960": {
            "Hitter": 0.407,
            "Pitcher": 0.391
        },
        "1961": {
            "Hitter": 0.415,
            "Pitcher": 0.402
        },
        "1962": {
            "Hitter": 0.409,
            "Pitcher": 0.391
        },
        "1963": {
            "Hitter": 0.392,
            "Pitcher": 0.384
        },
        "1964": {
            "Hitter": 0.395,
            "Pitcher": 0.38
        },
        "1965": {
            "Hitter": 0.39,
            "Pitcher": 0.381
        },
        "1966": {
            "Hitter": 0.391,
            "Pitcher": 0.371
        },
        "1967": {
            "Hitter": 0.375,
            "Pitcher": 0.371
        },
        "1968": {
            "Hitter": 0.364,
            "Pitcher": 0.353
        },
        "1969": {
            "Hitter": 0.388,
            "Pitcher": 0.384
        },
        "1970": {
            "Hitter": 0.405,
            "Pitcher": 0.391
        },
        "1971": {
            "Hitter": 0.385,
            "Pitcher": 0.373
        },
        "1972": {
            "Hitter": 0.375,
            "Pitcher": 0.369
        },
        "1973": {
            "Hitter": 0.39,
            "Pitcher": 0.387
        },
        "1974": {
            "Hitter": 0.384,
            "Pitcher": 0.384
        },
        "1975": {
            "Hitter": 0.391,
            "Pitcher": 0.38
        },
        "1976": {
            "Hitter": 0.379,
            "Pitcher": 0.371
        },
        "1977": {
            "Hitter": 0.412,
            "Pitcher": 0.403
        },
        "1978": {
            "Hitter": 0.391,
            "Pitcher": 0.384
        },
        "1979": {
            "Hitter": 0.409,
            "Pitcher": 0.396
        },
        "1980": {
            "Hitter": 0.403,
            "Pitcher": 0.395
        },
        "1981": {
            "Hitter": 0.385,
            "Pitcher": 0.374
        },
        "1982": {
            "Hitter": 0.402,
            "Pitcher": 0.388
        },
        "1983": {
            "Hitter": 0.404,
            "Pitcher": 0.401
        },
        "1984": {
            "Hitter": 0.398,
            "Pitcher": 0.387
        },
        "1985": {
            "Hitter": 0.403,
            "Pitcher": 0.394
        },
        "1986": {
            "Hitter": 0.407,
            "Pitcher": 0.392
        },
        "1987": {
            "Hitter": 0.427,
            "Pitcher": 0.407
        },
        "1988": {
            "Hitter": 0.391,
            "Pitcher": 0.384
        },
        "1989": {
            "Hitter": 0.389,
            "Pitcher": 0.383
        },
        "1990": {
            "Hitter": 0.399,
            "Pitcher": 0.379
        },
        "1991": {
            "Hitter": 0.399,
            "Pitcher": 0.379
        },
        "1992": {
            "Hitter": 0.391,
            "Pitcher": 0.374
        },
        "1993": {
            "Hitter": 0.416,
            "Pitcher": 0.394
        },
        "1994": {
            "Hitter": 0.434,
            "Pitcher": 0.413
        },
        "1995": {
            "Hitter": 0.427,
            "Pitcher": 0.404
        },
        "1996": {
            "Hitter": 0.435,
            "Pitcher": 0.41
        },
        "1997": {
            "Hitter": 0.427,
            "Pitcher": 0.406
        },
        "1998": {
            "Hitter": 0.427,
            "Pitcher": 0.405
        },
        "1999": {
            "Hitter": 0.441,
            "Pitcher": 0.416
        },
        "2000": {
            "Hitter": 0.445,
            "Pitcher": 0.417
        },
        "2001": {
            "Hitter": 0.434,
            "Pitcher": 0.407
        },
        "2002": {
            "Hitter": 0.427,
            "Pitcher": 0.394
        },
        "2003": {
            "Hitter": 0.432,
            "Pitcher": 0.399
        },
        "2004": {
            "Hitter": 0.437,
            "Pitcher": 0.404
        },
        "2005": {
            "Hitter": 0.43,
            "Pitcher": 0.398
        },
        "2006": {
            "Hitter": 0.442,
            "Pitcher": 0.405
        },
        "2007": {
            "Hitter": 0.432,
            "Pitcher": 0.4
        },
        "2008": {
            "Hitter": 0.428,
            "Pitcher": 0.394
        },
        "2009": {
            "Hitter": 0.428,
            "Pitcher": 0.393
        },
        "2010": {
            "Hitter": 0.415,
            "Pitcher": 0.386
        },
        "2011": {
            "Hitter": 0.411,
            "Pitcher": 0.377
        },
        "2012": {
            "Hitter": 0.418,
            "Pitcher": 0.376
        },
        "2013": {
            "Hitter": 0.41,
            "Pitcher": 0.374
        },
        "2014": {
            "Hitter": 0.4,
            "Pitcher": 0.366
        },
        "2015": {
            "Hitter": 0.417,
            "Pitcher": 0.38
        },
        "2016": {
            "Hitter": 0.426,
            "Pitcher": 0.388
        },
        "2017": {
            "Hitter": 0.436,
            "Pitcher": 0.395
        },
        "2018": {
            "Hitter": 0.42,
            "Pitcher": 0.382
        },
        "2019": {
            "Hitter": 0.447,
            "Pitcher": 0.405
        },
        "2020": {
            "Hitter": 0.424,
            "Pitcher": 0.38
        },
        "2021": {
            "Hitter": 0.423,
            "Pitcher": 0.378
        },
        "2022": {
            "Hitter": 0.401,
            "Pitcher": 0.367
        }
    }
}

LEAGUE_AVG_COMMAND = {
    "2000": {
        "1900": {
            "Hitter": 7.217,
            "Pitcher": 4.149
        },
        "1901": {
            "Hitter": 6.782,
            "Pitcher": 2.765
        },
        "1902": {
            "Hitter": 6.61,
            "Pitcher": 3.232
        },
        "1903": {
            "Hitter": 6.51,
            "Pitcher": 3.609
        },
        "1904": {
            "Hitter": 5.971,
            "Pitcher": 4.092
        },
        "1905": {
            "Hitter": 6.266,
            "Pitcher": 3.864
        },
        "1906": {
            "Hitter": 6.208,
            "Pitcher": 3.807
        },
        "1907": {
            "Hitter": 6.183,
            "Pitcher": 3.784
        },
        "1908": {
            "Hitter": 5.971,
            "Pitcher": 4.698
        },
        "1909": {
            "Hitter": 6.288,
            "Pitcher": 4.628
        },
        "1910": {
            "Hitter": 6.589,
            "Pitcher": 4.171
        },
        "1911": {
            "Hitter": 7.274,
            "Pitcher": 4.008
        },
        "1912": {
            "Hitter": 7.287,
            "Pitcher": 3.748
        },
        "1913": {
            "Hitter": 6.87,
            "Pitcher": 3.987
        },
        "1914": {
            "Hitter": 6.777,
            "Pitcher": 3.427
        },
        "1915": {
            "Hitter": 6.608,
            "Pitcher": 3.843
        },
        "1916": {
            "Hitter": 6.466,
            "Pitcher": 4.205
        },
        "1917": {
            "Hitter": 6.389,
            "Pitcher": 4.282
        },
        "1918": {
            "Hitter": 6.611,
            "Pitcher": 4.022
        },
        "1919": {
            "Hitter": 6.742,
            "Pitcher": 3.764
        },
        "1920": {
            "Hitter": 6.913,
            "Pitcher": 3.51
        },
        "1921": {
            "Hitter": 7.326,
            "Pitcher": 3.651
        },
        "1922": {
            "Hitter": 7.516,
            "Pitcher": 3.312
        },
        "1923": {
            "Hitter": 7.313,
            "Pitcher": 3.368
        },
        "1924": {
            "Hitter": 7.301,
            "Pitcher": 3.558
        },
        "1925": {
            "Hitter": 7.567,
            "Pitcher": 3.392
        },
        "1926": {
            "Hitter": 7.423,
            "Pitcher": 3.416
        },
        "1927": {
            "Hitter": 7.381,
            "Pitcher": 3.494
        },
        "1928": {
            "Hitter": 7.374,
            "Pitcher": 3.443
        },
        "1929": {
            "Hitter": 7.659,
            "Pitcher": 3.041
        },
        "1930": {
            "Hitter": 7.457,
            "Pitcher": 3.067
        },
        "1931": {
            "Hitter": 7.304,
            "Pitcher": 3.359
        },
        "1932": {
            "Hitter": 6.863,
            "Pitcher": 3.771
        },
        "1933": {
            "Hitter": 6.885,
            "Pitcher": 3.667
        },
        "1934": {
            "Hitter": 7.256,
            "Pitcher": 3.312
        },
        "1935": {
            "Hitter": 7.539,
            "Pitcher": 3.204
        },
        "1936": {
            "Hitter": 7.655,
            "Pitcher": 3.315
        },
        "1937": {
            "Hitter": 7.44,
            "Pitcher": 3.326
        },
        "1938": {
            "Hitter": 7.274,
            "Pitcher": 3.44
        },
        "1939": {
            "Hitter": 7.212,
            "Pitcher": 3.552
        },
        "1940": {
            "Hitter": 7.161,
            "Pitcher": 3.395
        },
        "1941": {
            "Hitter": 6.89,
            "Pitcher": 3.673
        },
        "1942": {
            "Hitter": 6.686,
            "Pitcher": 4.04
        },
        "1943": {
            "Hitter": 6.849,
            "Pitcher": 3.992
        },
        "1944": {
            "Hitter": 6.951,
            "Pitcher": 3.829
        },
        "1945": {
            "Hitter": 7.041,
            "Pitcher": 4.055
        },
        "1946": {
            "Hitter": 7.093,
            "Pitcher": 3.643
        },
        "1947": {
            "Hitter": 7.312,
            "Pitcher": 3.417
        },
        "1948": {
            "Hitter": 7.255,
            "Pitcher": 3.414
        },
        "1949": {
            "Hitter": 7.543,
            "Pitcher": 3.011
        },
        "1950": {
            "Hitter": 7.639,
            "Pitcher": 2.653
        },
        "1951": {
            "Hitter": 7.211,
            "Pitcher": 3.104
        },
        "1952": {
            "Hitter": 7.043,
            "Pitcher": 3.228
        },
        "1953": {
            "Hitter": 7.38,
            "Pitcher": 2.946
        },
        "1954": {
            "Hitter": 7.192,
            "Pitcher": 2.921
        },
        "1955": {
            "Hitter": 7.178,
            "Pitcher": 3.105
        },
        "1956": {
            "Hitter": 7.183,
            "Pitcher": 2.789
        },
        "1957": {
            "Hitter": 6.962,
            "Pitcher": 3.1
        },
        "1958": {
            "Hitter": 6.928,
            "Pitcher": 3.159
        },
        "1959": {
            "Hitter": 6.957,
            "Pitcher": 2.926
        },
        "1960": {
            "Hitter": 6.962,
            "Pitcher": 3.127
        },
        "1961": {
            "Hitter": 7.081,
            "Pitcher": 2.968
        },
        "1962": {
            "Hitter": 7.081,
            "Pitcher": 3.016
        },
        "1963": {
            "Hitter": 6.531,
            "Pitcher": 3.302
        },
        "1964": {
            "Hitter": 6.55,
            "Pitcher": 3.42
        },
        "1965": {
            "Hitter": 6.542,
            "Pitcher": 3.484
        },
        "1966": {
            "Hitter": 6.421,
            "Pitcher": 3.478
        },
        "1967": {
            "Hitter": 6.341,
            "Pitcher": 3.81
        },
        "1968": {
            "Hitter": 6.096,
            "Pitcher": 3.893
        },
        "1969": {
            "Hitter": 6.865,
            "Pitcher": 3.241
        },
        "1970": {
            "Hitter": 7.067,
            "Pitcher": 3.179
        },
        "1971": {
            "Hitter": 6.728,
            "Pitcher": 3.479
        },
        "1972": {
            "Hitter": 6.529,
            "Pitcher": 3.639
        },
        "1973": {
            "Hitter": 6.869,
            "Pitcher": 3.306
        },
        "1974": {
            "Hitter": 6.776,
            "Pitcher": 3.472
        },
        "1975": {
            "Hitter": 6.987,
            "Pitcher": 3.356
        },
        "1976": {
            "Hitter": 6.712,
            "Pitcher": 3.772
        },
        "1977": {
            "Hitter": 6.968,
            "Pitcher": 3.176
        },
        "1978": {
            "Hitter": 6.811,
            "Pitcher": 3.567
        },
        "1979": {
            "Hitter": 7.062,
            "Pitcher": 3.283
        },
        "1980": {
            "Hitter": 6.926,
            "Pitcher": 3.39
        },
        "1981": {
            "Hitter": 6.675,
            "Pitcher": 3.631
        },
        "1982": {
            "Hitter": 6.858,
            "Pitcher": 3.472
        },
        "1983": {
            "Hitter": 6.95,
            "Pitcher": 3.512
        },
        "1984": {
            "Hitter": 6.83,
            "Pitcher": 3.517
        },
        "1985": {
            "Hitter": 6.787,
            "Pitcher": 3.377
        },
        "1986": {
            "Hitter": 6.912,
            "Pitcher": 3.399
        },
        "1987": {
            "Hitter": 7.136,
            "Pitcher": 3.07
        },
        "1988": {
            "Hitter": 6.637,
            "Pitcher": 3.623
        },
        "1989": {
            "Hitter": 6.636,
            "Pitcher": 3.574
        },
        "1990": {
            "Hitter": 6.896,
            "Pitcher": 3.546
        },
        "1991": {
            "Hitter": 6.876,
            "Pitcher": 3.47
        },
        "1992": {
            "Hitter": 6.757,
            "Pitcher": 3.591
        },
        "1993": {
            "Hitter": 7.104,
            "Pitcher": 3.159
        },
        "1994": {
            "Hitter": 7.327,
            "Pitcher": 2.883
        },
        "1995": {
            "Hitter": 7.297,
            "Pitcher": 2.931
        },
        "1996": {
            "Hitter": 7.374,
            "Pitcher": 2.879
        },
        "1997": {
            "Hitter": 7.258,
            "Pitcher": 2.994
        },
        "1998": {
            "Hitter": 7.172,
            "Pitcher": 3.018
        },
        "1999": {
            "Hitter": 7.51,
            "Pitcher": 2.788
        },
        "2000": {
            "Hitter": 7.515,
            "Pitcher": 2.703
        },
        "2001": {
            "Hitter": 7.097,
            "Pitcher": 3.126
        },
        "2002": {
            "Hitter": 7.056,
            "Pitcher": 3.113
        },
        "2003": {
            "Hitter": 7.128,
            "Pitcher": 3.031
        },
        "2004": {
            "Hitter": 7.169,
            "Pitcher": 3.095
        },
        "2005": {
            "Hitter": 7.085,
            "Pitcher": 3.077
        },
        "2006": {
            "Hitter": 7.259,
            "Pitcher": 3.021
        },
        "2007": {
            "Hitter": 7.221,
            "Pitcher": 3.151
        },
        "2008": {
            "Hitter": 7.164,
            "Pitcher": 3.272
        },
        "2009": {
            "Hitter": 7.123,
            "Pitcher": 3.233
        },
        "2010": {
            "Hitter": 6.887,
            "Pitcher": 3.441
        },
        "2011": {
            "Hitter": 6.751,
            "Pitcher": 3.662
        },
        "2012": {
            "Hitter": 6.662,
            "Pitcher": 3.549
        },
        "2013": {
            "Hitter": 6.608,
            "Pitcher": 3.628
        },
        "2014": {
            "Hitter": 6.487,
            "Pitcher": 3.792
        },
        "2015": {
            "Hitter": 6.621,
            "Pitcher": 3.526
        },
        "2016": {
            "Hitter": 6.785,
            "Pitcher": 3.477
        },
        "2017": {
            "Hitter": 6.905,
            "Pitcher": 3.31
        },
        "2018": {
            "Hitter": 6.646,
            "Pitcher": 3.556
        },
        "2019": {
            "Hitter": 6.813,
            "Pitcher": 3.295
        },
        "2020": {
            "Hitter": 6.626,
            "Pitcher": 3.579
        },
        "2021": {
            "Hitter": 6.656,
            "Pitcher": 3.438
        },
        "2022": {
            "Hitter": 6.3,
            "Pitcher": 3.79
        }
    },
    "2001": {
        "1900": {
            "Hitter": 7.481,
            "Pitcher": 4.66
        },
        "1901": {
            "Hitter": 7.073,
            "Pitcher": 3.42
        },
        "1902": {
            "Hitter": 6.912,
            "Pitcher": 3.841
        },
        "1903": {
            "Hitter": 6.738,
            "Pitcher": 4.034
        },
        "1904": {
            "Hitter": 6.329,
            "Pitcher": 4.494
        },
        "1905": {
            "Hitter": 6.633,
            "Pitcher": 4.205
        },
        "1906": {
            "Hitter": 6.585,
            "Pitcher": 4.295
        },
        "1907": {
            "Hitter": 6.562,
            "Pitcher": 4.216
        },
        "1908": {
            "Hitter": 6.314,
            "Pitcher": 4.962
        },
        "1909": {
            "Hitter": 6.663,
            "Pitcher": 5.044
        },
        "1910": {
            "Hitter": 6.904,
            "Pitcher": 4.558
        },
        "1911": {
            "Hitter": 7.587,
            "Pitcher": 4.477
        },
        "1912": {
            "Hitter": 7.603,
            "Pitcher": 4.283
        },
        "1913": {
            "Hitter": 7.231,
            "Pitcher": 4.37
        },
        "1914": {
            "Hitter": 7.135,
            "Pitcher": 3.875
        },
        "1915": {
            "Hitter": 6.984,
            "Pitcher": 4.132
        },
        "1916": {
            "Hitter": 6.822,
            "Pitcher": 4.568
        },
        "1917": {
            "Hitter": 6.731,
            "Pitcher": 4.588
        },
        "1918": {
            "Hitter": 6.953,
            "Pitcher": 4.459
        },
        "1919": {
            "Hitter": 7.124,
            "Pitcher": 4.107
        },
        "1920": {
            "Hitter": 7.244,
            "Pitcher": 3.976
        },
        "1921": {
            "Hitter": 7.623,
            "Pitcher": 3.888
        },
        "1922": {
            "Hitter": 7.782,
            "Pitcher": 3.712
        },
        "1923": {
            "Hitter": 7.645,
            "Pitcher": 3.676
        },
        "1924": {
            "Hitter": 7.576,
            "Pitcher": 4.0
        },
        "1925": {
            "Hitter": 7.82,
            "Pitcher": 3.799
        },
        "1926": {
            "Hitter": 7.736,
            "Pitcher": 3.732
        },
        "1927": {
            "Hitter": 7.679,
            "Pitcher": 3.84
        },
        "1928": {
            "Hitter": 7.688,
            "Pitcher": 3.611
        },
        "1929": {
            "Hitter": 7.911,
            "Pitcher": 3.257
        },
        "1930": {
            "Hitter": 7.784,
            "Pitcher": 3.351
        },
        "1931": {
            "Hitter": 7.615,
            "Pitcher": 3.724
        },
        "1932": {
            "Hitter": 7.181,
            "Pitcher": 4.039
        },
        "1933": {
            "Hitter": 7.185,
            "Pitcher": 3.881
        },
        "1934": {
            "Hitter": 7.531,
            "Pitcher": 3.554
        },
        "1935": {
            "Hitter": 7.827,
            "Pitcher": 3.489
        },
        "1936": {
            "Hitter": 7.889,
            "Pitcher": 3.648
        },
        "1937": {
            "Hitter": 7.71,
            "Pitcher": 3.473
        },
        "1938": {
            "Hitter": 7.512,
            "Pitcher": 3.736
        },
        "1939": {
            "Hitter": 7.512,
            "Pitcher": 3.811
        },
        "1940": {
            "Hitter": 7.458,
            "Pitcher": 3.713
        },
        "1941": {
            "Hitter": 7.157,
            "Pitcher": 4.024
        },
        "1942": {
            "Hitter": 7.014,
            "Pitcher": 4.263
        },
        "1943": {
            "Hitter": 7.149,
            "Pitcher": 4.358
        },
        "1944": {
            "Hitter": 7.26,
            "Pitcher": 4.123
        },
        "1945": {
            "Hitter": 7.307,
            "Pitcher": 4.29
        },
        "1946": {
            "Hitter": 7.4,
            "Pitcher": 3.918
        },
        "1947": {
            "Hitter": 7.671,
            "Pitcher": 3.69
        },
        "1948": {
            "Hitter": 7.578,
            "Pitcher": 3.773
        },
        "1949": {
            "Hitter": 7.822,
            "Pitcher": 3.084
        },
        "1950": {
            "Hitter": 7.966,
            "Pitcher": 2.816
        },
        "1951": {
            "Hitter": 7.569,
            "Pitcher": 3.291
        },
        "1952": {
            "Hitter": 7.385,
            "Pitcher": 3.43
        },
        "1953": {
            "Hitter": 7.707,
            "Pitcher": 2.995
        },
        "1954": {
            "Hitter": 7.524,
            "Pitcher": 3.011
        },
        "1955": {
            "Hitter": 7.553,
            "Pitcher": 3.005
        },
        "1956": {
            "Hitter": 7.5,
            "Pitcher": 2.955
        },
        "1957": {
            "Hitter": 7.298,
            "Pitcher": 2.93
        },
        "1958": {
            "Hitter": 7.282,
            "Pitcher": 3.1
        },
        "1959": {
            "Hitter": 7.325,
            "Pitcher": 3.059
        },
        "1960": {
            "Hitter": 7.394,
            "Pitcher": 3.127
        },
        "1961": {
            "Hitter": 7.355,
            "Pitcher": 3.06
        },
        "1962": {
            "Hitter": 7.473,
            "Pitcher": 2.914
        },
        "1963": {
            "Hitter": 6.865,
            "Pitcher": 3.464
        },
        "1964": {
            "Hitter": 6.942,
            "Pitcher": 3.367
        },
        "1965": {
            "Hitter": 6.938,
            "Pitcher": 3.496
        },
        "1966": {
            "Hitter": 6.851,
            "Pitcher": 3.502
        },
        "1967": {
            "Hitter": 6.743,
            "Pitcher": 3.842
        },
        "1968": {
            "Hitter": 6.554,
            "Pitcher": 3.971
        },
        "1969": {
            "Hitter": 7.138,
            "Pitcher": 3.332
        },
        "1970": {
            "Hitter": 7.404,
            "Pitcher": 3.189
        },
        "1971": {
            "Hitter": 7.106,
            "Pitcher": 3.575
        },
        "1972": {
            "Hitter": 6.849,
            "Pitcher": 3.918
        },
        "1973": {
            "Hitter": 7.218,
            "Pitcher": 3.385
        },
        "1974": {
            "Hitter": 7.183,
            "Pitcher": 3.655
        },
        "1975": {
            "Hitter": 7.298,
            "Pitcher": 3.516
        },
        "1976": {
            "Hitter": 7.128,
            "Pitcher": 3.903
        },
        "1977": {
            "Hitter": 7.333,
            "Pitcher": 3.166
        },
        "1978": {
            "Hitter": 7.183,
            "Pitcher": 3.627
        },
        "1979": {
            "Hitter": 7.402,
            "Pitcher": 3.327
        },
        "1980": {
            "Hitter": 7.304,
            "Pitcher": 3.41
        },
        "1981": {
            "Hitter": 7.018,
            "Pitcher": 3.793
        },
        "1982": {
            "Hitter": 7.243,
            "Pitcher": 3.491
        },
        "1983": {
            "Hitter": 7.278,
            "Pitcher": 3.599
        },
        "1984": {
            "Hitter": 7.194,
            "Pitcher": 3.576
        },
        "1985": {
            "Hitter": 7.186,
            "Pitcher": 3.45
        },
        "1986": {
            "Hitter": 7.327,
            "Pitcher": 3.42
        },
        "1987": {
            "Hitter": 7.435,
            "Pitcher": 3.161
        },
        "1988": {
            "Hitter": 6.988,
            "Pitcher": 3.717
        },
        "1989": {
            "Hitter": 7.027,
            "Pitcher": 3.598
        },
        "1990": {
            "Hitter": 7.249,
            "Pitcher": 3.433
        },
        "1991": {
            "Hitter": 7.198,
            "Pitcher": 3.541
        },
        "1992": {
            "Hitter": 7.115,
            "Pitcher": 3.603
        },
        "1993": {
            "Hitter": 7.448,
            "Pitcher": 3.212
        },
        "1994": {
            "Hitter": 7.64,
            "Pitcher": 2.992
        },
        "1995": {
            "Hitter": 7.588,
            "Pitcher": 3.074
        },
        "1996": {
            "Hitter": 7.701,
            "Pitcher": 2.923
        },
        "1997": {
            "Hitter": 7.596,
            "Pitcher": 3.05
        },
        "1998": {
            "Hitter": 7.474,
            "Pitcher": 3.064
        },
        "1999": {
            "Hitter": 7.813,
            "Pitcher": 2.809
        },
        "2000": {
            "Hitter": 7.844,
            "Pitcher": 2.792
        },
        "2001": {
            "Hitter": 7.477,
            "Pitcher": 3.113
        },
        "2002": {
            "Hitter": 7.374,
            "Pitcher": 3.213
        },
        "2003": {
            "Hitter": 7.495,
            "Pitcher": 3.138
        },
        "2004": {
            "Hitter": 7.531,
            "Pitcher": 3.179
        },
        "2005": {
            "Hitter": 7.397,
            "Pitcher": 3.18
        },
        "2006": {
            "Hitter": 7.559,
            "Pitcher": 3.01
        },
        "2007": {
            "Hitter": 7.544,
            "Pitcher": 3.167
        },
        "2008": {
            "Hitter": 7.523,
            "Pitcher": 3.328
        },
        "2009": {
            "Hitter": 7.49,
            "Pitcher": 3.277
        },
        "2010": {
            "Hitter": 7.238,
            "Pitcher": 3.459
        },
        "2011": {
            "Hitter": 7.121,
            "Pitcher": 3.646
        },
        "2012": {
            "Hitter": 7.067,
            "Pitcher": 3.613
        },
        "2013": {
            "Hitter": 7.003,
            "Pitcher": 3.718
        },
        "2014": {
            "Hitter": 6.905,
            "Pitcher": 3.926
        },
        "2015": {
            "Hitter": 7.028,
            "Pitcher": 3.579
        },
        "2016": {
            "Hitter": 7.133,
            "Pitcher": 3.482
        },
        "2017": {
            "Hitter": 7.254,
            "Pitcher": 3.351
        },
        "2018": {
            "Hitter": 7.054,
            "Pitcher": 3.621
        },
        "2019": {
            "Hitter": 7.203,
            "Pitcher": 3.369
        },
        "2020": {
            "Hitter": 6.959,
            "Pitcher": 3.7
        },
        "2021": {
            "Hitter": 7.056,
            "Pitcher": 3.582
        },
        "2022": {
            "Hitter": 6.756,
            "Pitcher": 3.856
        }
    },
    "2002": {
        "1900": {
            "Hitter": 9.906,
            "Pitcher": 4.17
        },
        "1901": {
            "Hitter": 9.417,
            "Pitcher": 3.346
        },
        "1902": {
            "Hitter": 9.215,
            "Pitcher": 3.439
        },
        "1903": {
            "Hitter": 9.162,
            "Pitcher": 3.793
        },
        "1904": {
            "Hitter": 8.551,
            "Pitcher": 4.402
        },
        "1905": {
            "Hitter": 8.845,
            "Pitcher": 4.08
        },
        "1906": {
            "Hitter": 8.821,
            "Pitcher": 4.114
        },
        "1907": {
            "Hitter": 8.798,
            "Pitcher": 4.114
        },
        "1908": {
            "Hitter": 8.524,
            "Pitcher": 4.566
        },
        "1909": {
            "Hitter": 8.904,
            "Pitcher": 4.655
        },
        "1910": {
            "Hitter": 9.268,
            "Pitcher": 4.023
        },
        "1911": {
            "Hitter": 9.885,
            "Pitcher": 4.054
        },
        "1912": {
            "Hitter": 9.933,
            "Pitcher": 3.547
        },
        "1913": {
            "Hitter": 9.481,
            "Pitcher": 3.825
        },
        "1914": {
            "Hitter": 9.345,
            "Pitcher": 3.526
        },
        "1915": {
            "Hitter": 9.271,
            "Pitcher": 3.909
        },
        "1916": {
            "Hitter": 9.067,
            "Pitcher": 4.348
        },
        "1917": {
            "Hitter": 8.923,
            "Pitcher": 4.519
        },
        "1918": {
            "Hitter": 9.213,
            "Pitcher": 4.304
        },
        "1919": {
            "Hitter": 9.349,
            "Pitcher": 4.05
        },
        "1920": {
            "Hitter": 9.559,
            "Pitcher": 3.748
        },
        "1921": {
            "Hitter": 9.968,
            "Pitcher": 3.414
        },
        "1922": {
            "Hitter": 10.202,
            "Pitcher": 3.274
        },
        "1923": {
            "Hitter": 9.99,
            "Pitcher": 3.428
        },
        "1924": {
            "Hitter": 10.007,
            "Pitcher": 3.52
        },
        "1925": {
            "Hitter": 10.234,
            "Pitcher": 3.469
        },
        "1926": {
            "Hitter": 10.125,
            "Pitcher": 3.446
        },
        "1927": {
            "Hitter": 10.098,
            "Pitcher": 3.521
        },
        "1928": {
            "Hitter": 10.054,
            "Pitcher": 3.201
        },
        "1929": {
            "Hitter": 10.333,
            "Pitcher": 3.037
        },
        "1930": {
            "Hitter": 10.123,
            "Pitcher": 2.907
        },
        "1931": {
            "Hitter": 9.979,
            "Pitcher": 3.411
        },
        "1932": {
            "Hitter": 9.501,
            "Pitcher": 3.593
        },
        "1933": {
            "Hitter": 9.484,
            "Pitcher": 3.517
        },
        "1934": {
            "Hitter": 9.922,
            "Pitcher": 3.348
        },
        "1935": {
            "Hitter": 10.235,
            "Pitcher": 3.0
        },
        "1936": {
            "Hitter": 10.348,
            "Pitcher": 3.148
        },
        "1937": {
            "Hitter": 10.098,
            "Pitcher": 3.31
        },
        "1938": {
            "Hitter": 9.899,
            "Pitcher": 3.429
        },
        "1939": {
            "Hitter": 9.963,
            "Pitcher": 3.413
        },
        "1940": {
            "Hitter": 9.799,
            "Pitcher": 3.399
        },
        "1941": {
            "Hitter": 9.541,
            "Pitcher": 3.701
        },
        "1942": {
            "Hitter": 9.328,
            "Pitcher": 4.096
        },
        "1943": {
            "Hitter": 9.456,
            "Pitcher": 4.016
        },
        "1944": {
            "Hitter": 9.595,
            "Pitcher": 3.976
        },
        "1945": {
            "Hitter": 9.674,
            "Pitcher": 4.047
        },
        "1946": {
            "Hitter": 9.786,
            "Pitcher": 3.54
        },
        "1947": {
            "Hitter": 9.986,
            "Pitcher": 3.406
        },
        "1948": {
            "Hitter": 9.904,
            "Pitcher": 3.432
        },
        "1949": {
            "Hitter": 10.192,
            "Pitcher": 2.847
        },
        "1950": {
            "Hitter": 10.346,
            "Pitcher": 2.689
        },
        "1951": {
            "Hitter": 9.799,
            "Pitcher": 2.879
        },
        "1952": {
            "Hitter": 9.601,
            "Pitcher": 3.119
        },
        "1953": {
            "Hitter": 10.014,
            "Pitcher": 2.919
        },
        "1954": {
            "Hitter": 9.779,
            "Pitcher": 2.757
        },
        "1955": {
            "Hitter": 9.736,
            "Pitcher": 2.759
        },
        "1956": {
            "Hitter": 9.745,
            "Pitcher": 2.543
        },
        "1957": {
            "Hitter": 9.587,
            "Pitcher": 2.811
        },
        "1958": {
            "Hitter": 9.565,
            "Pitcher": 2.687
        },
        "1959": {
            "Hitter": 9.531,
            "Pitcher": 2.517
        },
        "1960": {
            "Hitter": 9.587,
            "Pitcher": 2.716
        },
        "1961": {
            "Hitter": 9.688,
            "Pitcher": 2.606
        },
        "1962": {
            "Hitter": 9.673,
            "Pitcher": 2.66
        },
        "1963": {
            "Hitter": 9.05,
            "Pitcher": 2.976
        },
        "1964": {
            "Hitter": 9.142,
            "Pitcher": 3.037
        },
        "1965": {
            "Hitter": 9.123,
            "Pitcher": 3.171
        },
        "1966": {
            "Hitter": 8.981,
            "Pitcher": 3.142
        },
        "1967": {
            "Hitter": 8.9,
            "Pitcher": 3.281
        },
        "1968": {
            "Hitter": 8.712,
            "Pitcher": 3.607
        },
        "1969": {
            "Hitter": 9.433,
            "Pitcher": 2.908
        },
        "1970": {
            "Hitter": 9.641,
            "Pitcher": 2.709
        },
        "1971": {
            "Hitter": 9.288,
            "Pitcher": 3.195
        },
        "1972": {
            "Hitter": 9.087,
            "Pitcher": 3.423
        },
        "1973": {
            "Hitter": 9.487,
            "Pitcher": 2.906
        },
        "1974": {
            "Hitter": 9.317,
            "Pitcher": 3.228
        },
        "1975": {
            "Hitter": 9.587,
            "Pitcher": 3.236
        },
        "1976": {
            "Hitter": 9.298,
            "Pitcher": 3.604
        },
        "1977": {
            "Hitter": 9.537,
            "Pitcher": 2.661
        },
        "1978": {
            "Hitter": 9.339,
            "Pitcher": 3.287
        },
        "1979": {
            "Hitter": 9.604,
            "Pitcher": 3.047
        },
        "1980": {
            "Hitter": 9.49,
            "Pitcher": 3.124
        },
        "1981": {
            "Hitter": 9.246,
            "Pitcher": 3.334
        },
        "1982": {
            "Hitter": 9.447,
            "Pitcher": 3.119
        },
        "1983": {
            "Hitter": 9.503,
            "Pitcher": 2.957
        },
        "1984": {
            "Hitter": 9.39,
            "Pitcher": 3.056
        },
        "1985": {
            "Hitter": 9.349,
            "Pitcher": 2.988
        },
        "1986": {
            "Hitter": 9.475,
            "Pitcher": 2.84
        },
        "1987": {
            "Hitter": 9.722,
            "Pitcher": 2.581
        },
        "1988": {
            "Hitter": 9.174,
            "Pitcher": 3.208
        },
        "1989": {
            "Hitter": 9.251,
            "Pitcher": 3.199
        },
        "1990": {
            "Hitter": 9.459,
            "Pitcher": 3.08
        },
        "1991": {
            "Hitter": 9.382,
            "Pitcher": 3.101
        },
        "1992": {
            "Hitter": 9.337,
            "Pitcher": 3.376
        },
        "1993": {
            "Hitter": 9.676,
            "Pitcher": 2.915
        },
        "1994": {
            "Hitter": 9.882,
            "Pitcher": 2.62
        },
        "1995": {
            "Hitter": 9.931,
            "Pitcher": 2.745
        },
        "1996": {
            "Hitter": 9.967,
            "Pitcher": 2.716
        },
        "1997": {
            "Hitter": 9.885,
            "Pitcher": 2.623
        },
        "1998": {
            "Hitter": 9.751,
            "Pitcher": 2.638
        },
        "1999": {
            "Hitter": 10.118,
            "Pitcher": 2.421
        },
        "2000": {
            "Hitter": 10.108,
            "Pitcher": 2.451
        },
        "2001": {
            "Hitter": 9.692,
            "Pitcher": 2.659
        },
        "2002": {
            "Hitter": 9.641,
            "Pitcher": 2.851
        },
        "2003": {
            "Hitter": 9.705,
            "Pitcher": 2.71
        },
        "2004": {
            "Hitter": 9.718,
            "Pitcher": 2.792
        },
        "2005": {
            "Hitter": 9.641,
            "Pitcher": 2.864
        },
        "2006": {
            "Hitter": 9.823,
            "Pitcher": 2.762
        },
        "2007": {
            "Hitter": 9.841,
            "Pitcher": 2.823
        },
        "2008": {
            "Hitter": 9.741,
            "Pitcher": 2.913
        },
        "2009": {
            "Hitter": 9.703,
            "Pitcher": 2.826
        },
        "2010": {
            "Hitter": 9.474,
            "Pitcher": 3.023
        },
        "2011": {
            "Hitter": 9.297,
            "Pitcher": 3.251
        },
        "2012": {
            "Hitter": 9.223,
            "Pitcher": 3.064
        },
        "2013": {
            "Hitter": 9.195,
            "Pitcher": 3.162
        },
        "2014": {
            "Hitter": 9.038,
            "Pitcher": 3.467
        },
        "2015": {
            "Hitter": 9.182,
            "Pitcher": 3.087
        },
        "2016": {
            "Hitter": 9.338,
            "Pitcher": 2.944
        },
        "2017": {
            "Hitter": 9.485,
            "Pitcher": 2.856
        },
        "2018": {
            "Hitter": 9.269,
            "Pitcher": 2.992
        },
        "2019": {
            "Hitter": 9.415,
            "Pitcher": 2.815
        },
        "2020": {
            "Hitter": 9.249,
            "Pitcher": 3.344
        },
        "2021": {
            "Hitter": 9.267,
            "Pitcher": 3.059
        },
        "2022": {
            "Hitter": 8.89,
            "Pitcher": 3.179
        }
    },
    "2003": {
        "1900": {
            "Hitter": 10.009,
            "Pitcher": 4.085
        },
        "1901": {
            "Hitter": 9.495,
            "Pitcher": 3.123
        },
        "1902": {
            "Hitter": 9.385,
            "Pitcher": 3.378
        },
        "1903": {
            "Hitter": 9.295,
            "Pitcher": 3.828
        },
        "1904": {
            "Hitter": 8.725,
            "Pitcher": 4.184
        },
        "1905": {
            "Hitter": 8.976,
            "Pitcher": 3.875
        },
        "1906": {
            "Hitter": 9.0,
            "Pitcher": 3.943
        },
        "1907": {
            "Hitter": 8.933,
            "Pitcher": 3.83
        },
        "1908": {
            "Hitter": 8.71,
            "Pitcher": 4.358
        },
        "1909": {
            "Hitter": 9.0,
            "Pitcher": 4.301
        },
        "1910": {
            "Hitter": 9.359,
            "Pitcher": 3.93
        },
        "1911": {
            "Hitter": 10.014,
            "Pitcher": 3.885
        },
        "1912": {
            "Hitter": 10.033,
            "Pitcher": 3.585
        },
        "1913": {
            "Hitter": 9.625,
            "Pitcher": 3.831
        },
        "1914": {
            "Hitter": 9.539,
            "Pitcher": 3.583
        },
        "1915": {
            "Hitter": 9.369,
            "Pitcher": 3.858
        },
        "1916": {
            "Hitter": 9.207,
            "Pitcher": 4.227
        },
        "1917": {
            "Hitter": 9.101,
            "Pitcher": 4.267
        },
        "1918": {
            "Hitter": 9.289,
            "Pitcher": 4.104
        },
        "1919": {
            "Hitter": 9.512,
            "Pitcher": 4.0
        },
        "1920": {
            "Hitter": 9.669,
            "Pitcher": 3.864
        },
        "1921": {
            "Hitter": 10.054,
            "Pitcher": 3.679
        },
        "1922": {
            "Hitter": 10.301,
            "Pitcher": 3.495
        },
        "1923": {
            "Hitter": 10.078,
            "Pitcher": 3.664
        },
        "1924": {
            "Hitter": 10.048,
            "Pitcher": 3.565
        },
        "1925": {
            "Hitter": 10.35,
            "Pitcher": 3.626
        },
        "1926": {
            "Hitter": 10.249,
            "Pitcher": 3.595
        },
        "1927": {
            "Hitter": 10.168,
            "Pitcher": 3.58
        },
        "1928": {
            "Hitter": 10.142,
            "Pitcher": 3.594
        },
        "1929": {
            "Hitter": 10.436,
            "Pitcher": 3.38
        },
        "1930": {
            "Hitter": 10.281,
            "Pitcher": 3.244
        },
        "1931": {
            "Hitter": 10.073,
            "Pitcher": 3.609
        },
        "1932": {
            "Hitter": 9.619,
            "Pitcher": 3.818
        },
        "1933": {
            "Hitter": 9.618,
            "Pitcher": 3.851
        },
        "1934": {
            "Hitter": 10.049,
            "Pitcher": 3.509
        },
        "1935": {
            "Hitter": 10.294,
            "Pitcher": 3.452
        },
        "1936": {
            "Hitter": 10.399,
            "Pitcher": 3.472
        },
        "1937": {
            "Hitter": 10.22,
            "Pitcher": 3.578
        },
        "1938": {
            "Hitter": 10.016,
            "Pitcher": 3.729
        },
        "1939": {
            "Hitter": 10.016,
            "Pitcher": 3.622
        },
        "1940": {
            "Hitter": 9.976,
            "Pitcher": 3.633
        },
        "1941": {
            "Hitter": 9.607,
            "Pitcher": 3.829
        },
        "1942": {
            "Hitter": 9.452,
            "Pitcher": 4.012
        },
        "1943": {
            "Hitter": 9.578,
            "Pitcher": 4.012
        },
        "1944": {
            "Hitter": 9.745,
            "Pitcher": 3.893
        },
        "1945": {
            "Hitter": 9.803,
            "Pitcher": 4.016
        },
        "1946": {
            "Hitter": 9.866,
            "Pitcher": 3.797
        },
        "1947": {
            "Hitter": 10.11,
            "Pitcher": 3.657
        },
        "1948": {
            "Hitter": 10.052,
            "Pitcher": 3.564
        },
        "1949": {
            "Hitter": 10.212,
            "Pitcher": 3.2
        },
        "1950": {
            "Hitter": 10.476,
            "Pitcher": 2.995
        },
        "1951": {
            "Hitter": 9.967,
            "Pitcher": 3.253
        },
        "1952": {
            "Hitter": 9.721,
            "Pitcher": 3.383
        },
        "1953": {
            "Hitter": 10.034,
            "Pitcher": 3.314
        },
        "1954": {
            "Hitter": 9.899,
            "Pitcher": 3.28
        },
        "1955": {
            "Hitter": 9.904,
            "Pitcher": 3.246
        },
        "1956": {
            "Hitter": 9.861,
            "Pitcher": 3.101
        },
        "1957": {
            "Hitter": 9.659,
            "Pitcher": 3.448
        },
        "1958": {
            "Hitter": 9.708,
            "Pitcher": 3.403
        },
        "1959": {
            "Hitter": 9.656,
            "Pitcher": 3.251
        },
        "1960": {
            "Hitter": 9.688,
            "Pitcher": 3.345
        },
        "1961": {
            "Hitter": 9.799,
            "Pitcher": 3.188
        },
        "1962": {
            "Hitter": 9.758,
            "Pitcher": 3.361
        },
        "1963": {
            "Hitter": 9.162,
            "Pitcher": 3.617
        },
        "1964": {
            "Hitter": 9.242,
            "Pitcher": 3.641
        },
        "1965": {
            "Hitter": 9.262,
            "Pitcher": 3.785
        },
        "1966": {
            "Hitter": 9.111,
            "Pitcher": 3.709
        },
        "1967": {
            "Hitter": 9.05,
            "Pitcher": 3.83
        },
        "1968": {
            "Hitter": 8.873,
            "Pitcher": 4.07
        },
        "1969": {
            "Hitter": 9.593,
            "Pitcher": 3.458
        },
        "1970": {
            "Hitter": 9.756,
            "Pitcher": 3.387
        },
        "1971": {
            "Hitter": 9.423,
            "Pitcher": 3.699
        },
        "1972": {
            "Hitter": 9.26,
            "Pitcher": 3.852
        },
        "1973": {
            "Hitter": 9.603,
            "Pitcher": 3.524
        },
        "1974": {
            "Hitter": 9.503,
            "Pitcher": 3.703
        },
        "1975": {
            "Hitter": 9.708,
            "Pitcher": 3.611
        },
        "1976": {
            "Hitter": 9.442,
            "Pitcher": 3.881
        },
        "1977": {
            "Hitter": 9.676,
            "Pitcher": 3.409
        },
        "1978": {
            "Hitter": 9.422,
            "Pitcher": 3.739
        },
        "1979": {
            "Hitter": 9.751,
            "Pitcher": 3.472
        },
        "1980": {
            "Hitter": 9.676,
            "Pitcher": 3.556
        },
        "1981": {
            "Hitter": 9.399,
            "Pitcher": 3.799
        },
        "1982": {
            "Hitter": 9.604,
            "Pitcher": 3.691
        },
        "1983": {
            "Hitter": 9.624,
            "Pitcher": 3.562
        },
        "1984": {
            "Hitter": 9.449,
            "Pitcher": 3.67
        },
        "1985": {
            "Hitter": 9.453,
            "Pitcher": 3.605
        },
        "1986": {
            "Hitter": 9.596,
            "Pitcher": 3.538
        },
        "1987": {
            "Hitter": 9.814,
            "Pitcher": 3.292
        },
        "1988": {
            "Hitter": 9.333,
            "Pitcher": 3.768
        },
        "1989": {
            "Hitter": 9.355,
            "Pitcher": 3.786
        },
        "1990": {
            "Hitter": 9.612,
            "Pitcher": 3.721
        },
        "1991": {
            "Hitter": 9.562,
            "Pitcher": 3.71
        },
        "1992": {
            "Hitter": 9.47,
            "Pitcher": 3.916
        },
        "1993": {
            "Hitter": 9.786,
            "Pitcher": 3.423
        },
        "1994": {
            "Hitter": 9.978,
            "Pitcher": 3.165
        },
        "1995": {
            "Hitter": 10.03,
            "Pitcher": 3.22
        },
        "1996": {
            "Hitter": 10.074,
            "Pitcher": 3.182
        },
        "1997": {
            "Hitter": 9.97,
            "Pitcher": 3.248
        },
        "1998": {
            "Hitter": 9.851,
            "Pitcher": 3.292
        },
        "1999": {
            "Hitter": 10.256,
            "Pitcher": 3.062
        },
        "2000": {
            "Hitter": 10.236,
            "Pitcher": 2.972
        },
        "2001": {
            "Hitter": 9.844,
            "Pitcher": 3.305
        },
        "2002": {
            "Hitter": 9.751,
            "Pitcher": 3.356
        },
        "2003": {
            "Hitter": 9.841,
            "Pitcher": 3.259
        },
        "2004": {
            "Hitter": 9.874,
            "Pitcher": 3.236
        },
        "2005": {
            "Hitter": 9.733,
            "Pitcher": 3.393
        },
        "2006": {
            "Hitter": 9.949,
            "Pitcher": 3.377
        },
        "2007": {
            "Hitter": 9.936,
            "Pitcher": 3.364
        },
        "2008": {
            "Hitter": 9.851,
            "Pitcher": 3.49
        },
        "2009": {
            "Hitter": 9.797,
            "Pitcher": 3.431
        },
        "2010": {
            "Hitter": 9.587,
            "Pitcher": 3.562
        },
        "2011": {
            "Hitter": 9.377,
            "Pitcher": 3.813
        },
        "2012": {
            "Hitter": 9.356,
            "Pitcher": 3.703
        },
        "2013": {
            "Hitter": 9.277,
            "Pitcher": 3.826
        },
        "2014": {
            "Hitter": 9.156,
            "Pitcher": 4.031
        },
        "2015": {
            "Hitter": 9.29,
            "Pitcher": 3.762
        },
        "2016": {
            "Hitter": 9.459,
            "Pitcher": 3.659
        },
        "2017": {
            "Hitter": 9.603,
            "Pitcher": 3.446
        },
        "2018": {
            "Hitter": 9.349,
            "Pitcher": 3.669
        },
        "2019": {
            "Hitter": 9.521,
            "Pitcher": 3.456
        },
        "2020": {
            "Hitter": 9.364,
            "Pitcher": 3.885
        },
        "2021": {
            "Hitter": 9.369,
            "Pitcher": 3.7
        },
        "2022": {
            "Hitter": 9.056,
            "Pitcher": 3.938
        }
    },
    "2004": {
        "1900": {
            "Hitter": 10.255,
            "Pitcher": 4.468
        },
        "1901": {
            "Hitter": 9.947,
            "Pitcher": 3.099
        },
        "1902": {
            "Hitter": 9.927,
            "Pitcher": 3.5
        },
        "1903": {
            "Hitter": 9.819,
            "Pitcher": 3.793
        },
        "1904": {
            "Hitter": 9.411,
            "Pitcher": 4.287
        },
        "1905": {
            "Hitter": 9.614,
            "Pitcher": 4.159
        },
        "1906": {
            "Hitter": 9.652,
            "Pitcher": 4.284
        },
        "1907": {
            "Hitter": 9.548,
            "Pitcher": 4.261
        },
        "1908": {
            "Hitter": 9.429,
            "Pitcher": 4.689
        },
        "1909": {
            "Hitter": 9.534,
            "Pitcher": 4.637
        },
        "1910": {
            "Hitter": 9.861,
            "Pitcher": 4.116
        },
        "1911": {
            "Hitter": 10.341,
            "Pitcher": 3.838
        },
        "1912": {
            "Hitter": 10.316,
            "Pitcher": 3.503
        },
        "1913": {
            "Hitter": 9.918,
            "Pitcher": 3.831
        },
        "1914": {
            "Hitter": 9.9,
            "Pitcher": 3.625
        },
        "1915": {
            "Hitter": 9.78,
            "Pitcher": 3.883
        },
        "1916": {
            "Hitter": 9.615,
            "Pitcher": 4.386
        },
        "1917": {
            "Hitter": 9.587,
            "Pitcher": 4.534
        },
        "1918": {
            "Hitter": 9.777,
            "Pitcher": 4.622
        },
        "1919": {
            "Hitter": 9.871,
            "Pitcher": 3.893
        },
        "1920": {
            "Hitter": 10.068,
            "Pitcher": 3.767
        },
        "1921": {
            "Hitter": 10.412,
            "Pitcher": 3.67
        },
        "1922": {
            "Hitter": 10.519,
            "Pitcher": 3.495
        },
        "1923": {
            "Hitter": 10.43,
            "Pitcher": 3.632
        },
        "1924": {
            "Hitter": 10.376,
            "Pitcher": 3.658
        },
        "1925": {
            "Hitter": 10.626,
            "Pitcher": 3.626
        },
        "1926": {
            "Hitter": 10.538,
            "Pitcher": 3.602
        },
        "1927": {
            "Hitter": 10.466,
            "Pitcher": 3.537
        },
        "1928": {
            "Hitter": 10.438,
            "Pitcher": 3.627
        },
        "1929": {
            "Hitter": 10.694,
            "Pitcher": 3.171
        },
        "1930": {
            "Hitter": 10.531,
            "Pitcher": 3.124
        },
        "1931": {
            "Hitter": 10.346,
            "Pitcher": 3.547
        },
        "1932": {
            "Hitter": 10.087,
            "Pitcher": 3.829
        },
        "1933": {
            "Hitter": 10.041,
            "Pitcher": 4.025
        },
        "1934": {
            "Hitter": 10.411,
            "Pitcher": 3.446
        },
        "1935": {
            "Hitter": 10.536,
            "Pitcher": 3.471
        },
        "1936": {
            "Hitter": 10.659,
            "Pitcher": 3.366
        },
        "1937": {
            "Hitter": 10.526,
            "Pitcher": 3.453
        },
        "1938": {
            "Hitter": 10.37,
            "Pitcher": 3.634
        },
        "1939": {
            "Hitter": 10.39,
            "Pitcher": 3.637
        },
        "1940": {
            "Hitter": 10.344,
            "Pitcher": 3.584
        },
        "1941": {
            "Hitter": 10.077,
            "Pitcher": 3.9
        },
        "1942": {
            "Hitter": 9.956,
            "Pitcher": 4.211
        },
        "1943": {
            "Hitter": 10.016,
            "Pitcher": 4.24
        },
        "1944": {
            "Hitter": 10.162,
            "Pitcher": 4.107
        },
        "1945": {
            "Hitter": 10.167,
            "Pitcher": 4.039
        },
        "1946": {
            "Hitter": 10.222,
            "Pitcher": 3.801
        },
        "1947": {
            "Hitter": 10.362,
            "Pitcher": 3.59
        },
        "1948": {
            "Hitter": 10.436,
            "Pitcher": 3.487
        },
        "1949": {
            "Hitter": 10.409,
            "Pitcher": 2.984
        },
        "1950": {
            "Hitter": 10.553,
            "Pitcher": 2.711
        },
        "1951": {
            "Hitter": 10.182,
            "Pitcher": 3.126
        },
        "1952": {
            "Hitter": 9.976,
            "Pitcher": 3.316
        },
        "1953": {
            "Hitter": 10.26,
            "Pitcher": 3.146
        },
        "1954": {
            "Hitter": 10.087,
            "Pitcher": 3.127
        },
        "1955": {
            "Hitter": 10.144,
            "Pitcher": 3.068
        },
        "1956": {
            "Hitter": 10.115,
            "Pitcher": 3.045
        },
        "1957": {
            "Hitter": 9.904,
            "Pitcher": 3.303
        },
        "1958": {
            "Hitter": 9.866,
            "Pitcher": 3.174
        },
        "1959": {
            "Hitter": 9.919,
            "Pitcher": 2.98
        },
        "1960": {
            "Hitter": 9.885,
            "Pitcher": 3.269
        },
        "1961": {
            "Hitter": 10.073,
            "Pitcher": 3.078
        },
        "1962": {
            "Hitter": 9.996,
            "Pitcher": 3.156
        },
        "1963": {
            "Hitter": 9.554,
            "Pitcher": 3.512
        },
        "1964": {
            "Hitter": 9.588,
            "Pitcher": 3.518
        },
        "1965": {
            "Hitter": 9.642,
            "Pitcher": 3.695
        },
        "1966": {
            "Hitter": 9.502,
            "Pitcher": 3.522
        },
        "1967": {
            "Hitter": 9.548,
            "Pitcher": 3.787
        },
        "1968": {
            "Hitter": 9.392,
            "Pitcher": 3.983
        },
        "1969": {
            "Hitter": 9.869,
            "Pitcher": 3.431
        },
        "1970": {
            "Hitter": 10.029,
            "Pitcher": 3.311
        },
        "1971": {
            "Hitter": 9.782,
            "Pitcher": 3.503
        },
        "1972": {
            "Hitter": 9.66,
            "Pitcher": 3.753
        },
        "1973": {
            "Hitter": 9.949,
            "Pitcher": 3.368
        },
        "1974": {
            "Hitter": 9.804,
            "Pitcher": 3.548
        },
        "1975": {
            "Hitter": 9.99,
            "Pitcher": 3.495
        },
        "1976": {
            "Hitter": 9.731,
            "Pitcher": 3.84
        },
        "1977": {
            "Hitter": 9.971,
            "Pitcher": 3.201
        },
        "1978": {
            "Hitter": 9.705,
            "Pitcher": 3.611
        },
        "1979": {
            "Hitter": 9.976,
            "Pitcher": 3.242
        },
        "1980": {
            "Hitter": 9.912,
            "Pitcher": 3.505
        },
        "1981": {
            "Hitter": 9.766,
            "Pitcher": 3.761
        },
        "1982": {
            "Hitter": 9.834,
            "Pitcher": 3.559
        },
        "1983": {
            "Hitter": 9.911,
            "Pitcher": 3.537
        },
        "1984": {
            "Hitter": 9.795,
            "Pitcher": 3.573
        },
        "1985": {
            "Hitter": 9.749,
            "Pitcher": 3.471
        },
        "1986": {
            "Hitter": 9.87,
            "Pitcher": 3.393
        },
        "1987": {
            "Hitter": 10.05,
            "Pitcher": 3.143
        },
        "1988": {
            "Hitter": 9.673,
            "Pitcher": 3.672
        },
        "1989": {
            "Hitter": 9.716,
            "Pitcher": 3.652
        },
        "1990": {
            "Hitter": 9.852,
            "Pitcher": 3.576
        },
        "1991": {
            "Hitter": 9.858,
            "Pitcher": 3.601
        },
        "1992": {
            "Hitter": 9.725,
            "Pitcher": 3.764
        },
        "1993": {
            "Hitter": 10.022,
            "Pitcher": 3.245
        },
        "1994": {
            "Hitter": 10.157,
            "Pitcher": 3.039
        },
        "1995": {
            "Hitter": 10.242,
            "Pitcher": 3.071
        },
        "1996": {
            "Hitter": 10.239,
            "Pitcher": 2.92
        },
        "1997": {
            "Hitter": 10.129,
            "Pitcher": 3.058
        },
        "1998": {
            "Hitter": 10.079,
            "Pitcher": 3.092
        },
        "1999": {
            "Hitter": 10.372,
            "Pitcher": 2.724
        },
        "2000": {
            "Hitter": 10.403,
            "Pitcher": 2.851
        },
        "2001": {
            "Hitter": 10.018,
            "Pitcher": 3.095
        },
        "2002": {
            "Hitter": 9.944,
            "Pitcher": 3.228
        },
        "2003": {
            "Hitter": 10.033,
            "Pitcher": 3.097
        },
        "2004": {
            "Hitter": 10.103,
            "Pitcher": 3.095
        },
        "2005": {
            "Hitter": 9.897,
            "Pitcher": 3.157
        },
        "2006": {
            "Hitter": 10.123,
            "Pitcher": 3.115
        },
        "2007": {
            "Hitter": 10.108,
            "Pitcher": 3.269
        },
        "2008": {
            "Hitter": 10.049,
            "Pitcher": 3.195
        },
        "2009": {
            "Hitter": 9.926,
            "Pitcher": 3.169
        },
        "2010": {
            "Hitter": 9.828,
            "Pitcher": 3.472
        },
        "2011": {
            "Hitter": 9.695,
            "Pitcher": 3.644
        },
        "2012": {
            "Hitter": 9.692,
            "Pitcher": 3.613
        },
        "2013": {
            "Hitter": 9.613,
            "Pitcher": 3.669
        },
        "2014": {
            "Hitter": 9.567,
            "Pitcher": 3.923
        },
        "2015": {
            "Hitter": 9.615,
            "Pitcher": 3.608
        },
        "2016": {
            "Hitter": 9.728,
            "Pitcher": 3.467
        },
        "2017": {
            "Hitter": 9.862,
            "Pitcher": 3.428
        },
        "2018": {
            "Hitter": 9.677,
            "Pitcher": 3.474
        },
        "2019": {
            "Hitter": 9.764,
            "Pitcher": 3.372
        },
        "2020": {
            "Hitter": 9.836,
            "Pitcher": 3.764
        },
        "2021": {
            "Hitter": 9.697,
            "Pitcher": 3.551
        },
        "2022": {
            "Hitter": 9.472,
            "Pitcher": 3.887
        }
    },
    "2005": {
        "1900": {
            "Hitter": 10.17,
            "Pitcher": 3.255
        },
        "1901": {
            "Hitter": 9.898,
            "Pitcher": 2.049
        },
        "1902": {
            "Hitter": 9.805,
            "Pitcher": 2.488
        },
        "1903": {
            "Hitter": 9.719,
            "Pitcher": 3.115
        },
        "1904": {
            "Hitter": 9.411,
            "Pitcher": 3.552
        },
        "1905": {
            "Hitter": 9.546,
            "Pitcher": 3.261
        },
        "1906": {
            "Hitter": 9.512,
            "Pitcher": 3.455
        },
        "1907": {
            "Hitter": 9.438,
            "Pitcher": 3.261
        },
        "1908": {
            "Hitter": 9.352,
            "Pitcher": 4.217
        },
        "1909": {
            "Hitter": 9.495,
            "Pitcher": 4.248
        },
        "1910": {
            "Hitter": 9.751,
            "Pitcher": 3.411
        },
        "1911": {
            "Hitter": 10.197,
            "Pitcher": 3.038
        },
        "1912": {
            "Hitter": 10.201,
            "Pitcher": 2.774
        },
        "1913": {
            "Hitter": 9.803,
            "Pitcher": 3.305
        },
        "1914": {
            "Hitter": 9.81,
            "Pitcher": 3.073
        },
        "1915": {
            "Hitter": 9.72,
            "Pitcher": 3.046
        },
        "1916": {
            "Hitter": 9.553,
            "Pitcher": 3.75
        },
        "1917": {
            "Hitter": 9.5,
            "Pitcher": 3.779
        },
        "1918": {
            "Hitter": 9.687,
            "Pitcher": 3.652
        },
        "1919": {
            "Hitter": 9.804,
            "Pitcher": 3.25
        },
        "1920": {
            "Hitter": 9.949,
            "Pitcher": 3.131
        },
        "1921": {
            "Hitter": 10.3,
            "Pitcher": 2.865
        },
        "1922": {
            "Hitter": 10.407,
            "Pitcher": 2.76
        },
        "1923": {
            "Hitter": 10.326,
            "Pitcher": 2.756
        },
        "1924": {
            "Hitter": 10.289,
            "Pitcher": 2.903
        },
        "1925": {
            "Hitter": 10.502,
            "Pitcher": 2.832
        },
        "1926": {
            "Hitter": 10.435,
            "Pitcher": 2.792
        },
        "1927": {
            "Hitter": 10.404,
            "Pitcher": 2.856
        },
        "1928": {
            "Hitter": 10.344,
            "Pitcher": 2.955
        },
        "1929": {
            "Hitter": 10.583,
            "Pitcher": 2.461
        },
        "1930": {
            "Hitter": 10.398,
            "Pitcher": 2.516
        },
        "1931": {
            "Hitter": 10.238,
            "Pitcher": 2.729
        },
        "1932": {
            "Hitter": 9.993,
            "Pitcher": 3.105
        },
        "1933": {
            "Hitter": 9.952,
            "Pitcher": 3.164
        },
        "1934": {
            "Hitter": 10.307,
            "Pitcher": 2.71
        },
        "1935": {
            "Hitter": 10.448,
            "Pitcher": 2.606
        },
        "1936": {
            "Hitter": 10.598,
            "Pitcher": 2.588
        },
        "1937": {
            "Hitter": 10.417,
            "Pitcher": 2.767
        },
        "1938": {
            "Hitter": 10.23,
            "Pitcher": 2.934
        },
        "1939": {
            "Hitter": 10.286,
            "Pitcher": 3.0
        },
        "1940": {
            "Hitter": 10.254,
            "Pitcher": 2.892
        },
        "1941": {
            "Hitter": 10.033,
            "Pitcher": 3.199
        },
        "1942": {
            "Hitter": 9.846,
            "Pitcher": 3.554
        },
        "1943": {
            "Hitter": 9.91,
            "Pitcher": 3.451
        },
        "1944": {
            "Hitter": 10.052,
            "Pitcher": 3.321
        },
        "1945": {
            "Hitter": 10.099,
            "Pitcher": 3.329
        },
        "1946": {
            "Hitter": 10.118,
            "Pitcher": 3.041
        },
        "1947": {
            "Hitter": 10.282,
            "Pitcher": 2.985
        },
        "1948": {
            "Hitter": 10.304,
            "Pitcher": 2.857
        },
        "1949": {
            "Hitter": 10.375,
            "Pitcher": 2.474
        },
        "1950": {
            "Hitter": 10.452,
            "Pitcher": 2.268
        },
        "1951": {
            "Hitter": 10.033,
            "Pitcher": 2.593
        },
        "1952": {
            "Hitter": 9.837,
            "Pitcher": 2.865
        },
        "1953": {
            "Hitter": 10.178,
            "Pitcher": 2.546
        },
        "1954": {
            "Hitter": 10.005,
            "Pitcher": 2.688
        },
        "1955": {
            "Hitter": 9.99,
            "Pitcher": 2.743
        },
        "1956": {
            "Hitter": 10.014,
            "Pitcher": 2.754
        },
        "1957": {
            "Hitter": 9.875,
            "Pitcher": 2.91
        },
        "1958": {
            "Hitter": 9.809,
            "Pitcher": 2.826
        },
        "1959": {
            "Hitter": 9.775,
            "Pitcher": 2.68
        },
        "1960": {
            "Hitter": 9.822,
            "Pitcher": 3.0
        },
        "1961": {
            "Hitter": 10.021,
            "Pitcher": 2.725
        },
        "1962": {
            "Hitter": 9.9,
            "Pitcher": 2.799
        },
        "1963": {
            "Hitter": 9.508,
            "Pitcher": 3.185
        },
        "1964": {
            "Hitter": 9.542,
            "Pitcher": 3.278
        },
        "1965": {
            "Hitter": 9.577,
            "Pitcher": 3.317
        },
        "1966": {
            "Hitter": 9.433,
            "Pitcher": 3.364
        },
        "1967": {
            "Hitter": 9.479,
            "Pitcher": 3.415
        },
        "1968": {
            "Hitter": 9.369,
            "Pitcher": 3.64
        },
        "1969": {
            "Hitter": 9.782,
            "Pitcher": 2.99
        },
        "1970": {
            "Hitter": 9.939,
            "Pitcher": 2.881
        },
        "1971": {
            "Hitter": 9.715,
            "Pitcher": 3.086
        },
        "1972": {
            "Hitter": 9.606,
            "Pitcher": 3.385
        },
        "1973": {
            "Hitter": 9.853,
            "Pitcher": 2.906
        },
        "1974": {
            "Hitter": 9.699,
            "Pitcher": 3.024
        },
        "1975": {
            "Hitter": 9.894,
            "Pitcher": 3.044
        },
        "1976": {
            "Hitter": 9.615,
            "Pitcher": 3.302
        },
        "1977": {
            "Hitter": 9.858,
            "Pitcher": 2.904
        },
        "1978": {
            "Hitter": 9.673,
            "Pitcher": 3.118
        },
        "1979": {
            "Hitter": 9.858,
            "Pitcher": 2.84
        },
        "1980": {
            "Hitter": 9.811,
            "Pitcher": 3.038
        },
        "1981": {
            "Hitter": 9.701,
            "Pitcher": 3.328
        },
        "1982": {
            "Hitter": 9.716,
            "Pitcher": 3.094
        },
        "1983": {
            "Hitter": 9.787,
            "Pitcher": 3.065
        },
        "1984": {
            "Hitter": 9.774,
            "Pitcher": 3.193
        },
        "1985": {
            "Hitter": 9.663,
            "Pitcher": 3.067
        },
        "1986": {
            "Hitter": 9.773,
            "Pitcher": 2.979
        },
        "1987": {
            "Hitter": 9.979,
            "Pitcher": 2.878
        },
        "1988": {
            "Hitter": 9.599,
            "Pitcher": 3.283
        },
        "1989": {
            "Hitter": 9.657,
            "Pitcher": 3.229
        },
        "1990": {
            "Hitter": 9.769,
            "Pitcher": 3.237
        },
        "1991": {
            "Hitter": 9.74,
            "Pitcher": 3.204
        },
        "1992": {
            "Hitter": 9.692,
            "Pitcher": 3.248
        },
        "1993": {
            "Hitter": 9.97,
            "Pitcher": 2.907
        },
        "1994": {
            "Hitter": 10.063,
            "Pitcher": 2.687
        },
        "1995": {
            "Hitter": 10.135,
            "Pitcher": 2.777
        },
        "1996": {
            "Hitter": 10.157,
            "Pitcher": 2.647
        },
        "1997": {
            "Hitter": 10.049,
            "Pitcher": 2.76
        },
        "1998": {
            "Hitter": 9.979,
            "Pitcher": 2.815
        },
        "1999": {
            "Hitter": 10.277,
            "Pitcher": 2.509
        },
        "2000": {
            "Hitter": 10.254,
            "Pitcher": 2.531
        },
        "2001": {
            "Hitter": 9.882,
            "Pitcher": 2.897
        },
        "2002": {
            "Hitter": 9.862,
            "Pitcher": 2.964
        },
        "2003": {
            "Hitter": 9.977,
            "Pitcher": 2.885
        },
        "2004": {
            "Hitter": 9.951,
            "Pitcher": 2.923
        },
        "2005": {
            "Hitter": 9.81,
            "Pitcher": 2.928
        },
        "2006": {
            "Hitter": 10.0,
            "Pitcher": 2.874
        },
        "2007": {
            "Hitter": 10.059,
            "Pitcher": 2.903
        },
        "2008": {
            "Hitter": 9.936,
            "Pitcher": 2.985
        },
        "2009": {
            "Hitter": 9.867,
            "Pitcher": 2.949
        },
        "2010": {
            "Hitter": 9.754,
            "Pitcher": 3.154
        },
        "2011": {
            "Hitter": 9.626,
            "Pitcher": 3.405
        },
        "2012": {
            "Hitter": 9.597,
            "Pitcher": 3.4
        },
        "2013": {
            "Hitter": 9.544,
            "Pitcher": 3.503
        },
        "2014": {
            "Hitter": 9.477,
            "Pitcher": 3.549
        },
        "2015": {
            "Hitter": 9.544,
            "Pitcher": 3.397
        },
        "2016": {
            "Hitter": 9.638,
            "Pitcher": 3.338
        },
        "2017": {
            "Hitter": 9.769,
            "Pitcher": 3.231
        },
        "2018": {
            "Hitter": 9.638,
            "Pitcher": 3.331
        },
        "2019": {
            "Hitter": 9.677,
            "Pitcher": 3.269
        },
        "2020": {
            "Hitter": 9.777,
            "Pitcher": 3.51
        },
        "2021": {
            "Hitter": 9.633,
            "Pitcher": 3.464
        },
        "2022": {
            "Hitter": 9.392,
            "Pitcher": 3.646
        }
    },
    CLASSIC_SET: {
        "1900": {
            "Hitter": 7.858,
            "Pitcher": 4.638
        },
        "1901": {
            "Hitter": 7.354,
            "Pitcher": 3.185
        },
        "1902": {
            "Hitter": 7.171,
            "Pitcher": 3.585
        },
        "1903": {
            "Hitter": 7.071,
            "Pitcher": 3.908
        },
        "1904": {
            "Hitter": 6.662,
            "Pitcher": 4.287
        },
        "1905": {
            "Hitter": 6.937,
            "Pitcher": 4.182
        },
        "1906": {
            "Hitter": 6.879,
            "Pitcher": 4.216
        },
        "1907": {
            "Hitter": 6.841,
            "Pitcher": 4.239
        },
        "1908": {
            "Hitter": 6.61,
            "Pitcher": 4.745
        },
        "1909": {
            "Hitter": 6.962,
            "Pitcher": 4.743
        },
        "1910": {
            "Hitter": 7.182,
            "Pitcher": 4.388
        },
        "1911": {
            "Hitter": 7.87,
            "Pitcher": 4.369
        },
        "1912": {
            "Hitter": 7.904,
            "Pitcher": 4.05
        },
        "1913": {
            "Hitter": 7.524,
            "Pitcher": 4.13
        },
        "1914": {
            "Hitter": 7.452,
            "Pitcher": 3.719
        },
        "1915": {
            "Hitter": 7.322,
            "Pitcher": 4.005
        },
        "1916": {
            "Hitter": 7.144,
            "Pitcher": 4.22
        },
        "1917": {
            "Hitter": 7.034,
            "Pitcher": 4.466
        },
        "1918": {
            "Hitter": 7.261,
            "Pitcher": 4.267
        },
        "1919": {
            "Hitter": 7.407,
            "Pitcher": 4.121
        },
        "1920": {
            "Hitter": 7.479,
            "Pitcher": 3.908
        },
        "1921": {
            "Hitter": 7.952,
            "Pitcher": 3.66
        },
        "1922": {
            "Hitter": 8.119,
            "Pitcher": 3.428
        },
        "1923": {
            "Hitter": 7.894,
            "Pitcher": 3.484
        },
        "1924": {
            "Hitter": 7.925,
            "Pitcher": 3.729
        },
        "1925": {
            "Hitter": 8.091,
            "Pitcher": 3.597
        },
        "1926": {
            "Hitter": 8.005,
            "Pitcher": 3.476
        },
        "1927": {
            "Hitter": 7.975,
            "Pitcher": 3.638
        },
        "1928": {
            "Hitter": 7.997,
            "Pitcher": 3.352
        },
        "1929": {
            "Hitter": 8.257,
            "Pitcher": 3.094
        },
        "1930": {
            "Hitter": 8.04,
            "Pitcher": 3.133
        },
        "1931": {
            "Hitter": 7.944,
            "Pitcher": 3.568
        },
        "1932": {
            "Hitter": 7.496,
            "Pitcher": 3.826
        },
        "1933": {
            "Hitter": 7.506,
            "Pitcher": 3.771
        },
        "1934": {
            "Hitter": 7.816,
            "Pitcher": 3.446
        },
        "1935": {
            "Hitter": 8.111,
            "Pitcher": 3.176
        },
        "1936": {
            "Hitter": 8.189,
            "Pitcher": 3.31
        },
        "1937": {
            "Hitter": 7.966,
            "Pitcher": 3.353
        },
        "1938": {
            "Hitter": 7.853,
            "Pitcher": 3.484
        },
        "1939": {
            "Hitter": 7.806,
            "Pitcher": 3.633
        },
        "1940": {
            "Hitter": 7.717,
            "Pitcher": 3.521
        },
        "1941": {
            "Hitter": 7.464,
            "Pitcher": 3.888
        },
        "1942": {
            "Hitter": 7.32,
            "Pitcher": 4.036
        },
        "1943": {
            "Hitter": 7.467,
            "Pitcher": 4.183
        },
        "1944": {
            "Hitter": 7.553,
            "Pitcher": 3.849
        },
        "1945": {
            "Hitter": 7.627,
            "Pitcher": 4.11
        },
        "1946": {
            "Hitter": 7.726,
            "Pitcher": 3.725
        },
        "1947": {
            "Hitter": 7.942,
            "Pitcher": 3.491
        },
        "1948": {
            "Hitter": 7.847,
            "Pitcher": 3.557
        },
        "1949": {
            "Hitter": 8.12,
            "Pitcher": 2.979
        },
        "1950": {
            "Hitter": 8.298,
            "Pitcher": 2.426
        },
        "1951": {
            "Hitter": 7.89,
            "Pitcher": 2.659
        },
        "1952": {
            "Hitter": 7.663,
            "Pitcher": 2.912
        },
        "1953": {
            "Hitter": 8.072,
            "Pitcher": 2.73
        },
        "1954": {
            "Hitter": 7.928,
            "Pitcher": 2.646
        },
        "1955": {
            "Hitter": 7.837,
            "Pitcher": 2.366
        },
        "1956": {
            "Hitter": 7.851,
            "Pitcher": 2.482
        },
        "1957": {
            "Hitter": 7.601,
            "Pitcher": 2.806
        },
        "1958": {
            "Hitter": 7.656,
            "Pitcher": 2.562
        },
        "1959": {
            "Hitter": 7.684,
            "Pitcher": 2.463
        },
        "1960": {
            "Hitter": 7.721,
            "Pitcher": 2.66
        },
        "1961": {
            "Hitter": 7.701,
            "Pitcher": 2.399
        },
        "1962": {
            "Hitter": 7.858,
            "Pitcher": 2.586
        },
        "1963": {
            "Hitter": 7.262,
            "Pitcher": 2.899
        },
        "1964": {
            "Hitter": 7.308,
            "Pitcher": 2.833
        },
        "1965": {
            "Hitter": 7.254,
            "Pitcher": 2.78
        },
        "1966": {
            "Hitter": 7.184,
            "Pitcher": 3.02
        },
        "1967": {
            "Hitter": 7.019,
            "Pitcher": 3.245
        },
        "1968": {
            "Hitter": 6.827,
            "Pitcher": 3.488
        },
        "1969": {
            "Hitter": 7.551,
            "Pitcher": 2.854
        },
        "1970": {
            "Hitter": 7.753,
            "Pitcher": 2.679
        },
        "1971": {
            "Hitter": 7.471,
            "Pitcher": 3.0
        },
        "1972": {
            "Hitter": 7.224,
            "Pitcher": 3.265
        },
        "1973": {
            "Hitter": 7.561,
            "Pitcher": 2.833
        },
        "1974": {
            "Hitter": 7.471,
            "Pitcher": 3.155
        },
        "1975": {
            "Hitter": 7.686,
            "Pitcher": 3.153
        },
        "1976": {
            "Hitter": 7.481,
            "Pitcher": 3.586
        },
        "1977": {
            "Hitter": 7.681,
            "Pitcher": 2.559
        },
        "1978": {
            "Hitter": 7.555,
            "Pitcher": 3.131
        },
        "1979": {
            "Hitter": 7.787,
            "Pitcher": 2.764
        },
        "1980": {
            "Hitter": 7.631,
            "Pitcher": 3.076
        },
        "1981": {
            "Hitter": 7.382,
            "Pitcher": 3.22
        },
        "1982": {
            "Hitter": 7.621,
            "Pitcher": 3.069
        },
        "1983": {
            "Hitter": 7.636,
            "Pitcher": 2.941
        },
        "1984": {
            "Hitter": 7.554,
            "Pitcher": 2.788
        },
        "1985": {
            "Hitter": 7.559,
            "Pitcher": 2.827
        },
        "1986": {
            "Hitter": 7.658,
            "Pitcher": 2.801
        },
        "1987": {
            "Hitter": 7.814,
            "Pitcher": 2.514
        },
        "1988": {
            "Hitter": 7.363,
            "Pitcher": 3.084
        },
        "1989": {
            "Hitter": 7.411,
            "Pitcher": 3.211
        },
        "1990": {
            "Hitter": 7.601,
            "Pitcher": 2.929
        },
        "1991": {
            "Hitter": 7.568,
            "Pitcher": 3.038
        },
        "1992": {
            "Hitter": 7.494,
            "Pitcher": 3.152
        },
        "1993": {
            "Hitter": 7.852,
            "Pitcher": 2.78
        },
        "1994": {
            "Hitter": 8.011,
            "Pitcher": 2.609
        },
        "1995": {
            "Hitter": 7.975,
            "Pitcher": 2.624
        },
        "1996": {
            "Hitter": 8.082,
            "Pitcher": 2.532
        },
        "1997": {
            "Hitter": 7.981,
            "Pitcher": 2.548
        },
        "1998": {
            "Hitter": 7.797,
            "Pitcher": 2.5
        },
        "1999": {
            "Hitter": 8.187,
            "Pitcher": 2.382
        },
        "2000": {
            "Hitter": 8.172,
            "Pitcher": 2.392
        },
        "2001": {
            "Hitter": 7.851,
            "Pitcher": 2.574
        },
        "2002": {
            "Hitter": 7.787,
            "Pitcher": 2.626
        },
        "2003": {
            "Hitter": 7.864,
            "Pitcher": 2.546
        },
        "2004": {
            "Hitter": 7.908,
            "Pitcher": 2.577
        },
        "2005": {
            "Hitter": 7.795,
            "Pitcher": 2.638
        },
        "2006": {
            "Hitter": 7.982,
            "Pitcher": 2.672
        },
        "2007": {
            "Hitter": 7.936,
            "Pitcher": 2.554
        },
        "2008": {
            "Hitter": 7.887,
            "Pitcher": 2.813
        },
        "2009": {
            "Hitter": 7.823,
            "Pitcher": 2.595
        },
        "2010": {
            "Hitter": 7.603,
            "Pitcher": 2.887
        },
        "2011": {
            "Hitter": 7.487,
            "Pitcher": 3.156
        },
        "2012": {
            "Hitter": 7.4,
            "Pitcher": 2.877
        },
        "2013": {
            "Hitter": 7.403,
            "Pitcher": 2.992
        },
        "2014": {
            "Hitter": 7.274,
            "Pitcher": 3.218
        },
        "2015": {
            "Hitter": 7.382,
            "Pitcher": 2.982
        },
        "2016": {
            "Hitter": 7.5,
            "Pitcher": 2.987
        },
        "2017": {
            "Hitter": 7.608,
            "Pitcher": 2.644
        },
        "2018": {
            "Hitter": 7.405,
            "Pitcher": 2.879
        },
        "2019": {
            "Hitter": 7.564,
            "Pitcher": 2.803
        },
        "2020": {
            "Hitter": 7.285,
            "Pitcher": 3.231
        },
        "2021": {
            "Hitter": 7.444,
            "Pitcher": 2.954
        },
        "2022": {
            "Hitter": 7.118,
            "Pitcher": 3.174
        }
    },
    EXPANDED_SET: {
        "1900": {
            "Hitter": 10.377,
            "Pitcher": 3.872
        },
        "1901": {
            "Hitter": 9.903,
            "Pitcher": 2.395
        },
        "1902": {
            "Hitter": 9.893,
            "Pitcher": 2.805
        },
        "1903": {
            "Hitter": 9.729,
            "Pitcher": 3.08
        },
        "1904": {
            "Hitter": 9.285,
            "Pitcher": 3.851
        },
        "1905": {
            "Hitter": 9.531,
            "Pitcher": 3.534
        },
        "1906": {
            "Hitter": 9.411,
            "Pitcher": 3.795
        },
        "1907": {
            "Hitter": 9.457,
            "Pitcher": 3.58
        },
        "1908": {
            "Hitter": 9.271,
            "Pitcher": 4.623
        },
        "1909": {
            "Hitter": 9.543,
            "Pitcher": 4.416
        },
        "1910": {
            "Hitter": 9.833,
            "Pitcher": 3.698
        },
        "1911": {
            "Hitter": 10.279,
            "Pitcher": 3.423
        },
        "1912": {
            "Hitter": 10.368,
            "Pitcher": 3.063
        },
        "1913": {
            "Hitter": 10.024,
            "Pitcher": 3.617
        },
        "1914": {
            "Hitter": 9.919,
            "Pitcher": 3.276
        },
        "1915": {
            "Hitter": 9.755,
            "Pitcher": 3.574
        },
        "1916": {
            "Hitter": 9.663,
            "Pitcher": 3.924
        },
        "1917": {
            "Hitter": 9.49,
            "Pitcher": 4.137
        },
        "1918": {
            "Hitter": 9.81,
            "Pitcher": 3.844
        },
        "1919": {
            "Hitter": 9.962,
            "Pitcher": 3.6
        },
        "1920": {
            "Hitter": 10.119,
            "Pitcher": 3.403
        },
        "1921": {
            "Hitter": 10.425,
            "Pitcher": 2.991
        },
        "1922": {
            "Hitter": 10.647,
            "Pitcher": 2.846
        },
        "1923": {
            "Hitter": 10.497,
            "Pitcher": 2.936
        },
        "1924": {
            "Hitter": 10.455,
            "Pitcher": 3.004
        },
        "1925": {
            "Hitter": 10.677,
            "Pitcher": 3.044
        },
        "1926": {
            "Hitter": 10.548,
            "Pitcher": 2.885
        },
        "1927": {
            "Hitter": 10.519,
            "Pitcher": 2.942
        },
        "1928": {
            "Hitter": 10.478,
            "Pitcher": 2.914
        },
        "1929": {
            "Hitter": 10.805,
            "Pitcher": 2.641
        },
        "1930": {
            "Hitter": 10.623,
            "Pitcher": 2.449
        },
        "1931": {
            "Hitter": 10.434,
            "Pitcher": 2.766
        },
        "1932": {
            "Hitter": 10.089,
            "Pitcher": 3.171
        },
        "1933": {
            "Hitter": 10.099,
            "Pitcher": 3.169
        },
        "1934": {
            "Hitter": 10.43,
            "Pitcher": 2.795
        },
        "1935": {
            "Hitter": 10.631,
            "Pitcher": 2.624
        },
        "1936": {
            "Hitter": 10.831,
            "Pitcher": 2.556
        },
        "1937": {
            "Hitter": 10.516,
            "Pitcher": 2.903
        },
        "1938": {
            "Hitter": 10.406,
            "Pitcher": 2.96
        },
        "1939": {
            "Hitter": 10.406,
            "Pitcher": 3.004
        },
        "1940": {
            "Hitter": 10.304,
            "Pitcher": 2.965
        },
        "1941": {
            "Hitter": 10.08,
            "Pitcher": 3.247
        },
        "1942": {
            "Hitter": 9.887,
            "Pitcher": 3.514
        },
        "1943": {
            "Hitter": 10.045,
            "Pitcher": 3.622
        },
        "1944": {
            "Hitter": 10.123,
            "Pitcher": 3.433
        },
        "1945": {
            "Hitter": 10.195,
            "Pitcher": 3.49
        },
        "1946": {
            "Hitter": 10.31,
            "Pitcher": 3.278
        },
        "1947": {
            "Hitter": 10.492,
            "Pitcher": 2.893
        },
        "1948": {
            "Hitter": 10.422,
            "Pitcher": 2.861
        },
        "1949": {
            "Hitter": 10.601,
            "Pitcher": 2.342
        },
        "1950": {
            "Hitter": 10.62,
            "Pitcher": 1.995
        },
        "1951": {
            "Hitter": 10.258,
            "Pitcher": 2.363
        },
        "1952": {
            "Hitter": 10.168,
            "Pitcher": 2.503
        },
        "1953": {
            "Hitter": 10.385,
            "Pitcher": 2.384
        },
        "1954": {
            "Hitter": 10.226,
            "Pitcher": 2.259
        },
        "1955": {
            "Hitter": 10.192,
            "Pitcher": 2.22
        },
        "1956": {
            "Hitter": 10.188,
            "Pitcher": 2.136
        },
        "1957": {
            "Hitter": 9.976,
            "Pitcher": 2.642
        },
        "1958": {
            "Hitter": 9.967,
            "Pitcher": 2.408
        },
        "1959": {
            "Hitter": 10.019,
            "Pitcher": 2.365
        },
        "1960": {
            "Hitter": 10.0,
            "Pitcher": 2.457
        },
        "1961": {
            "Hitter": 10.171,
            "Pitcher": 2.151
        },
        "1962": {
            "Hitter": 10.1,
            "Pitcher": 2.299
        },
        "1963": {
            "Hitter": 9.554,
            "Pitcher": 2.746
        },
        "1964": {
            "Hitter": 9.669,
            "Pitcher": 2.678
        },
        "1965": {
            "Hitter": 9.635,
            "Pitcher": 2.89
        },
        "1966": {
            "Hitter": 9.479,
            "Pitcher": 2.777
        },
        "1967": {
            "Hitter": 9.487,
            "Pitcher": 3.036
        },
        "1968": {
            "Hitter": 9.262,
            "Pitcher": 3.372
        },
        "1969": {
            "Hitter": 9.942,
            "Pitcher": 2.6
        },
        "1970": {
            "Hitter": 10.186,
            "Pitcher": 2.424
        },
        "1971": {
            "Hitter": 9.788,
            "Pitcher": 2.822
        },
        "1972": {
            "Hitter": 9.593,
            "Pitcher": 3.048
        },
        "1973": {
            "Hitter": 9.952,
            "Pitcher": 2.628
        },
        "1974": {
            "Hitter": 9.923,
            "Pitcher": 2.748
        },
        "1975": {
            "Hitter": 10.0,
            "Pitcher": 2.756
        },
        "1976": {
            "Hitter": 9.811,
            "Pitcher": 3.228
        },
        "1977": {
            "Hitter": 10.009,
            "Pitcher": 2.46
        },
        "1978": {
            "Hitter": 9.835,
            "Pitcher": 2.955
        },
        "1979": {
            "Hitter": 10.107,
            "Pitcher": 2.547
        },
        "1980": {
            "Hitter": 9.935,
            "Pitcher": 2.74
        },
        "1981": {
            "Hitter": 9.746,
            "Pitcher": 3.102
        },
        "1982": {
            "Hitter": 9.902,
            "Pitcher": 2.878
        },
        "1983": {
            "Hitter": 9.959,
            "Pitcher": 2.764
        },
        "1984": {
            "Hitter": 9.859,
            "Pitcher": 2.769
        },
        "1985": {
            "Hitter": 9.855,
            "Pitcher": 2.708
        },
        "1986": {
            "Hitter": 9.968,
            "Pitcher": 2.535
        },
        "1987": {
            "Hitter": 10.13,
            "Pitcher": 2.374
        },
        "1988": {
            "Hitter": 9.693,
            "Pitcher": 2.892
        },
        "1989": {
            "Hitter": 9.719,
            "Pitcher": 2.991
        },
        "1990": {
            "Hitter": 9.97,
            "Pitcher": 2.881
        },
        "1991": {
            "Hitter": 9.858,
            "Pitcher": 2.784
        },
        "1992": {
            "Hitter": 9.787,
            "Pitcher": 3.033
        },
        "1993": {
            "Hitter": 10.113,
            "Pitcher": 2.555
        },
        "1994": {
            "Hitter": 10.407,
            "Pitcher": 2.363
        },
        "1995": {
            "Hitter": 10.308,
            "Pitcher": 2.442
        },
        "1996": {
            "Hitter": 10.374,
            "Pitcher": 2.3
        },
        "1997": {
            "Hitter": 10.275,
            "Pitcher": 2.38
        },
        "1998": {
            "Hitter": 10.187,
            "Pitcher": 2.372
        },
        "1999": {
            "Hitter": 10.615,
            "Pitcher": 2.145
        },
        "2000": {
            "Hitter": 10.518,
            "Pitcher": 2.01
        },
        "2001": {
            "Hitter": 10.146,
            "Pitcher": 2.449
        },
        "2002": {
            "Hitter": 10.01,
            "Pitcher": 2.472
        },
        "2003": {
            "Hitter": 10.108,
            "Pitcher": 2.362
        },
        "2004": {
            "Hitter": 10.162,
            "Pitcher": 2.446
        },
        "2005": {
            "Hitter": 10.008,
            "Pitcher": 2.432
        },
        "2006": {
            "Hitter": 10.262,
            "Pitcher": 2.428
        },
        "2007": {
            "Hitter": 10.218,
            "Pitcher": 2.521
        },
        "2008": {
            "Hitter": 10.141,
            "Pitcher": 2.605
        },
        "2009": {
            "Hitter": 10.1,
            "Pitcher": 2.569
        },
        "2010": {
            "Hitter": 9.926,
            "Pitcher": 2.644
        },
        "2011": {
            "Hitter": 9.8,
            "Pitcher": 2.941
        },
        "2012": {
            "Hitter": 9.674,
            "Pitcher": 2.882
        },
        "2013": {
            "Hitter": 9.687,
            "Pitcher": 2.949
        },
        "2014": {
            "Hitter": 9.551,
            "Pitcher": 3.233
        },
        "2015": {
            "Hitter": 9.597,
            "Pitcher": 2.936
        },
        "2016": {
            "Hitter": 9.759,
            "Pitcher": 2.772
        },
        "2017": {
            "Hitter": 9.89,
            "Pitcher": 2.618
        },
        "2018": {
            "Hitter": 9.669,
            "Pitcher": 2.887
        },
        "2019": {
            "Hitter": 9.8,
            "Pitcher": 2.664
        },
        "2020": {
            "Hitter": 9.762,
            "Pitcher": 3.162
        },
        "2021": {
            "Hitter": 9.674,
            "Pitcher": 2.772
        },
        "2022": {
            "Hitter": 9.403,
            "Pitcher": 3.115
        }
    }
}

""" IMAGE COMPONENTS """
CARD_SIZE = (1500,2100)
CARD_SIZE_FINAL = (1488,2079)
CARD_BORDER_PADDING = 72
CARD_SIZE_BORDERED = (CARD_SIZE[0] + int(CARD_BORDER_PADDING*2), CARD_SIZE[1] + int(CARD_BORDER_PADDING*2))
CARD_SIZE_BORDERED_FINAL = (CARD_SIZE_FINAL[0] + int(CARD_BORDER_PADDING*2), CARD_SIZE_FINAL[1] + int(CARD_BORDER_PADDING*2))

class ImageComponent(Enum):

    BACKGROUND = "BG"
    CUSTOM_BACKGROUND = "CUSTOM BG"
    CUSTOM_FOREGROUND = "CUSTOM FG"
    SHADOW = "SHADOW"
    GLOW = "GLOW"
    CUT = "CUT"
    GRADIENT = "GRADIENT"
    DARKENER = "DARKENER"
    COOPERSTOWN = "COOPERSTOWN"
    ELLIPSE_LARGE = "ELLIPSE-LARGE"
    ELLIPSE_MEDIUM = "ELLIPSE-MEDIUM"
    ELLIPSE_SMALL = "ELLIPSE-SMALL"
    SUPER_SEASON = "SUPER SEASON"
    RAINBOW_FOIL = "RAINBOW FOIL"
    SILHOUETTE = "SILHOUETTE"
    SAPPHIRE = "SAPPHIRE"
    RADIAL = "RADIAL"
    COMIC_BOOK_LINES = "COMIC-BOOK-HERO"
    GOLD_RUSH = "GOLD-BEAMS"
    GOLD = "GOLD"
    WHITE_SMOKE = "WHITE_SMOKE"
    FLAMES = "FLAMES"
    WHITE_CIRCLE = "WHITE_CIRCLE"
    BLACK_CIRCLE = "BLACK_CIRCLE"
    TEAM_COLOR = "TEAM_COLOR"
    TEAM_LOGO = "TEAM_LOGO"
    NAME_CONTAINER_2000 = "NAME_CONTAINER_2000"

    @property
    def load_source(self) -> str:
        match self.name:
            case "BACKGROUND" | "SHADOW" | "GLOW" | "CUT": return "DOWNLOAD"
            case "TEAM_COLOR": return "COLOR"
            case "TEAM_LOGO": return "TEAM_LOGOS"
            case "NAME_CONTAINER_2000": return "NAME_CONTAINER"
            case "SILHOUETTE": return "SILHOUETTE"
            case _: return "CARD_ART"

    @property
    def is_loaded_via_download(self) -> bool:
        return self.load_source == "DOWNLOAD"
    
    @property
    def adjust_paste_coordinates_for_bordered(self) -> bool:
        return self.name in ["NAME_CONTAINER_2000", "SILHOUETTE"]
    
    @property
    def ignores_custom_crop(self) -> bool:
        return self.name in [
            "SUPER_SEASON",
            "CUSTOM_BACKGROUND",
            "CUSTOM_FOREGROUND",
            "GRADIENT",
            "RAINBOW_FOIL",
            "SAPPHIRE",
            "RADIAL",
            "COOPERSTOWN",
            "COMIC_BOOK_LINES",
            "GOLD_RUSH",
            "GOLD",
            "WHITE_SMOKE",
            "FLAMES",
            "WHITE_CIRCLE",
            "BLACK_CIRCLE",
            "TEAM_COLOR",
            "TEAM_LOGO",
            "SILHOUETTE",
            "NAME_CONTAINER_2000",
            "DARKENER",
        ]
    
    @property
    def crop_adjustment_02_03(self) -> tuple[int, int]:
        match self.name:
            case "WHITE_CIRCLE" | "BLACK_CIRCLE" | "TEAM_COLOR" | "TEAM_LOGO": return (75,0)
            case _: return None

    @property
    def opacity(self) -> float:
        match self.name:
            case "RAINBOW_FOIL" | "SAPPHIRE": return 0.65
            case "TEAM_COLOR": return 0.75
            case _: return 1.0

IMAGE_COMPONENT_ORDERED_LIST = [
    ImageComponent.BACKGROUND,
    ImageComponent.CUSTOM_BACKGROUND,
    ImageComponent.COOPERSTOWN,
    ImageComponent.SUPER_SEASON,
    ImageComponent.DARKENER,
    ImageComponent.GRADIENT,
    ImageComponent.RAINBOW_FOIL,
    ImageComponent.SAPPHIRE,
    ImageComponent.RADIAL,
    ImageComponent.COMIC_BOOK_LINES,
    ImageComponent.GOLD_RUSH,
    ImageComponent.GOLD,
    ImageComponent.WHITE_SMOKE,
    ImageComponent.FLAMES,
    ImageComponent.TEAM_LOGO,
    ImageComponent.TEAM_COLOR,
    ImageComponent.WHITE_CIRCLE,
    ImageComponent.BLACK_CIRCLE,
    ImageComponent.NAME_CONTAINER_2000,
    ImageComponent.SHADOW,
    ImageComponent.GLOW,
    ImageComponent.CUT,
    ImageComponent.CUSTOM_FOREGROUND,
    ImageComponent.SILHOUETTE,
]

ELLIPSE_IMAGE_COMPONENTS = [
    ImageComponent.ELLIPSE_LARGE,
    ImageComponent.ELLIPSE_MEDIUM,
    ImageComponent.ELLIPSE_SMALL,
]

PLAYER_IMAGE_MODE = {
    '2000': 'RGBA',
    '2001': 'RGBA',
    '2002': 'RGB',
    '2003': 'RGB',
    '2004': 'RGB',
    '2005': 'RGB',
    CLASSIC_SET: 'RGB',
    EXPANDED_SET: 'RGB',
}

AUTO_IMAGE_COMPONENTS = {
    '2000': [ImageComponent.NAME_CONTAINER_2000,ImageComponent.GLOW],
    '2001': [ImageComponent.GLOW],
    '2002': [ImageComponent.BACKGROUND],
    '2003': [ImageComponent.BACKGROUND],
    '2004': [ImageComponent.BACKGROUND],
    '2005': [ImageComponent.BACKGROUND],
    CLASSIC_SET: [ImageComponent.BACKGROUND,ImageComponent.SHADOW],
    EXPANDED_SET: [ImageComponent.BACKGROUND,ImageComponent.SHADOW],
}

AUTO_IMAGE_COMPONENTS_SPECIAL = {
    '2000': [ImageComponent.NAME_CONTAINER_2000,ImageComponent.GLOW],
    '2001': [ImageComponent.GLOW],
    '2002': [ImageComponent.BACKGROUND,ImageComponent.GLOW],
    '2003': [ImageComponent.BACKGROUND,ImageComponent.GLOW],
    '2004': [ImageComponent.BACKGROUND,ImageComponent.GLOW],
    '2005': [ImageComponent.BACKGROUND,ImageComponent.GLOW],
    CLASSIC_SET: [ImageComponent.BACKGROUND,ImageComponent.SHADOW],
    EXPANDED_SET: [ImageComponent.BACKGROUND,ImageComponent.SHADOW],
}

PLAYER_IMAGE_CROP_SIZE = {
    '2000': (1500,2100),
    '2001': (1200,1680),
    '2002': (1305,1827),
    '2003': (1305,1827),
    '2004': (1500,2100),
    '2005': (1500,2100),
    CLASSIC_SET: (1200, 1680),
    EXPANDED_SET: (1200, 1680),
}

PLAYER_IMAGE_CROP_ADJUSTMENT = {
    '2000': (-25,-300),
    '2001': (-35,-460),
    '2002': (75,-250),
    '2003': (75,-150),
    '2004': (0,0),
    '2005': (0,0),
    CLASSIC_SET: (0,int((PLAYER_IMAGE_CROP_SIZE[CLASSIC_SET][1] - 2100) / 2)),
    EXPANDED_SET: (0,int((PLAYER_IMAGE_CROP_SIZE[EXPANDED_SET][1] - 2100) / 2)),
}

""" SPECIAL EDITIONS """

class SpecialEdition(Enum):
    
    ASG_2023 = "ASG 2023"
    COOPERSTOWN_COLLECTION = "CC"
    SUPER_SEASON = "SS"
    TEAM_COLOR_BLAST_DARK = "TCBD"
    NONE = "NONE"

SPECIAL_EDITION_IMG_SATURATION_ADJUSTMENT = {
    SpecialEdition.COOPERSTOWN_COLLECTION: {
        ImageComponent.BACKGROUND: 0.33,
    },
    SpecialEdition.SUPER_SEASON: {
        ImageComponent.BACKGROUND: 0.75,
    },
}

SUPER_SEASON_IMG_INDEX = {
    '2000': '1',
    '2001': '1',
    '2002': '1',
    '2003': '1',
    '2004': '2',
    '2005': '2',
    CLASSIC_SET: '3',
    EXPANDED_SET: '3',
}

SUPER_SEASON_04_05_MIN_TEXT_LENGTH = 11
SUPER_SEASON_PRE_04_TEXT_LENGTH = 19

""" IMAGE PARALLELS """

class ImageParallel(Enum):
    
    RAINBOW_FOIL = "RF"
    SAPPHIRE = "SPH"
    BLACK_AND_WHITE = "B&W"
    RADIAL = "RAD"
    COMIC_BOOK_HERO = "CB"
    GOLD_RUSH = "GOLDRUSH"
    GOLD = "GOLD"
    WHITE_SMOKE = "WS"
    FLAMES = "FLAMES"
    TEAM_COLOR_BLAST = "TCB"
    MYSTERY = "MYSTERY"
    NONE = "NONE"

    @property
    def has_special_components(self) -> bool:
        return self.name not in ['NONE', 'BLACK_AND_WHITE']

    @property
    def special_component_additions(self) -> dict[str,str]:
        match self.name:
            case "RAINBOW_FOIL": return { ImageComponent.RAINBOW_FOIL: "RAINBOW-FOIL" }
            case "SAPPHIRE": return { ImageComponent.SAPPHIRE: "SAPPHIRE" }
            case "RADIAL": return { ImageComponent.RADIAL: "RADIAL" }
            case "COMIC_BOOK_HERO": return { ImageComponent.COMIC_BOOK_LINES: ImageComponent.COMIC_BOOK_LINES.name }
            case "GOLD_RUSH": return { ImageComponent.GOLD_RUSH: ImageComponent.GOLD_RUSH.name }
            case "GOLD": return { ImageComponent.GOLD: ImageComponent.GOLD.name }
            case "WHITE_SMOKE": return { ImageComponent.WHITE_SMOKE: ImageComponent.WHITE_SMOKE.name, ImageComponent.BACKGROUND: None }
            case "FLAMES": return { ImageComponent.FLAMES: ImageComponent.FLAMES.name }
            case "TEAM_COLOR_BLAST": return { ImageComponent.WHITE_CIRCLE: ImageComponent.WHITE_CIRCLE.name, ImageComponent.TEAM_LOGO: None, ImageComponent.TEAM_COLOR: None, ImageComponent.BACKGROUND: None }
            case _: return {}

    @property
    def special_components_replacements(self) -> dict[str,str]:
        match self.name:
            case "SAPPHIRE" | "WHITE_SMOKE" | "FLAMES" | "TEAM_COLOR_BLAST" | "GOLD_RUSH" | "GOLD": return { ImageComponent.GLOW: ImageComponent.SHADOW }
            case _: return {}
    
    @property
    def image_type_saturations_dict(self) -> dict[str,float]:
        match self.name:
            case "COMIC_BOOK_HERO" | "WHITE_SMOKE": return { ImageComponent.BACKGROUND: 0.05 }
            case "GOLD_RUSH" | "GOLD": return { ImageComponent.BACKGROUND: 0.40 }
            case "TEAM_COLOR_BLAST": return { ImageComponent.TEAM_LOGO: 0.10 }
            case _: return {}

    @property
    def is_team_background_black_and_white(self) -> bool:
        return self.name in ['COMIC_BOOK_HERO', 'GOLD_RUSH', 'GOLD', 'WHITE_SMOKE']
    
    @property
    def color_override_04_05_chart(self) -> str:
        match self.name:
            case 'GOLD_RUSH': return 'YELLOW'
            case 'GOLD': return 'YELLOW'
            case 'FLAMES': return 'RED'
            case _: return None

