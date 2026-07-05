import React, { useState, useEffect } from 'react';
import type { Team, TeamUpdatePayload } from '../../api/userTeams';
import FormInput from '../customs/FormInput';
import FormEnabler from '../customs/FormEnabler';
import { showdownSets, imageForSet } from '../shared/SiteSettingsContext';
import FormSection from '../customs/FormSection';
import RangeFilter from '../customs/RangeFilter';
import { TeamHierarchy } from '../cards/TeamHierarchy';
import { fetchTeamHierarchy, type TeamHierarchyRecord } from '../../api/card_db/cardDatabase';
import { FaUser, FaLayerGroup, FaGears, FaFilter, FaDatabase } from 'react-icons/fa6';

type PlayerFilters = {
    min_year?: number;
    max_year?: number;
    organization?: string[];
    league?: string[];
    team?: string[];
};

const CARD_SOURCE_OPTIONS = [
    { value: 'BOT',  label: 'Bot' },
    { value: 'WOTC', label: 'WOTC' },
    { value: 'WBC',  label: 'WBC' },
] as const;

type TeamSettingsFormProps = {
    team: Partial<Team>;
    onChange: (updates: TeamUpdatePayload) => void;
    /** Which sections start collapsed. Default: all open. */
    collapsedSections?: Array<'identity' | 'set' | 'sources' | 'rules' | 'player_filters'>;
};

export function TeamSettingsForm({ team, onChange, collapsedSections = [] }: TeamSettingsFormProps) {
    const isOpen = (section: 'identity' | 'set' | 'sources' | 'rules' | 'player_filters') =>
        !collapsedSections.includes(section);

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
    const AllowedSetsToggle = (
        <div className="flex flex-wrap gap-2 col-span-full">
            <div className="text-sm font-semibold text-(--text-secondary) w-full">
                Allowed Showdown Sets
            </div>
            {showdownSets.map(s => {
                const active = (team.allowed_sets ?? []).includes(s.value);
                return (
                    <button
                        key={s.value}
                        type="button"
                        onClick={() => {
                            const current = team.allowed_sets ?? [];
                            const next = active
                                ? current.filter(v => v !== s.value)
                                : [...current, s.value];
                            onChange({ allowed_sets: next });
                        }}
                        className={`p-1 rounded-lg border-2 transition-colors
                            ${active
                                ? 'border-(--secondary) bg-(--secondary)/10'
                                : 'border-(--divider) opacity-40 hover:opacity-70'
                            }`}
                    >
                        {imageForSet(s.value)
                            ? <img src={imageForSet(s.value)} alt={s.value} className="h-5 w-auto object-contain" />
                            : <span className="text-[11px] font-bold px-1">{s.value}</span>
                        }
                    </button>
                );
            })}
        </div>
    );

    const LINEUP_SLOTS = 9;
    const rosterSize   = team.roster_size    ?? 25;
    const minBench     = team.min_bench      ?? 4;
    const minBullpen   = team.min_bullpen    ?? 5;
    const numStarters  = team.num_starters   ?? 5;
    const rosterUsed   = LINEUP_SLOTS + minBench + minBullpen + numStarters;
    const rosterError  = rosterUsed > rosterSize
        ? `Minimum roster needs ${rosterUsed} slots (9 lineup + ${numStarters} SP + ${minBullpen} bullpen + ${minBench} bench) but roster size is ${rosterSize}.`
        : null;
    const minPtsLimit  = rosterSize * 10;
    const ptsLimit     = team.pts_limit ?? null;
    const ptsError     = ptsLimit !== null && ptsLimit < minPtsLimit
        ? `PTS limit (${ptsLimit}) must be at least roster size × 10 (${minPtsLimit}).`
        : null;

    return (
        <div className="flex flex-col gap-3 p-4">
            <FormSection title="Identity" icon={<FaUser />} isOpenByDefault={isOpen('identity')}>
                <FormInput
                    label="Team Name"
                    className="col-span-full"
                    value={team.name ?? ''}
                    onChange={v => onChange({ name: v ?? '' })}
                    isTitleCase
                />
                <FormInput
                    label="Abbreviation"
                    value={team.abbreviation ?? ''}
                    onChange={v => onChange({ abbreviation: (v ?? '').toUpperCase().slice(0, 5) })}
                    placeholder="e.g. NYY"
                />
                <FormEnabler
                    label="Public"
                    isEnabled={team.is_public ?? false}
                    onChange={v => onChange({ is_public: !v })}
                />
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

            <FormSection title="Allowed Sets" icon={<FaLayerGroup />} isOpenByDefault={isOpen('set')}>
                {AllowedSetsToggle}
                {(team.allowed_sets ?? []).length === 0 && (
                    <div className="col-span-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                        At least one set must be selected.
                    </div>
                )}

                <div className="flex flex-wrap gap-2 col-span-full">
                    <div className="text-sm font-semibold text-(--text-secondary) w-full">
                        Allowed Card Sources
                    </div>
                    {CARD_SOURCE_OPTIONS.map(s => {
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
                                    onChange({ allowed_card_sources: next });
                                }}
                                className={`px-3 py-1.5 rounded-lg border-2 text-[12px] font-bold transition-colors
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
                
            </FormSection>

            <FormSection title="Rules" icon={<FaGears />} isOpenByDefault={isOpen('rules')}>
                <FormInput
                    label="PTS Limit"
                    value={team.pts_limit ?? ''}
                    type="number"
                    placeholder="None"
                    onChange={v => onChange({ pts_limit: v ? Number(v) : null })}
                    step={10}
                />
                {ptsError && (
                    <div className="col-span-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                        {ptsError}
                    </div>
                )}
                <FormInput
                    label="Roster Size"
                    value={team.roster_size ?? 20}
                    type="number"
                    onChange={v => onChange({ roster_size: Number(v) || 20 })}
                />
                <FormInput
                    label="Starting Pitchers"
                    value={team.num_starters ?? 4}
                    type="number"
                    onChange={v => onChange({ num_starters: Number(v) || 4 })}
                />
                <FormInput
                    label="Min Bullpen"
                    value={team.min_bullpen ?? 5}
                    type="number"
                    onChange={v => onChange({ min_bullpen: Number(v) || 5 })}
                />

                <FormInput
                    label="Min Bench"
                    value={team.min_bench ?? 4}
                    type="number"
                    onChange={v => onChange({ min_bench: Number(v) || 4 })}
                />

                <FormInput
                    label="Bench PTS Multiplier"
                    value={team.bench_pts_multiplier ?? 0.2}
                    type="number"
                    step={0.1}
                    onChange={v => onChange({ bench_pts_multiplier: Number(v) || 0.2 })}
                />
                {rosterError && (
                    <div className="col-span-full text-[11px] text-red-400 px-2 py-1.5 rounded-lg border border-red-400/30 bg-red-400/5">
                        {rosterError}
                    </div>
                )}
            </FormSection>

            <FormSection title="Player Filters" icon={<FaFilter />} isOpenByDefault={isOpen('player_filters')}>
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
            </FormSection>
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
