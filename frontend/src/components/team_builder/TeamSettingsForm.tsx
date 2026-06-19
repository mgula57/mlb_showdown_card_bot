import React, { useState } from 'react';
import type { Team, TeamUpdatePayload } from '../../api/userTeams';
import FormInput from '../customs/FormInput';
import FormEnabler from '../customs/FormEnabler';
import { showdownSets } from '../shared/SiteSettingsContext';
import FormDropdown from '../customs/FormDropdown';

type TeamSettingsFormProps = {
    team: Partial<Team>;
    onChange: (updates: TeamUpdatePayload) => void;
};

export function TeamSettingsForm({ team, onChange }: TeamSettingsFormProps) {
    const setOptions = showdownSets.map(s => ({
        value: s.value,
        label: s.value,
        image: s.image,
    }));

    return (
        <div className="flex flex-col gap-3 p-4">
            {/* Identity */}
            <div className="grid grid-cols-2 gap-3">
                <FormInput
                    label="Team Name"
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
            </div>

            {/* Colors */}
            <div className="grid grid-cols-2 gap-3">
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
            </div>

            {/* Set */}
            <FormDropdown
                label="Showdown Set"
                options={setOptions}
                selectedOption={team.showdown_set ?? 'EXPANDED'}
                onChange={v => onChange({ showdown_set: v })}
            />

            {/* Visibility */}
            <FormEnabler
                label="Public (visible to others)"
                isEnabled={team.is_public ?? false}
                onChange={v => onChange({ is_public: v })}
            />

            {/* Roster constraints */}
            <div className="text-[11px] font-semibold text-(--text-secondary) uppercase tracking-wide pt-1">
                Roster Constraints
            </div>
            <div className="grid grid-cols-2 gap-3">
                <FormInput
                    label="PTS Limit"
                    value={team.pts_limit ?? ''}
                    type="number"
                    placeholder="None"
                    onChange={v => onChange({ pts_limit: v ? Number(v) : null })}
                />
                <FormInput
                    label="Roster Size"
                    value={team.roster_size ?? 25}
                    type="number"
                    onChange={v => onChange({ roster_size: Number(v) || 25 })}
                />
                <FormInput
                    label="Min Bench"
                    value={team.min_bench ?? 4}
                    type="number"
                    onChange={v => onChange({ min_bench: Number(v) || 4 })}
                />
                <FormInput
                    label="Min Bullpen"
                    value={team.min_bullpen ?? 5}
                    type="number"
                    onChange={v => onChange({ min_bullpen: Number(v) || 5 })}
                />
                <FormInput
                    label="Starting Pitchers"
                    value={team.num_starters ?? 5}
                    type="number"
                    onChange={v => onChange({ num_starters: Number(v) || 5 })}
                />
            </div>
            <FormInput
                label="Bench PTS Multiplier"
                value={team.bench_pts_multiplier ?? 1.0}
                type="number"
                onChange={v => onChange({ bench_pts_multiplier: Number(v) || 1.0 })}
            />

            {/* Allowed Sets */}
            <div className="text-[11px] font-semibold text-(--text-secondary) uppercase tracking-wide pt-1">
                Allowed Sets
            </div>
            <div className="flex flex-wrap gap-2">
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
                            className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border transition-colors
                                ${active
                                    ? 'border-(--secondary) text-(--secondary) bg-(--secondary)/10'
                                    : 'border-(--divider) text-(--text-secondary) hover:border-(--secondary)/50'
                                }`}
                        >
                            {s.value}
                        </button>
                    );
                })}
            </div>
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
