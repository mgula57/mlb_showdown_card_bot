import { useState } from "react";

import type { LiveGameState } from "../../../api/liveGame";
import { teamMovesBetween, type LiveTeamMove } from "./liveGameState";

/** Moves kept for the scoreboard: only the newest per club shows, so a few is plenty. */
const KEPT_MOVES = 8;

/** The substitutions each club has made since this page opened, oldest first, found by comparing
 *  each state the server sends with the one before it (`teamMovesBetween`). */
export function useLiveTeamMoves(state: LiveGameState | null): LiveTeamMove[] {
    const [track, setTrack] = useState<{ state: LiveGameState | null; moves: LiveTeamMove[] }>({ state, moves: [] });
    if (state && track.state?.seq !== state.seq) {
        const found = track.state ? teamMovesBetween(track.state, state) : [];
        setTrack({ state, moves: [...track.moves, ...found].slice(-KEPT_MOVES) });
    }
    return track.moves;
}
