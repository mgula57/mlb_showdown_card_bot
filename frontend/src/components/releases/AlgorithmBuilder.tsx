import { useState } from 'react';
import { FaWandMagicSparkles, FaSpinner, FaTriangleExclamation, FaStar, FaCalendarDays, FaChevronDown } from 'react-icons/fa6';
import type { ReleaseEdition, AlgorithmConfig, AlgorithmPlayerTypeDistribution, AlgorithmPreviewResult } from '../../api/releases';
import { previewAlgorithm, updateEdition } from '../../api/releases';
import { showdownSets } from '../shared/SiteSettingsContext';
import FormInput from '../customs/FormInput';
import FormEnabler from '../customs/FormEnabler';
import FormDropdown from '../customs/FormDropdown';
import MultiSelect from '../shared/MultiSelect';
import PercentageSlider from '../shared/PercentageSlider';
import { useAuth } from '../auth/AuthContext';

type AlgorithmBuilderProps = {
    releaseId: string;
    edition: ReleaseEdition;
    token?: string;
    defaultShowdownSet?: string | null;
    onPreviewResult: (result: AlgorithmPreviewResult) => void;
};

const DEFAULT_PLAYER_TYPE_DISTRIBUTION: AlgorithmPlayerTypeDistribution = {
    hitters_percentage: 0.65,
    starters_percentage: 0.20,
    relievers_percentage: 0.15,
};


const DISTRIBUTION_ROWS: { key: keyof AlgorithmPlayerTypeDistribution; label: string; fillClassName: string }[] = [
    { key: 'hitters_percentage', label: 'Hitters', fillClassName: 'bg-(--showdown-blue)' },
    { key: 'starters_percentage', label: 'Starters', fillClassName: 'bg-(--showdown-red)' },
    { key: 'relievers_percentage', label: 'Relievers', fillClassName: 'bg-(--showdown-gray)' },
];

/** Lightweight labelled group — used instead of FormSection so the algorithm settings keep
 * as much of the narrow build panel as possible. */
function SettingsGroup({ title, children, defaultOpen = true }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    return (
        <section className="flex flex-col gap-2.5 shrink-0 border-t border-(--divider) pt-4">
            <div className="flex items-center justify-between gap-2">
                <span className="text-[14px] font-black text-(--text-primary)">{title}</span>
                <button
                    type="button"
                    onClick={() => setIsOpen(o => !o)}
                    aria-expanded={isOpen}
                    aria-label={`${isOpen ? 'Collapse' : 'Expand'} ${title}`}
                    className="p-1 rounded-md text-(--text-tertiary) opacity-60 hover:opacity-100 hover:bg-(--background-secondary) transition cursor-pointer"
                >
                    <FaChevronDown className={`text-[10px] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                </button>
            </div>
            {isOpen && children}
        </section>
    );
}

function defaultAlgorithmConfig(defaultShowdownSet?: string | null): AlgorithmConfig {
    return {
        set_size: 100,
        years: String(new Date().getFullYear()),
        showdown_sets: defaultShowdownSet ? [defaultShowdownSet] : [],
        min_games_hitters: 60,
        min_ip_starters: 75,
        min_ip_relievers: 30,
        player_type_distribution: { ...DEFAULT_PLAYER_TYPE_DISTRIBUTION },
        include_all_stars: true,
        include_award_winners: true,
        all_stars_only: false,
        ideal_low_point_percentage: null,
    };
}

// =============================================================================
// MARK: - BLUEPRINTS
// =============================================================================

/** Fields a blueprint locks to its own preset value — greyed out in the form for as long as
 * that blueprint stays active (any manual edit elsewhere clears the active blueprint). */
type LockableField = 'player_type_distribution';

type AlgorithmBlueprint = {
    id: string;
    name: string;
    description: string;
    icon: React.ReactNode;
    /** Returns the full config to apply, given the current form state (so `years` and any
     * manually-entered set size/thresholds aren't clobbered where a blueprint doesn't care). */
    apply: (current: AlgorithmConfig) => AlgorithmConfig;
    /** Fields that don't make sense to hand-tune under this blueprint. */
    lockedFields?: LockableField[];
};

const BLUEPRINTS: AlgorithmBlueprint[] = [
    {
        id: 'full-season',
        name: 'Full Season',
        description: 'Balanced pool across all teams and player types.',
        icon: <FaCalendarDays />,
        apply: current => ({
            ...current,
            set_size: 100,
            min_games_hitters: 60,
            min_ip_starters: 75,
            min_ip_relievers: 30,
            player_type_distribution: { ...DEFAULT_PLAYER_TYPE_DISTRIBUTION },
            include_all_stars: true,
            include_award_winners: true,
            all_stars_only: false,
            ideal_low_point_percentage: null,
        }),
    },
    {
        id: 'all-stars',
        name: 'All Stars',
        description: 'Only players who earned an All-Star selection that year — team/type balance is fixed by the blueprint.',
        icon: <FaStar />,
        apply: current => ({
            ...current,
            set_size: 60,
            min_games_hitters: 20,
            min_ip_starters: 30,
            min_ip_relievers: 15,
            player_type_distribution: { ...DEFAULT_PLAYER_TYPE_DISTRIBUTION },
            include_all_stars: true,
            include_award_winners: true,
            all_stars_only: true,
            ideal_low_point_percentage: null,
        }),
        lockedFields: ['player_type_distribution'],
    },
];

/** Mirrors `parseNumberingSettings` in EditionBuilder.tsx — reads the last-used algorithm config
 * back out of the edition's free-form `attributes` blob. */
function parseAlgorithmSettings(attributes: Record<string, unknown>, defaultShowdownSet?: string | null): AlgorithmConfig {
    const defaults = defaultAlgorithmConfig(defaultShowdownSet);
    const raw = attributes.algorithm as Partial<AlgorithmConfig> | undefined;
    if (!raw || typeof raw !== 'object') return defaults;
    return {
        ...defaults,
        ...raw,
        player_type_distribution: {
            ...defaults.player_type_distribution!,
            ...(raw.player_type_distribution || {}),
        },
    };
}

export function AlgorithmBuilder({ releaseId, edition, token, defaultShowdownSet, onPreviewResult }: AlgorithmBuilderProps) {
    const [config, setConfig] = useState<AlgorithmConfig>(() => parseAlgorithmSettings(edition.attributes, defaultShowdownSet));
    const [activeBlueprintId, setActiveBlueprintId] = useState<string | null>(null);
    const [status, setStatus] = useState<'idle' | 'running' | 'error'>('idle');
    const [error, setError] = useState<string | null>(null);
    const { isAdmin } = useAuth();
    // Admin-only, per-run option - deliberately kept out of `config` so it isn't persisted to the edition
    const [rerunCards, setRerunCards] = useState(false);

    const activeBlueprint = BLUEPRINTS.find(b => b.id === activeBlueprintId) ?? null;
    const isFieldLocked = (field: LockableField) => !!activeBlueprint?.lockedFields?.includes(field);

    const distribution = config.player_type_distribution ?? DEFAULT_PLAYER_TYPE_DISTRIBUTION;
    const distributionTotal = distribution.hitters_percentage + distribution.starters_percentage + distribution.relievers_percentage;
    const distributionTotalPercent = Math.round(distributionTotal * 100);
    const isDistributionValid = distributionTotalPercent === 100;

    const canRun = !!token
        && config.set_size > 0
        && config.years.trim() !== ''
        && config.showdown_sets.length > 0
        && isDistributionValid
        && status !== 'running';

    /** Any manual field edit invalidates whichever blueprint was active, since the config no
     * longer matches what that blueprint would produce. */
    function updateConfig(updater: (prev: AlgorithmConfig) => AlgorithmConfig) {
        setActiveBlueprintId(null);
        setConfig(updater);
    }

    function updateDistribution(patch: Partial<AlgorithmPlayerTypeDistribution>) {
        if (isFieldLocked('player_type_distribution')) return;
        updateConfig(prev => ({ ...prev, player_type_distribution: { ...distribution, ...patch } }));
    }

    function applyBlueprint(blueprint: AlgorithmBlueprint) {
        setConfig(prev => blueprint.apply(prev));
        setActiveBlueprintId(blueprint.id);
    }

    async function handleRun() {
        if (!token || !canRun) return;
        setStatus('running');
        setError(null);
        try {
            const result = await previewAlgorithm(releaseId, edition.id, config, token, { rerun_cards: isAdmin && rerunCards });
            onPreviewResult(result);
            setStatus('idle');
            updateEdition(releaseId, edition.id, { attributes: { ...edition.attributes, algorithm: config } }, token).catch(() => {});
        } catch (err: any) {
            setStatus('error');
            setError(err.message ?? 'Failed to run algorithm.');
        }
    }

    const distributionLocked = isFieldLocked('player_type_distribution');

    return (
        <div className="flex-1 min-h-0 overflow-y-auto p-3 flex flex-col gap-5">
            <div className="flex flex-col gap-1.5 shrink-0">
                <div className="flex items-end justify-between gap-2">
                    <FormDropdown
                        label="Blueprint"
                        className="min-w-48"
                        options={BLUEPRINTS.map(blueprint => ({ value: blueprint.id, label: blueprint.name, icon: blueprint.icon }))}
                        selectedOption={activeBlueprintId ?? ''}
                        onChange={value => {
                            const blueprint = BLUEPRINTS.find(b => b.id === value);
                            if (blueprint) applyBlueprint(blueprint);
                        }}
                        placeholder="Select a blueprint..."
                    />

                    <button
                        type="button"
                        onClick={handleRun}
                        disabled={!canRun}
                        className="shrink-0 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-bold
                            bg-linear-to-r from-blue-500 to-red-500 text-white disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                        {status === 'running' ? <FaSpinner className="animate-spin" /> : <FaWandMagicSparkles />}
                        {status === 'running' ? 'Running…' : 'Run Algorithm'}
                    </button>
                </div>
                {activeBlueprint && (
                    <p className="text-[11px] text-(--text-tertiary)">{activeBlueprint.description}</p>
                )}
            </div>

            <SettingsGroup title="Basic Settings">
                <div className="grid grid-cols-2 gap-2">
                    <FormInput
                        label="Set Size"
                        type="number"
                        value={config.set_size}
                        onChange={value => updateConfig(prev => ({ ...prev, set_size: parseInt(value || '0', 10) || 0 }))}
                    />

                    <FormInput
                        label="Years"
                        type="text"
                        value={config.years}
                        placeholder='"2023" or "2000-2004" or "2006+2014"'
                        onChange={value => updateConfig(prev => ({ ...prev, years: value ?? '' }))}
                    />

                    <MultiSelect
                        label="Showdown Sets"
                        className="col-span-full"
                        options={showdownSets}
                        selections={config.showdown_sets}
                        onChange={values => updateConfig(prev => ({ ...prev, showdown_sets: values }))}
                        placeholder="Select set(s)..."
                    />
                </div>
            </SettingsGroup>

            <SettingsGroup title="Player Type Distribution">
                <div className="flex flex-col gap-1.5">
                    {DISTRIBUTION_ROWS.map(row => (
                        <PercentageSlider
                            key={row.key}
                            label={row.label}
                            fillClassName={row.fillClassName}
                            value={Math.round(distribution[row.key] * 100)}
                            disabled={distributionLocked}
                            onChange={percent => updateDistribution({ [row.key]: percent / 100 })}
                        />
                    ))}
                </div>
                {distributionLocked ? (
                    <p className="text-[11px] text-(--text-tertiary)">
                        Fixed by the {activeBlueprint?.name} blueprint. Edit another field to unlock.
                    </p>
                ) : !isDistributionValid && (
                    <div className="text-[11px] text-red-400 px-2 py-1.5 rounded-md border border-red-400/30 bg-red-400/5 flex items-center gap-1.5">
                        <FaTriangleExclamation className="shrink-0" />
                        Percentages add up to {distributionTotalPercent}% — they must total 100%.
                    </div>
                )}
            </SettingsGroup>

            <SettingsGroup title="Advanced Thresholds" defaultOpen={false}>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    <FormInput
                        label="Min Games (Hitters)"
                        type="number"
                        value={config.min_games_hitters ?? 60}
                        onChange={value => updateConfig(prev => ({ ...prev, min_games_hitters: parseInt(value || '0', 10) || 0 }))}
                    />
                    <FormInput
                        label="Min IP (Starters)"
                        type="number"
                        value={config.min_ip_starters ?? 75}
                        onChange={value => updateConfig(prev => ({ ...prev, min_ip_starters: parseInt(value || '0', 10) || 0 }))}
                    />
                    <FormInput
                        label="Min IP (Relievers)"
                        type="number"
                        value={config.min_ip_relievers ?? 30}
                        onChange={value => updateConfig(prev => ({ ...prev, min_ip_relievers: parseInt(value || '0', 10) || 0 }))}
                    />
                    <FormEnabler
                        label="Ideal Low-Point %"
                        isEnabled={config.ideal_low_point_percentage != null}
                        onChange={() => updateConfig(prev => ({
                            ...prev,
                            ideal_low_point_percentage: prev.ideal_low_point_percentage != null ? null : 0.2,
                        }))}
                    />
                    {config.ideal_low_point_percentage != null && (
                        <FormInput
                            label="Low-Point % Value"
                            type="number"
                            step="0.01"
                            value={config.ideal_low_point_percentage}
                            onChange={value => updateConfig(prev => ({ ...prev, ideal_low_point_percentage: parseFloat(value || '0') || 0 }))}
                        />
                    )}
                </div>
            </SettingsGroup>

            <div className="flex flex-wrap gap-2 shrink-0">
                <FormEnabler
                    label="Include All-Stars"
                    isEnabled={config.include_all_stars ?? true}
                    onChange={() => updateConfig(prev => ({ ...prev, include_all_stars: !(prev.include_all_stars ?? true) }))}
                />
                <FormEnabler
                    label="Include Award Winners"
                    isEnabled={config.include_award_winners ?? true}
                    onChange={() => updateConfig(prev => ({ ...prev, include_award_winners: !(prev.include_award_winners ?? true) }))}
                />
                <FormEnabler
                    label="All-Stars Only"
                    isEnabled={config.all_stars_only ?? false}
                    onChange={() => updateConfig(prev => ({ ...prev, all_stars_only: !(prev.all_stars_only ?? false) }))}
                />
            </div>

            {isAdmin && (
                <SettingsGroup title="Admin" defaultOpen={false}>
                    <FormEnabler
                        label="Re-run Cards"
                        isEnabled={rerunCards}
                        onChange={() => setRerunCards(prev => !prev)}
                    />
                    <p className="text-[11px] text-(--text-tertiary)">
                        Rebuilds each selected card with the current card algorithm instead of using the archived version. Slower for large sets.
                    </p>
                </SettingsGroup>
            )}

            {error && (
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5 flex items-center gap-2 shrink-0">
                    <FaTriangleExclamation className="shrink-0" /> {error}
                </div>
            )}

        </div>
    );
}
