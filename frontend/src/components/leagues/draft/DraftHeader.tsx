import { FaDisplay, FaRobot, FaSpinner, FaTrophy } from 'react-icons/fa6';
import { TeamChip } from '../../shared/TeamChip';
import type { DraftState } from '../../../api/leagues';
import { SECONDARY_BUTTON_CLASS, leagueTeamIdentity } from '../leagueUi';
import type { DraftView } from './draftView';

type Props = {
    draft: DraftState;
    view: DraftView;
    myMemberId: string | null;
    isCommissioner: boolean;
    autoPicking: boolean;
    onAutoPick: () => void;
    onOpenBigBoard: () => void;
};

/** Who's on the clock, the last pick, and the picks coming up. Shared by every draft layout. */
export function DraftHeader({ draft, view, myMemberId, isCommissioner, autoPicking, onAutoPick, onOpenBigBoard }: Props) {
    const { onTheClock, lastPick, isMyTurn, isComplete } = view;
    const lastPickTeam = lastPick ? view.teamsByMember.get(lastPick.member_id) : null;
    const picksUntilMine = myMemberId ? draft.upcoming.findIndex(p => p.member_id === myMemberId) : -1;
    const canAutoPick = !isComplete && (isMyTurn || isCommissioner);

    return (
        <div className="flex flex-col gap-3 rounded-2xl border border-(--divider) bg-linear-to-br from-(--background-tertiary) to-(--background-secondary) p-3 sm:p-4">
            <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-1 min-w-0">
                    {isComplete ? (
                        <div className="flex items-center gap-2 text-[18px] font-black text-(--text-primary)">
                            <FaTrophy className="text-(--secondary)" /> Draft complete
                        </div>
                    ) : (
                        <>
                            <div className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">
                                On the clock · Pick {draft.next_pick} · Round {draft.current_round}
                            </div>
                            <div className="flex items-center gap-2 min-w-0">
                                {onTheClock && <TeamChip team={leagueTeamIdentity(onTheClock)} />}
                                <span className="text-[16px] sm:text-[18px] font-black text-(--text-primary) truncate">
                                    {isMyTurn ? 'Your pick!' : onTheClock?.display_name}
                                </span>
                            </div>
                            {!isMyTurn && picksUntilMine > 0 && (
                                <div className="text-[11px] text-(--text-secondary)">Your pick in {picksUntilMine}</div>
                            )}
                        </>
                    )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                    {/* The Big Board is for a TV or monitor - not offered on phones */}
                    <button type="button" onClick={onOpenBigBoard} className={`${SECONDARY_BUTTON_CLASS} hidden md:flex`}>
                        <FaDisplay /> Big Board
                    </button>
                    {canAutoPick && (
                        <button type="button" onClick={onAutoPick} disabled={autoPicking} className={SECONDARY_BUTTON_CLASS} title={isMyTurn ? 'Let the bot pick for you' : `Auto-pick for ${onTheClock?.display_name}`}>
                            {autoPicking ? <FaSpinner className="animate-spin" /> : <FaRobot />}
                            <span className="hidden sm:inline">Auto-pick</span>
                        </button>
                    )}
                </div>
            </div>

            {lastPick && (
                <div className="flex items-center gap-2 text-[12px] text-(--text-secondary) min-w-0">
                    <span className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary) shrink-0">Last pick</span>
                    <span className="tabular-nums shrink-0">#{lastPick.overall_pick}</span>
                    {lastPickTeam && <TeamChip team={leagueTeamIdentity(lastPickTeam)} size="sm" />}
                    <span className="font-bold text-(--text-primary) truncate">{lastPick.name}</span>
                    <span className="tabular-nums shrink-0">{lastPick.points} pts</span>
                </div>
            )}

            {!isComplete && draft.upcoming.length > 1 && (
                <div className="flex gap-1.5 overflow-x-auto pb-0.5 -mx-1 px-1">
                    {draft.upcoming.slice(1).map(pick => {
                        const team = view.teamsByMember.get(pick.member_id);
                        const isMine = pick.member_id === myMemberId;
                        return (
                            <div
                                key={pick.overall_pick}
                                className={`flex items-center gap-1.5 shrink-0 rounded-lg px-2 py-1 border text-[11px] ${isMine ? 'border-(--secondary) bg-(--secondary)/15' : 'border-(--divider) bg-(--background-primary)'}`}
                            >
                                <span className="tabular-nums text-(--text-tertiary)">#{pick.overall_pick}</span>
                                {team && <TeamChip team={leagueTeamIdentity(team)} size="sm" />}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

