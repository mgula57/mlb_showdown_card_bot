# Showdown Bot Patch Notes

What's new in each Showdown Bot release, newest first.

## 4.4 Release — Team Builder & Season Simulator
_Unreleased_

This release focuses on the brand new Team Builder, full-season simulations for any MLB season, a revamped live game experience, and upgrades to the Custom Card Builder and Explore.

### Team Builder
Draft your own MLB Showdown roster from any era, then put it to the test in a simulated season.
- Build a roster from any era with live points tracking and a running draft history
- `Autofill` completes your lineup, rotation, and bullpen in one click, favoring players with a full season of stats
- `Fits my roster` toggle hides cards you can't afford or don't have a spot for
- Set your lineup and depth chart on an interactive field view
- Set manager tendencies for your club, like how quickly to pull a tired starter
- Browse, like, and copy community teams and curated all-time teams from the `Browse` tab
- Your teams are organized in `My Teams`, including teams copied from others
- Works on mobile, with a slide-over panel for drafting

### Challenges
Rotating scenarios that test how well you can build and manage a team.
- New `Challenges` tab with limited-time scenarios, like hitting a target win total
- Each challenge sets its own rules, such as a points cap, eligible players, and roster minimums
- Leaderboards show the best managers for each challenge

### Season Simulator
Pick any MLB season on the `Seasons` page and hit `Simulate this season` to play it out start to finish.
- A brand new engine rolls the full 162-game schedule, plus the postseason
- `Take over a club` swaps one of your Team Builder teams in for a real club
- Start from today's real standings, or skip straight to the real postseason
- Optional injuries, trade deadline moves, and handedness matchups for extra realism
- Watch a live progress view while the season plays out
- Results include standings, a win percentage chart, league leaders, `Awards`, `Transactions`, and `League Stats`
- Compare how simulated stats stack up against what really happened
- Awards now include MVP, Cy Young, Rookie of the Year, Gold Glove, Silver Slugger, series MVPs, and pitching Triple Crowns
- New PTS+ rating shows how a team's card points compare to the rest of the league
- Past sims are saved in the `Sims` tab so you can revisit them
- A built-in guide explains how the simulator works

### Live Games
Follow any game pitch by pitch, or take over and let Showdown decide the rest.
- Replay games with play, pause, fast-forward, rewind, and adjustable playback speed
- Take over a game mid-way through and simulate the rest with Showdown cards
- Results stay hidden during a replay so you can play through it without spoilers
- Box scores now include home runs and pitcher wins, losses, and saves

### Seasons
- New `Awards` page for every past season: MVP, Cy Young, Gold Glove, Silver Slugger, and more
- Revamped team pages for browsing historical rosters, with year filters and all-time teams
- Standings now show each team's historical card points
- The game schedule is grouped by month and refreshes automatically

### Custom Card Builder
- New option to hide the split or date text on a card
- New option to pull small sample sizes toward replacement level for more realistic stats

### Explore
- Flip between card sets right from a card's detail view
- New filters for card sets, and a redesigned browse menu

### Bug Fixes
- Fixed player search for names with a period (e.g. J.D. Martinez)
- Fixed players being counted twice in some simulated stat lines
- Fixed two-way players on historical rosters
- Fixed older teams not appearing due to changed team abbreviations
- Fixed sign-in sending you back to the home page
- Fixed drafting on mobile touch screens

---

## 4.3 Release — 2026 All-Star Game
_Released 2026-07-16 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v4.3)_

Adds 2026 All-Star Game design, available via the All-Star Game edition.

### Other Updates

- Add high-res versions of all historical all star games
- Add more variety to 2026+ pitcher charts
- Update 2026 avg stats
- Update side menu icons

---

## 4.2 Release — User Accounts
_Released 2026-06-16 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v4.2)_

Users can now sign up for a free Showdown Bot login to save settings, card history/images, and more across devices. Card Builder has been redesigned with Savant style percentiles and all new interactive breakdowns.

### Card Builder
- Sign in to save your custom card images
- Browse/search your creations in Gallery view
  - Combines multiple edits of a player + year into "stacks" for easier change tracking
- All surrounding card detail tables/graphs have been redesigned
  - Card vs Real: Add Savant style percentiles
  - Points Breakdown: Convert to bar chart
  - Chart Selection: Convert to bar chart, add KPI tiles
  - Baseline Opponent: Add chart representation
  - Outcome Probabilities: New breakdown that lets you quickly see card outcomes vs different Ctrl/Onbases or vs a specific Showdown Bot Card
  - WOTC Comps: Shows top WOTC cards that are most similar to your custom
- Add dedicated 'Showdown Style' selector that overrides the user's global default. Allows you to create cards across styles within the custom card editor without disrupting other tabs
- Change indexing for faster search

### Account Page
- Manage settings that apply across devices
- Sign-in with Google, Discord, or Email

### Explore
- 2026 Cards, updated daily
  - Shows WoW points trend to help you understand who's trending
- "Quick filter" presets available for all users
  - Current Season
  - Award Winners
  - HOF
- Create custom quick filter presets to quickly toggle to the cards you care about
- Improved sorting button
- Adjust width of Card Detail side window on desktop

### Home Page
- Add "Quick Nav" buttons on mobile for easier navigation to other tabs
- View recently created custom cards
- General spacing optimization

---

## 4.11 Release — 2026 Live Seasons
_Released 2026-04-22 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v4.11)_

This release focuses on Minor League card support, an enhanced live game companion, 2026 season tracking, and bug fixes stemming from the migration to MLB's API.

### Live Game Companion
The live game companion lets you follow any regular season game live using what you know best — MLB Showdown cards!
- Combines live MLB box score tracking with MLB Showdown cards
- Now uses 2026 cards that update live throughout the game
- Track which players rose or fell based on their performance
- Shows cards for the live pitcher vs. hitter matchup

### Season Tracking
Use the `Seasons` tab to follow standings, live games, rosters, and leaders with the context of MLB Showdown cards.
- Added a `Leaders` tab showing cards for live hitting and pitching leaders
- Updated the `Teams` tab to display live rosters and cards with PTS trends
- Added `Today's Games` on Showdown Bot's home page, letting users quickly view a banner of game box scores and WHIP/OPS leaders
- Improved load times

### MiLB Card Support
Added support for Minor League cards via the `League` dropdown in the _Customs_ tab.
- Supports all minor league stats available on MLB.com
- Some limitations apply compared to MLB data — see the README for details
- Coming soon:
  - MiLB team logos (currently shows a generic league logo)
  - Team/level filtering (e.g. AAA only)

### Bug Fixes
- Fixed handedness for pitchers with a different batting hand (MLB API only)
- Fixed player type overrides and two-way players (MLB API only)
- Enabled 2026 players in the search box

---

## 4.1 Release — Live WBC Content!
_Released 2026-03-10 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v4.1)_

The World Baseball Classic has arrived in Showdown Bot! This update adds several new WBC-themed features to celebrate the tournament.

### WBC-Themed Cards

You can now create World Baseball Classic cards for players participating in the tournament.
For 2026, WBC players from the following leagues are available:
- KBO
- NPB
- Minor Leagues
This allows you to see MLB Showdown cards for players in international or developmental leagues while they compete in the WBC.

### New Live WBC Tab
A brand new WBC tab has been added so you can follow the tournament in real time. From this tab you can:
- Track live games
- Check tournament standings
- Browse all WBC team rosters
- Search WBC cards across all countries

This update is designed to make it easier than ever to follow the WBC - using MLB Showdown cards!

---

## 4.01 Release — Home Page
_Released 2026-01-19 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v4.01)_

### Home Page
- New splash page to introduce users to Showdown Bot.
- **How to Play** now explains the core game mechanics, helping bring Showdown to new audiences.
- **Card of the Day:** A randomly selected card that rotates daily.
- **Trends:** Highlights trending cards from the past two weeks, most-created cards of all time, and curated spotlights tied to recent events.
- **FAQ:** Covers the most common user questions.

### Explore
- WOTC cards have been added to Explore.
  - Filter across all attributes from the original WOTC cards.
  - See which WOTC cards have the highest PTS value when processed through the Bot.
  - Errata cards are flagged, along with notes for special cases.
  - Real-life stats are included for context and tailored to expansions and unique scenarios (e.g., Mark McGwire 2001).
  - Users can now generate card images using original WOTC stats.
- When switching sets on desktop with Card Details open, the Bot will automatically reprocess the selected card in the new set.

#### Filters
- Updated UI.
- Added Hall of Fame (HOF) filter.

### Custom Cards
- Improved multi-year and career card generation for faster speed and greater reliability.
- Added WOTC All-Star Game templates (2002 Tan template and 2004 “Lines” design).

### Formula Updates
- Multi-season defense now uses a weighted average instead of a median.
- Reduced the number of small-sample 1B+2 defensive ratings by requiring at least 90 games played at 1B.

### Backend
- Migrated to a new database backend.
- Optimized data models to support future features and scaling.
- Added enhanced logging to better track usage patterns.
- Upgraded frontend packages.
- Laid the groundwork to remove dependency on Baseball-Reference for the 2026 season.

---

## 4.0 Release — New Frontend
_Released 2025-10-06 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v4.0.0)_

**Showdown Bot 4.0** introduces a complete visual and structural overhaul, making it easier than ever to explore, build, and customize your favorite cards and players.

### 🚀 Highlights
- Modern frontend framework for a faster, smoother experience
- Brand-new **Explore 2.0** with clean card previews and advanced filters
- Smarter, contextual **Custom Card Builder** search
- Collapsible sections and split-screen layout for easier customization

### Frontend
- Rebuilt on a modern framework that works seamlessly across all devices
- New side navigation for quick switching between **Explore** and **Customize** modes
- Consistent design language across all tabs
- Choose your Showdown set (e.g., *2001, 2005, Expanded*) once in the top-right — it applies across all tabs

### Explore 2.0
- Completely redesigned and now runs natively within Showdown Bot
- Clean, easy-to-read card previews matching **Classic** and **Expanded** designs
- Click any card to view the same detailed view used in the Custom Card Builder
- Filter by **real-world attributes** (e.g., PA, IP, team, league) or **Showdown stats** (e.g., Control/On-base, Speed)
- Quick search to instantly find players by name

### Custom Card Builder
- **Smarter Search:** Contextual search helps you find players faster, complete with player details and ranked results
- **Organized Sections:** Inputs are grouped into collapsible sections, making it easier to focus on the settings you care about; your preferences are saved across sessions
- **Split-Screen Layout:** On desktop, inputs and outputs are displayed side-by-side for a streamlined editing experience

---

## 3.9.5 Release — 2025 ASG Cards!
_Released 2025-07-15 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v3.9.5)_

### 2025 All Star Edition

Adds new custom designed all star game cards. Select `All-Star Game` edition for any 2025 card to try it yourself!

---

## 3.9.4 Release — Live Cards!
_Released 2025-05-26 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v3.9.4)_

### Live Cards

Using MLB's Realtime Stats API, Showdown Bot now has the ability to update cards in realtime. The Bot will display current game information and player statlines as well as the change in their card's points vs before the game.

### Player Trends

2 Graphs have been added to display _Career_ Trends and _In-Season_ Card Evolution. Users can quickly see weekly change in points next to the player's name. In-Season only available for 2020+ seasons, historical seasons will be backfilled in the coming weeks.

### Shuffle Button Filters

Shuffle Button now dynamically reduces sample based on user selections
- Year
  - Filters to only that season. Works with multiple season as well (ex: 2023-2024)
- Era
  - Filters to only seasons within era
- Edition (see below for requirements)
  - Cooperstown Collection: Only players in the Hall of Fame
  - Super Season: Must either be an all star or meet bWAR requirement.
  - All Star Game: Must be an all star
  - Rookie Season: Must be a rookie

The loading indicator will display to the user what the parameters of their shuffle are.

### Defense

An analysis was conducted in order to ensure defense is consistently handled across eras and shortened seasons.
- All defense is normalized to be per 150 games
  - Boosts defense for shortened seasons like 1994
- Implement slight tweaks to increase accuracy vs original WOTC
- Update small sample sizes and mid-season defense calculations to be more flexible

### Adjustable Outer Glow

Users can adjust the glow or shadow around players (where applicable). Options are 2x or 3x the default glow/shadow.

### UI Updates

- Add loading indicator to top right, allowing user to make edits for next card while processing
- Change default/blank image to match set's template
- Updated Showdown Bot Logo
- Misc Small Tweaks and Optimizations

### Team Logos

- Add 75+ historical logos
- Correct 15+ logo year ranges

### Set Specific Changes

2000/2001
- Fix stat highlights being cut off when expansion is shown

2002
- Update Super Season Text Font

2003
- Update Super Season Text Font

2004/2005
- Change Super Season Ellipse Locations
- Update Super Season Text Font

CLASSIC/EXPANDED
- Fix nationality cards not showing chart gradient

### Explore
- Add ability to filter players by whether they have an automated image

### Bug Fixes
- Use Bing instead of Google for Indexing
  - Google now blocks all Bot requests
  - Helps reduce errors on Rookies

### Code Enhancements
- Increase bulk card creation speed
- Store historical game log and postseason data for quicker access

---

## 3.9.3 Release — Quality of Life Improvements
_Released 2024-11-25 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v3.9.3)_

This update includes a few minor updates that improve the user experience and card creation process

- Auto populate form inputs based on last card created on page load
- Redesign stat highlight visuals to be customized per set
- Remove constraints on stat highlight categories and add ranking system to prioritize
- Auto fill width of highlights container with player stats
- Programmatically apply glow and drop shadow on images
- Make name font size adjustment more dynamic
- Order defensive positions based on games played
- Fix Multi-Year cards for players that skipped years
- Handle new pitcher enhanced tables on bref
- Use weighted avg for cross year OPS based on games
- Handle lighter colors on CLASSIC/EXPANDED Super Season text

---

## 3.9.2 Release — Formula Enhancements
_Released 2024-10-29 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v3.9.2)_

### Formula Updates

**Dynamic Command/Out Selection**
  - Remove hard coded list of command/out combinations, allowing the possibility for any command/out.
  - Manage frequency of "Outlier" charts by slightly reducing their accuracy
    - "Boost" mechanism will nullify this reduction if accuracy > 99%
  - Update match accuracy weights between `obp`, `slg`, and `ops`
  - Add `Command Estimation` category

**Year to Year Automatic Adjustments**
  - Cards now use year to year averages instead of era wide averages to buff/nerf cards to replicate that year's run scoring environment
  - Increases accuracy of cards in a simulation environment
  - Reduces maintenance of 3500+ lines of code

**Add Post-calculation Chart Adjustments**
   - After the first pass at creating a chart, the Bot will check projections and see if it is under/overrating the card due to rounding.
   - If it detects the ability to make SLG/OPS more accurate, it will identify the SLG category that is least accurate between 2B/3B/HR and will add or remove a value.

**Stronger Expanded Pitching Charts**
  - WOTC weights result in too much offense when simulating an entire season
  - Make baseline opponent batter slightly stronger (causing better pitcher charts) to get accurate simulation results
  - Will usually result in 1+ Out or Tier difference for pitchers

**Chart Calculations**
  - Improve allocation logic for 21+ Expanded Slots
    - Slightly reduce slot values for 1-20 slots
      - Ex: Instead of 1.0, use 0.975
    - Assign remaining slot values to 21+ results
      - Example:
         - If 1-20 slots are worth 0.975 each the total from 1-20 is 19.5
         - The remaining 0.5 slots would be allocated across 21-30 slots
    - Benefits:
      - Creates better estimations vs real stat
      - Allows for more chart variety
      - Accounts for strategy card use
  - Change the way chart values are populated
    - Add `Pct` fill method for outs (in some sets). Distributes chart values by multiplying total chart slots by real percent of total. Ignores opponent chart.
      - Ex: 30% of a hitter's real life outs happen via groundballs. If the player has 6 outs on their chart, 1.8 (rounded to 2) would be assigned `GB`.
  - Update baseline opponents for each set

**Speed Updates**
  - For players post 2016 with a SB/400 PA of 21+, change speed metric weighting from `75% SB / 25 % SPRINT SPEED` to `80% SB / 20% SPRINT SPEED`
  - Also change SB Speed requirement from 21 to 19.

**Points Updates**
  - Increase Points consistency and accuracy vs WOTC
    - Remove WOTC point outliers from testing
  - Change points decay method from complicated exponential logic to linear
    - Ex: In some sets, points over 500 cost 75% of normal

**Defense Updates**
  - Cap small sample size defense
  - Give any player that played all 4 infield positions in a season `IF` eligibility
    - Add ability to get `IF+2`
  - Add LF/RF eligibility for all CF in CLASSIC/EXPANDED sets

**Misc**
  - Add mechanism to change baseline opponent between relievers and starters for some sets
  - Reduce Size of Team Logo for 2004/2005 sets
  - Fix issue with mid-season team overrides
  - Add games played to stat highlights

### Website
- Add more detailed breakdowns to website
    - `Diff` column on stats
    - `Percentile` column on points
    - `OPS` and `Notes` on chart
- Explore Updates
  - Add 2024 stats
  - Add filter to see "Outlier" charts
  - Add ability to search specific Command Out combinations (ex: '5-17')
  - Fix filtering of Icons
- Fix fonts not showing correctly on Windows
- Update padding on smaller screen sizes
