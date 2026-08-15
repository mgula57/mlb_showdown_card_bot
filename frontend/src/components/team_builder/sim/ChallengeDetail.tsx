import { useEffect, useState } from 'react';
import { FaArrowLeft, FaSpinner, FaTrophy } from 'react-icons/fa6';
import {
    fetchChallengeInstance, fetchSimLeaderboard,
    type ChallengeInstance, type SimLeaderboardEntry, type SimLeaderboardSort,
} from '../../../api/sim';
import { ChallengeCard } from './ChallengeCard';
import { SimSeasonRow } from './SimSeasonRow';
import { Tabs, type TabItem } from '../../shared/Tabs';

type Props = {
    instanceId: string;
    token?: string;
    /** Warm-start only — the challenge as already known from the card that linked here, so the
     *  header paints instantly instead of blanking while the fetch below (the actual source of
     *  truth, since this page must also resolve for a cold, no-context shared link) resolves. */
    initialChallenge?: ChallengeInstance;
    onBack: () => void;
    onQuickStart: (challenge: ChallengeInstance) => void;
    onBuildFromScratch: (challenge: ChallengeInstance) => void;
    onUseExistingTeam: (challenge: ChallengeInstance, teamId: string) => void;
    onOpenSeason: (teamId: string, jobId: string) => void;
};

const SORT_TABS: TabItem<SimLeaderboardSort>[] = [
    { id: 'wins', label: 'Best Record', title: 'Ranked by wins' },
    { id: 'efficiency', label: 'Best GM', title: 'Ranked by wins per roster point spent' },
];

/**
 * One challenge, at its own shareable URL: its own details up top — the same card as the list
 * view, so the three ways to start a team stay one tap away — and below it the leaderboard
 * scoped to just this challenge instance. Entries only rank against others who took on the same
 * budget/goal, never the wider "every sim played this year" pool, and the viewer's own attempt
 * (if any) is highlighted inline via `SimSeasonRow`'s `is_own` styling.
 */
export function ChallengeDetail({ instanceId, token, initialChallenge, onBack, onQuickStart, onBuildFromScratch, onUseExistingTeam, onOpenSeason }: Props) {
    const [challenge, setChallenge] = useState<ChallengeInstance | null | undefined>(initialChallenge);
    const [challengeError, setChallengeError] = useState<string | null>(null);
    const [entries, setEntries] = useState<SimLeaderboardEntry[] | null>(null);
    const [entriesError, setEntriesError] = useState<string | null>(null);
    const [sort, setSort] = useState<SimLeaderboardSort>('wins');

    // The URL is the source of truth even when a card handed off an initial value — a cold
    // shared link has no such value, and a warm one may be showing stale pass/fail data.
    useEffect(() => {
        let stale = false;
        fetchChallengeInstance(instanceId, token)
            .then(result => { if (!stale) setChallenge(result); })
            .catch(err => { if (!stale) setChallengeError(err instanceof Error ? err.message : 'Failed to load this challenge.'); });
        return () => { stale = true; };
    }, [instanceId, token]);

    useEffect(() => {
        if (!challenge) return;
        let stale = false;
        fetchSimLeaderboard(token, challenge.year, sort)
            .then(seasons => {
                if (stale) return;
                const season = seasons.find(s => s.year === challenge.year);
                const group = season?.groups.find(g => g.challenge_instance_id === challenge.instance_id);
                setEntries(group?.entries ?? []);
            })
            .catch(err => { if (!stale) setEntriesError(err instanceof Error ? err.message : 'Failed to load leaderboard.'); });
        return () => { stale = true; };
    }, [token, challenge, sort]);

    const backButton = (
        <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 text-[12px] font-bold text-(--text-secondary) hover:text-(--text-primary) cursor-pointer transition-colors self-start"
        >
            <FaArrowLeft className="text-[10px]" /> All Challenges
        </button>
    );

    if (challengeError) {
        return (
            <div className="flex flex-col gap-4">
                {backButton}
                <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">{challengeError}</div>
            </div>
        );
    }

    if (challenge === null) {
        return (
            <div className="flex flex-col gap-4">
                {backButton}
                <p className="text-[13px] text-(--text-tertiary) py-8 text-center">
                    This challenge doesn't exist, or has been removed.
                </p>
            </div>
        );
    }

    if (challenge === undefined) {
        return (
            <div className="flex flex-col gap-4">
                {backButton}
                <div className="flex justify-center py-12">
                    <FaSpinner className="animate-spin text-(--text-tertiary) text-xl" />
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4">
            {backButton}

            <ChallengeCard
                challenge={challenge}
                token={token}
                onQuickStart={onQuickStart}
                onBuildFromScratch={onBuildFromScratch}
                onUseExistingTeam={onUseExistingTeam}
            />

            <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between gap-2">
                    <h3 className="flex items-center gap-1.5 text-[13px] font-black text-(--text-primary)">
                        <FaTrophy className="text-[11px] text-(--showdown-blue)" /> Leaderboard
                    </h3>
                    <Tabs tabs={SORT_TABS} value={sort} onChange={setSort} size="sm" />
                </div>

                {entriesError && (
                    <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                        {entriesError}
                    </div>
                )}
                {!entriesError && entries === null && (
                    <div className="flex justify-center py-8">
                        <FaSpinner className="animate-spin text-(--text-tertiary) text-lg" />
                    </div>
                )}
                {!entriesError && entries !== null && entries.length === 0 && (
                    <p className="text-[12px] text-(--text-tertiary) py-6 text-center">
                        No one has taken on this challenge yet — be the first.
                    </p>
                )}
                {entries !== null && entries.length > 0 && (
                    <div className="flex flex-col gap-1.5">
                        {entries.map(entry => (
                            <SimSeasonRow
                                key={entry.entry_id}
                                entry={entry}
                                rank={entry.rank}
                                attempts={entry.attempts}
                                onOpen={() => entry.team_id && entry.job_id && onOpenSeason(entry.team_id, entry.job_id)}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
