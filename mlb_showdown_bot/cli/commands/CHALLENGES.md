# Setting up Team Challenges

CLI: [`challenges.py`](challenges.py) — registered as `showdown_bot challenges`.

A **Team Challenge** is a weekly "take over a real club and hit a goal" scenario. There are two layers:

| Layer | What it is | How it's made | Lifetime |
|-------|-----------|---------------|----------|
| **Template** | Hand-authored content: the goal, budget cap, player pool, year/club pools. | You, via `challenges create-template`. | Permanent (until you set it `--inactive`). |
| **Instance** | A concrete playable challenge: one real `year` + `replaces_abbr` club resolved from a template's pools, with `pts_limit` / `roster_size` / `player_filters` snapshotted onto it. | The scheduler, via `challenges rotate` (or `challenges instance <slug>` by hand). | 7 days, then pruned 30 days after expiry. |

`rotate` keeps exactly **one live instance per category** (`legendary` / `budget_cap` / `themed`) — each category is a rotation pool of templates, and every cycle the least-recently-used template in a category becomes that week's challenge, but only if the category has no live instance already. The frontend challenges list shows the live instances; players build a team (min `roster_size`, under `pts_limit`, matching `player_filters`), sim the season, and pass/fail against `goal_type`.

So: write as many templates per category as you like — they queue up and take turns. Three categories → three live challenges at any time.

Tables and columns live in [`core/database/README.md`](../../core/database/README.md) (`internal.challenge_template` / `internal.challenge_instance`), created by `PostgresDB.build_challenge_tables()`.

---

## Which database?

**This is the #1 footgun.** `--env` picks the target DB, and the two don't talk to each other:

| `--env` | Database | Use |
|---------|----------|-----|
| `dev` (default) | `DATABASE_URL_LOGS` | **Production challenges live here.** The scheduled `rotate` workflow runs with no `--env`, so it reads/writes `LOGS`. |
| `prod` | `DATABASE_URL_ARCHIVE` | Only if you specifically want challenges in the archive DB. |

Every command echoes `Using --env dev (DATABASE_URL_LOGS).` on the first line — read it. Creating a template in one DB while `rotate` reads the other looks like "no templates exist" with no error anywhere.

**Rule of thumb: create templates with the default env** (no `--env` flag) so they match the scheduled rotation.

---

## One-time setup

1. Env vars set (`DATABASE_URL_LOGS`, plus the usual `SUPABASE_*` / `GOOGLE_CREDENTIALS`) — see the repo [`CLAUDE.md`](../../../CLAUDE.md).
2. Tables exist — `build_challenge_tables()` has run against the LOGS DB. It ALTERs `sim_season` and `user_teams`, so it must run after `build_sim_job_table` and `build_user_teams_tables`.
3. Weekly rotation is wired: [`.github/workflows/rotate_challenges.yml`](../../../.github/workflows/rotate_challenges.yml) runs `showdown_bot challenges rotate` every Monday 12:00 UTC (also runnable from the Actions tab).

---

## Authoring a template

```bash
showdown_bot challenges create-template \
  --slug small-budget-pennant \
  --title "Cinderella Run" \
  --description "Take over a real club on a shoestring budget and win the pennant." \
  --goal-type win_pennant \
  --pts-limit 3000 \
  --year-pool any \
  --replaces-pool worst_record \
  --category budget_cap
```

Then produce a live instance immediately instead of waiting for Monday. `rotate` only fills a
category that has no live challenge, so to force *this specific* template use `instance`:

```bash
showdown_bot challenges instance small-budget-pennant
```

### Options

| Option | Required | Notes |
|--------|----------|-------|
| `--slug` | yes | Unique short id, e.g. `small-budget-pennant`. |
| `--title` | yes | Display title. |
| `--description` | yes | Flavor text on the challenge card. |
| `--goal-type` | yes | See goal types below. |
| `--min-wins N` | when `--goal-type min_wins` | Win total the player must reach. |
| `--beat-team-abbr ABBR` | when `--goal-type beat_team_record` | Club (e.g. `NYY`) whose win total must be beaten **in the same simulated season**. The generator will never hand the player that club. |
| `--pts-limit N` | no | Team budget cap. Omit for no cap. |
| `--roster-size N` | no (default 25) | Minimum roster size to take the challenge on, and the size a challenge "New Team" is pre-built at. **Must be ≥ 22** (9 fielders + 5 SP + 5 RP + 3 bench). |
| `--year-pool` | no (default `any`) | `any` \| comma list `1998,2001,2004` \| `random_range:1977,2024`. Years before **1975** have no full archive card coverage and are skipped. |
| `--replaces-pool` | no (default `any`) | `any` (random club that played that year) \| `worst_record` (the year's worst club) \| comma list of abbrs (first one that actually played that year wins; franchises relocate/rename across eras). |
| `--player-filters` | no | JSON object restricting eligible players, same shape as a team's `player_filters` (`min_year`/`max_year`/`organization`/`league`/`team`/`hand`). E.g. `'{"team": ["NYM", "NYY"], "hand": ["L"]}'`. |
| `--category` | no (default `themed`) | `legendary` \| `budget_cap` \| `themed`. Drives the list's accent color **and the rotation pool** — one live challenge per category at a time, so this is the lever that controls how often a template comes up. The goal/cap/filters still do the gameplay work. |
| `--inactive` | no | Create it disabled; `rotate` skips it (but `challenges instance <slug>` still works on it, with a notice). Re-enable by flipping `active` in the DB. |
| `--env` | no (default `dev`) | See "Which database?" above. |

### Goal types

Evaluated in `api/sim.py::_challenge_passed()` against the played season:

| `goal_type` | Passes when | Extra flag |
|-------------|-------------|------------|
| `made_playoffs` | team made the postseason | — |
| `win_division` | `division_rank == 1` | — |
| `win_pennant` | won the league championship round (one step before the WS) | — |
| `win_world_series` | won the World Series | — |
| `min_wins` | `wins >= min_wins` | `--min-wins` |
| `beat_team_record` | `wins >` the target club's wins that same season | `--beat-team-abbr` |

### More examples

```bash
# Division crown, any year, worst club
showdown_bot challenges create-template --slug take-the-division --title "Division Crown" \
  --description "Take over a real club and finish first in your division." \
  --goal-type win_division --pts-limit 4000 --year-pool any --replaces-pool worst_record

# 90 wins, locked to 1998
showdown_bot challenges create-template --slug classic-90-wins --title "90-Win Season" \
  --description "Build a 1998 club and hit 90 wins." \
  --goal-type min_wins --min-wins 90 --pts-limit 4500 --year-pool 1998 --replaces-pool any

# Themed player pool: only lefty Mets/Yankees
showdown_bot challenges create-template --slug lefty-subway --title "Lefty Subway Series" \
  --description "Only lefties from the Mets or Yankees allowed." \
  --goal-type made_playoffs --player-filters '{"team": ["NYM", "NYY"], "hand": ["L"]}'

# Beat an iconic club in its own season
showdown_bot challenges create-template --slug dethrone-27-yankees --title "Dethrone the '27 Yankees" \
  --description "Take over another 1927 club and finish with more wins than Murderers' Row." \
  --goal-type beat_team_record --beat-team-abbr NYY --category legendary \
  --year-pool 1927 --replaces-pool worst_record
```

---

## `challenges rotate`

The scheduled command — advances the weekly rotation.

```bash
showdown_bot challenges rotate [--env dev] [--prune-after-days 30]
```

1. Prunes instances that expired more than `--prune-after-days` days ago (safe anytime — `sim_season.challenge_instance_id` is `ON DELETE SET NULL`).
2. Groups active templates by `category`.
3. For each category **with no live instance**, picks the least-recently-instanced template (never-instanced first, then oldest instance; random tie-break) and generates one instance for it. If that template can't resolve a valid year/club, it falls through to the next candidate in the pool.
4. A category whose whole pool fails to resolve prints `SKIP category '<name>'`.

Instance resolution for a chosen template:

- Resolves a concrete `year` from `year_pool` (retries up to 3 times on years with no standings data — transient MLB Stats API hiccups).
- Resolves a `replaces_abbr` from `replaces_pool` for that year, skipping the forbidden club for `beat_team_record`.
- Snapshots `pts_limit`, `roster_size`, `player_filters` onto a new instance that expires in 7 days.

Because instances live 7 days and the workflow runs weekly, each category holds exactly one live challenge and the pool rotates one step per week.

---

## `challenges instance`

The manual override — force one template live right now.

```bash
showdown_bot challenges instance <slug> [--force] [--env dev]
```

Generates one instance for that template immediately, ignoring the category gate and the rotation (and skipping the prune). Use it right after `create-template`, or to hand-pick the next challenge in a category. Works on inactive templates too (with a notice).

If the template already has a live instance, it refuses unless you pass `--force` (which then creates a second concurrent instance for it).

---

## `challenges list-templates`

```bash
showdown_bot challenges list-templates [--env dev]
```

Lists every template (active and inactive) with slug, title, category, goal type, cap, roster size, and player filters. Use it to confirm a `create-template` landed in the DB you expect.

---

## Typical workflow

```bash
# 1. Author (default env → LOGS, matches the scheduler)
showdown_bot challenges create-template --slug ... --title ... --description ... --goal-type ...

# 2. Confirm it's there
showdown_bot challenges list-templates

# 3. Make it playable now (its category may already be filled, so use `instance`, not `rotate`)
showdown_bot challenges instance <slug>

# 4. Check the frontend challenges list — the new instance should appear
```
