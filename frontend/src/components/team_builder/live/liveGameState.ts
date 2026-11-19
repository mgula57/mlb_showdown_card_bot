/**
 * @fileoverview Reading a live game's state for the screen: whose turn it is, who's at the plate and
 * on the mound right now, and what a player's pending moves are.
 */
import type { LiveAction, LiveGame, LiveGameState, LiveSeat, LiveSide, RollKind } from "../../../api/liveGame";
import type { SimTimelineLiveEdge } from "../../../domain/adapters/fromSim";
import type { PlayerRef } from "../../../domain/game";
import type { PendingRunnerThrow } from "../../games/SimRunnerRolls";

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
    const pending = state.pending;
    // Past the pitch roll the matchup is locked in, whoever's up next by the lineup.
    const batter = pending?.hitter_id ?? state.sides[sides.batting].due_up_id;
    const awaiting = pending?.roll === "swing" || pending?.roll === "advance" ? pending.roll : null;
    return {
        inning: state.situation.inning,
        isTop: state.situation.is_top,
        batter: ref(state, batter),
        pitcher: ref(state, state.sides[sides.fielding].pitcher_id),
        playInProgress: state.play_in_progress && awaiting ? { entry: state.play_in_progress, awaiting } : undefined,
    };
}

/** The throw on a runner the game is waiting on (a steal, or a runner sent for an extra base), for
 *  the field to set out with its die. Undefined while it waits on the pitch or the swing. */
export function pendingThrowOf(state: LiveGameState): PendingRunnerThrow | undefined {
    const pending = state.pending;
    if (!pending || (pending.roll !== "steal" && pending.roll !== "advance") || !pending.runner_id || pending.base == null) return undefined;
    return {
        kind: pending.roll,
        runner: { id: pending.runner_id, name: pending.runner || state.player_names[pending.runner_id] || "" },
        base: pending.base,
        defense: pending.defense ?? undefined,
        target: pending.target ?? undefined,
    };
}

/** The seat this viewer acts for right now: the one being waited on if it's theirs, else their own
 *  (the away seat, for someone playing both). Null for a spectator. */
export function actingSide(game: LiveGame): LiveSide | null {
    if (game.my_sides.length === 0) return null;
    const pending = game.state?.pending?.side;
    return pending && game.my_sides.includes(pending) ? pending : game.my_sides[0];
}

/** True while the game waits on a roll this player makes: their own, or one for a side on autopilot
 *  (the sim's seat, or an idle player's), which any player in the game rolls. */
export const isMyTurn = (game: LiveGame) => {
    const pending = game.state?.pending?.side;
    if (!pending || game.my_sides.length === 0) return false;
    return game.my_sides.includes(pending) || isRollingFor(game);
};

/** True while this player rolls for a side that isn't theirs, one on autopilot. */
export function isRollingFor(game: LiveGame): boolean {
    const pending = game.state?.pending?.side;
    return !!pending && game.my_sides.length > 0 && !game.my_sides.includes(pending) && !!game.state?.sides[pending].autopilot;
}

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

/** The Manager panel's tabs. */
export type SubPickerMode = "pitcher" | "pinch";

/** Which move the Manager panel opens on: the one this club can make right now, a pitching change
 *  while it's in the field and a pinch hitter while it's at bat. */
export function defaultPickerMode(game: LiveGame): SubPickerMode {
    const side = actingSide(game);
    const inPlay = game.state ? sidesInPlay(game.state) : null;
    return side && inPlay?.fielding === side ? "pitcher" : "pinch";
}

export type LiveTurn = { label: string; isWaiting: boolean };

/** Each roll as a turn: "Your throw", "Waiting on the Yankees to throw". */
const TURN_VERB: Record<RollKind, string> = { pitch: "pitch", swing: "swing", steal: "throw", advance: "throw" };

/** What the next-move button says for each roll. */
export const ROLL_BUTTON_LABEL: Record<RollKind, string> = { pitch: "Pitch", swing: "Swing", steal: "Throw", advance: "Throw" };

/** Whose turn it is, in words, or null between turns (a roll still being played out). */
export function liveTurnLabel(game: LiveGame): LiveTurn | null {
    const pending = game.state && !game.state.is_final ? game.state.pending : null;
    if (!pending) return null;
    const verb = TURN_VERB[pending.roll];
    if (isRollingFor(game)) return { label: `Roll the ${verb} for ${teamName(game, pending.side)}`, isWaiting: false };
    if (isMyTurn(game)) return { label: `Your ${verb}`, isWaiting: false };
    return { label: `Waiting on ${teamName(game, pending.side)} to ${verb}`, isWaiting: true };
}

/** A club's substitution, read off the change between two states. `seq` is the state it showed up
 *  in, so the board can hold it until the field has caught up to that move. */
export type LiveTeamMove = { side: LiveSide; key: string; seq: number; label: string; text: string };

/** The substitutions each club made between `before` and `after`: a new pitcher on the mound, and
 *  anyone who took over a spot in the batting order (a pinch hitter while the club is at bat). */
export function teamMovesBetween(before: LiveGameState, after: LiveGameState): LiveTeamMove[] {
    const name = (id: string) => after.player_names[id] || before.player_names[id] || "Player";
    const batting = sidesInPlay(after)?.batting;
    const moves: LiveTeamMove[] = [];
    for (const side of LIVE_SIDES) {
        const was = before.sides[side];
        const now = after.sides[side];
        const move = (label: string, text: string, playerId: string) =>
            moves.push({ side, label, text, seq: after.seq, key: `${after.seq}:${side}:${playerId}` });

        if (was.pitcher_id && now.pitcher_id && was.pitcher_id !== now.pitcher_id) {
            move("Pitching change", `${name(now.pitcher_id)} in for ${name(was.pitcher_id)}`, now.pitcher_id);
        }
        now.lineup_ids.forEach((id, slot) => {
            const replaced = was.lineup_ids[slot];
            // A pitcher batting for himself moves with the pitching change above.
            if (!replaced || replaced === id || id === now.pitcher_id) return;
            move(side === batting ? "Pinch hitter" : "Substitution", `${name(id)} for ${name(replaced)}`, id);
        });
    }
    return moves;
}
