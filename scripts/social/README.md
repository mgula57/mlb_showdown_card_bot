# Random Card Posts to X

A GitHub Action (`.github/workflows/social_post.yml`) posts a random ShowdownBot card to X three times a day: the card image, alt text, and a short caption built from the card's real data.

## How it works

1. **Pick:** `POST /api/cards/search` with `sort_by: random()` for a random set, skipping small-sample seasons and any player-season (`{bref_id}-{year}`) posted in the last 60 days. The draw is lightly weighted toward Hall of Famers, award winners, and high point values.
2. **Render:** `GET /api/cards/card` gets the full card, then `POST /api/build_image_for_card` renders it on the server. The image is downloaded from `/static/output/...`. All card logic stays in the Flask app.
3. **Caption:** a random template (hitter or pitcher) is filled with points, OB/Control, speed or IP, and the real stat line or one notable stat. The caption has no link, because X charges ~13x more for posts containing a URL.
4. **Post:** tweepy uploads the image with alt text, creates the post, then writes a row to `internal.social_post_log`. If the post succeeds but the log write fails, the job fails with the post id in the log.

| File | Purpose |
|---|---|
| `post_card.py` | Entry point (dry run by default) |
| `pick_card.py` | Random selection, exclusion, retries |
| `caption.py` | Caption templates + alt text |
| `showdown_api.py` | showdownbot.com API client |
| `x_poster.py` | X upload + post (tweepy) |
| `post_log.py` | `internal.social_post_log` reads/writes |

## Setup

### 1. Post log table

Build it in dev, then prod:

```bash
showdown_bot database build_social_post_log_table --env dev
showdown_bot database build_social_post_log_table --env prod
```

RLS is enabled with no policies, and the table is in the `internal` schema, so only the DB owner/service role can access it.

### 2. X developer app

1. Create a project and app at [developer.x.com](https://developer.x.com) while signed in as the account that will post.
2. Under **User authentication settings**, enable OAuth 1.0a with **Read and write** permissions. Regenerate the access token after changing permissions.
3. Copy the API Key/Secret and the Access Token/Secret.
4. Billing: new developer accounts are pay-per-use (no free tier since Feb 2026). At the time of writing a post costs ~$0.015 without a URL, and ~$0.20 with one. 3 posts/day ≈ 90/month ≈ $1.35/month plus media requests. Load credits in the developer portal and check current rates on [X's pricing page](https://docs.x.com/x-api/getting-started/pricing).

### 3. GitHub secrets

Repo → Settings → Secrets and variables → Actions:

| Secret | Notes |
|---|---|
| `X_API_KEY` | App API key (consumer key) |
| `X_API_SECRET` | App API secret |
| `X_ACCESS_TOKEN` | Posting account's access token |
| `X_ACCESS_TOKEN_SECRET` | Posting account's access token secret |
| `DATABASE_URL_ARCHIVE` | Prod Postgres URL (already used by other workflows) |

Optional repository **variable** `SHOWDOWN_SITE_URL` overrides the site root (default `https://www.showdownbot.com`).

## Running

Locally (dry run is the default and posts nothing):

```bash
pip install -r scripts/social/requirements.txt
python scripts/social/post_card.py                   # dry run; uses DATABASE_URL_ARCHIVE for exclusions if set
python scripts/social/post_card.py --env dev         # read exclusions from the dev DB
python scripts/social/post_card.py --live            # post for real (needs X_* env vars)
```

Options: `--days` (exclusion window, default 60), `--site-url`, `--output-dir`.

In GitHub: Actions → **Social Card Post** → **Run workflow**. `dry_run` is checked by default; uncheck it to post.

## Schedule

Cron is UTC and doesn't follow DST: `15:07`, `19:07`, `00:07` UTC = 9am / 1pm / 6pm CST in winter, 10am / 2pm / 7pm CDT in summer. Scheduled runs can start several minutes late. A `concurrency` group keeps runs from overlapping.

> **Heads up:** GitHub disables scheduled workflows in public repos after 60 days without repository activity. If posts stop, re-enable the workflow from the Actions tab (or push any commit).

## Notes

- Media upload and alt text use X's v1.1 media endpoints through tweepy (tweepy 4.x has no v2 media upload). If X retires them, only `XPoster.upload_image` needs to change.
- The search endpoint caches by payload for ~2h, so retries inside one run draw from the same sample of 50 cards. Each search also adds a row to the player-search log.
- Reposting a card after the window overwrites its log row (`UNIQUE (platform, card_key)`). The `platform` column leaves room for Bluesky/Threads later.
