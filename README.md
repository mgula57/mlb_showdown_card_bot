![Image](./static/interface/ShowdownLogo.png)
# Showdown Bot

[Showdown Bot](https://showdownbot.com) is the most simple way of creating custom MLB Showdown cards. Simply enter a player's **name**, **season**, and **image**. The Showdown Bot takes care of the rest. 

(Picture of Web app)

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
    * [Defense](#defense)
    * [Speed](#speed)
    * [Icons](#icons)
    * [Onbase/Control](#onbase/control)
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

### Gather Player Data

### Convert to MLB Showdown Card

----


## Card Methodology

### **Defense**

#### _**Hitters**_
Each player can have a maximum of **2 positions**. For a position to qualify, the player has to make at least **10 appearances** at that position in the given season. The positions are then limited to the top 2 by number of appearances. 

In-game defensive ratings are calculated based on Total Zone Rating (tzr). TZR is a fielding metric used to compare one player's defensive impact at a position to the average (0 TZR). So a +10 TZR is an above average rating, while a -7 TZR is below average.

The player's in-game rating is calculated with a TZR percentile, using a minimum of -18 to a maximum of +18. The player's in-game rating is calculated based on that percentile multiplied by the highest rating for each position (Ex: **3B: +4**, **SS: +5**, **LF/RF: +2**).

Ex: David Wright 2007 (+4 TZR)
* 3B Rating = Percentile * 3B In-Game Max  
* 3B Rating = 0.61 * 4
* 3B Rating = 2.44
* 3B Rating = +2


#### _**Pitchers**_
Pitchers fall under the following categories
1. STARTER - >65% of pitcher's appearances were starts
2. RELIEVER - <=65 % of pitcher's appearances were in relief
3. CLOSER - pitcher had at least 10 saves

### **Speed**

In-game SPEED is calculated differently depending on the year. 
* If the year is AFTER 2015, sprint speed is used. 
* If the year is BEFORE or ON 2015, stolen bases per 650 PA is used.

_** Pitchers are automatically given a SPEED of 10._


### **Icons**

Icons were a feature introduced in 2003 MLB Showdown sets. 

This is the list of available icons and how a player is eligible:

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

### Onbase/Control


----
## Contact the Dev