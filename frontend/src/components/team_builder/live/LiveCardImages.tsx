/**
 * @fileoverview Full card images for a live game's matchup, for viewers who pick them over
 * `CardItem`s (`useLiveCardView`). Each card is rendered on the server the first time anyone asks
 * (a few seconds), so the provider asks for the pitcher and hitter at the plate and, ahead of time,
 * the hitter on deck, and preloads each image so the swap is instant when he steps in.
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { fetchLiveGameCardImage, type LiveCardImage } from "../../../api/liveGame";
import type { GameView } from "../../../domain/game";
import { resolveCardKey } from "../../../domain/players";
import { MatchupCardImagesContext, type MatchupCardImageLookup, type MatchupCardImageState } from "../../games/matchupCardImages";

/** One request per card per page load, shared by every render that asks for it. */
const imageRequests = new Map<string, Promise<LiveCardImage>>();

function requestCardImage(liveGameId: string, cardKey: string, token?: string): Promise<LiveCardImage> {
    const requestKey = `${liveGameId}|${cardKey}`;
    let request = imageRequests.get(requestKey);
    if (!request) {
        request = fetchLiveGameCardImage(liveGameId, cardKey, token).then((image) => {
            new Image().src = image.image_url;
            return image;
        });
        // A failure is retried the next time the card comes up
        request.catch(() => imageRequests.delete(requestKey));
        imageRequests.set(requestKey, request);
    }
    return request;
}

type Props = {
    liveGameId: string;
    token?: string;
    /** The game at the playback cursor: whose cards to show and who's next. */
    game: GameView;
    isEnabled: boolean;
    children: ReactNode;
};

export default function LiveCardImagesProvider({ liveGameId, token, game, isEnabled, children }: Props) {
    const [images, setImages] = useState<Record<string, MatchupCardImageState>>({});
    const situation = game.situation;
    const cardKeys = useMemo(
        () => [
            resolveCardKey(situation?.pitcher?.id, "P"),
            resolveCardKey(situation?.batter?.id, "H"),
            resolveCardKey(situation?.onDeck?.id, "H"),
        ].filter((key): key is string => !!key),
        [situation?.pitcher?.id, situation?.batter?.id, situation?.onDeck?.id],
    );

    useEffect(() => {
        if (!isEnabled) return;
        let isStale = false;
        for (const cardKey of cardKeys) {
            requestCardImage(liveGameId, cardKey, token)
                .then((image) => { if (!isStale) setImages((current) => ({ ...current, [cardKey]: { status: "ready", image } })); })
                .catch(() => { if (!isStale) setImages((current) => ({ ...current, [cardKey]: { status: "failed" } })); });
        }
        return () => { isStale = true; };
    }, [isEnabled, cardKeys, liveGameId, token]);

    // Anything not answered yet is on its way
    const lookup = useMemo<MatchupCardImageLookup | null>(
        () => (isEnabled ? (cardKey) => images[cardKey] ?? { status: "loading" } : null),
        [isEnabled, images],
    );

    return <MatchupCardImagesContext.Provider value={lookup}>{children}</MatchupCardImagesContext.Provider>;
}
