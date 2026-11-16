/**
 * @fileoverview A manager's strategy hand on the game board. It's in the field's bottom-left
 * corner on every screen, opposite the player's own controls bottom right, and under the left thumb
 * on a phone:
 *  - `StrategyHandStack`: the hand put away, a fan of card backs with the count, dotted while a card
 *    can be played right now;
 *  - `StrategyHandTray`: the hand laid out, rising over the bottom of the field. Cards that can be
 *    played now sit raised and take a tap; the rest are dimmed with the reason they can't.
 */
import type { ReactNode } from "react";
import { FaChevronDown } from "react-icons/fa6";

import type { StrategyCard } from "../../../domain/strategy";
import { buttonClass } from "../../shared/buttonStyles";
import BoardCornerButton from "../BoardCornerButton";
import { CAPS_LABEL_CLASS } from "../../shared/fieldStyles";
import IconButton from "../../shared/IconButton";
import { StrategyCardFace } from "./StrategyCardFace";

/** The fan of card backs, by how many are drawn: up to three, however many are in the hand. */
const FAN: Record<number, string[]> = {
    1: ["rotate-0"],
    2: ["-rotate-6", "rotate-6"],
    3: ["-rotate-12", "rotate-0", "rotate-12"],
};

type StackProps = {
    count: number;
    /** Something in the hand can be played now. */
    hasPlayable: boolean;
    isOpen: boolean;
    onToggle: () => void;
};

/** A `BoardCornerButton`, like the Manager and next-move buttons across the field, so the two
 *  corners match. */
export function StrategyHandStack({ count, hasPlayable, isOpen, onToggle }: StackProps) {
    const fan = FAN[Math.min(count, 3)] ?? [];
    return (
        <BoardCornerButton
            icon={
                <span className="relative flex h-6 w-8 items-end justify-center">
                    {fan.length === 0 && <span className="h-5 w-3.5 rounded-plate border border-dashed border-(--rule-strong)" />}
                    {fan.map((rotation) => (
                        <span
                            key={rotation}
                            className={`absolute bottom-0 h-5 w-3.5 origin-bottom rounded-plate border border-(--background-secondary) bg-(--showdown-blue-fill) ${rotation}`}
                        />
                    ))}
                </span>
            }
            label={<span className="tabular-nums">{count}</span>}
            onClick={onToggle}
            isExpanded={isOpen}
            ariaLabel={`Strategy hand, ${count} ${count === 1 ? "card" : "cards"}${hasPlayable ? ", one can be played now" : ""}`}
            hasDot={hasPlayable}
        />
    );
}

type TrayProps = {
    hand: StrategyCard[];
    /** Why a card can't be played now, or null when it can (`strategyBlocker`). */
    blockerOf: (card: StrategyCard) => string | null;
    /** What the at-bat is waiting on, e.g. "Before the pitch · your call". */
    status?: ReactNode;
    onPlay: (card: StrategyCard) => void;
    /** Set while it's this manager's call: passing ends their turn at the moment without a card. */
    onPass?: () => void;
    onClose: () => void;
    /** A line under the cards. */
    note?: ReactNode;
};

export function StrategyHandTray({ hand, blockerOf, status, onPlay, onPass, onClose, note }: TrayProps) {
    return (
        <div className="strategy-tray-in rounded-t-card border border-b-0 border-(--divider) bg-(--background-primary) shadow-sheet">
            <div className="flex items-center gap-2 px-3 pb-1.5 pt-2">
                <span className={`${CAPS_LABEL_CLASS} shrink-0 text-(--text-primary)`}>Hand · {hand.length}</span>
                {status && <span className="min-w-0 truncate text-[12px] text-(--text-secondary)">{status}</span>}
                <div className="ml-auto flex shrink-0 items-center gap-2">
                    {onPass && <button type="button" onClick={onPass} className={buttonClass("primary", "sm")}>Pass</button>}
                    <IconButton icon={<FaChevronDown size={12} />} onClick={onClose} label="Put the hand away" />
                </div>
            </div>

            {hand.length === 0 ? (
                <p className="px-3 pb-3 text-[12px] text-(--text-secondary)">No cards in hand. You draw one each time a club comes to the plate.</p>
            ) : (
                // Top-aligned, so cards of different heights line up along their tops
                <div className="flex items-start gap-2 overflow-x-auto px-3 pb-3 pt-1 scrollbar-hide">
                    {hand.map((card) => {
                        const blocker = blockerOf(card);
                        return (
                            <button
                                key={card.id}
                                type="button"
                                disabled={blocker !== null}
                                onClick={() => onPlay(card)}
                                className={`
                                    shrink-0 rounded-card transition-[transform,opacity] duration-200
                                    ${blocker ? "cursor-not-allowed opacity-50" : "-translate-y-1 cursor-pointer shadow-raised hover:-translate-y-1.5"}
                                `}
                            >
                                <StrategyCardFace
                                    card={card}
                                    footer={
                                        <span className={`text-[10px] font-semibold ${blocker ? "text-(--text-tertiary)" : "text-(--green)"}`}>
                                            {blocker ?? "Tap to play"}
                                        </span>
                                    }
                                />
                            </button>
                        );
                    })}
                </div>
            )}

            {note && <div className="px-3 pb-2 text-[11px] text-(--text-tertiary)">{note}</div>}
        </div>
    );
}
