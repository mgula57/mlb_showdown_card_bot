import { useState } from 'react';
import { FaDice, FaPen, FaListUl, FaCheck, FaXmark, FaSpinner, FaChevronDown, FaChevronUp } from 'react-icons/fa6';
import { fetchUserTeams, type TeamSummary } from '../../../api/userTeams';
import type { ChallengeInstance } from '../../../api/sim';

type Props = {
    challenge: ChallengeInstance;
    token?: string;
    onQuickStart: (challenge: ChallengeInstance) => void;
    onBuildFromScratch: (challenge: ChallengeInstance) => void;
    onUseExistingTeam: (challenge: ChallengeInstance, teamId: string) => void;
};

function goalLabel(challenge: ChallengeInstance): string {
    switch (challenge.goal_type) {
        case 'made_playoffs': return 'Make the playoffs';
        case 'win_pennant': return 'Win the pennant';
        case 'win_world_series': return 'Win the World Series';
        case 'min_wins': return `Win at least ${(challenge.goal_value?.min_wins as number | undefined) ?? '?'} games`;
        default: return 'Clear the bar';
    }
}

function daysLeft(expiresAt: string): number {
    return Math.max(0, Math.ceil((new Date(expiresAt).getTime() - Date.now()) / 86_400_000));
}

/**
 * One live challenge instance: its goal/budget/club, the caller's own pass/fail badge, and the
 * three ways to bring a team to it. All three land on the normal team editor — a challenge team
 * is a real, permanent, editable team, not a throwaway roll.
 */
export function ChallengeCard({ challenge, token, onQuickStart, onBuildFromScratch, onUseExistingTeam }: Props) {
    const [showExisting, setShowExisting] = useState(false);
    const [existingTeams, setExistingTeams] = useState<TeamSummary[] | null>(null);
    const [existingError, setExistingError] = useState<string | null>(null);

    const fits = (team: TeamSummary) => challenge.pts_limit == null || team.total_points <= challenge.pts_limit;

    async function toggleExisting() {
        const next = !showExisting;
        setShowExisting(next);
        if (next && existingTeams === null && token) {
            try {
                setExistingTeams(await fetchUserTeams(token));
            } catch (err) {
                setExistingError(err instanceof Error ? err.message : 'Failed to load your teams.');
            }
        }
    }

    return (
        <div className="flex flex-col gap-3 rounded-xl border border-(--divider) bg-(--background-secondary) p-4">
            <div className="flex items-start justify-between gap-2">
                <div>
                    <h3 className="text-[14px] font-black text-(--text-primary)">{challenge.title}</h3>
                    <p className="text-[12px] text-(--text-secondary) mt-0.5">{challenge.description}</p>
                </div>
                {challenge.challenge_result && (
                    <span className={`shrink-0 flex items-center gap-1 text-[10px] font-black uppercase tracking-wide rounded-full px-2 py-1 ${
                        challenge.challenge_result === 'passed'
                            ? 'bg-green-500/15 text-green-600 dark:text-green-400'
                            : 'bg-(--background-tertiary) text-(--text-tertiary)'
                    }`}>
                        {challenge.challenge_result === 'passed' ? <FaCheck /> : <FaXmark />}
                        {challenge.challenge_result === 'passed' ? 'Passed' : 'Try again'}
                    </span>
                )}
            </div>

            <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                <span className="rounded-lg px-2 py-1 font-bold bg-(--background-tertiary) text-(--text-secondary)">{challenge.year}</span>
                <span className="rounded-lg px-2 py-1 font-bold bg-(--background-tertiary) text-(--text-secondary)">Take over {challenge.replaces_abbr}</span>
                <span className="rounded-lg px-2 py-1 font-bold bg-(--background-tertiary) text-(--text-secondary)">
                    {challenge.pts_limit != null ? `${challenge.pts_limit} pt limit` : 'No pt limit'}
                </span>
                <span className="rounded-lg px-2 py-1 font-bold bg-(--background-tertiary) text-(--text-secondary)">{goalLabel(challenge)}</span>
                <span className="ml-auto text-(--text-tertiary)">{daysLeft(challenge.expires_at)}d left</span>
            </div>

            {token ? (
                <div className="flex flex-col gap-1.5">
                    <div className="flex flex-wrap gap-1.5">
                        <button
                            type="button"
                            onClick={() => onQuickStart(challenge)}
                            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-bold bg-(--secondary) text-(--background-primary) hover:opacity-90 cursor-pointer transition-opacity"
                        >
                            <FaDice className="text-[10px]" /> Quick Start
                        </button>
                        <button
                            type="button"
                            onClick={() => onBuildFromScratch(challenge)}
                            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) hover:border-(--text-tertiary) cursor-pointer transition-colors"
                        >
                            <FaPen className="text-[10px]" /> Build from Scratch
                        </button>
                        <button
                            type="button"
                            onClick={toggleExisting}
                            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) hover:border-(--text-tertiary) cursor-pointer transition-colors"
                        >
                            <FaListUl className="text-[10px]" /> Use an Existing Team
                            {showExisting ? <FaChevronUp className="text-[9px]" /> : <FaChevronDown className="text-[9px]" />}
                        </button>
                    </div>

                    {showExisting && (
                        <div className="flex flex-col gap-1 rounded-lg border border-(--divider) p-2">
                            {existingError && <p className="text-[11px] text-red-400">{existingError}</p>}
                            {!existingError && existingTeams === null && (
                                <div className="flex justify-center py-3"><FaSpinner className="animate-spin text-(--text-tertiary) text-[13px]" /></div>
                            )}
                            {existingTeams !== null && existingTeams.filter(fits).length === 0 && (
                                <p className="text-[11px] text-(--text-tertiary) px-1 py-1.5">
                                    None of your teams fit this challenge's budget yet.
                                </p>
                            )}
                            {existingTeams?.filter(fits).map(t => (
                                <button
                                    key={t.team_id}
                                    type="button"
                                    onClick={() => onUseExistingTeam(challenge, t.team_id)}
                                    className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-[12px] font-semibold text-(--text-primary) hover:bg-(--background-tertiary) cursor-pointer transition-colors text-left"
                                >
                                    <span className="truncate">{t.name}</span>
                                    <span className="shrink-0 text-(--text-tertiary) font-normal">{t.total_points} pts</span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            ) : (
                <p className="text-[11px] text-(--text-tertiary)">Sign in to take on this challenge.</p>
            )}
        </div>
    );
}
