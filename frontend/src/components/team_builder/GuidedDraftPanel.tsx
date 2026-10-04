import { useEffect, useRef, useState } from 'react';
import {
    FaCircleCheck, FaCompass, FaBullseye, FaGaugeHigh, FaPlus, FaRotateRight, FaFlagCheckered,
    FaArrowRight, FaShuffle, FaListOl, FaMagnifyingGlass, FaArrowRotateLeft,
} from 'react-icons/fa6';

import { GUIDED_CORNERSTONES, GUIDED_FILL_ORDER_OPTIONS } from '../../api/userTeams';
import type { GuidedFillOrder, GuidedOption, GuidedRound, GuidedRoundRole } from '../../api/userTeams';
import type { GuidedDraftState } from '../../hooks/useGuidedDraft';
import { CardItemFromCardDatabaseRecord, CardItemSkeleton } from '../cards/CardItem';
import { CardDetail } from '../cards/CardDetail';
import { Modal } from '../shared/Modal';
import type { ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';
import { ProgressRing } from './ProgressRing';

type BucketProgress = { filled: number; target: number };

type Props = {
    state: GuidedDraftState;
    /** 'full' fills the desktop draft panel; 'docked' is the short strip pinned to the bottom of
     *  the screen on mobile, under the field view. */
    variant?: 'full' | 'docked';
    buckets: { lineup: BucketProgress; rotation: BucketProgress; bullpen: BucketProgress; bench: BucketProgress };
    rosterCount: number;
    rosterSize: number;
    currentPts: number;
    /** Team budget, or the drafter's one-off target for a team with no pts_limit. */
    budget: number | null;
    benchPtsMultiplier: number;
    order: GuidedFillOrder;
    onOrderChange: (order: GuidedFillOrder) => void;
    /** Team has no pts_limit and no one-off target has been chosen yet. */
    needsTarget: boolean;
    onSetTarget: (target: number) => void;
    onPick: (option: GuidedOption) => void;
    /** Set while the last pick is still saving. */
    pickDisabled: boolean;
    saveFailed: boolean;
    /** Leave guided mode for card search — shown in the docked header (which has no tabs) and as
     *  a fallback whenever a round has no options. */
    onExit?: () => void;
    /** Clear every pick and restart the draft from the first Cornerstone round. */
    onRestart?: () => void;
};

const OPTION_SKELETON_COUNT = 4;

/** Height of the docked strip — exported so the page can pad its scroll content to clear it. */
export const GUIDED_DOCK_HEIGHT_CLASS = 'h-65';

/** Fill-phase segments of the round stepper, in draft order, keyed to the round role that fills them. */
const FILL_SEGMENTS: { key: keyof Props['buckets']; label: string; role: GuidedRoundRole }[] = [
    { key: 'lineup', label: 'Lineup', role: 'field' },
    { key: 'rotation', label: 'Rotation', role: 'rotation' },
    { key: 'bullpen', label: 'Bullpen', role: 'bullpen' },
    { key: 'bench', label: 'Bench', role: 'bench' },
];

/**
 * Guided Draft: one round at a time, a handful of similarly priced options for a single roster
 * need. Opens with three Cornerstone rounds (Ace, Star, Closer), then fills the remaining
 * roster slot by slot. Rounds come from the server via `useGuidedDraft`.
 */
export function GuidedDraftPanel(props: Props) {
    const { state, variant = 'full', rosterCount, rosterSize, currentPts, budget, order, onOrderChange, needsTarget, onSetTarget, onExit, onRestart, pickDisabled } = props;
    // Nothing to restart before the first pick (or once the roster is complete).
    const restartButton = onRestart && rosterCount > 0 && !state.complete && (
        <HeaderIconButton icon={FaArrowRotateLeft} label="Start over" onClick={onRestart} disabled={pickDisabled} />
    );
    const docked = variant === 'docked';
    const { round } = state;
    const roundIndex = Math.min(rosterCount + 1, rosterSize);

    // After each pick, jump the options list back to its start so the next round's cards are
    // seen from the top (desktop grid) / first card (docked row) instead of where the last
    // round was left scrolled.
    const optionsScrollRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        optionsScrollRef.current?.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    }, [rosterCount]);

    const progressBar = (
        <div className="h-1 rounded-full overflow-hidden bg-(--background-quaternary)">
            <div
                className="h-full rounded-full bg-(--showdown-red) transition-all"
                style={{ width: `${rosterSize > 0 ? (rosterCount / rosterSize) * 100 : 0}%` }}
            />
        </div>
    );

    const target = round ? (
        <span className="flex items-center gap-1 whitespace-nowrap" title="Points target for this round">
            <FaBullseye className="text-(--showdown-red)" />
            ~{round.target_points} PTS <span className="font-semibold text-(--text-tertiary)">±{round.window}</span>
        </span>
    ) : (
        <span className="h-3.5 w-24 rounded bg-(--background-quaternary) animate-pulse" />
    );

    return (
        <div className={`flex flex-col min-h-0 ${docked ? GUIDED_DOCK_HEIGHT_CLASS : 'h-full'}`}>
            {docked ? (
                /* Compact one-line header — the full stepper doesn't fit in the dock. */
                <div className="flex flex-col gap-1.5 px-3 pt-2 pb-2 border-b border-(--divider) shrink-0">
                    <div className="flex items-center gap-2 min-w-0">
                        <FaCompass className="text-(--showdown-red) text-[12px] shrink-0" />
                        <span className="text-[11px] font-black tabular-nums text-(--text-tertiary) shrink-0">{roundIndex}/{rosterSize}</span>
                        {round
                            ? <span className="text-[13px] font-black uppercase text-(--text-primary) truncate">{round.round.label}</span>
                            : <span className="h-4 w-28 rounded bg-(--background-quaternary) animate-pulse" />}
                        <span className="ml-auto flex items-center gap-1.5 shrink-0 text-[10px] font-bold text-(--text-secondary)">
                            {target}
                            <OrderToggle order={order} onChange={onOrderChange} compact />
                            {restartButton}
                            {onExit && <HeaderIconButton icon={FaMagnifyingGlass} label="Search cards instead" onClick={onExit} />}
                        </span>
                    </div>
                    {progressBar}
                </div>
            ) : (
                <div className="flex flex-col gap-2.5 px-4 py-3 border-b border-(--divider) shrink-0">
                    <div className="flex items-end justify-between gap-3">
                        <div className="min-w-0">
                            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">
                                <span>Round <span className="tabular-nums text-(--text-primary)">{roundIndex}</span> of <span className="tabular-nums">{rosterSize}</span></span>
                                {round && <PhasePill phase={round.round.phase} />}
                            </div>
                            {round ? (
                                <div className="text-lg font-black uppercase text-(--text-primary) truncate">{round.round.label}</div>
                            ) : (
                                <div className="h-6 w-40 mt-1 rounded bg-(--background-quaternary) animate-pulse" />
                            )}
                        </div>
                        <div className="flex flex-col items-end gap-0.5 shrink-0 text-[11px] font-bold text-(--text-secondary)">
                            {target}
                            {budget != null && (
                                <span className="flex items-center gap-1 text-(--text-tertiary)">
                                    <FaGaugeHigh className="text-[10px]" /> {Math.max(0, budget - currentPts).toLocaleString()} PTS left
                                </span>
                            )}
                        </div>
                    </div>
                    {progressBar}
                    <div className="flex items-center gap-2">
                        <RoundStepper round={round} buckets={props.buckets} />
                        <OrderToggle order={order} onChange={onOrderChange} />
                        {restartButton}
                    </div>
                </div>
            )}

            <div ref={optionsScrollRef} className={`flex-1 min-h-0 ${docked ? 'overflow-x-auto overflow-y-hidden scrollbar-hide px-3 py-2.5' : 'overflow-y-auto scrollbar-hide p-4'}`}>
                {needsTarget
                    ? <GuidedTargetPrompt onSetTarget={onSetTarget} />
                    : <GuidedOptions {...props} docked={docked} />}
            </div>
        </div>
    );
}

/** The current round's options (or its loading / empty / error / complete state). */
function GuidedOptions({ state, docked, currentPts, budget, benchPtsMultiplier, onPick, pickDisabled, saveFailed, onExit }: Props & { docked: boolean }) {
    const { round, loading, complete, error, retry } = state;
    // Option whose full card detail is open in the modal.
    const [detailOption, setDetailOption] = useState<GuidedOption | null>(null);
    // Docked: one horizontally-scrolling row that snaps card-by-card. Full: a wrapping grid.
    const listClass = docked
        ? 'flex gap-2.5 h-full snap-x snap-mandatory'
        : 'grid grid-cols-1 xl:grid-cols-2 gap-3';
    const itemClass = docked ? 'w-80 shrink-0 snap-start' : '';

    const noticeButtonClass = 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) cursor-pointer transition-colors';
    const retryButton = (
        <div className="flex flex-wrap justify-center gap-2">
            <button type="button" onClick={retry} className={noticeButtonClass}>
                <FaRotateRight className="text-[10px]" /> Try again
            </button>
            {/* The round can't be filled from its price band — let the drafter search for this slot themselves. */}
            {onExit && (
                <button type="button" onClick={onExit} className={noticeButtonClass}>
                    <FaMagnifyingGlass className="text-[10px]" /> Search cards
                </button>
            )}
        </div>
    );
    const notice = (children: React.ReactNode) => (
        <div className={`flex flex-col items-center justify-center gap-3 text-center ${docked ? 'h-full' : 'py-10'}`}>{children}</div>
    );

    if (complete) {
        return notice(<>
            <FaFlagCheckered className="text-2xl text-(--success)" />
            <div className="text-[13px] font-bold text-(--text-primary)">Roster complete</div>
        </>);
    }
    if (error) {
        return notice(<><p className="text-[12px] text-red-500">{error}</p>{retryButton}</>);
    }
    if (round && !loading && round.options.length === 0) {
        return notice(<>
            <p className="text-[12px] text-(--text-tertiary)">No cards fit this round within your team's sets, filters, and budget.</p>
            {retryButton}
        </>);
    }

    return (
        <>
            {saveFailed && (
                <p className="mb-3 text-[11px] text-red-500 bg-red-500/10 rounded-lg px-3 py-2">
                    Couldn't save your last pick. It'll retry on your next change.
                </p>
            )}
            <div className={listClass}>
                {loading || !round
                    ? Array.from({ length: OPTION_SKELETON_COUNT }, (_, i) => (
                        <div key={i} className={`${itemClass} flex flex-col gap-1.5 rounded-xl border border-(--divider) p-1.5`}>
                            <div className="h-9 rounded-lg bg-(--background-quaternary) animate-pulse" />
                            <CardItemSkeleton className="h-28" />
                        </div>
                    ))
                    : round.options.map(option => (
                        <GuidedOptionCard
                            key={option.card.card_id || option.card.id}
                            className={itemClass}
                            option={option}
                            currentPts={currentPts}
                            budget={budget}
                            benchPtsMultiplier={benchPtsMultiplier}
                            onPick={onPick}
                            onOpenDetail={setDetailOption}
                            disabled={pickDisabled}
                        />
                    ))}
            </div>

            {/* Kept mounted and only hidden (same as FieldView / ShowdownCardSearch): CardDetail
                fetches by `cardId` only when that prop *changes* after mount, so mounting it fresh
                with the id already set would never load the card. */}
            <div className={detailOption ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={() => setDetailOption(null)} isVisible={!!detailOption}>
                    <CardDetail
                        showdownBotCardData={detailOption?.card.card_data ? { card: detailOption.card.card_data } as ShowdownBotCardAPIResponse : undefined}
                        cardId={detailOption?.card.card_id}
                        hideTrendGraphs={true}
                        context="explore"
                        parent="modal"
                        onDraft={detailOption ? () => { onPick(detailOption); setDetailOption(null); } : undefined}
                        draftDisabled={pickDisabled}
                    />
                </Modal>
            </div>
        </>
    );
}

/** One option: the Draft button sits directly on top of its card, framed together so it's
 *  unambiguous which card the button drafts. */
function GuidedOptionCard({ option, currentPts, budget, benchPtsMultiplier, onPick, onOpenDetail, disabled, className = '' }: {
    option: GuidedOption;
    currentPts: number;
    budget: number | null;
    benchPtsMultiplier: number;
    onPick: (option: GuidedOption) => void;
    /** Tapping the card itself opens its full CardDetail. */
    onOpenDetail: (option: GuidedOption) => void;
    disabled: boolean;
    className?: string;
}) {
    const isBench = option.roster_position === 'BE';
    const cost = isBench ? Math.round(option.card.points * benchPtsMultiplier) : option.card.points;
    const projected = currentPts + cost;
    const overBudget = budget != null && projected > budget;
    return (
        <div className={`${className} flex flex-col gap-1.5 rounded-xl border border-(--divider) bg-(--background-secondary) p-1.5 transition-colors hover:border-(--showdown-red)/60`}>
            <button
                type="button"
                onClick={() => onPick(option)}
                disabled={disabled}
                className="flex items-center justify-between gap-2 px-3 h-9 rounded-lg text-[12px] font-bold text-white bg-(--showdown-red) hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-opacity"
            >
                <span className="flex items-center gap-1.5">
                    <FaPlus className="text-[10px]" /> Draft
                    <FaArrowRight className="text-[9px] opacity-70" /> {option.roster_position}
                </span>
                <span className={`tabular-nums text-[11px] font-semibold ${overBudget ? 'text-red-200' : 'opacity-80'}`}>
                    {currentPts} → {projected} PTS
                </span>
            </button>
            <CardItemFromCardDatabaseRecord
                card={option.card}
                cardPtsMultiplier={isBench ? benchPtsMultiplier : undefined}
                onClick={() => onOpenDetail(option)}
            />
        </div>
    );
}

/** Small icon-only action in the panel header. */
function HeaderIconButton({ icon: Icon, label, onClick, disabled = false }: { icon: React.ComponentType<{ className?: string }>; label: string; onClick: () => void; disabled?: boolean }) {
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            className="p-1.5 shrink-0 rounded-lg text-(--text-tertiary) hover:text-(--text-primary) hover:bg-(--background-tertiary) disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            aria-label={label}
            title={label}
        >
            <Icon className="text-[11px]" />
        </button>
    );
}

/** In order / Random switch for how Fill rounds choose the next roster need. */
function OrderToggle({ order, onChange, compact = false }: { order: GuidedFillOrder; onChange: (order: GuidedFillOrder) => void; compact?: boolean }) {
    return (
        <div className="flex shrink-0 rounded-lg bg-(--background-tertiary) p-0.5" role="radiogroup" aria-label="Round order">
            {GUIDED_FILL_ORDER_OPTIONS.map(({ value, label }) => {
                const Icon = value === 'random' ? FaShuffle : FaListOl;
                const active = order === value;
                return (
                    <button
                        key={value}
                        type="button"
                        role="radio"
                        aria-checked={active}
                        onClick={() => onChange(value)}
                        title={value === 'random' ? 'Each round targets a random open roster spot' : 'Rounds walk the roster: lineup, rotation, bullpen, bench'}
                        className={`flex items-center gap-1 rounded-md px-1.5 py-1 text-[10px] font-bold whitespace-nowrap cursor-pointer transition-colors ${
                            active ? 'bg-(--background-primary) text-(--text-primary) shadow-sm' : 'text-(--text-tertiary) hover:text-(--text-primary)'
                        }`}
                    >
                        <Icon className="text-[10px]" />
                        {!compact && label}
                    </button>
                );
            })}
        </div>
    );
}

function PhasePill({ phase }: { phase: GuidedRound['round']['phase'] }) {
    return phase === 'cornerstone' ? (
        <span className="rounded-full px-1.5 py-px bg-amber-500/15 text-amber-600 dark:text-amber-400">Cornerstone</span>
    ) : (
        <span className="rounded-full px-1.5 py-px bg-sky-500/15 text-sky-600 dark:text-sky-300">Fill</span>
    );
}

/** Where the draft stands: the three cornerstone picks, then each roster bucket's fill, with
 *  the current round's segment highlighted. */
function RoundStepper({ round, buckets }: { round: GuidedRound | null; buckets: Props['buckets'] }) {
    const segmentClass = (active: boolean) =>
        `flex items-center gap-1 rounded-lg px-1.5 py-1 text-[10px] font-bold whitespace-nowrap transition-colors ${
            active ? 'bg-(--showdown-red)/10 text-(--showdown-red) ring-1 ring-(--showdown-red)/40' : 'text-(--text-tertiary)'
        }`;

    return (
        <div className="flex flex-1 min-w-0 items-center gap-1 py-1 overflow-x-auto scrollbar-hide px-1">
            {GUIDED_CORNERSTONES.map(({ role, label }, i) => {
                const active = round?.round.phase === 'cornerstone' && round.round.role === role;
                const done = !!round?.cornerstones[role];
                return (
                    <span key={role} className={segmentClass(active)}>
                        {done
                            ? <FaCircleCheck className="text-[10px] text-(--success)" />
                            : active
                                ? <span className="w-1.5 h-1.5 rounded-full bg-(--showdown-red) animate-pulse" />
                                : <span className="tabular-nums">{i + 1}.</span>}
                        {label}
                    </span>
                );
            })}
            <FaCompass className="mx-1 text-[10px] text-(--text-tertiary) opacity-50 shrink-0" />
            {FILL_SEGMENTS.map(({ key, label, role }) => {
                const bucket = buckets[key];
                const active = round?.round.phase === 'fill' && round.round.role === role;
                return (
                    <span key={key} className={segmentClass(active)} title={`${label}: ${bucket.filled}/${bucket.target}`}>
                        {bucket.filled >= bucket.target
                            ? <FaCircleCheck className="text-[10px] text-(--success)" />
                            : <ProgressRing filled={bucket.filled} target={bucket.target} size={10} />}
                        {label}
                        <span className="tabular-nums font-semibold opacity-70">{bucket.filled}/{bucket.target}</span>
                    </span>
                );
            })}
        </div>
    );
}

/** Teams without a pts_limit pick a one-off budget for the guided draft to pace against. */
function GuidedTargetPrompt({ onSetTarget }: { onSetTarget: (target: number) => void }) {
    const [target, setTarget] = useState(5000);
    return (
        <div className="flex flex-col gap-3 max-w-sm">
            <p className="text-[12px] text-(--text-secondary)">
                This team has no points cap. Pick a budget so each round can offer options at the right price.
                It won't change the team's settings.
            </p>
            <label className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide">
                Target Points
                <input
                    type="number"
                    min={100}
                    step={50}
                    value={target}
                    onChange={e => setTarget(Math.max(0, Number(e.target.value)))}
                    className="mt-1 w-full rounded-lg border border-(--divider) bg-(--background-secondary) px-3 py-2 text-[13px] font-bold text-(--text-primary) normal-case"
                />
            </label>
            <button
                type="button"
                onClick={() => onSetTarget(target)}
                disabled={target < 100}
                className="flex items-center justify-center gap-1.5 rounded-lg py-2 text-[13px] font-bold text-white bg-(--showdown-red) hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-opacity"
            >
                Start Guided Draft <FaArrowRight className="text-[11px]" />
            </button>
        </div>
    );
}
