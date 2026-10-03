import { useState, useEffect } from 'react';
import type { Team, TeamUpdatePayload } from '../../api/userTeams';
import { MAX_STARTERS } from '../../api/userTeams';
import FormInput from '../customs/FormInput';
import NumberInput from '../customs/NumberInput';
import FormEnabler from '../customs/FormEnabler';
import { imageForSet } from '../shared/SiteSettingsContext';
import FormSection from '../customs/FormSection';
import RangeFilter from '../customs/RangeFilter';
import { TeamHierarchy } from '../cards/TeamHierarchy';
import { fetchTeamHierarchy, type TeamHierarchyRecord } from '../../api/card_db/cardDatabase';
import {
    TEAM_CARD_SOURCES, activeSources, allowedSetsForSource, isSingleSetSource,
    normalizeSetSettings, setOptionsForSource, toggleSetForSource,
} from '../../domain/teamSets';
import { FaUser, FaLayerGroup, FaGears, FaFilter, FaBoxArchive, FaSpinner, FaCheck, FaFloppyDisk, FaTrashCan } from 'react-icons/fa6';
import { CardSource } from '../../types/cardSource';
import ColorPicker from '../shared/ColorPicker';
import { containsProfanity } from '../../domain/profanity';
import { useAuth } from '../auth/AuthContext';
import { DEFAULT_PRIMARY_COLOR, DEFAULT_SECONDARY_COLOR } from '../../api/userSettings';
import { useMediaQuery } from '../../hooks/useMediaQuery';

const TEAM_NAME_MAX_LENGTH = 25;

type PlayerFilters = {
    min_year?: number;
    max_year?: number;
    organization?: string[];
    league?: string[];
    team?: string[];
    hand?: string[];
};

const HAND_OPTIONS: { value: string; label: string }[] = [
    { value: 'L', label: 'Left' },
    { value: 'R', label: 'Right' },
    { value: 'S', label: 'Switch' },
];

type SummaryItem = {
    label?: string;
    value: string;
    image?: string;
};

/** Compact badge row shown under a collapsed FormSection, mirroring CustomCardBuilder's summary style. */
function SectionSummary({ items }: { items: SummaryItem[] }) {
    if (items.length === 0) return null;
    return (
        <div className="text-xs font-bold flex flex-wrap items-center gap-x-1.5 gap-y-1 text-(--tertiary)">
            {items.map((item, i) => (
                <div key={`${item.label ?? ''}-${item.value}-${i}`} className="flex shrink-0 items-center whitespace-nowrap rounded-md px-1.5 border border-(--divider)">
                    {item.image
                        ? <img src={item.image} alt={item.value} className="h-5 w-auto object-contain" />
                        : <span>{item.label ? `${item.label}: ` : ''}{item.value}</span>
                    }
                </div>
            ))}
        </div>
    );
}

type TeamSettingsFormProps = {
    team: Partial<Team>;
    onChange: (updates: TeamUpdatePayload) => void;
    /** When provided, renders the Archive / Unarchive control at the bottom of the form. */
    onArchive?: () => void;
    archiving?: boolean;
};

export function TeamSettingsForm({ team, onChange, onArchive, archiving = false }: TeamSettingsFormProps) {
    const { syncSetting } = useAuth();
    const [hierarchyData, setHierarchyData] = useState<TeamHierarchyRecord[]>([]);
    const [savedColorsAsDefault, setSavedColorsAsDefault] = useState(false);
    // Matches the `xl:grid` breakpoint below. In the two-column grid every section starts open so
    // paired sections in a row don't sit half-collapsed next to each other.
    const isGridLayout = useMediaQuery('(min-width: 1024px)');
    const sectionLayoutKey = isGridLayout ? 'grid' : 'stack';
    useEffect(() => {
        fetchTeamHierarchy().then(setHierarchyData).catch(() => {});
    }, []);

    // Confirmation is transient, and any further color edit makes it stale.
    useEffect(() => {
        if (!savedColorsAsDefault) return;
        const timer = setTimeout(() => setSavedColorsAsDefault(false), 2500);
        return () => clearTimeout(timer);
    }, [savedColorsAsDefault]);
    useEffect(() => {
        setSavedColorsAsDefault(false);
    }, [team.primary_color, team.secondary_color]);

    const isChallengeTeam = team.creation_source === 'challenge';
    const pf = (team.player_filters ?? {}) as PlayerFilters;
    const updatePlayerFilters = (patch: Partial<PlayerFilters>) => {
        const next = { ...pf, ...patch };
        // strip undefined/empty values so the JSONB stays clean
        const cleaned = Object.fromEntries(
            Object.entries(next).filter(([, v]) => v !== undefined && v !== null && !(Array.isArray(v) && v.length === 0))
        );
        onChange({ player_filters: Object.keys(cleaned).length ? cleaned : null });
    };

    const MIN_ROSTER = 15;
    const MAX_ROSTER = 40;

    const getDefaultStartersForRosterSize = (roster: number): number => {
        if (roster >= 35) return 7;
        if (roster >= 29) return 6;
        if (roster >= 24) return 5;
        if (roster >= 18) return 4;
        return 3;
    };

    const LINEUP_SLOTS = 9;
    const rosterSize   = team.roster_size    ?? 25;
    const minBench     = team.min_bench      ?? 4;
    const minBullpen   = team.min_bullpen    ?? 5;
    const numStarters  = team.num_starters   ?? getDefaultStartersForRosterSize(rosterSize);
    const rosterUsed   = LINEUP_SLOTS + minBench + minBullpen + numStarters;
    const rosterError  = rosterUsed > rosterSize
        ? `Minimum roster needs ${rosterUsed} slots (9 lineup + ${numStarters} SP + ${minBullpen} bullpen + ${minBench} bench) but roster size is ${rosterSize}.`
        : null;
    const rosterSizeError = rosterSize < MIN_ROSTER || rosterSize > MAX_ROSTER
        ? `Roster size must be between ${MIN_ROSTER} and ${MAX_ROSTER}.`
        : null;
    const nameError = containsProfanity(team.name) ? 'Team name contains language that is not allowed.' : null;
    const abbreviationError = containsProfanity(team.abbreviation) ? 'Abbreviation contains language that is not allowed.' : null;
    const minPtsLimit  = rosterSize * 10;
    const ptsLimit     = team.pts_limit ?? 5000;
    const ptsError     = ptsLimit < minPtsLimit
        ? `PTS limit (${ptsLimit}) must be at least roster size × 10 (${minPtsLimit}).`
        : null;

    const handleSaveColorsAsDefault = () => {
        syncSetting({
            default_primary_color: team.primary_color ?? DEFAULT_PRIMARY_COLOR,
            default_secondary_color: team.secondary_color ?? DEFAULT_SECONDARY_COLOR,
        });
        setSavedColorsAsDefault(true);
    };

    const handleRosterSizeChange = (size: number) => {
        const newStarterCount = getDefaultStartersForRosterSize(size);
        onChange({ roster_size: size, num_starters: newStarterCount });
    };

    const cardsSummary: SummaryItem[] = (() => {
        const restricted = team.allowed_card_sources ?? [];
        const items: SummaryItem[] = restricted.length > 0
            ? TEAM_CARD_SOURCES.filter(s => restricted.includes(s.value)).map(s => ({ value: s.label }))
            : [{ value: 'All Sources' }];
        activeSources(team).forEach(source => {
            allowedSetsForSource(team, source).forEach(set => {
                items.push({ value: set, image: imageForSet(set) });
            });
        });
        return items;
    })();

    const rulesSummary: SummaryItem[] = [
        { label: 'PTS', value: team.pts_limit != null ? String(team.pts_limit) : 'No Limit' },
        { label: 'Roster', value: String(rosterSize) },
        { label: 'SP', value: String(numStarters) },
        { label: 'Min Bullpen', value: String(minBullpen) },
        { label: 'Min Bench', value: String(minBench) },
        { label: 'Bench Pts', value: `${team.bench_pts_multiplier ?? 0.2}x` },
    ];

    const playerRestrictionsSummary: SummaryItem[] = (() => {
        if (Object.keys(pf).length === 0) return [];
        const items: SummaryItem[] = [];
        if (pf.min_year !== undefined || pf.max_year !== undefined) {
            if (pf.min_year === pf.max_year) {
                // Single year restriction
                items.push({ label: 'Year', value: `${pf.min_year}` });
            } else {
                items.push({ label: 'Year', value: `${pf.min_year ?? 'Any'}–${pf.max_year ?? 'Any'}` });
            }
        }
        
        (pf.organization ?? []).forEach(o => items.push({ label: 'Org', value: o }));
        (pf.league ?? []).forEach(l => items.push({ label: 'League', value: l }));
        (pf.team ?? []).forEach(t => items.push({ label: 'Team', value: t }));
        (pf.hand ?? []).forEach(h => items.push({ label: 'Bats', value: HAND_OPTIONS.find(o => o.value === h)?.label ?? h }));
        return items;
    })();

    return (
        <div className="flex flex-col lg:grid lg:grid-cols-2 gap-6 p-4">
            <FormSection title="Identity" icon={<FaUser />} isOpenByDefault={true}>
                <FormInput
                    label="Team Name"
                    className="col-span-full"
                    value={team.name ?? ''}
                    onChange={v => onChange({ name: v ?? '' })}
                    isTitleCase
                    maxLength={TEAM_NAME_MAX_LENGTH}
                />
                {nameError && (
                    <div className="col-span-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                        {nameError}
                    </div>
                )}
                <FormInput
                    label="Abbreviation"
                    value={team.abbreviation ?? ''}
                    onChange={v => onChange({ abbreviation: (v ?? '').toUpperCase().slice(0, 5) })}
                    placeholder="e.g. NYY"
                />
                {abbreviationError && (
                    <div className="col-span-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                        {abbreviationError}
                    </div>
                )}
                <div className='flex flex-col space-y-2' >
                    <label className="text-sm font-medium text-secondary mt-0.5">Make Public?</label>
                    <FormEnabler
                        label={`${team.is_public ?? true ? 'Public' : 'Private'}`}
                        isEnabled={team.is_public ?? true}
                        onChange={v => onChange({ is_public: !v })}
                    />
                </div>
                
                <ColorPicker
                    label="Primary Color"
                    value={team.primary_color ?? DEFAULT_PRIMARY_COLOR}
                    onChange={v => onChange({ primary_color: v })}
                />
                <ColorPicker
                    label="Secondary Color"
                    value={team.secondary_color ?? DEFAULT_SECONDARY_COLOR}
                    onChange={v => onChange({ secondary_color: v })}
                />
                <button
                    type="button"
                    onClick={handleSaveColorsAsDefault}
                    disabled={savedColorsAsDefault}
                    className="col-span-full self-start flex items-center gap-1.5 rounded-lg px-3 py-2 text-[12px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) disabled:opacity-70 cursor-pointer disabled:cursor-default transition-colors"
                >
                    {savedColorsAsDefault ? <><FaCheck /> Saved as default</> : <><FaFloppyDisk /> Save colors as default</>}
                </button>
            </FormSection>

            <FormSection
                key={`rules-${sectionLayoutKey}`}
                title="Rules"
                icon={<FaGears />}
                isOpenByDefault={isGridLayout}
                childrenWhenClosed={<SectionSummary items={rulesSummary} />}
            >
                <NumberInput
                    label="PTS Limit"
                    value={ptsLimit}
                    step={10}
                    onChange={v => onChange({ pts_limit: v })}
                />
                {ptsError && (
                    <div className="col-span-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                        {ptsError}
                    </div>
                )}
                <NumberInput
                    label={`Roster Size (${MIN_ROSTER}–${MAX_ROSTER})`}
                    value={team.roster_size ?? 25}
                    onChange={handleRosterSizeChange}
                />
                {rosterSizeError && (
                    <div className="col-span-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                        {rosterSizeError}
                    </div>
                )}
                <NumberInput
                    label={`Starting Pitchers (1–${MAX_STARTERS})`}
                    value={numStarters}
                    onChange={v => onChange({ num_starters: Math.max(1, Math.min(MAX_STARTERS, Math.round(v))) })}
                />
                <NumberInput
                    label="Min Bullpen"
                    value={minBullpen}
                    onChange={v => onChange({ min_bullpen: v })}
                />

                <NumberInput
                    label="Min Bench"
                    value={minBench}
                    onChange={v => onChange({ min_bench: v })}
                />

                <NumberInput
                    label="Bench PTS Multiplier"
                    value={team.bench_pts_multiplier ?? 0.2}
                    step={0.1}
                    onChange={v => onChange({ bench_pts_multiplier: v })}
                />
                {rosterError && (
                    <div className="col-span-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                        {rosterError}
                    </div>
                )}
            </FormSection>

            <FormSection
                key={`allowed-sets-${sectionLayoutKey}`}
                title="Allowed Sets"
                icon={<FaLayerGroup />}
                isOpenByDefault={isGridLayout}
                childrenWhenClosed={<SectionSummary items={cardsSummary} />}
            >
                <div className="flex flex-wrap gap-2 col-span-full">
                    <div className="text-sm font-semibold text-(--text-secondary) w-full">
                        Allowed Card Sources
                    </div>
                    {TEAM_CARD_SOURCES.map(s => {
                        const active = (team.allowed_card_sources ?? []).includes(s.value);
                        // Customs drafting isn't wired up yet — show it but don't let teams pick it.
                        const comingSoon = s.value === CardSource.CUSTOM;
                        // Challenges are Bot-only (WOTC is rejected at launch), so a challenge team
                        // can drop a stray non-Bot source but never add one or drop Bot — an empty
                        // list would mean "all sources".
                        const challengeLocked = isChallengeTeam && !comingSoon && (s.value === CardSource.BOT || !active);
                        return (
                            <button
                                key={s.value}
                                type="button"
                                disabled={comingSoon || challengeLocked}
                                onClick={() => {
                                    const current = team.allowed_card_sources ?? [];
                                    const next = active
                                        ? current.filter(v => v !== s.value)
                                        : [...current, s.value];
                                    onChange({ allowed_card_sources: next, ...normalizeSetSettings({ ...team, allowed_card_sources: next }) });
                                }}
                                className={`px-3 py-1.5 rounded-lg border-2 text-[12px] font-bold transition-colors
                                    ${comingSoon || (challengeLocked && !active)
                                        ? 'border-(--divider) opacity-40 text-(--text-secondary) cursor-not-allowed'
                                        : challengeLocked
                                        ? 'border-(--secondary) bg-(--secondary)/10 text-(--secondary) cursor-not-allowed'
                                        : active
                                        ? 'border-(--secondary) bg-(--secondary)/10 text-(--secondary) cursor-pointer'
                                        : 'border-(--divider) opacity-40 hover:opacity-70 text-(--text-secondary) cursor-pointer'
                                    }`}
                            >
                                {s.label}{comingSoon ? ' (Coming Soon)' : ''}
                            </button>
                        );
                    })}
                    {isChallengeTeam && (
                        <div className="w-full text-[11px] text-(--text-tertiary)">
                            Challenge teams can only use Bot cards.
                        </div>
                    )}
                    {(team.allowed_card_sources ?? []).length === 0 && (
                        <div className="w-full text-[11px] text-(--text-tertiary) px-2 py-1.5 rounded-lg border border-(--divider) bg-(--background-secondary)">
                            No restriction — all sources allowed.
                        </div>
                    )}
                </div>

                {/* Sets are chosen per source: Bot cards exist in every set so a team pins one,
                    while WOTC sets were printed alongside each other and can be combined. */}
                {activeSources(team).map(source => (
                    <SetToggleGroup
                        key={source}
                        label={`${TEAM_CARD_SOURCES.find(s => s.value === source)?.label ?? source} Sets`}
                        hint={isSingleSetSource(source) ? 'Pick one' : 'Combine any'}
                        options={setOptionsForSource(source)}
                        selected={allowedSetsForSource(team, source)}
                        onToggle={set => onChange(toggleSetForSource(team, source, set))}
                    />
                ))}
            </FormSection>

            <FormSection
                key={`player-restrictions-${sectionLayoutKey}`}
                title="Player Restrictions"
                icon={<FaFilter />}
                isOpenByDefault={isGridLayout}
                childrenWhenClosed={playerRestrictionsSummary.length > 0 ? <SectionSummary items={playerRestrictionsSummary} /> : undefined}
            >
                <RangeFilter
                    label="Year"
                    minValue={pf.min_year}
                    maxValue={pf.max_year}
                    onMinChange={n => updatePlayerFilters({ min_year: n })}
                    onMaxChange={n => updatePlayerFilters({ max_year: n })}
                />
                <TeamHierarchy
                    hierarchyData={hierarchyData}
                    selectedOrganizations={pf.organization}
                    selectedLeagues={pf.league}
                    selectedTeams={pf.team}
                    onOrganizationChange={values => updatePlayerFilters({ organization: values })}
                    onLeagueChange={values => updatePlayerFilters({ league: values })}
                    onTeamChange={values => updatePlayerFilters({ team: values })}
                />
                <div className="flex flex-wrap gap-2 col-span-full">
                    <div className="text-sm font-semibold text-(--text-secondary) w-full">Bats</div>
                    {HAND_OPTIONS.map(({ value, label }) => {
                        const active = (pf.hand ?? []).includes(value);
                        return (
                            <button
                                key={value}
                                type="button"
                                onClick={() => {
                                    const current = pf.hand ?? [];
                                    const next = active ? current.filter(v => v !== value) : [...current, value];
                                    updatePlayerFilters({ hand: next });
                                }}
                                className={`px-3 py-1.5 rounded-lg border-2 text-[12px] font-bold transition-colors cursor-pointer
                                    ${active
                                        ? 'border-(--secondary) bg-(--secondary)/10 text-(--secondary)'
                                        : 'border-(--divider) opacity-40 hover:opacity-70 text-(--text-secondary)'
                                    }`}
                            >
                                {label}
                            </button>
                        );
                    })}
                </div>
            </FormSection>

            {onArchive && (
                <div className={`col-span-full flex flex-col gap-2 rounded-xl border-2 p-3 ${team.is_archived
                    ? 'border-amber-500/50 bg-amber-500/10'
                    : 'border-red-500/50 bg-red-500/10'
                }`}>
                    <div className={`flex items-center gap-2 text-sm font-bold ${team.is_archived ? 'text-amber-500' : 'text-red-500'}`}>
                        {team.is_archived ? <FaBoxArchive /> : <FaTrashCan />}
                        {team.is_archived ? 'Team Archived' : 'Delete Team'}
                    </div>
                    <p className="text-[12px] text-(--text-secondary)">
                        {team.is_archived
                            ? 'This team is marked for deletion and hidden from your team list and from Browse. Unarchive it to restore its previous visibility.'
                            : 'Done with this team? Archiving marks it for deletion and hides it from your team list and from Browse. You can unarchive it any time if you change your mind.'}
                    </p>
                    <button
                        type="button"
                        onClick={onArchive}
                        disabled={archiving}
                        className={`self-start flex items-center gap-1.5 rounded-lg px-3 py-2 text-[12px] font-bold transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-default ${team.is_archived
                            ? 'border border-amber-500/60 text-amber-500 hover:bg-amber-500/15'
                            : 'bg-red-600 text-white hover:bg-red-700'
                        }`}
                    >
                        {archiving ? <FaSpinner className="animate-spin" /> : team.is_archived ? <FaBoxArchive /> : <FaTrashCan />}
                        {team.is_archived ? 'Unarchive team' : 'Archive team'}
                    </button>
                </div>
            )}
        </div>
    );
}


type SetToggleGroupProps = {
    label: string;
    /** Short rule reminder shown next to the label (e.g. "Pick one"). */
    hint: string;
    options: string[];
    selected: string[];
    onToggle: (set: string) => void;
};

/** Set picker for a single card source. Empty selection is an error — the caller decides how
 *  strictly to enforce it, but a team with no sets for a source can't draft from it. */
function SetToggleGroup({ label, hint, options, selected, onToggle }: SetToggleGroupProps) {
    return (
        <div className="flex flex-wrap gap-2 col-span-full">
            <div className="flex items-baseline gap-2 w-full">
                <span className="text-sm font-semibold text-(--text-secondary)">{label}</span>
                <span className="text-[11px] text-(--text-tertiary)">{hint}</span>
            </div>
            {options.map(value => {
                const active = selected.includes(value);
                const image = imageForSet(value);
                return (
                    <button
                        key={value}
                        type="button"
                        onClick={() => onToggle(value)}
                        className={`p-1 rounded-lg border-2 transition-colors cursor-pointer
                            ${active
                                ? 'border-(--secondary) bg-(--secondary)/10'
                                : 'border-(--divider) opacity-40 hover:opacity-70'
                            }`}
                    >
                        {image
                            ? <img src={image} alt={value} className="h-5 w-auto object-contain" />
                            : <span className="text-[11px] font-bold px-1">{value}</span>
                        }
                    </button>
                );
            })}
            {selected.length === 0 && (
                <div className="w-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                    At least one set must be selected.
                </div>
            )}
        </div>
    );
}


