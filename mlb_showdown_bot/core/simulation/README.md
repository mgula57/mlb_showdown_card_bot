# `core/simulation`

A dice-based baseball engine that plays out games using `ShowdownPlayerCard`s (from
`core/card`) as the source of truth for every player's ability. It can simulate:

- **A full MLB season** — real schedule, real rosters (rebuilt from archived/pre-built cards),
  real standings and postseason format, optionally with injuries/callups.
- **A season takeover** — a user's `team_builder` `Team` swapped into one real club's slot,
  inheriting its schedule/division/opponents for the season.
- **A tournament** — a round robin between several user-built teams, no real MLB data involved.
- **A single real MLB game** — pre-game (the sim's own lineup or MLB's announced one) or
  mid-game takeover of a live/finished game, via `mlb_game.py`.

Every mode funnels through the same play-by-play machinery (`Game` / `PlateAppearance`), so a
season game, a tournament game, and a real-game takeover are simulated identically once the two
`SimTeam`s and a starting state exist.

## Entry points

| Mode | Class | Driven by |
|---|---|---|
| CLI season sim | `Season` | `__main__.py` (`python -m core.simulation --year 2019 ...`) |
| Web season/takeover sim | `Season` | `api/sim.py: start_season_sim` → background thread |
| Web single-game sim | `MLBGameSimulator` (`mlb_game.py`) | `api/sim.py: start_game_sim` |

`Season.simulate()` is the top-level orchestrator for the first two rows; `MLBGameSimulator` is
a self-contained parallel path for the third that reuses `Game`/`SimTeam` but skips schedule/
standings/postseason entirely.

## The at-bat engine: `plate_appearance.py`

Every plate appearance is two dice rolls against the two cards' printed charts, resolved by
`PlateAppearance` (called from `Game.simulate`'s main loop):

1. **Pitch roll** (`execute_pitch`) — a 1-20 roll plus the pitcher's chart `command`. If the
   total is `<=` the hitter's chart `command`, the **hitter** has the advantage for the swing
   roll; otherwise the **pitcher** does. This is the classic Showdown "who rolls on whose chart"
   mechanic.
2. **Swing roll** (`execute_swing`) — a second 1-20 roll, looked up on whichever player has the
   advantage via `SimPlayer.result_for_roll` (a precomputed roll→`Result` list built once from
   `card.chart.results_as_list` — see `SimPlayer.model_post_init`). Rolls past the top of the
   chart resolve to the best (highest) listed result.

Both rolls get small randomized ±adjustments (`random_plus_or_minus_to_roll`) so outcomes aren't
perfectly deterministic replays of the same chart entry.

After the swing result is known:

- **`check_and_execute_double_play`** — on a `GB` with a runner on first, a second roll against
  infield defense vs. hitter speed decides if it's a double play.
- **`check_and_execute_advance`** — on an advanceable result (a hit, or a flyout with `<3` outs),
  runners on 2nd/3rd get a probabilistic tag-up/extra-base attempt against outfield defense vs.
  runner speed (`probability_of_advance`).
- **`check_and_execute_steal`** (called *before* the pitch) — runners on 1st/2nd with the next
  base open get a probability-weighted steal attempt against the catcher's arm rating.

`Runners` (`runners.py`) owns basepath state and resolves force plays / walks / extra-base
advancement per `Result` (`result.py`) in `Runners.move`. `Inning` (`inning.py`) tracks the
half-inning's outs/runs/runners and reports `is_played` so a phantom half-inning appended right
before a walk-off never renders as a real frame.

Every `PlateAppearance` also produces `pitcher_stats` / `hitter_stats` / steal / advance / double
-play `Stats` deltas that `Game.simulate` merges into each team's per-game `StatsGroup`, and a
`PlateAppearanceNarrator` (`narration.py`) that turns the resolved play into MLB-feed-style
text (`event` badge + `description` sentence) purely by diffing base-state before/after — it
never invents detail (batted-ball type, fielder) the engine doesn't actually model.

## Teams and rosters

### `SimPlayer` / `SimPitcher` (`player.py`)

A thin, mostly-read-only wrapper around a `ShowdownPlayerCard` plus simulation-only mutable
state: current `position_slot`, preset lineup/position (for builder-team lineups), and — for
pitchers — innings-pitched tracking (`is_tired`) and bullpen "situational fit" scoring
(`situational_fit`, used to pick a reliever).

### `SimTeam` (`team.py`)

Owns the active roster, current game's lineup/defense/bullpen availability, win/loss record, and
per-game stat bookkeeping. Built one of three ways:

- **`from_player_pool`** — a real season team. Delegates roster *selection* to `Roster.select`
  (see below), then wraps the result. Gets a year-aware color identity from `shared.Team`.
- **`from_builder_team`** — a user's `team_builder.Team`. Honors its explicit lineup/rotation/
  bullpen role assignments (`SP1`-`SP5`, `CL`, etc.) verbatim rather than auto-selecting. No
  `Roster` (`self.roster` stays `None`) — builder teams have no 40-man, no injuries, no callups.
  That `None` is the scope guard every roster/injury-aware code path checks.
- **`from_mlb_game_roster`** — one side of a real MLB game (`mlb_game.py`). Pins the announced
  lineup when known, falls back to auto-fill otherwise.

Per-game, `SimTeam.add_new_game` rebuilds the lineup (`fill_starting_position_players` →
`generate_batting_order`) and resets pitcher-usage tracking. `_player_for_slot` fills each
defensive spot with a layered fallback so a thin/injured roster can never deadlock a lineup:
eligible active player → emergency callup from reserves → an out-of-position active player →
force-activate the soonest-returning injured player → raise (truly nobody left).

### `Roster` (`roster.py`) — the 40-man, injuries, and transactions

Only real-season teams get one. Two responsibilities:

1. **`Roster.select`** (pure, no mutation/RNG) — splits a pool of cards into an active roster
   (13 position players + 5 SP + 8 RP by default) and a reserve pool, applying playing-time
   floors so cup-of-coffee cards don't pad the bench. Coverage-first: every defensive position is
   filled before the roster is topped up by raw points.
2. **Injuries** (opt-in via `SeasonSimulationConfig.enable_injuries`) — `InjuryProfile` is built
   once per player at roster construction (`build_profiles`), calibrated so a player's *expected*
   simulated missed games match the gap between his real games played and a role-adjusted healthy
   baseline (scaled by playing-time "confidence" so a bench bat doesn't read as chronically hurt
   just because he's a bench bat). `Roster.process_date` rolls one hazard check per active player
   per calendar day; a hit calls `place_on_il`, which finds a reserve replacement and logs a
   `Transaction`. `emergency_callup` / `emergency_activate_earliest` are lineup-fill safety valves
   for when both the active roster *and* the reserve pool are exhausted — a legal lineup always
   beats a legal roster/IL stint.

### `player_group.py` — `Rotation`, `Bullpen`, `PositionEligibility`

- `Rotation` is a positional round-robin (`pitcher_index`) advanced once per team-game.
- `Bullpen.suggested_reliever` picks a reliever using save-situation logic for the closer and a
  situational-fit score (leverage, score tightness, recent workload) for everyone else.
- `PositionEligibility` is the shared "who can play where" logic used by both roster selection
  and in-game lineup filling, keyed off each card's `positions_and_defense`.

## A game: `game.py`

`Game.setup` wires two `SimTeam`s together (`add_new_game` on each) and seeds the inning stack —
either fresh (`Inning(inning=1, is_top=True)`) or, for a real-game takeover, replayed from a
`GameStartState` (completed innings, the in-progress one, both teams' pitcher-usage/lineup-index/
score state).

`Game.simulate` is the main loop: for each plate appearance, pick the current pitcher/hitter,
run the full at-bat sequence (steal → pitch → swing → double play → advance), fold the resulting
`Stats` deltas into both teams, optionally narrate/log it, and check for the game-over condition
(3 outs in the bottom/top of 9+ with the home/away team ahead). `finalize_game` snapshots final
score, builds the linescore (and, if requested, a full box score) and marks the game over.

## Schedule, standings, postseason

- **`Schedule`** (`schedule.py`) — real seasons pull the MLB Stats API's season schedule and
  normalize team abbreviations to their *era-correct* code (`normalized_team_abbr`, via
  `shared.Team`) so a 1998 Tampa Bay game joins to `TBD` cards, not a modern code. Tournaments
  generate a round robin between the given team names instead (`generate_schedule`).
- **`Standings`** (`standings.py`) — holds `SimTeam`s plus their division/league alignment
  (fetched from the MLB Stats API, with hardcoded fallbacks for API failures or pre-1969
  league-only alignment). Sorts by win% for bracket seeding and division-leader lookups.
- **`Postseason`** (`postseason.py`) — `PostseasonFormat` (`WC1`/`WC2`/`WC3`/`LCS`/`WS`, or
  `DYNAMIC` to pick the era-correct real format for the year) drives bracket generation
  (`generate_initial_schedule`) and round-by-round advancement (`advance_teams_to_next_round`).
  Each round is a `PostseasonSeries` of `Game`s. Only IL *returns* are processed during the
  postseason (`process_il_returns_for_date`), never new injury rolls — the regular-season hazard
  rates aren't calibrated for October's sparser schedule.

## Stats: `stats.py`

`Stats` is a single statline (one player, one team-game, or a league aggregate): raw counting
stats live in `totals: dict[str, float]` keyed by `StatCategory`, and rate stats (`ba`, `obp`,
`ops`, `era`, `whip`, `wOBA`/`wRAA`/`wRC`/`wRC+`, ...) are computed properties/methods, some of
which need league context (`ops_plus`, `wRC_plus`) or Fangraphs wOBA weights (loaded per-year
from `real_stats/league_wOBA_weights.csv`). `StatsGroup` is a keyed collection with merge
semantics; `PlayerStatsGroup` seeds one identity statline per live `SimPlayer` (including
reserves, so a mid-season callup already has a row) and can build a real-life comparison line
from each card's actual stats for sim-vs-real accuracy checks. `PitchingLog` tracks daily IP per
pitcher so both bullpen-availability (`pitcher_ids_with_recent_workload`) and reliever leverage
scoring (`recent_ip_by_pitcher`) can see recent workload without rescanning the whole season.

`real_stats/*.csv` holds real MLB league averages and wOBA weights per year, used purely as a
benchmark (`SeasonSimulationResult.top_outliers`, `print_real_life_comparison`) — never fed back
into the simulation itself.

## Season takeover: `takeover.py`

`TakeoverOptions` lists the real clubs available to replace for a given year (worst record
first — the default is deliberately the season's worst team, the "uphill" version of the game),
sourced from MLB Stats API standings rather than the archive (which stores cards, not results).
`Season._build_season_teams` swaps the builder team into the replaced club's dict slot *under
that club's own key* — the schedule, standings, and division mapping all key off abbreviation,
so keeping the key is what makes the takeover team inherit the real club's entire season without
any special-casing elsewhere.

## Awards: `awards.py`

`AwardsBuilder` computes MVP / Cy Young / Rookie of the Year / Silver Slugger per league from the
finished season's full player pool. None of these are real award criteria (no ballots) — each
picks a single deciding stat already available in the pipeline (wRC+ × playing time × a small
defense bump for MVP, lowest ERA for Cy Young, most points among flagged rookies for RoY, highest
OPS per position for Silver Slugger). See the class docstring for the exact caveats (RoY is only
reliable for 2026+ MLB-API-sourced seasons; outfield gets one combined `LF/RF` award since the
engine never assigns a bare LF or RF).

## Turning a result into output

`Season.simulate()` returns a `SeasonSimulationResult` (`models.py`) — the full, ~6 MB, fully
JSON-serializable record of the run (every game, every player's season stats, standings,
postseason, transactions). Two different consumers project it down differently:

- **`SeasonReport`** (`reporting.py`) — CLI-only. Renders `PrettyTable`s and an ASCII postseason
  bracket directly to stdout. Never persisted.
- **`SeasonSummaryBuilder`** (`summary.py`) — the web path. Projects the full result down to the
  ~100 KB `SeasonSimSummary` that the frontend result screen actually renders (one team's games/
  players, trimmed leaderboards, standings, postseason without box scores) so the full result can
  be freed immediately after. Shares its stat column sets with `SeasonReport` so the CLI and web
  tables never drift apart.

## Single real MLB game: `mlb_game.py`

A parallel, self-contained path (not used by `Season`) for simulating one real MLB game rather
than a full season. `MLBGameCardPool` resolves a Showdown card for every player who could appear
(pre-built → generated from season-to-date stats → synthetic replacement-level, cheapest tier
first), `MLBGameSetup` assembles both `SimTeam`s (via `SimTeam.from_mlb_game_roster`) either
pre-game or mid-game, and `MLBGameSimulator.simulate` hands off to the exact same `Game.simulate`
loop the season path uses — `Game.setup(start_state=...)` is the only seam that differs, seeding
completed innings, the in-progress one, and each team's used-pitchers/lineup-index/score from a
live game's real box score.

## Web API wiring: `api/sim.py`

Season/takeover sims run in a background thread (`_run_sim_job`) behind a small semaphore
(`_MAX_CONCURRENT_SIMS`) so a burst of requests can't starve the Flask worker. Progress is
written to Postgres via two callbacks passed into `Season.simulate`:

- `progress_callback(completed, total)` — fires once per game (~2,400×/season); throttled to
  ~1 write/second (`_PROGRESS_WRITE_INTERVAL`) rather than writing every game.
- `status_callback(message)` — fires with human-readable setup milestones (card loading, schedule
  building, roster construction). `_friendly_phase` maps these onto a small set of coarse,
  user-facing phase labels (`SETUP_PHASES` in the frontend's `SimProgress.tsx` mirrors this list)
  and drops anything it doesn't recognize (e.g. per-team roster warnings), so the progress bar
  never shows raw internal log lines.

A single real-game sim (`start_game_sim`) is synchronous instead — a few hundred plate
appearances runs in milliseconds, so there's no job/poll cycle for it.

## File map

| File | Responsibility |
|---|---|
| `season.py` | Top-level season/tournament orchestrator (`Season`, `PlayerLoader`) |
| `game.py` | One game's play-by-play loop, linescore/box score building |
| `plate_appearance.py` | The dice-roll at-bat engine |
| `runners.py`, `inning.py`, `result.py` | Basepath state, half-inning state, the chart result enum |
| `team.py` | `SimTeam` — roster/lineup/defense/pitching-usage per game |
| `roster.py` | 40-man selection, injuries, callups/transactions |
| `player.py` | `SimPlayer`/`SimPitcher` — card + sim state wrapper |
| `player_group.py` | `Rotation`, `Bullpen`, `PositionEligibility` |
| `schedule.py` | Real MLB schedule fetch / tournament round robin |
| `standings.py` | Division/league alignment, sorting, seeding |
| `postseason.py` | Bracket generation and round advancement |
| `stats.py` | `Stats`/`StatsGroup`, sabermetric formulas, real-life reference data |
| `narration.py` | Play-by-play sentence generation |
| `awards.py` | End-of-season awards |
| `takeover.py` | Real clubs available to replace, per year |
| `mlb_game.py` | Single real-MLB-game sim (pre-game or mid-game takeover) |
| `models.py` | All Pydantic request/result models |
| `reporting.py` | CLI table/bracket rendering |
| `summary.py` | Web-facing result projection |
| `__main__.py` | CLI entry point |
| `real_stats/*.csv` | Real MLB league averages / wOBA weights, per year |
