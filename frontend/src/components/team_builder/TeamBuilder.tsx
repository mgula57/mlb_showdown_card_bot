/**
 * @fileoverview TeamBuilder - Team list view and entry point for the team builder
 */

import { useState, useEffect } from 'react';
import { FaPlus, FaUsers } from 'react-icons/fa';
import { useAuth } from '../auth/AuthContext';
import { useSiteSettings, showdownSets } from '../shared/SiteSettingsContext';
import FormInput from '../customs/FormInput';
import FormDropdown from '../customs/FormDropdown';
import {
    listTeams,
    createTeam,
    deleteTeam,
    type TeamBuilderTeam,
} from '../../api/teamBuilder';
import TeamBuilderEditor from './TeamBuilderEditor';

const setOptions = showdownSets.map(s => ({ value: s.value, label: s.value, image: s.image }));

function TeamCard({ team, onOpen, onDelete }: { team: TeamBuilderTeam; onOpen: () => void; onDelete: () => void }) {
    const [confirmDelete, setConfirmDelete] = useState(false);

    const updatedDate = new Date(team.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

    return (
        <div
            className="relative rounded-xl border border-(--divider) bg-(--background-secondary) p-4 cursor-pointer hover:border-(--showdown-blue)/60 transition-colors group"
            onClick={onOpen}
        >
            <div className="flex items-start justify-between gap-2">
                <div>
                    <h3 className="font-semibold text-(--text-primary) truncate">{team.name}</h3>
                    <div className="flex gap-2 mt-1 flex-wrap">
                        <span className="text-xs px-1.5 py-0.5 rounded bg-(--background-tertiary) text-(--text-secondary) font-medium uppercase">{team.showdown_set}</span>
                        <span className="text-xs text-(--text-tertiary)">{team.roster_size} players</span>
                    </div>
                    <p className="text-xs text-(--text-tertiary) mt-2">Updated {updatedDate}</p>
                </div>
                <div className="flex flex-col items-end gap-1 shrink-0">
                    {!confirmDelete ? (
                        <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); setConfirmDelete(true); }}
                            className="opacity-0 group-hover:opacity-100 text-xs text-(--text-tertiary) hover:text-(--red) transition-all cursor-pointer"
                        >
                            Delete
                        </button>
                    ) : (
                        <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                            <button type="button" onClick={() => setConfirmDelete(false)} className="text-xs px-2 py-0.5 rounded bg-(--background-tertiary) text-(--text-secondary) cursor-pointer">Cancel</button>
                            <button type="button" onClick={onDelete} className="text-xs px-2 py-0.5 rounded bg-(--red) text-white cursor-pointer">Confirm</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function TeamBuilder() {
    const { user } = useAuth();
    const { userShowdownSet } = useSiteSettings();

    const [teams, setTeams] = useState<TeamBuilderTeam[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
    const [isCreating, setIsCreating] = useState(false);
    const [newName, setNewName] = useState('');
    const [newSet, setNewSet] = useState(userShowdownSet);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!user) { setIsLoading(false); return; }
        listTeams('custom')
            .then(setTeams)
            .catch(e => setError(e.message))
            .finally(() => setIsLoading(false));
    }, [user]);

    const handleCreate = async () => {
        if (!newName.trim()) return;
        setIsSubmitting(true);
        try {
            const team = await createTeam({ name: newName.trim(), showdown_set: newSet, team_type: 'custom' });
            setTeams(prev => [team, ...prev]);
            setIsCreating(false);
            setNewName('');
            setSelectedTeamId(team.id);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Create failed');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async (teamId: number) => {
        try {
            await deleteTeam(teamId);
            setTeams(prev => prev.filter(t => t.id !== teamId));
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Delete failed');
        }
    };

    if (selectedTeamId !== null) {
        return (
            <TeamBuilderEditor
                teamId={selectedTeamId}
                onBack={() => setSelectedTeamId(null)}
            />
        );
    }

    if (!user) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-3 text-(--text-secondary)">
                <FaUsers className="w-10 h-10 opacity-30" />
                <p className="text-lg font-semibold">Sign in to build teams</p>
                <p className="text-sm">Create and save your custom Showdown lineups.</p>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-(--text-primary)">My Teams</h1>
                    <p className="text-sm text-(--text-secondary) mt-0.5">Build custom Showdown lineups from the card database</p>
                </div>
                <button
                    type="button"
                    onClick={() => setIsCreating(true)}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-(--showdown-red) text-white font-semibold text-sm hover:brightness-110 transition-all cursor-pointer"
                >
                    <FaPlus className="w-3 h-3" />
                    New Team
                </button>
            </div>

            {/* Create form */}
            {isCreating && (
                <div className="rounded-xl border border-(--divider) bg-(--background-secondary) p-4 space-y-3">
                    <h2 className="font-semibold text-(--text-primary) text-sm">New Team</h2>
                    <div className="grid grid-cols-2 gap-3">
                        <FormInput
                            label="Team Name"
                            value={newName}
                            onChange={v => setNewName(v ?? '')}
                            isTitleCase
                            placeholder="My All-Time Team"
                            className="col-span-2"
                        />
                        <FormDropdown
                            label="Showdown Set"
                            options={setOptions}
                            selectedOption={newSet}
                            onChange={setNewSet}
                            className="col-span-2"
                        />
                    </div>
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={handleCreate}
                            disabled={isSubmitting || !newName.trim()}
                            className="px-4 py-1.5 rounded-lg text-sm font-semibold bg-(--showdown-red) text-white hover:brightness-110 disabled:opacity-50 cursor-pointer"
                        >
                            {isSubmitting ? 'Creating…' : 'Create Team'}
                        </button>
                        <button
                            type="button"
                            onClick={() => { setIsCreating(false); setNewName(''); }}
                            className="px-4 py-1.5 rounded-lg text-sm font-semibold bg-(--background-tertiary) text-(--text-secondary) hover:bg-(--background-quaternary) cursor-pointer"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {error && <p className="text-xs text-(--red)">{error}</p>}

            {/* Teams list */}
            {isLoading ? (
                <div className="flex items-center gap-2 py-8">
                    {[0, 150, 300].map(d => (
                        <span key={d} className="w-2 h-2 rounded-full bg-(--text-secondary) animate-bounce" style={{ animationDelay: `${d}ms` }} />
                    ))}
                </div>
            ) : teams.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3 text-(--text-secondary)">
                    <FaUsers className="w-10 h-10 opacity-20" />
                    <p className="font-semibold">No teams yet</p>
                    <p className="text-sm">Click <strong>New Team</strong> to get started.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {teams.map(team => (
                        <TeamCard
                            key={team.id}
                            team={team}
                            onOpen={() => setSelectedTeamId(team.id)}
                            onDelete={() => handleDelete(team.id)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
