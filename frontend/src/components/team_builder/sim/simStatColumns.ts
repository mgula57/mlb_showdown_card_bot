import type { SimStatLine } from '../../../api/sim';

// Column sets mirror HITTER_CATEGORIES / PITCHER_CATEGORIES in reporting.py so the web tables
// and the CLI tables never drift. Keys are StatCategory values.
export const HITTER_COLUMNS = ['g', 'pa', 'ba', 'obp', 'slg', 'ops', 'ops+', 'hr', 'rbi', 'bb', 'so', 'sb', 'r', 'wRC+', 'advantage_pct', 'own_chart_out_pct'];
export const PITCHER_COLUMNS = ['g', 'era', 'whip', 'ip', 'er', 'so9', 'advantage_pct', 'own_chart_out_pct'];
const RATE_KEYS = new Set(['ba', 'obp', 'slg', 'ops', 'wOBA']);
const PERCENT_KEYS = new Set(['advantage_pct', 'own_chart_out_pct']);
// SHORT HEADERS FOR KEYS WHOSE UPPERCASED VALUE WOULDN'T FIT A COLUMN - MIRRORS StatCategory.abbreviation.
export const COLUMN_LABELS: Record<string, string> = { advantage_pct: 'ADV%', own_chart_out_pct: 'OCHO%' };

// Shown on `CardDetail`'s tooltip banner wherever a card is opened with `simStats` set, so it's
// clear the SIM column/highlights reflect this simulated season, not the card's real one.
export const SIM_STATS_TOOLTIP = "Stats highlighted in red reflect this simulated season, not the player's real-life season.";

export function formatStat(key: string, value: number | undefined): string {
    if (value === undefined) return '—';
    if (PERCENT_KEYS.has(key)) return `${(value * 100).toFixed(1)}%`;
    if (RATE_KEYS.has(key)) return value.toFixed(3).replace(/^0\./, '.');
    if (key === 'era' || key === 'whip') return value.toFixed(2);
    if (key === 'ip' || key === 'so9') return value.toFixed(1);
    return String(Math.round(value));
}

// A CLASSIC-style highlight category, mirroring `StatHighlightsCategory` in
// mlb_showdown_bot/core/card/stats/stat_highlights.py: `multiplier` alone is the sort rank for a
// category with no `cutoff` (it always shows, regardless of value); a category WITH a cutoff is
// ranked by how the player's value compares to a 650-PA-pace cutoff, and is dropped entirely at 0
// (a zero-value counting stat can never clear a positive cutoff there either).
type HighlightCategory = { key: string; label: string; multiplier: number; cutoff?: number; isPaMetric?: boolean };

const HITTER_HIGHLIGHT_CATEGORIES: HighlightCategory[] = [
    { key: 'g', label: 'G', multiplier: 10.0 },
    { key: 'hr', label: 'HR', multiplier: 1.0, cutoff: 20, isPaMetric: true },
    { key: 'sb', label: 'SB', multiplier: 1.0, cutoff: 17, isPaMetric: true },
    { key: 'rbi', label: 'RBI', multiplier: 0.85, cutoff: 85, isPaMetric: true },
    { key: '2b', label: '2B', multiplier: 1.0, cutoff: 30, isPaMetric: true },
    { key: '3b', label: '3B', multiplier: 1.0, cutoff: 6, isPaMetric: true },
    { key: 'h', label: 'H', multiplier: 1.0, cutoff: 170, isPaMetric: true },
];

// W/SV aren't tracked per pitcher in the sim, so this substitutes K/9 (the closest available
// "how dominant" counting-adjacent stat) in their place — CLASSIC proper doesn't include it.
const PITCHER_HIGHLIGHT_CATEGORIES: HighlightCategory[] = [
    { key: 'g', label: 'G', multiplier: 10.0 },
    { key: 'era', label: 'ERA', multiplier: 5.0 },
    { key: 'whip', label: 'WHIP', multiplier: 3.0 },
    { key: 'ip', label: 'IP', multiplier: 2.0 },
    { key: 'so9', label: 'K/9', multiplier: 1.0, cutoff: 8.5 },
];

function highlightRank(category: HighlightCategory, value: number, pa: number | undefined): number {
    if (category.cutoff === undefined) return category.multiplier;
    const denominator = category.isPaMetric && pa ? pa / 650 : 1;
    const perPace = denominator > 0 ? value / denominator : value;
    return (perPace / category.cutoff) * category.multiplier;
}

/**
 * A highlight ribbon built from a sim statline — the simulated-season equivalent of
 * `CardDatabaseRecord.stat_highlights_list` (the card's own real-life highlights), for sim result
 * screens that should show what a player did in THIS simulated season, not their real one. Mirrors
 * `ShowdownPlayerCard._generate_stat_highlights_list`'s CLASSIC category set and sort/skip rules
 * as closely as the stats available on a `SimStatLine` allow.
 */
export function buildSimStatHighlights(row: SimStatLine): string[] {
    const s = row.stats;
    const isPitcher = row.player_type === 'Pitcher';
    const pa = s['pa'];

    const entries: { label: string; rank: number }[] = [];
    for (const category of (isPitcher ? PITCHER_HIGHLIGHT_CATEGORIES : HITTER_HIGHLIGHT_CATEGORIES)) {
        const value = s[category.key];
        if (value === undefined) continue;
        if (category.cutoff !== undefined && value === 0) continue;
        entries.push({ label: `${formatStat(category.key, value)} ${category.label}`, rank: highlightRank(category, value, pa) });
    }

    // SLASHLINE HAS NO SINGLE STAT KEY, SO IT ISN'T PART OF THE CATEGORY LOOP ABOVE - SAME RANK AS ERA (5.0).
    if (!isPitcher && s['ba'] !== undefined && s['obp'] !== undefined && s['slg'] !== undefined) {
        entries.push({ label: `${formatStat('ba', s['ba'])}/${formatStat('obp', s['obp'])}/${formatStat('slg', s['slg'])}`, rank: 5.0 });
    }

    entries.sort((a, b) => b.rank - a.rank);
    return entries.map(e => e.label);
}
