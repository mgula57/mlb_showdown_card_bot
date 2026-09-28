---
name: patch-notes
description: Draft user-facing patch notes / release notes / "what's new" summaries as a Markdown file, written in plain language for non-technical hobbyist users of the app rather than developers. Use this whenever the user asks to write, draft, or generate patch notes, release notes, a changelog, or a "what's new" summary — including requests like "write up what changed for users", "summarize this release for the app", or "draft notes for the 4.4 release" — even if they don't say "patch notes" explicitly. Pulls the underlying changes from git history and translates them into short, benefit-first bullets a card-collecting hobbyist would actually want to read, not a technical diff.
---

# Patch Notes

Turn a range of commits into a short, plain-language Markdown summary of what changed —
written for the people who use the app to build cards and run simulations, not for other
developers. The output is a Markdown document, not code. Don't edit any frontend
components as part of this skill.

## Why this needs its own pass

A commit log and a diff describe *how* the code changed. A hobbyist opening the app doesn't
care about that — they care what they can now do, or what got better, described the way a
teammate would casually tell them about it. Most raw commit messages are useless for this
directly (`Fix pitcher HBP dupes`, `Update leaders CLI endpoint`) and need translating, and a
good chunk of any given commit range is invisible to a user entirely (refactors, tests, CI,
internal renames) and should be left out rather than dressed up.

## Workflow

**1. Establish the range.**
Releases are developed on a branch (e.g. `update/4.4--Team-Builder`) and merged to `master`,
so for an unreleased branch the range is `git log --no-merges master..HEAD`. Commits since the
last tag (`git tag --sort=-creatordate | head -1`) is the wrong default there, because the
branch merges `master` back in and picks up already-released patches. Use the last tag only
when drafting notes from `master` itself. If the user names a branch, PR, version range, or
"since X", use that instead. If it's ambiguous, ask — getting the range wrong means either missing real changes or
padding the notes with stuff nobody asked about.

**2. Read the actual changes, not just messages.**
`git log --oneline <range>` gives you the headline list, but commit messages in this repo
range from clear to cryptic. For anything non-obvious, `git show` or `git diff` the commit to
see what actually changed before deciding whether/how to describe it. Group related commits
that land as a single user-visible change (e.g. three commits fixing the same feature) into
one bullet rather than three.

**3. Filter for what a user would actually notice.**
Keep: new features, new pages/tabs, meaningfully changed behavior, UI changes, fixed bugs that
users would have hit and noticed. Drop: refactors, renames, test changes, CI/tooling, internal
API changes, performance work with no visible effect, dependency bumps. When a commit is
ambiguous (could be internal-only, could be user-visible), check the diff before guessing —
and if it's still unclear whether it's worth including, ask rather than padding the notes or
silently dropping something that mattered.

**4. Write each bullet to editorial guidelines.**
This is the part that actually makes these "for a non-technical audience" instead of a raw
changelog:

- **No internal vocabulary.** Nothing about components, functions, endpoints, tables,
  "refactored," "migrated," "backend/frontend" — describe the user-visible result only.
- **Lead with the verb or the benefit, not the mechanism.** Say what changed for the user, not
  how it was built. "Autofill completes your lineup, rotation, and bullpen in one click," not
  "Implemented bullpen slot-weighting for autofill."
- **One idea per bullet**, short enough to read at a glance — a sentence, not a paragraph.
  There's no hard width limit in a Markdown doc (unlike the in-app banner text below), but
  brevity is still the point: if a bullet needs two sentences, it's probably two bullets.
- **Concrete over vague.** "Regress small sample sizes toward replacement level for more
  realistic stats" beats "Improved stats accuracy." If you can name the specific thing that
  got better, name it.
- **This is a highlights reel, not a full changelog.** Small or narrow bug fixes are fine to
  group into one line ("Fixed a handful of small bugs in the game simulator") or skip
  entirely if truly minor. Don't manufacture a bullet out of nothing just to look thorough.

For tone calibration, this repo already ships user-facing copy in the `WhatsNewBanner`
component (`frontend/src/components/shared/WhatsNewBanner.tsx`), used per-page in
`Home.tsx`, `CustomCardBuilder.tsx`, `TeamBuilder.tsx`, and `Seasons.tsx`. Skim a live
`features={[...]}` array there before writing if you want a feel for the house voice — real
examples like "Simulate a full 162 game season with your team" or "Revamped live games - take
over a game mid-way through and simulate the rest" are a good register to match. Don't edit
those files, though — they're a separate, disabled-by-default in-app banner mechanism, not the
target of this skill.

**5. Group and format.**
Match the house format (this is a real past example from this project, `4.11 Release`):

```markdown
## 4.11 Release — 2026 Live Seasons
_Released 2026-04-22 · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v4.11)_

This release focuses on Minor League card support, an enhanced live game companion, 2026 season tracking, and bug fixes stemming from the migration to MLB's API.

### Live Game Companion
The live game companion lets you follow any regular season game live using what you know best — MLB Showdown cards!
- Combines live MLB box score tracking with MLB Showdown cards
- Now uses 2026 cards that update live throughout the game
- Track which players rose or fell based on their performance
- Shows cards for the live pitcher vs. hitter matchup

### Season Tracking
Use the `Seasons` tab to follow standings, live games, rosters, and leaders with the context of MLB Showdown cards.
- Added a `Leaders` tab showing cards for live hitting and pitching leaders
- Updated the `Teams` tab to display live rosters and cards with PTS trends
- Added `Today's Games` on Showdown Bot's home page, letting users quickly view a banner of game box scores and WHIP/OPS leaders
- Improved load times

### Bug Fixes
- Fixed handedness for pitchers with a different batting hand (MLB API only)
- Enabled 2026 players in the search box
```

The pieces to reproduce:
- **Title**: `## <version> Release — <short subtitle>`, where the subtitle names the release's
  headline feature (it becomes the GitHub release name too). Under it, a status line:
  `_Unreleased_` while drafting, replaced with the `_Released <date> · [GitHub release](<url>)_`
  line once the version is tagged and published.
- **Intro paragraph**: one sentence right under the title, "This release focuses on
  <theme>, <theme>, and <theme>." Name the 2-4 headline areas the release actually touches —
  don't force a theme that isn't there. Skip this paragraph entirely for a small release with
  only one area or only fixes.
- **Per-area sections** (`### <Area Name>`): a short, human name for the area — often matching
  an actual tab/page name in the app. Each optionally opens with one plain sentence explaining
  what the area is or does (skip it if the area is self-explanatory or was already covered by
  the intro), then a flat bullet list of the specific, concrete changes in that area. Wrap
  actual UI element names — tab labels, dropdown names, button text — in backticks (`` `Seasons`
  tab``, `` `League` dropdown``) since that's what the user sees on screen and helps them find
  the thing being described.
- **`### Bug Fixes`** last, always a flat list, no intro sentence. Slightly more license here to
  be specific/technical in a way a user can still recognize ("(MLB API only)" tells a user which
  data source it affects) — but still no internal code vocabulary.

For a small release that doesn't span multiple areas, drop the section headers and intro
paragraph and just use `## <version> Release` followed by a flat bullet list (plus `### Bug
Fixes` if relevant) — don't force the multi-section shape onto a one-feature release.

Pull the version number from `pyproject.toml`'s `version` field unless the user gives one.

**6. Save the file.**
`PATCH_NOTES.md` at the repo root is the running history of every release since 3.9.2, newest
first, with releases separated by `---`. Insert the new version's section right below the file's
`# Showdown Bot Patch Notes` header and intro line, above the previous newest release. If a
section for this version already exists (an earlier draft), update it in place instead of adding
a second one, and keep any wording the user has edited by hand. Never rewrite past releases: they
are a record of what was actually shipped. If the user names a different destination (a specific
path, or "just show me the text"), use that instead.

The file is committed with the release PR, so the notes ship alongside the code they describe.
The same section is pasted into the GitHub release for the version tag
(https://github.com/mgula57/mlb_showdown_card_bot/releases).

**Finalizing for release.** When the user says the release is going out (e.g. "finalize the 4.4
notes", "we're releasing today", or opening the release PR), replace that version's
`_Unreleased_` line with:

```markdown
_Released <today's date, YYYY-MM-DD> · [GitHub release](https://github.com/mgula57/mlb_showdown_card_bot/releases/tag/v<version>)_
```

Fill this in before the release PR merges, so no follow-up PR is needed. The tag URL is
predictable from the version, and the link goes live once the user tags and publishes the release
after merging. Then remind them to tag it with exactly `v<version>` so the link resolves, and give
them the section's text (without the status line) to paste into the GitHub release.

**7. Show the draft before finalizing.**
This is a writing task — surface the drafted bullets for review before or right after writing
the file, since wording is exactly the kind of thing worth a quick pass. If the user asks for
direct output without review, skip this and just write it.

## A quick nudge, not a requirement

If this looks like an actual version release (not just a draft), it's worth mentioning that
`pyproject.toml`'s `version` field may need bumping to match — that's outside this skill's job,
just flag it once.
