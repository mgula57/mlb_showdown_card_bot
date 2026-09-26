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
his own separate penalty — his fit score is cut in half outside of a 9th-inning-or-later save
situation — so he's naturally kept fresh for when a real save chance shows up. (Exactly what counts
as a "save situation" in the sim is covered in Part 3.)

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

### 📋 Before the first pitch: the nine are locked in

Once the day's lineup and batting order are set (Part 2), they're frozen for the whole game.
There are **no in-game substitutions for position players** — no pinch hitters, no pinch runners,
no defensive replacements, no double switches. The nine who start are the nine who finish.

That's also why team defense is worked out once, up front, and then reused on every play:

- **Infield defense** is the sum of the 1B, 2B, 3B, and SS fielding ratings, each read at the
  position that player is actually playing today. It's what turns double plays.
- **Outfield defense** is the sum of the LF, CF, and RF ratings. It's what throws out runners
  trying to take an extra base.
- **The catcher's arm** is the starting catcher's own rating. It's what throws out base stealers.

A player playing out of position brings whatever rating his card has at that spot, which is often
none at all, so his team's defense gets weaker for the day.

*Planned for a future update:* proper in game substitutions for pinch running and pinch hitting.

### 🔁 The order of one plate appearance

Every plate appearance runs through the same fixed sequence:

1. **Bullpen check:** is the pitching team's current pitcher tired? If so, a reliever comes in now,
   before the next batter (see *Pitching changes* below).
2. **Steal check:** runners on base may try to steal before the pitch. If the last batter hit a
   1B+, he takes second here automatically instead.
3. **The pitch roll**, then **the swing roll** (below).
4. **Runners move** according to the result.
5. **Double play check** on a ground ball with a runner on first.
6. **Extra-base check:** a runner may be sent for one more base on a hit or a fly ball.

If a runner is caught stealing for the third out, the inning ends before the pitch is ever thrown,
and the batter who was standing at the plate leads off the next inning instead of losing his turn.

### 🎲 The at-bat: two rolls, nothing else

1. **The pitch roll** decides who's "in control" of the at-bat. A 1-20 roll is added to the
   pitcher's printed Control/Command number. If the total comes in at or under the *hitter's*
   printed Onbase/Control number, the **hitter** rolls on their own chart for the outcome;
   otherwise the **pitcher** does.
2. **The swing roll** is a second 1-20 roll read against whichever player just won control. If the
   roll comes in above the top of that player's chart, it doesn't miss or reroll — it simply
   resolves to the single best result printed on the chart.

Both rolls sometimes will get a small random wobble (+/- to the roll) added on top before being compared to anything.
Most of the time there's no wobble at all (about 15% of pitch rolls and 35% of swing rolls get
one); when there is, it's usually a small nudge,
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

### 🏠 How runners move on each result

Before any extra-base decision comes into play, every result moves runners by a fixed rule:

- **Single / 1B+ / double / triple:** every runner moves up exactly as many bases as the batter
  does. A single moves a runner from first to second, and a double scores a runner from second.
  A **1B+** is a single, but the batter then takes second automatically before the next plate
  appearance, as long as second is open and the inning isn't over. There's no throw and no roll. It
  goes in the books as a stolen base, and it counts as that plate appearance's one steal, so nobody
  else runs behind it.
- **Home run:** everyone scores.
- **Walk:** only forced runners move. A runner on second holds on a walk unless first base was
  occupied too.
- **Ground ball:** with a runner on first, it's a force at second, and then a double-play roll
  decides whether the batter is out at first too (below). Otherwise the batter is out, and runners
  on second and third each move up one base. That means a runner on third scores on a ground out
  with fewer than two outs.
- **Fly ball:** runners hold, but a runner may tag up (see *extra bases* below).
- **Strikeout / popup:** nobody moves.

Nothing moves on the third out, so a runner on third doesn't score on an inning-ending ground ball.

### 🏃 After the swing: baserunning is its own set of dice

Stealing, extra-base advances on hits and fly balls, and double plays are **not** chart-driven at
all — each is a fresh roll comparing the runner's speed against the relevant defender's rating, with
a few hand-tuned real-baseball instincts layered in. Every one of them uses the same d20 check: the
defense's rating plus a 1-20 roll has to beat the runner's speed to get the out. So a runner's
chance of being safe is roughly *(his speed minus the defense's rating) ÷ 20*.

**Steals** happen before the pitch:

- Only a runner on first (going to second) or on second (going to third) can steal, and only into
  an open base. Nobody steals home, and there's at most one steal attempt per plate appearance.
  A runner can still steal second before one batter and third before the next.
- The runner goes up against the catcher's arm.
- Stealing third is meaningfully riskier to attempt than stealing second, and the model docks the
  runner's odds accordingly — mirroring the old baseball rule of thumb about never making an
  aggressive out at third. Concretely, a runner going from second to third has his speed rating
  knocked down by 5 (out of the roughly 0-20 scale defense and speed are both rated on) for that
  attempt only — both in deciding whether he's sent at all and in the actual safe-or-out roll
  against the catcher's arm once he goes.
- Whether a runner even tries depends on his odds. A runner needs about an 8-point speed edge over
  the catcher's arm before he'll consider going at all, so slow runners simply never steal. On the
  other end, no runner is ever a guaranteed green light: even the fastest runner against the
  weakest arm tops out at roughly an 85% chance to go (before the era adjustment below). A runner on
  second with two outs is much less likely to try for third, so the probability of an attempt is
  reduced significantly.
- A real MLB season's actual stolen-base rate scales how often steals get *attempted* that year —
  a high-steal era plays out with visibly more stolen-base attempts than a low-steal one, rather
  than every season running at the same fixed rate.

**Double plays:** on a ground ball with a runner on first and fewer than two outs, the lead runner
is always forced at second. Then the team's combined infield defense plus a d20 roll is checked
against the *batter's* speed. If the defense wins, the batter is out too; if not, it's a fielder's
choice and he's safe at first. A fast batter beats out a lot of double plays, and a slow one hits
into a lot of them. If the double play is the third out, any run that crossed home on the play is
wiped off the board.

**Extra bases (sends and tag-ups):** after a hit, or a fly ball that isn't the third out, one existing runner may be sent for one base more than the hit gave him. This covers first-to-third on a
single, scoring from second on a single, scoring from first on a double, and tagging up from third
(or from second to third) on a fly ball.

- Only one runner is ever sent on a play. If third base is occupied after the hit, the runner on
  third is the one who might go home. If third is open, the runner on second might go to third.
  The batter himself never stretches a hit.
- The runner goes up against the combined outfield defense.
- Going to third is docked 5 speed, just like stealing third. Going home gets a +5 bonus, and +10
  with two outs, because the runner was off on contact.
- Unlike steals, the decision to send does **not** have randomness to it. At a neutral setting, a runner is sent
  whenever he's at least a 50/50 shot to be safe. That works out to his speed, after those
  bonuses, beating the outfield defense by 10 or more. The manager dial below moves that line.
  Once he's sent, the safe-or-out roll is random as usual.

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

**A pitcher getting hammered comes out early, no matter his innings rating.** If he's allowed 5 or
more runs, or he's been in for at least an inning and allowed 1.5 or more runs per inning pitched,
he's pulled right away.

A few more rules that shape the bullpen inside a game:

- **Fatigue is the only reason a pitcher is ever taken out.** There are no lefty-on-lefty
  specialist moves and no pulling a pitcher for a matchup. Relievers follow the same rules as
  starters, measured against their own innings rating, so a 1-inning reliever is usually done
  after about an inning.
- **Checks happen before every batter**, so a pitching change can come in the middle of an inning.
- **Once a pitcher leaves, he can't come back** in that game.
- **An empty bullpen means no relief.** If every reliever has already pitched today or is
  unavailable from recent work, whoever is on the mound stays in, however tired he is.

Picking a reliever isn't "grab the best arm available" — every available reliever gets scored on
how well the situation (score margin, inning, leverage) fits his role, discounted for how much
he's already pitched in the last few days. The bullpen is ranked from best to worst (by the
opponent OPS his card projects to allow, or by the roles the user assigned on a builder team), and
the fit score pairs the best arms with close games late, and the weaker arms with blowouts and
early innings. A pitcher who threw 2+ innings in the last two days gets filtered out of
consideration entirely. None of this reads recent *results* — a reliever coming off three straight
blown outings is exactly as available as one who's been lights-out. Only workload matters, never a
hot or cold streak.

**The closer is a special case.** In the sim, a "save situation" means the 9th inning or later with
his team **ahead by any margin or tied**. It's looser than the official save rule on purpose. If a
change is needed in a save situation and the closer is rested and hasn't pitched yet today, he
comes in automatically, skipping the scoring above entirely. Outside a save situation his fit score
is cut in half, so he mostly only appears in the 9th or later with the game close. The closer
doesn't bump a pitcher who isn't tired, though: if the setup man is still fresh in the 9th, he stays
in.

### 📝 Keeping score

- **Runs are charged to whoever put the runner on base.** A reliever who inherits a runner on third
  and gives up a sacrifice fly isn't charged with that run. The pitcher who allowed the runner is.
- **Every run is earned.** The sim doesn't model errors, so the box score always shows 0 errors and
  runs allowed always equal earned runs.
- **No RBI on a double play**, matching the real scoring rule.
- **Win, loss, save, and blown save** are handed out when the game ends. The sim only remembers
  the score at the moment each pitcher entered, not a full inning-by-inning history, so these
  follow the official rules as closely as that allows:
  - **Win:** the winning team's pitcher who was on the mound when it took the lead for good. If
    that's the starter and he didn't finish 5 innings, the win goes to the winning team's most
    effective reliever instead (most outs recorded, then fewest runs allowed).
  - **Loss:** the losing team's pitcher who was on the mound when it fell behind for good.
  - **Save:** the winning team's final pitcher, if he isn't the winning pitcher, entered with the
    lead, and either protected a lead of 3 or fewer or got at least 9 outs.
  - **Blown save:** any reliever who entered protecting a 1-3 run lead and left with it gone. A
    pitcher can blow a save and still get the win.

### 🔚 How a game ends

- **Nine innings.** If the home team is leading after the top of the 9th, the bottom half isn't
  played.
- **Walk-offs end it immediately.** The moment the home team takes the lead in the 9th or later,
  the game is over, even mid-inning.
- **Extra innings go as long as needed.** There are no ties, and no automatic runner on second
  in extras, whatever era is being played.

### 📺 Taking over a real game in progress

A live real-game takeover freezes the real game where it stands and plays the rest in the sim. It
picks up the inning, outs, baserunners, score, and whose turn it is in the batting order. Every
pitcher already used comes along with his innings and runs allowed so far, so the innings a real
pitcher has already thrown count toward his fatigue, and a reliever who's already pitched can't come back.
The real innings stay in the line score and the real box score stats carry over, so the final box
score shows the whole game, not just the simulated part. From there, every rule above applies
unchanged.

### 🎛️ The manager dial

Every other decision above is fixed — but a run can assign each club its own "manager" with one to
five settings for how aggressive it plays. Every club starts at the neutral middle setting:

- **Steal aggression** raises or lowers how often runners try to steal.
- **Baserunning aggression** moves the "send him" line for extra bases up or down from the neutral
  50/50.
- **Bullpen hook** pulls tiring pitchers up to an inning sooner, or leaves them in up to an inning
  longer.
- **Closer usage** changes how often the closer is used outside a save situation. At the top two
  settings, a save situation also starts earlier, in the 8th or even the 7th inning.

A neutral (middle) setting for all four is a complete no-op — it plays exactly like a run with no
manager settings at all. This only ever shifts *decisions* (should we even try), never the
underlying fairness of the dice roll that decides whether the attempt succeeds.

### 🚫 What the engine deliberately does not model

A few things are left out on purpose, not by oversight. Some will be added at a future date:

- No momentum, no "clutch," no hot streaks or slumps beyond what's already reflected in a player's
  printed chart.
- No errors or unearned runs.
- No in-game position-player substitutions: no pinch hitters, pinch runners, or defensive
  replacements.
- No matchup-based pitching changes. A pitcher only leaves because he's tired or getting hit hard.
- No sacrifice bunts, intentional walks, hit-and-runs, or pickoffs.
- No automatic extra-innings runner, and no tie games.
