# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Flask / Python)

```bash
# Run Flask dev server (from repo root)
flask --app app run --debug

# Install Python dependencies
pip install -e .

# Run a specific test script
python tests/test_sets.py
python mlb_showdown_bot/scripts/test_card_generation.py

# CLI entry point
showdown_bot --help
```

### Frontend (React / Vite)

```bash
cd frontend

npm install          # install deps
npm run dev          # dev server on :5173
npm run build        # production build
npm run type-check   # tsc type check (no emit)
npm run lint         # eslint
```

### Running both together

Flask serves the built frontend at `/` in production. In dev, run Flask on `:5000` and Vite on `:5173` — the frontend proxies API calls to `http://127.0.0.1:5000/api` when `import.meta.env.PROD` is false.

## Required Environment Variables

```
DATABASE_URL_LOGS       # PostgreSQL connection string for the logs DB
DATABASE_URL_ARCHIVE    # PostgreSQL connection string for the archive DB
SUPABASE_URL            # Supabase project URL
SUPABASE_KEY            # Supabase anon/service key
GOOGLE_CREDENTIALS      # JSON string for Google service account (Drive image uploads)
FRONTEND_ORIGIN         # CORS allowed origin (default: http://localhost:5173)
```

## Architecture

### The card generation pipeline

The core domain is in `mlb_showdown_bot/core/card/`. A card generation request flows:

1. **`app.py`** registers Flask blueprints under `/api`, including `cards_bp` which handles `POST /api/build_custom_card`.
2. **`mlb_showdown_bot/api/cards.py`** extracts form payload and calls `generate_card(**kwargs)`.
3. **`mlb_showdown_bot/core/card/card_generation.py` → `generate_card()`** is the central orchestrator. It:
   - Determines the `Datasource` (MLB_API for 2026+, BREF for older years, or MANUAL).
   - Builds a `StatsPeriod` from `stats_period_type`, `year`, `start_date`/`end_date`, and `split`.
   - Fetches and normalizes player stats into `NormalizedPlayerStats` via `PlayerStatsNormalizer`.
   - Instantiates `ShowdownPlayerCard` (Pydantic model) with all computed fields.
   - Optionally runs historical/in-season trend generation and fetches latest game boxscores.
4. **`mlb_showdown_bot/core/card/showdown_player_card.py`** is the central domain model — a large Pydantic `BaseModel` that holds every field on the card (chart, speed, defense, image metadata, etc.) and renders the final card image using Pillow.

### Stats sources

Stats fetching branches on `Datasource`:
- **MLB_API** (`mlb_showdown_bot/core/card/stats/mlb_stats_api.py`): Used for 2026+ seasons. Hits the MLB Stats API directly. Normalized via `PlayerStatsNormalizer.from_mlb_api()`.
- **BREF** (`mlb_showdown_bot/core/card/stats/baseball_ref_scraper.py`): Scrapes Baseball Reference for historical data. `SPLIT` stat period type only works here (fuzzy-matches against BREF's split tables).
- **MANUAL**: Raw stats dict passed directly in the request payload.

`NormalizedPlayerStats` is the shared intermediate format fed into `ShowdownPlayerCard` regardless of source.

### Sets and Eras

`mlb_showdown_bot/core/card/sets.py` defines `Set` (the card set: `2000`–`2005`, `CLASSIC`, `EXPANDED`) and `Era` (the statistical era a player's year falls in: e.g. `PITCH_CLOCK`, `STATCAST`). Each `Set` has a `baseline_chart` for each `PlayerType`/`Era` combination that determines the on-card stat distribution.

### Year string format

The `year` field is a flexible string parsed by `convert_year_string_to_list()`:
- `"2023"` → single year
- `"2000-2004"` → range
- `"2006+2014+2008"` → multi-year combo (e.g. Super Season)
- `"CAREER"` → all years played

### Flask API blueprints

All blueprints are registered under `/api` in `app.py`:

| Blueprint | File | Key routes |
|-----------|------|-----------|
| `cards_bp` | `api/cards.py` | `POST /build_custom_card`, `POST /build_cards` |
| `search_bp` | `api/search.py` | `GET /players/search` |
| `card_db_bp` | `api/card_db.py` | `GET /cards/search`, `/cards/card`, `/teams/data` |
| `seasons_bp` | `api/seasons.py` | `GET /seasons/list`, `/seasons/<id>/...` |
| `schedule_bp` | `api/schedule.py` | `GET /schedule`, `/game/<pk>/boxscore` |
| `splits_bp` | `api/splits.py` | `GET /splits?season=` |
| `feature_status_bp` | `api/feature_status.py` | `GET /feature_status` |

In-memory caching is done per-blueprint with `dict[str, tuple[data, datetime]]` + a `timedelta` TTL (checked manually on each request). The MLB Stats API client (`mlb_showdown_bot/core/mlb_stats_api/base_client.py`) has its own internal cache keyed by `"{endpoint}:{sorted_params}"`.

### Frontend structure

The frontend is a React 19 + Vite + Tailwind 4 SPA. API calls go through typed functions in `frontend/src/api/`. The main page of interest is the Custom Card Builder:

- **`frontend/src/components/customs/CustomCardBuilder.tsx`** — the entire card builder form. Manages all form state, triggers `buildCustomCard()`, and renders the result.
- **`frontend/src/api/mlbAPI.ts`** — typed fetch wrappers for all backend `/api` routes. Module-level `Map` caches are used for browser-session caching (e.g. `_splitsCache`).
- `FormDropdown`, `FormInput`, `FormSection`, `FormEnabler` are the reusable form primitives consumed by the builder.

### Databases

Two PostgreSQL connections (separate pools warmed at startup):
- **`DATABASE_URL_LOGS`**: Logs of card generation requests from the web UI.
- **`DATABASE_URL_ARCHIVE`**: Archive of pre-computed card stats used to skip re-scraping for historical seasons. `SPLIT` period type always bypasses the archive.

Supabase is used for auth and for uploading card images.
