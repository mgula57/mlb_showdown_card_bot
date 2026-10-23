import { useEffect, useMemo, useState } from 'react';
import { FaWandMagicSparkles, FaSpinner, FaTriangleExclamation, FaStar, FaLayerGroup, FaChevronDown, FaFloppyDisk, FaCheck, FaSliders, FaRotateLeft } from 'react-icons/fa6';
import type { ReleaseEdition, AlgorithmConfig, AlgorithmPlayerTypeDistribution, AlgorithmPreviewResult, AlgorithmSelectionWeights, WotcSetProfile } from '../../api/releases';
import { fetchWotcSetProfiles, previewAlgorithm, updateEdition } from '../../api/releases';
import { showdownSets } from '../shared/SiteSettingsContext';
import FormInput from '../customs/FormInput';
import FormEnabler from '../customs/FormEnabler';
import MultiSelect from '../shared/MultiSelect';
import PercentageSlider from '../shared/PercentageSlider';
import InlineWarning from '../shared/InlineWarning';
import { useAuth } from '../auth/AuthContext';
import PointBucketsEditor from './PointBucketsEditor';
import { validatePointBuckets } from './pointBuckets';
import PositionTargetsTable from './PositionTargetsTable';
import { distributionFromPositionTargets } from './positionTargets';

type AlgorithmBuilderProps = {
    releaseId: string;
    edition: ReleaseEdition;
    token?: string;
    defaultShowdownSet?: string | null;
    onPreviewResult: (result: AlgorithmPreviewResult) => void;
    onEditionUpdated: (edition: ReleaseEdition) => void;
};

const DEFAULT_PLAYER_TYPE_DISTRIBUTION: AlgorithmPlayerTypeDistribution = {
    hitters_percentage: 0.65,
    starters_percentage: 0.20,
    relievers_percentage: 0.15,
};

/** Mirrors `SelectionWeights` defaults on the backend. */
const DEFAULT_SELECTION_WEIGHTS: AlgorithmSelectionWeights = {
    quality: 1,
    volume: 0.5,
    team_balance: 0.75,
    points_fit: 1,
};

const WEIGHT_ROWS: { key: keyof AlgorithmSelectionWeights; label: string; hint: string; requiresPositionTargets?: boolean }[] = [
    { key: 'quality', label: 'Quality', hint: 'WAR (plus award boost)' },
    { key: 'volume', label: 'Volume', hint: 'PA for hitters, IP for pitchers' },
    { key: 'team_balance', label: 'Teams', hint: 'even card count per team' },
    { key: 'points_fit', label: 'PTS Fit', hint: "each position's average points", requiresPositionTargets: true },
];

const DISTRIBUTION_ROWS: { key: keyof AlgorithmPlayerTypeDistribution; label: string; fillClassName: string }[] = [
    { key: 'hitters_percentage', label: 'Hitters', fillClassName: 'bg-(--showdown-blue)' },
    { key: 'starters_percentage', label: 'Starters', fillClassName: 'bg-(--showdown-red)' },
    { key: 'relievers_percentage', label: 'Relievers', fillClassName: 'bg-(--showdown-gray)' },
];

/** Number of WOTC base sets (2000-2005) — sizes the template chip skeletons while profiles load. */
const WOTC_BASE_SET_COUNT = 6;

const percentLabel = (fraction: number) => Math.round(fraction * 100);

/** Structural equality that ignores object key order — edition attributes round-trip through
 * Postgres JSONB, which reorders keys, so `JSON.stringify` comparisons aren't reliable. */
function isDeepEqual(a: unknown, b: unknown): boolean {
    if (a === b) return true;
    if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) return false;
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    const aKeys = Object.keys(a);
    const bKeys = Object.keys(b);
    if (aKeys.length !== bKeys.length) return false;
    return aKeys.every(key => isDeepEqual((a as Record<string, unknown>)[key], (b as Record<string, unknown>)[key]));
}

const sectionOpenStorageKey = (id: string) => `releaseBuilder.algorithmSection.${id}`;

function loadSectionOpen(id: string, defaultOpen: boolean): boolean {
    try {
        const saved = localStorage.getItem(sectionOpenStorageKey(id));
        return saved === null ? defaultOpen : saved === 'open';
    } catch {
        return defaultOpen;
    }
}

/** Lightweight collapsible group — used instead of FormSection so the algorithm settings keep
 * as much of the narrow build panel as possible. Shows `summary` while collapsed so the whole
 * config stays readable at a glance; open/closed is remembered per section. */
function SettingsGroup({ id, title, summary, children, defaultOpen = true }: { id: string; title: string; summary?: string; children: React.ReactNode; defaultOpen?: boolean }) {
    const [isOpen, setIsOpen] = useState(() => loadSectionOpen(id, defaultOpen));

    function toggle() {
        const next = !isOpen;
        setIsOpen(next);
        try { localStorage.setItem(sectionOpenStorageKey(id), next ? 'open' : 'closed'); } catch { /* storage unavailable */ }
    }

    return (
        <section className="flex flex-col gap-2.5 shrink-0 border-t border-(--divider) pt-4">
            <button
                type="button"
                onClick={toggle}
                aria-expanded={isOpen}
                className="group flex items-center justify-between gap-3 text-left cursor-pointer"
            >
                <span className="shrink-0 text-[14px] font-black text-(--text-primary)">{title}</span>
                <span className="flex items-center gap-2 min-w-0">
                    {!isOpen && summary && (
                        <span title={summary} className="text-[11px] font-semibold text-(--text-tertiary) truncate">{summary}</span>
                    )}
                    <FaChevronDown className={`shrink-0 text-[10px] text-(--text-tertiary) opacity-60 group-hover:opacity-100 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                </span>
            </button>
            {isOpen && children}
        </section>
    );
}

/** Small bold label for a sub-part of a SettingsGroup. */
function SettingsLabel({ children }: { children: React.ReactNode }) {
    return <span className="text-[12px] font-bold text-(--text-secondary)">{children}</span>;
}

// =============================================================================
// MARK: - TEMPLATES
// =============================================================================

const CUSTOM_TEMPLATE_ID = 'custom';
const ALL_STARS_TEMPLATE_ID = 'all-stars';

/** Everything a template resets: who's eligible, what the set is made of and how players are
 * picked. Years, sets, size (unless the template sets them) and card options stay the user's own. */
const SELECTION_DEFAULTS = {
    min_games_hitters: 60,
    min_ip_starters: 75,
    min_ip_relievers: 30,
    player_type_distribution: DEFAULT_PLAYER_TYPE_DISTRIBUTION,
    include_all_stars: true,
    include_award_winners: true,
    all_stars_only: false,
    point_buckets: [],
    selection_weights: DEFAULT_SELECTION_WEIGHTS,
    position_targets: [],
} satisfies Partial<AlgorithmConfig>;

function defaultAlgorithmConfig(defaultShowdownSet?: string | null): AlgorithmConfig {
    return {
        set_size: 100,
        years: String(new Date().getFullYear()),
        showdown_sets: defaultShowdownSet ? [defaultShowdownSet] : [],
        ...SELECTION_DEFAULTS,
        variable_speed: false,
        template_id: CUSTOM_TEMPLATE_ID,
    };
}

/** Fields a template locks to its own preset value — greyed out in the form while it's active. */
type LockableField = 'player_type_distribution';

/** A starting point for the form. Picking one applies its `preset`; later edits keep it active
 * and show up as "changes" against it, with a reset back to the preset. */
type AlgorithmTemplate = {
    id: string;
    name: string;
    description: string;
    icon: React.ReactNode;
    preset: Partial<AlgorithmConfig>;
    lockedFields?: LockableField[];
};

const CUSTOM_TEMPLATE: AlgorithmTemplate = {
    id: CUSTOM_TEMPLATE_ID,
    name: 'Custom',
    description: 'Starts from the default settings — tune everything below yourself.',
    icon: <FaSliders />,
    preset: SELECTION_DEFAULTS,
};

/** The only template whose mode (`all_stars_only`) isn't editable in the form — it's a different
 * kind of set (All-Star pool, AL/NL numbering, no games/IP minimums), so it stays on until
 * another template is picked. */
const ALL_STARS_TEMPLATE: AlgorithmTemplate = {
    id: ALL_STARS_TEMPLATE_ID,
    name: 'All-Stars',
    description: 'An All-Star Game set: every All-Star from the chosen years, numbered AL then NL. Team/type balance is fixed by the template.',
    icon: <FaStar />,
    preset: {
        ...SELECTION_DEFAULTS,
        set_size: 60,
        min_games_hitters: 20,
        min_ip_starters: 30,
        min_ip_relievers: 15,
        all_stars_only: true,
    },
    lockedFields: ['player_type_distribution'],
};

/** Mirrors an original WOTC base set: card count, cards per position, average points per position and low point buckets. */
function wotcBaseSetTemplate(profile: WotcSetProfile): AlgorithmTemplate {
    return {
        id: `wotc-${profile.showdown_set}`,
        name: `${profile.showdown_set} Base`,
        description: `Matches WOTC's ${profile.showdown_set} Base Set: ${profile.set_size} cards with the same mix of positions, average points at each position and share of low point cards. Change the set size to scale it.`,
        icon: <FaLayerGroup />,
        preset: {
            ...SELECTION_DEFAULTS,
            set_size: profile.set_size,
            showdown_sets: [profile.showdown_set],
            player_type_distribution: distributionFromPositionTargets(profile.position_targets),
            point_buckets: profile.point_buckets ?? [],
            position_targets: profile.position_targets,
        },
    };
}

/** Preset fields the config no longer matches. Set size doesn't count — scaling a template is expected. */
function templateChanges(template: AlgorithmTemplate, config: AlgorithmConfig): (keyof AlgorithmConfig)[] {
    return (Object.keys(template.preset) as (keyof AlgorithmConfig)[])
        .filter(key => key !== 'set_size' && !isDeepEqual(template.preset[key], config[key]));
}

/** Single low-point bucket fields that older editions saved before `point_buckets` existed. */
type LegacyLowPointSettings = {
    ideal_low_point_percentage?: number | null;
    low_point_max_points?: number;
};

/** Mirrors `parseNumberingSettings` in EditionBuilder.tsx — reads the last-used algorithm config
 * back out of the edition's free-form `attributes` blob. */
function parseAlgorithmSettings(attributes: Record<string, unknown>, defaultShowdownSet?: string | null): AlgorithmConfig {
    const defaults = defaultAlgorithmConfig(defaultShowdownSet);
    const raw = attributes.algorithm as (Partial<AlgorithmConfig> & LegacyLowPointSettings) | undefined;
    if (!raw || typeof raw !== 'object') return defaults;
    const { ideal_low_point_percentage, low_point_max_points, ...rest } = raw;
    return {
        ...defaults,
        ...rest,
        // Editions saved before templates were persisted: all-star mode can only come from the All-Stars template
        template_id: raw.template_id ?? (raw.all_stars_only ? ALL_STARS_TEMPLATE_ID : CUSTOM_TEMPLATE_ID),
        player_type_distribution: {
            ...defaults.player_type_distribution!,
            ...(raw.player_type_distribution || {}),
        },
        selection_weights: {
            ...defaults.selection_weights!,
            ...(raw.selection_weights || {}),
        },
        // Editions saved before multi-bucket support stored a single 10-max bucket
        point_buckets: raw.point_buckets
            ?? (ideal_low_point_percentage != null
                ? [{ min_points: 10, max_points: low_point_max_points ?? 50, percentage: ideal_low_point_percentage }]
                : []),
    };
}

function TemplateChip({ template, isActive, onSelect }: { template: AlgorithmTemplate; isActive: boolean; onSelect: () => void }) {
    return (
        <button
            type="button"
            onClick={onSelect}
            aria-pressed={isActive}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[12px] whitespace-nowrap transition-colors cursor-pointer ${
                isActive
                    ? 'border-(--text-secondary) bg-(--background-quaternary) text-(--text-primary) font-bold'
                    : 'border-(--divider) text-(--text-secondary) font-medium hover:bg-(--background-secondary)'
            }`}
        >
            <span className="text-[10px]">{template.icon}</span>
            {template.name}
        </button>
    );
}

export function AlgorithmBuilder({ releaseId, edition, token, defaultShowdownSet, onPreviewResult, onEditionUpdated }: AlgorithmBuilderProps) {
    const [config, setConfig] = useState<AlgorithmConfig>(() => parseAlgorithmSettings(edition.attributes, defaultShowdownSet));
    // Last config persisted to the edition — the Save button is enabled only while `config` differs from it
    const [savedConfig, setSavedConfig] = useState<AlgorithmConfig>(config);
    const [saving, setSaving] = useState(false);
    const isDirty = useMemo(() => !isDeepEqual(config, savedConfig), [config, savedConfig]);
    const [status, setStatus] = useState<'idle' | 'running' | 'error'>('idle');
    const [error, setError] = useState<string | null>(null);
    const { isAdmin } = useAuth();
    // Admin-only, per-run option - deliberately kept out of `config` so it isn't persisted to the edition
    const [rerunCards, setRerunCards] = useState(false);

    // WOTC templates are derived from the original sets' cards, so they appear once those load (null = loading)
    const [wotcProfiles, setWotcProfiles] = useState<WotcSetProfile[] | null>(null);
    useEffect(() => {
        fetchWotcSetProfiles().then(setWotcProfiles).catch(() => setWotcProfiles([]));
    }, []);
    const wotcTemplates = useMemo(() => (wotcProfiles ?? []).map(wotcBaseSetTemplate), [wotcProfiles]);
    const templates = useMemo(() => [CUSTOM_TEMPLATE, ...wotcTemplates, ALL_STARS_TEMPLATE], [wotcTemplates]);

    // Null while a saved WOTC template's profile is still loading
    const activeTemplate = templates.find(t => t.id === config.template_id) ?? null;
    const changes = activeTemplate && activeTemplate.id !== CUSTOM_TEMPLATE_ID ? templateChanges(activeTemplate, config) : [];
    const isFieldLocked = (field: LockableField) => !!activeTemplate?.lockedFields?.includes(field);

    const isAllStarSet = config.all_stars_only ?? false;

    const positionTargets = config.position_targets ?? [];
    const hasPositionTargets = positionTargets.length > 0;
    const selectionWeights = config.selection_weights ?? DEFAULT_SELECTION_WEIGHTS;
    const visibleWeightRows = WEIGHT_ROWS.filter(row => hasPositionTargets || !row.requiresPositionTargets);
    const hasAwardBoost = (config.include_all_stars ?? true) || (config.include_award_winners ?? true);

    const distribution = config.player_type_distribution ?? DEFAULT_PLAYER_TYPE_DISTRIBUTION;
    const distributionTotal = distribution.hitters_percentage + distribution.starters_percentage + distribution.relievers_percentage;
    const distributionTotalPercent = Math.round(distributionTotal * 100);
    const isDistributionValid = distributionTotalPercent === 100;
    const distributionLocked = isFieldLocked('player_type_distribution');

    const pointBuckets = config.point_buckets ?? [];
    const arePointBucketsValid = validatePointBuckets(pointBuckets) === null;

    const hasSet00_01 = config.showdown_sets.some(set => set === '2000' || set === '2001');

    const canRun = !!token
        && config.set_size > 0
        && config.years.trim() !== ''
        && config.showdown_sets.length > 0
        && (isDistributionValid || hasPositionTargets)
        && arePointBucketsValid
        && status !== 'running';

    // Shown in each section's header while it's collapsed
    const summaries = {
        basics: `${config.set_size} cards · ${config.years.trim() || 'no years'} · ${config.showdown_sets.join(', ') || 'no sets'}`,
        eligibility: isAllStarSet
            ? 'All-Stars only'
            : `${config.min_games_hitters ?? 60} G · ${config.min_ip_starters ?? 75} IP SP · ${config.min_ip_relievers ?? 30} IP RP`,
        makeup: [
            hasPositionTargets
                ? `${positionTargets.length} positions`
                : DISTRIBUTION_ROWS.map(row => percentLabel(distribution[row.key])).join('/'),
            pointBuckets.length > 0 ? `${pointBuckets.length} point bucket${pointBuckets.length === 1 ? '' : 's'}` : 'no point buckets',
        ].join(' · '),
        priority: [
            ...visibleWeightRows.map(row => `${row.label} ${percentLabel(selectionWeights[row.key])}`),
            ...(hasAwardBoost ? ['Award boost'] : []),
        ].join(' · '),
        cardOptions: [
            ...(hasSet00_01 ? [config.variable_speed ? 'Variable speed' : 'Standard speed'] : []),
            ...(isAdmin && rerunCards ? ['Re-run cards'] : []),
        ].join(' · '),
    };

    function updateDistribution(patch: Partial<AlgorithmPlayerTypeDistribution>) {
        if (distributionLocked) return;
        setConfig(prev => ({ ...prev, player_type_distribution: { ...distribution, ...patch } }));
    }

    function updateWeights(patch: Partial<AlgorithmSelectionWeights>) {
        setConfig(prev => ({ ...prev, selection_weights: { ...selectionWeights, ...patch } }));
    }

    function applyTemplate(template: AlgorithmTemplate) {
        setConfig(prev => ({ ...prev, ...template.preset, template_id: template.id }));
    }

    async function handleSave() {
        if (!token || saving) return;
        const toSave = config;
        setSaving(true);
        setError(null);
        try {
            const updated = await updateEdition(releaseId, edition.id, { attributes: { algorithm: toSave } }, token);
            setSavedConfig(toSave);
            onEditionUpdated(updated);
        } catch (err: any) {
            setError(err.message ?? 'Failed to save algorithm settings.');
        } finally {
            setSaving(false);
        }
    }

    async function handleRun() {
        if (!token || !canRun) return;
        if (isDirty) handleSave();
        setStatus('running');
        setError(null);
        try {
            const result = await previewAlgorithm(releaseId, edition.id, config, token, { rerun_cards: isAdmin && rerunCards });
            onPreviewResult(result);
            setStatus('idle');
        } catch (err: any) {
            setStatus('error');
            setError(err.message ?? 'Failed to run algorithm.');
        }
    }

    return (
        <div className="relative flex-1 min-h-0 flex flex-col">
        <div className="flex-1 min-h-0 overflow-y-auto p-3 pb-24 flex flex-col gap-5">

            <section className="flex flex-col gap-2 shrink-0">
                <span className="text-[14px] font-black text-(--text-primary)">Start From</span>
                <div className="flex flex-wrap gap-1.5">
                    <TemplateChip template={CUSTOM_TEMPLATE} isActive={config.template_id === CUSTOM_TEMPLATE_ID} onSelect={() => config.template_id !== CUSTOM_TEMPLATE_ID && applyTemplate(CUSTOM_TEMPLATE)} />
                    {wotcProfiles === null
                        ? Array.from({ length: WOTC_BASE_SET_COUNT }, (_, i) => (
                            <div key={i} aria-hidden className="h-6.5 w-20 rounded-full bg-(--background-quaternary) animate-pulse" />
                        ))
                        : wotcTemplates.map(template => (
                            <TemplateChip key={template.id} template={template} isActive={config.template_id === template.id} onSelect={() => config.template_id !== template.id && applyTemplate(template)} />
                        ))}
                    <TemplateChip template={ALL_STARS_TEMPLATE} isActive={config.template_id === ALL_STARS_TEMPLATE_ID} onSelect={() => config.template_id !== ALL_STARS_TEMPLATE_ID && applyTemplate(ALL_STARS_TEMPLATE)} />
                </div>
                {activeTemplate && (
                    <p className="text-[11px] text-(--text-tertiary)">{activeTemplate.description}</p>
                )}
                {activeTemplate && changes.length > 0 && (
                    <div className="flex items-center justify-between gap-2 rounded-lg border border-(--divider) px-2.5 py-1.5">
                        <span className="text-[11px] font-semibold text-(--text-secondary)">
                            Based on {activeTemplate.name} · {changes.length} change{changes.length === 1 ? '' : 's'}
                        </span>
                        <button
                            type="button"
                            onClick={() => applyTemplate(activeTemplate)}
                            title={`Reset to the ${activeTemplate.name} settings`}
                            className="flex items-center gap-1 text-[11px] font-semibold text-(--text-tertiary) hover:text-(--text-primary) transition-colors cursor-pointer"
                        >
                            <FaRotateLeft className="text-[10px]" /> Reset
                        </button>
                    </div>
                )}
            </section>

            <SettingsGroup id="basics" title="Basics" summary={summaries.basics}>
                <div className="grid grid-cols-2 gap-2">
                    <FormInput
                        label="Set Size"
                        type="number"
                        value={config.set_size}
                        onChange={value => setConfig(prev => ({ ...prev, set_size: parseInt(value || '0', 10) || 0 }))}
                    />

                    <FormInput
                        label="Years"
                        type="text"
                        value={config.years}
                        placeholder='"2023" or "2000-2004" or "2006+2014"'
                        onChange={value => setConfig(prev => ({ ...prev, years: value ?? '' }))}
                    />

                    <MultiSelect
                        label="Showdown Sets"
                        className="col-span-full"
                        options={showdownSets}
                        selections={config.showdown_sets}
                        onChange={values => setConfig(prev => ({ ...prev, showdown_sets: values }))}
                        placeholder="Select set(s)..."
                    />
                </div>
            </SettingsGroup>

            <SettingsGroup id="eligibility" title="Who's Eligible?" summary={summaries.eligibility} defaultOpen={false}>
                {isAllStarSet ? (
                    <p className="text-[11px] text-(--text-tertiary)">
                        Every All-Star selection from {config.years.trim() || 'the chosen years'} is eligible. Games and innings minimums don't apply — pick another template to change this.
                    </p>
                ) : (
                    <>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <FormInput
                                label="Min Games (Hitters)"
                                type="number"
                                value={config.min_games_hitters ?? 60}
                                onChange={value => setConfig(prev => ({ ...prev, min_games_hitters: parseInt(value || '0', 10) || 0 }))}
                            />
                            <FormInput
                                label="Min IP (Starters)"
                                type="number"
                                value={config.min_ip_starters ?? 75}
                                onChange={value => setConfig(prev => ({ ...prev, min_ip_starters: parseInt(value || '0', 10) || 0 }))}
                            />
                            <FormInput
                                label="Min IP (Relievers)"
                                type="number"
                                value={config.min_ip_relievers ?? 30}
                                onChange={value => setConfig(prev => ({ ...prev, min_ip_relievers: parseInt(value || '0', 10) || 0 }))}
                            />
                        </div>
                        <p className="text-[11px] text-(--text-tertiary)">
                            Players below these minimums are left out of the pool. Catchers only need 80% of the games minimum.
                        </p>
                    </>
                )}
            </SettingsGroup>

            <SettingsGroup id="makeup" title="What's in the Set?" summary={summaries.makeup}>
                <SettingsLabel>{hasPositionTargets ? 'Position Mix' : 'Player Mix'}</SettingsLabel>
                {hasPositionTargets ? (
                    <PositionTargetsTable
                        targets={positionTargets}
                        setSize={config.set_size}
                        onClear={() => setConfig(prev => ({ ...prev, position_targets: [] }))}
                    />
                ) : (
                    <>
                        <div className="flex flex-col gap-1.5">
                            {DISTRIBUTION_ROWS.map(row => (
                                <PercentageSlider
                                    key={row.key}
                                    label={row.label}
                                    fillClassName={row.fillClassName}
                                    value={percentLabel(distribution[row.key])}
                                    disabled={distributionLocked}
                                    onChange={percent => updateDistribution({ [row.key]: percent / 100 })}
                                />
                            ))}
                        </div>
                        {distributionLocked ? (
                            <p className="text-[11px] text-(--text-tertiary)">
                                Fixed by the {activeTemplate?.name} template.
                            </p>
                        ) : !isDistributionValid && (
                            <InlineWarning>
                                Percentages add up to {distributionTotalPercent}% — they must total 100%.
                            </InlineWarning>
                        )}
                    </>
                )}

                <div className="mt-2">
                    <SettingsLabel>Point Buckets</SettingsLabel>
                </div>
                <PointBucketsEditor
                    buckets={pointBuckets}
                    onChange={buckets => setConfig(prev => ({ ...prev, point_buckets: buckets }))}
                />
            </SettingsGroup>

            <SettingsGroup id="priority" title="Who Gets Picked First?" summary={summaries.priority} defaultOpen={false}>
                <div className="flex flex-col gap-1.5">
                    {visibleWeightRows.map(row => (
                        <PercentageSlider
                            key={row.key}
                            label={row.label}
                            fillClassName="bg-(--secondary)"
                            value={percentLabel(selectionWeights[row.key])}
                            onChange={percent => updateWeights({ [row.key]: percent / 100 })}
                        />
                    ))}
                </div>
                <p className="text-[11px] text-(--text-tertiary)">
                    How much each factor counts when picking the next card.{' '}
                    {visibleWeightRows.map(row => `${row.label}: ${row.hint}`).join(' · ')}.
                </p>
                <FormEnabler
                    label="Award Boost"
                    className="self-start"
                    isEnabled={hasAwardBoost}
                    onChange={() => setConfig(prev => ({ ...prev, include_all_stars: !hasAwardBoost, include_award_winners: !hasAwardBoost }))}
                />
                <p className="text-[11px] text-(--text-tertiary) -mt-1">
                    Raises Quality for All-Star selections and MVP, Cy Young, Rookie of the Year, Gold Glove and Silver Slugger winners.
                </p>
            </SettingsGroup>

            {(hasSet00_01 || isAdmin) && (
                <SettingsGroup id="card-options" title="Card Options" summary={summaries.cardOptions} defaultOpen={false}>
                    {hasSet00_01 && (
                        <>
                            <FormEnabler
                                label="Variable Speed"
                                className="self-start"
                                isEnabled={config.variable_speed ?? false}
                                onChange={() => setConfig(prev => ({ ...prev, variable_speed: !(prev.variable_speed ?? false) }))}
                            />
                            <p className="text-[11px] text-(--text-tertiary) -mt-1">
                                2000/2001 cards use exact speed instead of 10/15/20, with points recalculated. Players are picked on their standard points, so point totals may shift slightly from your buckets.
                            </p>
                        </>
                    )}
                    {isAdmin && (
                        <>
                            <SettingsLabel>Admin</SettingsLabel>
                            <FormEnabler
                                label="Re-run Cards"
                                className="self-start"
                                isEnabled={rerunCards}
                                onChange={() => setRerunCards(prev => !prev)}
                            />
                            <p className="text-[11px] text-(--text-tertiary) -mt-1">
                                Rebuilds each selected card with the current card algorithm instead of using the archived version. Slower for large sets.
                            </p>
                        </>
                    )}
                </SettingsGroup>
            )}

            {error && (
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5 flex items-center gap-2 shrink-0">
                    <FaTriangleExclamation className="shrink-0" /> {error}
                </div>
            )}

        </div>

        <button
            type="button"
            onClick={handleSave}
            disabled={!token || !isDirty || saving}
            aria-label="Save algorithm settings"
            title={isDirty ? 'Save settings' : 'Settings saved'}
            className="absolute bottom-3 right-22 w-16 h-16 rounded-full flex flex-col items-center justify-center gap-1 text-[12px] font-bold shadow-lg
                border border-(--divider) bg-(--background-secondary) text-(--text-secondary) hover:border-(--text-tertiary) transition-colors disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
        >
            {saving ? <FaSpinner className="animate-spin text-[18px]" /> : (isDirty ? <FaFloppyDisk className="text-[18px]" /> : <FaCheck className="text-[18px]" />)}
            {saving ? '…' : (isDirty ? 'Save' : 'Saved')}
        </button>

        <button
            type="button"
            onClick={handleRun}
            disabled={!canRun}
            aria-label="Run algorithm"
            className="absolute bottom-3 right-3 w-16 h-16 rounded-full flex flex-col items-center justify-center gap-1 text-[12px] font-bold shadow-lg
                bg-linear-to-r from-blue-500 to-red-500 text-white disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
            {status === 'running' ? <FaSpinner className="animate-spin text-[18px]" /> : <FaWandMagicSparkles className="text-[18px]" />}
            {status === 'running' ? '…' : 'Run'}
        </button>
        </div>
    );
}
