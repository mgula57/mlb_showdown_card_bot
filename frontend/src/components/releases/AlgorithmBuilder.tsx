import { useEffect, useMemo, useRef, useState } from 'react';
import { FaWandMagicSparkles, FaSpinner, FaTriangleExclamation, FaStar, FaLayerGroup, FaFloppyDisk, FaCheck, FaSliders, FaRotateLeft, FaCodeBranch, FaXmark } from 'react-icons/fa6';
import type { ReleaseEdition, AlgorithmConfig, AlgorithmPlayerTypeDistribution, AlgorithmPreviewResult, AlgorithmSelectionWeights, AlgorithmTeamMinimums, AlgorithmTeamWeighting, WotcSetProfile } from '../../api/releases';
import { fetchAllStarCount, fetchWotcSetProfiles, previewAlgorithm, updateEdition } from '../../api/releases';
import FormInput from '../customs/FormInput';
import FormEnabler from '../customs/FormEnabler';
import FormDropdown from '../customs/FormDropdown';
import PercentageSlider from '../shared/PercentageSlider';
import { InlineError } from '../shared/InlineError';
import { Heading } from '../shared/Heading';
import { choiceClass } from '../shared/choiceStyles';
import { useAuth } from '../auth/AuthContext';
import { useBeforeUnloadWarning } from '../../hooks/useBeforeUnloadWarning';
import { useStableCallback } from '../../hooks/useStableCallback';
import { isSingleYear, parseYearsValue, validateYears } from './years';
import PointBucketsEditor from './PointBucketsEditor';
import { validatePointBuckets } from './pointBuckets';
import { SettingsGroup, SettingsLabel } from './SettingsGroup';
import type { AlgorithmRules, EditionScope } from './editionScope';
import { omitScope } from './editionScope';
import PositionTargetsTable from './PositionTargetsTable';
import { distributionFromPositionTargets } from './positionTargets';
import type { ManualPick, ManualPicks } from './manualPicks';
import { manualPickLabel, withoutManualPick } from './manualPicks';
import {
    DEFAULT_PLAYER_TYPE_DISTRIBUTION, DEFAULT_SELECTION_WEIGHTS, DEFAULT_TEAM_MINIMUMS, DEFAULT_LEGEND_MIN_CAREER_WAR, SELECTION_DEFAULTS,
    CUSTOM_TEMPLATE_ID, ALL_STARS_TEMPLATE_ID, EXPANSION_TEMPLATE_ID, parseAlgorithmSettings, estimateAlgorithmSeconds,
} from './algorithmSettings';

type AlgorithmBuilderProps = {
    releaseId: string;
    edition: ReleaseEdition;
    token?: string;
    defaultShowdownSet?: string | null;
    /** Owned by EditionBuilder and edited in the Scope panel: the Algorithm runs against it live. Templates that preset scope fields write through `onScopeChange`. */
    scope: EditionScope;
    onScopeChange: (patch: Partial<EditionScope>) => void;
    /** Owned by EditionBuilder: removing a card from the pool excludes the player, adding one manually includes them. */
    manualPicks: ManualPicks;
    onManualPicksChange: (picks: ManualPicks) => void;
    onPreviewResult: (result: AlgorithmPreviewResult) => void;
    /** Fires when a run starts and finishes, so the pool can show loading skeletons. */
    onRunningChange?: (running: boolean, estimatedSeconds?: number) => void;
    onEditionUpdated: (edition: ReleaseEdition) => void;
};

const WEIGHT_ROWS: { key: keyof AlgorithmSelectionWeights; label: string; info: string; requiresPositionTargets?: boolean }[] = [
    { key: 'quality', label: 'Quality', info: "The season's WAR, plus the Award Boost when it's on." },
    { key: 'volume', label: 'Volume', info: 'Playing time: plate appearances for hitters, innings pitched for pitchers.' },
    { key: 'team_balance', label: 'Teams', info: "Keeps each team near its share of the set (see Cards per Team)." },
    { key: 'points_fit', label: 'PTS Fit', info: "Steers each position toward its target average points.", requiresPositionTargets: true },
    { key: 'career', label: 'Career', info: "Career WAR through the set's last year, to favor established veterans." },
];

const TEAM_MINIMUM_FIELDS: { key: keyof AlgorithmTeamMinimums; label: string }[] = [
    { key: 'hitters', label: 'Hitters' },
    { key: 'starters', label: 'Starters' },
    { key: 'relievers', label: 'Relievers' },
];

const TEAM_WEIGHTING_OPTIONS: { value: AlgorithmTeamWeighting; label: string }[] = [
    { value: 'EVEN', label: 'Even' },
    { value: 'STRENGTH', label: 'By Team Strength' },
];

const DISTRIBUTION_ROWS: { key: keyof AlgorithmPlayerTypeDistribution; label: string; fillClassName: string }[] = [
    { key: 'hitters_percentage', label: 'Hitters', fillClassName: 'bg-(--showdown-blue-fill)' },
    { key: 'starters_percentage', label: 'Starters', fillClassName: 'bg-(--showdown-red-fill)' },
    { key: 'relievers_percentage', label: 'Relievers', fillClassName: 'bg-(--showdown-gray)' },
];

/** Number of WOTC base sets (2000-2005) — sizes the template chip skeletons while profiles load. */
const WOTC_BASE_SET_COUNT = 6;

const percentLabel =(fraction: number) => Math.round(fraction * 100);

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

// =============================================================================
// MARK: - TEMPLATES
// =============================================================================

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
    description: 'An All-Star Game set: every All-Star from the chosen season, numbered AL then NL. Set size matches the number of All-Stars; team/type balance is fixed by the template.',
    icon: <FaStar />,
    preset: {
        ...SELECTION_DEFAULTS,
        // Placeholder until the All-Star count for the chosen years loads
        set_size: 60,
        min_pa_hitters: 75,
        min_ip_starters: 30,
        min_ip_relievers: 15,
        all_stars_only: true,
    },
    lockedFields: ['player_type_distribution'],
};

/** A follow-up to a base edition, like WOTC's Trading Deadline and Pennant Run: mostly players new to the
 * release, plus players traded since their card in another edition. Lower minimums let rookies and call-ups in. */
const EXPANSION_TEMPLATE: AlgorithmTemplate = {
    id: EXPANSION_TEMPLATE_ID,
    name: 'Expansion',
    description: "A Trading Deadline or Pennant Run style follow-up to another edition: new players plus anyone on a new team since their card there. Lower minimums let in rookies and call-ups. Set Years to the newer season.",
    icon: <FaCodeBranch />,
    preset: {
        ...SELECTION_DEFAULTS,
        set_size: 150,
        min_pa_hitters: 100,
        min_ip_starters: 25,
        min_ip_relievers: 15,
        other_editions_rule: 'NEW_TEAM_ONLY',
        selection_weights: { ...DEFAULT_SELECTION_WEIGHTS, volume: 0.25 },
    },
};

/** Mirrors an original WOTC base set: card count, cards per position, average points per position and low point buckets. */
function wotcBaseSetTemplate(profile: WotcSetProfile): AlgorithmTemplate {
    return {
        id: `wotc-${profile.showdown_set}`,
        name: `${profile.showdown_set} Base`,
        description: `Matches WOTC's ${profile.showdown_set} Base Set: ${profile.set_size} cards with the same mix of positions, average points at each position, share of low point cards and ${profile.team_weighting === 'EVEN' ? 'an even count per team' : 'more cards for stronger teams'}. Change the set size to scale it.`,
        icon: <FaLayerGroup />,
        preset: {
            ...SELECTION_DEFAULTS,
            set_size: profile.set_size,
            showdown_sets: [profile.showdown_set],
            pitcher_showdown_sets: null,
            player_type_distribution: distributionFromPositionTargets(profile.position_targets),
            point_buckets: profile.point_buckets ?? [],
            position_targets: profile.position_targets,
            team_weighting: profile.team_weighting ?? 'EVEN',
        },
    };
}

/** Preset fields the config no longer matches. Set size doesn't count — scaling a template is expected. */
function templateChanges(template: AlgorithmTemplate, config: AlgorithmConfig): (keyof AlgorithmConfig)[] {
    return (Object.keys(template.preset) as (keyof AlgorithmConfig)[])
        .filter(key => key !== 'set_size' && !isDeepEqual(template.preset[key], config[key]));
}

/** Names of manually included or excluded players, each removable. */
function ManualPickList({ label, picks, emptyText, onRemove }: { label: string; picks: ManualPick[]; emptyText: string; onRemove: (id: string) => void }) {
    return (
        <div className="flex flex-col gap-1.5">
            <SettingsLabel>{label} <span className="tabular-nums">{picks.length}</span></SettingsLabel>
            {picks.length === 0 ? (
                <p className="text-[11px] text-(--text-tertiary)">{emptyText}</p>
            ) : (
                <div className="flex flex-wrap gap-1.5">
                    {picks.map(pick => (
                        <span key={pick.id} className="inline-flex items-center gap-1 rounded-control border border-(--divider) py-0.5 pl-2 pr-0.5 text-[12px] font-semibold text-(--text-secondary)">
                            {manualPickLabel(pick)}
                            <button
                                type="button"
                                onClick={() => onRemove(pick.id)}
                                aria-label={`Remove ${manualPickLabel(pick)}`}
                                className="flex items-center justify-center w-4 h-4 rounded-full text-(--text-tertiary) hover:bg-(--red)/90 hover:text-white transition-colors cursor-pointer"
                            >
                                <FaXmark className="text-[10px]" />
                            </button>
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}

function TemplateChip({ template, isActive, onSelect }: { template: AlgorithmTemplate; isActive: boolean; onSelect: () => void }) {
    return (
        <button
            type="button"
            onClick={onSelect}
            aria-pressed={isActive}
            className={choiceClass(isActive, 'sm')}
        >
            <span className="text-[10px]">{template.icon}</span>
            {template.name}
        </button>
    );
}

export function AlgorithmBuilder({ releaseId, edition, token, defaultShowdownSet, scope, onScopeChange, manualPicks, onManualPicksChange, onPreviewResult, onRunningChange, onEditionUpdated }: AlgorithmBuilderProps) {
    // The Algorithm's own rules. Scope (size, years, sets...) lives in the Scope panel and is merged in below.
    const [rules, setRules] = useState<AlgorithmRules>(() => omitScope(parseAlgorithmSettings(edition.attributes, defaultShowdownSet)));
    const config = useMemo<AlgorithmConfig>(() => ({ ...rules, ...scope }), [rules, scope]);
    // Last rules persisted to the edition — the Save button is enabled only while `rules` differ from it
    const [savedConfig, setSavedConfig] = useState<AlgorithmRules>(rules);
    const [saving, setSaving] = useState(false);
    const isDirty = useMemo(() => !isDeepEqual(rules, savedConfig), [rules, savedConfig]);
    useBeforeUnloadWarning(isDirty);
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
    const templates = useMemo(() => [CUSTOM_TEMPLATE, ...wotcTemplates, EXPANSION_TEMPLATE, ALL_STARS_TEMPLATE], [wotcTemplates]);

    // Null while a saved WOTC template's profile is still loading
    const activeTemplate = templates.find(t => t.id === config.template_id) ?? null;
    const changes = activeTemplate && activeTemplate.id !== CUSTOM_TEMPLATE_ID ? templateChanges(activeTemplate, config) : [];
    const isFieldLocked = (field: LockableField) => !!activeTemplate?.lockedFields?.includes(field);

    const isAllStarSet = config.all_stars_only ?? false;
    // An All-Star set is one season's All-Star Game, so the template is offered only for a single year
    // (kept while active, so an older multi-year All-Star edition still shows what it is)
    const showAllStarsTemplate = isSingleYear(config.years) || config.template_id === ALL_STARS_TEMPLATE_ID;

    // All-Star sets hold every All-Star from the chosen years, so the set size follows that count: when the
    // template is picked and when the years or teams change under it. Only the latest request applies.
    const allStarCountRequest = useRef(0);
    const sizeToAllStars = useStableCallback(async (years: string, teams: string[]) => {
        const validation = validateYears(parseYearsValue(years));
        if (validation.error || validation.isBlank) return;
        const requestId = ++allStarCountRequest.current;
        try {
            const count = await fetchAllStarCount(years, teams);
            if (requestId === allStarCountRequest.current && count > 0) onScopeChange({ set_size: count });
        } catch {
            // Keep the current size; the user can still set it by hand
        }
    });
    const allStarScopeKey = isAllStarSet ? JSON.stringify([config.years.trim(), config.teams ?? []]) : null;
    // Starts at the loaded scope, so opening a saved All-Star edition keeps its size
    const sizedAllStarScopeKey = useRef(allStarScopeKey);
    useEffect(() => {
        if (allStarScopeKey === sizedAllStarScopeKey.current) return;
        sizedAllStarScopeKey.current = allStarScopeKey;
        if (allStarScopeKey === null) return;
        const [years, teams] = JSON.parse(allStarScopeKey) as [string, string[]];
        // Waits out typing in the years field
        const timer = window.setTimeout(() => { void sizeToAllStars(years, teams); }, 400);
        return () => window.clearTimeout(timer);
    }, [allStarScopeKey, sizeToAllStars]);

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

    const teamMinimums = config.team_minimums ?? DEFAULT_TEAM_MINIMUMS;
    const teamMinimumsTotal = teamMinimums.hitters + teamMinimums.starters + teamMinimums.relievers;
    const teamWeighting = config.team_weighting ?? 'EVEN';
    const otherEditionsRule = config.other_editions_rule;
    const uniquePlayers = config.unique_players ?? true;
    const legendMinCareerWar = config.legend_min_career_war ?? null;
    const hasLegends = legendMinCareerWar !== null;

    const pointBuckets = config.point_buckets ?? [];
    const arePointBucketsValid = validatePointBuckets(pointBuckets) === null;

    const pitcherShowdownSets = config.pitcher_showdown_sets ?? null;
    const hasPitcherSets = pitcherShowdownSets !== null;

    const canRun = !!token
        && config.set_size > 0
        && config.years.trim() !== ''
        && config.showdown_sets.length > 0
        && (!hasPitcherSets || pitcherShowdownSets.length > 0)
        && (isDistributionValid || hasPositionTargets)
        && arePointBucketsValid
        && status !== 'running';

    // Shown in each section's header while it's collapsed
    const summaries = {
        eligibility: [
            isAllStarSet
                ? 'All-Stars only'
                : `${config.min_pa_hitters ?? 200} PA · ${config.min_ip_starters ?? 75} IP SP · ${config.min_ip_relievers ?? 30} IP RP`,
            ...(hasLegends && !isAllStarSet ? [`Legends ${legendMinCareerWar}+ WAR`] : []),
            ...(uniquePlayers ? [] : ['Repeats allowed']),
            ...(otherEditionsRule === 'ALLOW' ? [] : [otherEditionsRule === 'EXCLUDE' ? 'New players only' : 'New or traded players']),
        ].join(' · '),
        manualPicks: manualPicks.included.length + manualPicks.excluded.length > 0
            ? `${manualPicks.included.length} included · ${manualPicks.excluded.length} excluded`
            : 'None',
        teams: [
            TEAM_WEIGHTING_OPTIONS.find(o => o.value === teamWeighting)?.label,
            teamMinimumsTotal > 0 ? `Min ${teamMinimums.hitters}/${teamMinimums.starters}/${teamMinimums.relievers} per team` : 'No minimums',
        ].join(' · '),
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
        cardOptions: isAdmin && rerunCards ? 'Re-run cards' : '',
    };

    function updateDistribution(patch: Partial<AlgorithmPlayerTypeDistribution>) {
        if (distributionLocked) return;
        setRules(prev => ({ ...prev, player_type_distribution: { ...distribution, ...patch } }));
    }

    function updateTeamMinimums(patch: Partial<AlgorithmTeamMinimums>) {
        setRules(prev => ({ ...prev, team_minimums: { ...teamMinimums, ...patch } }));
    }

    function updateWeights(patch: Partial<AlgorithmSelectionWeights>) {
        setRules(prev => ({ ...prev, selection_weights: { ...selectionWeights, ...patch } }));
    }

    function applyTemplate(template: AlgorithmTemplate) {
        const { set_size, years, showdown_sets, pitcher_showdown_sets, variable_speed, other_editions_rule, ...rulePreset } = template.preset;
        const scopePatch: Partial<EditionScope> = { set_size, years, showdown_sets, pitcher_showdown_sets, variable_speed, other_editions_rule };
        const definedScopePatch = Object.fromEntries(Object.entries(scopePatch).filter(([, value]) => value !== undefined));
        if (Object.keys(definedScopePatch).length > 0) onScopeChange(definedScopePatch);
        setRules(prev => ({ ...prev, ...rulePreset, template_id: template.id }));
        // Re-applying (Reset) doesn't change the years, so it won't trigger the effect above
        if (template.preset.all_stars_only && isAllStarSet) void sizeToAllStars(config.years.trim(), config.teams ?? []);
    }

    async function handleSave() {
        if (!token || saving) return;
        const toSave = rules;
        setSaving(true);
        setError(null);
        try {
            // Scope rides along so an edition saved before scope existed moves its years, sets and size out of the old algorithm blob
            const updated = await updateEdition(releaseId, edition.id, { attributes: { algorithm: toSave, scope } }, token);
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
        onRunningChange?.(true, estimateAlgorithmSeconds(config));
        setError(null);
        try {
            const result = await previewAlgorithm(releaseId, edition.id, config, token, {
                rerun_cards: isAdmin && rerunCards,
                manually_included_ids: manualPicks.included.map(p => p.id),
                manually_excluded_ids: manualPicks.excluded.map(p => p.id),
            });
            onPreviewResult(result);
            setStatus('idle');
        } catch (err: any) {
            setStatus('error');
            setError(err.message ?? 'Failed to run algorithm.');
        } finally {
            onRunningChange?.(false);
        }
    }

    return (
        <div className="relative flex-1 min-h-0 flex flex-col">
        <div className="flex-1 min-h-0 overflow-y-auto p-3 pb-24 flex flex-col gap-5">

            <section className="flex flex-col gap-2 shrink-0">
                <Heading level="panel" as="span">Start From</Heading>
                <div className="flex flex-wrap gap-1.5">
                    <TemplateChip template={CUSTOM_TEMPLATE} isActive={config.template_id === CUSTOM_TEMPLATE_ID} onSelect={() => config.template_id !== CUSTOM_TEMPLATE_ID && applyTemplate(CUSTOM_TEMPLATE)} />
                    {wotcProfiles === null
                        ? Array.from({ length: WOTC_BASE_SET_COUNT }, (_, i) => (
                            <div key={i} aria-hidden className="h-6.5 w-20 rounded-control bg-(--background-tertiary) animate-pulse" />
                        ))
                        : wotcTemplates.map(template => (
                            <TemplateChip key={template.id} template={template} isActive={config.template_id === template.id} onSelect={() => config.template_id !== template.id && applyTemplate(template)} />
                        ))}
                    <TemplateChip template={EXPANSION_TEMPLATE} isActive={config.template_id === EXPANSION_TEMPLATE_ID} onSelect={() => config.template_id !== EXPANSION_TEMPLATE_ID && applyTemplate(EXPANSION_TEMPLATE)} />
                    {showAllStarsTemplate && (
                        <TemplateChip template={ALL_STARS_TEMPLATE} isActive={config.template_id === ALL_STARS_TEMPLATE_ID} onSelect={() => config.template_id !== ALL_STARS_TEMPLATE_ID && applyTemplate(ALL_STARS_TEMPLATE)} />
                    )}
                </div>
                {activeTemplate && (
                    <p className="text-[11px] text-(--text-tertiary)">{activeTemplate.description}</p>
                )}
                {activeTemplate && changes.length > 0 && (
                    <div className="flex items-center justify-between gap-2 rounded-card border border-(--divider) px-2.5 py-1.5">
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

            <SettingsGroup id="eligibility" title="Who's Eligible?" summary={summaries.eligibility} defaultOpen={false}>
                {isAllStarSet ? (
                    <p className="text-[11px] text-(--text-tertiary)">
                        Every All-Star selection from {config.years.trim() || 'the chosen years'} is eligible. Plate appearance and innings minimums don't apply — pick another template to change this.
                    </p>
                ) : (
                    <>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <FormInput
                                label="Min PA (Hitters)"
                                type="number"
                                value={config.min_pa_hitters ?? 200}
                                onChange={value => setRules(prev => ({ ...prev, min_pa_hitters: parseInt(value || '0', 10) || 0 }))}
                            />
                            <FormInput
                                label="Min IP (Starters)"
                                type="number"
                                value={config.min_ip_starters ?? 75}
                                onChange={value => setRules(prev => ({ ...prev, min_ip_starters: parseInt(value || '0', 10) || 0 }))}
                            />
                            <FormInput
                                label="Min IP (Relievers)"
                                type="number"
                                value={config.min_ip_relievers ?? 30}
                                onChange={value => setRules(prev => ({ ...prev, min_ip_relievers: parseInt(value || '0', 10) || 0 }))}
                            />
                        </div>
                        <p className="text-[11px] text-(--text-tertiary)">
                            Players below these minimums are left out of the pool. Catchers only need 80% of the plate appearances minimum.
                        </p>
                        <FormEnabler
                            label="Legends"
                            className="self-start"
                            isEnabled={hasLegends}
                            onChange={() => setRules(prev => ({ ...prev, legend_min_career_war: hasLegends ? null : DEFAULT_LEGEND_MIN_CAREER_WAR }))}
                        />
                        {hasLegends && (
                            <FormInput
                                label="Min Career WAR"
                                type="number"
                                inputMode="decimal"
                                step={5}
                                value={legendMinCareerWar}
                                onChange={value => setRules(prev => ({ ...prev, legend_min_career_war: Math.max(0, parseFloat(value || '0') || 0) }))}
                            />
                        )}
                        <p className="text-[11px] text-(--text-tertiary) -mt-1">
                            Guarantees a card to every player with this much career WAR through {config.years.trim() || 'the chosen years'}, even below the minimums — like a veteran's injury-shortened season. Each legend gets their best card.
                        </p>
                    </>
                )}
                <FormEnabler
                    label="One Card per Player"
                    className="self-start"
                    isEnabled={uniquePlayers}
                    onChange={() => setRules(prev => ({ ...prev, unique_players: !uniquePlayers }))}
                />
                <p className="text-[11px] text-(--text-tertiary) -mt-1">
                    Keeps only a player's best version when the years or sets would give them more than one card.
                </p>
            </SettingsGroup>

            <SettingsGroup id="manual-picks" title="Manual Picks" summary={summaries.manualPicks} defaultOpen={false}>
                <ManualPickList
                    label="Always Include"
                    picks={manualPicks.included}
                    emptyText="Players you add from Manual search show up here."
                    onRemove={id => onManualPicksChange(withoutManualPick(manualPicks, id, 'included'))}
                />
                <ManualPickList
                    label="Always Exclude"
                    picks={manualPicks.excluded}
                    emptyText="Remove a card from the pool (the X beside it) to keep that player's season out of future runs."
                    onRemove={id => onManualPicksChange(withoutManualPick(manualPicks, id, 'excluded'))}
                />
                <p className="text-[11px] text-(--text-tertiary)">
                    Picks are per season, across every showdown set. Included seasons skip the plate appearance and innings minimums, but still need to be in the chosen years.
                </p>
            </SettingsGroup>

            <SettingsGroup id="makeup" title="What's in the Set?" summary={summaries.makeup}>
                <SettingsLabel>{hasPositionTargets ? 'Position Mix' : 'Player Mix'}</SettingsLabel>
                {hasPositionTargets ? (
                    <PositionTargetsTable
                        targets={positionTargets}
                        setSize={config.set_size}
                        onClear={() => setRules(prev => ({ ...prev, position_targets: [] }))}
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
                            <InlineError icon>
                                Percentages add up to {distributionTotalPercent}% — they must total 100%.
                            </InlineError>
                        )}
                    </>
                )}

                <div className="mt-2">
                    <SettingsLabel>Point Buckets</SettingsLabel>
                </div>
                <PointBucketsEditor
                    buckets={pointBuckets}
                    onChange={buckets => setRules(prev => ({ ...prev, point_buckets: buckets }))}
                />
            </SettingsGroup>

            <SettingsGroup id="teams" title="Teams" summary={summaries.teams} defaultOpen={false}>
                <FormDropdown
                    label="Cards per Team"
                    options={TEAM_WEIGHTING_OPTIONS}
                    selectedOption={teamWeighting}
                    onChange={value => setRules(prev => ({ ...prev, team_weighting: (value as AlgorithmTeamWeighting) || 'EVEN' }))}
                />
                <p className="text-[11px] text-(--text-tertiary) -mt-1">
                    Even gives every team about the same count (WOTC 2000-01: 15-17 each). By Team Strength gives stronger teams more cards (WOTC 2002-05: 5-16 each).
                </p>
                <SettingsLabel>Minimum per Team</SettingsLabel>
                <div className="grid grid-cols-3 gap-2">
                    {TEAM_MINIMUM_FIELDS.map(field => (
                        <FormInput
                            key={field.key}
                            label={field.label}
                            type="number"
                            value={teamMinimums[field.key]}
                            onChange={value => updateTeamMinimums({ [field.key]: Math.max(0, parseInt(value || '0', 10) || 0) })}
                        />
                    ))}
                </div>
                <p className="text-[11px] text-(--text-tertiary)">
                    Every team gets at least this many cards of each type, so each one can field a club. Lowered automatically when the set doesn't have room.
                </p>
            </SettingsGroup>

            <SettingsGroup id="priority" title="Who Gets Picked First?" summary={summaries.priority} defaultOpen={false}>
                <div className="flex flex-col gap-1.5">
                    {visibleWeightRows.map(row => (
                        <PercentageSlider
                            key={row.key}
                            label={row.label}
                            info={row.info}
                            fillClassName="bg-(--secondary)"
                            value={percentLabel(selectionWeights[row.key])}
                            onChange={percent => updateWeights({ [row.key]: percent / 100 })}
                        />
                    ))}
                </div>
                <p className="text-[11px] text-(--text-tertiary)">
                    How much each factor counts when picking the next card.
                </p>
                <FormEnabler
                    label="Award Boost"
                    className="self-start"
                    isEnabled={hasAwardBoost}
                    onChange={() => setRules(prev => ({ ...prev, include_all_stars: !hasAwardBoost, include_award_winners: !hasAwardBoost }))}
                />
                <p className="text-[11px] text-(--text-tertiary) -mt-1">
                    Raises Quality for All-Star selections and MVP, Cy Young, Rookie of the Year, Gold Glove and Silver Slugger winners.
                </p>
            </SettingsGroup>

            {isAdmin && (
                <SettingsGroup id="card-options" title="Card Options" summary={summaries.cardOptions} defaultOpen={false}>
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
                </SettingsGroup>
            )}

            {error && (
                <InlineError size="md" className="flex items-center gap-2 shrink-0">
                    <FaTriangleExclamation className="shrink-0" /> {error}
                </InlineError>
            )}

        </div>

        <button
            type="button"
            onClick={handleSave}
            disabled={!token || !isDirty || saving}
            aria-label="Save algorithm settings"
            title={isDirty ? 'Save settings' : 'Settings saved'}
            className="fixed md:absolute bottom-[calc(0.75rem+var(--safe-bottom))] md:bottom-3 right-22 w-16 h-16 rounded-full flex flex-col items-center justify-center gap-1 text-[12px] font-bold shadow-overlay
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
            // A run keeps the button at full strength (just busy) so it doesn't read as unavailable
            className={`fixed md:absolute bottom-[calc(0.75rem+var(--safe-bottom))] md:bottom-3 right-3 w-16 h-16 rounded-full flex flex-col items-center justify-center gap-1 font-display uppercase leading-none text-[15px] shadow-feature-float
                bg-(--showdown-blue-fill) text-white hover:brightness-110 active:translate-y-0.5 active:shadow-overlay disabled:cursor-not-allowed cursor-pointer ${status === 'running' ? 'disabled:cursor-progress' : 'disabled:opacity-50'}`}
        >
            {status === 'running' ? <FaSpinner className="animate-spin text-[18px]" /> : <FaWandMagicSparkles className="text-[18px]" />}
            {status === 'running' ? '…' : 'Run'}
        </button>
        </div>
    );
}
