/**
 * @fileoverview An edition's scope: the settings every way of filling its pool shares (Algorithm,
 * Manual and Customs). Saved under `attributes.scope`, apart from the Algorithm's own rules.
 * Editions saved before scope existed kept these in `attributes.algorithm`, so the parser falls
 * back to that blob field by field.
 */

import type { AlgorithmConfig, ReleaseCard } from '../../api/releases';
import { CardSource } from '../../types/cardSource';
import { SEASON_HALF_LABELS } from '../../api/showdownBotCard';
import { parseAlgorithmSettings, allShowdownSets } from './algorithmSettings';
import { yearsInclude } from './years';

export const SCOPE_KEYS = ['set_size', 'years', 'showdown_sets', 'pitcher_showdown_sets', 'variable_speed', 'season_half', 'other_editions_rule'] as const satisfies readonly (keyof AlgorithmConfig)[];
export type ScopeKey = typeof SCOPE_KEYS[number];

export type EditionScope = Required<Pick<AlgorithmConfig, ScopeKey>>;

/** What stays with the Algorithm tab: who's eligible, the makeup of the set and how players are picked. */
export type AlgorithmRules = Omit<AlgorithmConfig, ScopeKey>;

export function pickScope(config: AlgorithmConfig): EditionScope {
    return {
        set_size: config.set_size,
        years: config.years,
        showdown_sets: config.showdown_sets,
        pitcher_showdown_sets: config.pitcher_showdown_sets ?? null,
        variable_speed: config.variable_speed ?? false,
        season_half: config.season_half ?? null,
        other_editions_rule: config.other_editions_rule ?? 'ALLOW',
    };
}

export function omitScope(config: AlgorithmConfig): AlgorithmRules {
    const rules: Partial<AlgorithmConfig> = { ...config };
    for (const key of SCOPE_KEYS) delete rules[key];
    return rules as AlgorithmRules;
}

export function parseEditionScope(attributes: Record<string, unknown>, defaultShowdownSet?: string | null): EditionScope {
    const saved = attributes.scope && typeof attributes.scope === 'object' ? attributes.scope as Partial<EditionScope> : {};
    return { ...pickScope(parseAlgorithmSettings(attributes, defaultShowdownSet)), ...saved };
}

/** The showdown sets a card of this type should come from. */
function setsFor(scope: EditionScope, isPitcher: boolean): string[] {
    return isPitcher && scope.pitcher_showdown_sets?.length ? scope.pitcher_showdown_sets : scope.showdown_sets;
}

export type OutsideScopeCounts = { years: number; sets: number; periods: number };

/** Saved cards that sit outside the scope: a season not in the years, a showdown set not in the sets
 * or a different stats period than the edition's. Customs are never scoped (they can be date ranges
 * or splits), so they don't count. */
export function countOutsideScope(cards: ReleaseCard[], scope: EditionScope): OutsideScopeCounts {
    const counts = { years: 0, sets: 0, periods: 0 };
    for (const card of cards) {
        if (card.source_card_type === CardSource.CUSTOM) continue;
        const { year, showdown_set, is_pitcher } = card.card_snapshot;
        if (year != null && !yearsInclude(scope.years, year)) counts.years += 1;
        const sets = setsFor(scope, is_pitcher);
        if (showdown_set && sets.length > 0 && !sets.includes(showdown_set)) counts.sets += 1;
        if ((card.card_snapshot.card_data?.stats_period?.season_half ?? null) !== scope.season_half) counts.periods += 1;
    }
    return counts;
}

/** Mirrors `AlgorithmPreviewRequest.set_size` on the backend. */
export const MAX_SET_SIZE = 800;

/** A set size field's text as a size: 0 while blank, never over the max. */
export function parseSetSize(value: string | null): number {
    return Math.min(parseInt(value || '0', 10) || 0, MAX_SET_SIZE);
}

/** One-line description, e.g. "100 cards · 2000-2004 · 2001". `withSize: false` leaves the size out for places that edit it. */
export function scopeSummary(scope: EditionScope, { withSize = true }: { withSize?: boolean } = {}): string {
    const hasPitcherSets = scope.pitcher_showdown_sets !== null;
    return [
        ...(withSize ? [`${scope.set_size} cards`] : []),
        scope.years.trim() || 'no years',
        ...(scope.season_half ? [SEASON_HALF_LABELS[scope.season_half]] : []),
        ...(hasPitcherSets
            ? [`${scope.showdown_sets.join(', ') || 'no'} hitters`, `${scope.pitcher_showdown_sets?.join(', ') || 'no'} pitchers`]
            : [allShowdownSets(scope).join(', ') || 'no sets']),
    ].join(' · ');
}
