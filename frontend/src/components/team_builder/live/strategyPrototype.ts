/**
 * @fileoverview A stand-in for the strategy-card rules on the server, so the board's strategy UX
 * can be played with before the engine supports it. Dev only (`?strategy=1` on a live game).
 *
 * It runs both hands in the browser: this viewer's, and a pretend opponent's that plays a card now
 * and then. Windows follow the live game's own beats: "before the pitch" opens when the pitch is
 * next to roll, "after a result" when a play lands. "On a result" needs the server to hold the swing
 * result before applying it, so it never opens here. Card effects aren't applied; the cards are a
 * sample set written for the prototype, not the printed ones.
 *
 * Pure reducer, randomness from a seed (the game's id), so React can run it twice.
 */
import type { RollKind } from "../../../api/liveGame";
import {
    STRATEGY_DECK_SIZE, STRATEGY_OPENING_HAND, strategyBlocker,
    type PlayedStrategyCard, type StrategyCard, type StrategyTiming,
} from "../../../domain/strategy";

export type Seat = "me" | "them";
const other = (seat: Seat): Seat => (seat === "me" ? "them" : "me");

type SampleCard = Omit<StrategyCard, "id" | "cardId">;

const SAMPLE_CARDS: SampleCard[] = [
    { name: "Sit on It", kind: "offense", timing: "before_pitch", text: "+2 to the hitter's swing roll this at-bat." },
    { name: "Work the Count", kind: "offense", timing: "before_pitch", text: "If the pitcher has the advantage, the hitter rolls again. Keep the second roll." },
    { name: "Hot Bat", kind: "offense", timing: "before_pitch", text: "+1 to this hitter's on-base until the end of the inning.", staysInPlay: true },
    { name: "Extra Base", kind: "offense", timing: "after_result", text: "After a single or double, one runner advances one more base." },
    { name: "Green Light", kind: "offense", timing: "after_result", text: "After a single, the runner on first tries to steal second." },
    { name: "Find the Gap", kind: "offense", timing: "on_result", text: "On a single, roll. 16 or more: it's a double." },
    { name: "Paint the Corner", kind: "defense", timing: "before_pitch", text: "+2 to the pitch roll this at-bat." },
    { name: "Shift", kind: "defense", timing: "before_pitch", text: "-1 to the hitter's swing roll. A single to the infield becomes a ground out." },
    { name: "Mound Visit", kind: "defense", timing: "before_pitch", text: "The pitcher's fatigue goes back one inning." },
    { name: "Pickoff", kind: "defense", timing: "after_result", text: "Roll against the runner on first's speed. Win: he's out." },
    { name: "Diving Stop", kind: "defense", timing: "on_result", text: "On a single, make a fielding check. Pass: it's an out." },
    { name: "Strong Arm", kind: "defense", timing: "after_result", text: "A runner who advanced on this play has to beat the outfielder's arm." },
    { name: "Scouting Report", kind: "utility", timing: "before_pitch", text: "Draw a card." },
    { name: "Second Look", kind: "utility", timing: "after_result", text: "Draw two cards, then discard one." },
    { name: "Momentum", kind: "utility", timing: "after_result", text: "Your next card this inning can be played at any moment.", staysInPlay: true },
];

/** A small seeded random (mulberry32). */
function seededRandom(seed: number): () => number {
    let a = seed >>> 0;
    return () => {
        a = (a + 0x6d2b79f5) >>> 0;
        let t = a;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

const hashString = (text: string) => [...text].reduce((hash, char) => Math.imul(hash ^ char.charCodeAt(0), 16777619), 2166136261);

/** A full deck: four copies of each sample card, trimmed to `STRATEGY_DECK_SIZE` and shuffled. */
function sampleDeck(seat: Seat, seed: string): StrategyCard[] {
    const copies = SAMPLE_CARDS.flatMap((card, index) => Array.from({ length: 4 }, (_, copy) => ({
        ...card, cardId: `sample-${index}`, id: `${seat}-${index}-${copy}`,
    }))).slice(0, STRATEGY_DECK_SIZE);
    const random = seededRandom(hashString(`${seed}:${seat}`));
    for (let i = copies.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1));
        [copies[i], copies[j]] = [copies[j], copies[i]];
    }
    return copies;
}

/** The live game, boiled down to what the windows follow. */
export type StrategyInputs = {
    seed: string;
    /** Changes each half-inning, e.g. "3T". */
    half: string;
    /** Plays so far: a new one is a result landing. */
    playCount: number;
    pendingRoll: RollKind | null;
    /** This viewer's club is at the plate. */
    isBatting: boolean;
    isFinal: boolean;
};

export type StrategyWindow = {
    timing: StrategyTiming;
    key: string;
    turn: Seat;
    /** Passes in a row: two closes the window. */
    passes: number;
};

export type StrategyPrototypeState = {
    inputs: StrategyInputs | null;
    deck: Record<Seat, StrategyCard[]>;
    hand: Record<Seat, StrategyCard[]>;
    played: { card: StrategyCard; seat: Seat; isCarriedOver?: boolean }[];
    /** Every card played this game, oldest first, for the scoreboard to announce. */
    history: { card: StrategyCard; seat: Seat }[];
    window: StrategyWindow | null;
    /** Window keys already played out. */
    done: string[];
    isTrayOpen: boolean;
};

export const INITIAL_STRATEGY_STATE: StrategyPrototypeState = {
    inputs: null,
    deck: { me: [], them: [] },
    hand: { me: [], them: [] },
    played: [],
    history: [],
    window: null,
    done: [],
    isTrayOpen: false,
};

export type StrategyAction =
    | { type: "sync"; inputs: StrategyInputs }
    | { type: "play"; seat: Seat; cardId: string }
    | { type: "pass"; seat: Seat }
    | { type: "toggleTray"; isOpen?: boolean };

const isSeatBatting = (state: StrategyPrototypeState, seat: Seat) =>
    seat === "me" ? !!state.inputs?.isBatting : !state.inputs?.isBatting;

/** Why `seat` can't play `card` right now, or null when it can. */
export function blockerFor(state: StrategyPrototypeState, seat: Seat, card: StrategyCard): string | null {
    return strategyBlocker(card, {
        timing: state.window?.timing ?? null,
        isBatting: isSeatBatting(state, seat),
        playedNames: state.played.filter((entry) => !entry.isCarriedOver).map((entry) => entry.card.name),
    });
}

export const playableFor = (state: StrategyPrototypeState, seat: Seat) =>
    state.hand[seat].filter((card) => blockerFor(state, seat, card) === null);

function draw(state: StrategyPrototypeState, seat: Seat, count: number): StrategyPrototypeState {
    const drawn = state.deck[seat].slice(0, count);
    return {
        ...state,
        deck: { ...state.deck, [seat]: state.deck[seat].slice(drawn.length) },
        hand: { ...state.hand, [seat]: [...state.hand[seat], ...drawn] },
    };
}

/** While it's this viewer's call and nothing in hand can be played, pass for them, so a window
 *  only stops the game when there's a choice to make. With a choice, the hand opens. */
function settle(state: StrategyPrototypeState): StrategyPrototypeState {
    const window = state.window;
    if (!window || window.turn !== "me") return state;
    if (playableFor(state, "me").length > 0) return { ...state, isTrayOpen: true };
    return pass(state, "me");
}

function openWindow(state: StrategyPrototypeState, timing: StrategyTiming, key: string): StrategyPrototypeState {
    // The club in the field goes first.
    const turn: Seat = state.inputs?.isBatting ? "them" : "me";
    return settle({ ...state, window: { timing, key, turn, passes: 0 } });
}

/** Opens the next window the game has reached, if one hasn't been played out yet. */
function advance(state: StrategyPrototypeState): StrategyPrototypeState {
    const inputs = state.inputs;
    if (!inputs || inputs.isFinal || state.window || inputs.pendingRoll !== "pitch") return state;
    const key = `before:${inputs.playCount}`;
    if (state.done.includes(key)) return state;
    // A new at-bat: cards from the last one are discarded unless they stay in play.
    const played = state.played.filter((entry) => entry.card.staysInPlay).map((entry) => ({ ...entry, isCarriedOver: true }));
    return openWindow({ ...state, played }, "before_pitch", key);
}

function pass(state: StrategyPrototypeState, seat: Seat): StrategyPrototypeState {
    const window = state.window;
    if (!window || window.turn !== seat) return state;
    const passes = window.passes + 1;
    if (passes >= 2) {
        return advance({ ...state, window: null, done: [...state.done, window.key], isTrayOpen: false });
    }
    return settle({ ...state, window: { ...window, turn: other(seat), passes } });
}

function play(state: StrategyPrototypeState, seat: Seat, cardId: string): StrategyPrototypeState {
    const window = state.window;
    const card = state.hand[seat].find((entry) => entry.id === cardId);
    if (!window || window.turn !== seat || !card || blockerFor(state, seat, card) !== null) return state;
    return settle({
        ...state,
        hand: { ...state.hand, [seat]: state.hand[seat].filter((entry) => entry.id !== cardId) },
        played: [...state.played, { card, seat }],
        history: [...state.history, { card, seat }],
        window: { ...window, turn: other(seat), passes: 0 },
        isTrayOpen: seat === "me" ? false : state.isTrayOpen,
    });
}

function sync(state: StrategyPrototypeState, inputs: StrategyInputs): StrategyPrototypeState {
    const previous = state.inputs;
    let next: StrategyPrototypeState = { ...state, inputs };

    if (!previous) {
        next = { ...next, deck: { me: sampleDeck("me", inputs.seed), them: sampleDeck("them", inputs.seed) } };
        next = draw(draw(next, "me", STRATEGY_OPENING_HAND), "them", STRATEGY_OPENING_HAND);
    }

    // Each time a club comes to the plate, both managers draw. A new half also ends the inning's
    // carried-over cards.
    const isNewHalf = previous?.half !== inputs.half;
    if (isNewHalf) next = { ...draw(draw(next, "me", 1), "them", 1), played: [] };

    // A result landed mid-inning: the after-result window, before the next pitch.
    const hasResult = !!previous && inputs.playCount > previous.playCount;
    if (hasResult && !isNewHalf && !inputs.isFinal && !next.window) {
        const key = `after:${inputs.playCount}`;
        if (!next.done.includes(key)) return openWindow(next, "after_result", key);
    }
    return advance(next);
}

export function strategyReducer(state: StrategyPrototypeState, action: StrategyAction): StrategyPrototypeState {
    switch (action.type) {
        case "sync": return sync(state, action.inputs);
        case "play": return play(state, action.seat, action.cardId);
        case "pass": return pass(state, action.seat);
        case "toggleTray": return { ...state, isTrayOpen: action.isOpen ?? !state.isTrayOpen };
    }
}

/** The cards on the table as the board shows them: by the batting or the fielding club. */
export function playedForBoard(state: StrategyPrototypeState): Record<"batting" | "fielding", PlayedStrategyCard[]> {
    const byBatting = { batting: [] as PlayedStrategyCard[], fielding: [] as PlayedStrategyCard[] };
    for (const { card, seat, isCarriedOver } of state.played) {
        const by = isSeatBatting(state, seat) ? "batting" : "fielding";
        byBatting[by].push({ card, by, isCarriedOver });
    }
    return byBatting;
}

/** How often the pretend opponent plays a card it can. */
export const OPPONENT_PLAY_RATE = 0.4;
