/**
 * @fileoverview Strategy cards, the expert game's second deck. Each manager holds a hand drawn from
 * their own deck and plays cards into an at-bat at three set moments (`StrategyTiming`): before the
 * pitch, on a result (after the swing roll, before the result is applied), and after a result. At
 * each moment the managers take turns playing or passing until both pass in a row. Offense cards are
 * played only while batting, defense cards only while in the field, utility cards either way, and no
 * two cards with the same name go into the same at-bat. Played cards are discarded at the end of the
 * at-bat unless they say they stay in play.
 *
 * Pure rules for the screen: which cards can be played right now and why the rest can't.
 */

export type StrategyKind = "offense" | "defense" | "utility";

export type StrategyTiming = "before_pitch" | "on_result" | "after_result";

export type StrategyCard = {
    /** This copy of the card. A deck can hold up to four copies of one card, so it isn't `cardId`. */
    id: string;
    /** The card itself, shared by its copies. */
    cardId: string;
    name: string;
    kind: StrategyKind;
    timing: StrategyTiming;
    text: string;
    /** Stays in play past the end of the at-bat, until the card's own text ends it. */
    staysInPlay?: boolean;
};

/** A card on the table: who played it, from the batting or the fielding club. */
export type PlayedStrategyCard = {
    card: StrategyCard;
    by: "batting" | "fielding";
    /** Still in play from an earlier at-bat. */
    isCarriedOver?: boolean;
};

export const STRATEGY_DECK_SIZE = 60;
export const STRATEGY_MAX_COPIES = 4;
export const STRATEGY_OPENING_HAND = 3;

export const STRATEGY_KIND_LABEL: Record<StrategyKind, string> = {
    offense: "Offense",
    defense: "Defense",
    utility: "Utility",
};

export const STRATEGY_TIMING_LABEL: Record<StrategyTiming, string> = {
    before_pitch: "Before the pitch",
    on_result: "On a result",
    after_result: "After a result",
};

type PlayContext = {
    /** The moment the at-bat is at, or null between moments. */
    timing: StrategyTiming | null;
    isBatting: boolean;
    /** Names already played into this at-bat, by either club. */
    playedNames: string[];
};

/** Why `card` can't be played right now, or null when it can. */
export function strategyBlocker(card: StrategyCard, { timing, isBatting, playedNames }: PlayContext): string | null {
    if (card.kind === "offense" && !isBatting) return "Offense only";
    if (card.kind === "defense" && isBatting) return "Defense only";
    if (timing !== card.timing) return `Plays ${STRATEGY_TIMING_LABEL[card.timing].toLowerCase()}`;
    if (playedNames.includes(card.name)) return "Already played this at-bat";
    return null;
}

export const playableStrategyCards = (hand: StrategyCard[], context: PlayContext) =>
    hand.filter((card) => strategyBlocker(card, context) === null);
