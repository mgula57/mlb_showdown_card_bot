/**
 * @fileoverview What fills the game board around the field: the wide board's score track (the
 * score, the inning and bases with the outs, and the linescore in one strip), and the last play in
 * words for the tab that grows out of the scoreboard. All read `GameView` or a `PlayEntry`, so a
 * live game, a sim and a replay frame match.
 */
import type { ReactNode } from "react";

import type { GameSide, GameView } from "../../domain/game";
import type { PlayEntry } from "../../domain/play";
import { BOARD_PANEL_CLASS } from "./boardStyles";
import { ScoreSituation, TeamBadge } from "./detail/ScoreHeader";
import GameLinescore from "./GameLinescore";

function TeamRuns({ side, reverse = false }: { side: GameSide; reverse?: boolean }) {
    return (
        <div className={`flex shrink-0 items-center gap-3 ${reverse ? "flex-row-reverse" : ""}`}>
            <TeamBadge team={side.team} className="h-11 w-11 text-base" />
            <span className="font-display-upright text-[40px] leading-none tabular-nums text-(--text-primary)">{side.score ?? 0}</span>
        </div>
    );
}

/** The score, the inning and bases with the outs, and the linescore as one strip along the board's
 *  top edge. `centerAction` stands in for the inning and bases once the game isn't in progress,
 *  e.g. the Recap / Field toggle. */
export function GameScoreTrack({ game, centerAction }: { game: GameView; centerAction?: ReactNode }) {
    return (
        <div className={`${BOARD_PANEL_CLASS} flex items-center justify-between gap-4 px-3 py-1.5`}>
            <TeamRuns side={game.away} />
            <ScoreSituation game={game} compact centerAction={centerAction} />
            <GameLinescore game={game} variant="track" className="min-w-0" />
            <TeamRuns side={game.home} reverse />
        </div>
    );
}

/** The last play in words, for the scoreboard's tab: the result in bold, then what happened. */
export function LastPlayLine({ play }: { play: PlayEntry }) {
    const description = play.description?.trim();
    if (!description && !play.event) return null;
    return (
        <p className="line-clamp-2 text-center text-[12px] leading-snug text-(--text-primary)">
            {play.event && <span className="font-semibold">{play.event}</span>}
            {description && description !== play.event && <span className="ml-1">{description}</span>}
        </p>
    );
}
