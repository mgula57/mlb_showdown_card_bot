/**
 * @fileoverview Puts the strategy-card prototype (`strategyPrototype.ts`) on a live game's board.
 * A render prop, so the live page can hand what it returns straight to `GameStage`: the hand, its
 * tray and the played cards (`slots`), what the island says during a window, and whether the roll
 * is held for one. Off, it hands back nothing and the game plays as before.
 */
import { useEffect, useReducer, type ReactNode } from "react";

import type { LiveGame } from "../../../api/liveGame";
import { TeamMoveNote } from "../../games/GameBoardPanels";
import type { TeamAnnouncement, TeamStatus } from "../../games/ScoreboardIsland";
import PlayedStrategyCards from "../../games/strategy/PlayedStrategyCards";
import { StrategyCardFace } from "../../games/strategy/StrategyCardFace";
import { StrategyHandStack, StrategyHandTray } from "../../games/strategy/StrategyHand";
import StrategyWindowStatus from "../../games/strategy/StrategyWindowStatus";
import type { StrategyBoardSlots } from "../../games/strategy/strategyBoard";
import { otherSide, sidesInPlay, teamName } from "./liveGameState";
import {
    blockerFor, INITIAL_STRATEGY_STATE, OPPONENT_PLAY_RATE, playableFor, playedForBoard, strategyReducer,
    type StrategyInputs,
} from "./strategyPrototype";

/** How long the pretend opponent takes to decide. */
const OPPONENT_THINK_MS = 900;

export type LiveStrategy = {
    slots?: StrategyBoardSlots;
    /** What the island says while a window is open. */
    island: TeamStatus | null;
    /** The at-bat waits on strategy cards: no roll until both managers pass. */
    isHoldingRoll: boolean;
    /** The next-move button's job while the roll is held. */
    pass: { isMyCall: boolean; onPass: () => void } | null;
    /** Each card as it's played, dropped from under the club's side of the scoreboard. */
    announcements: TeamAnnouncement[];
};

const OFF: LiveStrategy = { island: null, isHoldingRoll: false, pass: null, announcements: [] };

function inputsOf(game: LiveGame): StrategyInputs | null {
    const state = game.state;
    const mySide = game.my_sides[0];
    const sides = state ? sidesInPlay(state) : null;
    if (!state || !mySide || !sides || !state.situation) return null;
    return {
        seed: game.live_game_id,
        half: `${state.situation.inning}${state.situation.is_top ? "T" : "B"}`,
        playCount: state.game.log.length,
        pendingRoll: state.pending?.roll ?? null,
        isBatting: sides.batting === mySide,
        isFinal: state.is_final,
    };
}

const sameInputs = (a: StrategyInputs | null, b: StrategyInputs | null) =>
    !!a && !!b && a.half === b.half && a.playCount === b.playCount && a.pendingRoll === b.pendingRoll
    && a.isBatting === b.isBatting && a.isFinal === b.isFinal;

type Props = {
    game: LiveGame;
    isEnabled: boolean;
    /** False while the last play is still playing out on the field: windows wait for it. */
    isCaughtUp: boolean;
    children: (strategy: LiveStrategy) => ReactNode;
};

export default function LiveStrategyPrototype({ game, isEnabled, isCaughtUp, children }: Props) {
    const [state, dispatch] = useReducer(strategyReducer, INITIAL_STRATEGY_STATE);

    // Follows the game as it's played, once each roll has finished on the field.
    const inputs = isEnabled ? inputsOf(game) : null;
    if (inputs && isCaughtUp && !sameInputs(inputs, state.inputs)) dispatch({ type: "sync", inputs });

    const activeWindow = isEnabled && isCaughtUp ? state.window : null;

    // The pretend opponent takes its turn after a beat: a card now and then, otherwise a pass.
    useEffect(() => {
        if (activeWindow?.turn !== "them") return;
        const timer = setTimeout(() => {
            const options = playableFor(state, "them");
            if (options.length > 0 && Math.random() < OPPONENT_PLAY_RATE) {
                dispatch({ type: "play", seat: "them", cardId: options[Math.floor(Math.random() * options.length)].id });
            } else {
                dispatch({ type: "pass", seat: "them" });
            }
        }, OPPONENT_THINK_MS);
        return () => clearTimeout(timer);
    }, [activeWindow, state]);

    if (!inputs || !state.inputs || inputs.isFinal) return children(OFF);

    const mySide = game.my_sides[0];
    const opponent = teamName(game, otherSide(mySide));
    const isMyCall = activeWindow?.turn === "me";
    const onPass = () => dispatch({ type: "pass", seat: "me" });
    const blockerOf = (card: Parameters<typeof blockerFor>[2]) => blockerFor(state, "me", card);
    const hasPlayable = !!activeWindow && state.hand.me.some((card) => blockerOf(card) === null);
    const played = playedForBoard(state);
    const status = activeWindow && (isMyCall ? "Your call" : `${opponent} deciding…`);

    return children({
        slots: {
            hand: (
                <StrategyHandStack
                    count={state.hand.me.length}
                    hasPlayable={hasPlayable && isMyCall}
                    isOpen={state.isTrayOpen}
                    onToggle={() => dispatch({ type: "toggleTray" })}
                />
            ),
            tray: state.isTrayOpen && (
                <StrategyHandTray
                    hand={state.hand.me}
                    blockerOf={blockerOf}
                    status={status}
                    onPlay={(card) => dispatch({ type: "play", seat: "me", cardId: card.id })}
                    onPass={isMyCall ? onPass : undefined}
                    onClose={() => dispatch({ type: "toggleTray", isOpen: false })}
                    note="Prototype: sample cards, and their effects aren't applied yet."
                />
            ),
            played: {
                pitcher: <PlayedStrategyCards cards={played.fielding} />,
                hitter: <PlayedStrategyCards cards={played.batting} />,
            },
        },
        island: activeWindow ? {
            side: isMyCall ? mySide : otherSide(mySide),
            key: `${activeWindow.key}|${activeWindow.turn}`,
            content: (
                <StrategyWindowStatus
                    timing={activeWindow.timing}
                    waitingOn={isMyCall ? null : opponent}
                    onPass={onPass}
                />
            ),
        } : null,
        announcements: state.history.map(({ card, seat }) => ({
            side: seat === "me" ? mySide : otherSide(mySide),
            key: card.id,
            content: (
                <TeamMoveNote label="Strategy card">
                    <StrategyCardFace card={card} size="mini" />
                </TeamMoveNote>
            ),
        })),
        isHoldingRoll: !!state.window,
        pass: state.window ? { isMyCall, onPass } : null,
    });
}
