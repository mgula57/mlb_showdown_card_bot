/**
 * @fileoverview TeamBuilderEditor - Full editor for a single saved team
 */

import { useState, useEffect, useCallback } from 'react';
import { FaArrowLeft } from 'react-icons/fa';
import {
    getTeamWithSlots,
    updateTeam,
    upsertSlot,
    deleteSlot,
    type TeamBuilderTeamWithSlots,
    type TeamBuilderSlot,
    type TeamBuilderCardSnapshot,
    type TeamBuilderTeamUpdates,
} from '../../api/teamBuilder';
import TeamFieldView from './TeamFieldView';
import TeamPitchersView from './TeamPitchersView';
import TeamSettingsPanel from './TeamSettingsPanel';
import CardPickerModal from './CardPickerModal';
import TeamSlot from './TeamSlot';

interface TeamBuilderEditorProps {
    teamId: number;
    onBack: () => void;
}

type Tab = 'field' | 'pitchers' | 'bench';

const FIELD_KEYS = new Set(['CA', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH']);
const SP_KEYS = new Set(['SP1', 'SP2', 'SP3', 'SP4', 'SP5']);

function computePoints(team: TeamBuilderTeamWithSlots): { starters: number; bench: number; total: number } {
    let starters = 0;
    let bench = 0;
    for (const slot of team.slots) {
        const pts = slot.card_snapshot?.points ?? 0;
        if (FIELD_KEYS.has(slot.slot_key) || SP_KEYS.has(slot.slot_key) || slot.slot_key.startsWith('RP')) {
            starters += pts;
        } else if (slot.slot_key.startsWith('BE')) {
            bench += pts;
        }
    }
    const total = starters + Math.round(bench * team.bench_multiplier);
    return { starters, bench, total };
}

export default function TeamBuilderEditor({ teamId, onBack }: TeamBuilderEditorProps) {
    const [team, setTeam] = useState<TeamBuilderTeamWithSlots | null>(null);
    const [slotMap, setSlotMap] = useState<Record<string, TeamBuilderSlot>>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState<Tab>('field');
    const [pickerSlotKey, setPickerSlotKey] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setIsLoading(true);
        getTeamWithSlots(teamId)
            .then(t => {
                setTeam(t);
                const map: Record<string, TeamBuilderSlot> = {};
                for (const s of t.slots) map[s.slot_key] = s;
                setSlotMap(map);
            })
            .catch(e => setError(e.message))
            .finally(() => setIsLoading(false));
    }, [teamId]);

    const handleSaveSettings = useCallback(async (updates: TeamBuilderTeamUpdates) => {
        if (!team) return;
        setIsSaving(true);
        try {
            await updateTeam(team.id, updates);
            setTeam(prev => prev ? { ...prev, ...updates } : prev);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Save failed');
        } finally {
            setIsSaving(false);
        }
    }, [team]);

    const handleSlotClick = useCallback((slotKey: string) => {
        setPickerSlotKey(slotKey);
    }, []);

    const handleSlotRemove = useCallback(async (slotKey: string) => {
        if (!team) return;
        try {
            await deleteSlot(team.id, slotKey);
            setSlotMap(prev => { const next = { ...prev }; delete next[slotKey]; return next; });
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Remove failed');
        }
    }, [team]);

    const handleCardSelect = useCallback(async (
        snapshot: TeamBuilderCardSnapshot,
        cardId: string,
        source: 'bot' | 'wotc',
    ) => {
        if (!team || !pickerSlotKey) return;
        setPickerSlotKey(null);
        try {
            await upsertSlot(team.id, pickerSlotKey, source, cardId, snapshot);
            const newSlot: TeamBuilderSlot = {
                id: Date.now(),
                team_id: team.id,
                slot_key: pickerSlotKey,
                card_source: source,
                card_id: cardId,
                card_snapshot: snapshot,
                created_at: new Date().toISOString(),
            };
            setSlotMap(prev => ({ ...prev, [pickerSlotKey]: newSlot }));
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Update failed');
        }
    }, [team, pickerSlotKey]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-48 gap-2">
                {[0, 150, 300].map(d => (
                    <span key={d} className="w-2 h-2 rounded-full bg-(--text-secondary) animate-bounce" style={{ animationDelay: `${d}ms` }} />
                ))}
            </div>
        );
    }

    if (!team) {
        return <p className="text-(--text-secondary) p-6">{error ?? 'Team not found.'}</p>;
    }

    const pts = computePoints({ ...team, slots: Object.values(slotMap) });
    const benchSlots = Math.max(0, team.roster_size - 9 - 5 - team.bullpen_size);
    const benchKeys = Array.from({ length: benchSlots }, (_, i) => `BE${i + 1}`);
    const tabs: { id: Tab; label: string }[] = [
        { id: 'field', label: 'Field' },
        { id: 'pitchers', label: 'Pitchers' },
        { id: 'bench', label: 'Bench' },
    ];

    return (
        <div className="max-w-5xl mx-auto space-y-4 px-4 py-4">
            {/* Header */}
            <div className="flex items-center gap-3">
                <button type="button" onClick={onBack} className="text-(--text-secondary) hover:text-(--text-primary) cursor-pointer">
                    <FaArrowLeft />
                </button>
                <h1 className="text-xl font-bold text-(--text-primary)">{team.name}</h1>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-(--background-tertiary) text-(--text-secondary) uppercase">{team.showdown_set}</span>
            </div>

            {/* Points summary */}
            <div className="flex flex-wrap gap-4 text-sm rounded-xl border border-(--divider) px-4 py-3 bg-(--background-secondary)">
                <span className="text-(--text-secondary)">Starters <span className="font-bold text-(--text-primary)">{pts.starters}</span></span>
                <span className="text-(--text-secondary)">Bench <span className="font-bold text-(--text-primary)">{pts.bench}</span> <span className="text-(--text-tertiary)">×{team.bench_multiplier}</span></span>
                <span className="text-(--text-secondary) font-semibold">Total <span className="text-(--text-primary)">{pts.total} pts</span></span>
            </div>

            {/* Settings */}
            <TeamSettingsPanel team={team} onSave={handleSaveSettings} isSaving={isSaving} />

            {/* Tabs */}
            <div className="flex gap-1 border-b border-(--divider)">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        type="button"
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors cursor-pointer ${
                            activeTab === tab.id
                                ? 'bg-(--background-secondary) border border-b-0 border-(--divider) text-(--text-primary)'
                                : 'text-(--text-secondary) hover:text-(--text-primary)'
                        }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab content */}
            <div className="bg-(--background-secondary) rounded-xl border border-(--divider) p-4">
                {activeTab === 'field' && (
                    <TeamFieldView
                        slotMap={slotMap}
                        onSlotClick={handleSlotClick}
                        onSlotRemove={handleSlotRemove}
                    />
                )}
                {activeTab === 'pitchers' && (
                    <TeamPitchersView
                        slotMap={slotMap}
                        bullpenSize={team.bullpen_size}
                        onSlotClick={handleSlotClick}
                        onSlotRemove={handleSlotRemove}
                    />
                )}
                {activeTab === 'bench' && (
                    <div>
                        {benchSlots === 0 ? (
                            <p className="text-(--text-secondary) text-sm">No bench slots. Increase roster size or reduce bullpen slots in settings.</p>
                        ) : (
                            <div className="flex flex-wrap gap-3 py-2">
                                {benchKeys.map(key => (
                                    <TeamSlot
                                        key={key}
                                        slotKey={key}
                                        slot={slotMap[key]}
                                        onClick={() => handleSlotClick(key)}
                                        onRemove={slotMap[key] ? () => handleSlotRemove(key) : undefined}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {error && (
                <p className="text-xs text-(--red) px-2">{error}</p>
            )}

            {/* Card picker modal */}
            {pickerSlotKey && (
                <CardPickerModal
                    slotKey={pickerSlotKey}
                    onSelect={handleCardSelect}
                    onClose={() => setPickerSlotKey(null)}
                    defaultSet={team.showdown_set}
                />
            )}
        </div>
    );
}
