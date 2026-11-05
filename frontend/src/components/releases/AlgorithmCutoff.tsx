/**
 * @fileoverview Where an Algorithm run's cutoff fell in each slot group: its lowest picks above the
 * line, the closest calls below it, and why each score landed where it did (match score, then the
 * team balance and points fit that moved it).
 */

import type { AlgorithmCutLine, AlgorithmCutLinePlayer, AlgorithmScoreBreakdown, AlgorithmSelectionReason } from '../../api/releases';
import { Plate } from '../shared/Plate';
import { Heading } from '../shared/Heading';
import { EmptyState } from '../shared/EmptyState';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';
import { SELECTION_REASON_LABELS, SELECTION_REASON_SHORT, cutLineGroupLabel, formatMargin, formatScore } from './algorithmScores';

type AlgorithmCutoffProps = {
    cutLines: AlgorithmCutLine[];
    /** True while the run is an unsaved preview; false for the last run once it's saved */
    isPreview: boolean;
    isRunning: boolean;
    /** Ids of picks that are still in the pool, so their rows can open the card */
    openablePickIds: Set<string>;
    onOpenPick: (id: string) => void;
};

/** Smallest score span a group's plot covers, so a tight race isn't blown up into a wide one */
const MIN_DOMAIN_SPAN = 10;

/** Player | Pts | plot | (Match | Team | Fit, from sm) | Score */
const ROW_GRID_CLASS = 'grid items-center gap-x-2 grid-cols-[minmax(0,1fr)_2.25rem_minmax(5rem,1.3fr)_3rem] sm:grid-cols-[minmax(0,1fr)_2.5rem_minmax(7rem,1.6fr)_3rem_3rem_3rem_3.25rem]';

type RowTone = 'pick' | 'miss' | 'swapped';

// Picks wear navy and the rest muted ink. Color is never the only cue: each sits in its own labeled
// section above or below the cutoff rule, and left-out rows also drop to secondary text.
const TONE_CLASSES: Record<RowTone, { fill: string; ring: string; text: string }> = {
    pick: { fill: 'bg-(--showdown-blue)', ring: 'border-(--showdown-blue)', text: 'text-(--text-primary)' },
    miss: { fill: 'bg-(--text-tertiary)', ring: 'border-(--text-tertiary)', text: 'text-(--text-secondary)' },
    swapped: { fill: 'bg-(--text-tertiary)', ring: 'border-(--text-tertiary)', text: 'text-(--text-secondary)' },
};

type ScoreDomain = { lo: number; hi: number };

function scoreDomain(line: AlgorithmCutLine): ScoreDomain {
    const breakdowns = [...(line.picks ?? []), ...(line.near_misses ?? []), ...(line.swapped_out ?? [])]
        .map(p => p.breakdown)
        .filter((b): b is AlgorithmScoreBreakdown => !!b);
    const values = [line.pick_score, ...breakdowns.flatMap(b => [b.match, b.total])];
    let lo = Math.floor(Math.min(...values) - 1);
    let hi = Math.ceil(Math.max(...values) + 1);
    if (hi - lo < MIN_DOMAIN_SPAN) {
        const mid = (lo + hi) / 2;
        lo = Math.floor(mid - MIN_DOMAIN_SPAN / 2);
        hi = lo + MIN_DOMAIN_SPAN;
    }
    return { lo, hi };
}

function percentAt(value: number, { lo, hi }: ScoreDomain): number {
    return ((value - lo) / (hi - lo)) * 100;
}

function breakdownSentence(b: AlgorithmScoreBreakdown): string {
    return `Match ${formatScore(b.match)} · Team balance ${formatMargin(b.team_balance)} · Points fit ${formatMargin(b.points_fit)} = ${formatScore(b.total)}`;
}

// =============================================================================
// MARK: - ROWS
// =============================================================================

/** A hollow dot at the match score joined to a filled dot at the score the slot was judged on */
function ScorePlot({ breakdown, cutScore, domain, tone }: { breakdown: AlgorithmScoreBreakdown | null; cutScore: number; domain: ScoreDomain; tone: RowTone }) {
    const colors = TONE_CLASSES[tone];
    const cutAt = percentAt(cutScore, domain);
    return (
        <div className="relative h-5">
            <span aria-hidden className="absolute inset-y-0 border-l border-dashed border-(--showdown-red)" style={{ left: `${cutAt}%` }} />
            {breakdown && (() => {
                const matchAt = percentAt(breakdown.match, domain);
                const totalAt = percentAt(breakdown.total, domain);
                return (
                    <>
                        <span
                            aria-hidden
                            className={`absolute top-1/2 h-0.5 -translate-y-1/2 ${colors.fill}`}
                            style={{ left: `${Math.min(matchAt, totalAt)}%`, width: `${Math.abs(totalAt - matchAt)}%` }}
                        />
                        <span
                            aria-hidden
                            className={`absolute top-1/2 w-2 h-2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 bg-(--background-secondary) ${colors.ring}`}
                            style={{ left: `${matchAt}%` }}
                        />
                        <span
                            aria-hidden
                            className={`absolute top-1/2 w-2.5 h-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-(--background-secondary) ${colors.fill}`}
                            style={{ left: `${totalAt}%` }}
                        />
                    </>
                );
            })()}
        </div>
    );
}

function CutoffRow({ player, tone, cutScore, domain, reason, note, onOpen }: {
    player: AlgorithmCutLinePlayer;
    tone: RowTone;
    cutScore: number;
    domain: ScoreDomain;
    reason?: AlgorithmSelectionReason | null;
    /** Extra meta after the team and year, e.g. who a swapped-out card lost its slot to */
    note?: string;
    onOpen?: () => void;
}) {
    const { breakdown } = player;
    const reasonShort = reason ? SELECTION_REASON_SHORT[reason] : undefined;
    const title = [breakdown && breakdownSentence(breakdown), reason && reason !== 'WEIGHTED' && SELECTION_REASON_LABELS[reason], note]
        .filter(Boolean).join(' · ');
    const content = (
        <>
            <span className="flex flex-col min-w-0">
                <span className="flex items-center gap-1 min-w-0">
                    <span className={`font-display-upright text-[13px] leading-4 truncate ${TONE_CLASSES[tone].text}`}>{player.name}</span>
                    {reasonShort && <Plate variant="outline" size="sm" className="shrink-0">{reasonShort}</Plate>}
                </span>
                <span className="text-[11px] leading-4 text-(--text-tertiary) truncate">
                    {player.year} {player.team}{note && ` · ${note}`}
                </span>
            </span>
            <span className="text-[12px] tabular-nums text-right text-(--text-secondary)">{player.points ?? '—'}</span>
            <ScorePlot breakdown={breakdown} cutScore={cutScore} domain={domain} tone={tone} />
            <span className="hidden sm:block text-[12px] tabular-nums text-right text-(--text-secondary)">{breakdown ? formatScore(breakdown.match) : '—'}</span>
            <span className="hidden sm:block text-[12px] tabular-nums text-right text-(--text-secondary)">{breakdown ? formatMargin(breakdown.team_balance) : '—'}</span>
            <span className="hidden sm:block text-[12px] tabular-nums text-right text-(--text-secondary)">{breakdown ? formatMargin(breakdown.points_fit) : '—'}</span>
            <span className={`text-[13px] font-semibold tabular-nums text-right ${TONE_CLASSES[tone].text}`}>{breakdown ? formatScore(breakdown.total) : '—'}</span>
        </>
    );
    const rowClass = `${ROW_GRID_CLASS} w-full px-3 py-1 text-left`;
    return onOpen ? (
        <button type="button" onClick={onOpen} title={title} className={`${rowClass} hover:bg-(--background-tertiary) transition-colors cursor-pointer`}>
            {content}
        </button>
    ) : (
        <div title={title} className={rowClass}>{content}</div>
    );
}

function SectionLabel({ children }: { children: string }) {
    return <div className={`px-3 pt-2 pb-0.5 ${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>{children}</div>;
}

// =============================================================================
// MARK: - GROUP
// =============================================================================

function CutoffGroup({ line, openablePickIds, onOpenPick }: { line: AlgorithmCutLine; openablePickIds: Set<string>; onOpenPick: (id: string) => void }) {
    const domain = scoreDomain(line);
    // Highest first, so the closest calls on each side meet at the line
    const picks = [...(line.picks ?? [])].reverse();
    const nearMisses = line.near_misses ?? [];
    const swappedOut = line.swapped_out ?? [];
    const cutAt = percentAt(line.pick_score, domain);
    return (
        <section className="rounded-card border border-(--divider) bg-(--background-secondary) overflow-hidden">
            <header className="flex flex-wrap items-center gap-2 px-3 pt-2.5 pb-1.5">
                <Heading level="panel">{cutLineGroupLabel(line.group)}</Heading>
                {line.slot_count != null && <Plate variant="ink" size="sm" className="tabular-nums">{line.slot_count} card{line.slot_count === 1 ? '' : 's'}</Plate>}
                <span className="flex items-center gap-1.5 ml-auto text-[11px] text-(--text-secondary)">
                    Cutoff
                    <Plate variant="red" size="sm" className="tabular-nums">{formatScore(line.pick_score)}</Plate>
                </span>
            </header>

            <div className={`${ROW_GRID_CLASS} px-3 pb-1 border-b border-(--divider) ${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>
                <span>Player</span>
                <span className="text-right">Pts</span>
                <span className="flex justify-between tabular-nums normal-case font-normal">
                    <span>{domain.lo}</span>
                    <span>{domain.hi}</span>
                </span>
                <span className="hidden sm:block text-right">Match</span>
                <span className="hidden sm:block text-right">Team</span>
                <span className="hidden sm:block text-right">Fit</span>
                <span className="text-right">Score</span>
            </div>

            {picks.length > 0 && (
                <>
                    <SectionLabel>{picks.length < (line.slot_count ?? 0) ? `Made it · lowest ${picks.length}` : 'Made it'}</SectionLabel>
                    {picks.map(pick => (
                        <CutoffRow
                            key={pick.id}
                            player={pick}
                            tone="pick"
                            cutScore={line.pick_score}
                            domain={domain}
                            reason={pick.selection_reason}
                            onOpen={openablePickIds.has(pick.id) ? () => onOpenPick(pick.id) : undefined}
                        />
                    ))}
                </>
            )}

            {/* The cutoff rule, its label pinned to where the line sits in the plot column */}
            <div className={`${ROW_GRID_CLASS} px-3 py-1`}>
                <span className="col-span-2 h-px bg-(--showdown-red)" />
                <span className="relative h-4">
                    <span className="absolute inset-x-0 top-1/2 h-px bg-(--showdown-red)" />
                    <span
                        className={`absolute top-1/2 -translate-y-1/2 px-1 bg-(--background-secondary) ${CAPS_LABEL_CLASS} text-(--showdown-red) whitespace-nowrap ${cutAt > 50 ? '-translate-x-full' : ''}`}
                        style={{ left: `${cutAt}%` }}
                    >
                        Cutoff
                    </span>
                </span>
                <span className="col-span-1 sm:col-span-4 h-px bg-(--showdown-red)" />
            </div>

            {nearMisses.length > 0 && (
                <>
                    <SectionLabel>Just missed</SectionLabel>
                    {nearMisses.map(miss => (
                        <CutoffRow key={miss.id} player={miss} tone="miss" cutScore={line.pick_score} domain={domain} />
                    ))}
                </>
            )}

            {swappedOut.length > 0 && (
                <>
                    <SectionLabel>Swapped out for point buckets</SectionLabel>
                    {swappedOut.map(player => (
                        <CutoffRow
                            key={player.id}
                            player={player}
                            tone="swapped"
                            cutScore={line.pick_score}
                            domain={domain}
                            note={`for ${player.replaced_by}`}
                        />
                    ))}
                </>
            )}
            <div className="h-2" />
        </section>
    );
}

// =============================================================================
// MARK: - PANEL
// =============================================================================

function LegendKey() {
    return (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-(--text-secondary)">
            <span className="flex items-center gap-1.5">
                <span aria-hidden className="w-2 h-2 rounded-full border-2 border-(--showdown-blue)" />
                Match score
            </span>
            <span className="flex items-center gap-1.5">
                <span aria-hidden className="w-2.5 h-2.5 rounded-full bg-(--showdown-blue)" />
                Pick score
            </span>
            <span className="flex items-center gap-1.5">
                <span aria-hidden className="w-2.5 h-2.5 rounded-full bg-(--text-tertiary)" />
                Left out
            </span>
            <span className="flex items-center gap-1.5">
                <span aria-hidden className="h-3 border-l border-dashed border-(--showdown-red)" />
                Cutoff
            </span>
        </div>
    );
}

function CutoffSkeleton() {
    return (
        <div className="flex flex-col gap-3">
            {[0, 1].map(i => (
                <div key={i} className="rounded-card border border-(--divider) bg-(--background-secondary) p-3 flex flex-col gap-2 animate-pulse">
                    <div className="h-4 w-28 rounded-plate bg-(--background-tertiary)" />
                    {Array.from({ length: 8 }, (_, row) => (
                        <div key={row} className="h-6 rounded-plate bg-(--background-tertiary)" />
                    ))}
                </div>
            ))}
        </div>
    );
}

export function AlgorithmCutoff({ cutLines, isPreview, isRunning, openablePickIds, onOpenPick }: AlgorithmCutoffProps) {
    if (isRunning) {
        return <div className="p-3"><CutoffSkeleton /></div>;
    }
    if (cutLines.length === 0) {
        return (
            <EmptyState title="No cutoff yet.">
                Run the Algorithm to see where each slot group's cutoff fell: who just made it, who just missed, and why.
            </EmptyState>
        );
    }
    return (
        <div className="flex flex-col gap-3 p-3">
            <div className="flex flex-col gap-1.5">
                <p className="text-[12px] text-(--text-secondary) max-w-3xl">
                    Each slot group fills best score first until it's full. A player's match score (quality, playing time and career) is
                    moved up or down by team balance and points fit, which shift after every pick, so an early pick can sit below the final cutoff.
                    Picks marked MAN, LGND or TM MIN skipped the line.
                    {!isPreview && ' From your last run this session; the saved pool may have changed since.'}
                </p>
                <LegendKey />
            </div>
            {cutLines.map(line => (
                <CutoffGroup key={line.group} line={line} openablePickIds={openablePickIds} onOpenPick={onOpenPick} />
            ))}
        </div>
    );
}
