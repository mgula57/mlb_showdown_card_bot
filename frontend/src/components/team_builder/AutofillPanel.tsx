import { useState, useMemo } from 'react';
import { FaXmark, FaWandMagicSparkles, FaSpinner } from 'react-icons/fa6';

import type { AutofillStrategy, PtsDistribution } from '../../api/userTeams';
import {
    AUTOFILL_PRESETS,
    PITCHING_STRATEGY_OPTIONS,
    HITTING_STRATEGY_OPTIONS,
    DEFENSE_STRATEGY_OPTIONS,
    CATCHER_DEFENSE_STRATEGY_OPTIONS,
    DEFAULT_PTS_DISTRIBUTION,
} from '../../api/userTeams';

type BucketSizes = {
    offense: number;   // always 9
    rotation: number;  // num_starters
    bench: number;     // min_bench
    bullpen: number;   // min_bullpen
};

type BucketPts = Record<keyof PtsDistribution, number>;

type Props = {
    /** null when the team has no points cap — the user picks a one-off target instead. */
    ptsLimit: number | null;
    bucketSizes: BucketSizes;
    /** Points already spent per bucket from manual draft picks — acts as a floor for each slider. */
    existingPts: BucketPts;
    /** Number of players already on the roster. Non-zero enables the "replace existing" toggle. */
    existingPickCount: number;
    onConfirm: (strategy: AutofillStrategy) => Promise<void>;
    onClose: () => void;
};

const ZERO_PTS: BucketPts = { offense: 0, rotation: 0, bullpen: 0, bench: 0 };

const BUCKET_LABELS: { key: keyof PtsDistribution; label: string }[] = [
    { key: 'offense', label: 'Lineup' },
    { key: 'rotation', label: 'Rotation' },
    { key: 'bullpen', label: 'Bullpen' },
    { key: 'bench', label: 'Bench' },
];

function distributionFromPts(pts: BucketPts, ptsLimit: number): PtsDistribution {
    const total = ptsLimit || 1;
    return {
        offense:  pts.offense  / total,
        rotation: pts.rotation / total,
        bullpen:  pts.bullpen  / total,
        bench:    pts.bench    / total,
    };
}

function defaultBucketPts(ptsLimit: number, dist: PtsDistribution, floors: BucketPts): BucketPts {
    return {
        offense:  Math.max(floors.offense,  Math.round(ptsLimit * dist.offense)),
        rotation: Math.max(floors.rotation, Math.round(ptsLimit * dist.rotation)),
        bullpen:  Math.max(floors.bullpen,  Math.round(ptsLimit * dist.bullpen)),
        bench:    Math.max(floors.bench,    Math.round(ptsLimit * dist.bench)),
    };
}

function StrategyPill({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={[
                'px-2.5 py-1 rounded-full text-[11px] font-semibold border transition-colors',
                active
                    ? 'bg-(--showdown-red) border-(--showdown-red) text-white'
                    : 'bg-transparent border-(--divider) text-(--text-secondary) hover:border-(--text-tertiary)',
            ].join(' ')}
        >
            {label}
        </button>
    );
}

export function AutofillPanel({ ptsLimit, bucketSizes, existingPts, existingPickCount, onConfirm, onClose }: Props) {
    const hasCap = ptsLimit != null;

    // When "replace existing" is on the server wipes the roster first, so manual picks no
    // longer act as per-bucket floors — the whole budget is free to allocate.
    const [replaceExisting, setReplaceExisting] = useState(false);
    const floors = replaceExisting ? ZERO_PTS : existingPts;
    const totalFloors = floors.offense + floors.rotation + floors.bullpen + floors.bench;

    // When the team has no points cap, the user picks a one-off target budget first.
    const [customTarget, setCustomTarget] = useState<number>(Math.max(1000, totalFloors));
    const [targetConfirmed, setTargetConfirmed] = useState(hasCap);
    const effectiveLimit = hasCap ? ptsLimit : customTarget;

    const [bucketPts, setBucketPts] = useState<BucketPts>(
        () => defaultBucketPts(effectiveLimit, DEFAULT_PTS_DISTRIBUTION, floors)
    );
    const [activePreset, setActivePreset] = useState<string>('Balanced');
    const [pitchingStrategy, setPitchingStrategy] = useState<string | null>(null);
    const [hittingStrategy, setHittingStrategy] = useState<string | null>(null);
    const [defenseStrategy, setDefenseStrategy] = useState<string | null>(null);
    const [catcherDefenseStrategy, setCatcherDefenseStrategy] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const totalAllocated = useMemo(
        () => bucketPts.offense + bucketPts.rotation + bucketPts.bullpen + bucketPts.bench,
        [bucketPts]
    );

    const overBudget = totalFloors > effectiveLimit;

    // Highest a bucket can go without pushing the total past effectiveLimit, given the other buckets' floors
    function bucketMax(key: keyof PtsDistribution): number {
        const otherFloorsTotal = totalFloors - floors[key];
        return Math.max(floors[key], effectiveLimit - otherFloorsTotal);
    }

    function applyPreset(label: string, dist: PtsDistribution) {
        setBucketPts(defaultBucketPts(effectiveLimit, dist, floors));
        setActivePreset(label);
    }

    function toggleReplaceExisting() {
        const next = !replaceExisting;
        setReplaceExisting(next);
        // Re-seed the sliders against the new floors (zero when wiping, manual-pick pts otherwise).
        const dist = AUTOFILL_PRESETS.find(p => p.label === activePreset)?.distribution ?? DEFAULT_PTS_DISTRIBUTION;
        setBucketPts(defaultBucketPts(effectiveLimit, dist, next ? ZERO_PTS : existingPts));
        if (activePreset === 'Custom') setActivePreset('Balanced');
    }

    function confirmTarget() {
        setBucketPts(defaultBucketPts(customTarget, DEFAULT_PTS_DISTRIBUTION, floors));
        setActivePreset('Balanced');
        setTargetConfirmed(true);
    }

    function updateBucket(changedKey: keyof PtsDistribution, rawNewPts: number) {
        setBucketPts(prev => {
            const newPts = Math.min(Math.max(rawNewPts, floors[changedKey]), bucketMax(changedKey));
            const otherKeys = (Object.keys(prev) as (keyof PtsDistribution)[]).filter(k => k !== changedKey);
            const remaining = effectiveLimit - newPts;
            const otherFloorsTotal = otherKeys.reduce((sum, k) => sum + floors[k], 0);
            // Points left to freely distribute among the other buckets, above their floors
            const distributable = Math.max(0, remaining - otherFloorsTotal);
            const otherAboveFloorTotal = otherKeys.reduce((sum, k) => sum + Math.max(0, prev[k] - floors[k]), 0);
            const updated = { ...prev, [changedKey]: newPts };
            const lastKey = otherKeys[otherKeys.length - 1];

            if (otherAboveFloorTotal === 0) {
                const share = Math.round(distributable / otherKeys.length / 10) * 10;
                otherKeys.forEach(k => { updated[k] = floors[k] + share; });
                updated[lastKey] = floors[lastKey] + (distributable - share * (otherKeys.length - 1));
            } else {
                let distributed = 0;
                for (const k of otherKeys.slice(0, -1)) {
                    const share = Math.round((prev[k] - floors[k]) / otherAboveFloorTotal * distributable / 10) * 10;
                    updated[k] = floors[k] + share;
                    distributed += share;
                }
                // Last bucket absorbs remainder — may not be a multiple of 10 but stays exact
                updated[lastKey] = floors[lastKey] + (distributable - distributed);
            }

            return updated;
        });
        setActivePreset('Custom');
    }

    async function handleConfirm() {
        setError(null);
        setLoading(true);
        try {
            await onConfirm({
                pts_distribution: distributionFromPts(bucketPts, effectiveLimit),
                pitching_strategy: pitchingStrategy,
                hitting_strategy: hittingStrategy,
                defense_strategy: defenseStrategy,
                catcher_defense_strategy: catcherDefenseStrategy,
                replace_existing: replaceExisting,
                ...(hasCap ? {} : { pts_target: effectiveLimit }),
            });
            onClose();
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Autofill failed');
        } finally {
            setLoading(false);
        }
    }

    const sliderStep = 10;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            onClick={onClose}
        >
            <div
                className="bg-(--background-primary) rounded-2xl w-full max-w-sm shadow-2xl border border-(--divider) overflow-hidden"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 pt-4 pb-3 border-b border-(--divider)">
                    <div>
                        <div className="text-[13px] font-bold text-(--text-primary) flex items-center gap-1.5">
                            <FaWandMagicSparkles className="text-(--showdown-red)" />
                            Autofill Roster
                        </div>
                        <div className="text-[11px] text-(--text-secondary) mt-0.5">
                            {targetConfirmed ? (
                                <>Budget: <span className="font-bold text-(--text-primary)">{effectiveLimit.toLocaleString()} pts</span></>
                            ) : (
                                'This team has no points cap — pick a target to autofill against'
                            )}
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        className="text-(--text-tertiary) hover:text-(--text-primary) transition-colors hover:bg-(--divider) rounded-md p-1 cursor-pointer"
                    >
                        <FaXmark />
                    </button>
                </div>

                {existingPickCount > 0 && (
                    <div className="px-4 pt-3">
                        <button
                            type="button"
                            role="switch"
                            aria-checked={replaceExisting}
                            onClick={toggleReplaceExisting}
                            className="w-full flex items-center gap-3 rounded-lg border border-(--divider) bg-(--background-secondary) px-3 py-2.5 text-left cursor-pointer hover:border-(--text-tertiary) transition-colors"
                        >
                            <span className={[
                                'relative shrink-0 w-9 h-5 rounded-full transition-colors',
                                replaceExisting ? 'bg-(--showdown-red)' : 'bg-(--divider)',
                            ].join(' ')}>
                                <span className={[
                                    'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform',
                                    replaceExisting ? 'translate-x-4' : 'translate-x-0',
                                ].join(' ')} />
                            </span>
                            <span className="min-w-0">
                                <span className="block text-[12px] font-bold text-(--text-primary)">
                                    Replace existing roster
                                </span>
                                <span className="block text-[10.5px] text-(--text-tertiary) leading-snug">
                                    {replaceExisting
                                        ? `All ${existingPickCount} current player${existingPickCount !== 1 ? 's' : ''} will be cleared and re-drafted.`
                                        : `Keep the ${existingPickCount} current player${existingPickCount !== 1 ? 's' : ''} and fill the rest.`}
                                </span>
                            </span>
                        </button>
                    </div>
                )}

                {!targetConfirmed ? (
                    <div className="px-4 py-4 space-y-3">
                        <p className="text-[12px] text-(--text-secondary)">
                            Set a one-off points target for this autofill. It won't change the team's settings.
                        </p>
                        <div>
                            <label className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide mb-1 block">
                                Target Points
                            </label>
                            <input
                                type="number"
                                min={totalFloors}
                                step={50}
                                value={customTarget}
                                onChange={e => setCustomTarget(Math.max(0, Number(e.target.value)))}
                                className="w-full rounded-lg border border-(--divider) bg-(--background-secondary) px-3 py-2 text-[13px] font-bold text-(--text-primary)"
                            />
                            {totalFloors > 0 && (
                                <div className="text-[10px] text-(--text-tertiary) mt-1">
                                    {totalFloors.toLocaleString()} pts already drafted — target must be at least that much
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                <div className="px-4 py-3 space-y-4 max-h-[60vh] overflow-y-auto">
                    {/* Layer 1: Points Distribution */}
                    <section>
                        <div className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide mb-2">
                            Points Distribution
                        </div>

                        {/* Preset pills */}
                        <div className="flex flex-wrap gap-1.5 mb-3">
                            {AUTOFILL_PRESETS.map(p => (
                                <StrategyPill
                                    key={p.label}
                                    label={p.label}
                                    active={activePreset === p.label}
                                    onClick={() => applyPreset(p.label, p.distribution)}
                                />
                            ))}
                            <StrategyPill
                                label="Custom"
                                active={activePreset === 'Custom'}
                                onClick={() => {}}
                            />
                        </div>

                        {/* Sliders */}
                        <div className="space-y-3">
                            {BUCKET_LABELS.map(({ key, label }) => {
                                const pts = bucketPts[key];
                                const slots = bucketSizes[key];
                                const avg = slots > 0 ? Math.round(pts / slots) : 0;
                                const floor = floors[key];
                                return (
                                    <div key={key}>
                                        <div className="flex items-baseline justify-between mb-1">
                                            <span className="text-[11px] font-semibold text-(--text-secondary)">
                                                {label}
                                            </span>
                                            <div className="flex items-baseline gap-2">
                                                <span className="text-[13px] font-bold text-(--text-primary)">
                                                    {pts.toLocaleString()} pts
                                                </span>
                                                <span className="text-[10px] text-(--text-tertiary)">
                                                    ~{avg}/player · {slots} slots
                                                </span>
                                            </div>
                                        </div>
                                        <input
                                            type="range"
                                            min={floor}
                                            max={bucketMax(key)}
                                            step={sliderStep}
                                            value={pts}
                                            onChange={e => updateBucket(key, Number(e.target.value))}
                                            className="w-full accent-(--showdown-red)"
                                        />
                                        {floor > 0 && (
                                            <div className="text-[10px] text-(--text-tertiary) mt-0.5">
                                                {floor.toLocaleString()} pts already drafted
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Budget summary */}
                        <div className={[
                            'flex items-center justify-between mt-2 rounded-lg px-3 py-1.5 text-[11px] font-semibold',
                            totalAllocated > effectiveLimit
                                ? 'bg-red-500/10 text-red-500'
                                : 'bg-(--background-secondary) text-(--text-secondary)',
                        ].join(' ')}>
                            <span>Total allocated</span>
                            <span>{totalAllocated.toLocaleString()} / {effectiveLimit.toLocaleString()} pts</span>
                        </div>
                        {overBudget && (
                            <p className="text-[11px] text-red-500 bg-red-500/10 rounded-lg px-3 py-2 mt-2">
                                Manually drafted picks already total {totalFloors.toLocaleString()} pts, over the {effectiveLimit.toLocaleString()} pt budget. {hasCap ? 'Raise the pts limit or remove picks before autofilling.' : 'Pick a higher target or remove picks before autofilling.'}
                            </p>
                        )}
                    </section>

                    {/* Layer 2: Pitching Strategy */}
                    <section>
                        <div className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide mb-2">
                            Pitching Focus
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                            {PITCHING_STRATEGY_OPTIONS.map(opt => (
                                <StrategyPill
                                    key={String(opt.value)}
                                    label={opt.label}
                                    active={pitchingStrategy === opt.value}
                                    onClick={() => setPitchingStrategy(opt.value)}
                                />
                            ))}
                        </div>
                    </section>

                    {/* Layer 3: Hitting Strategy */}
                    <section>
                        <div className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide mb-2">
                            Hitting Focus
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                            {HITTING_STRATEGY_OPTIONS.map(opt => (
                                <StrategyPill
                                    key={String(opt.value)}
                                    label={opt.label}
                                    active={hittingStrategy === opt.value}
                                    onClick={() => setHittingStrategy(opt.value)}
                                />
                            ))}
                        </div>
                    </section>

                    {/* Layer 4: Defense Strategy */}
                    <section>
                        <div className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide mb-2">
                            Defense Priority
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                            {DEFENSE_STRATEGY_OPTIONS.map(opt => (
                                <StrategyPill
                                    key={String(opt.value)}
                                    label={opt.label}
                                    active={defenseStrategy === opt.value}
                                    onClick={() => setDefenseStrategy(opt.value)}
                                />
                            ))}
                        </div>
                    </section>

                    {/* Layer 5: Catcher Defense Strategy */}
                    <section>
                        <div className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide mb-2">
                            Catcher Defense Priority
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                            {CATCHER_DEFENSE_STRATEGY_OPTIONS.map(opt => (
                                <StrategyPill
                                    key={String(opt.value)}
                                    label={opt.label}
                                    active={catcherDefenseStrategy === opt.value}
                                    onClick={() => setCatcherDefenseStrategy(opt.value)}
                                />
                            ))}
                        </div>
                    </section>

                </div>
                )}

                {/* Footer */}
                <div className="flex flex-col gap-2 px-4 pb-4 pt-3 border-t border-(--divider)">
                    {error && (
                        <div className="bg-red-500/15 border border-red-500/30 rounded-lg px-3 py-2.5 space-y-2">
                            <div className="text-[12px] font-semibold text-red-600">
                                Autofill couldn't complete
                            </div>
                            <p className="text-[11px] text-red-600/90 leading-snug">
                                {error}
                            </p>
                        </div>
                    )}
                    {!targetConfirmed ? (
                        <button
                            type="button"
                            onClick={confirmTarget}
                            disabled={customTarget < totalFloors}
                            className="w-full flex cursor-pointer items-center justify-center gap-2 rounded-xl py-2.5 text-[13px] font-bold text-white bg-linear-to-r from-blue-500 to-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                        >
                            Continue
                        </button>
                    ) : (
                        <button
                            type="button"
                            onClick={handleConfirm}
                            disabled={loading || overBudget || totalAllocated > effectiveLimit}
                            className="w-full flex cursor-pointer items-center justify-center gap-2 rounded-xl py-2.5 text-[13px] font-bold text-white bg-linear-to-r from-blue-500 to-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                        >
                            {loading ? (
                                <>
                                    <FaSpinner className="animate-spin" />
                                    Filling…
                                </>
                            ) : (
                                <>
                                    <FaWandMagicSparkles />
                                    Fill Roster
                                </>
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
