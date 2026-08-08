import { useEffect, useMemo, useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { fetchSimLeaderboard, type SimLeaderboardSeason } from '../../../api/sim';
import { SimSeasonRow } from './SimSeasonRow';

type Props = {
    token?: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
};

/**
 * Season simulation results, grouped by season and ranked by wins — one row per team, its best
 * run at that season.
 *
 * Seasons the viewer has an entry in float to the top; everything else follows newest-first.
 * Only public teams appear to other users — the viewer's own private results are visible to
 * them alone, which is why a rank is "among entries you can see" rather than global.
 */
export function SimLeaderboard({ token, onOpenSeason }: Props) {
    const [seasons, setSeasons] = useState<SimLeaderboardSeason[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let stale = false;
        fetchSimLeaderboard(token)
            .then(data => { if (!stale) setSeasons(data); })
            .catch(err => { if (!stale) setError(err instanceof Error ? err.message : 'Failed to load leaderboard.'); });
        return () => { stale = true; };
    }, [token]);

    // Seasons you've played come first — "the seasons you're in" — then the rest, newest first.
    const ordered = useMemo(() => {
        if (!seasons) return [];
        return [...seasons].sort((a, b) => {
            if (a.has_own_entry !== b.has_own_entry) return a.has_own_entry ? -1 : 1;
            return b.year - a.year;
        });
    }, [seasons]);

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

    if (ordered.length === 0) {
        return (
            <p className="text-[13px] text-(--text-tertiary) py-8 text-center px-4">
                No seasons have been played yet. Open one of your teams and hit Play Season.
            </p>
        );
    }

    return (
        <div className="flex flex-col gap-5 px-4">
            {ordered.map(season => (
                <section key={season.year}>
                    <div className="flex items-baseline gap-2 mb-1.5">
                        <h2 className="text-[15px] font-black text-(--text-primary)">{season.year}</h2>
                        <span className="text-[11px] text-(--text-tertiary)">
                            {season.entries.length} {season.entries.length === 1 ? 'team' : 'teams'} played
                        </span>
                        {season.has_own_entry && (
                            <span className="text-[10px] font-bold text-(--showdown-blue) uppercase tracking-wide">You</span>
                        )}
                    </div>
                    <div className="flex flex-col gap-1.5">
                        {season.entries.map(entry => (
                            <SimSeasonRow
                                key={entry.entry_id}
                                entry={entry}
                                rank={entry.rank}
                                attempts={entry.attempts}
                                onOpen={() => entry.team_id && entry.job_id && onOpenSeason(entry.team_id, entry.job_id)}
                            />
                        ))}
                    </div>
                </section>
            ))}
        </div>
    );
}
