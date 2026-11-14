/**
 * @fileoverview Reading a live game's state for the screen: whose turn it is, who's at the plate and
 * on the mound right now, and what a player's pending moves are.
 */
import type { LiveAction, LiveGame, LiveGameState, LiveSeat, LiveSide } from "../../../api/liveGame";
import type { SimTimelineLiveEdge } from "../../../domain/adapters/fromSim";
import type { PlayerRef } from "../../../domain/game";

export const LIVE_SIDES: LiveSide[] = ["away", "home"];
export const otherSide = (side: LiveSide): LiveSide => (side === "away" ? "home" : "away");

/** The club batting and the club in the field in the half-inning being played. */
export function sidesInPlay(state: LiveGameState): { batting: LiveSide; fielding: LiveSide } | null {
    if (!state.situation) return null;
    const batting: LiveSide = state.situation.is_top ? "away" : "home";
    return { batting, fielding: otherSide(batting) };
}

const ref = (state: LiveGameState, id?: string | null): PlayerRef | undefined =>
    id ? { id, name: state.player_names[id] ?? "" } : undefined;

/** Where the field stands now, for `fromSimTimeline`. Undefined once the game is final. */
export function liveEdgeOf(state: LiveGameState): SimTimelineLiveEdge | undefined {
    const sides = sidesInPlay(state);
    if (!sides || !state.situation || state.is_final) return undefined;
    const batter = state.pending?.roll === "swing" ? state.pending.hitter_id : state.sides[sides.batting].due_up_id;
    return {
        inning: state.situation.inning,
        isTop: state.situation.is_top,
        batter: ref(state, batter),
        pitcher: ref(state, state.sides[sides.fielding].pitcher_id),
    };
}

/** The seat this viewer acts for right now: the one being waited on if it's theirs, else their own
 *  (the away seat, for someone playing both). Null for a spectator. */
export function actingSide(game: LiveGame): LiveSide | null {
    if (game.my_sides.length === 0) return null;
    const pending = game.state?.pending?.side;
    return pending && game.my_sides.includes(pending) ? pending : game.my_sides[0];
}

export const isMyTurn = (game: LiveGame) => {
    const pending = game.state?.pending?.side;
    return !!pending && game.my_sides.includes(pending);
};

/** A seat's club by name, or what the seat is waiting for. */
export function seatName(seat: LiveSeat | undefined, side: LiveSide): string {
    if (seat?.identity?.name) return seat.identity.name;
    if (seat?.is_open) return "An opponent's team";
    return side === "away" ? "Away" : "Home";
}

export const teamName = (game: LiveGame, side: LiveSide) => seatName(game.seats[side], side);

/** A queued move in words, e.g. "Smith pinch hits for Jones" or "Rivera comes in to pitch". */
export function describeQueued(action: LiveAction, names: Record<string, string>): string {
    const name = (id?: string | null) => (id && names[id]) || "Player";
    if (action.kind === "pinch_hit") return `${name(action.player_id)} pinch hits for ${name(action.for_player_id)}`;
    if (action.kind === "pitching_change") return `${name(action.player_id)} comes in to pitch`;
    return "";
}
