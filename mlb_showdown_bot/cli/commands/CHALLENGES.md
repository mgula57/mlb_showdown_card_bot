# Setting up Team Challenges

CLI: [`challenges.py`](challenges.py) — registered as `showdown_bot challenges`.

**Admin UI:** the same operations (template CRUD, "generate instance now", "run rotation now")
live at `/teams/admin/challenges` — reached via the "Manage templates" link in the Team
Challenges tab header (admins only). Frontend: `AdminChallengesView` /
`ChallengeTemplateForm` in `frontend/src/components/team_builder/sim/admin/`. Backend:
[`api/admin_challenges.py`](../../api/admin_challenges.py) (`/api/admin/challenges*`,
`require_admin`). Both the CLI and the API run through
[`core/simulation/challenge_generator.py`](../../core/simulation/challenge_generator.py) — the
one source of truth for validation and instance generation.

A **Team Challenge** is a weekly "take over a real club and hit a goal" scenario. There are two layers:

| Layer | What it is | How it's made | Lifetime |
|-------|-----------|---------------|----------|
| **Template** | Hand-authored content: the goal, budget cap, player pool, year/club pools. | You, via `challenges create-template` or the admin UI. | Permanent (until you deactivate it). |
| **Instance** | A concrete playable challenge: one real `year` + `replaces_abbr` club resolved from a template's pools, with `pts_limit` / `roster_size` / `player_filters` snapshotted onto it. | The scheduler, via `challenges rotate` (or `challenges instance <slug>` by hand). | 7 days, then pruned 30 days after expiry. |

`rotate` keeps exactly **one live instance per category** (`legendary` / `budget_cap` / `superteam` / `themed`) — each category is a rotation pool of templates, and every cycle the least-recently-used template in a category becomes that week's challenge, but only if the category has no live instance already. The frontend challenges list shows the live instances; players build a team (min `roster_size`, under `pts_limit`, matching `player_filters`), sim the season, and pass/fail against `goal_type`.

So: write as many templates per category as you like — they queue up and take turns. Four categories → four live challenges at any time.

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
| `--year-pool` | no (default `any`) | `any` \| comma list `1998,2001,2004` \| `random_range:1977,2024`. Years before **1920** have no full archive card coverage and are skipped. |
| `--replaces-pool` | no (default `any`) | `any` (random club that played that year) \| `worst_record` (the year's worst club) \| comma list of abbrs (first one that actually played that year wins; franchises relocate/rename across eras). |
| `--player-filters` | no | JSON object restricting eligible players, same shape as a team's `player_filters` (`min_year`/`max_year`/`organization`/`league`/`team`/`hand`), plus `min_fielding`/`max_fielding` (best rating across every position the card is rated at - add an `_if`/`_of`/`_ca` suffix, e.g. `min_fielding_if`, to scope it to just infield, outfield, or catcher) and `min_chart_<category>`/`max_chart_<category>` (chart slot count, e.g. `min_chart_hr`). Append `_hitters` to any key (e.g. `min_speed_hitters`, `min_fielding_if_hitters`, `min_chart_hr_hitters`) to apply it to hitters only - pitchers pass automatically. Use this for any hitter-themed rule: pitchers all have speed 10 and no fielding ratings, so a plain `min_speed`/`min_fielding_*` would make the roster unfillable. Append `_catchers` instead (e.g. `max_fielding_ca_catchers`, `min_fielding_ca_catchers`) to apply it to catchers only - anyone not rated at catcher passes - for a catcher-arm rule that doesn't wipe out every non-catcher. E.g. `'{"team": ["NYM", "NYY"], "hand": ["L"]}'`. Also accepts `era_lock_years` (int) — see below. |
| `--category` | no (default `themed`) | `legendary` \| `budget_cap` \| `superteam` \| `themed`. Drives the list's accent color **and the rotation pool** — one live challenge per category at a time, so this is the lever that controls how often a template comes up. The goal/cap/filters still do the gameplay work. |
| `--inactive` | no | Create it disabled; `rotate` skips it (but `challenges instance <slug>` still works on it, with a notice). Re-enable by flipping `active` in the DB. |
| `--env` | no (default `dev`) | See "Which database?" above. |

### Goal types

Evaluated in `api/sim.py::_challenge_passed()` against the played season:

| `goal_type` | Passes when | Extra flag |
|-------------|-------------|------------|
| `made_playoffs` | team made the postseason | — |
| `win_division` | `division_rank == 1` | — |
| `win_pennant` | reached the World Series (any format, incl. pre-1969 WS-only) | — |
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

### Required players

`--player-filters '{"required_players": [{"bref_id": "mantlmi01", "name": "Mickey Mantle", "position": "CF"}, {"bref_id": "marisro01", "name": "Roger Maris", "position": "RF"}]}'`
forces specific players onto the roster. `position` is one of `C 1B 2B 3B SS LF CF RF DH` (one player per position); `name` is display-only.
A challenge's "New Team" is created with those players already on the roster at that position (their `year` card in the
team's Showdown set), the card shows "Must roster ...", and `start_season_sim` / the eligible-teams picker reject a roster
missing any of them (bench counts). It's a convention key, not a card filter: the card queries and `PlayerFilterSet` skip
it. It still counts against `--pts-limit`, so size the cap with their points in mind. Use it with a fixed `--year-pool`
(the card is `{year}-{bref_id}-{set}`).

### Era-locking a rotating year_pool

`--player-filters '{"era_lock_years": 5}'` locks eligible players to within 5 years of whatever
year the *instance* ends up with — useful for a template whose `--year-pool` isn't a fixed year
(e.g. `budget_cap`'s `any`/`random_range`), where you can't hand-author `min_year`/`max_year`
because the year isn't known until generation time. At instance-creation time the generator
consumes `era_lock_years` and replaces it with a concrete `min_year`/`max_year` window on the
*instance's* snapshot — the template itself stays year-agnostic and can be reused indefinitely.

For a template with a fixed `--year-pool` (e.g. `legendary`), just hardcode `min_year`/`max_year`
directly instead — the year is already known at authoring time, so there's nothing to resolve.

```bash
# Budget cap challenge, era-locked to whatever year gets rolled each time it's instanced
showdown_bot challenges create-template --slug shoestring-era-locked --title "Shoestring, In Era" \
  --description "Build a shoestring roster from players active around that season." \
  --goal-type win_pennant --pts-limit 3000 --year-pool any --replaces-pool worst_record \
  --player-filters '{"era_lock_years": 5}' --category budget_cap
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

## `challenges social`

Builds the socials deliverable for the live challenges: one 1080x1350 (4:5) slide. Up top, the
headline sits beside a fanned stack of 2-3 key-player cards that fit the theme, each with a sticker
naming its challenge. Below that is the week's menu (each challenge's club, goal, budget and
rules).

```bash
showdown_bot challenges social [--env dev] [--headline "Sixties Week"] [--subhead "..."] \
  [--start-date 2026-10-19] [--slug <slug> ...] [--card-id 1961-mantlmi01 ...] [--set 2001] [--out DIR] [--image-format png|jpg|none]
```

- **Challenges:** every live instance in `--env` (category order), or only the `--slug`s given.
- **Cards:** `--card-id` (repeatable, max 3) as `{year}-{bref_id}` (the `--set` is appended) or
  the full `{year}-{bref_id}-{set}`. Each card is tagged with the first challenge whose season it
  fits. If you don't pass any, the command picks one per challenge, round-robin: required players
  first, then the top-points non-small-sample card that passes that challenge's filters.
- **Start date:** `--start-date YYYY-MM-DD` sets the slide's "Week of" date and the default output
  folder name. It defaults to today, so pass it when you build the post ahead of (or after) launch.
- **Output** (default `sim_output/challenges_{start date}/`): `challenges.html` (self-contained),
  `challenges.pdf`, `challenges_1.png` (the slide), and the full-size card renders in `cards/`. The PDF and PNGs need headless Chrome (set `CHROME_PATH` if it isn't
  found). Without it they're skipped with a notice.

It renders through the same `SocialSheetReport` base
([`core/simulation/social_report.py`](../../core/simulation/social_report.py),
`templates/_social_base.html.j2`) as the postseason batch summary.

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
