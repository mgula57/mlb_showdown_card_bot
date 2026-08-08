/**
 * @fileoverview Which Showdown sets a team allows is a per-card-source rule, not one flat list.
 * Bot cards exist for every set, so a Bot team pins exactly one; WOTC sets were printed alongside
 * each other and are freely combined. `allowed_sets_by_source` is the source of truth —
 * `allowed_sets` is kept as its flattened union so list/header views (and teams saved before the
 * split) keep working without a backfill.
 */
import { CardSource, type CardSource as CardSourceType } from '../types/cardSource';

/** Card sources a user team can draft from. WBC is deliberately not offered. */
export const TEAM_CARD_SOURCES: { value: CardSourceType; label: string }[] = [
    { value: CardSource.BOT, label: 'Bot' },
    { value: CardSource.WOTC, label: 'WOTC' },
];

const BOT_SET_VALUES = ['2000', '2001', 'CLASSIC', '2002', '2003', '2004', '2005', 'EXPANDED'];
/** WOTC only ever printed 2000-2005 — CLASSIC and EXPANDED are bot-only sets. */
const WOTC_SET_VALUES = ['2000', '2001', '2002', '2003', '2004', '2005'];

export type AllowedSetsBySource = Record<string, string[]>;

/** The subset of a team's settings that governs card eligibility. */
export type TeamSetSettings = {
    allowed_sets?: string[] | null;
    allowed_sets_by_source?: AllowedSetsBySource | null;
    allowed_card_sources?: string[] | null;
};

export const setOptionsForSource = (source: CardSourceType): string[] =>
    source === CardSource.WOTC ? WOTC_SET_VALUES : BOT_SET_VALUES;

/** Bot teams pin exactly one set; any other source combines freely. */
export const isSingleSetSource = (source: CardSourceType): boolean => source === CardSource.BOT;

/** Sources the team drafts from — an empty restriction (or one naming only sources no longer
 *  offered, e.g. a team saved as WBC-only) means all of them. */
export function activeSources(team: TeamSetSettings): CardSourceType[] {
    const restricted = team.allowed_card_sources ?? [];
    const all = TEAM_CARD_SOURCES.map(s => s.value);
    const filtered = all.filter(s => restricted.includes(s));
    return filtered.length ? filtered : all;
}

/**
 * Sets allowed for one source. Teams saved before the per-source split have no map entry and
 * fall back to their flat `allowed_sets`, narrowed to what that source could have produced.
 * An empty result means "no set restriction" to the callers that build search filters.
 */
export function allowedSetsForSource(team: TeamSetSettings, source: CardSourceType): string[] {
    const stored = team.allowed_sets_by_source?.[source];
    if (stored !== undefined) return stored;
    const valid = setOptionsForSource(source);
    const legacy = (team.allowed_sets ?? []).filter(s => valid.includes(s));
    return isSingleSetSource(source) ? legacy.slice(0, 1) : legacy;
}

/**
 * Recompute the stored set fields after any change to sources or sets: the map is pruned to the
 * active sources (seeded from the legacy fallback for sources it doesn't cover yet) and
 * `allowed_sets` is refreshed to mirror it.
 */
export function normalizeSetSettings(team: TeamSetSettings): {
    allowed_sets_by_source: AllowedSetsBySource;
    allowed_sets: string[];
} {
    const map: AllowedSetsBySource = {};
    for (const source of activeSources(team)) map[source] = allowedSetsForSource(team, source);
    return {
        allowed_sets_by_source: map,
        allowed_sets: [...new Set(Object.values(map).flat())],
    };
}

/** Apply a set selection for one source, returning the full settings update to persist. */
export function toggleSetForSource(team: TeamSetSettings, source: CardSourceType, set: string) {
    const current = allowedSetsForSource(team, source);
    const next = isSingleSetSource(source)
        ? (current.includes(set) ? [] : [set])
        : (current.includes(set) ? current.filter(s => s !== set) : [...current, set]);
    return normalizeSetSettings({
        ...team,
        allowed_sets_by_source: { ...(team.allowed_sets_by_source ?? {}), [source]: next },
    });
}
