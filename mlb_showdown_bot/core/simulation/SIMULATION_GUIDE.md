# How a season simulation actually works

This is a plain-language walkthrough of what happens when you click "simulate" on a full MLB
season (or a season takeover) in this app. It assumes you know how MLB Showdown itself plays —
charts, dice, on-base/advantage rolls — and walks through everything *around* that: how a season
gets built, how a single game gets played out, and all the smaller rules bolted on to make 162
games of simulated baseball feel like a real season instead of 162 identical coin flips.

For the file-by-file developer reference, see [README.md](README.md). This document is about
*behavior* — what the engine assumes, decides, and deliberately ignores.

---

## Part 1 — Building the season, before a single pitch is thrown

### Step 1: Every player gets a card

The sim doesn't know about players — it only knows about `ShowdownPlayerCard`s. Before anything
else, it loads a card for every player who appeared that season. Most of these are pulled
pre-built from the archive; a handful of players who slipped through the cracks get their card
built on the fly from raw stats. If a card truly can't be built (no usable stats on record), that
player just doesn't exist in the sim.

### Step 2: The real schedule comes down

The season's actual game-by-game schedule is pulled straight from the MLB Stats API — same
matchups, same days, same home/away split as really happened that year. Old team abbreviations are
mapped to their era-correct codes, so a 1998 Tampa Bay game correctly finds Devil Rays cards
instead of quietly matching nothing.

If you're running a **rest-of-season projection** instead of a full season, this is where that
gets carved out: every club's real record as of today (or whatever date you picked) is loaded as
the *starting* record, and only the games after that date actually get simulated.

### Step 3: Trades get planned (optional)

If trade-deadline moves are turned on, the sim looks at every player who really played for more
than one club that season and figures out which was his *first* club and which was his *last*.
Anyone who was clearly just a September call-up or a spring-training paper transaction (fewer than
about 10 real games on one end of the split) is pinned to a single club for the whole run instead —
that's not a real mid-season trade, so it doesn't get treated like one.

For everyone else, a trade is scheduled for that year's era-correct deadline date (mid-June before
1986, July 31 from then on). The move doesn't split his stats — his one statline just accrues to
whichever club owns him at the time, exactly like a real transaction.

### Step 4: Rosters get built, position by position

Each club's 40-man roster is assembled from the cards that played for it that year — but not by
simply grabbing whoever's most valuable. The active roster is filled **one defensive position at a
time**, taking the best player available at each spot before ever topping the roster off with raw
value. A backup catcher is a hard requirement no matter what — nobody else is allowed to quietly
cover that job. This is deliberate: a real team that's stacked at shortstop and thin behind the
plate doesn't get to field a lineup with two shortstops and no catcher just because the shortstops
are better players.

A reserve pool sits behind the active 26 as the on-deck pool for injuries and call-ups. Players
without enough real playing time to be a meaningful sample don't make either group.

### Step 5: If it's a takeover, your team gets swapped in

A season-takeover team doesn't get its own new schedule — it's dropped directly into a real club's
slot, taking over that club's exact schedule, division, and opponents for the year. By default the
game offers you the *worst* team in baseball that season first, since turning a last-place club
around is the point of the mode. A takeover team skips the 40-man/injury system entirely — your
lineup, rotation, and bullpen play exactly as you built them, with no auto-resting and no
auto-swapping.

### Step 6: Injury profiles get calibrated (optional)

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

## Part 2 — Playing the season, day by day

With the season built, the sim plays through the schedule one real game at a time, in
chronological order.

### Before each game: who's actually available today

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
that's longer than a bench player's, so stars sit less often — and catchers get a shorter gap than
every other position by default, regardless of how good the individual catcher is, because the
model treats the position itself as more physically demanding. If a roster gets thin enough
(injuries stacking up, a short bench), the sim will start an out-of-position player, call up a
reserve, or even activate an injured player ahead of schedule rather than ever leave a lineup spot
empty. A legal lineup always wins out over a legal roster.

**Builder teams skip all of this.** A user-built team's lineup, rotation, and bullpen are played
exactly as assigned — no rest system, no injuries, no auto-swapping.

### Then the game itself gets played

Covered in full in Part 3 below — but the short version is that the two lineups, rotations, and
bullpens built above get handed off to the same at-bat engine no matter what kind of game this is:
a real-season game, a tournament game, or a live real-game takeover.

### After the game

Both teams' stats get folded into the league totals, the standings update, and — if you're
tracking a specific club's live win/loss record as the season plays (useful for watching a takeover
unfold game by game) — that gets recorded too. Then it's on to the next scheduled date.

### Once the regular season ends

Final regular-season standings get locked in *before* any postseason games are played, so playoff
wins and losses never bleed back into the "real" 162-game record.

If the postseason is turned on, brackets are generated using that year's actual format — Wild
Card, LCS, straight to the World Series, whatever was really used that season (or you can force a
specific format). Each round is its own best-of series played with the exact same game engine.

One important difference in October: **injuries stop happening.** Players can still return from
the IL, but nobody gets hurt for the first time once the regular season is over — the injury math
is calibrated against a 162-game grind, not October's shorter, higher-stakes stretch, so it's
deliberately turned off rather than applied inaccurately.

### End-of-season awards

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

---

## Part 3 — How a single game actually plays out

Every game — regular season, postseason, tournament, or a real-game mid-game takeover — runs
through the exact same play-by-play engine. Here's what happens inside one plate appearance, and
the situational rules layered around it.

### The at-bat: two rolls, nothing else

1. **The pitch roll** decides who's "in control" of the at-bat. A 1-20 roll is added to the
   pitcher's printed Control/Command number. If the total comes in at or under the *hitter's*
   printed Onbase/Control number, the **hitter** rolls on their own chart for the outcome;
   otherwise the **pitcher** does. This is the same "whose chart do we read" mechanic as tabletop
   Showdown.
2. **The swing roll** is a second 1-20 roll read against whichever player just won control. If the
   roll comes in above the top of that player's chart, it doesn't miss or reroll — it simply
   resolves to the single best result printed on the chart.

Both rolls get a small random wobble added on top before being compared to anything, so the exact
same matchup — same hitter, same pitcher, same situation — won't play out identically every time.
Most of the time there's no wobble at all; when there is, it's usually the smallest possible nudge,
with bigger swings getting rarer the bigger they are. This isn't a strategy-card mechanic and there
are no in-game player decisions modeled inside an at-bat — it's a flat, symmetric randomizer that
doesn't favor the hitter or the pitcher.

**Handedness can optionally tilt this roll.** By default it doesn't — a card performs identically
against a lefty or a righty. But the engine supports nudging both rolls a notch in the hitter's
favor when he has the platoon advantage (batting opposite the pitcher's throwing hand — which is
why a switch-hitter always counts as advantaged), and a notch toward the pitcher when they share a
hand. It's off unless a run specifically turns it on.

### After the swing: baserunning is its own set of dice

Stealing, extra-base advances on hits and fly balls, and double plays are **not** chart-driven at
all — each is a fresh roll comparing the runner's speed against the relevant defender's rating, with
a few hand-tuned real-baseball instincts layered in:

- Stealing third is meaningfully riskier to attempt than stealing second, and the model docks the
  runner's odds accordingly — mirroring the old baseball rule of thumb about never making an
  aggressive out at third.
- A runner already standing on second with two outs is much less likely to try for third — there's
  little value in the extra risk when he's already in scoring position.
- No steal attempt is ever a guaranteed green light or a guaranteed hold — the model always leaves
  some chance either way, no matter how fast or slow the runner is.
- A double play can only happen off a ground ball with a runner on first — the engine has no
  concept of batted-ball type beyond that, so there's no double play off a line drive or a bunt.
- A real MLB season's actual stolen-base rate scales how often steals get *attempted* that year —
  a high-steal era plays out with visibly more stolen-base attempts than a low-steal one, rather
  than every season running at the same fixed rate.

### Pitching changes: fatigue, not pitch counts

There's no pitch-count model at all. A pitcher's "tiredness" is purely **innings actually thrown
this game compared to his own card's printed innings rating** — and every 3 runs he's allowed
counts as roughly an extra inning of fatigue, so a starter getting shelled tires out faster than
his raw innings alone would suggest. A starter who's still spotless and within his printed limit
is never pulled for fatigue, no matter how deep into the game he's gone — a great outing is allowed
to run long.

Picking a reliever isn't "grab the best arm available" — every available reliever gets scored on
how well the situation (score margin, inning, leverage) fits his role, discounted for how much
he's already pitched in the last few days. A pitcher who threw multiple innings in the last two
days gets filtered out of consideration entirely. The closer is treated as a special case: his fit
score is cut in half in anything but a genuine save situation, so he mostly only appears in the
9th inning with a lead. None of this reads recent *results* — a reliever coming off three straight
blown outings is exactly as available as one who's been lights-out. Only workload matters, never a
hot or cold streak.

### The manager dial (optional, off by default)

Every other decision above is fixed — but a run can optionally assign each club's own "manager"
one to five settings for how aggressive it plays: how often it sends runners on steals, how often
it sends runners on extra-base tag-ups, how quickly it pulls a tiring starter, and how often it
uses its closer outside of a true save situation. A neutral (middle) setting for all four is a
complete no-op — it plays exactly like a run with no manager settings at all. This only ever shifts
*decisions* (should we even try), never the underlying fairness of the dice roll that decides
whether the attempt succeeds.

### What the engine deliberately does not model

A few things are left out on purpose, not by oversight:

- No weather, no park factors, no crowd noise, no travel fatigue — whatever context is already
  baked into a card's printed chart at generation time is the only context that reaches the game.
- No pitch counts, no explicit rest requirement between a starter's outings on the calendar.
- No batted-ball type (grounder vs. liner vs. fly) beyond what's needed for the double-play and
  tag-up rules above — so the play-by-play text never invents a "sharp grounder to short" detail
  the engine didn't actually track.
- No momentum, no "clutch," no hot streaks or slumps beyond what's already reflected in a player's
  printed chart.

---

## Where to look next

- [README.md](README.md) — the file-by-file map of the actual code, for anyone making changes to
  the engine itself.
- `frontend/src/components/team_builder/sim/SimEngineExplainer.tsx` — the short, rotating
  plain-language facts shown to users while a simulation is running in the app. This guide is the
  long-form version of the same idea.
