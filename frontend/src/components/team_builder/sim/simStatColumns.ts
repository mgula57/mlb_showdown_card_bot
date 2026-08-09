// Column sets mirror HITTER_CATEGORIES / PITCHER_CATEGORIES in reporting.py so the web tables
// and the CLI tables never drift. Keys are StatCategory values.
export const HITTER_COLUMNS = ['g', 'pa', 'ba', 'obp', 'slg', 'ops', 'ops+', 'hr', 'rbi', 'bb', 'so', 'sb', 'r', 'wRC+', 'advantage_pct', 'own_chart_out_pct'];
export const PITCHER_COLUMNS = ['g', 'era', 'whip', 'ip', 'er', 'so9', 'advantage_pct', 'own_chart_out_pct'];
const RATE_KEYS = new Set(['ba', 'obp', 'slg', 'ops', 'wOBA']);
const PERCENT_KEYS = new Set(['advantage_pct', 'own_chart_out_pct']);
// SHORT HEADERS FOR KEYS WHOSE UPPERCASED VALUE WOULDN'T FIT A COLUMN - MIRRORS StatCategory.abbreviation.
export const COLUMN_LABELS: Record<string, string> = { advantage_pct: 'ADV%', own_chart_out_pct: 'OCHO%' };

export function formatStat(key: string, value: number | undefined): string {
    if (value === undefined) return '—';
    if (PERCENT_KEYS.has(key)) return `${(value * 100).toFixed(1)}%`;
    if (RATE_KEYS.has(key)) return value.toFixed(3).replace(/^0\./, '.');
    if (key === 'era' || key === 'whip') return value.toFixed(2);
    if (key === 'ip' || key === 'so9') return value.toFixed(1);
    return String(Math.round(value));
}
