/**
 * @fileoverview What fills the game board around the field: the wide board's score track (the
 * score, the inning and bases with the outs, and the linescore in one strip), and the last play in
 * words for the tab that grows out of the scoreboard. All read `GameView` or a `PlayEntry`, so a
 * live game, a sim and a replay frame match.
 */
import type { ReactNode } from "react";

import type { GameSide, GameView } from "../../domain/game";
import { advantageSideOf, type PlayEntry } from "../../domain/play";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { BOARD_OVERLAY_CLASS } from "./boardStyles";
import { ScoreSituation, TeamBadge } from "./detail/ScoreHeader";
import { PlayRolls } from "./RollMirrors";
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
        <div className={`${BOARD_OVERLAY_CLASS} flex items-center justify-between gap-4 px-3 py-1.5`}>
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
    const roll = play.roll;
    const text = (
        <p className={`line-clamp-2 text-center text-[12px] leading-snug text-(--text-primary) ${roll ? "last-play-text-in" : ""}`}>
            {play.event && <span className="font-semibold">{play.event}</span>}
            {description && description !== play.event && <span className="ml-1">{description}</span>}
        </p>
    );
    // A play the dice decided opens on its two rolls, and the play reads in a beat after.
    if (!roll || !roll.pitchRoll || !roll.swingRoll) return text;
    return (
        <div className="flex flex-col items-center gap-0.5">
            <PlayRolls playId={play.id} pitchRoll={roll.pitchRoll} advantage={advantageSideOf(play)} swingRoll={roll.swingRoll} swingResult={roll.swingResult} />
            {text}
        </div>
    );
}

/** A club's move, for its tab under the scoreboard (`TeamAnnouncement`): what kind of move in caps
 *  ("Pitching change", "Strategy card"), then the move itself. */
export function TeamMoveNote({ label, children }: { label: string; children: ReactNode }) {
    return (
        <div className="flex min-w-0 flex-col gap-0.5">
            <span className={`${CAPS_LABEL_CLASS} text-(--text-secondary)`}>{label}</span>
            <div className="min-w-0 text-[12px] leading-snug text-(--text-primary)">{children}</div>
        </div>
    );
}
