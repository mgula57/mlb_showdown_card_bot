import { useState, type ReactNode } from 'react';
import {
    FaDice, FaPen, FaListUl, FaSpinner, FaChevronDown, FaChevronUp,
    FaCalendarDays, FaShirt, FaSackDollar, FaFlagCheckered, FaClock, FaTrophy, FaChevronRight,
} from 'react-icons/fa6';
import { fetchUserTeams, type TeamSummary } from '../../../api/userTeams';
import type { ChallengeInstance } from '../../../api/sim';

type Props = {
    challenge: ChallengeInstance;
    token?: string;
    onQuickStart: (challenge: ChallengeInstance) => void;
    onBuildFromScratch: (challenge: ChallengeInstance) => void;
    onUseExistingTeam: (challenge: ChallengeInstance, teamId: string) => void;
    /** Present only in the list view — opens the challenge's own detail + scoped leaderboard.
     *  Omitted when this card is already the detail view's own header. */
    onViewLeaderboard?: (challenge: ChallengeInstance) => void;
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

/** One tile in the challenge's info grid — an icon, a label, and its value, stacked. */
function StatTile({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
    return (
        <div className="flex items-start gap-2.5 rounded-lg bg-(--background-tertiary) px-3 py-3">
            <span className="text-(--text-tertiary) text-[13px] mt-0.5 shrink-0">{icon}</span>
            <span className="min-w-0">
                <span className="block text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary)">{label}</span>
                <span className="block text-[13px] font-bold text-(--text-primary) truncate">{value}</span>
            </span>
        </div>
    );
}

/**
 * One live challenge instance: its goal/budget/club, the caller's own pass/fail badge, and the
 * three ways to bring a team to it. All three land on the normal team editor — a challenge team
 * is a real, permanent, editable team, not a throwaway roll.
 *
 * Sized for a small, high-value set (usually 3-6 live at once) rather than a dense scrolling
 * list, so it spends vertical space generously on a proper info grid instead of a cramped pill row.
 */
export function ChallengeCard({ challenge, token, onQuickStart, onBuildFromScratch, onUseExistingTeam, onViewLeaderboard }: Props) {
    const [showExisting, setShowExisting] = useState(false);
    const [existingTeams, setExistingTeams] = useState<TeamSummary[] | null>(null);
    const [existingError, setExistingError] = useState<string | null>(null);

    const fits = (team: TeamSummary) => !team.is_drafting && (challenge.pts_limit == null || team.total_points <= challenge.pts_limit);
    const left = daysLeft(challenge.expires_at);

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
        <div className="flex flex-col gap-4 rounded-xl border border-(--divider) bg-(--background-secondary) p-5">
            <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                    <div className="flex gap-3 items-center">
                        <h3 className="text-[16px] font-black text-(--text-primary)">{challenge.title}</h3>
                        <span className="flex items-center gap-1 text-[11px] text-(--text-tertiary) bg-(--background-tertiary) px-2 py-1 rounded-full">
                            <FaClock className="text-[10px]" />
                            {left > 0 ? `${left}d left` : 'Expires today'}
                        </span>
                    </div>
                    
                    <p className="text-[12px] text-(--text-secondary) mt-1.5 leading-relaxed">{challenge.description}</p>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1.5">
                    {onViewLeaderboard && (
                        <button
                            type="button"
                            onClick={() => onViewLeaderboard(challenge)}
                            className="flex items-center gap-1 text-sm font-bold text-(--showdown-blue) hover:opacity-80 cursor-pointer transition-opacity"
                        >
                            <FaTrophy /> Leaderboard <FaChevronRight className="text-[9px]" />
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
                <StatTile icon={<FaCalendarDays />} label="Season" value={String(challenge.year)} />
                <StatTile icon={<FaShirt />} label="Take Over" value={challenge.replaces_abbr} />
                <StatTile icon={<FaSackDollar />} label="Budget" value={challenge.pts_limit != null ? `${challenge.pts_limit} pts` : 'No limit'} />
                <StatTile icon={<FaFlagCheckered />} label="Goal" value={goalLabel(challenge)} />
            </div>

            {token ? (
                <div className="flex flex-col gap-2">

                    <h5 className="text-[12px] font-bold text-(--text-primary) mb-1">
                        Build your team:
                    </h5>

                    <div className="grid grid-cols-3 gap-2">
                        <button
                            type="button"
                            onClick={() => onQuickStart(challenge)}
                            className="flex items-center justify-center gap-1.5 rounded-lg px-2.5 py-2.5 text-[11px] font-bold bg-(--secondary) text-(--background-primary) hover:opacity-90 cursor-pointer transition-opacity"
                        >
                            <FaDice className="text-[11px]" /> Quick Start
                        </button>
                        <button
                            type="button"
                            onClick={() => onBuildFromScratch(challenge)}
                            className="flex items-center justify-center gap-1.5 rounded-lg px-2.5 py-2.5 text-[11px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) hover:border-(--text-tertiary) cursor-pointer transition-colors"
                        >
                            <FaPen className="text-[10px]" /> From Scratch
                        </button>
                        <button
                            type="button"
                            onClick={toggleExisting}
                            className="flex items-center justify-center gap-1.5 rounded-lg px-2.5 py-2.5 text-[11px] font-bold border border-(--divider) text-(--text-secondary) hover:text-(--text-primary) hover:border-(--text-tertiary) cursor-pointer transition-colors"
                        >
                            <FaListUl className="text-[10px]" /> Existing
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
                                    None of your finished teams fit this challenge's budget yet.
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
