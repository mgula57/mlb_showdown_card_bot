/**
 * @fileoverview Lets a game's host show the matchup as full rendered card images instead of
 * `CardItem`s. `MatchupSide` asks the context for each card by its card-map key; with no provider,
 * or no answer for a card, it shows the `CardItem` as usual.
 */
import { createContext } from "react";

import type { LiveCardImage } from "../../api/liveGame";

export type MatchupCardImageState =
    | { status: "loading" }
    | { status: "ready"; image: LiveCardImage }
    | { status: "failed" };

/** A card's image by its card-map key. Undefined means "show the `CardItem`". */
export type MatchupCardImageLookup = (cardKey: string) => MatchupCardImageState | undefined;

export const MatchupCardImagesContext = createContext<MatchupCardImageLookup | null>(null);
