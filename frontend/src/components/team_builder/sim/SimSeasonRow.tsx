import { FaTrophy, FaLock } from 'react-icons/fa6';
import type { SimSeasonListItem } from '../../../api/sim';

function medalClass(rank: number): string {
    if (rank === 1) return 'text-yellow-300';
    if (rank === 2) return 'text-(--text-secondary)';
    if (rank === 3) return 'text-orange-400';
    return 'text-(--text-tertiary)';
}

function relativeTime(iso: string): string {
    const ms = Date.now() - new Date(iso).getTime();
    const mins = Math.round(ms / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.round(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.round(hours / 24);
    if (days < 30) return `${days}d ago`;
    return new Date(iso).toLocaleDateString();
}

type Props = {
    entry: SimSeasonListItem;
    onOpen: () => void;
    /** Leaderboard context: this row's rank in the season, and how many runs it beat out. */
    rank?: number;
    attempts?: number;
    /** History context: when this specific run happened. */
    showTime?: boolean;
};

/** One played season, as a clickable row. Shared by the leaderboard and personal history so a
 *  result reads identically wherever it's found. */
export function SimSeasonRow({ entry, onOpen, rank, attempts, showTime }: Props) {
    return (
        <button
            type="button"
            onClick={onOpen}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors cursor-pointer hover:bg-(--divider) ${
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
                        {entry.team_name ?? entry.team_abbreviation ?? 'Unnamed team'}
                    </span>
                    {entry.is_champion && <FaTrophy className="text-[10px] text-yellow-300 shrink-0" title="Won the World Series" />}
                    {entry.is_own && rank !== undefined && <FaLock className="text-[9px] text-(--text-tertiary) shrink-0" title="Your result" />}
                </span>
                <span className="block text-[11px] text-(--text-tertiary) truncate">
                    {!showTime && `${entry.year} · `}
                    took over {entry.replaced_abbr ?? '—'}
                    {entry.showdown_set ? ` · set ${entry.showdown_set}` : ''}
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
            </span>
        </button>
    );
}
