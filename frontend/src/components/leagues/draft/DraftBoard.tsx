import { TeamChip } from '../../shared/TeamChip';
import type { DraftState } from '../../../api/leagues';
import { leagueTeamIdentity } from '../leagueUi';
import { pickPositionLabel, shortName, type DraftView } from './draftView';

type Props = {
    draft: DraftState;
    view: DraftView;
    myMemberId: string | null;
    /** `big` is the TV Big Board: larger type, sized to fill the screen. */
    size?: 'normal' | 'big';
    /** Inclusive round range to show; defaults to every round. The Big Board passes a window
     *  around the current round so it fits one screen. */
    rounds?: [number, number];
};

const SIZES = {
    normal: { column: 'minmax(104px, 1fr)', roundColumn: '32px', cell: 'min-h-14 p-1.5 text-[11px]', name: 'text-[12px]', header: 'py-1.5' },
    big: { column: 'minmax(120px, 1fr)', roundColumn: '56px', cell: 'min-h-[9vh] p-2.5 text-[1.1vw]', name: 'text-[1.35vw]', header: 'py-3' },
};

/** Rounds x teams grid of picks: done picks filled in, the live pick marked, the rest empty.
 *  Scrolls sideways when the teams don't fit, with the team row and round column pinned. */
export function DraftBoard({ draft, view, myMemberId, size = 'normal', rounds }: Props) {
    const sizing = SIZES[size];
    const [firstRound, lastRound] = rounds ?? [1, draft.rounds];
    const roundNumbers = Array.from({ length: lastRound - firstRound + 1 }, (_, i) => firstRound + i);
    const gridTemplateColumns = `${sizing.roundColumn} repeat(${view.teams.length}, ${sizing.column})`;

    return (
        <div className="overflow-auto rounded-xl border border-(--divider) bg-(--background-primary)">
            <div className="grid min-w-max" style={{ gridTemplateColumns }}>
                {/* Team row */}
                <div className="sticky top-0 left-0 z-20 bg-(--background-secondary) border-b border-(--divider)" />
                {view.teams.map(team => (
                    <div
                        key={team.member_id}
                        className={`sticky top-0 z-10 flex flex-col items-center gap-0.5 px-1 ${sizing.header} border-b border-l border-(--divider) ${team.member_id === myMemberId ? 'bg-(--secondary)/15' : 'bg-(--background-secondary)'}`}
                    >
                        <TeamChip team={leagueTeamIdentity(team)} size={size === 'big' ? 'md' : 'sm'} />
                        <span className={`truncate max-w-full text-(--text-secondary) ${size === 'big' ? 'text-[1vw]' : 'text-[10px]'}`}>{team.display_name}</span>
                    </div>
                ))}

                {roundNumbers.map(round => (
                    <div key={round} className="contents">
                        <div className={`sticky left-0 z-10 flex items-center justify-center bg-(--background-secondary) border-b border-(--divider) font-black text-(--text-tertiary) ${size === 'big' ? 'text-[1.2vw]' : 'text-[11px]'}`}>
                            {round}
                        </div>
                        {view.teams.map(team => {
                            const pick = view.pickFor(round, team.member_id);
                            const isLive = !pick && draft.current_round === round && draft.on_the_clock_member_id === team.member_id;
                            return (
                                <div
                                    key={team.member_id}
                                    className={`border-b border-l border-(--divider) ${sizing.cell} ${isLive ? 'bg-(--secondary)/20 ring-2 ring-inset ring-(--secondary)' : pick ? 'bg-(--background-secondary)' : ''}`}
                                >
                                    {pick ? (
                                        <div className="flex flex-col gap-0.5 min-w-0">
                                            <div className="flex items-center justify-between gap-1 text-(--text-tertiary)">
                                                <span className="tabular-nums">#{pick.overall_pick}</span>
                                                <span className="font-bold">{pickPositionLabel(pick)}</span>
                                            </div>
                                            <div className={`font-black text-(--text-primary) truncate ${sizing.name}`} title={pick.name}>
                                                {shortName(pick.name)}
                                            </div>
                                            <div className="text-(--text-secondary) tabular-nums truncate">
                                                {pick.points} pts{pick.team ? ` · ${pick.team}` : ''}
                                            </div>
                                        </div>
                                    ) : isLive ? (
                                        <div className="h-full flex items-center justify-center font-black italic text-(--secondary) animate-pulse">
                                            On the clock
                                        </div>
                                    ) : null}
                                </div>
                            );
                        })}
                    </div>
                ))}
            </div>
        </div>
    );
}

/** Same shape as the board while the first poll is in flight. */
export function DraftBoardSkeleton() {
    return (
        <div className="rounded-xl border border-(--divider) overflow-hidden animate-pulse">
            <div className="h-12 bg-(--background-secondary)" />
            {Array.from({ length: 6 }, (_, i) => (
                <div key={i} className="h-14 border-t border-(--divider) bg-(--background-primary)" />
            ))}
        </div>
    );
}
