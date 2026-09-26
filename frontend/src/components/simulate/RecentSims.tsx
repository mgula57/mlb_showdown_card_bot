import { useEffect, useMemo, useState } from 'react';
import { fetchSimHistory, type SimSeasonListItem } from '../../api/sim';
import { SimSeasonRow, SimSeasonRowSkeleton } from '../team_builder/sim/SimSeasonRow';

const RECENT_LIMIT = 8;

type Props = {
    token?: string;
    onOpen: (jobId: string) => void;
    /** When set, only runs from this season show by default; a toggle reveals every season. */
    seasonYear?: number;
    /** Layout style for displaying the recent sims, e.g., 'grid' or 'list' */
    layout?: 'grid' | 'list';
};

/**
 * The signed-in user's own recent open sims (runs with no takeover team, i.e. `team_id === null`
 * on the shared `sim_season` row) — a takeover played from a built team already shows up in that
 * team's own Sims tab, so this stays scoped to the plain "simulate a season" path. Deliberately
 * minimal for now; can grow filters/grouping later if it gets used.
 */
export function RecentSims({ token, onOpen, seasonYear, layout }: Props) {
    const [seasons, setSeasons] = useState<SimSeasonListItem[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showAllSeasons, setShowAllSeasons] = useState(false);
    const isGridLayout = layout === 'grid';
    const layoutClass = isGridLayout ? 'grid grid-cols-2 gap-2' : 'flex flex-col gap-2';

    useEffect(() => {
        if (!token) return;
        let stale = false;
        fetchSimHistory(token)
            .then(data => { if (!stale) setSeasons(data.filter(entry => entry.team_id === null)); })
            .catch(err => { if (!stale) setError(err instanceof Error ? err.message : 'Failed to load your simulations.'); });
        return () => { stale = true; };
    }, [token]);

    const canFilterBySeason = seasonYear !== undefined && !showAllSeasons;
    const visibleSeasons = useMemo(() => {
        if (!seasons) return seasons;
        return canFilterBySeason ? seasons.filter(entry => entry.year === seasonYear) : seasons;
    }, [seasons, canFilterBySeason, seasonYear]);
    const hiddenByFilter = seasons && visibleSeasons ? seasons.length - visibleSeasons.length : 0;

    const seasonToggle = seasonYear !== undefined && seasons && seasons.length > 0 && (hiddenByFilter > 0 || showAllSeasons) ? (
        <button
            type="button"
            onClick={() => setShowAllSeasons(prev => !prev)}
            className="text-[11px] font-semibold text-(--text-secondary) hover:text-(--text-primary) underline underline-offset-2 cursor-pointer"
        >
            {showAllSeasons ? `Show only ${seasonYear}` : `Show all seasons${hiddenByFilter > 0 ? ` (${hiddenByFilter} more)` : ''}`}
        </button>
    ) : null;

    if (!token || error) {
        return error ? (
            <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                {error}
            </div>
        ) : null;
    }

    if (seasons === null) {
        return (
            <div className={layoutClass}>
                {Array.from({ length: RECENT_LIMIT }).map((_, index) => <SimSeasonRowSkeleton key={index} />)}
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

    if (!visibleSeasons || visibleSeasons.length === 0) {
        return (
            <div className="flex flex-col items-center gap-2 py-8 px-4 text-center">
                <p className="text-[13px] text-(--text-tertiary)">
                    No simulations for {seasonYear} yet.
                </p>
                {seasonToggle}
            </div>
        );
    }

    return (
        <div className={layoutClass}>
            {seasonToggle && <div className="flex justify-end pb-0.5">{seasonToggle}</div>}
            {visibleSeasons.slice(0, RECENT_LIMIT).map(entry => (
                <SimSeasonRow
                    key={entry.entry_id}
                    entry={entry}
                    showTime
                    disabled={!entry.job_id}
                    onOpen={() => entry.job_id && onOpen(entry.job_id)}
                />
            ))}
        </div>
    );
}
