/**
 * @fileoverview A live game's controls, in the game board's `actions` zone where the transport strip
 * sits for a replay: whose turn it is, a full-width Roll button within thumb reach, and this club's
 * moves (a pitching change, a pinch hitter, autopilot). The same roll can be made from the die on the
 * field; this is the one that's always easy to reach on a phone.
 */
import { FaDiceD20, FaRobot } from "react-icons/fa6";

import type { LiveGame } from "../../../api/liveGame";
import { ordinal } from "../../../functions/formatters";
import { buttonClass } from "../../shared/buttonStyles";
import { choiceClass } from "../../shared/choiceStyles";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";
import { InlineError } from "../../shared/InlineError";
import { BOARD_PANEL_CLASS } from "../../games/boardStyles";
import { actingSide, describeQueued, isMyTurn, sidesInPlay, teamName } from "./liveGameState";

export type SubPickerMode = "pitcher" | "pinch";

type Props = {
    game: LiveGame;
    /** False while the last play is still animating: the next roll waits for it to finish. */
    isCaughtUp: boolean;
    isSubmitting: boolean;
    moveError: string | null;
    onRoll: () => void;
    onOpenPicker: (mode: SubPickerMode) => void;
    onToggleAutopilot: (enabled: boolean) => void;
};

export default function LiveTurnBar({ game, isCaughtUp, isSubmitting, moveError, onRoll, onOpenPicker, onToggleAutopilot }: Props) {
    const state = game.state;
    if (!state || state.is_final) return null;

    const pending = state.pending;
    const side = actingSide(game);
    const mine = side ? state.sides[side] : null;
    const myTurn = isMyTurn(game);
    const inPlay = sidesInPlay(state);
    const situation = state.situation;
    const where = situation ? `${situation.is_top ? "Top" : "Bot"} ${ordinal(situation.inning)}, ${situation.outs} out${situation.outs === 1 ? "" : "s"}` : "";

    const status = !pending
        ? "Playing…"
        : myTurn
            ? `Your ${pending.roll}`
            : `Waiting on ${teamName(game, pending.side)} to ${pending.roll === "pitch" ? "pitch" : "swing"}`;

    const isFielding = !!mine && inPlay?.fielding === side;
    const pitcherName = mine ? state.player_names[mine.pitcher_id] : undefined;
    const fatigueNote = mine && isFielding && (mine.pitcher_fatigue > 0
        ? `${pitcherName} is past his IP: −${mine.pitcher_fatigue} Control`
        : mine.pitcher_is_tired ? `${pitcherName} is tiring` : null);

    return (
        <div className={`${BOARD_PANEL_CLASS} flex flex-col gap-2 p-2.5`}>
            <div className="flex items-center justify-between gap-2">
                <span className={`${CAPS_LABEL_CLASS} truncate text-(--text-primary)`}>
                    {status}
                    {where && <span className="ml-2 text-(--text-primary) opacity-70">{where}</span>}
                </span>
                {!myTurn && pending && <span className="live-pulse h-2 w-2 shrink-0 rounded-full bg-(--live)" aria-hidden />}
            </div>

            {mine && myTurn && pending && (
                <button
                    type="button"
                    onClick={onRoll}
                    disabled={isSubmitting || !isCaughtUp}
                    className={buttonClass("primary", "lg", "w-full")}
                >
                    <FaDiceD20 className={isSubmitting ? "animate-spin" : ""} />
                    Roll {pending.roll}
                </button>
            )}

            {mine && (
                <div className="flex flex-wrap items-center gap-2">
                    <button
                        type="button"
                        onClick={() => onOpenPicker("pitcher")}
                        disabled={mine.available_reliever_ids.length === 0}
                        className={buttonClass("secondary", "sm")}
                    >
                        Pitching change
                    </button>
                    <button
                        type="button"
                        onClick={() => onOpenPicker("pinch")}
                        disabled={mine.bench_ids.length === 0}
                        className={buttonClass("secondary", "sm")}
                    >
                        Pinch hit
                    </button>
                    <button
                        type="button"
                        onClick={() => onToggleAutopilot(!mine.autopilot)}
                        disabled={isSubmitting}
                        aria-pressed={mine.autopilot}
                        title="Let the sim's manager roll and decide for your club until you switch it off"
                        className={choiceClass(mine.autopilot, "sm", "ml-auto")}
                    >
                        <FaRobot /> Autopilot {mine.autopilot ? "on" : "off"}
                    </button>
                </div>
            )}

            {fatigueNote && <p className="text-[11px] text-(--text-primary)">{fatigueNote}</p>}
            {mine && mine.queued.length > 0 && (
                <ul className="space-y-0.5 text-[11px] text-(--text-primary)">
                    {mine.queued.map((action, i) => <li key={i}>Up next: {describeQueued(action, state.player_names)}</li>)}
                </ul>
            )}
            {moveError && <InlineError>{moveError}</InlineError>}
        </div>
    );
}
