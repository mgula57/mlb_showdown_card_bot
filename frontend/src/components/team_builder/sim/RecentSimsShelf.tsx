import { useEffect, useState } from 'react';
import { fetchSimHistory, type SimSeasonListItem } from '../../../api/sim';
import { SimSeasonRow } from './SimSeasonRow';

const RECENT_COUNT = 6;

type Props = {
    token: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
};

/**
 * Quick-access grid of the signed-in user's most recent team takeover sims, shown on the My Teams
 * tab so a returning user can jump back into a season without digging through Challenges or a
 * team's own Sims tab. Team-less open sims (played from the Seasons page) are excluded — those
 * don't resolve to a /teams/:teamId/sim/:jobId URL. Renders nothing until the fetch resolves with
 * at least one entry, so it never flashes an empty section.
 */
export function RecentSimsShelf({ token, onOpenSeason }: Props) {
    const [seasons, setSeasons] = useState<SimSeasonListItem[] | null>(null);

    useEffect(() => {
        let stale = false;
        fetchSimHistory(token, undefined, false, RECENT_COUNT)
            .then(data => { if (!stale) setSeasons(data.filter(entry => entry.team_id)); })
            .catch(() => { if (!stale) setSeasons([]); });
        return () => { stale = true; };
    }, [token]);

    if (!seasons || seasons.length === 0) return null;

    return (
        <div className="flex flex-col gap-2">
            <h3 className="text-[15px] font-black text-(--text-primary)">Recent Sims</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
                {seasons.map(entry => (
                    <SimSeasonRow
                        key={entry.entry_id}
                        entry={entry}
                        showTime
                        onOpen={() => entry.team_id && entry.job_id && onOpenSeason(entry.team_id, entry.job_id)}
                    />
                ))}
            </div>
        </div>
    );
}
