
# -------------------------------------------
# SHOWDOWN_CONSTANTS.PY
#   - ONE FILE TO STORE ALL WEIGHTS / STATIC VALUES
#     NEEDED TO GENERATE PLAYER CARDS
# -------------------------------------------

"""
SET STYLES
"""
EXPANDED_ALIAS = 'EXPANDED'
CLASSIC_ALIAS = 'CLASSIC'
EXPANDED_SETS = ['2002','2003','2004','2005',f'2022-{EXPANDED_ALIAS}',]
CLASSIC_SETS = ['2000','2001',f'2022-{CLASSIC_ALIAS}',]
SETS_HAS_ICONS = ['2003','2004','2005','2022',]
"""
SPEED AND FIELDING
  - MIN AND MAX USED IN PERCENTILE CALCULATIONS
  - ** STOLEN BASES MINIMUM IS NEGATIVE JUST TO BALANCE OUT PERCENTILE RANGE
"""
MAX_SPRINT_SPEED = 31
MIN_SPRINT_SPEED = 23
MAX_STOLEN_BASES = 26
MIN_STOLEN_BASES = -25
SB_MULTIPLIER = {
    '2000': 1.21,
    '2001': 1.22,
    '2002': 1.2,
    '2003': 0.95,
    '2004': 0.98,
    '2005': 1.0,
    f'2022-{CLASSIC_ALIAS}': 1.0,
    f'2022-{EXPANDED_ALIAS}': 1.0,
}
MAX_IN_GAME_SPD = {
    '2000': 25,
    '2001': 25,
    '2002': 27,
    '2003': 27,
    '2004': 27,
    '2005': 27,
    f'2022-{CLASSIC_ALIAS}': 25,
    f'2022-{EXPANDED_ALIAS}': 25,
}

MIN_SABER_FIELDING = {
    'drs': -20,
    'tzr': -18,
    'dWAR': -2.5
}
MAX_SABER_FIELDING = {
    'drs': 20,
    'tzr': 18,
    'dWAR': 2.5
}
# FOR 1B, USE A STATIC CUTOFFS INSTEAD OF RANGE
FIRST_BASE_PLUS_2_CUTOFF = {
    'drs': 17,
    'tzr': 15,
    'dWAR': 0.8
}
FIRST_BASE_PLUS_1_CUTOFF = {
    'drs': 4,
    'tzr': 4,
    'dWAR': -0.25
}
# -1 1B DEFENSE ONLY APPLIES TO 2022 SET AND BEYOND
FIRST_BASE_MINUS_1_CUTOFF = {
    'drs': -5,
    'tzr': -5,
    'dWAR': -1.0
}
# MINIMUM REQUIRED GAMES PLAYED AT A POSITION TO QUALIFY
NUMBER_OF_GAMES_DEFENSE = 7 
PCT_OF_GAMES_DEFENSE = 0.15
PCT_OF_GAMES_DEFENSE_MULTI_YEAR = 0.25
STARTING_PITCHER_PCT_GAMES_STARTED = 0.40
CLOSER_MIN_SAVES_REQUIRED = 10
MAX_NUMBER_OF_POSITIONS = {
    '2000': 2,
    '2001': 2,
    '2002': 2,
    '2003': 2,
    '2004': 2,
    '2005': 2,
    f'2022-{CLASSIC_ALIAS}': 3,
    f'2022-{EXPANDED_ALIAS}': 3,
}

# MULTIPLIER TO MATCH PU WITH ORIGINAL SETS
PU_MULTIPLIER = {
    '2000': 2.25,
    '2001': 2.5,
    '2002': 2.8,
    '2003': 2.2,
    '2004': 2.05,
    '2005': 2.4,
    f'2022-{CLASSIC_ALIAS}': 2.5,
    f'2022-{EXPANDED_ALIAS}': 2.4,
}
# THIS GB MULTIPLIER IS A MORE SIMPLE MODE OF ADJUSTMENT.
# REPLACE HAVING DEFAULT GB AND FB FOR OPPONENT CHART
GB_MULTIPLIER = {
    'hitter': {
        '2000': 1.00,
        '2001': 1.11,
        '2002': 1.15,
        '2003': 1.12,
        '2004': 1.1,
        '2005': 1.1,
        f'2022-{CLASSIC_ALIAS}': 1.0,
        f'2022-{EXPANDED_ALIAS}': 1.0,
    },
    'pitcher': {
        '2000': 0.85,
        '2001': 0.93,
        '2002': 0.91,
        '2003': 1.05,
        '2004': 1.05,
        '2005': 1.05,
        f'2022-{CLASSIC_ALIAS}': 1.0,
        f'2022-{EXPANDED_ALIAS}': 1.0,
    },
}
# MULTIPLIER TO MATCH PU WITH ORIGINAL SETS
HR_ROUNDING_CUTOFF = {
    '2000': 0.85,
    '2001': 0.85,
    '2002': 0.85,
    '2003': 0.85,
    '2004': 0.85,
    '2005': 0.85,
    f'2022-{CLASSIC_ALIAS}': 0.75,
    f'2022-{EXPANDED_ALIAS}': 0.75,
}
"""
BASELINE PITCHER VALUES
NOTE: INDIVIDUAL RESULT CATEGORIES MAY NOT ADD UP TO 20 OR TOTAL OUTS.
      THIS IS BECAUSE NOT DOING SO HELPS ACCURACY AGAINST THE ORIGINAL SETS.
"""
BASELINE_PITCHER = {
    '2000': {
        'command': 3.0,
        'outs': 15.75,
        'so': 4.5,
        'bb': 1.35,
        '1b': 1.95,
        '2b': 0.67,
        '3b': 0.00,
        'hr': 0.08
    },
    '2001': {
        'command': 3.0,
        'outs': 16.0,
        'so': 4.1,
        'bb': 1.35,
        '1b': 2.0,
        '2b': 0.62,
        '3b': 0.00,
        'hr': 0.11
    },
    '2002': {
        'command': 3.3,
        'outs': 16.7,
        'so': 4.20,
        'bb': 1.05,
        '1b': 1.40,
        '2b': 0.51,
        '3b': 0.01,
        'hr': 0.13
    },
    '2003': {
        'command': 3.9,
        'outs': 16.3,
        'so': 3.65,
        'bb': 1.2,
        '1b': 1.93,
        '2b': 0.54,
        '3b': 0.13,
        'hr': 0.28
    },
    '2004': {
        'command': 3.85,
        'outs': 16.35,
        'so': 4.0,
        'bb': 1.1,
        '1b': 2.1,
        '2b': 0.48,
        '3b': 0.09,
        'hr': 0.3
    },
    '2005': {
        'command': 3.9,
        'outs': 16.2,
        'so': 3.87,
        'bb': 1.25,
        '1b': 2.05,
        '2b': 0.50,
        '3b': 0.09,
        'hr': 0.33
    },
    # INCREASED FOR 2022 TO ACCOUNT FOR BETTER AVG PITCHING IN MLB
    f'2022-{CLASSIC_ALIAS}': {
        'command': 3.3,
        'outs': 16.0,
        'so': 5.25,
        'bb': 1.35,
        '1b': 2.0,
        '2b': 0.62,
        '3b': 0.00,
        'hr': 0.11
    },
    f'2022-{EXPANDED_ALIAS}': {
        'command': 4.2,
        'outs': 16.2,
        'so': 5.5,
        'bb': 1.25,
        '1b': 2.05,
        '2b': 0.50,
        '3b': 0.09,
        'hr': 0.33
    },
}

"""
BASELINE HITTER VALUES
NOTE: INDIVIDUAL RESULT CATEGORIES MAY NOT ADD UP TO 20 OR TOTAL OUTS.
      THIS IS BECAUSE NOT DOING SO HELPS ACCURACY AGAINST THE ORIGINAL SETS.
"""
BASELINE_HITTER = {
    '2000': {
        'command': 7.7,
        'outs': 3.7,
        'so': 0.2,
        'bb': 4.4,
        '1b': 6.65,
        '1b+': 0.41,
        '2b': 1.94,
        '3b': 0.30,
        'hr': 1.98
    },
    '2001': {
        'command': 7.8,
        'outs': 3.9,
        'so': 1.31,
        'bb': 4.45,
        '1b': 6.7,
        '1b+': 0.63,
        '2b': 1.95,
        '3b': 0.2,
        'hr': 2.0
    },
    '2002': {
        'command': 9.4,
        'outs': 6.0,
        'so': 2.09,
        'bb': 3.35,
        '1b': 6.0,
        '1b+': 0.2,
        '2b': 1.94,
        '3b': 0.24,
        'hr': 1.52
    },
    '2003': {
        'command': 8.6,
        'outs': 7.2,
        'so': 2.1,
        'bb': 3.0,
        '1b': 6.57,
        '1b+': 0.28,
        '2b': 1.55,
        '3b': 0.32,
        'hr': 1.75
    },
    '2004': {
        'command': 9.05,
        'outs': 7.5,
        'so': 2.3,
        'bb': 2.95,
        '1b': 6.59,
        '1b+': 0.12,
        '2b': 1.25,
        '3b': 0.17,
        'hr': 1.6
    },
    '2005': {
        'command': 9.0,
        'outs': 7.3,
        'so': 2.4,
        'bb': 3.3,
        '1b': 6.0,
        '1b+': 0.12,
        '2b': 1.3,
        '3b': 0.19,
        'hr': 1.4
    },
    f'2022-{CLASSIC_ALIAS}': {
        'command': 7.5,
        'outs': 4.0,
        'so': 2.0,
        'bb': 4.45,
        '1b': 6.7,
        '1b+': 0.63,
        '2b': 1.95,
        '3b': 0.2,
        'hr': 2.0
    },
    f'2022-{EXPANDED_ALIAS}': {
        'command': 9.5,
        'outs': 7.4,
        'so': 3.0,
        'bb': 3.3,
        '1b': 6.0,
        '1b+': 0.12,
        '2b': 1.3,
        '3b': 0.19,
        'hr': 1.4
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
        [7,3],[7,4],[7,5],
        [8,3],[8,4],[8,5],
        [9,3],[9,4],[9,5],
        [10,2],[10,3],[10,4],[10,5],
        [11,2],[11,3],
        [12,0],[12,2],[12,3]
    ],
    '2001':[
        [4,5],[4,6],
        [5,2],[5,3],[5,4],[5,5],[5,6],
        [6,2],[6,3],[6,4],[6,5],[6,6],
        [7,3],[7,4],[7,5],[7,6],
        [8,3],[8,4],[8,5],
        [9,3],[9,4],[9,5],
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
        [16,3],[16,6],
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
        [15,6],
        [16,3],[16,4],[16,5],[16,6]
    ],
    '2004':[
        [9,5],[9,6],[9,7],[9,8],[9,9],
        [10,5],[10,6],[10,7],
        [11,5],[11,6],[11,7],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],[14,7],
        [15,6],
        [16,3],[16,6]
    ],
    '2005':[
        [9,5],[9,6],[9,7],[9,8],[9,9],[9,10],[9,11],
        [10,5],[10,6],[10,7],
        [11,5],[11,6],[11,7],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],
        [15,6],
        [16,3],[16,6]
    ],
    f'2022-{CLASSIC_ALIAS}': [
        [4,5],[4,6],
        [5,2],[5,3],[5,4],[5,5],[5,6],
        [6,2],[6,3],[6,4],[6,5],[6,6],
        [7,3],[7,4],[7,5],[7,6],
        [8,3],[8,4],[8,5],[8,6],
        [9,3],[9,4],[9,5],[9,6],
        [10,2],[10,3],[10,4],
        [11,2],[11,3],[11,4],
        [12,0],[12,2],[12,3]
    ],
    f'2022-{EXPANDED_ALIAS}': [
        [7,7],[7,8],[7,9],
        [8,5],[8,6],[8,7],[8,8],[8,9],[8,10],[8,11],
        [9,5],[9,6],[9,7],[9,8],[9,9],[9,10],[9,11],
        [10,5],[10,6],[10,7],[10,8],
        [11,5],[11,6],[11,7],[11,8],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],[14,7],
        [15,6],[15,7],
        [16,3],[16,6],
    ],

}
CONTROL_COMBOS = {
    '2000':[
        [0,17],[0,18],
        [2,15],[2,16],
        [3,15],[3,16],[3,17],[3,18],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,15],[5,16],[5,17],[5,18],[5,19],
        [6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    '2001':[
        [0,17],[0,18],
        [1,17],
        [2,16],[2,17],
        [3,14],[3,15],[3,16],[3,17],
        [4,14],[4,15],[4,16],[4,17],
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
        [1,15],[1,16],
        [2,14],[2,15],[2,16],
        [3,14],[3,15],[3,16],
        [4,14],[4,15],[4,16],[4,17],
        [5,15],[5,16],[5,17],[5,18],
        [6,16],[6,17],[6,18],[6,20],
    ],
    '2004':[
        [1,13],[1,14],[1,15],[1,16],
        [2,14],[2,15],[2,16],
        [3,15],[3,16],[3,17],
        [4,14],[4,16],[4,17],
        [5,12],[5,15],[5,16],[5,17],[5,18],[5,19],
        [6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    '2005':[
        [1,14],[1,15],[1,16],
        [2,15],[2,16],
        [3,15],[3,16],[3,17],
        [4,16],[4,17],
        [5,16],[5,17],[5,18],[5,19],
        [6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    f'2022-{CLASSIC_ALIAS}': [
        [0,17],[0,18],
        [1,17],[1,18],
        [1,16],[2,16],[2,17],[2,18],
        [3,14],[3,15],[3,16],[3,17],[3,18],[3,19],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,14],[5,15],[5,16],[5,17],[5,18],[5,19],
        [6,14],[6,15],[6,16],[6,17],[6,18],[6,20],
    ],
    f'2022-{EXPANDED_ALIAS}': [
        [1,14],[1,15],[1,16],[1,17],[1,18],
        [2,15],[2,16],[2,17],[2,18],
        [3,15],[3,16],[3,17],[3,18],
        [4,16],[4,17],[4,18],[4,19],
        [5,16],[5,17],[5,18],[5,19],
        [6,15],[6,16],[6,17],[6,18],[6,20],
    ],
}

"""
MAX HITTER SO
  - MAXIMUM AMOUNT OF SO RESULTS FOR HITTERS IN EACH SET
"""
MAX_HITTER_SO_RESULTS = {
    '2000': 4,
    '2001': 5,
    '2002': 6,
    '2003': 4,
    '2004': 4,
    '2005': 4,
    f'2022-{CLASSIC_ALIAS}': 5,
    f'2022-{EXPANDED_ALIAS}': 4,
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
    f'2022-{CLASSIC_ALIAS}': {
        'min': 3.2,
        'max': 9.6
    },
    f'2022-{EXPANDED_ALIAS}': {
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
    '2001': {
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
    f'2022-{CLASSIC_ALIAS}': {
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
    f'2022-{EXPANDED_ALIAS}': {
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
    f'2022-{CLASSIC_ALIAS}': {
        'position_player': {
            'defense': 65,
            'speed': 65,
            'onbase': 200,
            'average': 55,
            'slugging': 170,
            'home_runs': 50
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
    f'2022-{EXPANDED_ALIAS}': {
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
    f'2022-{CLASSIC_ALIAS}': {
        'C': 1.0,
        '1B': 0.5,
        '2B': 1.0,
        '3B': 1.0,
        'SS': 1.0,
        'CF': 1.0,
        'OF': 1.0,
        'LF/RF': 1.0,
        'IF': 1.0,
    },
    f'2022-{EXPANDED_ALIAS}': {
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
}

"""
ICON POINTS
"""
POINTS_ICONS = {
    '2003': {
        'G': 10,
        'S': 10,
        'V': 15,
        'HR': 15,
        'SB': 10,
        'RY': 10,
        'R': 0,
        'RP': 10,
        'K': 10,
        '20': 10,
        'CY': 15,
    },
    '2004': {
        'G': 10,
        'S': 10,
        'V': 15,
        'HR': 15,
        'SB': 10,
        'RY': 10,
        'R': 0,
        'RP': 10,
        'K': 10,
        '20': 10,
        'CY': 15,
    },
    '2005': {
        'G': 10,
        'S': 10,
        'V': 15,
        'HR': 15,
        'SB': 10,
        'RY': 10,
        'R': 0,
        'RP': 10,
        'K': 10,
        '20': 10,
        'CY': 15,
    },
    f'2022-{EXPANDED_ALIAS}': {
        'G': 10,
        'S': 10,
        'V': 15,
        'HR': 15,
        'SB': 10,
        'RY': 10,
        'R': 0,
        'RP': 10,
        'K': 10,
        '20': 10,
        'CY': 15,
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

        '2-17': 0.92,
        '3-17': 0.85,
        '4-14': 1.15,
        '4-15': 1.15,
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
    },
    '2005': {
        '9-5': 1.15,
        '9-6': 1.1,
        '9-7': 0.95,

        '3-15': 1.25,
        '3-16': 1.05,
        '3-17': 0.8,
        '3-18': 0.9,
        '4-17': 0.8,
        '5-17': 0.95,
        '6-17': 1.03,
    },
    f'2022-{CLASSIC_ALIAS}': {
        '10-4': 1.05,
        '10-2': 0.96,
        '9-5': 1.05,
        '9-3': 0.925,
        '8-4': 0.925,
        '8-3': 0.90,
        '7-4': 0.90,
        '7-3': 0.90,

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
    f'2022-{EXPANDED_ALIAS}': {
        '9-5': 1.15,
        '9-6': 1.1,
        '9-7': 0.95,

        '1-18': 0.90,
        '2-18': 0.90,
        '3-17': 0.90,
        '3-18': 0.90,
        '4-17': 0.90,
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
    f'2022-{CLASSIC_ALIAS}': {
        'position_player': True,
        'starting_pitcher': False,
        'relief_pitcher': False,
    },
    f'2022-{EXPANDED_ALIAS}': {
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
    f'2022-{CLASSIC_ALIAS}': {
        'position_player': False,
        'starting_pitcher': True,
        'relief_pitcher': True,
    },
    f'2022-{EXPANDED_ALIAS}': {
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
        'starting_pitcher': 0.75,
        'relief_pitcher': 0.675,
    },
    '2005': {
        'position_player': 0.65,
        'starting_pitcher': 0.75,
        'relief_pitcher': 0.74,
    },
    f'2022-{CLASSIC_ALIAS}': {
        'position_player': 0.65,
        'starting_pitcher': 0.70,
        'relief_pitcher': 0.72,
    },
    f'2022-{EXPANDED_ALIAS}': {
        'position_player': 0.65,
        'starting_pitcher': 0.75,
        'relief_pitcher': 0.70,
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
    f'2022-{CLASSIC_ALIAS}': 1.5,
    f'2022-{EXPANDED_ALIAS}': 2.0,
}

"""
POINTS_RELIEVER_IP_MULTIPLIER
  - WHAT PERCENT OF POINTS TO GIVE FOR 2ND INNING OF RELIEF
"""
POINTS_RELIEVER_IP_MULTIPLIER = {
    '2000': 0.95,
    '2001': 0.80,
    '2002': 0.60,
    '2003': 0.55,
    '2004': 0.67,
    '2005': 0.625,
    f'2022-{CLASSIC_ALIAS}': 0.80,
    f'2022-{EXPANDED_ALIAS}': 0.625,
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
    f'2022-{CLASSIC_ALIAS}': {
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
    f'2022-{EXPANDED_ALIAS}': {
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
    f'2022-{CLASSIC_ALIAS}': {
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
    f'2022-{EXPANDED_ALIAS}': {
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
            'min': 0.350,
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
            'min': 0.350,
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
            'min': 0.360,
            'max': 0.550
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
            'min': 0.360,
            'max': 0.545
        }
    },
    f'2022-{CLASSIC_ALIAS}': {
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
    f'2022-{EXPANDED_ALIAS}': {
        'starting_pitcher': {
            'min': 0.335,
            'max': 0.475
        },
        'relief_pitcher': {
            'min': 0.330,
            'max': 0.480
        },
        'position_player': {
            'min': 0.360,
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
    f'2022-{CLASSIC_ALIAS}': {
        'min': 10,
        'max': 20
    },
    f'2022-{EXPANDED_ALIAS}': {
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
    f'2022-{CLASSIC_ALIAS}': {
        'min': 10,
        'max': 35
    },
    f'2022-{EXPANDED_ALIAS}': {
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
    f'2022-{CLASSIC_ALIAS}': {
        'C': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.5,
        'SS': 6.0,
        'LF': 2.0,
        'CF': 3.5,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.5,
        'LF/RF': 2.0,
        'DH': 0
    },
    f'2022-{EXPANDED_ALIAS}': {
        'CA': 12.0,
        '1B': 1.0,
        '2B': 5.0,
        '3B': 4.5,
        'SS': 6.0,
        'LF': 2.0,
        'CF': 3.5,
        'RF': 2.0,
        'OF': 2.0,
        'IF': 1.5,
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

""" COORDINATES FOR IMAGE COMPONENTS """
IMAGE_LOCATIONS = {
    'team_logo': {
        '2000': (1200,1086),
        '2001': (78,1584),
        '2002': (80,1380),
        '2003': (1179,1074),
        '2004': (1161,1440),
        '2005': (1161,1440),
        '2022': (1161,1375),
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
    'number': {
        '2002': (120,1785),
        '2003': (116,1785),
        '2004': (1191,1911),
        '2005': (1191,1911),
        '2022': (1000,2020),
    },
    'super_season': {
        '2000': (1200,1035),
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
    'version': {
        '2000': (1360,2050),
        '2001': (1360,2050),
        '2002': (164,2011),
        '2003': (752,1810),
        '2004': (1355,2069),
        '2005': (1355,2069),
        '2022': (1417,2064),
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
        '2022': (60,1995),
    }
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
        '2000': (273,420),
        '2001': (273,420),
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
    }
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

""" ALTERNATE TEAM LOGO RANGES. NOTE: END YEAR SHOULD BE YEAR OF NEW LOGO """

TEAM_LOGO_ALTERNATES = {
    'ANA': {
        '1': list(range(2002, 2005)),
    },
    'ARI': {
        '1': list(range(1998,2007))
    },
    'ATL': {
        '1': list(range(1966,1972)),
        '2': list(range(1972,1981)),
        '3': list(range(1981,1987)),
    },
    'BAL': {
        '1': list(range(1872,1900)),
        '2': list(range(1914,1916)),
        '3': list(range(1954,1966)),
        '4': list(range(1966,1992)),
        '5': list(range(1992,1995)),
        '6': list(range(1995,2009)),
        '7': list(range(2009,2019)),
    },
    'BOS': {
        '1': list(range(1871,1901)),
        '2': list(range(1901,1924)),
        '3': list(range(1924,1961)),
        '4': list(range(1961,1976)),
    },
    'CHC': {
        '1': list(range(1876,1919)),
        '2': list(range(1919,1946)),
        '3': list(range(1946,1957)),
        '4': list(range(1957,1979)),
        '5': list(range(1979,1997)),
    },
    'CHW': {
        '1': list(range(1901,1939)),
        '2': list(range(1939,1960)),
        '3': list(range(1960,1976)),
        '4': list(range(1976,1991)),
    },
    'CIN': {
        '1': list(range(1876,1953)),
        '2': list(range(1953,1968)),
        '3': list(range(1968,1993)),
        '4': list(range(1993,1999)),
    },
    'CLE': {
        '1': list(range(1871,1921)),
        '2': list(range(1921,1946)),
        '3': list(range(1946,1973)),
        '4': list(range(1973,1979)),
        '5': list(range(1979,2013)),
        '6': list(range(2013,2022)),
    },
    'DET': {
        '1': list(range(1901,1957)),
        '2': list(range(1957,1994)),
        '3': list(range(1994,2005)),
    },
    'HOU': {
        '1': list(range(1965,1994)),
        '2': list(range(1994,2000)),
        '3': list(range(2000,2013)),
    },
    'KCR': {
        '1': list(range(1969,1986)),
        '2': list(range(1986,1993)),
        '3': list(range(1993,2002)),
    },
    'MIA': {
        '1': list(range(2012,2019)),
    },
    'MIL': {
        '1': list(range(1970,1978)),
        '2': list(range(1978,1994)),
        '3': list(range(1994,2000)),
        '4': list(range(2000,2018)),
    },
    'MIN': {
        '1': list(range(1961,1987)),
        '2': list(range(1987,2009)),
    },
    'NYM': {
        '1': list(range(1962,1993)),
        '2': list(range(1993,1998)),
        '3': list(range(1998,2011)),
    },
    'NYY': {
        '1': list(range(1900,1950)),
    },
    'OAK': {
        '1': list(range(1968,1982)),
        '2': list(range(1982,1993)),
    },
    'PHI': {
        '1': list(range(1900,1950)),
        '2': list(range(1950,1970)),
        '3': list(range(1970,1992)),
        '4': list(range(1992,2019)),
    },
    'PIT': {
        '1': list(range(1900,1948)),
        '2': list(range(1948,1970)),
        '3': list(range(1970,2009)),
    },
    'SDP': {
        '1': list(range(1969,1985)),
        '2': list(range(1985,1992)),
        '3': list(range(1992,2004)),
        '4': list(range(2004,2012)),
    },
    'SEA': {
        '1': list(range(1977,1981)),
        '2': list(range(1981,1987)),
        '3': list(range(1987,1993)),
    },
    'SFG': {
        '1': list(range(1968,1983)),
        '2': list(range(1983,1994)),
        '3': list(range(1994,2000)),
    },
    'STL': {
        '1': list(range(1875,1927)),
        '2': list(range(1927,1965)),
        '3': list(range(1965,1998)),
    },
    'TBD': {
        '1': list(range(1998,2001)),
    },
    'TEX': {
        '1': list(range(1972,1982)),
        '2': list(range(1982,1994)),
        '3': list(range(1994,2003)),
    },
    'TOR': {
        '1': list(range(1977,1997)),
        '2': list(range(1997,2003)),
        '3': list(range(2003,2012)),
    },
    'WSN': {
        '1': list(range(2005,2011)),
    },
}

TEAM_COLOR_PRIMARY = {
    'AB2': (172, 0, 0, 255),
    'AB3': (172, 0, 0, 255),
    'ABC': (172, 0, 0, 255),
    'AG': (2, 2, 2, 255),
    'AG': (2, 2, 2, 255),
    'ALT': (104, 5, 49, 255),
    'ANA': (19, 41, 75, 255),
    'ARI': (167, 25, 48, 255),
    'ATH': (0, 51, 160, 255),
    'ATL': (206, 17, 65, 255),
    'BAL': (223, 70, 1, 255),
    'BBB': (184, 0, 0, 255),
    'BBS': (135, 72, 42, 255),
    'BCA': (10, 53, 132, 255),
    'BE': (12, 35, 64, 255),
    'BEG': (0, 4, 42, 255),
    'BLA': (236, 165, 73, 255),
    'BLU': (243, 105, 22, 255),
    'BLN': (21, 10, 106, 255),
    'BOS': (189, 48, 57, 255),
    'BRA': (55, 55, 55, 255),
    'BRO': (8, 41, 132, 255),
    'BRG': (248, 41, 31, 255),
    'BSN': (213, 0, 50, 255),
    'BTT': (1, 55, 129, 255),
    'BUF': (36, 32, 33, 255),
    'BWW': (8, 41, 132, 255),
    'CAL': (191, 13, 62, 255),
    'CAG': (18, 44, 73, 255),
    'CBB': (25, 73, 158, 255),
    'CBE': (200, 16, 46, 255),
    'CBN': (37, 76, 139, 255),
    'CC': (228, 0, 23, 255),
    'CCB': (200, 16, 46, 255),
    'CCC': (160, 135, 69, 255),
    'CCU': (192, 0, 49, 255),
    'CEG': (0, 4, 42, 255),
    'CEL': (37, 76, 139, 255),
    'CEN': (192, 0, 49, 255),
    'CHC': (14, 51, 134, 255),
    'CHI': (1, 31, 105, 255),
    'CHT': (14, 0, 119, 255),
    'CHW': (39, 37, 31, 255),
    'CIN': (198,1,31,255),
    'CLE': (227,25,55,255),
    'CKK': (209, 9, 47, 255),
    'CLV': (14, 0, 119, 255),
    'COL': (51,0,111,255),
    'COR': (198,1,31,255),
    'CRS': (14, 0, 119, 255),
    'CSE': (10, 34, 64, 255),
    'CS': (10, 34, 64, 255),
    'CSW': (10, 34, 64, 255),
    'CT': (198,1,31,255),
    'CTG': (198,1,31,255),
    'DET': (12, 35, 64, 255),
    'DS': (193, 44, 56, 255),
    'DTS': (193, 44, 56, 255),
    'DW': (189, 47, 45, 255),
    'FLA': (2, 159, 171, 255),
    'HAR': (5, 0, 51, 255),
    'HBG': (5, 0, 51, 255),
    'HG': (2, 2, 2, 255),
    'HIL': (203, 17, 66, 255),
    'HOU': (235, 110, 31, 255),
    'IAB': (172, 0, 0, 255),
    'IA': (160, 39, 60, 255),
    'IC': (228, 0, 23, 255),
    'ID': (172, 0, 0, 255),
    'JRC': (219, 35, 77, 255),
    'KCA': (2, 133, 68, 255),
    'KCC': (34, 39, 63, 255),
    'KCM': (243, 0, 0, 255),
    'KCN': (34, 39, 63, 255),
    'KCR': (0, 70, 135, 255),
    'LAA': (186, 0, 33, 255),
    'LAD': (0, 90, 156, 255),
    'LOU': (185, 32, 39, 255),
    'LOW': (234, 26, 43, 255),
    'LRG': (18, 26, 65, 255),
    'LVB': (234, 26, 43, 255),
    'MB': (45, 45, 45, 255),
    'MGS': (19, 16, 45, 255),
    'MIA': (0, 163, 224, 255),
    'MIL': (18, 40, 75, 255),
    'MIN': (211,17,69,255),
    'MLA': (0, 33, 68, 255),
    'MON': (228, 0, 43, 255),
    'MRS': (181, 0, 51, 255),
    'NE': (12, 35, 64, 255),
    'NBY': (25, 37, 62, 255),
    'NEG': (0, 4, 42, 255),
    'NLG': (17, 36, 55, 255),
    'NYC': (162, 0, 45, 255),
    'NYG': (227, 82, 5, 255),
    'NYM': (252, 89, 16, 255),
    'NYU': (7, 91, 72, 255),
    'NYY': (12, 35, 64, 255),
    'OAK': (0, 56, 49, 255),
    'OLY': (2, 17, 103, 255),
    'PBG': (0, 0, 0, 255),
    'PBS': (15, 135, 1, 255),
    'PC': (123, 46, 42, 255),
    'PHA': (0, 51, 160, 255),
    'PHI': (232, 24, 40, 255),
    'PK': (255, 196, 12, 255),
    'PIT': (253, 184, 39, 255),
    'PRO': (35, 31, 32, 255),
    'PS': (192, 62, 51, 255),
    'PTG': (203, 17, 66, 255),
    'RES': (0, 4, 91, 255),
    'RIC': (250, 138, 49, 255),
    'ROC': (101, 55, 19, 255),
    'ROK': (17, 111, 59, 255),
    'SDP': (249, 182, 1, 255),
    'SEA': (0, 92, 92, 255),
    'SEP': (0, 79, 157, 255),
    'SFG': (253, 90, 30, 255),
    'SLB': (227, 73, 18, 255),
    'SLG': (10, 34, 64, 255),
    'SLM': (5, 14, 55, 255),
    'SLR': (200, 16, 46, 255),
    'SL2': (214, 0, 36, 255),
    'SL3': (214, 0, 36, 255),
    'SNS': (214, 0, 36, 255),
    'STL': (196, 30, 58, 255),
    'STP': (20, 52, 141, 255),
    'TC': (158, 25, 23, 255),
    'TC2': (158, 25, 23, 255),
    'TBD': (0, 70, 55, 255),
    'TBR': (70, 188, 230, 255),
    'TEX': (192,17,31, 255),
    'TOL': (64, 62, 98, 255),
    'TOR': (19, 74, 142, 255),
    'TT': (189, 47, 45, 255),
    'WAP': (103, 172, 221, 255),
    'WAS': (0, 33, 68, 255),
    'WEG': (0, 4, 42, 255),
    'WHS': (0, 33, 68, 255),
    'WIL': (99, 61, 146, 255),
    'WMP': (228, 0, 23, 255),
    'WOR': (224, 17, 95, 255),
    'WP': (228, 0, 23, 255),
    'WSA': (0, 33, 68, 255),
    'WSH': (0, 33, 68, 255),
    'WSN': (171, 0, 3, 255),
}

TEAM_COLOR_PRIMARY_ALT = {
    'ANA': {
        '1': (186,0,33,255),
    },
    'ARI': {
        '1': (0,96,86,255),
    },
    'ATL': {
        '1': (1, 51, 172, 255),
        '2': (213, 0, 50, 255),
        '3': (213, 0, 50, 255),
    },
    'BAL': {
        '1': (21, 10, 106, 255),
        '2': (243, 105, 22, 255),
        '3': (220, 72, 20, 255),
        '4': (220, 72, 20, 255),
        '5': (220, 72, 20, 255),
        '6': (220, 72, 20, 255),
        '7': (220, 72, 20, 255),
    },
    'BOS': {
        '1': (189, 48, 57, 255),
        '2': (189, 48, 57, 255),
        '3': (189, 48, 57, 255),
        '4': (189, 48, 57, 255),
    },
    'CHC': {
        '1': (12, 35, 64, 255),
        '2': (14, 51, 134, 255),
        '3': (14, 51, 134, 255),
        '4': (14, 51, 134, 255),
        '5': (14, 51, 134, 255),
    },
    'CHW': {
        '1': (0, 38, 99, 255),
        '2': (0, 38, 99, 255),
        '3': (0, 38, 99, 255),
        '4': (0, 38, 99, 255),
    },
    'CIN': {
        '1': (198,1,31,255),
        '2': (198,1,31,255),
        '3': (198,1,31,255),
        '4': (198,1,31,255),
    },
    'CLE': {
        '1': (0,33,68,255),
        '2': (215,0,44,255),
        '3': (215,0,44,255),
        '4': (215,0,44,255),
        '5': (215,0,44,255),
        '6': (237,23,79,255),
    },
    'DET': {
        '1': (0,33,68,255),
        '2': (0,33,68,255),
        '3': (0,33,68,255),
    },
    'HOU': {
        '1': (255, 72, 25, 255),
        '2': (114, 116, 74, 255),
        '3': (157, 48, 34, 255),
    },
    'KCR': {
        '1': (0, 70, 135, 255),
        '2': (0, 70, 135, 255),
        '3': (0, 70, 135, 255),
    },
    'MIA': {
        '1': (255, 102, 0, 255),
    },
    'MIL': {
        '1': (18, 40, 75, 255),
        '2': (0, 70, 174, 255),
        '3': (141, 116, 74, 255),
        '4': (18, 40, 75, 255),
    },
    'MIN': {
        '1': (190, 15, 52, 255),
        '2': (190, 15, 52, 255),
    },
    'NYM': {
        '1': (252, 89, 16, 255),
        '2': (252, 89, 16, 255),
        '3': (252, 89, 16, 255),
    },
    'NYY': {
        '1': (12, 35, 64, 255),
    },
    'OAK': {
        '1': (0, 56, 49, 255),
        '2': (0, 56, 49, 255),
    },
    'PHI': {
        '1': (232, 24, 40, 255),
        '2': (232, 24, 40, 255),
        '3': (232, 24, 40, 255),
        '4': (232, 24, 40, 255),
    },
    'PIT': {
        '1': (253, 184, 39, 255),
        '2': (253, 184, 39, 255),
        '3': (253, 184, 39, 255),
    },
    'SDP': {
        '1': (97, 55, 30, 255),
        '2': (70, 36, 37, 255),
        '3': (10, 35, 67, 255),
        '4': (183, 166, 109, 255),
    },
    'SEA': {
        '1': (0, 40, 120, 255),
        '2': (0, 40, 120, 255),
        '3': (0, 40, 120, 255),
    },
    'SFG': {
        '1': (253, 90, 30, 255),
        '2': (253, 90, 30, 255),
        '3': (253, 90, 30, 255),
    },
    'STL': {
        '1': (196, 30, 58, 255),
        '2': (196, 30, 58, 255),
        '3': (196, 30, 58, 255),
    },
    'TBD': {
        '1': (17, 141, 196, 255),
    },
    'TEX': {
        '1': (235, 0, 44, 255),
        '2': (235, 0, 44, 255),
        '3': (192, 17, 31, 255),
    },
    'TOR': {
        '1': (0, 107, 166, 255),
        '2': (0, 107, 166, 255),
        '3': (0, 75, 135, 255),
    },
    'WSN': {
        '1': (171,0,3,255),
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
}

G_DRIVE_TEAM_BACKGROUND_FOLDERS = {
    '2000': '1PCLjUznKwkfIzcCiHz79J9z6b-jgE0w9',
    '2001': '1JxgfhicVJDNK1PJEiw4zFWa5nqlnx_p5',
}