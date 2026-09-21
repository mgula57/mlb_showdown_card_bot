import { useEffect, useState } from 'react';
import { FaSpinner, FaTerminal } from 'react-icons/fa6';
import { Modal } from '../shared/Modal';
import { ordinal } from '../../functions/formatters';
import { fetchGameSimHistory, fetchGameSimResult, type SimGameRecord } from '../../api/simGame';

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

/** `created_at` comes back as a naive Postgres timestamp (no zone) - it's UTC on the wire, so a
 * bare `Date` parse would read it as local time and show the wrong hour. */
function formatCreatedAt(raw: string): string {
    const iso = raw.includes('T') ? raw : raw.replace(' ', 'T');
    const date = new Date(iso.endsWith('Z') ? iso : `${iso}Z`);
    if (Number.isNaN(date.getTime())) return raw;
    return date.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

type Props = {
    gamePk: number;
    onClose: () => void;
    /** The full stored record, `result` included - the caller drops it straight into the same
     * state a fresh sim would populate. */
    onSelect: (record: SimGameRecord) => void;
};

/** Lists every simulation previously run for this real game, newest first, and lets the user
 * reopen one instead of running a fresh sim. Sims of a game carry no private roster - both clubs
 * are real MLB teams - so this list (and loading any entry from it) needs no sign-in. */
export default function GameSimHistoryModal({ gamePk, onClose, onSelect }: Props) {
    const [games, setGames] = useState<SimGameRecord[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [loadingId, setLoadingId] = useState<string | null>(null);

    useEffect(() => {
        const controller = new AbortController();
        fetchGameSimHistory(gamePk)
            .then((rows) => { if (!controller.signal.aborted) setGames(rows); })
            .catch((err) => { if (!controller.signal.aborted) setError(errorMessage(err)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [gamePk]);

    async function handlePick(row: SimGameRecord) {
        setLoadingId(row.sim_id);
        setError(null);
        try {
            const full = await fetchGameSimResult(row.sim_id);
            onSelect(full);
        } catch (err) {
            setError(errorMessage(err));
            setLoadingId(null);
        }
    }

    return (
        <Modal title="Previous Simulations" size="sm" onClose={onClose}>
            <div className="max-h-[70vh] space-y-2 overflow-y-auto p-4">
                {loading && (
                    <div className="flex items-center justify-center gap-2 py-10 text-(--secondary)">
                        <FaSpinner className="animate-spin" /> Loading simulations…
                    </div>
                )}

                {error && (
                    <div className="rounded-lg border border-(--red)/30 bg-(--red)/5 px-3 py-2 text-[12px] text-(--red)">
                        {error}
                    </div>
                )}

                {!loading && games?.length === 0 && (
                    <div className="py-10 text-center text-xs text-(--secondary)">
                        No one has simulated this game yet.
                    </div>
                )}

                {games?.map((row) => (
                    <button
                        key={row.sim_id}
                        type="button"
                        onClick={() => handlePick(row)}
                        disabled={loadingId !== null}
                        className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-lg border border-(--divider) px-3 py-2.5 text-left transition-colors hover:bg-(--background-secondary) disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        <div className="min-w-0">
                            <div className="text-sm font-semibold text-(--primary)">
                                {row.away_abbr} {row.away_score} – {row.home_abbr} {row.home_score}
                            </div>
                            <div className="mt-0.5 text-[11px] text-(--secondary)">
                                {formatCreatedAt(row.created_at)}
                                {' · '}
                                {row.is_takeover ? `Took over in the ${ordinal(row.takeover_inning ?? 1)}` : 'Full game'}
                                {' · '}
                                {row.showdown_set}
                            </div>
                        </div>
                        {loadingId === row.sim_id ? (
                            <FaSpinner className="shrink-0 animate-spin text-(--secondary)" />
                        ) : (
                            <FaTerminal className="shrink-0 text-(--secondary)" />
                        )}
                    </button>
                ))}
            </div>
        </Modal>
    );
}
