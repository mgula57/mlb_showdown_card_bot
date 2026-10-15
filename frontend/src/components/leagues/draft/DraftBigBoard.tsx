import { useEffect, useMemo, useRef, useState } from 'react';
import { FaCompress, FaExpand, FaXmark } from 'react-icons/fa6';
import { TeamChip } from '../../shared/TeamChip';
import { fetchDraft, fetchLeague, type DraftPayload, type LeagueState } from '../../../api/leagues';
import { usePolling } from '../../../hooks/usePolling';
import { leagueTeamIdentity } from '../leagueUi';
import { DraftBoard } from './DraftBoard';
import { draftView } from './draftView';

const POLL_MS = 2000;
// ROUNDS SHOWN AT ONCE - A WINDOW AROUND THE CURRENT ROUND SO THE BOARD NEVER SCROLLS ON A TV
const VISIBLE_ROUNDS = 6;
const CONTROLS_HIDE_MS = 3000;

type Props = {
    leagueId: string;
    token: string;
    onExit: () => void;
};

/**
 * The draft on a TV: full screen, dark, read-only. A big on-the-clock banner and the latest pick
 * over a window of the board around the current round. Polls like the draft room; the only
 * controls (full screen, exit) fade out when the mouse is still.
 */
export function DraftBigBoard({ leagueId, token, onExit }: Props) {
    const rootRef = useRef<HTMLDivElement>(null);
    const [league, setLeague] = useState<LeagueState | null>(null);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [showControls, setShowControls] = useState(true);

    useEffect(() => {
        fetchLeague(token, leagueId).then(setLeague).catch(() => {});
    }, [leagueId, token]);

    // THE BOARD SHOWS THE LEAGUE'S CURRENT SEASON'S DRAFT
    const seasonNumber = league?.season?.season_number ?? null;
    const { data } = usePolling<DraftPayload | null>(
        () => (seasonNumber === null ? Promise.resolve(null) : fetchDraft(token, leagueId, seasonNumber)),
        seasonNumber === null ? null : POLL_MS,
        [leagueId, seasonNumber, token],
    );
    const draft = data?.draft ?? null;
    const view = useMemo(() => (draft ? draftView(draft, null) : null), [draft]);

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

            {/* Board */}
            <div className="flex-1 min-h-0">
                {draft && view ? (
                    <DraftBoard draft={draft} view={view} myMemberId={null} size="big" rounds={rounds} />
                ) : (
                    <div className="h-full rounded-[1.5vh] bg-(--background-secondary) animate-pulse" />
                )}
            </div>

            {/* Controls - fade when the mouse is still */}
            <div className={`fixed top-[2vh] right-[2vh] flex gap-2 transition-opacity duration-500 ${showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
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
