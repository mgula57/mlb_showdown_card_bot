/**
 * @fileoverview What the scoreboard's island says while an at-bat waits on strategy cards: which
 * moment it is and whose call, with a Pass button when it's this player's. A card being played
 * drops from under its club's side of the scoreboard instead (`TeamAnnouncement`).
 */
import { STRATEGY_TIMING_LABEL, type StrategyTiming } from "../../../domain/strategy";
import { buttonClass } from "../../shared/buttonStyles";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";

type Props = {
    timing: StrategyTiming;
    /** Null while it's this player's call. */
    waitingOn: string | null;
    onPass?: () => void;
};

export default function StrategyWindowStatus({ timing, waitingOn, onPass }: Props) {
    return (
        <div className="flex items-center gap-2">
            <span className={`${CAPS_LABEL_CLASS} flex items-center gap-2 whitespace-nowrap text-(--text-primary)`}>
                {waitingOn && <span className="live-pulse h-2 w-2 shrink-0 rounded-full bg-(--live)" aria-hidden />}
                {STRATEGY_TIMING_LABEL[timing]} · {waitingOn ? `${waitingOn} deciding` : "your call"}
            </span>
            {!waitingOn && onPass && (
                <button type="button" onClick={onPass} className={buttonClass("secondary", "sm", "px-2! py-0.5! text-[11px]!")}>Pass</button>
            )}
        </div>
    );
}
