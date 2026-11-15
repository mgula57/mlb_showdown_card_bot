/**
 * @fileoverview Picks a team to play: the user's own finished teams, and optionally public ones with a
 * search. Shared by everything that pits one team against another (a Faceoff, a live game).
 */
import { useEffect, useState } from 'react';

import { fetchPublicTeams, fetchUserTeams, type TeamSummary } from '../../api/userTeams';
import { EmptyState } from '../shared/EmptyState';
import { Tabs, type TabItem } from '../shared/Tabs';
import { isPlayable } from './faceoff/teamPicking';
import { TeamCard } from './TeamCard';
import { TeamSearchInput } from './TeamSearchInput';

type PickerTab = 'mine' | 'public';
const PICKER_TABS: TabItem<PickerTab>[] = [
    { id: 'mine', label: 'My Teams' },
    { id: 'public', label: 'Public Teams' },
];
const PUBLIC_RESULT_LIMIT = 30;
const SEARCH_DEBOUNCE_MS = 300;

type Props = {
    token: string;
    selectedTeamId?: string | null;
    onPick: (team: TeamSummary) => void;
    /** Offers public teams too, under their own tab. */
    allowPublic?: boolean;
    /** Left out of both lists, e.g. the team on the other side. */
    excludeTeamId?: string | null;
    /** Public teams by this user are left out (they're under My Teams already). */
    excludePublicUserId?: string | null;
    /** What to say when the user has no team to pick. */
    emptyMessage?: string;
};

export function TeamPicker({ token, selectedTeamId, onPick, allowPublic = false, excludeTeamId, excludePublicUserId, emptyMessage = 'You need a finished team first.' }: Props) {
    const [myTeams, setMyTeams] = useState<TeamSummary[] | null>(null);
    const [publicTeams, setPublicTeams] = useState<TeamSummary[] | null>(null);
    const [tab, setTab] = useState<PickerTab>('mine');
    const [query, setQuery] = useState('');

    useEffect(() => {
        let stale = false;
        fetchUserTeams(token)
            .then(teams => { if (!stale) setMyTeams(teams.filter(t => isPlayable(t) && t.team_id !== excludeTeamId)); })
            .catch(() => { if (!stale) setMyTeams([]); });
        return () => { stale = true; };
    }, [token, excludeTeamId]);

    useEffect(() => {
        if (tab !== 'public') return;
        let stale = false;
        const timer = setTimeout(() => {
            fetchPublicTeams(['user', 'official'], PUBLIC_RESULT_LIMIT, 0, query.trim() || undefined)
                .then(teams => { if (!stale) setPublicTeams(teams.filter(t => isPlayable(t) && t.team_id !== excludeTeamId && t.user_id !== excludePublicUserId)); })
                .catch(() => { if (!stale) setPublicTeams([]); });
        }, SEARCH_DEBOUNCE_MS);
        return () => { stale = true; clearTimeout(timer); };
    }, [tab, query, excludeTeamId, excludePublicUserId]);

    const showPublic = allowPublic && tab === 'public';
    const teams = showPublic ? publicTeams : myTeams;

    return (
        <div className="flex flex-col gap-3">
            {allowPublic && <Tabs tabs={PICKER_TABS} value={tab} onChange={setTab} fullWidth />}
            {showPublic && <TeamSearchInput value={query} onChange={setQuery} placeholder="Search public teams…" />}
            {teams === null ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 animate-pulse" aria-label="Loading teams">
                    {Array.from({ length: 4 }, (_, i) => <div key={i} className="h-16 rounded-control bg-(--background-tertiary)" />)}
                </div>
            ) : teams.length === 0 ? (
                <EmptyState size="inline">{showPublic ? 'No public teams found.' : emptyMessage}</EmptyState>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-72 overflow-y-auto scrollbar-hide">
                    {teams.map(summary => (
                        <TeamCard key={summary.team_id} team={summary} isSelected={summary.team_id === selectedTeamId} onClick={() => onPick(summary)} />
                    ))}
                </div>
            )}
        </div>
    );
}
