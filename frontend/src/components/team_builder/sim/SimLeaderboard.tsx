import { useEffect, useMemo, useState } from 'react';
import { FaTrophy, FaChevronRight, FaShirt } from 'react-icons/fa6';
import {
    fetchChallenges, fetchSimLeaderboard,
    type SimLeaderboardEntry, type SimLeaderboardGroup, type SimLeaderboardSeason, type SimLeaderboardSort,
} from '../../../api/sim';
import { OutcomeDivider, SimSeasonRow, SimSeasonRowSkeleton } from './SimSeasonRow';
import { Tabs, type TabItem } from '../../shared/Tabs';

type Props = {
    token?: string;
    onOpenSeason: (teamId: string, jobId: string) => void;
    /** Opens a challenge instance's own shareable page (its full details + scoped leaderboard). */
    onOpenChallenge: (instanceId: string) => void;
    /** Owned by the parent so it can sit alongside the Leaderboard/My Attempts toggle in one
     *  header row instead of a second one of its own. */
    sort: SimLeaderboardSort;
};

type View = 'challenges' | 'open';

const VIEW_TABS: TabItem<View>[] = [
    { id: 'challenges', label: 'Challenges' },
    { id: 'open', label: 'Open Play' },
];

/** How many rows a challenge card shows inline, split into cleared/didn't-clear buckets, before
 *  pointing to the full leaderboard for the rest. */
const ENTRY_CAP = 12;

/** "Mar 3 – Mar 10, 2026", or just the end year if the run was inside one calendar year. Null
 *  when either end of the window is missing — an instance pruned before that column existed. */
function formatChallengeWindow(startsAt: string | null, expiresAt: string | null): string | null {
    if (!startsAt || !expiresAt) return null;
    const start = new Date(startsAt);
    const end = new Date(expiresAt);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
    const sameYear = start.getFullYear() === end.getFullYear();
    const startLabel = start.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: sameYear ? undefined : 'numeric' });
    const endLabel = end.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    return `${startLabel} – ${endLabel}`;
}

type ChallengeCardData = { year: number; group: SimLeaderboardGroup; hasOwnEntry: boolean };

/** One challenge instance's card: title/description, its takeover club and live window, a
 *  cleared-vs-didn't-clear split of its top results (capped at `ENTRY_CAP`), and a link through
 *  to the instance's own full leaderboard. Shared by the flat list and the Active/Historical
 *  sections "Full history" splits into. */
function ChallengeLeaderboardCard({ card, onOpenSeason, onOpenChallenge }: {
    card: ChallengeCardData;
    onOpenSeason: (teamId: string, jobId: string) => void;
    onOpenChallenge: (instanceId: string) => void;
}) {
    const { year, group, hasOwnEntry } = card;
    const entries = group.entries;
    const passes = entries.filter(e => e.challenge_result === 'passed').length;
    const clearedPct = entries.length > 0 ? Math.round((passes / entries.length) * 100) : null;
    const preview = entries.slice(0, ENTRY_CAP);
    const remaining = entries.length - preview.length;
    const passedPreview = preview.filter(e => e.challenge_result === 'passed');
    const failedPreview = preview.filter(e => e.challenge_result !== 'passed');
    const splitPreview = passedPreview.length > 0 && failedPreview.length > 0;
    // The challenge assigns one club to every entrant, so any entry's `replaced_abbr` speaks
    // for the whole instance.
    const takeoverAbbr = entries[0]?.replaced_abbr ?? null;
    const dateRange = formatChallengeWindow(group.challenge_starts_at, group.challenge_expires_at);

    const renderEntry = (entry: SimLeaderboardEntry) => (
        <SimSeasonRow
            key={entry.entry_id}
            entry={entry}
            rank={entry.rank}
            attempts={entry.attempts}
            onOpen={() => entry.team_id && entry.job_id && onOpenSeason(entry.team_id, entry.job_id)}
        />
    );

    return (
        <div className="flex flex-col gap-2.5 rounded-xl border border-(--divider) border-l-4 border-l-(--showdown-blue) bg-(--background-secondary) p-4">
            <div className="flex items-start justify-between gap-2 flex-wrap">
                <div className="min-w-0 flex flex-col gap-1">
                    <h4 className="flex items-center gap-1.5 text-[13px] font-black text-(--text-primary)">
                        <FaTrophy className="text-[11px] text-(--showdown-blue) shrink-0" />
                        {group.challenge_title}
                        {hasOwnEntry && (
                            <span className="text-[10px] font-bold text-(--showdown-blue) uppercase tracking-wide">You</span>
                        )}
                    </h4>
                    {group.challenge_description && (
                        <p className="text-[11px] text-(--text-secondary) leading-snug line-clamp-2">
                            {group.challenge_description}
                        </p>
                    )}
                </div>
                <button
                    type="button"
                    onClick={() => group.challenge_instance_id && onOpenChallenge(group.challenge_instance_id)}
                    className="flex items-center gap-1 text-[11px] font-bold text-(--showdown-blue) hover:opacity-80 cursor-pointer transition-opacity shrink-0"
                >
                    {remaining > 0 ? `View full leaderboard (+${remaining})` : 'View challenge'}
                    <FaChevronRight className="text-[10px]" />
                </button>
            </div>

            <span className="flex items-center gap-1.5 text-[11px] text-(--text-tertiary) flex-wrap">
                {takeoverAbbr && (
                    <span className="flex items-center gap-1 font-semibold text-(--text-secondary)">
                        <FaShirt className="text-[10px]" /> {takeoverAbbr}
                    </span>
                )}
                {year}
                <span>· {entries.length} {entries.length === 1 ? 'entry' : 'entries'}</span>
                {clearedPct !== null && <span>· {clearedPct}% cleared</span>}
                {dateRange && <span>· {dateRange}</span>}
            </span>

            {splitPreview ? (
                <>
                    <OutcomeDivider label={`Cleared · ${passedPreview.length}`} tone="success" />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{passedPreview.map(renderEntry)}</div>
                    <OutcomeDivider label={`Didn't clear · ${failedPreview.length}`} tone="muted" />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{failedPreview.map(renderEntry)}</div>
                </>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{preview.map(renderEntry)}</div>
            )}
        </div>
    );
}

/**
 * Season simulation results. Most visitors here are chasing one thing — how a challenge shook
 * out — so that's the default, main-focus view: one card per challenge instance, newest/most
 * relevant first, with a handful of top results and a link through to that challenge's own page.
 * Open-play seasons (no challenge attached) live behind a secondary tab, since they aren't
 * comparable to anything and aren't what most people came here for.
 *
 * The Challenges view itself defaults to just the currently-live instances (the same set the
 * "Active Challenges" grid above shows) — rotated-out ones are still real results, but they'd
 * otherwise pile up and bury what's actually running right now. "Full history" reveals them.
 *
 * Only public teams appear to other users — the viewer's own private results are visible to
 * them alone, which is why a rank is "among entries you can see" rather than global.
 */
export function SimLeaderboard({ token, onOpenSeason, onOpenChallenge, sort }: Props) {
    const [seasons, setSeasons] = useState<SimLeaderboardSeason[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [view, setView] = useState<View>('challenges');
    // Null while loading — treated as "no filter yet" so the list doesn't flash empty and then
    // populate. Instance ids only, from the same endpoint the Active Challenges grid uses.
    const [activeInstanceIds, setActiveInstanceIds] = useState<Set<string> | null>(null);
    const [showFullHistory, setShowFullHistory] = useState(false);

    useEffect(() => {
        let stale = false;
        fetchSimLeaderboard(token, undefined, sort)
            .then(data => { if (!stale) setSeasons(data); })
            .catch(err => { if (!stale) setError(err instanceof Error ? err.message : 'Failed to load leaderboard.'); });
        return () => { stale = true; };
    }, [token, sort]);

    useEffect(() => {
        let stale = false;
        fetchChallenges(token)
            .then(data => { if (!stale) setActiveInstanceIds(new Set(data.map(c => c.instance_id))); })
            .catch(() => { /* best-effort — falls back to showing every challenge group */ });
        return () => { stale = true; };
    }, [token]);

    // Every challenge group across every season, flattened into one list — a challenge instance
    // belongs to exactly one year, so there's no meaningful "within a year" grouping to preserve.
    // Cards you have an entry in float to the top, then newest season first.
    const allChallengeCards = useMemo(() => {
        if (!seasons) return [];
        const cards: { year: number; group: SimLeaderboardGroup; hasOwnEntry: boolean }[] = [];
        for (const season of seasons) {
            for (const group of season.groups) {
                if (!group.challenge_instance_id) continue;
                cards.push({ year: season.year, group, hasOwnEntry: group.entries.some(e => e.is_own) });
            }
        }
        return cards.sort((a, b) => {
            if (a.hasOwnEntry !== b.hasOwnEntry) return a.hasOwnEntry ? -1 : 1;
            return b.year - a.year;
        });
    }, [seasons]);

    const challengeCards = useMemo(() => {
        if (showFullHistory || !activeInstanceIds) return allChallengeCards;
        return allChallengeCards.filter(c => c.group.challenge_instance_id && activeInstanceIds.has(c.group.challenge_instance_id));
    }, [allChallengeCards, activeInstanceIds, showFullHistory]);

    const hiddenHistoricalCount = allChallengeCards.length - challengeCards.length;

    // Once "Full history" is on, `challengeCards` is a mix of live and rotated-out instances —
    // split it back into two labeled sections rather than leaving them interleaved. Skipped (both
    // just alias the flat list) until the active-id set has actually loaded.
    const { activeCards, historicalCards } = useMemo(() => {
        if (!showFullHistory || !activeInstanceIds) return { activeCards: challengeCards, historicalCards: [] as typeof challengeCards };
        const active = challengeCards.filter(c => c.group.challenge_instance_id && activeInstanceIds.has(c.group.challenge_instance_id));
        const historical = challengeCards.filter(c => !c.group.challenge_instance_id || !activeInstanceIds.has(c.group.challenge_instance_id));
        return { activeCards: active, historicalCards: historical };
    }, [challengeCards, activeInstanceIds, showFullHistory]);
    const sectioned = showFullHistory && activeInstanceIds !== null;

    // Open-play groups keep the year-sectioned layout, since there's no other axis to hang them on.
    const openSeasons = useMemo(() => {
        if (!seasons) return [];
        return [...seasons]
            .sort((a, b) => {
                if (a.has_own_entry !== b.has_own_entry) return a.has_own_entry ? -1 : 1;
                return b.year - a.year;
            })
            .map(season => ({ ...season, groups: season.groups.filter(g => !g.challenge_instance_id) }))
            .filter(season => season.groups.length > 0);
    }, [seasons]);

    const header = (
        <div className="px-2 flex items-center justify-between gap-2 flex-wrap">
            <Tabs tabs={VIEW_TABS} value={view} onChange={setView} size="sm" />
            {view === 'challenges' && (hiddenHistoricalCount > 0 || showFullHistory) && (
                <button
                    type="button"
                    onClick={() => setShowFullHistory(v => !v)}
                    className="flex items-center gap-1 text-[11px] font-bold text-(--text-tertiary) hover:text-(--text-primary) cursor-pointer transition-colors"
                >
                    {showFullHistory ? 'Active challenges only' : `Full history (+${hiddenHistoricalCount})`}
                    <FaChevronRight className="text-[9px]" />
                </button>
            )}
        </div>
    );

    if (error) {
        return (
            <div className="flex flex-col gap-3">
                {header}
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                    {error}
                </div>
            </div>
        );
    }

    if (seasons === null) {
        return (
            <div className="flex flex-col gap-3">
                {header}
                {view === 'challenges' ? (
                    <div className="flex flex-col gap-3">
                        {[0, 1].map(i => (
                            <div
                                key={i}
                                aria-hidden
                                className="flex flex-col gap-2.5 rounded-xl border border-(--divider) border-l-4 border-l-(--divider) bg-(--background-secondary) p-4 animate-pulse"
                            >
                                <div className="flex items-start justify-between gap-2">
                                    <div className="flex flex-col gap-1.5 flex-1">
                                        <div className="h-3.5 w-32 rounded bg-(--background-tertiary)" />
                                        <div className="h-2.5 w-3/4 rounded bg-(--background-tertiary)" />
                                    </div>
                                    <div className="h-3 w-24 rounded bg-(--background-tertiary) shrink-0" />
                                </div>
                                <div className="h-2.5 w-24 rounded bg-(--background-tertiary)" />
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {Array.from({ length: 4 }, (_, j) => <SimSeasonRowSkeleton key={j} showRank />)}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col gap-6 px-4">
                        {[0, 1].map(i => (
                            <section key={i} className="flex flex-col gap-1.5">
                                <div className="h-3 w-14 rounded bg-(--background-tertiary) animate-pulse mb-1" />
                                {Array.from({ length: 3 }, (_, j) => <SimSeasonRowSkeleton key={j} showRank />)}
                            </section>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-3">
            {header}

            {view === 'challenges' && (
                challengeCards.length === 0 ? (
                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center px-4">
                        {allChallengeCards.length === 0
                            ? 'No challenge attempts yet. Take on one of the Active Challenges above.'
                            : 'No results yet for the active challenges.'}
                    </p>
                ) : sectioned ? (
                    <div className="flex flex-col gap-5 px-4">
                        {activeCards.length > 0 && (
                            <section className="flex flex-col gap-3">
                                <h4 className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide">
                                    Active · {activeCards.length}
                                </h4>
                                {activeCards.map(card => (
                                    <ChallengeLeaderboardCard
                                        key={card.group.challenge_instance_id}
                                        card={card}
                                        onOpenSeason={onOpenSeason}
                                        onOpenChallenge={onOpenChallenge}
                                    />
                                ))}
                            </section>
                        )}
                        {historicalCards.length > 0 && (
                            <section className="flex flex-col gap-3">
                                <h4 className="text-[11px] font-bold text-(--text-tertiary) uppercase tracking-wide">
                                    Historical · {historicalCards.length}
                                </h4>
                                {historicalCards.map(card => (
                                    <ChallengeLeaderboardCard
                                        key={card.group.challenge_instance_id}
                                        card={card}
                                        onOpenSeason={onOpenSeason}
                                        onOpenChallenge={onOpenChallenge}
                                    />
                                ))}
                            </section>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col gap-3 px-4">
                        {challengeCards.map(card => (
                            <ChallengeLeaderboardCard
                                key={card.group.challenge_instance_id}
                                card={card}
                                onOpenSeason={onOpenSeason}
                                onOpenChallenge={onOpenChallenge}
                            />
                        ))}
                    </div>
                )
            )}

            {view === 'open' && (
                openSeasons.length === 0 ? (
                    <p className="text-[13px] text-(--text-tertiary) py-8 text-center px-4">
                        No open-play seasons yet. Open one of your teams and hit Play Season.
                    </p>
                ) : (
                    <div className="flex flex-col gap-6 px-4">
                        {openSeasons.map(season => {
                            const teamCount = season.groups.reduce((n, g) => n + g.entries.length, 0);
                            return (
                                <section key={season.year} className="flex flex-col gap-2">
                                    <div className="flex items-baseline gap-2">
                                        <h2 className="text-[13px] font-bold text-(--text-secondary)">{season.year}</h2>
                                        <span className="text-[11px] text-(--text-tertiary)">
                                            {teamCount} {teamCount === 1 ? 'team' : 'teams'} played
                                        </span>
                                        {season.has_own_entry && (
                                            <span className="text-[10px] font-bold text-(--showdown-blue) uppercase tracking-wide">You</span>
                                        )}
                                    </div>
                                    <div className="flex flex-col gap-1.5">
                                        {season.groups.flatMap(g => g.entries).map(entry => (
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
                            );
                        })}
                    </div>
                )
            )}
        </div>
    );
}
