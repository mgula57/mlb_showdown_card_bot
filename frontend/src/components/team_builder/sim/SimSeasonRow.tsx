import type { ReactNode } from 'react';
import { FaTrophy, FaLock, FaCheck, FaXmark } from 'react-icons/fa6';
import type { SimSeasonListItem } from '../../../api/sim';
import { ordinal, relativeTime } from '../../../functions/formatters';
import { SetBadge } from '../../shared/SetBadge';
import { Plate, type PlateVariant } from '../../shared/Plate';
import { FitText } from '../../shared/FitText';
import { CAPS_LABEL_CLASS } from '../../shared/fieldStyles';
import { UserAvatar } from '../../shared/UserAvatar';

/** A labelled rule between the runs that cleared a challenge and the ones that didn't. Shared by
 *  every place a challenge's entries get split into those two buckets. */
export function OutcomeDivider({ label, tone }: { label: string; tone: 'success' | 'muted' }) {
    const color = tone === 'success' ? 'text-(--success)' : 'text-(--text-tertiary)';
    return (
        <div className="flex items-center gap-2 pt-1">
            <span className={`shrink-0 ${color} ${CAPS_LABEL_CLASS}`}>{label}</span>
            <span className="h-px flex-1 bg-(--divider)" />
        </div>
    );
}

function medalClass(rank: number): string {
    if (rank === 1) return 'text-(--gold)';
    if (rank === 2) return 'text-(--text-secondary)';
    if (rank === 3) return 'text-(--bronze)';
    return 'text-(--text-tertiary)';
}

/** The "Best GM" number, shown per row: wins per 1,000 roster points spent. Higher is a more
 *  efficient roster. Null when the run has no recorded point cost. */
function gmEfficiency(entry: SimSeasonListItem): number | null {
    if (!entry.roster_points || entry.roster_points <= 0) return null;
    return (entry.wins / entry.roster_points) * 1000;
}

type FinishPlate = { key: string; variant: PlateVariant; content: ReactNode; title?: string };

/** How the season ended, as plates: how far the club went in October (if it got there), where it
 *  finished in its division, and a challenge run's pass/fail. Ordered most to least notable. */
function finishPlates(entry: SimSeasonListItem): FinishPlate[] {
    const plates: FinishPlate[] = [];
    if (entry.is_champion) {
        plates.push({ key: 'post', variant: 'navy', content: <><FaTrophy className="text-(--gold)" />Champions</>, title: 'Won the World Series' });
    } else if (entry.won_pennant) {
        plates.push({ key: 'post', variant: 'outline', content: 'Pennant', title: 'Reached the World Series' });
    } else if (entry.made_playoffs) {
        plates.push({ key: 'post', variant: 'outline', content: entry.seed ? `Playoffs · #${entry.seed} seed` : 'Playoffs' });
    }
    if (entry.division && entry.division_rank) {
        plates.push({ key: 'div', variant: 'ink', content: `${ordinal(entry.division_rank)} ${entry.division}` });
    }
    if (entry.challenge_result) {
        const passed = entry.challenge_result === 'passed';
        plates.push({
            key: 'challenge',
            variant: passed ? 'success' : 'outline',
            content: <>{passed ? <FaCheck /> : <FaXmark />}{passed ? 'Cleared' : 'Missed goal'}</>,
        });
    }
    return plates;
}

/** The win total on a .000-1.000 track with a tick at .500, filled in the club's color, so a
 *  list of runs can be compared at a glance without reading every record. */
function WinTrack({ winPct, color }: { winPct: number; color: string }) {
    const pct = Math.max(0, Math.min(1, winPct)) * 100;
    return (
        <span aria-hidden className="relative block w-16 h-1 rounded-plate bg-(--divider) overflow-hidden">
            <span className="absolute inset-y-0 left-0" style={{ width: `${pct}%`, backgroundColor: color }} />
            <span className="absolute inset-y-0 left-1/2 w-px bg-(--text-tertiary)" />
        </span>
    );
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
 *  result reads identically wherever it's found. Leads with a small team-color field (the club's
 *  abbreviation over its year, like the year/team plate on a card), then how the season finished
 *  as plates, and the record as the hero number with a win track under it. */
export function SimSeasonRow({ entry, onOpen, rank, attempts, showTime, disabled }: Props) {
    const efficiency = gmEfficiency(entry);
    const abbreviation = entry.team_abbreviation ?? entry.replaced_abbr ?? '—';
    const teamColor = entry.primary_color ?? 'var(--field-ink)';
    // Open sims often carry only the abbreviation as the name; don't print it twice
    const title = entry.team_name && entry.team_name !== abbreviation ? entry.team_name : `${entry.year} Season`;
    const plates = finishPlates(entry);

    // The creator leads the meta line beside their avatar; the rest follows as plain text
    const meta = [
        entry.replaced_abbr && entry.replaced_abbr !== abbreviation ? `took over ${entry.replaced_abbr}` : null,
        attempts && attempts > 1 ? `best of ${attempts}` : null,
        showTime ? relativeTime(entry.created_at) : null,
    ].filter(Boolean).join(' · ');

    return (
        <button
            type="button"
            onClick={onOpen}
            disabled={disabled}
            className={`group w-full flex items-stretch overflow-hidden rounded-card border text-left transition-colors ${
                disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:border-(--rule-strong)'
            } ${
                entry.is_own && rank !== undefined
                    ? 'border-(--showdown-blue) ring-1 ring-(--showdown-blue)/40 bg-(--showdown-blue)/5'
                    : 'border-(--divider) bg-(--background-secondary)'
            }`}
        >
            {rank !== undefined && (
                <span className={`w-8 shrink-0 flex items-center justify-center font-display-upright text-[17px] leading-none tabular-nums ${medalClass(rank)}`}>
                    {rank}
                </span>
            )}

            {/* Team-color field: the club's abbreviation over the season year */}
            <span
                className="relative w-16 shrink-0 flex flex-col items-center justify-center gap-1 px-1.5 py-2 border-r-2 border-(--card-edge)"
                style={{ backgroundColor: teamColor }}
            >
                <span aria-hidden className="absolute inset-0 bg-pinstripe opacity-60" />
                <FitText minScale={0.55} as="span" className="relative w-full text-center font-display text-[22px] leading-[0.9] text-white text-outline-double">
                    {abbreviation}
                </FitText>
                <Plate variant="onField" size="xs" className="relative">{entry.year}</Plate>
            </span>

            <span className="min-w-0 flex-1 flex flex-col justify-center gap-1 px-3 py-2">
                <span className="flex items-center gap-1.5 min-w-0">
                    <FitText minScale={0.75} as="span" className="min-w-0 flex-1 font-display-upright text-[15px] leading-none text-(--text-primary)">
                        {title}
                    </FitText>
                    {entry.is_own && rank !== undefined && <FaLock className="text-[9px] text-(--text-tertiary) shrink-0" title="Your result" />}
                </span>
                {(plates.length > 0 || entry.showdown_set) && (
                    <span className="flex flex-wrap items-center gap-1">
                        {entry.showdown_set && <SetBadge set={entry.showdown_set} abbreviated size="sm" />}
                        {plates.map(p => <Plate key={p.key} variant={p.variant} size="sm" title={p.title}>{p.content}</Plate>)}
                    </span>
                )}
                {(entry.creator_username || meta) && (
                    <span className="flex items-center gap-1 min-w-0 text-[11px] text-(--text-tertiary)">
                        {entry.creator_username && (
                            <>
                                <UserAvatar
                                    name={entry.creator_username}
                                    avatarUrl={entry.creator_avatar_url}
                                    primaryColor={entry.creator_primary_color}
                                    size={14}
                                />
                                <span className="shrink-0 font-medium text-(--text-secondary)">{entry.creator_username}</span>
                            </>
                        )}
                        {meta && <span className="truncate">{entry.creator_username ? `· ${meta}` : meta}</span>}
                    </span>
                )}
            </span>

            <span className="shrink-0 flex flex-col items-end justify-center gap-1 pl-2 pr-3 py-2">
                <span className="font-display-upright text-[20px] leading-none text-(--text-primary) tabular-nums">
                    {entry.wins}<span className="text-(--text-tertiary)">–</span>{entry.losses}
                </span>
                <WinTrack winPct={entry.win_pct} color={entry.primary_color ?? 'var(--text-secondary)'} />
                <span className="text-[11px] leading-none text-(--text-tertiary) tabular-nums">
                    {entry.win_pct.toFixed(3).replace(/^0\./, '.')}
                    {efficiency !== null && (
                        <span title="Wins per 1,000 roster points spent (Best GM)">
                            {' · '}{efficiency.toFixed(1)} <span className="font-semibold">W/1k</span>
                        </span>
                    )}
                </span>
            </span>
        </button>
    );
}

/** Loading placeholder for `SimSeasonRow`, same footprint so a list settles into place instead
 *  of growing/shrinking once real rows replace it. `showRank` mirrors whether the real rows here
 *  reserve the rank column, so the skeleton doesn't shift width when data lands. */
export function SimSeasonRowSkeleton({ showRank = false }: { showRank?: boolean }) {
    return (
        <div aria-hidden className="w-full flex items-stretch overflow-hidden rounded-card border border-(--divider) bg-(--background-tertiary) animate-pulse">
            {showRank && <span className="w-8 shrink-0 flex items-center justify-center"><span className="w-3 h-3.5 rounded-plate bg-(--background-primary)" /></span>}
            <span className="w-16 shrink-0 bg-(--background-primary)" />
            <span className="min-w-0 flex-1 flex flex-col justify-center gap-1.5 px-3 py-2.5">
                <span className="h-3.5 w-2/5 rounded-plate bg-(--background-primary)" />
                <span className="flex gap-1">
                    <span className="h-4 w-8 rounded-plate bg-(--background-primary)" />
                    <span className="h-4 w-20 rounded-plate bg-(--background-primary)" />
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-3.5 h-3.5 rounded-full bg-(--background-primary)" />
                    <span className="h-2.5 w-3/5 rounded-plate bg-(--background-primary)" />
                </span>
            </span>
            <span className="flex flex-col items-end justify-center gap-1.5 shrink-0 pl-2 pr-3 py-2.5">
                <span className="h-4 w-12 rounded-plate bg-(--background-primary)" />
                <span className="h-1 w-16 rounded-plate bg-(--background-primary)" />
                <span className="h-2.5 w-10 rounded-plate bg-(--background-primary)" />
            </span>
        </div>
    );
}
