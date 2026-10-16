import { useEffect, useMemo, useRef, useState } from 'react';
import { FaBaseball, FaCompress, FaExpand, FaTableCells, FaXmark } from 'react-icons/fa6';
import { TeamChip } from '../../shared/TeamChip';
import { Tabs } from '../../shared/Tabs';
import { fetchLeague, type DraftState, type LeagueSettings, type LeagueState } from '../../../api/leagues';
import { useLeagueDraft } from '../../../hooks/useLeagueDraft';
import { useCardMap } from '../../../hooks/useCardMap';
import { CardSource } from '../../../types/cardSource';
import { leagueTeamIdentity } from '../leagueUi';
import { DraftBoard } from './DraftBoard';
import { DraftTeamFieldView, DraftTeamFieldViewSkeleton } from './DraftTeamFieldView';
import { DraftTeamSummary } from './DraftTeamSummary';
import { draftView, teamRoster, type DraftView } from './draftView';

// ROUNDS SHOWN AT ONCE - A WINDOW AROUND THE CURRENT ROUND SO THE BOARD NEVER SCROLLS ON A TV
const VISIBLE_ROUNDS = 6;
const CONTROLS_HIDE_MS = 3000;

type BigBoardView = 'board' | 'teams';

type Props = {
    leagueId: string;
    token: string;
    onExit: () => void;
};

/**
 * The draft on a TV: full screen, dark, read-only. A big on-the-clock banner and the latest pick
 * over a window of the board around the current round. Updates live like the draft room; the only
 * controls (full screen, exit) fade out when the mouse is still.
 */
export function DraftBigBoard({ leagueId, token, onExit }: Props) {
    const rootRef = useRef<HTMLDivElement>(null);
    const [league, setLeague] = useState<LeagueState | null>(null);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [showControls, setShowControls] = useState(true);
    const [boardView, setBoardView] = useState<BigBoardView>('board');

    useEffect(() => {
        fetchLeague(token, leagueId).then(setLeague).catch(() => {});
    }, [leagueId, token]);

    // THE BOARD SHOWS THE LEAGUE'S CURRENT SEASON'S DRAFT
    const seasonNumber = league?.season?.season_number ?? null;
    const { data } = useLeagueDraft(token, leagueId, seasonNumber);
    const draft = data?.draft ?? null;
    const view = useMemo(() => (draft ? draftView(draft, null) : null), [draft]);
    const settings = league?.league.settings ?? null;
    const pickSlots = useMemo(
        () => (draft?.picks ?? []).map(pick => ({ card_id: pick.release_card_id, card_source: CardSource.RELEASE })),
        [draft?.picks],
    );
    const { cardMap, loading: cardsLoading } = useCardMap(pickSlots, token);

    // Try for full screen right away (the Big Board button click still counts as the gesture)
    useEffect(() => {
        rootRef.current?.requestFullscreen?.().catch(() => {});
        const onChange = () => setIsFullscreen(document.fullscreenElement !== null);
        document.addEventListener('fullscreenchange', onChange);
        return () => {
            document.removeEventListener('fullscreenchange', onChange);
            if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
        };
    }, []);

    // Controls fade out when the mouse sits still
    useEffect(() => {
        let timer = window.setTimeout(() => setShowControls(false), CONTROLS_HIDE_MS);
        const onMove = () => {
            setShowControls(true);
            window.clearTimeout(timer);
            timer = window.setTimeout(() => setShowControls(false), CONTROLS_HIDE_MS);
        };
        window.addEventListener('mousemove', onMove);
        return () => {
            window.clearTimeout(timer);
            window.removeEventListener('mousemove', onMove);
        };
    }, []);


    const rounds = useMemo<[number, number] | undefined>(() => {
        if (!draft) return undefined;
        const current = draft.current_round ?? draft.rounds;
        const start = Math.max(1, Math.min(current - 1, draft.rounds - VISIBLE_ROUNDS + 1));
        return [start, Math.min(draft.rounds, start + VISIBLE_ROUNDS - 1)];
    }, [draft]);

    const lastPick = view?.lastPick ?? null;
    const lastPickTeam = lastPick ? view?.teamsByMember.get(lastPick.member_id) : null;

    return (
        <div ref={rootRef} className="dark fixed inset-0 z-[60] flex flex-col gap-[1.5vh] p-[2vh] bg-(--background-primary) text-(--text-primary) overflow-hidden">
            {/* Banner */}
            <div className="flex items-stretch gap-[1.5vw] shrink-0">
                <div className="flex-1 flex flex-col justify-center rounded-[1.5vh] border border-(--divider) bg-linear-to-br from-(--background-tertiary) to-(--background-secondary) px-[2vw] py-[1.5vh]">
                    <div className="text-[1.1vw] font-bold uppercase tracking-widest text-(--text-tertiary)">
                        {league?.league.name ?? 'League Draft'}
                        {draft && !view?.isComplete && ` · Pick ${draft.next_pick} of ${draft.total_picks} · Round ${draft.current_round}`}
                    </div>
                    {view?.isComplete ? (
                        <div className="text-[3.5vw] font-black">Draft complete</div>
                    ) : view?.onTheClock ? (
                        <div className="flex items-center gap-[1vw] min-w-0">
                            <span className="text-[1.6vw] font-black text-(--secondary) shrink-0">ON THE CLOCK</span>
                            <TeamChip team={leagueTeamIdentity(view.onTheClock)} />
                            <span className="text-[3.5vw] font-black truncate leading-tight">{view.onTheClock.display_name}</span>
                        </div>
                    ) : (
                        <div className="h-[5vh] w-1/2 rounded bg-(--background-primary) animate-pulse" />
                    )}
                </div>

                {lastPick && (
                    // KEYED BY PICK SO EACH NEW PICK REMOUNTS AND PLAYS THE ONE-SHOT FLASH
                    <div key={lastPick.overall_pick} className="league-new-pick w-[28vw] shrink-0 flex flex-col justify-center rounded-[1.5vh] border border-(--divider) bg-(--background-secondary) px-[1.5vw] py-[1.5vh]">
                        <div className="text-[1vw] font-bold uppercase tracking-widest text-(--text-tertiary)">Last pick · #{lastPick.overall_pick}</div>
                        <div className="text-[2.2vw] font-black truncate leading-tight">{lastPick.name}</div>
                        <div className="flex items-center gap-[0.6vw] text-[1.2vw] text-(--text-secondary)">
                            {lastPickTeam && <TeamChip team={leagueTeamIdentity(lastPickTeam)} />}
                            <span className="tabular-nums">{lastPick.points} pts</span>
                            {lastPick.roster_position && <span className="font-bold">{lastPick.roster_position}</span>}
                        </div>
                    </div>
                )}
            </div>

            {boardView === 'board' ? (
                <div className="flex-1 min-h-0 flex gap-[1.5vh]">
                    <div className="w-[20vw] shrink-0 overflow-y-auto scrollbar-hide">
                        {draft && view && settings
                            ? <TeamStandings draft={draft} view={view} settings={settings} />
                            : <div className="h-full rounded-[1.5vh] bg-(--background-secondary) animate-pulse" />}
                    </div>
                    <div className="flex-1 min-w-0 min-h-0">
                        {draft && view ? (
                            <DraftBoard draft={draft} view={view} myMemberId={null} size="big" rounds={rounds} />
                        ) : (
                            <div className="h-full rounded-[1.5vh] bg-(--background-secondary) animate-pulse" />
                        )}
                    </div>
                </div>
            ) : (
                <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide grid grid-cols-2 2xl:grid-cols-3 content-start gap-[1.5vh]">
                    {draft && view && settings
                        ? view.teams.map(team => (
                            <DraftTeamFieldView
                                key={team.member_id}
                                team={team}
                                picks={draft.picks}
                                settings={settings}
                                cards={cardMap}
                                isLoadingCards={cardsLoading}
                                isOnTheClock={draft.on_the_clock_member_id === team.member_id}
                            />
                        ))
                        : Array.from({ length: 4 }, (_, i) => <DraftTeamFieldViewSkeleton key={i} />)}
                </div>
            )}

            {/* Controls - fade when the mouse is still */}
            <div className={`fixed top-[2vh] right-[2vh] flex items-center gap-2 transition-opacity duration-500 ${showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
                <Tabs<BigBoardView>
                    tabs={[
                        { id: 'board', label: 'Board', icon: <FaTableCells /> },
                        { id: 'teams', label: 'Teams', icon: <FaBaseball /> },
                    ]}
                    value={boardView}
                    onChange={setBoardView}
                    size="sm"
                    className="rounded-lg bg-(--background-tertiary) px-1"
                />
                <button
                    type="button"
                    onClick={() => (isFullscreen ? document.exitFullscreen() : rootRef.current?.requestFullscreen())?.catch(() => {})}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-(--background-tertiary) text-[13px] font-bold cursor-pointer hover:opacity-90"
                >
                    {isFullscreen ? <FaCompress /> : <FaExpand />} {isFullscreen ? 'Exit full screen' : 'Full screen'}
                </button>
                <button type="button" onClick={onExit} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-(--background-tertiary) text-[13px] font-bold cursor-pointer hover:opacity-90">
                    <FaXmark /> Close
                </button>
            </div>
        </div>
    );
}

/** Every team in draft order with its points so far, beside the board. */
function TeamStandings({ draft, view, settings }: { draft: DraftState; view: DraftView; settings: LeagueSettings }) {
    return (
        <div className="flex flex-col gap-[1vh]">
            {view.teams.map(team => {
                const roster = teamRoster(draft.picks, team, settings);
                const isOnTheClock = draft.on_the_clock_member_id === team.member_id;
                return (
                    <div
                        key={team.member_id}
                        className={`rounded-[1.2vh] border px-3 py-2 bg-(--background-secondary) ${isOnTheClock ? 'border-(--secondary) ring-2 ring-(--secondary)' : 'border-(--divider)'}`}
                    >
                        <DraftTeamSummary team={team} points={roster.points} picksMade={roster.picksMade} settings={settings} isOnTheClock={isOnTheClock} />
                    </div>
                );
            })}
        </div>
    );
}
