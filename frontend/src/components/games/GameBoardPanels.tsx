/**
 * @fileoverview What fills the wide game board's zones: the score and inning track, the game state
 * with its outs and count, who's due up, and the situation in words. All read `GameView`, so a live
 * game, a sim and a replay frame match.
 */
import type { ReactNode } from "react";

import type { GameSide, GameView, LiveSituation } from "../../domain/game";
import { situationHeadline } from "../../domain/gameSummary";
import type { PlayEntry } from "../../domain/play";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { Heading } from "../shared/Heading";
import { BOARD_PANEL_CLASS } from "./boardStyles";
import { TeamBadge } from "./detail/ScoreHeader";
import GameLinescore from "./GameLinescore";
import { GameStatePlate } from "./GameStatePlate";

function TeamRuns({ side, reverse = false }: { side: GameSide; reverse?: boolean }) {
    return (
        <div className={`flex shrink-0 items-center gap-3 ${reverse ? "flex-row-reverse" : ""}`}>
            <TeamBadge team={side.team} className="h-11 w-11 text-base" />
            <span className="font-display-upright text-[40px] leading-none tabular-nums text-(--text-primary)">{side.score ?? 0}</span>
        </div>
    );
}

/** The score and the linescore as one strip along the board's top edge. */
export function GameScoreTrack({ game }: { game: GameView }) {
    return (
        <div className={`${BOARD_PANEL_CLASS} flex items-center justify-between gap-3 px-3 py-1.5`}>
            <TeamRuns side={game.away} />
            <GameLinescore game={game} variant="track" className="min-w-0" />
            <TeamRuns side={game.home} reverse />
        </div>
    );
}

function PegRow({ label, filled, total, fillClass }: { label: string; filled: number; total: number; fillClass: string }) {
    return (
        <div className="flex items-center justify-between gap-3" aria-label={`${label}: ${filled}`}>
            <span className={`${CAPS_LABEL_CLASS} text-(--text-primary)`}>{label}</span>
            <span className="flex gap-1">
                {Array.from({ length: total }, (_, peg) => (
                    <span key={peg} className={`h-3 w-3 rounded-full border border-(--text-primary)/50 ${peg < filled ? fillClass : ""}`} />
                ))}
            </span>
        </div>
    );
}

/** Game state over the outs and, on an MLB feed, the count. A sim has no ball or strike state. */
export function BoardStatePanel({ game, action, children }: {
    game: GameView;
    /** Under the state once the game isn't in progress, e.g. the Recap / Field toggle. */
    action?: ReactNode;
    /** Below the pegs, e.g. the defense summary. */
    children?: ReactNode;
}) {
    const situation = game.situation;
    const isInProgress = game.state === "LIVE";
    const inning = situation?.inningLabel ? `${situation.isTop ? "Top" : "Bot"} ${situation.inningLabel}` : undefined;
    const hasCount = situation?.balls != null && situation.strikes != null;

    return (
        <div className={`${BOARD_PANEL_CLASS} flex flex-col items-start gap-2 p-3`}>
            <GameStatePlate state={game.state} detailedState={game.detailedState} liveDetail={inning} size="md" />
            {!isInProgress && action}
            {isInProgress && situation && (
                <div className="w-full space-y-1.5">
                    <PegRow label="Outs" filled={situation.outs} total={3} fillClass="border-(--live) bg-(--live)" />
                    {hasCount && (
                        <>
                            <PegRow label="Balls" filled={situation.balls ?? 0} total={4} fillClass="border-(--green) bg-(--green)" />
                            <PegRow label="Strikes" filled={situation.strikes ?? 0} total={3} fillClass="border-(--warning) bg-(--warning)" />
                        </>
                    )}
                </div>
            )}
            {children}
        </div>
    );
}

export function DueUpPanel({ situation }: { situation?: LiveSituation }) {
    if (!situation?.onDeck && !situation?.inHole) return null;
    const rows = [["On deck", situation.onDeck], ["In hole", situation.inHole]] as const;

    return (
        <div className={`${BOARD_PANEL_CLASS} space-y-1.5 p-3 text-[12px]`}>
            <div className={`${CAPS_LABEL_CLASS} text-(--text-primary)`}>Due up</div>
            {rows.map(([label, player]) => player && (
                <div key={label} className="flex items-baseline justify-between gap-2">
                    <span className="shrink-0 text-(--text-primary)">{label}</span>
                    <span className="truncate font-semibold text-(--text-primary)">{player.name}</span>
                </div>
            ))}
        </div>
    );
}

/** The situation in words over the last play. */
export function SituationPanel({ game, lastPlay }: { game: GameView; lastPlay?: PlayEntry }) {
    const headline = game.state === "LIVE" && game.situation ? situationHeadline(game.situation) : undefined;
    const description = lastPlay?.description?.trim() || lastPlay?.event;
    if (!headline && !description) return null;

    return (
        <div className={`${BOARD_PANEL_CLASS} flex min-h-30 flex-col justify-center gap-1.5 p-3 @[62rem]:h-37.5`}>
            {headline && <Heading level="section" as="div">{headline}</Heading>}
            {description && <p className="line-clamp-3 text-[13px] leading-snug text-(--text-primary)">{description}</p>}
        </div>
    );
}
