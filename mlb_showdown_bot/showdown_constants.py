
# -------------------------------------------
# SHOWDOWN_CONSTANTS.PY
#   - ONE FILE TO STORE ALL WEIGHTS / STATIC VALUES
#     NEEDED TO GENERATE PLAYER CARDS
# -------------------------------------------

"""
SPEED AND FIELDING
  - MIN AND MAX USED IN PERCENTILE CALCULATIONS
  - ** STOLEN BASES MINIMUM IS NEGATIVE JUST TO BALANCE OUT PERCENTILE RANGE
"""
MAX_SPRINT_SPEED = 31
MIN_SPRINT_SPEED = 23
MAX_STOLEN_BASES = 28
MIN_STOLEN_BASES = -25
MAX_SABER_FIELDING = 18
MIN_SABER_FIELDING = -18
NUMBER_OF_GAMES = 10 # MINIMUM REQUIRED GAMES PLAYED AT A POSITION TO QUALIFY

"""
BASELINE PITCHER VALUES
NOTE: INDIVIDUAL RESULT CATEGORIES MAY NOT ADD UP TO 20 OR TOTAL OUTS.
      THIS IS BECAUSE NOT DOING SO HELPS ACCURACY AGAINST THE ORIGINAL SETS.
"""
BASELINE_PITCHER = {
    '2000': {
        'command': 3.0,
        'outs': 15.2,
        'pu': 2.32,
        'so': 3.9,
        'gb': 5.1,
        'fb': 3.9,
        'bb': 1.24,
        '1b': 1.97,
        '2b': 0.67,
        '3b': 0.01,
        'hr': 0.085
    },
    '2001': {
        'command': 3.1,
        'outs': 16.1,
        'pu': 2.69,
        'so': 4.30,
        'gb': 5.56,
        'fb': 3.41,
        'bb': 1.24,
        '1b': 1.97,
        '2b': 0.73,
        '3b': 0.00,
        'hr': 0.1
    },
    '2002': {
        'command': 3.7,
        'outs': 15.7,
        'pu': 3.10,
        'so': 4.93,
        'gb': 5.64,
        'fb': 3.44,
        'bb': 0.89,
        '1b': 1.40,
        '2b': 0.5,
        '3b': 0.01,
        'hr': 0.3
    },
    '2003': {
        'command': 4.2,
        'outs': 16.3,
        'pu': 2.1,
        'so': 4.33,
        'gb': 6.47,
        'fb': 3.19,
        'bb': 1.00,
        '1b': 1.93,
        '2b': 0.57,
        '3b': 0.025,
        'hr': 0.25
    },
    '2004': {
        'command': 3.9,
        'outs': 16.9,
        'pu': 2.09,
        'so': 4.25,
        'gb': 6.29,
        'fb': 4.0,
        'bb': 0.9,
        '1b': 2.1,
        '2b': 0.66,
        '3b': 0.025,
        'hr': 0.2
    },
    '2005': {
        'command': 4.2,
        'outs': 16.6,
        'pu': 2.01,
        'so': 4.31,
        'gb': 6.42,
        'fb': 3.45,
        'bb': 1.0,
        '1b': 2.05,
        '2b': 0.65,
        '3b': 0.02,
        'hr': 0.15
    }
}

"""
BASELINE HITTER VALUES
NOTE: INDIVIDUAL RESULT CATEGORIES MAY NOT ADD UP TO 20 OR TOTAL OUTS.
      THIS IS BECAUSE NOT DOING SO HELPS ACCURACY AGAINST THE ORIGINAL SETS.
"""
BASELINE_HITTER = {
    '2000': {
        'command': 8.1,
        'outs': 3.7,
        'pu': 0,
        'so': 1.15,
        'gb': 1.77,
        'fb': 1.09,
        'bb': 4.70,
        '1b': 6.60,
        '1b+': 0.41,
        '2b': 1.95,
        '3b': 0.34,
        'hr': 1.98
    },
    '2001': {
        'command': 7.7,
        'outs': 3.4,
        'pu': 0,
        'so': 1.31,
        'gb': 1.62,
        'fb': 1.11,
        'bb': 4.23,
        '1b': 6.67,
        '1b+': 0.63,
        '2b': 1.88,
        '3b': 0.39,
        'hr': 2.15
    },
    '2002': {
        'command': 9.8,
        'outs': 6.2,
        'pu': 0,
        'so': 2.09,
        'gb': 2.53,
        'fb': 1.82,
        'bb': 3.3,
        '1b': 6.0,
        '1b+': 0.2,
        '2b': 1.94,
        '3b': 0.24,
        'hr': 1.52
    },
    '2003': {
        'command': 9.1,
        'outs': 6.5,
        'pu': 0,
        'so': 1.44,
        'gb': 2.6,
        'fb': 2.13,
        'bb': 2.9,
        '1b': 6.57,
        '1b+': 0.28,
        '2b': 1.69,
        '3b': 0.17,
        'hr': 1.4
    },
    '2004': {
        'command': 9.8,
        'outs': 6.0,
        'pu': 0,
        'so': 1.46,
        'gb': 2.54,
        'fb': 2.11,
        'bb': 3.0,
        '1b': 6.59,
        '1b+': 0.12,
        '2b': 1.65,
        '3b': 0.17,
        'hr': 1.4
    },
    '2005': {
        'command': 9.85,
        'outs': 6.4,
        'pu': 0,
        'so': 1.66,
        'gb': 2.54,
        'fb': 2.11,
        'bb': 3.1,
        '1b': 5.9,
        '1b+': 0.12,
        '2b': 1.3,
        '3b': 0.17,
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
        [15,7]
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
        [15,0],[15,1],[15,2],[15,6],
        [16,3],[16,4],[16,5],[16,6]
    ],
    '2004':[
        [9,5],[9,6],[9,7],[9,8],[9,9],
        [10,5],[10,6],[10,7],[10,8],
        [11,5],[11,6],[11,7],[11,8],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],[14,7],
        [15,6],
        [16,3],[16,6]
    ],
    '2005':[
        [9,5],[9,6],[9,7],[9,8],[9,9],[9,10],[9,11],
        [10,5],[10,6],[10,7],
        [11,4],[11,5],[11,6],[11,7],
        [12,5],[12,6],[12,7],
        [13,5],[13,6],[13,7],
        [14,5],[14,6],
        [15,6],
        [16,3],[16,6]
    ]
}
CONTROL_COMBOS = {
    '2000':[
        [0,17],[0,18],
        [2,15],[2,16],
        [3,15],[3,16],[3,17],[3,18],
        [4,14],[4,15],[4,16],[4,17],[4,18],
        [5,15],[5,16],[5,17],[5,18],
        [6,15],[6,16],[6,17]
    ],
    '2001':[
        [0,17],[0,18],
        [1,17],
        [2,16],[2,17],
        [3,14],[3,15],[3,16],[3,17],
        [4,14],[4,15],[4,16],[4,17],
        [5,14],[5,15],[5,16],[5,17],
        [6,14],[6,15],[6,16]
    ],
    '2002':[
        [1,15],[1,16],[1,17],[1,18],
        [2,15],[2,16],[2,17],[2,18],[2,19],
        [3,15],[3,16],[3,17],[3,18],[3,19],
        [4,14],[4,15],[4,16],[4,17],[4,18],[4,19],
        [5,15],[5,16],[5,17],[5,18],
        [6,16],[6,17],[6,18]
    ],
    '2003':[
        [1,14],[1,15],[1,16],[1,17],
        [2,14],[2,15],[2,16],[2,17],
        [3,14],[3,15],[3,16],[3,17],
        [4,14],[4,15],[4,16],[4,17],
        [5,15],[5,16],[5,17],
        [6,16],[6,17],[6,18]
    ],
    '2004':[
        [1,13],[1,14],[1,15],[1,16],[1,17],[1,18],[1,20],
        [2,14],[2,15],[2,16],[2,17],[2,18],
        [3,15],[3,16],[3,17],
        [4,13],[4,14],[4,15],[4,16],[4,17],[4,18],
        [5,12],[5,15],[5,16],[5,17],[5,18],
        [6,15],[6,16],[6,17],[6,18]
    ],
    '2005':[
        [1,14],[1,15],[1,16],
        [2,15],[2,16],[2,17],
        [3,15],[3,16],[3,17],[3,18],[3,19],
        [4,15],[4,16],[4,17],
        [5,15],[5,16],[5,17],[5,18],
        [6,15],[6,16],[6,17],[6,18]
    ]
}

"""
POINT WEIGHTS
  - POINT VALUE GIVEN TO A PLAYER IN THE 100TH PERCENTILE FOR A CATEGORY
"""
POINT_CATEGORY_WEIGHTS = {
    '2000': {
        'position_player': {
            'defense': 80,
            'speed': 70,
            'onbase': 270,
            'average': 160,
            'slugging': 110,
            'home_runs': 50
        },
        'starting_pitcher': {
            'ip': 90,
            'onbase': 410,
            'average': 150,
            'slugging': 160
        },
        'relief_pitcher': {
            'ip': 50,
            'onbase': 140,
            'average': 50,
            'slugging': 55
        }
    },
    '2001': {
        'position_player': {
            'defense': 70,
            'speed': 60,
            'onbase': 220,
            'average': 120,
            'slugging': 80,
            'home_runs': 40
        },
        'starting_pitcher': {
            'ip': 100,
            'onbase': 410,
            'average': 150,
            'slugging': 160
        },
        'relief_pitcher': {
            'ip': 60,
            'onbase': 160,
            'average': 60,
            'slugging': 70
        }
    },
    '2002': {
        'position_player': {
            'defense': 80,
            'speed': 70,
            'onbase': 250,
            'average': 130,
            'slugging': 110,
            'home_runs': 40
        },
        'starting_pitcher': {
            'ip': 70,
            'onbase': 400,
            'average': 110,
            'slugging': 120
        },
        'relief_pitcher': {
            'ip': 40,
            'onbase': 100,
            'average': 50,
            'slugging': 55
        }
    },
    '2003': {
        'position_player': {
            'defense': 70,
            'speed': 60,
            'onbase': 230,
            'average': 120,
            'slugging': 100,
            'home_runs': 50
        },
        'starting_pitcher': {
            'ip': 60,
            'onbase': 360,
            'average': 100,
            'slugging': 110
        },
        'relief_pitcher': {
            'ip': 60,
            'onbase': 130,
            'average': 60,
            'strikeouts': 10,
            'slugging': 65
        }
    },
    '2004': {
        'position_player': {
            'defense': 70,
            'speed': 60,
            'onbase': 180,
            'average': 100,
            'slugging': 90,
            'home_runs': 45
        },
        'starting_pitcher': {
            'ip': 60,
            'onbase': 300,
            'average': 125,
            'slugging': 125
        },
        'relief_pitcher': {
            'ip': 50,
            'onbase': 110,
            'average': 55,
            'slugging': 60
        }
    },
    '2005': {
        'position_player': {
            'defense': 70,
            'speed': 60,
            'onbase': 200,
            'average': 110,
            'slugging': 100,
            'home_runs': 45
        },
        'starting_pitcher': {
            'ip': 60,
            'onbase': 330,
            'average': 100,
            'slugging': 110
        },
        'relief_pitcher': {
            'ip': 60,
            'onbase': 125,
            'average': 60,
            'slugging': 65
        }
    }
}

"""
POINT CATEGORY RANGES
  - MIN AND MAX VALUES FOR EACH CATEGORY USED TO PRODUCE POINT VALUE.
  - USED TO CALCULATE A PLAYER'S PERCENTILE IN THAT CATEGORY.
"""
ONBASE_PCT_RANGE = {
    '2000': {
        'pitcher': {
            'min': 0.250,
            'max': 0.400
        },
        'hitter': {
            'min': 0.250,
            'max': 0.450
        }
    },
    '2001': {
        'pitcher': {
            'min': 0.240,
            'max': 0.400
        },
        'hitter': {
            'min': 0.250,
            'max': 0.450
        }
    },
    '2002': {
        'pitcher': {
            'min': 0.270,
            'max': 0.360
        },
        'hitter': {
            'min': 0.250,
            'max': 0.450
        }
    },
    '2003': {
        'pitcher': {
            'min': 0.240,
            'max': 0.400
        },
        'hitter': {
            'min': 0.270,
            'max': 0.425
        }
    },
    '2004': {
        'pitcher': {
            'min': 0.240,
            'max': 0.380
        },
        'hitter': {
            'min': 0.280,
            'max': 0.410
        }
    },
    '2005': {
        'pitcher': {
            'min': 0.240,
            'max': 0.380
        },
        'hitter': {
            'min': 0.280,
            'max': 0.410
        }
    }
}
BATTING_AVG_RANGE = {
    '2000': {
        'pitcher': {
            'min': 0.225,
            'max': 0.300
        },
        'hitter': {
            'min': 0.225,
            'max': 0.330
        }
    },
    '2001': {
        'pitcher': {
            'min': 0.210,
            'max': 0.290
        },
        'hitter': {
            'min': 0.225,
            'max': 0.330
        }
    },
    '2002': {
        'pitcher': {
            'min': 0.210,
            'max': 0.290
        },
        'hitter': {
            'min': 0.225,
            'max': 0.330
        }
    },
    '2003': {
        'pitcher': {
            'min': 0.210,
            'max': 0.290
        },
        'hitter': {
            'min': 0.245,
            'max': 0.320
        }
    },
    '2004': {
        'pitcher': {
            'min': 0.210,
            'max': 0.280
        },
        'hitter': {
            'min': 0.245,
            'max': 0.315
        }
    },
    '2005': {
        'pitcher': {
            'min': 0.210,
            'max': 0.280
        },
        'hitter': {
            'min': 0.245,
            'max': 0.330
        }
    }
}
SLG_RANGE = {
    '2000': {
        'pitcher': {
            'min': 0.330,
            'max': 0.500
        },
        'hitter': {
            'min': 0.350,
            'max': 0.550
        }
    },
    '2001': {
        'pitcher': {
            'min': 0.330,
            'max': 0.500
        },
        'hitter': {
            'min': 0.350,
            'max': 0.550
        }
    },
    '2002': {
        'pitcher': {
            'min': 0.330,
            'max': 0.500
        },
        'hitter': {
            'min': 0.350,
            'max': 0.550
        }
    },
    '2003': {
        'pitcher': {
            'min': 0.330,
            'max': 0.500
        },
        'hitter': {
            'min': 0.350,
            'max': 0.550
        }
    },
    '2004': {
        'pitcher': {
            'min': 0.330,
            'max': 0.480
        },
        'hitter': {
            'min': 0.350,
            'max': 0.550
        }
    },
    '2005': {
        'pitcher': {
            'min': 0.330,
            'max': 0.480
        },
        'hitter': {
            'min': 0.350,
            'max': 0.550
        }
    }
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
    }
}

"""
DEFENSIVE MAXIMUM
  - MAX VALUE POSSIBLE FOR IN-GAME DEFENSE AT EACH POSITION.
  - GIVEN TO PLAYER IN 100TH PERCENTILE IN THAT POSITION FOR TZR.
"""
POSITION_DEFENSE_RANGE = {
    '2000': {
        'C': 12.0,
        '1B': 2.0,
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
        'C': 12.0,
        '1B': 2.0,
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
        '1B': 2.0,
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
        '1B': 2.0,
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
        '1B': 2.0,
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
    '2005': {
        'CA': 12.0,
        '1B': 2.0,
        '2B': 5.0,
        '3B': 4.0,
        'SS': 5.0,
        'LF': 2.0,
        'CF': 3.0,
        'RF': 2.0,
        'OF': 2.0,
        'LF/RF': 2.0,
        'DH': 0
    }
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
        'min': 9.0,
        'max': 10.3
    },
    '2004': {
        'min': 9.0,
        'max': 10.3
    },
    '2005': {
        'min': 9.0,
        'max': 10.3
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
        'max': 7.1
    },
    '2004': {
        'min': 5.9,
        'max': 7.1
    },
    '2005': {
        'min': 5.9,
        'max': 7.1
    }
}
TEST_COMMAND_RANGE_PITCHER = {
    '2000': {
        'min': 3.0,
        'max': 4.0
    },
    '2001': {
        'min': 3.0,
        'max': 4.0
    },
    '2002': {
        'min': 3.0,
        'max': 4.2
    },
    '2003': {
        'min': 3.0,
        'max': 4.2
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
        'min': 15.0,
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
        'min': 15.9,
        'max': 17.1
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

""" COORDINATES FOR IMAGE COMPONENTS """
IMAGE_LOCATIONS = {
    'team_logo': {
        '2000': (400,362),
        '2001': (26,528),
        '2002': (8,460),
        '2003': (393,358),
        '2004': (387,480),
        '2005': (387,480),
    },
    'player_name': {
        '2000': (50,0),
        '2001': (35,0),
        '2002': (425,0),
        '2003': (455,0),
        '2004': (92,535),
        '2005': (92,535),
    },
    'chart': {
        '2000p': (327,450),
        '2000h': (327,444),
        '2001p': (327,450),
        '2001h': (327,444),
        '2002': (316,535),
        '2003': (327,511),
        '2004': (0,593),
        '2005': (0,593),
    },
    'metadata': {
        '2000': (0,0),
        '2001': (0,0),
        '2002': (270,535),
        '2003': (275,510),
        '2004': (94,570),
        '2005': (94,570),
    },
    'set': {
        '2000': (50,672),
        '2001': (50,672),
        '2002': (23,620),
        '2003': (31,595),
        '2004': (448,637),
        '2005': (448,637),
    },
    'number': {
        '2003': (56,595),
        '2004': (407,637),
        '2005': (407,637),
    },
    'super_season': {
        '2000': (400,345),
        '2001': (26,528),
        '2002': (15,371),
        '2003': (347,262),
        '2004': (357,388),
        '2005': (357,388),
    }
}

""" LIST OF ICON IMAGE COORDINATES FOR EACH ICON INDEX """
ICON_LOCATIONS = {
    '2003': [(335,635), (335,610), (310,635), (310,610)],
    '2004': [(350,565), (375,565), (400,565), (425,565)],
    '2005': [(350,565), (375,565), (400,565), (425,565)],
}

""" WIDTH AND HEIGHT TUPLES FOR EACH IMAGE COMPONENT """
IMAGE_SIZES = {
    'team_logo': {
        '2000': (75,75),
        '2001': (85,85),
        '2002': (150,150),
        '2003': (90,90),
        '2004': (85,85),
        '2005': (85,85),
    },
    'player_name': {
        '2000': (1100, 100),
        '2001': (515, 100),
        '2002': (465, 100),
        '2003': (1100, 100),
        '2004': (300, 100),
        '2005': (300, 100),
    },
    'super_season': {
        '2000': (91,140),
        '2001': (91,140),
        '2002': (156,240),
        '2003': (130,200),
        '2004': (113,174),
        '2005': (113,174),
    }
}

""" WIDTH AND HEIGHT TUPLES FOR EACH TEXT IMAGE COMPONENT """
TEXT_SIZES = {
    'chart': {
        '2000': 48,
        '2001': 48,
        '2002': 39,
        '2003': 48,
        '2004': 48,
        '2005': 48
    },
    'chart_spacing': {
        '2000': 22,
        '2001': 22,
        '2002': 18,
        '2003': 19,
        '2004': 25,
        '2005': 25
    },
}
