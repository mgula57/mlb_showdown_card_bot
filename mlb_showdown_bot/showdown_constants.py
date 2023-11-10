
# -------------------------------------------
# SHOWDOWN_CONSTANTS.PY
#   - FILE TO STORE ALL WEIGHTS / STATIC VALUES
#     NEEDED TO GENERATE PLAYER CARDS
# -------------------------------------------

"""
LEAGUE AVG PROJECTIONS
  - BASED ON 26 MAN ROSTERS PER YEAR
  - USED TO INFORM THE shOPS+ METRIC
"""

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
    'CLASSIC': {
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
    'EXPANDED': {
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
    'CLASSIC': {
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
    'EXPANDED': {
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
    'CLASSIC': {
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
    'EXPANDED': {
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
