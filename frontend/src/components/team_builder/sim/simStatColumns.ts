import type { SimStatLine } from '../../../api/sim';

// Column sets mirror HITTER_CATEGORIES / PITCHER_CATEGORIES in reporting.py so the web tables
// and the CLI tables never drift. Keys are StatCategory values.
export const HITTER_COLUMNS = ['g', 'pa', 'ba', 'obp', 'slg', 'ops', 'ops+', '2b', '3b', 'hr', 'rbi', 'bb', 'so', 'sb', 'r', 'wRC+', 'advantage_pct', 'own_chart_out_pct'];
export const PITCHER_COLUMNS = ['g', 'wins', 'losses', 'sv', 'bs', 'era', 'whip', 'ip', 'er', 'hr', 'hr_own_chart', 'so9', 'gidp', 'advantage_pct', 'own_chart_out_pct'];
// The League Stats "SIM vs. REAL" comparison table's column sets - `HITTER_COLUMNS`/
// `PITCHER_COLUMNS` minus whatever `SeasonReport.print_real_life_comparison`'s `stats_to_ignore`
// drops for having no real-life league-average counterpart (W/L/SV/BS, own-chart HR, and G itself),
// plus ADV%/OCHO% - the CLI keeps those, but they're dropped here too since they're engine-roll
// concepts with no real-life meaning to compare against, not just a missing baseline number.
const COMPARISON_IGNORE = ['advantage_pct', 'own_chart_out_pct'];
export const HITTER_COMPARISON_COLUMNS = HITTER_COLUMNS.filter(key => key !== 'g' && !COMPARISON_IGNORE.includes(key));
export const PITCHER_COMPARISON_COLUMNS = PITCHER_COLUMNS.filter(key => !['g', 'wins', 'losses', 'sv', 'bs', 'hr_own_chart', ...COMPARISON_IGNORE].includes(key));
const RATE_KEYS = new Set(['ba', 'obp', 'slg', 'ops', 'wOBA', 'real_ops', 'ops_diff']);
const PERCENT_KEYS = new Set(['advantage_pct', 'own_chart_out_pct']);
// SHORT HEADERS FOR KEYS WHOSE UPPERCASED VALUE WOULDN'T FIT A COLUMN - MIRRORS StatCategory.abbreviation.
export const COLUMN_LABELS: Record<string, string> = { advantage_pct: 'ADV%', own_chart_out_pct: 'OCHO%', wins: 'W', losses: 'L', hr_own_chart: 'HR-OC', gidp: 'GDP', real_ops: 'OPS (REAL)', ops_diff: 'DIFF' };

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

// CLASSIC proper ranks pitchers on W / SV / ERA / WHIP / IP; the sim now tracks W and SV per
// pitcher (see `Game._award_pitcher_decisions`), so both are here. K/9 stays on as an extra
// "how dominant" signal CLASSIC itself doesn't use.
const PITCHER_HIGHLIGHT_CATEGORIES: HighlightCategory[] = [
    { key: 'g', label: 'G', multiplier: 10.0 },
    { key: 'wins', label: 'W', multiplier: 1.0, cutoff: 15 },
    { key: 'sv', label: 'SV', multiplier: 1.0, cutoff: 30 },
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

export type TeamKpi = { label: string; value: string };

function sumStat(rows: SimStatLine[], key: string): number {
    return rows.reduce((sum, row) => sum + (row.stats[key] ?? 0), 0);
}

/** Rate stats (BA, ERA, …) are already computed per-player server-side, so a team total weights
 * each row by its opportunity count rather than re-deriving the rate from raw components the
 * frontend doesn't have. This is exact for anything defined per unit of the weight (WHIP/SO9 per
 * IP), and a close approximation for anything defined per AB rather than PA (BA/SLG). */
function weightedAvgStat(rows: SimStatLine[], key: string, weightKey: string): number {
    let weightedSum = 0;
    let totalWeight = 0;
    for (const row of rows) {
        const weight = row.stats[weightKey] ?? 0;
        const value = row.stats[key];
        if (value === undefined || weight <= 0) continue;
        weightedSum += value * weight;
        totalWeight += weight;
    }
    return totalWeight > 0 ? weightedSum / totalWeight : 0;
}

/** Team-level KPI tiles for the batting tab — counting stats summed, rate stats PA-weighted. */
export function buildHitterTeamKpis(rows: SimStatLine[]): TeamKpi[] {
    if (rows.length === 0) return [];
    return [
        { label: 'AVG', value: formatStat('ba', weightedAvgStat(rows, 'ba', 'pa')) },
        { label: 'OBP', value: formatStat('obp', weightedAvgStat(rows, 'obp', 'pa')) },
        { label: 'SLG', value: formatStat('slg', weightedAvgStat(rows, 'slg', 'pa')) },
        { label: 'OPS', value: formatStat('ops', weightedAvgStat(rows, 'ops', 'pa')) },
        { label: 'HR', value: formatStat('hr', sumStat(rows, 'hr')) },
        { label: 'RBI', value: formatStat('rbi', sumStat(rows, 'rbi')) },
    ];
}

/** Team-level KPI tiles for the pitching tab — counting stats summed, rate stats IP-weighted. */
export function buildPitcherTeamKpis(rows: SimStatLine[]): TeamKpi[] {
    if (rows.length === 0) return [];
    return [
        { label: 'ERA', value: formatStat('era', weightedAvgStat(rows, 'era', 'ip')) },
        { label: 'WHIP', value: formatStat('whip', weightedAvgStat(rows, 'whip', 'ip')) },
        { label: 'K/9', value: formatStat('so9', weightedAvgStat(rows, 'so9', 'ip')) },
        { label: 'IP', value: formatStat('ip', sumStat(rows, 'ip')) },
    ];
}

function pct(numerator: number, denominator: number): number {
    return denominator > 0 ? numerator / denominator : 0;
}

/** KPI tiles for the "League Stats" tab — the board game's own dice-roll outcomes (advantage
 * rolls, own-chart results, double play / extra-base / steal rolls), distinct from regular
 * baseball stats. These describe the simulation engine itself (how the dice broke this season),
 * not any one club, so they're pulled from `summary.league_totals` — already summed across every
 * plate appearance in the season — rather than one team's roster. Sourcing from a single club's
 * hitters/pitchers would pool two disjoint, unrelated PA samples (the club's own plate appearances
 * vs. the plate appearances its pitching staff faced, against dozens of different opponents)
 * under one club's name, which is misleading — e.g. Hitter/Pitcher Advantage% only sum to 100%
 * when both sides are drawn from the same PA pool, as they are here. */
export function buildLeagueStatsKpis(leagueTotals: Record<string, SimStatLine>): TeamKpi[] {
    const hitter = leagueTotals['Hitter']?.stats;
    const pitcher = leagueTotals['Pitcher']?.stats;
    if (!hitter || !pitcher) return [];
    const sb = hitter['sb'] ?? 0;
    const cs = hitter['cs'] ?? 0;
    return [
        { label: 'Hitter Advantage%', value: formatStat('advantage_pct', pct(hitter['hadv'] ?? 0, hitter['pa'] ?? 0)) },
        { label: 'Pitcher Advantage%', value: formatStat('advantage_pct', pct(pitcher['padv'] ?? 0, pitcher['pa'] ?? 0)) },
        { label: 'Own Chart Out% (Hit)', value: formatStat('own_chart_out_pct', pct(hitter['own_chart_out'] ?? 0, hitter['hadv'] ?? 0)) },
        { label: 'Own Chart Out% (Pit)', value: formatStat('own_chart_out_pct', pct(pitcher['own_chart_out'] ?? 0, pitcher['padv'] ?? 0)) },
        { label: 'DP Success%', value: formatStat('advantage_pct', pct(pitcher['gidp'] ?? 0, pitcher['gidpa'] ?? 0)) },
        { label: 'Extra Base Success%', value: formatStat('advantage_pct', pct(hitter['xb'] ?? 0, hitter['xba'] ?? 0)) },
        { label: 'SB Success%', value: formatStat('advantage_pct', pct(sb, sb + cs)) },
        { label: 'Pitcher Chart HR', value: formatStat('hr', pitcher['hr_own_chart'] ?? 0) },
        { label: '21+ Swing Rolls', value: formatStat('hr', (hitter['swing21'] ?? 0) + (pitcher['swing21'] ?? 0)) },
    ];
}
