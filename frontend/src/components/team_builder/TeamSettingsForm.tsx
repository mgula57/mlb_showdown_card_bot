import React, { useState, useEffect } from 'react';
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
import { FaUser, FaLayerGroup, FaGears, FaFilter } from 'react-icons/fa6';

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
        <div className="text-sm font-bold flex flex-wrap items-center gap-x-2 gap-y-1 text-(--text-tertiary)">
            {items.map((item, i) => (
                <div key={`${item.label ?? ''}-${item.value}-${i}`} className="flex items-center rounded-lg px-1.5 py-0.5 border-2 border-(--divider)">
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
};

export function TeamSettingsForm({ team, onChange }: TeamSettingsFormProps) {
    const [hierarchyData, setHierarchyData] = useState<TeamHierarchyRecord[]>([]);
    useEffect(() => {
        fetchTeamHierarchy().then(setHierarchyData).catch(() => {});
    }, []);

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
    const minPtsLimit  = rosterSize * 10;
    const ptsLimit     = team.pts_limit ?? 5000;
    const ptsError     = ptsLimit < minPtsLimit
        ? `PTS limit (${ptsLimit}) must be at least roster size × 10 (${minPtsLimit}).`
        : null;

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

    const playerFiltersSummary: SummaryItem[] = (() => {
        if (Object.keys(pf).length === 0) return [];
        const items: SummaryItem[] = [];
        if (pf.min_year !== undefined || pf.max_year !== undefined) {
            items.push({ label: 'Year', value: `${pf.min_year ?? 'Any'}–${pf.max_year ?? 'Any'}` });
        }
        (pf.organization ?? []).forEach(o => items.push({ label: 'Org', value: o }));
        (pf.league ?? []).forEach(l => items.push({ label: 'League', value: l }));
        (pf.team ?? []).forEach(t => items.push({ label: 'Team', value: t }));
        (pf.hand ?? []).forEach(h => items.push({ label: 'Bats', value: HAND_OPTIONS.find(o => o.value === h)?.label ?? h }));
        return items;
    })();

    return (
        <div className="flex flex-col gap-6 p-4">
            <FormSection title="Identity" icon={<FaUser />} isOpenByDefault={true}>
                <FormInput
                    label="Team Name"
                    className="col-span-full"
                    value={team.name ?? ''}
                    onChange={v => onChange({ name: v ?? '' })}
                    isTitleCase
                    maxLength={TEAM_NAME_MAX_LENGTH}
                />
                <FormInput
                    label="Abbreviation"
                    value={team.abbreviation ?? ''}
                    onChange={v => onChange({ abbreviation: (v ?? '').toUpperCase().slice(0, 5) })}
                    placeholder="e.g. NYY"
                />
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
                    value={team.primary_color ?? 'rgb(0,0,0)'}
                    onChange={v => onChange({ primary_color: v })}
                />
                <ColorPicker
                    label="Secondary Color"
                    value={team.secondary_color ?? 'rgb(255,255,255)'}
                    onChange={v => onChange({ secondary_color: v })}
                />
            </FormSection>

            <FormSection
                title="Rules"
                icon={<FaGears />}
                isOpenByDefault={false}
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
                    value={team.min_bullpen ?? 5}
                    onChange={v => onChange({ min_bullpen: v })}
                />

                <NumberInput
                    label="Min Bench"
                    value={team.min_bench ?? 4}
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
                title="Allowed Sets"
                icon={<FaLayerGroup />}
                isOpenByDefault={false}
                childrenWhenClosed={<SectionSummary items={cardsSummary} />}
            >
                <div className="flex flex-wrap gap-2 col-span-full">
                    <div className="text-sm font-semibold text-(--text-secondary) w-full">
                        Allowed Card Sources
                    </div>
                    {TEAM_CARD_SOURCES.map(s => {
                        const active = (team.allowed_card_sources ?? []).includes(s.value);
                        return (
                            <button
                                key={s.value}
                                type="button"
                                onClick={() => {
                                    const current = team.allowed_card_sources ?? [];
                                    const next = active
                                        ? current.filter(v => v !== s.value)
                                        : [...current, s.value];
                                    onChange({ allowed_card_sources: next, ...normalizeSetSettings({ ...team, allowed_card_sources: next }) });
                                }}
                                className={`px-3 py-1.5 rounded-lg border-2 text-[12px] font-bold transition-colors cursor-pointer
                                    ${active
                                        ? 'border-(--secondary) bg-(--secondary)/10 text-(--secondary)'
                                        : 'border-(--divider) opacity-40 hover:opacity-70 text-(--text-secondary)'
                                    }`}
                            >
                                {s.label}
                            </button>
                        );
                    })}
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
                title="Player Filters"
                icon={<FaFilter />}
                isOpenByDefault={false}
                childrenWhenClosed={playerFiltersSummary.length > 0 ? <SectionSummary items={playerFiltersSummary} /> : undefined}
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


type ColorPickerProps = {
    label: string;
    value: string;       // "rgb(r, g, b)"
    onChange: (value: string) => void;
};

function rgbToHex(rgb: string): string {
    const match = rgb.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (!match) return '#000000';
    const r = parseInt(match[1]).toString(16).padStart(2, '0');
    const g = parseInt(match[2]).toString(16).padStart(2, '0');
    const b = parseInt(match[3]).toString(16).padStart(2, '0');
    return `#${r}${g}${b}`;
}

function hexToRgb(hex: string): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgb(${r}, ${g}, ${b})`;
}

function ColorPicker({ label, value, onChange }: ColorPickerProps) {
    const [hex, setHex] = useState(rgbToHex(value));

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newHex = e.target.value;
        setHex(newHex);
        onChange(hexToRgb(newHex));
    };

    return (
        <div className="flex flex-col gap-1">
            <label className="text-[11px] font-semibold text-(--text-secondary) uppercase tracking-wide">
                {label}
            </label>
            <div className="flex items-center gap-2">
                <input
                    type="color"
                    value={hex}
                    onChange={handleChange}
                    className="w-8 h-8 rounded border border-(--divider) cursor-pointer p-0"
                />
                <span className="text-[12px] text-(--text-secondary) font-mono">{value}</span>
            </div>
        </div>
    );
}
