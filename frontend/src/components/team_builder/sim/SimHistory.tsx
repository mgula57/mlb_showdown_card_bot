import { useEffect, useMemo, useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { fetchSimHistory, type SimSeasonListItem } from '../../../api/sim';
import { SimSeasonRow } from './SimSeasonRow';

type Props = {
    token?: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
};

/**
 * Every season the signed-in user has personally played, most recent first, grouped by year.
 *
 * Unlike the leaderboard this keeps every run rather than collapsing to a team's best — it's a
 * record of what you did, not a ranking.
 */
export function SimHistory({ token, onOpenSeason }: Props) {
    const [seasons, setSeasons] = useState<SimSeasonListItem[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;
        let stale = false;
        fetchSimHistory(token)
            .then(data => { if (!stale) setSeasons(data); })
            .catch(err => { if (!stale) setError(err instanceof Error ? err.message : 'Failed to load your simulations.'); });
        return () => { stale = true; };
    }, [token]);

    const byYear = useMemo(() => {
        const groups = new Map<number, SimSeasonListItem[]>();
        for (const entry of seasons ?? []) {
            const group = groups.get(entry.year);
            if (group) group.push(entry);
            else groups.set(entry.year, [entry]);
        }
        return [...groups.entries()].sort((a, b) => b[0] - a[0]);
    }, [seasons]);

    if (!token) {
        return (
            <p className="text-[13px] text-(--text-tertiary) py-8 text-center px-4">
                Sign in to see the seasons you've played.
            </p>
        );
    }

    if (error) {
        return (
            <div className="mx-4 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                {error}
            </div>
        );
    }

    if (seasons === null) {
        return (
            <div className="flex justify-center py-12">
                <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
            </div>
        );
    }

    if (seasons.length === 0) {
        return (
            <p className="text-[13px] text-(--text-tertiary) py-8 text-center px-4">
                You haven't played a season yet. Open one of your teams and hit Play Season.
            </p>
        );
    }

    return (
        <div className="flex flex-col gap-5 px-4">
            {byYear.map(([year, entries]) => (
                <section key={year}>
                    <h2 className="text-[15px] font-black text-(--text-primary) mb-1.5">{year}</h2>
                    <div className="flex flex-col gap-1.5">
                        {entries.map(entry => (
                            <SimSeasonRow
                                key={entry.entry_id}
                                entry={entry}
                                showTime
                                onOpen={() => entry.team_id && entry.job_id && onOpenSeason(entry.team_id, entry.job_id)}
                            />
                        ))}
                    </div>
                </section>
            ))}
        </div>
    );
}
