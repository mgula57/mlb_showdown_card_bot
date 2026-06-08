/**
 * @fileoverview TeamSettingsPanel - Collapsible settings form for a team
 */

import { useState } from 'react';
import FormSection from '../customs/FormSection';
import FormInput from '../customs/FormInput';
import FormDropdown from '../customs/FormDropdown';
import { showdownSets } from '../shared/SiteSettingsContext';
import type { TeamBuilderTeam, TeamBuilderTeamUpdates } from '../../api/teamBuilder';

interface TeamSettingsPanelProps {
    team: TeamBuilderTeam;
    onSave: (updates: TeamBuilderTeamUpdates) => Promise<void>;
    isSaving: boolean;
}

const setOptions = showdownSets.map(s => ({ value: s.value, label: s.value, image: s.image }));

export default function TeamSettingsPanel({ team, onSave, isSaving }: TeamSettingsPanelProps) {
    const [name, setName] = useState(team.name);
    const [showdownSet, setShowdownSet] = useState(team.showdown_set);
    const [rosterSize, setRosterSize] = useState(String(team.roster_size));
    const [bullpenSize, setBullpenSize] = useState(String(team.bullpen_size));
    const [benchMultiplier, setBenchMultiplier] = useState(String(team.bench_multiplier));

    const benchSlots = Math.max(0, (parseInt(rosterSize) || 25) - 9 - 5 - (parseInt(bullpenSize) || 7));

    const handleSave = async () => {
        const updates: TeamBuilderTeamUpdates = {};
        if (name.trim() !== team.name) updates.name = name.trim();
        if (showdownSet !== team.showdown_set) updates.showdown_set = showdownSet;
        const rs = parseInt(rosterSize);
        if (!isNaN(rs) && rs !== team.roster_size) updates.roster_size = rs;
        const bp = parseInt(bullpenSize);
        if (!isNaN(bp) && bp !== team.bullpen_size) updates.bullpen_size = bp;
        const bm = parseFloat(benchMultiplier);
        if (!isNaN(bm) && bm !== team.bench_multiplier) updates.bench_multiplier = bm;
        if (Object.keys(updates).length > 0) {
            await onSave(updates);
        }
    };

    return (
        <FormSection title="Team Settings" isOpenByDefault={false}>
            <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="col-span-2">
                    <FormInput
                        label="Team Name"
                        value={name}
                        onChange={(v) => setName(v ?? '')}
                        isClearable
                        isTitleCase
                        placeholder="My All-Time Team"
                    />
                </div>
                <FormDropdown
                    label="Showdown Set"
                    options={setOptions}
                    selectedOption={showdownSet}
                    onChange={setShowdownSet}
                />
                <FormInput
                    label="Roster Size"
                    value={rosterSize}
                    type="number"
                    onChange={(v) => setRosterSize(v ?? '25')}
                />
                <FormInput
                    label="Bullpen Slots"
                    value={bullpenSize}
                    type="number"
                    onChange={(v) => setBullpenSize(v ?? '7')}
                />
                <FormInput
                    label="Bench Multiplier"
                    value={benchMultiplier}
                    type="number"
                    onChange={(v) => setBenchMultiplier(v ?? '0.2')}
                />
            </div>
            <p className="text-xs text-(--text-tertiary) mb-3">
                Bench slots: {benchSlots} &nbsp;•&nbsp; Bench players count for {(parseFloat(benchMultiplier) * 100 || 20).toFixed(0)}% of their points
            </p>
            <button
                type="button"
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-1.5 rounded-lg text-sm font-semibold bg-(--showdown-red) text-white hover:brightness-110 disabled:opacity-50 cursor-pointer"
            >
                {isSaving ? 'Saving…' : 'Save Settings'}
            </button>
        </FormSection>
    );
}
