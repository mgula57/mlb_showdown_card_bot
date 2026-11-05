import { Fragment, useCallback, useLayoutEffect, useRef, useState, type ReactNode, type Ref } from 'react';
import { FaAnglesLeft, FaAnglesRight, FaDisplay, FaRobot, FaSpinner, FaTrophy } from 'react-icons/fa6';
import { TeamChip } from '../../shared/TeamChip';
import type { DraftState, LeagueTeam } from '../../../api/leagues';
import { leagueTeamIdentity } from '../leagueUi';
import { Heading } from '../../shared/Heading';
import { buttonClass } from '../../shared/buttonStyles';
import { CAPS_LABEL_CLASS } from '../../shared/fieldStyles';

const SECONDARY_SM = buttonClass('secondary', 'sm');
import { shortName, type DraftView } from './draftView';

/** The draft page's sticky bar: back / league title on the left, then the live draft status. Fixed
 *  at h-14 so the team panel can pin flush beneath it (`top-14` in LeagueDraftRoom). */
export function DraftTopBar({ leading, children }: { leading: ReactNode; children?: ReactNode }) {
    return (
        <div className="sticky top-0 z-30 h-14 shrink-0 flex items-center gap-3 px-4 sm:px-6 border-b border-(--divider) bg-(--background-primary)">
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

const PICK_STRIP_CLASS = 'flex items-center gap-1.5 shrink-0 h-11 px-4 sm:px-6 border-b border-(--divider)';

/** `DraftPickStrip` placeholder while the draft loads. */
export function DraftPickStripSkeleton() {
    return (
        <div className={PICK_STRIP_CLASS}>
            <div aria-hidden className="h-6 w-full rounded-plate bg-(--background-tertiary) animate-pulse" />
        </div>
    );
}

/** Top-bar placeholder while the draft loads, sized like `DraftClock`. */
export function DraftClockSkeleton() {
    return <div aria-hidden className="flex-1 h-9 max-w-64 rounded-plate bg-(--background-tertiary) animate-pulse" />;
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
                <Heading level="panel" as="div" className="flex items-center gap-2">
                    <FaTrophy className="text-(--gold)" /> Draft complete
                </Heading>
            ) : (
                <div className="flex flex-col min-w-0">
                    <div className={`${CAPS_LABEL_CLASS} text-(--text-tertiary) truncate`}>
                        On the clock · Pick {draft.next_pick} · Rd {draft.current_round}
                        {!isMyTurn && picksUntilMine > 0 && <span className="text-(--showdown-red)"> · You're up in {picksUntilMine}</span>}
                    </div>
                    <div className="flex items-center gap-2 min-w-0">
                        {onTheClock && <TeamChip team={leagueTeamIdentity(onTheClock)} size="sm" />}
                        <span className={`font-display-upright text-[17px] leading-none truncate ${isMyTurn ? 'text-(--showdown-red)' : 'text-(--text-primary)'}`}>
                            {isMyTurn ? 'Your pick' : onTheClock?.display_name}
                        </span>
                    </div>
                </div>
            )}

            <div className="flex items-center gap-2 shrink-0">
                {/* The Big Board is for a TV or monitor - not offered on phones */}
                <button type="button" onClick={onOpenBigBoard} className={`${SECONDARY_SM} max-md:hidden`}>
                    <FaDisplay /> Big Board
                </button>
                {canAutoPick && (
                    <button type="button" onClick={onAutoPick} disabled={autoPicking} className={SECONDARY_SM} title={isMyTurn ? 'Let the bot pick for you' : `Auto-pick for ${onTheClock?.display_name}`}>
                        {autoPicking ? <FaSpinner className="animate-spin" /> : <FaRobot />}
                        <span className="hidden sm:inline">Auto-pick</span>
                    </button>
                )}
            </div>
        </div>
    );
}

type StripPick = { overall_pick: number; round: number; member_id: string; name?: string; points?: number };
type PickKind = 'past' | 'current' | 'mine' | 'future';

type StripProps = {
    draft: DraftState;
    view: DraftView;
    myMemberId: string | null;
};

/**
 * Every pick as one scrolling strip: made picks to the left (scroll back through them), the pick
 * on the clock, then the picks coming up. Keeps the pick on the clock centered as the draft moves,
 * with a "Now" button to jump back once it's scrolled out of view.
 * A full-bleed band under the top bar, so chips scroll straight off the screen edges.
 */
export function DraftPickStrip({ draft, view, myMemberId }: StripProps) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const currentRef = useRef<HTMLDivElement>(null);
    const hasScrolled = useRef(false);
    // Which side the pick on the clock is off to, when it's scrolled out of view
    const [currentOffscreen, setCurrentOffscreen] = useState<'left' | 'right' | null>(null);
    const strip: StripPick[] = [...draft.picks, ...(view.isComplete ? [] : draft.upcoming)];

    const scrollToCurrent = useCallback((behavior: ScrollBehavior) => {
        const container = scrollRef.current;
        if (!container) return;
        const current = currentRef.current;
        // Center the pick on the clock (or the end, once complete)
        container.scrollTo({
            left: current ? current.offsetLeft - (container.clientWidth - current.offsetWidth) / 2 : container.scrollWidth,
            behavior,
        });
    }, []);

    const trackCurrent = useCallback(() => {
        const container = scrollRef.current;
        const current = currentRef.current;
        if (!container || !current) return setCurrentOffscreen(null);
        const left = current.offsetLeft - container.scrollLeft;
        setCurrentOffscreen(left + current.offsetWidth < 0 ? 'left' : left > container.clientWidth ? 'right' : null);
    }, []);

    useLayoutEffect(() => {
        scrollToCurrent(hasScrolled.current ? 'smooth' : 'auto');
        hasScrolled.current = true;
    }, [draft.next_pick, draft.picks.length, scrollToCurrent]);

    if (!strip.length) return null;

    return (
        <div className="relative shrink-0">
            <div ref={scrollRef} onScroll={trackCurrent} className={`${PICK_STRIP_CLASS} relative overflow-x-auto scrollbar-hide`}>
                {strip.map((pick, index) => {
                    const newRound = index === 0 || strip[index - 1].round !== pick.round;
                    const kind: PickKind = pick.name ? 'past'
                        : pick.overall_pick === draft.next_pick ? 'current'
                        : pick.member_id === myMemberId ? 'mine'
                        : 'future';
                    return (
                        <Fragment key={pick.overall_pick}>
                            {newRound && (
                                <span className={`shrink-0 px-1 ${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Rd {pick.round}</span>
                            )}
                            <PickChip
                                ref={kind === 'current' ? currentRef : undefined}
                                pick={pick}
                                team={view.teamsByMember.get(pick.member_id)}
                                kind={kind}
                                isMine={pick.member_id === myMemberId}
                            />
                        </Fragment>
                    );
                })}
            </div>
            {currentOffscreen && (
                <button
                    type="button"
                    onClick={() => scrollToCurrent('smooth')}
                    className={buttonClass('primary', 'sm', `absolute top-1/2 -translate-y-1/2 ${currentOffscreen === 'left' ? 'left-2' : 'right-2'} gap-1`)}
                >
                    {currentOffscreen === 'left' && <FaAnglesLeft />}
                    Now
                    {currentOffscreen === 'right' && <FaAnglesRight />}
                </button>
            )}
        </div>
    );
}

const PICK_CHIP_TONE: Record<PickKind, string> = {
    // Done - flat and faded, so the live end of the strip stands out
    past: 'border-transparent bg-(--background-secondary) opacity-60',
    current: 'border-transparent bg-(--showdown-blue-fill) text-white font-bold',
    // My upcoming picks - the red emphasis, so they read apart from the navy pick on the clock
    mine: 'border-(--showdown-red) bg-(--showdown-red)/10',
    // Not made yet - an outline only
    future: 'border-dashed border-(--divider)',
};

function PickChip({ ref, pick, team, kind, isMine }: {
    ref?: Ref<HTMLDivElement>;
    pick: StripPick;
    team?: LeagueTeam;
    kind: PickKind;
    isMine: boolean;
}) {
    return (
        <div
            ref={ref}
            title={pick.name ? `#${pick.overall_pick} ${pick.name} · ${pick.points} pts` : undefined}
            className={`flex items-center gap-1.5 shrink-0 rounded-control px-2 py-1 border text-[11px] ${PICK_CHIP_TONE[kind]}`}
        >
            {kind === 'current' && <span className="size-1.5 rounded-full bg-white animate-pulse" />}
            <span className={`tabular-nums ${kind === 'current' ? '' : 'text-(--text-tertiary)'}`}>#{pick.overall_pick}</span>
            {team && <TeamChip team={leagueTeamIdentity(team)} size="sm" />}
            {pick.name && <span className="font-bold text-(--text-primary) whitespace-nowrap">{shortName(pick.name)}</span>}
            {kind === 'current' && <span className={CAPS_LABEL_CLASS}>{isMine ? 'Your pick' : 'On the clock'}</span>}
            {kind === 'mine' && <span className={`${CAPS_LABEL_CLASS} text-(--showdown-red)`}>You</span>}
        </div>
    );
}
