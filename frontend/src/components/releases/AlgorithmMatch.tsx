/**
 * @fileoverview How an Algorithm run picked a Release Builder card: its match score, how it got in,
 * and its margin over the cut line (the best player of its type left out).
 */

import type { AlgorithmCutLine, AlgorithmSelectionReason, ReleaseCard } from '../../api/releases';
import { Plate } from '../shared/Plate';
import { matchMargin } from './poolGrouping';

const SELECTION_REASON_LABELS: Record<AlgorithmSelectionReason, string> = {
    WEIGHTED: 'Weighted pick',
    MANUAL: 'Manual include',
    LEGEND: 'Legend',
    TEAM_MINIMUM: 'Team minimum',
    POINTS_SWAP: 'Points swap',
};

/** Short plate text for picks that skipped the weighted score */
const SELECTION_REASON_SHORT: Partial<Record<AlgorithmSelectionReason, string>> = {
    MANUAL: 'MAN',
    LEGEND: 'LGND',
    TEAM_MINIMUM: 'TM MIN',
    POINTS_SWAP: 'PTS SWAP',
};

const CUT_LINE_GROUP_LABELS: Record<string, string> = {
    POSITION_PLAYER: 'Hitters',
    STARTING_PITCHER: 'Starters',
    RELIEF_PITCHER: 'Relievers',
    ANY: 'Any',
};

function formatScore(value: number): string {
    return value.toFixed(1);
}

function formatMargin(margin: number): string {
    return `${margin >= 0 ? '+' : '−'}${formatScore(Math.abs(margin))}`;
}

/** Score plate (with margin) for a card picked by an Algorithm run; nothing for hand-added cards.
 * `labeled` spells out how the card got in, for roomier spots like the card detail modal. */
export function AlgorithmMatchBadge({ card, labeled = false }: { card: ReleaseCard; labeled?: boolean }) {
    const { algorithm_match_score: score, algorithm_selection_reason: reason } = card.card_snapshot;
    if (score == null) return null;
    const margin = matchMargin(card);
    const title = [
        `Match score ${formatScore(score)}`,
        margin != null && `${formatMargin(margin)} pick score vs. the best player left out of its slot`,
        reason && SELECTION_REASON_LABELS[reason],
    ].filter(Boolean).join(' · ');
    const reasonShort = reason ? SELECTION_REASON_SHORT[reason] : undefined;
    return (
        <span title={title} className="flex items-center gap-1">
            {labeled && <span className="text-[11px] text-(--text-secondary)">Match</span>}
            <Plate variant="ink" size="sm" className="tabular-nums">
                {Math.round(score)}
                {margin != null && <span className="opacity-60">{formatMargin(margin)}</span>}
            </Plate>
            {labeled
                ? reason && <span className="text-[11px] text-(--text-secondary)">{SELECTION_REASON_LABELS[reason]}</span>
                : reasonShort && <Plate variant="outline" size="sm">{reasonShort}</Plate>}
        </span>
    );
}

/** Per slot group, who just missed the set. Their pick scores sit on a different scale from match
 * scores (team balance can push them past 100), so the numbers stay in the tooltip. */
export function AlgorithmCutLineSummary({ cutLines }: { cutLines: AlgorithmCutLine[] }) {
    if (cutLines.length === 0) return null;
    return (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-(--text-secondary)">
            <span className="font-semibold text-(--text-primary)">Just missed</span>
            {cutLines.map(line => (
                <span key={line.group} title={`Pick score ${formatScore(line.pick_score)}, the best left out when this slot filled`}>
                    {CUT_LINE_GROUP_LABELS[line.group] ?? line.group}:{' '}
                    <span className="text-(--text-primary)">{line.name}</span> ({line.team} {line.year})
                </span>
            ))}
        </div>
    );
}
