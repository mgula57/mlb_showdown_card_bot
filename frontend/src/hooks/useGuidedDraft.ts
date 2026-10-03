import { useState, useEffect, useMemo, useCallback } from 'react';
import { fetchGuidedRound } from '../api/userTeams';
import type { GuidedFillOrder, GuidedRound, TeamRosterSlot } from '../api/userTeams';

type Options = {
    /** Only fetch while the Guided tab is actually in use. */
    enabled: boolean;
    teamId?: string;
    token?: string;
    roster: TeamRosterSlot[];
    /** True once the local roster matches what's saved — the server plans the next round from
     *  the saved roster, so fetching any earlier would offer options for the previous round. */
    saved: boolean;
    /** Points budget for a team with no pts_limit; undefined = team has a limit (or none chosen yet). */
    ptsTarget?: number;
    /** False for a no-limit team until the drafter picks a target. */
    hasBudget: boolean;
    /** Changing it re-plans the current round. */
    order: GuidedFillOrder;
};

type Loaded =
    | { key: string; status: 'round'; round: GuidedRound }
    | { key: string; status: 'complete' }
    | { key: string; status: 'error'; message: string };

export type GuidedDraftState = {
    /** The current round, or null while it loads (or once the draft is complete). */
    round: GuidedRound | null;
    loading: boolean;
    complete: boolean;
    error: string | null;
    retry: () => void;
};

/**
 * Drives Guided Draft rounds: re-requests the next round whenever the saved roster changes.
 * Results are keyed by the roster they were planned against, so a pick immediately drops back
 * to the loading state until the next round for the new roster arrives.
 */
export function useGuidedDraft({ enabled, teamId, token, roster, saved, ptsTarget, hasBudget, order }: Options): GuidedDraftState {
    const rosterKey = useMemo(() => roster.map(s => s.card_id).sort().join(','), [roster]);
    const [loaded, setLoaded] = useState<Loaded | null>(null);
    const [retryNonce, setRetryNonce] = useState(0);
    const requestKey = `${rosterKey}|${ptsTarget ?? ''}|${order}|${retryNonce}`;

    useEffect(() => {
        if (!enabled || !saved || !hasBudget || !teamId || !token) return;
        if (loaded?.key === requestKey) return;
        const controller = new AbortController();
        fetchGuidedRound(teamId, token, { ptsTarget, order }, controller.signal)
            .then(res => setLoaded(res.complete
                ? { key: requestKey, status: 'complete' }
                : { key: requestKey, status: 'round', round: res }))
            .catch(err => {
                if (controller.signal.aborted) return;
                setLoaded({ key: requestKey, status: 'error', message: err instanceof Error ? err.message : 'Failed to load round' });
            });
        return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [enabled, saved, hasBudget, teamId, token, requestKey]);

    const retry = useCallback(() => setRetryNonce(n => n + 1), []);
    const current = loaded?.key === requestKey ? loaded : null;

    return {
        round: current?.status === 'round' ? current.round : null,
        loading: enabled && hasBudget && !current,
        complete: current?.status === 'complete',
        error: current?.status === 'error' ? current.message : null,
        retry,
    };
}
