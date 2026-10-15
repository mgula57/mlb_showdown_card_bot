import { useState } from 'react';
import CustomSelect from '../../shared/CustomSelect';
import type { DraftPick, DraftState, LeagueSettings } from '../../../api/leagues';
import { teamRoster } from './draftView';

type Props = {
    draft: DraftState;
    settings: LeagueSettings;
    myMemberId: string | null;
};

/** A team's roster as drafted so far, by position, with what it still needs. Defaults to the
 *  viewer's team; any team can be picked to scout. */
export function DraftTeamPanel({ draft, settings, myMemberId }: Props) {
    const [memberId, setMemberId] = useState<string>(myMemberId ?? draft.teams[0]?.member_id ?? '');
    const team = draft.teams.find(t => t.member_id === memberId) ?? draft.teams[0];
    if (!team) return null;
    const roster = teamRoster(draft.picks, team, settings);

    return (
        <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-2">
                <CustomSelect
                    value={team.member_id}
                    onChange={setMemberId}
                    options={draft.teams.map(t => ({ value: t.member_id, label: t.member_id === myMemberId ? `${t.name} (you)` : t.name }))}
                    buttonClassName="text-[12px] py-1 px-2 rounded-md bg-(--background-tertiary) text-(--text-primary) cursor-pointer"
                />
                {roster.required > 0 ? (
                    <span className="shrink-0 rounded-full bg-(--secondary)/15 text-(--secondary) px-2 py-0.5 text-[10px] font-black uppercase tracking-wide">
                        {roster.required} more needed
                    </span>
                ) : (
                    <span className="shrink-0 text-[10px] font-bold text-(--success) uppercase tracking-wide">Required spots filled</span>
                )}
            </div>
            <div className="text-[11px] text-(--text-tertiary)">
                {roster.picksMade}/{settings.roster_size} picks · {roster.points} pts{settings.pts_cap ? ` of ${settings.pts_cap}` : ''}
            </div>

            <RosterGroup title="Lineup" filled={roster.lineup.filter(s => s.pick).length} total={roster.lineup.length}>
                {roster.lineup.map(({ position, pick }) => <RosterRow key={position} position={position} pick={pick} />)}
            </RosterGroup>
            <RosterGroup title="Rotation" filled={roster.rotation.filter(s => s.pick).length} total={roster.rotation.length}>
                {roster.rotation.map(({ position, pick }) => <RosterRow key={position} position={position} pick={pick} />)}
            </RosterGroup>
            <RosterGroup title="Bullpen" filled={roster.bullpen.length} total={settings.min_bullpen} isMinimum>
                {roster.bullpen.map(pick => <RosterRow key={pick.release_card_id} position={pick.roster_position ?? 'RP'} pick={pick} />)}
            </RosterGroup>
            <RosterGroup title="Bench" filled={roster.bench.length} total={settings.min_bench} isMinimum>
                {roster.bench.map(pick => <RosterRow key={pick.release_card_id} position="BE" pick={pick} />)}
            </RosterGroup>
        </div>
    );
}

function RosterGroup({ title, filled, total, isMinimum = false, children }: { title: string; filled: number; total: number; isMinimum?: boolean; children: React.ReactNode }) {
    return (
        <div className="flex flex-col rounded-xl border border-(--divider) overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 bg-(--background-tertiary)">
                <span className="text-[12px] font-black text-(--text-primary)">{title}</span>
                <span className={`text-[11px] font-bold tabular-nums ${filled >= total ? 'text-(--success)' : 'text-(--text-secondary)'}`}>
                    {filled}/{total}{isMinimum ? '+' : ''}
                </span>
            </div>
            <div className="flex flex-col divide-y divide-(--divider)">
                {children}
                {isMinimum && filled < total && Array.from({ length: total - filled }, (_, i) => (
                    <RosterRow key={`open-${i}`} position={title === 'Bench' ? 'BE' : 'RP'} pick={null} />
                ))}
            </div>
        </div>
    );
}

function RosterRow({ position, pick }: { position: string; pick: DraftPick | null }) {
    return (
        <div className="flex items-center gap-2 px-3 py-1.5 text-[12px] bg-(--background-secondary)">
            <span className="w-8 shrink-0 font-black text-(--text-tertiary)">{position}</span>
            {pick ? (
                <>
                    <span className="flex-1 min-w-0 font-bold text-(--text-primary) truncate">{pick.name}</span>
                    <span className="shrink-0 tabular-nums text-(--text-secondary)">{pick.points}</span>
                </>
            ) : (
                <span className="flex-1 text-(--text-tertiary) italic">Empty</span>
            )}
        </div>
    );
}
