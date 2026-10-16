import { Fragment, useLayoutEffect, useRef, type ReactNode, type Ref } from 'react';
import { FaDisplay, FaRobot, FaSpinner, FaTrophy } from 'react-icons/fa6';
import { TeamChip } from '../../shared/TeamChip';
import type { DraftState, LeagueTeam } from '../../../api/leagues';
import { SECONDARY_BUTTON_CLASS, leagueTeamIdentity } from '../leagueUi';
import { shortName, type DraftView } from './draftView';

/** The draft page's sticky bar: back / league title on the left, then the live draft status. Fixed
 *  at h-14 so the team panel can pin flush beneath it (`top-14` in LeagueDraftRoom). */
export function DraftTopBar({ leading, children }: { leading: ReactNode; children?: ReactNode }) {
    return (
        <div className="sticky top-0 z-30 h-14 shrink-0 flex items-center gap-3 px-4 sm:px-6 border-b border-(--divider) bg-(--background-primary)/90 backdrop-blur">
            <div className="flex items-center gap-3 min-w-0 shrink">{leading}</div>
            {children && (
                <>
                    <div className="hidden sm:block h-8 w-px bg-(--divider) shrink-0" />
                    {children}
                </>
            )}
        </div>
    );
}

const PICK_STRIP_CLASS = 'flex items-center gap-1.5 shrink-0 h-10 px-4 sm:px-6 border-b border-(--divider)';

/** `DraftPickStrip` placeholder while the draft loads. */
export function DraftPickStripSkeleton() {
    return (
        <div className={PICK_STRIP_CLASS}>
            <div className="h-6 w-full rounded-lg bg-(--background-secondary) animate-pulse" />
        </div>
    );
}

/** Top-bar placeholder while the draft loads, sized like `DraftClock`. */
export function DraftClockSkeleton() {
    return <div className="flex-1 h-9 max-w-64 rounded-lg bg-(--background-secondary) animate-pulse" />;
}

type ClockProps = {
    draft: DraftState;
    view: DraftView;
    myMemberId: string | null;
    isCommissioner: boolean;
    autoPicking: boolean;
    onAutoPick: () => void;
    onOpenBigBoard: () => void;
};

/** Who's on the clock and the draft actions - lives in the top bar. */
export function DraftClock({ draft, view, myMemberId, isCommissioner, autoPicking, onAutoPick, onOpenBigBoard }: ClockProps) {
    const { onTheClock, isMyTurn, isComplete } = view;
    const picksUntilMine = myMemberId ? draft.upcoming.findIndex(p => p.member_id === myMemberId) : -1;
    const canAutoPick = !isComplete && (isMyTurn || isCommissioner);

    return (
        <div className="flex flex-1 items-center justify-between gap-3 min-w-0">
            {isComplete ? (
                <div className="flex items-center gap-2 text-[16px] font-black text-(--text-primary)">
                    <FaTrophy className="text-(--secondary)" /> Draft complete
                </div>
            ) : (
                <div className="flex flex-col min-w-0">
                    <div className="text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary) truncate">
                        On the clock · Pick {draft.next_pick} · Rd {draft.current_round}
                        {!isMyTurn && picksUntilMine > 0 && <span className="text-(--secondary)"> · You're up in {picksUntilMine}</span>}
                    </div>
                    <div className="flex items-center gap-2 min-w-0">
                        {onTheClock && <TeamChip team={leagueTeamIdentity(onTheClock)} size="sm" />}
                        <span className="text-[15px] font-black text-(--text-primary) truncate">
                            {isMyTurn ? 'Your pick!' : onTheClock?.display_name}
                        </span>
                    </div>
                </div>
            )}

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
    );
}

type StripPick = { overall_pick: number; round: number; member_id: string; name?: string; points?: number };

type StripProps = {
    draft: DraftState;
    view: DraftView;
    myMemberId: string | null;
};

/**
 * Every pick as one scrolling strip: made picks to the left (scroll back through them), the pick
 * on the clock, then the picks coming up. Opens parked on the last pick + the one on the clock.
 * A full-bleed band under the top bar, so chips scroll straight off the screen edges.
 */
export function DraftPickStrip({ draft, view, myMemberId }: StripProps) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const currentRef = useRef<HTMLDivElement>(null);
    const hasScrolled = useRef(false);
    const strip: StripPick[] = [...draft.picks, ...(view.isComplete ? [] : draft.upcoming)];

    useLayoutEffect(() => {
        const container = scrollRef.current;
        if (!container) return;
        // Keep the last pick in view just left of the one on the clock (or the end, once complete)
        const anchor = (currentRef.current?.previousElementSibling ?? currentRef.current) as HTMLElement | null;
        container.scrollTo({
            left: anchor ? anchor.offsetLeft - parseFloat(getComputedStyle(container).paddingLeft) : container.scrollWidth,
            behavior: hasScrolled.current ? 'smooth' : 'auto',
        });
        hasScrolled.current = true;
    }, [draft.next_pick, draft.picks.length]);

    if (!strip.length) return null;

    return (
        <div ref={scrollRef} className={`${PICK_STRIP_CLASS} relative overflow-x-auto scrollbar-hide`}>
            {strip.map((pick, index) => {
                const newRound = index === 0 || strip[index - 1].round !== pick.round;
                const isCurrent = pick.overall_pick === draft.next_pick;
                return (
                    <Fragment key={pick.overall_pick}>
                        {newRound && (
                            <span className="shrink-0 px-1 text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">Rd {pick.round}</span>
                        )}
                        <PickChip
                            ref={isCurrent ? currentRef : undefined}
                            pick={pick}
                            team={view.teamsByMember.get(pick.member_id)}
                            isMine={pick.member_id === myMemberId}
                            isCurrent={isCurrent}
                        />
                    </Fragment>
                );
            })}
        </div>
    );
}

function PickChip({ ref, pick, team, isMine, isCurrent }: {
    ref?: Ref<HTMLDivElement>;
    pick: StripPick;
    team?: LeagueTeam;
    isMine: boolean;
    isCurrent: boolean;
}) {
    const isMade = !!pick.name;
    const tone = isCurrent ? 'border-(--secondary) bg-(--secondary)/25 ring-1 ring-(--secondary)'
        : isMine ? 'border-(--secondary) bg-(--secondary)/15'
        : isMade ? 'border-(--divider) bg-(--background-secondary)'
        : 'border-(--divider) bg-(--background-primary)';
    return (
        <div
            ref={ref}
            title={isMade ? `#${pick.overall_pick} ${pick.name} · ${pick.points} pts` : undefined}
            className={`flex items-center gap-1.5 shrink-0 rounded-lg px-2 py-1 border text-[11px] ${tone}`}
        >
            <span className="tabular-nums text-(--text-tertiary)">#{pick.overall_pick}</span>
            {team && <TeamChip team={leagueTeamIdentity(team)} size="sm" />}
            {isMade && <span className="font-bold text-(--text-primary) whitespace-nowrap">{shortName(pick.name!)}</span>}
        </div>
    );
}
