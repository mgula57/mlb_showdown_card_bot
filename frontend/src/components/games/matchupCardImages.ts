/**
 * @fileoverview Lets a game's host show the matchup as full rendered card images instead of
 * `CardItem`s. `MatchupSide` asks the context for each card by its card-map key; with no provider,
 * or no answer for a card, it shows the `CardItem` as usual. The same answers give `GameStage`'s
 * card detail the image already on the board, so opening a card doesn't render it again.
 */
import { createContext } from "react";

import type { LiveCardImage } from "../../api/liveGame";
import type { ShowdownBotCardAPIResponse } from "../../api/showdownBotCard";
import { CARD_ASPECT } from "../cards/CardImageWithChart";

export type MatchupCardImageState =
    | { status: "loading" }
    | { status: "ready"; image: LiveCardImage }
    | { status: "failed" };

/** A card's image by its card-map key. Undefined means "show the `CardItem`". */
export type MatchupCardImageLookup = (cardKey: string) => MatchupCardImageState | undefined;

export const MatchupCardImagesContext = createContext<MatchupCardImageLookup | null>(null);

/** The tallest, in px, a card image in the matchup can stand while showing the whole card. Set by
 *  the wide board, where the corner cards share the stage's height with the field; null (a narrow
 *  board's scrolling column) means there's room for any. */
export const MatchupCardRoomContext = createContext<number | null>(null);

/** The narrowest a whole card image is shown. With less room it's a short window on one part of
 *  the card instead. */
const MIN_FULL_CARD_WIDTH = 200;

/** The width, in px, of a whole card image standing in `room` px of height (`MatchupCardRoomContext`),
 *  or null when that's too narrow to read and the card takes a short window instead. Infinity when
 *  the room is unlimited. */
export function fullCardWidthIn(room: number | null): number | null {
    if (room == null) return Infinity;
    const width = room * CARD_ASPECT;
    return width >= MIN_FULL_CARD_WIDTH ? width : null;
}

/** The card-map key of a card picked from the board (`onCardSelect` hands over the map's own
 *  object), so it can be looked up by key again. */
export function cardKeyOf(cardMap: Record<string, ShowdownBotCardAPIResponse>, card: ShowdownBotCardAPIResponse | null | undefined): string | undefined {
    if (!card) return undefined;
    return Object.keys(cardMap).find((key) => cardMap[key] === card);
}
