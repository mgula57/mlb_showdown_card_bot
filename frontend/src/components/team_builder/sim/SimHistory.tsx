import { useEffect, useMemo, useState } from 'react';
import { fetchSimHistory, type SimLeaderboardSort, type SimSeasonListItem } from '../../../api/sim';
import { SimSeasonRow, SimSeasonRowSkeleton } from './SimSeasonRow';

type Props = {
    token?: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
    /** Same sort as the leaderboard, so the two share one control instead of each needing its
     *  own — 'wins' orders each year's runs by best record, 'efficiency' by wins per roster
     *  point spent. Ties fall back to most recent first either way. */
    sort: SimLeaderboardSort;
};

/** Wins-per-1,000-roster-points, or 0 for a run with no recorded cost — mirrors the leaderboard's
 *  own efficiency ranking (`SimSeasonRow`'s `gmEfficiency`) so the two orderings agree. */
function efficiency(entry: SimSeasonListItem): number {
    return entry.roster_points && entry.roster_points > 0 ? entry.wins / entry.roster_points : 0;
}

function compareEntries(sort: SimLeaderboardSort) {
    return (a: SimSeasonListItem, b: SimSeasonListItem) => {
        const primary = sort === 'efficiency'
            ? efficiency(b) - efficiency(a) || b.wins - a.wins
            : b.wins - a.wins || b.win_pct - a.win_pct || Number(b.is_champion) - Number(a.is_champion);
        return primary || new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    };
}

/**
 * Every season the signed-in user has personally played, grouped by year (newest year first) and
 * ranked within each year by the shared sort — best record or best GM efficiency.
 *
 * Unlike the leaderboard this keeps every run rather than collapsing to a team's best — it's a
 * record of what you did, not a ranking against other players.
 */
export function SimHistory({ token, onOpenSeason, sort }: Props) {
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
        const compare = compareEntries(sort);
        return [...groups.entries()]
            .sort((a, b) => b[0] - a[0])
            .map(([year, entries]) => [year, [...entries].sort(compare)] as const);
    }, [seasons, sort]);

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
            <div className="flex flex-col gap-5 px-4">
                {[0, 1].map(i => (
                    <section key={i} className="flex flex-col gap-1.5">
                        <div className="h-3.5 w-16 rounded bg-(--background-tertiary) animate-pulse mb-1" />
                        {Array.from({ length: 3 }, (_, j) => <SimSeasonRowSkeleton key={j} />)}
                    </section>
                ))}
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
