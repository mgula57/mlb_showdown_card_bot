import { useEffect, useState } from 'react';
import { FaSpinner, FaTrophy } from 'react-icons/fa6';
import { fetchSimHistory, type SimSeasonListItem } from '../../api/sim';
import { relativeTime } from '../../functions/formatters';

const RECENT_LIMIT = 8;

type Props = {
    token?: string;
    onOpen: (jobId: string) => void;
};

/**
 * The signed-in user's own recent open sims (runs with no takeover team, i.e. `team_id === null`
 * on the shared `sim_season` row) — a takeover played from a built team already shows up in that
 * team's own Sims tab, so this stays scoped to the plain "simulate a season" path. Deliberately
 * minimal for now; can grow filters/grouping later if it gets used.
 */
export function RecentSims({ token, onOpen }: Props) {
    const [seasons, setSeasons] = useState<SimSeasonListItem[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;
        let stale = false;
        fetchSimHistory(token)
            .then(data => { if (!stale) setSeasons(data.filter(entry => entry.team_id === null)); })
            .catch(err => { if (!stale) setError(err instanceof Error ? err.message : 'Failed to load your simulations.'); });
        return () => { stale = true; };
    }, [token]);

    if (!token || error) {
        return error ? (
            <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                {error}
            </div>
        ) : null;
    }

    if (seasons === null) {
        return (
            <div className="flex justify-center py-8">
                <FaSpinner className="animate-spin text-(--text-tertiary) text-lg" />
            </div>
        );
    }

    if (seasons.length === 0) {
        return (
            <p className="text-[13px] text-(--text-tertiary) py-8 text-center px-4">
                You haven't simulated a season yet — hit Create to start one.
            </p>
        );
    }

    return (
        <div className="flex flex-col gap-1.5">
            {seasons.slice(0, RECENT_LIMIT).map(entry => (
                <button
                    key={entry.entry_id}
                    type="button"
                    onClick={() => entry.job_id && onOpen(entry.job_id)}
                    disabled={!entry.job_id}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors cursor-pointer hover:bg-(--divider) bg-(--background-tertiary) disabled:opacity-40 disabled:cursor-not-allowed"
                >
                    <span className="min-w-0 flex-1">
                        <span className="flex items-center gap-1.5">
                            <span className="text-[13px] font-bold text-(--text-primary)">{entry.year}</span>
                            {entry.replaced_abbr && (
                                <span className="text-[12px] text-(--text-secondary)">{entry.replaced_abbr}</span>
                            )}
                            {entry.is_champion && <FaTrophy className="text-[10px] text-yellow-300 shrink-0" title="Won the World Series" />}
                        </span>
                        <span className="block text-[11px] text-(--text-tertiary) truncate">
                            {entry.showdown_set ? `Set ${entry.showdown_set} · ` : ''}{relativeTime(entry.created_at)}
                        </span>
                    </span>
                    <span className="text-right shrink-0">
                        <span className="block text-[14px] font-black text-(--text-primary) tabular-nums">
                            {entry.wins}<span className="text-(--text-tertiary)">–</span>{entry.losses}
                        </span>
                    </span>
                </button>
            ))}
        </div>
    );
}
