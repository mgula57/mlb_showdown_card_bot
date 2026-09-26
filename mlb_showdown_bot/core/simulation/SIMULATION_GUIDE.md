# ⚾ How a season simulation actually works

This is a walkthrough of what happens when you click "simulate" on a full MLB
season (or a season challenge) in this app. It assumes you know how MLB Showdown itself plays —
charts, dice, on-base/advantage rolls — and walks through everything *around* that: how a season
gets built, how a single game gets played out, and all the smaller rules bolted on to make 162
games of simulated baseball feel like a real season instead of 162 identical coin flips.

---

## 🏗️ Part 1 — Building the season, before a single pitch is thrown

### 🃏 Step 1: Every player gets a card

Before anything
else, it loads a card for every player who appeared that season. These players are pulled down from an archive of historical MLB Showdown Cards, the same backend that drives the `Explore` page. If it's simming a season in progress, it will use the latest card available, snapshotted daily.

If the user is doing a takeover with their own team, it will load those cards as well. Optionally the player can
elect to **regress small sample sizes toward replacement level**, which combines small sample card actual stats 
with average replacement level stats to nerf those cards slightly.

### 📅 Step 2: The real schedule comes down

The season's actual game-by-game schedule is pulled from the MLB Stats API — same
matchups, same days, same home/away split as really happened that year.

If you're running a **rest-of-season projection** instead of a full season, this is where that
gets carved out: every club's real record as of today (or whatever date you picked) is loaded as
the *starting* record, and only the games after that date actually get simulated.

### 🔄 Step 3: Real Trades get queued (optional)

If trade-deadline moves are turned on, the sim looks at every player who really played for more
than one club that season and figures out which was his *first* club and which was his *last*.
Anyone who was clearly just a September call-up or a spring-training paper transaction (fewer than
about 10 real games on one end of the split) is pinned to a single club for the whole run instead —
that's not a real mid-season trade, so it doesn't get treated like one.

For everyone else, a trade is scheduled for that year's era-correct deadline date (mid-June before
1986, July 31 from then on). Once the trading deadline comes, the simulation will decide whether the contending team would actually make that trade again given their _simulated_ record.

For example: in real life, a last-place club sells off a good reliever at the deadline. But in this
particular simulated run, injuries and lucky rolls have that same club sitting only 5 games back
of a playoff spot — well within the "still contending" cutoff of 8 games. Because a club that close
to a playoff spot wouldn't actually be selling, the trade is cancelled for this run: the reliever
stays put on his original club for the rest of the season instead of moving.

*Planned for a future update:* right now the sim can only cancel a real trade that already
happened — it can't invent a brand-new one. The next step is letting the simulation generate
**organic trades that never occurred in real life** — a club that's simulating as a surprise seller
or buyer trading with another club in the same situation, based purely on how the simulated season
is actually playing out.

### 👥 Step 4: Rosters get built, position by position

Each club's 40-man roster is assembled from the cards that played for it that year — but not by
simply grabbing whoever's most valuable. Before any slot gets filled, every card is bucketed into a
**preferred tier** (real playing time at or above a minimum — e.g. plate appearances for hitters,
innings/starts for pitchers) and a **fallback tier** below that bar. The preferred tier is always
exhausted first — a part-timer in the fallback tier can only win a roster spot once no preferred-tier
player is left who's eligible for it. This prevents small sample size players with high points getting
too much playing time during the sim.

The active roster is filled one defensive position a time for each spot, the sim looks at every card 
that's eligible to play there — eligibility comes straight off the card itself, from whichever 
positions it actually earned real playing time at that season, not from anything the roster step 
re-measures — and takes the single most valuable one left (by overall Showdown point value, not innings, games, or fielding rating at that specific spot) before moving on to the next position. A backup catcher is a hard requirement no matter what — nobody else is allowed to quietly cover that job.

A reserve pool sits behind the active 26 as the on-deck pool for injuries and call-ups. Players
without enough real playing time to be a meaningful sample don't make either group.

### 🔁 Step 5: If it's a takeover, your team gets swapped in

A season-takeover team doesn't get its own new schedule — it's dropped directly into a real club's
slot, taking over that club's exact schedule, division, and opponents for the year. A takeover team 
skips the 40-man/injury system entirely — your lineup, rotation, and bullpen play exactly as you 
built them, with no auto-resting and no auto-swapping.

*Planned for a future update:* if the user adds a team of >= 30 players, it will apply injuries and call ups.

### 🩹 Step 6: Injury profiles get calibrated (optional)

If injuries are turned on, every player on a real roster gets a personal injury profile — but it's
not random. It's tuned so that a player's *simulated* expected missed time lines up with the gap
between what he actually played in real life and a healthy baseline for his role. A guy who played
158 of 162 games gets modeled as durable; a guy who missed half the year gets modeled as fragile.
A bench player or September call-up with a small sample doesn't get unfairly flagged as
"chronically hurt" just because his role gave him a low game count — the model discounts its
confidence until there's enough playing time to trust the comparison.

Every player carries at least a small floor of risk, and no matter how fragile a profile is, the
chance of landing on the IL in any single game is capped at 25%. Most injuries that do happen are
short (3-10 days); long, season-wrecking injuries are the rare exception on purpose.

---

## 📆 Part 2 — Playing the season, day by day

With the season built, the sim plays through the schedule one real game at a time, in
chronological order.

### ✅ Before each game: who's actually available today

**If the trade deadline has arrived** and a scheduled move hasn't fired yet, it fires now — the
scheduled players change teams, permanently, for the rest of the run. (If the "respect the
standings" option is on, a selling club that's still within about 8 games of a playoff spot at
deadline time gets to keep its player — the real trade is cancelled for that particular run,
because in the simulated world that club isn't actually selling.)

**Injuries are checked once per calendar day**, not once per game — so a doubleheader doesn't
double a player's chance of getting hurt that day. Any new IL placement finds a healthy
replacement from the reserve pool and returning players are activated when their stint is up.

**The lineup gets rebuilt from scratch.** There's no concept of a scheduled "day off" — instead,
*every* eligible player at *every* position gets a rest score for that day's game, and the
highest-scoring player starts. A team's best hitter gets a personal "expected days between rest"
that's longer than a bench player's, so stars sit less often — and catchers get that expected gap
cut in **half** compared to every other position, regardless of how good the individual catcher is,
because the model treats the position itself as more physically demanding rather than judging any
one player's durability. At the top of the scale, an elite everyday player at another position can
go about 13 games between rest days; an equally valuable catcher tops out around 6-7. The halved
gap even follows a player around: a versatile guy who's eligible at catcher *and* another spot still
gets the catcher discount every day, not just the days he actually catches. If a roster gets thin enough
(injuries stacking up, a short bench), the sim will start an out-of-position player, call up a
reserve, or even activate an injured player ahead of schedule rather than ever leave a lineup spot
empty. A legal lineup always wins out over a legal roster.

**Once the day's starters are picked, a batting order is dynamically generated** A team with an
explicit batting order already assigned (a builder team's own lineup) uses those exact spots as-is;
if one of those designated hitters got bumped out of the starting lineup by the rest system above,
whichever open spots are left over get filled by the best-OPS hitter still available, lowest open
spot number first — so a fill-in doesn't necessarily bat where the missing starter would have.
Everyone else (every real-season team, every day) gets an order built by need rather than
front-to-back: the **3-hole is filled first**, taking the best remaining OPS in the whole lineup;
then the **cleanup (4th) spot**, taking the best remaining home-run rate; then the **leadoff (1st)
spot**, taking the fastest remaining runner (ties broken by on-base percentage); then **2nd** (best
remaining OPS again); then **5th** (best remaining slugging); and finally **6th through 9th**, each
simply the next-best OPS left in the shrinking pool.

**Pitchers get a rest check of their own before each game, separate from the hitters' rest scores
above.** A starter's turn is a fixed round robin all regular season long — whoever's next in the
rotation order starts, full stop, with no check on how many actual days off he's had (a 5-man
rotation naturally lands on 4 days' rest anyway whenever the schedule has no off days). Relievers
work differently: any reliever who threw 2+ innings in the last 2 calendar days is pulled from
consideration entirely for that day's bullpen; everyone else still takes a soft penalty to how well
he "fits" a situation, scaled by how many innings he's thrown in the last 3 days (up to a 90%
reduction for someone who's been in it every day). On top of that, once a reliever's appearance
count for the season climbs meaningfully above his own bullpen's average, his fit score gets
discounted further, so one arm can't get run into the ground while others sit idle. The closer gets
his own separate penalty — his fit score is cut in half outside of a genuine 9th-inning-or-later
save situation — so he's naturally kept fresh for when a real save chance shows up.

**User built teams skip the roster machinery, not the daily rest system.** There's no 40-man, no
reserve pool, and no injuries for a builder team — its roster is exactly what the user assembled,
full stop. But its *lineup* still runs through the same daily rest-score algorithm described above:
a builder team's designated starters just get a large flat bonus added to their rest score, big
enough that they almost always win their slot, but not infinite — after enough games in a row
without a break, a bench player's fresher rest score can eventually outweigh that bonus, and the
bench player gets started in his place for that game. The bullpen works the same way: a tired
starter is still automatically relieved mid-game by the same fit-scoring logic real teams use, just
nudged toward whichever reliever the user labeled closer/setup/etc. Only the rotation truly plays
exactly as assigned — turns rotate in the fixed order the user set, with no rest-based override.

### ⚾ Then the game itself gets played

Covered in full in Part 3 below — but the short version is that the two lineups, rotations, and
bullpens built above get handed off to the same at-bat engine no matter what kind of game this is:
a real-season game, a tournament game, or a live real-game takeover.

### 📊 After the game

Both teams' stats get folded into the league totals, the standings update, and — if you're
tracking a specific club's live win/loss record as the season plays (useful for watching a takeover
unfold game by game) — that gets recorded too. Then it's on to the next scheduled date.

### 🏁 Once the regular season ends

Final regular-season standings get locked in *before* any postseason games are played, so playoff
wins and losses never bleed back into the "real" 162-game record.

If the postseason is turned on, brackets are generated using that year's actual format — Wild
Card, LCS, straight to the World Series, whatever was really used that season (or you can force a
specific format). Each round is its own best-of series played with the exact same game engine.

*Planned for a future update:* standings tie breaker logic is not currently included. If 2 teams end up with the same record, it will randomly choose one of them as the team that advances. Era specific tie breaker logic will be added later.

One important difference in October: **injuries stop happening.** Players can still return from
the IL, but nobody gets hurt for the first time once the regular season is over — the injury math
is calibrated against a 162-game grind, not October's shorter, higher-stakes stretch, so it's
deliberately turned off rather than applied inaccurately.

**Starter rest changes shape for October, though.** The fixed rotation described above gives way to genuine
rest-based selection: at "4 days rest" (5 calendar days since his last start), the best-ranked
starter who's actually rested gets the ball; if nobody on the staff is fully rested yet, the sim
falls back to whoever's closest to it — so a deep postseason run can lean harder on its top two or
three arms instead of blindly cycling through five. Reliever rest doesn't change at all — same rules
as the regular season, described above.

### 🏆 End-of-season awards

MVP, Cy Young, Rookie of the Year, and Silver Slugger are all handed out by formula, not by a
simulated vote — there's no ballot model. A few notable choices baked into those formulas:

- **MVP** leans on overall offensive value (wRC+) scaled by playing time, with a small bonus for
  defensive value and net stolen bases — not just raw counting stats.
- **Cy Young** is built around *runs saved relative to a league-average pitcher, scaled by innings
  pitched* rather than plain ERA. That's specifically so a reliever who was brilliant in a tiny
  sample can't out-rank a true workhorse starter's full season.
- **Silver Slugger** at the outfield corners is awarded based on which position — left or right —
  a player actually logged more playing time at *that specific season*, not just whatever position
  happens to be printed on his card.
- **Rookie of the Year** doesn't get its own formula — it reuses the MVP score for rookie hitters
  and the Cy Young score for rookie pitchers, then compares whichever rookie is best at each by
  where he ranks, percentile-wise, against the *entire* qualified league at his own type (all
  hitters, or all pitchers) — not against other rookies. That's what makes a rookie pitcher and a
  rookie hitter comparable for one award despite using two totally different raw scores.

---

## 🎲 Part 3 — How a single game actually plays out

Every game — regular season, postseason, tournament, or a real-game mid-game takeover — runs
through the exact same play-by-play engine. Here's what happens inside one plate appearance, and
the situational rules layered around it.

### 🎲 The at-bat: two rolls, nothing else

1. **The pitch roll** decides who's "in control" of the at-bat. A 1-20 roll is added to the
   pitcher's printed Control/Command number. If the total comes in at or under the *hitter's*
   printed Onbase/Control number, the **hitter** rolls on their own chart for the outcome;
   otherwise the **pitcher** does.
2. **The swing roll** is a second 1-20 roll read against whichever player just won control. If the
   roll comes in above the top of that player's chart, it doesn't miss or reroll — it simply
   resolves to the single best result printed on the chart.

Both rolls sometimes will get a small random wobble (+/- to the roll) added on top before being compared to anything.
Most of the time there's no wobble at all; when there is, it's usually a small nudge,
with bigger rolls (ex: +3) getting rarer the bigger they are. This is a stand-in for strategy cards before they are implemented, and helps especially in expanded sets where there are 21+ chart results.

*Planned for a future update:* Strategy Cards will be added as an option, replacing the random +/-.

**Handedness, when a run turns it on, rides along on that exact same roll** rather than being a
separate mechanic — the platoon nudge and the random wobble are just added together before either
roll is compared to anything. By default handedness does nothing at all — a card performs
identically against a lefty or a righty. However when turned on, the nudge is fixed at one pip: it pushes the
swing roll a notch toward the hitter when he has the platoon advantage (batting opposite the
pitcher's throwing hand — which is why a switch-hitter always counts as advantaged) and a notch
toward the pitcher when they share a hand, and it does the same to the pitch roll that decides who's
even in control of the at-bat in the first place. Since it's just one more addend on the same die
roll, an unlucky wobble can still cancel out a real platoon edge on any given pitch — handedness
shifts the odds over time, it doesn't guarantee anything on a single roll.

*Possible for a future update:* Player's chart fully changes based on the matchup handedness according to actual splits.

### 🏃 After the swing: baserunning is its own set of dice

Stealing, extra-base advances on hits and fly balls, and double plays are **not** chart-driven at
all — each is a fresh roll comparing the runner's speed against the relevant defender's rating, with
a few hand-tuned real-baseball instincts layered in:

- Stealing third is meaningfully riskier to attempt than stealing second, and the model docks the
  runner's odds accordingly — mirroring the old baseball rule of thumb about never making an
  aggressive out at third. Concretely, a runner going from second to third has his speed rating
  knocked down by 5 (out of the roughly 0-20 scale defense and speed are both rated on) for that
  attempt only — both in deciding whether he's sent at all and in the actual safe-or-out roll
  against the catcher's arm once he goes.
- No steal attempt is ever a guaranteed green light or a guaranteed hold — the model always leaves
  some chance either way, no matter how fast or slow the runner is. A runner on second with two outs is much less likely to try for third — so the probability of attempt is reduced significantly.
- A real MLB season's actual stolen-base rate scales how often steals get *attempted* that year —
  a high-steal era plays out with visibly more stolen-base attempts than a low-steal one, rather
  than every season running at the same fixed rate.

### 🥵 Pitching changes: IP and runs allowed based fatigue

There's no pitch-count or batters faced model for simplicity and alignment to original MLB Showdown. A pitcher's "tiredness" is purely **innings actually thrown this game compared to his own card's printed innings rating** — and every 3 runs he's allowed
counts as roughly an extra inning of fatigue, so a starter getting shelled tires out faster than
his raw innings alone would suggest. A starter who's still under his printed limit is never pulled
for fatigue no matter how deep into the game he's gone — but once he actually reaches that limit,
he isn't guaranteed to keep going either: if he's the original starter and has allowed 1 run or
fewer, he gets a fresh 35% chance *every remaining plate appearance* to stay in rather than come out
right on schedule, simulating a manager who lets a guy who's dealing keep working past his printed
innings. It's a coin that gets flipped repeatedly rather than a one-time roll, so a truly dominant
start can run several innings past its printed limit, but the longer it goes past that point the
more times the 35% has to hit in a row, so it's not indefinite.

Picking a reliever isn't "grab the best arm available" — every available reliever gets scored on
how well the situation (score margin, inning, leverage) fits his role, discounted for how much
he's already pitched in the last few days. A pitcher who threw multiple innings in the last two
days gets filtered out of consideration entirely. The closer is treated as a special case: his fit
score is cut in half in anything but a genuine save situation, so he mostly only appears in the
9th inning with a lead. None of this reads recent *results* — a reliever coming off three straight
blown outings is exactly as available as one who's been lights-out. Only workload matters, never a
hot or cold streak.

### 🎛️ The manager dial (optional, off by default)

Every other decision above is fixed — but a run can optionally assign each club's own "manager"
one to five settings for how aggressive it plays: how often it sends runners on steals, how often
it sends runners on extra-base tag-ups, how quickly it pulls a tiring starter, and how often it
uses its closer outside of a true save situation. A neutral (middle) setting for all four is a
complete no-op — it plays exactly like a run with no manager settings at all. This only ever shifts
*decisions* (should we even try), never the underlying fairness of the dice roll that decides
whether the attempt succeeds.

### 🚫 What the engine deliberately does not model

A few things are left out on purpose, not by oversight:

- No momentum, no "clutch," no hot streaks or slumps beyond what's already reflected in a player's
  printed chart.
