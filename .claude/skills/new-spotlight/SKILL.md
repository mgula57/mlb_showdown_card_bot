---
name: new-spotlight
description: Come up with and publish a new Home page Spotlight (the curated card shelf under "Cards Worth Building" in frontend/src/components/Home.tsx), e.g. MVPs from a decade, themed sets like Negro League Legends, or players in the news (a World Series champion club, an all-time franchise team, award winners, retirements, Hall of Fame classes). Suggests timely themes, finds real cards that fit, then publishes to DEV for a preview before PROD. Use when asked to brainstorm, pick, refresh, update, or publish a spotlight, or for "what should we feature on the home page".
---

# New Spotlight

Pick a theme, find the cards, preview in DEV, publish to PROD.

## How a spotlight works

- `showdown_bot database spotlight -p <ids> -m "<reason>" -e <env>` calls
  `PostgresDB.publish_new_spotlight` (`core/database/postgres_db.py`). For each card id it copies
  `card_data` for **every Showdown set** from `internal.dim_card` into `public.card_spotlight`,
  with `sort_index` = the id's position in `-p` and the same `spotlight_reason` on every row.
- Home (`Home.tsx`, `cardShelves.spotlight`) fetches `POST /api/cards/spotlight` for the viewer's
  set: the newest publish, ordered by `sort_index`. The shelf's description line is
  `spotlight_reason`, so write the message as **one full sentence** that names the theme and why
  it is worth a look (e.g. `Johnny Bench, Joe Mauer and Buster Posey lead the catchers who were named
  MVP.`), not a bare label like `1980s AL MVPs`. Keep it to one sentence every time.
- Home requests `CARD_SHELF_SIZE` (8) cards, so **only the first 8 ids show**. Pick up to 8
  and put the headliner first; the first few are visible without scrolling. Extra ids publish but stay hidden.
- The API caches each set for 8 hours (`_HOMEPAGE_CACHE_TTL` in `api/card_db.py`). A new publish
  shows up after that, or once the Flask server restarts.

## Databases

| Stage | `-e` | DB | Purpose |
|-------|------|----|---------|
| Preview | `dev` (CLI default) | `DATABASE_URL_LOGS` | The local Flask app reads this one, so the user can see the shelf. The table is created on first publish. |
| Live | `prod` | `DATABASE_URL_ARCHIVE` | Real past spotlights live here. Publish only after the user signs off. |

Run Python as `.venv/bin/python` / `.venv/bin/showdown_bot` from the repo root. Never start Flask.
Don't write SQL to insert or delete spotlight rows; go through the CLI.

## Card ids

Card ids are season-specific (`card_bot.id` = `dim_card.player_id`):
- Through 2025: `<year>-<bref_id>`, e.g. `1982-yountro01`. Negro League players often end in `99` (`1943-gibsojo99`).
- 2026 on (MLB API seasons): `<year>-<mlb_id>`, e.g. `2026-592885` (Yelich).

Use one season per player, usually their best or most on-theme year. Don't repeat a player.

## Step 1: Suggest themes

1. See what has run, so a theme doesn't repeat:

   ```bash
   .venv/bin/python .claude/skills/new-spotlight/scripts/spotlight_tools.py history
   ```

2. Check what's in the news **as of today's date** with WebSearch (postseason results, award
   announcements, trades and signings, retirements, Hall of Fame votes, milestones, deaths of
   former players). Don't rely on memory for current events.

3. Suggest **4-6 themes** across these families, timely ones first:
   - **Awards by era**: `MVP-1` / `CYA-1` / `RoY-1` winners for a decade, league, or position
     (e.g. `1990s NL Cy Youngs`, `Catcher MVPs`).
   - **Themed**: Negro League Legends, Hall of Fame class, `Iron Men` (high G/IP), speedsters,
     unanimous MVPs, Triple Crown seasons, rookies who won MVP.
   - **In the news**: the World Series champion club's current roster, that franchise's all-time
     best seasons (e.g. `All-Time Brewers`), award finalists, a retiring star's best seasons, a
     player chasing a record, big free-agent signings (see `Recent Offseason Movers`).
   - **Calendar hooks**: Opening Day, Jackie Robinson Day (Apr 15), Black History Month (Feb,
     Negro Leagues), HOF induction (July), trade deadline, postseason, awards week (Nov), anniversaries.

   For each theme give: a one-sentence description, why now, and 6-8 candidate players. Then **stop and ask
   which theme the user wants**.

## Step 2: Find the cards

Query `card_bot` (PROD) with Card Explorer filters. Results are sorted by bWAR and deduped to one
row per card id:

```bash
.venv/bin/python .claude/skills/new-spotlight/scripts/spotlight_tools.py find '<filters json>' [--limit 60]
```

Useful filter keys (see `_card_list_filter_clauses` in `postgres_db.py`):

| Key | Example | Notes |
|-----|---------|-------|
| `awards` | `["MVP-1", "CYA-1"]` | Codes are `<AWARD>-<vote rank>`; `-1` = won. `MVP-*` = any vote. Also `AS`, `GG`, `SS`. Rookie of the Year shows up as both `RoY-1` and `ROY-1`, so pass both. |
| `lg_id` | `["AL"]` | Season league: AL / NL, or a Negro League code. |
| `pro_league` | `["NNL","NN2","ECL","NAL","NSL","ANL","EWL"]` | Negro Leagues. Others: `AA`, `UA`, `PL`, `FL`. |
| `team` | `["MIL"]` | Season team abbreviation. Franchises that moved or were renamed have several codes (1969 Pilots are `SEP`), so look up older ones. |
| `min_year` / `max_year` | `1980` / `1989` | |
| `is_hof` | `["true"]` | |
| `player_type` | `"PITCHER"` / `"HITTER"` | |
| `search` | `"yount"` | Name search. |
| `include_small_sample_size` | `["false"]` | Drop small-sample seasons. |

For current-roster themes (e.g. champions), use the newest season (`min_year` = current year, `team`).

Pick up to 8 cards (order matters, best first). Try for a mix of hitters and pitchers and of eras, unless
the theme is one kind of player. Then check each id has a card in every set:

```bash
.venv/bin/python .claude/skills/new-spotlight/scripts/spotlight_tools.py check <id,id,...> --env dev
.venv/bin/python .claude/skills/new-spotlight/scripts/spotlight_tools.py check <id,id,...> --env prod
```

A `MISSING` set means viewers on that set see fewer cards. Swap the id, or flag it to the user. DEV's
`dim_card` is smaller than PROD's, so an id missing only in DEV is fine for PROD.

## Step 3: Preview in DEV

Show the user the final list (order, id, name, year, team, points) and the reason text, then:

```bash
.venv/bin/showdown_bot database spotlight -e dev -p "<id1>,<id2>,...,<id8>" -m "<reason>"
```

Ask the user to restart their Flask server (or wait for the cache) and check the Home shelf.

## Step 4: Publish to PROD

Only after the user approves the preview:

```bash
.venv/bin/showdown_bot database spotlight -e prod -p "<same ids>" -m "<same reason>"
```

Confirm with `spotlight_tools.py history`: the new reason should be on top.
