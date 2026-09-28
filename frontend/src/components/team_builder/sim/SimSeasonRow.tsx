import { FaTrophy, FaLock } from 'react-icons/fa6';
import type { SimSeasonListItem } from '../../../api/sim';
import { relativeTime } from '../../../functions/formatters';
import { imageForSet } from '../../shared/SiteSettingsContext';

/** A labelled rule between the runs that cleared a challenge and the ones that didn't. Shared by
 *  every place a challenge's entries get split into those two buckets. */
export function OutcomeDivider({ label, tone }: { label: string; tone: 'success' | 'muted' }) {
    const color = tone === 'success' ? 'text-(--success)' : 'text-(--text-tertiary)';
    return (
        <div className="flex items-center gap-2 pt-1">
            <span className={`text-[10px] font-bold uppercase tracking-wide shrink-0 ${color}`}>{label}</span>
            <span className="h-px flex-1 bg-(--divider)" />
        </div>
    );
}

function medalClass(rank: number): string {
    if (rank === 1) return 'text-yellow-300';
    if (rank === 2) return 'text-(--text-secondary)';
    if (rank === 3) return 'text-orange-400';
    return 'text-(--text-tertiary)';
}

/** The "Best GM" number, shown per row: wins per 1,000 roster points spent. Higher is a more
 *  efficient roster. Null when the run has no recorded point cost. */
function gmEfficiency(entry: SimSeasonListItem): number | null {
    if (!entry.roster_points || entry.roster_points <= 0) return null;
    return (entry.wins / entry.roster_points) * 1000;
}

type Props = {
    entry: SimSeasonListItem;
    onOpen: () => void;
    /** Leaderboard context: this row's rank in the season, and how many runs it beat out. */
    rank?: number;
    attempts?: number;
    /** History context: when this specific run happened. */
    showTime?: boolean;
    /** Greys the row out and blocks the click — e.g. a run with no viewable result yet. */
    disabled?: boolean;
};

/** One played season, as a clickable row. Shared by the leaderboard and personal history so a
 *  result reads identically wherever it's found. A team-less "open sim" (no takeover, `team_id`
 *  null — the plain "simulate a season" path) carries no team branding, so it leads with the year
 *  instead and drops the "took over X" line, which wouldn't have a club to name. */
export function SimSeasonRow({ entry, onOpen, rank, attempts, showTime, disabled }: Props) {
    const efficiency = gmEfficiency(entry);
    const isOpenSim = entry.team_id === null;
    return (
        <button
            type="button"
            onClick={onOpen}
            disabled={disabled}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:bg-(--divider)'
            } ${
                entry.is_own ? 'bg-(--showdown-blue)/10 ring-1 ring-(--showdown-blue)/40' : 'bg-(--background-tertiary)'
            }`}
        >
            {rank !== undefined && (
                <span className={`w-6 shrink-0 text-[13px] font-black tabular-nums ${medalClass(rank)}`}>{rank}</span>
            )}

            <span className="w-1.5 h-7 rounded-full shrink-0" style={{ backgroundColor: entry.primary_color ?? 'var(--divider)' }} />

            <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1.5">
                    <span className="text-[13px] font-bold text-(--text-primary) truncate">
                        {entry.team_name ?? entry.team_abbreviation ?? (isOpenSim ? entry.year : 'Unnamed team')}
                    </span>
                    {entry.is_champion && <FaTrophy className="text-[10px] text-yellow-300 shrink-0" title="Won the World Series" />}
                    {entry.is_own && rank !== undefined && <FaLock className="text-[9px] text-(--text-tertiary) shrink-0" title="Your result" />}
                </span>
                <span className="block text-[11px] text-(--text-tertiary) truncate">
                    {entry.creator_username ? `${entry.creator_username} · ` : ''}
                    {!showTime && !isOpenSim && `${entry.year} · `}
                    {entry.replaced_abbr ? `took over ${entry.replaced_abbr}` : ''}
                    {entry.showdown_set && (
                        <>
                            {entry.replaced_abbr ? ' · ' : ''}
                            <img
                                src={imageForSet(entry.showdown_set, true)}
                                alt={entry.showdown_set}
                                className="inline h-3 w-auto object-contain align-middle"
                            />
                        </>
                    )}
                    {entry.division ? ` · ${entry.division}` : ''}
                    {attempts && attempts > 1 ? ` · best of ${attempts}` : ''}
                    {showTime ? ` · ${relativeTime(entry.created_at)}` : ''}
                </span>
            </span>

            <span className="text-right shrink-0">
                <span className="block text-[14px] font-black text-(--text-primary) tabular-nums">
                    {entry.wins}<span className="text-(--text-tertiary)">–</span>{entry.losses}
                </span>
                <span className="block text-[11px] text-(--text-tertiary) tabular-nums">
                    {entry.win_pct.toFixed(3).replace(/^0\./, '.')}
                </span>
                {efficiency !== null && (
                    <span
                        className="block text-[10px] text-(--text-tertiary) tabular-nums"
                        title="Wins per 1,000 roster points spent (Best GM)"
                    >
                        {efficiency.toFixed(1)} <span className="font-semibold">Wins/1k PTS</span>
                    </span>
                )}
            </span>
        </button>
    );
}

/** Loading placeholder for `SimSeasonRow`, same footprint so a list settles into place instead
 *  of growing/shrinking once real rows replace it. `showRank` mirrors whether the real rows here
 *  reserve the rank column, so the skeleton doesn't shift width when data lands. */
export function SimSeasonRowSkeleton({ showRank = false }: { showRank?: boolean }) {
    return (
        <div aria-hidden className="w-full flex items-center gap-3 px-3 py-2 rounded-lg bg-(--background-tertiary) animate-pulse">
            {showRank && <span className="w-6 h-3.5 rounded bg-(--background-primary) shrink-0" />}
            <span className="w-1.5 h-7 rounded-full shrink-0 bg-(--background-primary)" />
            <span className="min-w-0 flex-1 flex flex-col gap-1.5 py-0.5">
                <span className="h-3 w-2/5 rounded bg-(--background-primary)" />
                <span className="h-2.5 w-3/5 rounded bg-(--background-primary)" />
            </span>
            <span className="flex flex-col items-end gap-1.5 shrink-0 py-0.5">
                <span className="h-3.5 w-10 rounded bg-(--background-primary)" />
                <span className="h-2.5 w-8 rounded bg-(--background-primary)" />
            </span>
        </div>
    );
}
