import { useState } from 'react';
import { FaRobot } from 'react-icons/fa6';
import CustomSelect from '../../shared/CustomSelect';
import { TeamChip } from '../../shared/TeamChip';
import { EmptyState } from '../../shared/EmptyState';
import type { DraftState } from '../../../api/leagues';
import { leagueTeamIdentity } from '../leagueUi';
import { pickPositionLabel, type DraftView } from './draftView';

const ALL_TEAMS = 'all';

/** Every pick so far, newest first, optionally narrowed to one team. */
export function DraftHistory({ draft, view }: { draft: DraftState; view: DraftView }) {
    const [memberId, setMemberId] = useState(ALL_TEAMS);
    const picks = [...draft.picks]
        .filter(pick => memberId === ALL_TEAMS || pick.member_id === memberId)
        .reverse();

    return (
        <div className="flex flex-col gap-3">
            <CustomSelect
                value={memberId}
                onChange={setMemberId}
                options={[{ value: ALL_TEAMS, label: 'All teams' }, ...view.teams.map(t => ({ value: t.member_id, label: t.name }))]}
                size="sm"
            />
            {picks.length === 0 ? (
                <EmptyState size="inline">No picks yet.</EmptyState>
            ) : (
                <div className="flex flex-col rounded-card border border-(--divider) divide-y divide-(--divider) overflow-hidden">
                    {picks.map(pick => {
                        const team = view.teamsByMember.get(pick.member_id);
                        return (
                            <div key={pick.overall_pick} className="flex items-center gap-2 px-3 py-2 text-[12px] bg-(--background-secondary)">
                                <span className="w-9 shrink-0 tabular-nums text-(--text-tertiary)">#{pick.overall_pick}</span>
                                {team && <TeamChip team={leagueTeamIdentity(team)} size="sm" />}
                                <span className="flex-1 min-w-0 font-bold text-(--text-primary) truncate">{pick.name}</span>
                                {pick.is_auto && <FaRobot className="shrink-0 text-(--text-tertiary)" title="Auto-pick" />}
                                <span className="shrink-0 font-semibold text-(--text-tertiary)">{pickPositionLabel(pick)}</span>
                                <span className="shrink-0 w-12 text-right tabular-nums text-(--text-secondary)">{pick.points}</span>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
