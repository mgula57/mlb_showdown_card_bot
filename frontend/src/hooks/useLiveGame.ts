/**
 * @fileoverview Keeps one live game current and sends this player's moves.
 *
 * The server broadcasts each new `seq` on the Supabase Realtime channel `live-game:<id>`, and this
 * refetches on it. Polling backs it up: slowly while Realtime is connected, quickly while it isn't,
 * and not at all once the game is final. A poll sends the last `seq` seen, so an unchanged game
 * costs the server almost nothing.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { fetchLiveGame, LiveGameError, postLiveAction, type LiveAction, type LiveGame } from "../api/liveGame";
import { supabase } from "../api/supabase";

const POLL_MS_CONNECTED = 20_000;
const POLL_MS_DISCONNECTED = 4_000;

export type LiveGameControls = {
    game: LiveGame | null;
    loadError: string | null;
    /** The last move that didn't go through, cleared by the next one. */
    moveError: string | null;
    isSubmitting: boolean;
    submit: (action: LiveAction) => Promise<void>;
    refresh: () => Promise<void>;
};

export function useLiveGame(liveGameId: string, token?: string): LiveGameControls {
    const [game, setGame] = useState<LiveGame | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [moveError, setMoveError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const seqRef = useRef<number | undefined>(undefined);

    const apply = useCallback((next: LiveGame | null) => {
        if (!next) return;
        const nextSeq = next.state?.seq;
        // Responses can land out of order; never step back to an older game.
        if (nextSeq !== undefined && seqRef.current !== undefined && nextSeq < seqRef.current) return;
        seqRef.current = nextSeq;
        setGame(next);
    }, []);

    const refresh = useCallback(async () => {
        try {
            apply(await fetchLiveGame(liveGameId, token, seqRef.current));
            setLoadError(null);
        } catch (err) {
            setLoadError(err instanceof Error ? err.message : "Failed to load game.");
        }
    }, [liveGameId, token, apply]);

    useEffect(() => {
        seqRef.current = undefined;
        setGame(null);
        refresh();
    }, [refresh]);

    useEffect(() => {
        const channel = supabase
            .channel(`live-game:${liveGameId}`)
            .on("broadcast", { event: "seq" }, ({ payload }) => {
                if (typeof payload?.seq !== "number" || payload.seq !== seqRef.current) refresh();
            })
            .subscribe((status) => setIsConnected(status === "SUBSCRIBED"));
        return () => { supabase.removeChannel(channel); };
    }, [liveGameId, refresh]);

    const isFinal = game?.status === "final" || game?.status === "cancelled";
    useEffect(() => {
        if (isFinal) return;
        const timer = window.setInterval(refresh, isConnected ? POLL_MS_CONNECTED : POLL_MS_DISCONNECTED);
        return () => window.clearInterval(timer);
    }, [isFinal, isConnected, refresh]);

    const submit = useCallback(async (action: LiveAction) => {
        if (!token || seqRef.current === undefined) return;
        setIsSubmitting(true);
        setMoveError(null);
        try {
            apply(await postLiveAction(liveGameId, seqRef.current, action, token));
        } catch (err) {
            // Someone else's move landed first: catch up rather than calling it an error.
            if (err instanceof LiveGameError && err.status === 409) {
                await refresh();
            } else {
                setMoveError(err instanceof Error ? err.message : "That move didn't go through.");
            }
        } finally {
            setIsSubmitting(false);
        }
    }, [liveGameId, token, apply, refresh]);

    return { game, loadError, moveError, isSubmitting, submit, refresh };
}
