![Image](./static/interface/ShowdownLogo.png)
# Showdown Bot

[Showdown Bot](https://showdownbot.com) is the most simple way of creating custom MLB Showdown cards. Simply enter a player's **name**, **season**, and **image**. The Showdown Bot takes care of the rest. 

![](./static/interface/Example.gif)

----


## Table of Contents
* [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
    * [Running Locally](#running-locally)
* [How it Works](#how-it-works)
    * [Player Identification](#player-identification)
    * [Gather Player Data](#get-player-data)
    * [Convert to MLB Showdown Card](#convert-to-mlb-showdown-card)
* [Card Methodology](#card-methodology)
    * [Creating a Chart](#creating-a-chart)
    * [Defense](#defense)
    * [Speed](#speed)
    * [Icons](#icons)
* [Contact the Dev](#contact-the-dev)

----

## Getting Started

### Prerequisites
* [Python3](https://www.python.org/downloads/)

* (Optional) [pyenv](https://github.com/pyenv/pyenv) or [virtualenv](https://virtualenv.pypa.io/en/latest/)
### Installation

1. Clone the repo
```sh
git clone https://github.com/mgula57/mlb_showdown_card_bot.git
```
2. Install dependencies
```sh
pip install -r requirements.txt
```

### Running Locally

#### Run Web App
```sh
python app.py
```
#### Run through CLI
```sh 
python main.py -n "Mike Trout" -c 2004 -y 2020 
```

----


## How it Works

### Player Identification

At minimum, the bot takes a player's NAME and SEASON as inputs. The first step is identifying which player the user is trying to create a card for. Because there has been around 20,000 unique players in the history of the MLB, there are cases of multiple players sharing the same name (ex: Frank Thomas _(1951-1966)_ and Frank Thomas _(1990-2008)_).

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

1. Calculate ONBASE % for each possible COMMAND/OUT combination.
2. Produce CHARTS for each COMMAND/OUT combination using the player's real life statline.
3. Choose the most accurate CHART + COMMAND/OUT combination by comparing projected Showdown statline to real life statline.

Each of these steps work by using baseline opponents to project in-game outcomes. A baseline opponent represents the approximate average pitcher or hitter a player would face in-game. The baseline stats are represented by a dictionary that includes COMMAND, OUTS, and number of CHART results for each category (SO, BB, HR, etc). Baseline opponents differ for each MLB Showdown set. 

###### _Example baseline pitcher for 2001 set_
    
    '2001': {
        'command': 3.35,
        'outs': 15.97,
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

These baseline opponents are vital to determining the final output of the player card. Adjusting these values will change which chart the bot decides is the most accurate.

### **Defense**

#### _Hitters_
Each player can have a maximum of **2 positions**. For a position to qualify, the player has to make at least **10 appearances** at that position in the given season. The positions are then limited to the top 2 by number of appearances. 

In-game defensive ratings are calculated based on Total Zone Rating (tzr). TZR is a fielding metric used to compare one player's defensive impact at a position to the average (0 TZR). So a +10 TZR is an above average rating, while a -7 TZR is below average.

The player's in-game rating is calculated with a TZR percentile, using a minimum of -18 to a maximum of +18. The player's in-game rating is calculated based on that percentile multiplied by the highest rating for each position (Ex: **3B: +4**, **SS: +5**, **LF/RF: +2**).

Ex: David Wright 2007 (+4 TZR)
* 3B Rating = Percentile * 3B In-Game Max  
* 3B Rating = 0.61 * 4
* 3B Rating = 2.44
* 3B Rating = +2


#### _Pitchers_
Pitchers fall under the following categories
1. STARTER - >65% of pitcher's appearances were starts
2. RELIEVER - <=65 % of pitcher's appearances were in relief
3. CLOSER - pitcher had at least 10 saves

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
* **RY**: Won AL or NL Rookie of the Year Award.
* **20**: Won 20 or more games as a Pitcher.
* **K**: Struck out at least 215 batters.
* **HR**: Hit at least 40 Home Runs.
* **SB**: Stole at least 40 bases.

_** TODO: ADD RP and R Icons_

----
## Contact the Dev