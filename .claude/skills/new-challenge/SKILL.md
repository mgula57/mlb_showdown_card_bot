---
name: new-challenge
description: Come up with new Team Challenge templates (the weekly "take over a real club and hit a goal" scenarios), starting by suggesting eras based on what the existing templates already cover, then authoring the template into the DEV database (DATABASE_URL_LOGS) for testing before promoting it to PROD (DATABASE_URL_ARCHIVE), and finally building the week's socials post (a key-player card stack over the challenge menu). Use when asked to brainstorm, design, add, or ideate new challenges or challenge templates, or to make the socials post for this week's challenges.
---

# New Challenge

Ideate a new Team Challenge template, test it in DEV, then promote it to PROD. Background on what a
template is, its options, and the goal types: [`CHALLENGES.md`](../../../mlb_showdown_bot/cli/commands/CHALLENGES.md).
Validation and instance generation live in `core/simulation/challenge_generator.py`; always go
through the `showdown_bot challenges` CLI rather than writing SQL.

## Which database is which

| Stage | `--env` | DB | Purpose |
|-------|---------|----|---------|
| Test  | `dev` (CLI default) | `DATABASE_URL_LOGS` | Author + play-test here first. |
| Live  | `prod` | `DATABASE_URL_ARCHIVE` | Where the user's established challenges are. Promote here only after the user signs off. |

(`CHALLENGES.md` calls LOGS "production" because the weekly `rotate` workflow runs with no `--env`.
The user treats LOGS as the test DB and ARCHIVE as prod. Follow the user, and don't "fix" this
unprompted.)

Every CLI command echoes `Using --env X (DATABASE_URL_...)` as its first line; check it.

Python lives in the repo `.venv`: run `showdown_bot ...` and scripts as `.venv/bin/showdown_bot` /
`.venv/bin/python` from the repo root. Never start the Flask server.

## Step 1: Suggest eras

1. Run the coverage report (read-only, queries both DBs):

   ```bash
   .venv/bin/python .claude/skills/new-challenge/scripts/era_coverage.py
   ```

   It maps every active template's year span onto the game's `Era` enum (`core/card/sets.py`) and
   shows, per era, how many templates are **fixed-year** (a one-season spotlight) versus
   **rotating** (a range or `any`), plus a category x goal table. Only eras from 1975 on are
   usable (`EARLIEST_SEASON` in `challenge_generator.py`).

2. Suggest **3-5 eras (or sub-spans)** to build a new challenge around. Rank by how
   under-served they are. Weigh:
   - **Zero or few fixed-year templates** means no spotlight season there yet.
   - A thin **category mix** in that era (e.g. only budget_cap, no themed/superteam).
   - **Era character**, which should suggest a mechanic: Free Agency/80s (speed, small ball,
     pitching), Steroid/90s-00s (power, `min_chart_hr_*`, superteams), Post-Steroid (pitching
     dominance), Statcast/Pitch Clock (modern, strikeout-heavy).
   - Which **pool restrictions** would suit the era (e.g. speed in the 80s, power in the 90s-00s),
     since each challenge should force a distinct draft style.
   - `any` / wide random ranges count lightly; they don't give an era an identity.
   - Real-history hooks that make a good fixed year (famous team, rivalry, record season).

3. Present the suggestions as a short table: era, year span, what's covered now, the gap, and one
   one-line challenge seed each. Then **stop and ask which era(s) the user wants to develop**.
   Don't move to the template design until they pick.

## Design principle: keep the player pool limited

Each challenge should force a **different kind of draft** than the others, so every week feels
fresh. The main lever is a restricted player pool (`--player-filters`), not just a different
budget or goal. An unrestricted pool where the user drafts the best available cards is the
default draft; reserve it for the occasional "open" challenge (`beat-the-best`, `moneyball`).
Everything else should carry at least one filter that changes who's worth drafting.

- Existing example: `runnin-wild-1980s` uses `min_speed_hitters: 18` (A-speed hitters only, since
  speed is 10/15/20 for C/B/A).
- Filter menu (full syntax in `CHALLENGES.md`): `team`, `hand`, `organization`, `league`,
  `min_year`/`max_year`, `min_speed_hitters`, `min_fielding_*_hitters` (`_if`/`_of`/`_ca`),
  `min_chart_<cat>_hitters` / `max_chart_<cat>` (e.g. HR, SO slot counts). Use the `_hitters`
  suffix for any hitter-only rule, or pitchers (speed 10, no fielding) make the roster unfillable.
- **Filters are ANDed per player, not per position slot.** `min_fielding_if_hitters` +
  `min_fielding_of_hitters` together only pass hitters rated at *both* an infield and an outfield
  position (1968: 21 of 333 hitters at >=1), which is unfillable. A single group filter alone
  (e.g. `_if` only) also drops every OF/C-only hitter. For a "good defense" theme use the combined
  `min_fielding_hitters` (best rating at any position); to scope a rule to one kind of player use a
  suffix: `_hitters` (pitchers pass) or `_catchers` (non-catchers pass, e.g. `max_fielding_ca_catchers: 4`
  for weak-armed catchers). A per-IF/OF-position rule doesn't exist yet.
- To check fillability, call `PostgresDB(is_archive=True).fetch_card_list(filters={'min_year': y,
  'max_year': y, 'limit': 5000, **filters})` (keep `limit` <= 5000, bigger falls back to 50 rows)
  and dedupe on `r['id']` (one row per set per player).
- **Required players:** `required_players` in `player_filters` puts specific players on the roster
  (pre-populated at the named position, enforced at launch). See `CHALLENGES.md`. Good for a
  one-week spotlight ("M&M Boys": Mantle CF, Maris RF). Budget their points into the cap, and use a
  fixed year pool.
- Themes that restrict well: one trait (speed, power, defense), one handedness, a division or
  rivalry (`team` list), a narrow window (`era_lock_years`), or a cap on a trait (e.g. few
  strikeouts, low HR).
- **Before proposing a filter, check it's fillable**: the pool must still hold at least a full roster
  (22+: 9 fielders, 5 SP, 5 RP, 3 bench) across every year the template can land on. Too tight and
  the challenge is unplayable; too loose and it's a normal draft. When unsure, count cards that
  pass the filter for the narrowest year in the pool.
- Compare against the filters on existing templates (the report prints them via `--json`) and pick
  a restriction **no other active challenge uses**, so the weekly rotation doesn't repeat a draft style.

## Step 2: Design the template (after the user picks an era)

Propose **one template idea per category** for the chosen era (`budget_cap`, `legendary`,
`superteam`, `themed`), so the user can see the whole week's menu and pick one or several. Every
category's idea gets its own pool theme/filter (see the principle above), not just `themed`:
category sets the goal/cap flavor, the filter sets the draft style, and a different restriction
per idea keeps the four from feeling alike. Present them in one table, each with: `slug`, `title`, `description`,
`category`, `goal_type` (+ `--min-wins` / `--beat-team-abbr`), `--pts-limit`, `--year-pool`,
`--replaces-pool`, and any `--player-filters`. Calibrate against the existing rows the report
printed (budget_cap ~5000-5500, legendary ~6250-6500, superteam 7000-9000, themed ~6000; superteam
`min_wins` 120-135). Check that the slug is unique in both DBs and that the player-filter restriction is distinct. Let the user choose or tweak one or several.

Each template is effectively a **one-week challenge**, not a reusable rotating template. Design it
as a specific scenario: a fixed `--year-pool` (one season, or a short span for the theme),
`min_year`/`max_year` hardcoded in `--player-filters`, and a specific `--replaces-pool` club when
the story calls for it. Don't reach for `era_lock_years`, `any`, or wide `random_range` pools to
make a template reusable; that only matters if a template is meant to recur. Give it a distinct
slug and title for its week. The coverage report counts a template as fixed-year when its span is
one season; treat short spans the same way when judging how much of an era is "spotlighted".

## Step 3: Create in DEV

```bash
.venv/bin/showdown_bot challenges create-template --slug ... --title ... --description ... \
  --goal-type ... --category ... [...]            # default env = dev (LOGS)
.venv/bin/showdown_bot challenges list-templates   # confirm it landed
.venv/bin/showdown_bot challenges instance <slug>  # make it playable now so the user can test
```

Hand the user the slug and tell them to play it on their dev frontend. Iterate on feedback
(difficulty of the cap/goal, whether the roster is fillable under the filters, club resolution). To
change a template, ask before deleting; the admin UI at `/teams/admin/challenges` can edit.

## Step 4: Promote to PROD (only on explicit go-ahead)

Writing to ARCHIVE is outward-facing, so get the user's explicit confirmation in this conversation
for that specific template, even if they approved DEV. Then rerun the **exact same**
`create-template` command with `--env prod`, confirm with `list-templates --env prod`, and ask
when it should go live. Since it's a one-week challenge, the usual answer is `instance <slug>
--env prod` for that week (add `--force` only if it already has a live instance); otherwise
`rotate` picks it up in order, and being never-instanced it goes first in its category. Once its
week is over, ask whether to deactivate it (`--inactive` at creation, or flip `active` in the admin
UI), since an active template re-enters the rotation pool and will be instanced again.

## Step 5: Socials deliverable

Once the week's challenges are live, build the socials post: one 1080x1350 slide with 2-3
key-player cards fanned out beside the headline and the challenge menu below. Details are in
`CHALLENGES.md` → `challenges social`.

1. **Pick the key players (2-3).** Choose cards that sell the week's theme, one per challenge
   where you can: a challenge's required player (e.g. Mantle for M&M Boys), the poster player of
   its restriction (the fastest hitter in a speed pool, the ace of a pitching year), or the star
   of the club being chased in a `beat_team_record` goal. Each one must be a player the user can
   actually draft under that challenge's filters. Check this with `fetch_card_list` (the same
   filter call from the design principle above). Skip small-sample cameo seasons. Propose the
   picks with a one-line reason each, and let the user swap any before rendering.
2. **Render it** against the env that holds the live instances (`prod` once promoted, `dev` while
   testing). Give it a headline that names the week's theme:

   ```bash
   .venv/bin/showdown_bot challenges social --env prod --headline "Sixties Week" --start-date 2026-10-19 \
     --card-id 1961-mantlmi01 --card-id 1965-mayswi01 --card-id 1966-koufasa01
   ```

   If you leave out `--card-id`, it auto-picks (required players first, then each challenge's
   top-points eligible card). That's fine as a draft, but hand-picked cards tell the story better.
3. **Review the output.** Look at `challenges_1.png` yourself (Read the image) before you hand it
   over. Check for clipped or overflowing text, stickers covering each other, a card that failed
   to render (`SKIPPED CARD` in the output), and a card tagged to the wrong challenge. Then give
   the user the output folder, which holds the PNG slide, the PDF, the HTML, and full-size card
   renders in `cards/` for posting on their own.
