import { useEffect, useState } from 'react';
import { FaSpinner } from 'react-icons/fa6';
import { fetchSimHistory, fetchRecentSims as fetchRecentCommunitySims, type SimSeasonListItem } from '../../../api/sim';
import { SimSeasonRow } from './SimSeasonRow';

const RECENT_COUNT = 3;

type Props = {
    token?: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
};

/** One column of the Recent Sims section — a short list of seasons, or a placeholder note when
 *  there's nothing to show yet. */
function RecentSimsColumn({ title, seasons, loading, error, emptyNote, onOpenSeason }: {
    title: string;
    seasons: SimSeasonListItem[] | null;
    loading: boolean;
    error: string | null;
    emptyNote: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
}) {
    return (
        <div className="flex flex-col gap-2 min-w-0">
            <h4 className="text-[13px] font-black text-(--text-tertiary) uppercase tracking-wide">{title}</h4>
            {error ? (
                <p className="text-[12px] text-red-400 py-2">{error}</p>
            ) : loading ? (
                <div className="flex justify-center py-6">
                    <FaSpinner className="animate-spin text-(--text-tertiary)" />
                </div>
            ) : !seasons || seasons.length === 0 ? (
                <p className="text-[12px] text-(--text-tertiary) py-2">{emptyNote}</p>
            ) : (
                <div className="flex flex-col gap-1.5">
                    {seasons.slice(0, RECENT_COUNT).map(entry => (
                        <SimSeasonRow
                            key={entry.entry_id}
                            entry={entry}
                            showTime
                            onOpen={() => entry.team_id && entry.job_id && onOpenSeason(entry.team_id, entry.job_id)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

/**
 * A quick two-column snapshot of recent challenge activity: the signed-in user's own last few
 * completed challenge runs ("Mine") next to the community's most recent public challenge runs
 * ("Community"). Open-play (non-challenge) seasons are excluded — this is meant to surface
 * challenge activity specifically, not general sim history. Unlike `SimHistory`/`SimLeaderboard`
 * this isn't a full browsable list — just enough to show that challenges are being played, with
 * the full history/leaderboard a scroll away.
 */
export function RecentSims({ token, onOpenSeason }: Props) {
    const [mine, setMine] = useState<SimSeasonListItem[] | null>(null);
    const [mineError, setMineError] = useState<string | null>(null);
    const [community, setCommunity] = useState<SimSeasonListItem[] | null>(null);
    const [communityError, setCommunityError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) { setMine([]); return; }
        let stale = false;
        fetchSimHistory(token, undefined, true)
            .then(data => { if (!stale) setMine(data); })
            .catch(err => { if (!stale) setMineError(err instanceof Error ? err.message : 'Failed to load your simulations.'); });
        return () => { stale = true; };
    }, [token]);

    useEffect(() => {
        let stale = false;
        fetchRecentCommunitySims(token, RECENT_COUNT, true)
            .then(data => { if (!stale) setCommunity(data); })
            .catch(err => { if (!stale) setCommunityError(err instanceof Error ? err.message : 'Failed to load community simulations.'); });
        return () => { stale = true; };
    }, [token]);

    return (
        <div className="flex flex-col gap-3">
            <h3 className="text-[16px] font-black text-(--text-primary)">Recent Sims</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <RecentSimsColumn
                    title="Mine"
                    seasons={mine}
                    loading={mine === null && !mineError}
                    error={mineError}
                    emptyNote={token ? "You haven't completed a challenge yet." : 'Sign in to see your recent challenges.'}
                    onOpenSeason={onOpenSeason}
                />
                <RecentSimsColumn
                    title="Community"
                    seasons={community}
                    loading={community === null && !communityError}
                    error={communityError}
                    emptyNote="No community challenge runs yet."
                    onOpenSeason={onOpenSeason}
                />
            </div>
        </div>
    );
}
