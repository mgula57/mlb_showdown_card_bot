![Image](./static/interface/ShowdownLogo.png)
# Showdown Bot

[Showdown Bot](https://showdownbot.com) is the simplest way of creating custom MLB Showdown cards. Simply enter a player's **name**, **season**, and **image**. The Showdown Bot takes care of the rest. 

![](./static/interface/Example.gif)

----


## Table of Contents
* [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
* [How it Works](#how-it-works)
    * [Player Identification](#player-identification)
    * [Gather Player Data](#gather-player-data)
    * [Convert to MLB Showdown Card](#convert-to-mlb-showdown-card)
* [Card Methodology](#card-methodology)
    * [Creating a Chart](#creating-a-chart)
    * [Defense](#defense)
    * [Speed](#speed)
    * [Icons](#icons)
    * [Points](#points)
* [Contact the Dev](#contact-the-dev)

----

## Getting Started

### Prerequisites
* [Python3](https://www.python.org/downloads/)

* (Optional) [pyenv](https://github.com/pyenv/pyenv) or [virtualenv](https://virtualenv.pypa.io/en/latest/)

### Installation

MLB Showdown Bot is available on PyPi

```sh
pip install mlb-showdown-bot
```

MLB Showdown Bot can be run directly from the CLI

```sh
showdownbot --name "Mike Piazza" --year 1997 --context 2001
```

Example Python use:

```python
from mlb_showdown_bot.showdown_player_card_generator import ShowdownPlayerCardGenerator
from mlb_showdown_bot.baseball_ref_scraper import BaseballReferenceScraper

name = 'Mike Piazza'
year = '1997'

# GET PLAYER DATA
scraper = BaseballReferenceScraper(name=name,year=year)
statline = scraper.player_statline()

# CREATE SHOWDOWN CARD 
showdown = ShowdownPlayerCardGenerator(
    name=name,
    year=year,
    stats=statline,
    context='2001',
    print_to_cli=True
)

# CREATE SHOWDOWN CARD IMAGE
showdown.player_image(show=True)
```

----


## How it Works

### Player Identification

At minimum, the bot takes a player's NAME and SEASON as inputs. The first step is identifying which player the user is trying to create a card for. Because there have been around 20,000 unique players in the history of the MLB, there are cases of multiple players sharing the same name (ex: Frank Thomas _(1951-1966)_ and Frank Thomas _(1990-2008)_).

To solve for this, the bot first searches the phrase **"baseball reference {name} {year}"**. (Ex: "baseball reference frank thomas 1994"). Using Google's indexing algorithm, the bot chooses the first search result and derives the player's unique baseball reference id from it. 

![Image](./static/interface/GoogleSearch.png)

### Gather Player Data

The bot uses [Baseball Reference](https://www.baseball-reference.com) as it's source for player data. Baseball Reference stores statistics for all of the ~20,000 players to make an appearance in the big leagues. 

Stats are extracted from the the baseball reference page for the player id selected in the previous step. Stats like batting average, home runs, and total zone runs (tzr) are extracted only for the chosen season. For pitchers, opponent batting results are used (ex: batting average against). 

If the selected season occured after 2015, sprint speed is also extracted from [Baseball Savant](https://baseballsavant.mlb.com/sprint_speed_leaderboard). A player's average sprint speed is used to determine in-game SPEED.

### Convert to MLB Showdown Card

The stats scraped in the previous step are used as inputs to determine the player's MLB Showdown card for the selected season. The player's in-game abilities are derived using the probability of outcome for each result on an MLB Showdown chart. More about that process is detailed below in the [Card Methodology](#card-methodology) section.

To create the card image, the [Pillow](https://pillow.readthedocs.io/en/stable/) library is leveraged to dynamically create the final jpg. The user can add optional enhancements like selecting an image and adding _Super Season_ or _Cooperstown Collection_ graphics.

----


## Card Methodology


### Creating a Chart

##### _**NOTE: A player's ONBASE (hitter) or CONTROL (pitcher) are referred to in this repository as COMMAND**._ 

The following steps are used to select the most accurate MLB Showdown card stats for a player:

1. Calculate **Onbase Pct** for each possible **Command/Out** combination.
2. Produce a chart for each **Command/Out** combination using the player's real life statline.
3. Choose the most accurate chart + **Command/Out** combination by comparing projected Showdown statline to real life statline.

Each of these steps work by a using baseline opponent to project in-game outcomes. A baseline opponent represents the approximate average pitcher or hitter a player would face in-game. The baseline stats are represented by a dictionary that includes **Command**, **Outs**, and number of chart results for each category (SO, BB, HR, etc). Baseline opponents differ for each MLB Showdown set. 


###### _Example baseline pitcher for 2001 set. **Note that all weight categories may not add up to 20 perfectly._
    
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
    }

These baseline opponents are vital to determining the final output of the player card. Adjusting these values will change which chart the bot decides is the most accurate. Because the actual baselines used to create the original sets are unknown, these are estimations based on set averages and testing. The goal is to find the baseline weights that most closely resemble the original sets from 2000-2005.

### **Command/Out --> Onbase Pct**

For each set, a static list of possible **Command/Out** combinations is defined for each player type (Hitter, Pitcher) in the [showdown constants](https://github.com/mgula57/mlb_showdown_card_bot/blob/master/mlb_showdown/showdown_constants.py) file. This list is used to generate the expected **Onbase Pct** for each combination using the baseline described above as the opponent. The following formula is used: 

`P(My Advantage) * P(Walk Or Hit on My Chart) + P(Opponent Advantage) * P(Walk Or Hit on Opponent's Chart)`

Only the **Command/Out** combinations that are closest to the player's real life onbase pct are further processed. This is for efficiency and greater accuracy. 

### Generating Player Chart

Now that a list of the most accurate **Command/Out** combinations (in terms of onbase pct) has been generated, a player's full in-game chart can be produced for each combination.

A player's chart is generated by populating each result category.

* Pitcher: _(PU, SO, GB, FB, BB, 1B, 2B, HR)_
* Hitters: _(SO, GB, FB, BB, 1B, 1B+, 2B, 3B, HR)_

The number of results (out of 20 slots) assigned to each category are calculated using this formula:

`(category_real_life_results_per_400_pa - (baseline_opponent_advantages_per_20_rolls * baseline_opponent_category_results)) / my_advantages_per_20_rolls`

**Important caveats:** 

* Stats are normalized to 400 Plate Appearances to mirror the 400 possible showdown roll combinations (_20 (Pitch Roll) * 20 (Swing Roll)_).
* FB, GB, PU are limited to OUT constraints. They use a different formula involving **Ground/Air Out Ratio** and **Infield FB Pct**.
* 1B+ is determined by dividing stolen bases per 400 PA by 10 _(Should be changed to be more dynamic in the future)_.
* 1B is filled with the slots remaining after all other categories are populated.

### Selecting Most Accurate Chart

Now that a chart has been generated for each **Command/Out** combination, the bot has all the required datapoints needed to determine accuracy. 

The player's **Command** and chart values are used to estimate the player's _in-game_ statline for 400 Plate Appearances. That statline is then compared to the player's _real life_ statline per 400 Plate Appearances. Some stat categories are given more weight than others (ex: _Batting Avg_ accuracy is weighted more heavily than _2B_ accuracy). _Both real and in-game statlines are displayed in website and CLI outputs._

**The chart with the highest aggregate accuracy is chosen as the final chart returned by the bot.**

To display one of the other chart outputs, add the optional **offset** argument. It allows the user to use any of the other charts from the Top 5 most accurate list. Use the `--offset` argument if in the CLI or choose an offset > 0 in the _More Options_ section of the website.

### **Defense**

#### _Hitters_
Each player can have a maximum of **2 positions**. For a position to qualify, the player has to make at least **10 appearances** at that position in the given season. The positions are then limited to the top 2 by number of appearances. 

In-game defensive ratings are calculated based on either Total Zone Rating (tzr), Defensive Runs Saved (drs), or Defensive Wins Above Replacement (dWAR). The bot will choose which metric to use depending on the year:

- 1870-1953: dWAR
- 1953-2002: TZR
- 2003-Pres: DRS

All these metrics work by comparing a certain player to the average replacement at that position (0). For example a +10 TZR is an above average rating, while a -7 TZR is below average.

The player's in-game rating is calculated with a percentile within a range. The player's in-game rating is calculated based on that percentile multiplied by the highest rating for each position (Ex: **3B: +4**, **SS: +5**, **LF/RF: +2**).

Ex: David Wright 2007 (+12 DRS)
* 3B Rating = Percentile * 3B In-Game Max  
* 3B Rating = 0.8 * 4
* 3B Rating = 3.2
* 3B Rating = +3


#### _Pitchers_
Pitchers fall under the following categories
1. STARTER: >65% of pitcher's appearances were starts
2. RELIEVER: <=65 % of pitcher's appearances were in relief
3. CLOSER: pitcher had at least 10 saves

### **Speed**

In-game SPEED is calculated differently depending on the year. 
* If the year is AFTER 2015, SPRINT SPEED is used. 
* If the year is BEFORE or ON 2015, STOLEN BASES (per 650 PA) is used.

Either SPRINT SPEED or STOLEN BASES is then converted to a percentile based off a range (the same way that defense is calculated). That percentile is then multiplied by the maximum in-game speed.

For example, the range of SPRINT SPEED is from 23 ft/sec to 31 ft/sec. If a player's SPRINT SPEED was 27ft/sec, they are in the 50th percentile (0.5). If the maximum in-game speed was 25, then this player's in-game SPEED is equal to 25 * 0.5, which rounds to **13**.


_** Pitchers are automatically given a SPEED of 10._


### **Icons**

Icons were a feature introduced in 2003 MLB Showdown sets. 

This is the list of available icons and how a player is eligible:

_** Some of these thresholds are slightly different than the original game._

* **SS**: Won Silver Slugger Award.
* **GG**: Won Gold Glove Award.
* **V**: Won AL or NL Most Valuable Player Award.
* **CY**: Won AL or NL CY Young Award.
* **R**: Selected season was player's first year in MLB.
* **RY**: Won AL or NL Rookie of the Year Award.
* **20**: Won 20 or more games as a Pitcher.
* **K**: Struck out at least 215 batters.
* **HR**: Hit at least 40 Home Runs.
* **SB**: Stole at least 40 bases.
* **RP**: Led AL or NL in Saves.

### **Points**

A player's point value is calculated by summing up a player's value provided in the following categories:

_Hitters_
* Onbase Pct
* Batting Avg
* Slugging Pct
* Defense (Avg Across Positions)
* Speed
* Home Runs

_Pitchers_
* Onbase Pct Against
* Batting Avg Against
* Slugging Pct Against
* Innings Pitched

A player's point value in each category is calculated by multiplying the WEIGHT given to the category by the PERCENTILE the player placed in. 

The WEIGHT is the number of points provided if the player achieves the 100th percentile in that category. The percentile is calculated by taking difference between the player's stat and minimum values for a category, and dividing it by the difference between maximum and minimum values assigned to the category. The WEIGHT represents how many points a player will receive if they are in the 100th percentile in the category. _NOTE: WEIGHTS change across sets._

Ex: **_Mike Yastrzemski 2019 (2000 Set)_**
```
Points (OBP) = WEIGHT * PERCENTILE
             = 250 * (0.330 - 0.250) / (0.450 - 0.250)
             = 250 * 0.4
             = 100 pts.
```
##### _Note: Pitchers have some categories (ex: BAA) where is percentile is reversed (1-percentile)_

This calculation is performed for each category. The categorical point values are summed into the player's final total point value. 

There are additional weights/logic applied across the different sets to try to match to the original WOTC sets. 
Including:

- **Allow Negatives**: If True, allows a player to be penalized in the negative for a bad category. For example if a player is under the threshold defined for OBP, they will receive negative PTS for OBP. If False, player gets +0 PTS for that category if below threshold.
- **Normalize Towards Median**: If True, a player over a certain value will get overall points reduced in order to keep a "Bell Curve" of point distribution. Scaler increases as point value above set value increases.

----
## Contact the Dev

You can reach out to the developer of MLB Showdown Bot through email mlbshowdownbot@gmail.com

Follow MLB Showdown Bot Twitter for updates and daily card posts!

[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/mlbshowdownbot.svg?style=social&label=Follow%20%40mlbshowdownbot)](https://twitter.com/mlbshowdownbot)