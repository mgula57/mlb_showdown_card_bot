---
name: migrate-release
description: Migrate (copy, promote, push, move) a Release Builder release built in DEV (DATABASE_URL_LOGS) into PROD (DATABASE_URL_ARCHIVE) as an unpublished release owned by the same email's PROD account, or re-sync one migrated earlier. Use when asked to migrate, promote, copy, push or move a release / set / edition from dev to prod.
---

# Migrate Release

A wrapper around `showdown_bot set migrate_release <slug>`. The logic lives in
`mlb_showdown_bot/core/set_builder/release_migrator.py` (`ReleaseMigrator`). Always go through the
CLI rather than writing SQL.

## What it does

| | |
|---|---|
| Source → target | DEV `DATABASE_URL_LOGS` → PROD `DATABASE_URL_ARCHIVE` (fixed, there's no `--env`) |
| Owner | The PROD `auth.users` account with the DEV owner's email. Stops if there isn't exactly one. |
| Copied | Release settings, live editions (a working copy's content if the owner has unpublished edits), their live cards (snapshots, numbers, tags, overrides, preview ranks) |
| Not copied | Images (no rows, no files, no render), publish state, versions, likes/saves/views/comments, remix parent |
| Lands as | **Unpublished.** The owner reviews it, renders images and publishes it in PROD through the normal Release Builder flow. |
| Ids | New release and edition ids in PROD (image files sit under `releases/{release_id}/{edition_id}/`, so shared ids could let one side's cleanup delete the other's renders) |
| Re-run | Syncs into the PROD release with the same slug and owner, matching editions by slug, **only while it has never been published in PROD**. Card ids stay stable for each (edition, source card). |

Python lives in the repo `.venv`. Run from the repo root and export `.env` first:
`set -a; source .env; set +a`. Never start the Flask server.

## Steps

1. **Find the slug.** It's the `/releases/<slug>` part of the DEV link. If the user only gives a name,
   ask for the link, or look it up read-only in DEV (`SELECT slug, name, created_by FROM
   internal.releases WHERE name ILIKE ...`). Use plain autocommit SELECTs only. Never `SET` or
   `set_session` on these pooler connections.
2. **Dry run** (the default, read-only):
   ```bash
   .venv/bin/showdown_bot set migrate_release <slug>
   ```
   Show the user the plan: owner email → PROD user id, create vs. update, each edition's card count,
   which came from a working copy, and any warnings. Call out:
   - **CUSTOM cards.** They render from their embedded `card_data`, but their source id is a DEV
     custom-card log id.
   - **Remix credit dropped** (`fork_parent_id`).
3. **Get an explicit go-ahead for this release before `--apply`.** Writing to PROD is outward-facing.
   Approval for a dry run, or for an earlier release, doesn't carry over.
   ```bash
   .venv/bin/showdown_bot set migrate_release <slug> --apply
   ```
4. **Report back:** the PROD release id and link (`/release-builder/<id>`), that it's unpublished
   with no images yet, and any orphaned image paths the command printed. A re-sync that removed
   editions lists files it left in storage. Don't delete them from here: local Supabase credentials
   may point at the DEV project.

## When it refuses

| Message | What to do |
|---|---|
| No release tables in the target | PROD hasn't run `build_releases_table`. Deploying 4.5 creates them, or `showdown_bot database build_releases_tables --env prod` does. That's DDL on PROD, so ask first. |
| No account / several accounts for `<email>` | The owner has to sign up in PROD (or the duplicate needs sorting out). Don't pick an account yourself. |
| Slug taken by another user's release | Ask the user. Renaming the DEV release changes its slug only if the app regenerates it, so check before suggesting that. |
| Target release has been published | By design. Make further edits in PROD. Re-syncing could pull cards out from under teams holding them. |
| Target release was deleted (retired) | Its slug stays reserved in PROD. Ask the user how they want to proceed. |
