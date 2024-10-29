
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
        },
        "2023": {
            "Hitter": 0.319,
            "Pitcher": 0.310
        },
        "2024": {
            "Hitter": 0.312,
            "Pitcher": 0.307
        },
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
        },
        "2023": {
            "Hitter": 0.318,
            "Pitcher": 0.311
        },
        "2024": {
            "Hitter": 0.313,
            "Pitcher": 0.309
        },
    }
}

LEAGUE_AVG_PROJ_SLG = {
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
        },
        "2023": {
            "Hitter": 0.400,
            "Pitcher": 0.370
        },
        "2024": {
            "Hitter": 0.395,
            "Pitcher": 0.366
        },
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
        },
        "2023": {
            "Hitter": 0.410,
            "Pitcher": 0.375
        },
        "2024": {
            "Hitter": 0.403,
            "Pitcher": 0.370
        },
    }
}

LEAGUE_AVG_COMMAND = {
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
        },
        "2023": {
            "Hitter": 7.100,
            "Pitcher": 3.200
        },
        "2024": {
            "Hitter": 7.000,
            "Pitcher": 3.210
        },
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
        },
        "2023": {
            "Hitter": 9.300,
            "Pitcher": 3.120
        },
        "2024": {
            "Hitter": 9.290,
            "Pitcher": 3.150
        },
    }
}

FIP_CONSTANT = {
    2024: 3.255,
    2023: 3.255,
    2022: 3.112,
    2021: 3.17,
    2020: 3.191,
    2019: 3.214,
    2018: 3.16,
    2017: 3.158,
    2016: 3.147,
    2015: 3.134,
    2014: 3.132,
    2013: 3.048,
    2012: 3.094,
    2011: 3.025,
    2010: 3.078,
    2009: 3.097,
    2008: 3.132,
    2007: 3.24,
    2006: 3.147,
    2005: 3.02,
    2004: 3.049,
    2003: 3.032,
    2002: 2.962,
    2001: 3.049,
    2000: 3.134,
    1999: 3.134,
    1998: 3.139,
    1997: 3.109,
    1996: 3.172,
    1995: 3.103,
    1994: 3.131,
    1993: 2.988,
    1992: 2.783,
    1991: 2.856,
    1990: 2.808,
    1989: 2.763,
    1988: 2.769,
    1987: 2.871,
    1986: 2.771,
    1985: 2.684,
    1984: 2.768,
    1983: 2.755,
    1982: 2.717,
    1981: 2.6,
    1980: 2.752,
    1979: 2.732,
    1978: 2.585,
    1977: 2.738,
    1976: 2.633,
    1975: 2.587,
    1974: 2.578,
    1973: 2.565,
    1972: 2.399,
    1971: 2.451,
    1970: 2.638,
    1969: 2.509,
    1968: 2.385,
    1967: 2.539,
    1966: 2.554,
    1965: 2.517,
    1964: 2.605,
    1963: 2.479,
    1962: 2.617,
    1961: 2.574,
    1960: 2.527,
    1959: 2.543,
    1958: 2.475,
    1957: 2.456,
    1956: 2.369,
    1955: 2.368,
    1954: 2.398,
    1953: 2.591,
    1952: 2.391,
    1951: 2.479,
    1950: 2.584,
    1949: 2.511,
    1948: 2.754,
    1947: 2.669,
    1946: 2.579,
    1945: 2.69,
    1944: 2.674,
    1943: 2.654,
    1942: 2.471,
    1941: 2.669,
    1940: 2.878,
    1939: 2.979,
    1938: 3.049,
    1937: 3.2,
    1936: 3.314,
    1935: 3.182,
    1934: 3.181,
    1933: 2.9,
    1932: 3.009,
    1931: 3.136,
    1930: 3.488,
    1929: 3.229,
    1928: 3.027,
    1927: 2.989,
    1926: 3.028,
    1925: 3.333,
    1924: 3.148,
    1923: 3.038,
    1922: 3.15,
    1921: 3.136,
    1920: 2.803,
    1919: 2.486,
    1918: 2.229,
    1917: 2.261,
    1916: 2.315,
    1915: 2.409,
    1914: 2.436,
    1913: 2.556,
    1912: 2.849,
    1911: 2.768,
    1910: 2.322,
    1909: 2.215,
    1908: 2.101,
    1907: 2.178,
    1906: 2.366,
    1905: 2.522,
    1904: 2.418,
    1903: 2.755,
    1902: 2.665,
    1901: 2.924,
    1900: 2.827,
    1899: 2.935,
    1898: 2.766,
    1897: 3.323,
    1896: 3.425,
    1895: 3.727,
    1894: 3.929,
    1893: 3.374,
    1892: 2.53,
    1891: 2.679,
    1890: 2.968,
    1889: 3.08,
    1888: 2.659,
    1887: 3.277,
    1886: 3.101,
    1885: 2.881,
    1884: 3.269,
    1883: 3.256,
    1882: 2.764,
    1881: 2.688,
    1880: 2.533,
    1879: 2.739,
    1878: 2.536,
    1877: 2.839,
    1876: 2.233,
    1875: 2.37,
    1874: 2.808,
    1873: 2.932,
    1872: 3.508,
    1871: 3.58,
}