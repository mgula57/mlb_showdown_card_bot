/**
 * @fileoverview A live game's controls, each in the same area on every screen so the board reads
 * the same way everywhere:
 *  - whose turn it is grows out of the scoreboard when it changes (`LiveTurnStatus`, in the
 *    `ScoreboardIsland`);
 *  - the Manager button, which opens this club's moves (`LiveSubPanel`), sits top right;
 *  - the roll is the die on the field, and a narrow board adds a thumb-sized next-move button in
 *    the field's bottom-right corner (`LiveActionButton`).
 */
import { FaClipboardList, FaDiceD20 } from "react-icons/fa6";

import type { LiveGame } from "../../../api/liveGame";
import { buttonClass } from "../../shared/buttonStyles";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";
import { InlineError } from "../../shared/InlineError";
import { actingSide, isMyTurn, type LiveTurn } from "./liveGameState";

export type { SubPickerMode } from "./liveGameState";

/** What the scoreboard's island says during a live game: whose turn it is, and the last move's
 *  error. Null while there's nothing to say, which folds the island away. `turn` is
 *  `liveTurnLabel`, left out while a roll is still playing out on the field. */
export function LiveTurnStatus({ turn, moveError }: { turn: LiveTurn | null; moveError?: string | null }) {
    if (!turn && !moveError) return null;
    return (
        <div className="flex flex-col items-center gap-1">
            {turn && (
                <span className={`${CAPS_LABEL_CLASS} flex items-center gap-2 whitespace-nowrap text-(--text-primary)`}>
                    {turn.isWaiting && <span className="live-pulse h-2 w-2 shrink-0 rounded-full bg-(--live)" aria-hidden />}
                    {turn.label}
                </span>
            )}
            {moveError && <InlineError>{moveError}</InlineError>}
        </div>
    );
}

/** Opens this club's moves. Dotted while something needs a look: a move queued, or the pitcher
 *  tiring. Nothing shows for a spectator. */
export function ManagerButton({ game, onOpen, className = "" }: { game: LiveGame; onOpen: () => void; className?: string }) {
    const state = game.state;
    const side = actingSide(game);
    const mine = side && state && !state.is_final ? state.sides[side] : null;
    if (!mine) return null;

    const needsLook = mine.queued.length > 0 || mine.pitcher_is_tired || mine.pitcher_fatigue > 0;

    return (
        <button type="button" onClick={onOpen} className={buttonClass("secondary", "sm", `relative shrink-0 ${className}`)}>
            <FaClipboardList />
            Manager
            {needsLook && <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-(--live)" aria-label="Needs a look" />}
        </button>
    );
}

type Props = {
    game: LiveGame;
    /** False while the last play is still animating: the next roll waits for it to finish. */
    isCaughtUp: boolean;
    isSubmitting: boolean;
    onRoll: () => void;
};

/** A narrow board's next-move button: thumb-sized, in the field's bottom-right corner, and always
 *  there while this player has a seat. On their turn it rolls the pitch or swing (the same die the
 *  field offers); otherwise it says to wait, so the spot never jumps. */
export default function LiveActionButton({ game, isCaughtUp, isSubmitting, onRoll }: Props) {
    const state = game.state;
    if (!state || state.is_final || !actingSide(game)) return null;

    const pending = state.pending;
    const canRoll = !!pending && isMyTurn(game);
    const label = canRoll ? (pending.roll === "pitch" ? "Pitch" : "Swing") : "Wait";

    return (
        <button
            type="button"
            onClick={onRoll}
            disabled={!canRoll || !isCaughtUp || isSubmitting}
            aria-label={canRoll ? `Roll ${pending.roll}` : "Waiting on the other club"}
            className={buttonClass(canRoll ? "primary" : "secondary", "sm", "h-14 w-14 flex-col gap-0.5 p-0! text-[11px]! shadow-raised")}
        >
            <FaDiceD20 size={20} className={isSubmitting ? "animate-spin" : ""} />
            {label}
        </button>
    );
}
