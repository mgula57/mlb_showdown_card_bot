---
name: review-set-build
description: Review Release Builder set-building results against the original WOTC base sets (2000-2005) - points distribution / low-point counts, command (On-Base/Control), speed, and per-position defense shape - then flag gaps and suggest point buckets or defense range tweaks in metrics.py. Use when asked to review, check, audit, or compare set builds, release builder output, or "how do the sets look vs WOTC", including after changing card formulas or defense ranges.
---

# Review Set Build

Automates the Release Builder review loop: build the current season's set for each WOTC set (2000-2005)
with that set's **Base Set blueprint**, re-run the cards through the current algorithm, and compare against
the WOTC base set the way the Edition Builder's Summary tab does ("Compare to WOTC").

## 1. Build and compare

From the repo root (needs `.env` DB access; does **not** need the Flask server):

```bash
.venv/bin/python mlb_showdown_bot/scripts/review_set_build.py --rerun \
  --buckets-file .claude/skills/review-set-build/point_buckets.json \
  -o <scratchpad>/set_review.json
```

- `--rerun` rebuilds every selected card through current code (the admin "Re-run cards" toggle). Always use it unless the user says otherwise; formula/`metrics.py` changes only show up with it.
- `-s 2001` (or `-s 2000,2001`) limits sets; `-y` changes the year (defaults to the current year).
- `-b "2001=10-100:0.08"` overrides one set's point buckets for a trial run (multiple buckets: `"2001=10-50:0.05,60-100:0.05"`).
- A run takes ~5-10s per set. Selection is deterministic, so before/after runs pick the same players.
- The JSON has every breakdown in raw form if you need more than the Markdown report.

How it matches the UI: blueprint = WOTC set size + position mix + avg points per position (`WotcSetProfile`), default weights/thresholds, plus the per-set buckets in `point_buckets.json`. WOTC counts are **scaled** to the set's size (defense is scaled within each position). Point buckets are enforced on **archived** points, so a re-run can shift points after selection. Note that in the warnings.

## 2. Review checks

Review each set in turn. Small samples are noisy (a 20-card position has ±2 cards of noise per rating), so look for real shape problems and for patterns that show up in more than one set, not single-cell noise.

**Don't trust WOTC's odd bumps.** The target is a smooth, roughly normal curve, not WOTC's exact histogram. When the WOTC chart has a bump that breaks the bell shape (two peaks, a lone spike, a dip in the middle; e.g. CF peaking at both +1 and +3), treat it as WOTC noise. Don't try to match it, and don't flag our set for lacking it. Compare against the smooth curve WOTC implies (its avg and std dev), and score shape by avg and spread rather than cell-by-cell diffs or total variation. Say so in the report when a WOTC bump drove the decision.

### 2a. Points: enough low-point players?
Focus on the **Low point cards (10-100) by player type** table.
- Flag when the set's total 10-100 count is under ~85% of WOTC scaled, or any type is ≥3 cards short.
- Fix with a point bucket. A bucket is a **per-type floor**: each type (hitters / SP / RP) gets at least `pct` of its cards in the range, and types already above it are left alone. Pick `pct` near the WOTC share of the short type(s), but no higher than the WOTC share of any type it would push past WOTC. If one type needs much more than the others, use two buckets (e.g. `10-50` + `60-100`) or accept a small shortfall. Keep the percent low; the user wants just enough to match WOTC.
- Check the trial: re-run that set with `-b "<set>=<buckets>"`. An "Only reached X of Y" warning means the pool doesn't have enough low-point cards.
- When the user accepts a bucket, save it to `point_buckets.json` (`{"2001": "10-100:0.08"}`) so later reviews and the UI config stay in sync. Remind them to add the same bucket in the Release Builder.
- Also mention big gaps elsewhere in the 50-pt histogram (e.g. a hole at 400-549 or a pile-up at 250-299).

### 2b. Command (On-Base / Control): flag only
- Flag a command value when |diff| ≥ max(5 cards, ~30% of WOTC scaled), when a value WOTC never printed (diff with WOTC actual = 0) has many cards, or when Avg OnBase/Control differs by ≥0.4.
- Describe the direction (e.g. "On-Base piles up at 9, WOTC peaks at 10 and 12 → hitters are under-rated by ~1"). Don't propose chart code changes unless asked.

### 2c. Speed: similar distribution?
- **Skip speed for 2003.** WOTC's 2003 base set speed runs too low (most hitters at 8-12, peak at 9), so it's not a useful target. Report it as "Speed: skipped (WOTC 2003 speed runs low)" and don't flag it or suggest fixes.
- **Hitters only**, on both sides: pitchers' speed is meaningless, so leave them out of every speed number (distribution, bands, average). The script's Speed table and Avg Speed already filter to `is_pitcher = false` for this set and for WOTC. Don't fall back to all-card numbers from the JSON.
- Compare Avg Speed (flag ≥1.0 diff) and banded shares: slow (≤12), average (13-17), fast (18+). Flag a band that's off by more than ~8 percentage points, and any big tail cluster (e.g. too many 21+ or nobody ≤10).

### 2d. Defense: shape per position vs WOTC
For each position with ≥8 cards (skip `IF`/tiny groups), compare **Avg**, **Std dev**, and the histogram shape. WOTC is roughly a normal curve around the middle of each position's range.
- Flag: avg off by ≥0.5 (C), ≥0.3 (2B/3B/SS/CF), ≥0.2 (1B/LF/RF/OF); std dev ratio outside ~0.75-1.3; a lopsided tail (e.g. too many at the top rating, a missing low end); or two peaks where WOTC has one.
- The report shows the **metric actually used** per position (2026: catchers use DRS; everyone else uses OAA) and the current mapping: `range_min`, `range_max`, where an average defender (0) lands, and how much of the metric it takes per +1.

**How `metrics.py` shapes it** (see `DefenseMetric` and `ShowdownPlayerCard._convert_to_in_game_defense`):
`percentile = (rating_per_150 - range_min) / (range_max - range_min)`, `defense = pos_min + percentile × (pos_max - pos_min)`, rounded and floored at 0 (`pos_min`/`pos_max` come from `Set.position_defense_min/max`). Ratings above `range_max` are compressed by `over_max_multiplier`, so cards can land above `pos_max` (e.g. SS +6).
- **`range_max` multiplier** scales both ends (because `range_min = -range_max × min_multiplier`). Higher → more OAA per +1 → **narrower** spread, more cards in the middle, fewer extremes. Lower → **wider** spread. It doesn't move where an average defender lands.
- **`range_min` multiplier (m)** moves the center: an average defender lands at `pos_min + m/(1+m) × (pos_max - pos_min)`. Lower m → whole curve **shifts down** (the file's comments call this "SHALLOWER MIN -> PUSH BOTTOM HALF DOWN"); higher m → shifts up. It also stretches or squeezes the bottom half.
- Metric-specific basis tweaks also apply (OAA LF/RF ×1.3 on min, dWAR OF ×1.5).
- **1B** has separate cutoffs: `first_base_plus_1_cutoff(set, year)` (set/year specific, e.g. 2001+2026 → 4 OAA) and `first_base_plus_2_cutoff` (+2 also needs 90+ games). Raise a cutoff → fewer +1/+2 cards. 2000-2005 sets have no -1 at 1B.
- Positions in `metrics.py` are keyed `'C'`, `'2B'`, `'3B'`, `'SS'`, `'LF' | 'RF'` (used for LF/RF cards), `'CF'`, `'OF'`.

**Suggestions:** give a concrete diff for the right `match` branch, scoped under `if max_year >= 2026:` (with an `else:` that keeps the old value) so historical cards don't change. Follow the file's existing style and short comments. Estimate the effect with the formulas above, e.g. "m 0.9 → 0.75 moves the average SS from 2.61 to 2.36".

**Don't edit `metrics.py` unless the user asks;** they often edit it themselves during review. If they ask you to apply a change, make it, re-run only the affected set(s) with `--rerun`, and show that position's before/after avg/std dev/histogram. Revert it if the shape got worse.

## 3. Report

For each set, keep it short:

```
## 2001 (2026) — 462 cards
Points ⚠️  Low (10-100): 21 vs WOTC 34 scaled — RP short by 9. Suggest bucket 10-100:0.10 (RP share 11% → ~WOTC 12%; hitters already at 9%, unaffected)
Command ✅  (or ⚠️ with the specific values)
Speed   ✅
Defense ⚠️  SS: avg 3.4 vs 2.8, top-heavy (8 at +5 vs 3 scaled) → suggest range_max mult 1.4 → 1.6 for 2001/2026
```

Then add a short **cross-set summary**: issues that repeat across sets (likely a shared formula problem, not a per-set range tweak), all suggested `metrics.py` diffs together, and the bucket changes to apply in the Release Builder.
