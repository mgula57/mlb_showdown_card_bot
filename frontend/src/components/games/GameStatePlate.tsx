/**
 * @fileoverview A game's status as a plate: red LIVE (with the pulse dot) while in progress, ink
 * for Final, outline for anything else (scheduled times, Postponed, Delayed). Shared by the
 * schedule list (`GameItem`) and the game detail header (`ScoreHeader`) so the two read the same.
 */
import type { GameState } from "../../domain/game";
import { Plate, type PlateSize } from "../shared/Plate";

type GameStatePlateProps = {
    state: GameState;
    /** MLB's wording ("Final", "Postponed", "Delayed Start"); shown for every state but LIVE. */
    detailedState: string;
    /** Appended after LIVE, e.g. the inning ("Top 5th"). */
    liveDetail?: string;
    size?: PlateSize;
};

export function GameStatePlate({ state, detailedState, liveDetail, size = 'sm' }: GameStatePlateProps) {
    if (state === 'LIVE') {
        return (
            <Plate variant="red" size={size}>
                <span className="live-pulse w-1.5 h-1.5 rounded-full bg-white shrink-0" />
                LIVE
                {liveDetail && <span className="font-medium opacity-90">· {liveDetail}</span>}
            </Plate>
        );
    }
    return (
        <Plate variant={state === 'FINAL' ? 'ink' : 'outline'} size={size}>
            {detailedState}
        </Plate>
    );
}

export default GameStatePlate;
