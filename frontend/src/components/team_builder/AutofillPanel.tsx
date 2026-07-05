import { useState, useMemo } from 'react';
import { FaXmark, FaWandMagicSparkles, FaSpinner } from 'react-icons/fa6';

import type { AutofillStrategy, PtsDistribution } from '../../api/userTeams';
import {
    AUTOFILL_PRESETS,
    PITCHING_STRATEGY_OPTIONS,
    HITTING_STRATEGY_OPTIONS,
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
    ptsLimit: number;
    bucketSizes: BucketSizes;
    onConfirm: (strategy: AutofillStrategy) => Promise<void>;
    onClose: () => void;
};

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

function defaultBucketPts(ptsLimit: number, dist: PtsDistribution): BucketPts {
    return {
        offense:  Math.round(ptsLimit * dist.offense),
        rotation: Math.round(ptsLimit * dist.rotation),
        bullpen:  Math.round(ptsLimit * dist.bullpen),
        bench:    Math.round(ptsLimit * dist.bench),
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

export function AutofillPanel({ ptsLimit, bucketSizes, onConfirm, onClose }: Props) {
    const [bucketPts, setBucketPts] = useState<BucketPts>(
        () => defaultBucketPts(ptsLimit, DEFAULT_PTS_DISTRIBUTION)
    );
    const [activePreset, setActivePreset] = useState<string>('Balanced');
    const [pitchingStrategy, setPitchingStrategy] = useState<string | null>(null);
    const [hittingStrategy, setHittingStrategy] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const totalAllocated = useMemo(
        () => bucketPts.offense + bucketPts.rotation + bucketPts.bullpen + bucketPts.bench,
        [bucketPts]
    );

    function applyPreset(label: string, dist: PtsDistribution) {
        setBucketPts(defaultBucketPts(ptsLimit, dist));
        setActivePreset(label);
    }

    function updateBucket(changedKey: keyof PtsDistribution, newPts: number) {
        setBucketPts(prev => {
            const otherKeys = (Object.keys(prev) as (keyof PtsDistribution)[]).filter(k => k !== changedKey);
            const remaining = ptsLimit - newPts;
            const otherTotal = otherKeys.reduce((sum, k) => sum + prev[k], 0);
            const updated = { ...prev, [changedKey]: newPts };
            const lastKey = otherKeys[otherKeys.length - 1];

            if (otherTotal === 0) {
                const share = Math.round(remaining / otherKeys.length / 10) * 10;
                otherKeys.forEach(k => { updated[k] = share; });
                updated[lastKey] = remaining - share * (otherKeys.length - 1);
            } else {
                let distributed = 0;
                for (const k of otherKeys.slice(0, -1)) {
                    const share = Math.round((prev[k] / otherTotal) * remaining / 10) * 10;
                    updated[k] = share;
                    distributed += share;
                }
                // Last bucket absorbs remainder — may not be a multiple of 10 but stays exact
                updated[lastKey] = remaining - distributed;
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
                pts_distribution: distributionFromPts(bucketPts, ptsLimit),
                pitching_strategy: pitchingStrategy,
                hitting_strategy: hittingStrategy,
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
                            Budget: <span className="font-bold text-(--text-primary)">{ptsLimit.toLocaleString()} pts</span>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        className="text-(--text-tertiary) hover:text-(--text-primary) transition-colors"
                    >
                        <FaXmark />
                    </button>
                </div>

                <div className="px-4 py-3 space-y-4 max-h-[70vh] overflow-y-auto">
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
                                            min={0}
                                            max={ptsLimit}
                                            step={sliderStep}
                                            value={pts}
                                            onChange={e => updateBucket(key, Number(e.target.value))}
                                            className="w-full accent-(--showdown-red)"
                                        />
                                    </div>
                                );
                            })}
                        </div>

                        {/* Budget summary */}
                        <div className="flex items-center justify-between mt-2 rounded-lg px-3 py-1.5 text-[11px] font-semibold bg-(--background-secondary) text-(--text-secondary)">
                            <span>Total allocated</span>
                            <span>{totalAllocated.toLocaleString()} / {ptsLimit.toLocaleString()} pts</span>
                        </div>
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

                    {error && (
                        <p className="text-[11px] text-red-500 bg-red-500/10 rounded-lg px-3 py-2">
                            {error}
                        </p>
                    )}
                </div>

                {/* Footer */}
                <div className="px-4 pb-4 pt-3 border-t border-(--divider)">
                    <button
                        type="button"
                        onClick={handleConfirm}
                        disabled={loading}
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
                </div>
            </div>
        </div>
    );
}
