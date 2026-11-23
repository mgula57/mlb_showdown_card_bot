import type { KpiComparison } from '../team_builder/sim/simStatColumns';

/** "12,318" */
export const formatCount = (value: number | null | undefined): string => (value ?? 0).toLocaleString();

/** "2.7%" (one decimal under 10%, whole numbers above). */
export function formatPct(value: number | null | undefined): string {
    const pct = (value ?? 0) * 100;
    if (pct > 0 && pct < 0.1) return '<0.1%';
    return `${pct < 10 ? pct.toFixed(1) : Math.round(pct)}%`;
}

/** `part / whole`, 0 when there's no whole. */
export const ratio = (part: number | null | undefined, whole: number | null | undefined): number => (whole ? (part ?? 0) / whole : 0);

/** Change vs the previous period for a `KpiTile`: "+12% vs prev", colored by whether up is good. */
export function periodComparison(current: number, previous: number, higherIsGood = true): KpiComparison {
    if (!previous) {
        return current
            ? { direction: 'up', isGood: higherIsGood, label: 'new this period' }
            : { direction: 'flat', isGood: true, label: 'no change' };
    }
    const change = (current - previous) / previous;
    if (Math.abs(change) < 0.005) return { direction: 'flat', isGood: true, label: 'no change' };
    const direction = change > 0 ? 'up' : 'down';
    return {
        direction,
        isGood: direction === 'up' ? higherIsGood : !higherIsGood,
        label: `${change > 0 ? '+' : '−'}${formatPct(Math.abs(change))} vs prev`,
    };
}

/** Change in a rate, in percentage points: "+0.4 pts vs prev". */
export function rateComparison(current: number, previous: number, higherIsGood = true): KpiComparison {
    const points = (current - previous) * 100;
    if (Math.abs(points) < 0.05) return { direction: 'flat', isGood: true, label: 'no change' };
    const direction = points > 0 ? 'up' : 'down';
    return {
        direction,
        isGood: direction === 'up' ? higherIsGood : !higherIsGood,
        label: `${points > 0 ? '+' : '−'}${Math.abs(points).toFixed(1)} pts vs prev`,
    };
}

/** "Nov 21" for chart axes; dates arrive as UTC `YYYY-MM-DD`. */
export function formatDay(isoDate: string): string {
    return new Date(`${isoDate.slice(0, 10)}T00:00:00Z`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

/** Where a build came from (`generation_source` on the build log). */
export const GENERATION_SOURCE_LABELS: Record<string, string> = {
    web_customs_tab: 'Card Builder',
    web_release_builder: 'Release Builder',
};

/** Build stages recorded with a failure (see `generate_card`). */
export const ERROR_STAGE_LABELS: Record<string, string> = {
    inputs: 'Reading inputs',
    stats: 'Loading stats',
    cached_card: 'Archived card',
    card: 'Building card',
    trends: 'Trends',
};

/** Enum-style values ("PITCH CLOCK ERA", "REPLACEMENT_LEVEL") as readable labels. */
export function humanizeLabel(value: string): string {
    if (!/^[A-Z0-9 _]+$/.test(value) || value.length <= 4) return value;
    return value.toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
