/**
 * @fileoverview The viewer's choice of matchup card on a live game's board: the full rendered card
 * (`LiveCardImagesProvider`, the default) or the compact `CardItem`. Remembered on this device.
 */
import { useState } from "react";

const VIEW_STORAGE_KEY = "liveGame.cardView";
export type LiveCardView = "item" | "image";

export function useLiveCardView(): [LiveCardView, (view: LiveCardView) => void] {
    const [view, setView] = useState<LiveCardView>(() => {
        try {
            return localStorage.getItem(VIEW_STORAGE_KEY) === "item" ? "item" : "image";
        } catch {
            return "image";
        }
    });
    const choose = (next: LiveCardView) => {
        setView(next);
        try {
            localStorage.setItem(VIEW_STORAGE_KEY, next);
        } catch {
            // Not remembered; the choice still holds for this visit
        }
    };
    return [view, choose];
}
