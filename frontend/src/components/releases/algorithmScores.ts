/**
 * @fileoverview Labels and number formats for how an Algorithm run scored its picks, shared by the
 * match badge, the cut line summary and the Cutoff tab.
 */

import type { AlgorithmSelectionReason } from '../../api/releases';

export const SELECTION_REASON_LABELS: Record<AlgorithmSelectionReason, string> = {
    WEIGHTED: 'Weighted pick',
    MANUAL: 'Manual include',
    LEGEND: 'Legend',
    TEAM_MINIMUM: 'Team minimum',
    POINTS_SWAP: 'Points swap',
};

/** Short plate text for picks that skipped the weighted score */
export const SELECTION_REASON_SHORT: Partial<Record<AlgorithmSelectionReason, string>> = {
    MANUAL: 'MAN',
    LEGEND: 'LGND',
    TEAM_MINIMUM: 'TM MIN',
    POINTS_SWAP: 'PTS SWAP',
};

const CUT_LINE_GROUP_LABELS: Record<string, string> = {
    POSITION_PLAYER: 'Hitters',
    STARTING_PITCHER: 'Starters',
    RELIEF_PITCHER: 'Relievers',
    STARTER: 'Starters',
    RELIEVER: 'Relievers',
    CLOSER: 'Closers',
    ANY: 'Any',
};

/** A slot group's name: a player type, a pitcher slot, or a hitter position as printed (C, SS, LF/RF) */
export function cutLineGroupLabel(group: string): string {
    return CUT_LINE_GROUP_LABELS[group] ?? group;
}

export function formatScore(value: number): string {
    return value.toFixed(1);
}

export function formatMargin(margin: number): string {
    return `${margin >= 0 ? '+' : '−'}${formatScore(Math.abs(margin))}`;
}
