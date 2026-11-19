/**
 * @fileoverview A live game's controls, each in the same area on every screen so the board reads
 * the same way everywhere:
 *  - whose turn it is grows out of the scoreboard when it changes (`LiveTurnStatus`, in the
 *    `ScoreboardIsland`);
 *  - the field's bottom-right corner holds this player's controls, thumb-sized on every board
 *    (`BoardCornerButton`): the Manager button, which opens this club's moves (`LiveSubPanel`), and
 *    the next-move button (`LiveActionButton`), which rolls the same die the field offers.
 */
import { FaClipboardList, FaDiceD20, FaForward } from "react-icons/fa6";

import type { LiveGame } from "../../../api/liveGame";
import BoardCornerButton from "../../games/BoardCornerButton";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";
import { InlineError } from "../../shared/InlineError";
import { actingSide, isMyTurn, ROLL_BUTTON_LABEL, type LiveTurn } from "./liveGameState";

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
export function ManagerButton({ game, onOpen }: { game: LiveGame; onOpen: () => void }) {
    const state = game.state;
    const side = actingSide(game);
    const mine = side && state && !state.is_final ? state.sides[side] : null;
    if (!mine) return null;

    const needsLook = mine.queued.length > 0 || mine.pitcher_is_tired || mine.pitcher_fatigue > 0;

    return (
        <BoardCornerButton
            icon={<FaClipboardList size={18} />}
            label="Manager"
            onClick={onOpen}
            ariaLabel={needsLook ? "Manager, something needs a look" : "Manager"}
            hasDot={needsLook}
        />
    );
}

type Props = {
    game: LiveGame;
    /** False while the last play is still animating: the next roll waits for it to finish. */
    isCaughtUp: boolean;
    isSubmitting: boolean;
    onRoll: () => void;
    /** Set while the at-bat waits on strategy cards: the button passes instead of rolling. */
    pass?: { isMyCall: boolean; onPass: () => void } | null;
};

/** The next-move button: thumb-sized, in the field's bottom-right corner on every board, and always
 *  there while this player has a seat. On their turn it rolls the pitch, the swing, or the throw on
 *  a runner stealing or sent for an extra base (the same die the field offers), and the same for a
 *  side on autopilot, the sim's seat included, so every die is thrown from a button; otherwise it
 *  says to wait, so the spot never jumps. */
export default function LiveActionButton({ game, isCaughtUp, isSubmitting, onRoll, pass }: Props) {
    const state = game.state;
    if (!state || state.is_final || !actingSide(game)) return null;

    if (pass) {
        return (
            <BoardCornerButton
                icon={<FaForward size={18} />}
                label={pass.isMyCall ? "Pass" : "Wait"}
                onClick={pass.onPass}
                variant={pass.isMyCall ? "primary" : "secondary"}
                disabled={!pass.isMyCall}
                ariaLabel={pass.isMyCall ? "Pass without playing a strategy card" : "Waiting on the other club's strategy card"}
            />
        );
    }

    const pending = state.pending;
    const canRoll = !!pending && isMyTurn(game);
    const label = canRoll ? ROLL_BUTTON_LABEL[pending.roll] : "Wait";

    return (
        <BoardCornerButton
            // Still while the roll is on its way: the die on the field is what moves
            icon={<FaDiceD20 size={20} />}
            label={label}
            onClick={onRoll}
            variant={canRoll ? "primary" : "secondary"}
            disabled={!canRoll || !isCaughtUp || isSubmitting}
            ariaLabel={canRoll ? `Roll ${pending.roll}` : "Waiting on the other club"}
        />
    );
}
