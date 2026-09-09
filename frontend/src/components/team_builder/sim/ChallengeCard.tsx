import { useState, type ReactNode } from 'react';
import {
    FaPlus, FaListUl, FaSpinner, FaChevronDown, FaChevronUp,
    FaCalendarDays, FaShirt, FaSackDollar, FaFlagCheckered, FaClock, FaTrophy, FaChevronRight, FaFilter, FaUsers,
} from 'react-icons/fa6';
import { fetchUserTeams, type TeamSummary } from '../../../api/userTeams';
import { fetchEligibleTeamIds, type ChallengeInstance } from '../../../api/sim';
import { TeamCard } from '../TeamCard';
import { challengeCategoryMeta } from './challengeCategory';
import { challengeGoalLabel, challengeDaysLeft, challengeRestrictionsLabel } from './challengeLabels';
import { challengeSuccessRate } from './challengeStats';

type Props = {
    challenge: ChallengeInstance;
    token?: string;
    /** Spins up a fresh team pre-configured for this challenge (budget, player filters, and a
     *  roster pre-sized to the challenge's minimum) and drops the user on the team editor's
     *  setup step. */
    onNewTeam: (challenge: ChallengeInstance) => void;
    onUseExistingTeam: (challenge: ChallengeInstance, teamId: string) => void;
    /** Present only in the list view — opens the challenge's own detail + scoped leaderboard.
     *  Omitted when this card is already the detail view's own header. */
    onViewLeaderboard?: (challenge: ChallengeInstance) => void;
};

/** One tile in the challenge's info grid — an icon, a label, and its value, stacked. */
function StatTile({ icon, label, value, fullWidth }: { icon: ReactNode; label: string; value: string; fullWidth?: boolean }) {
    return (
        <div className={`flex items-start gap-2.5 rounded-lg bg-(--background-tertiary) px-3 py-3 ${fullWidth ? 'col-span-2' : ''}`}>
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
 * two ways to bring a team to it — a fresh team pre-configured for the challenge, or one of the
 * caller's existing teams. Both land on the normal team editor — a challenge team is a real,
 * permanent, editable team, not a throwaway roll.
 *
 * Sized for a small, high-value set (usually 3-6 live at once) rather than a dense scrolling
 * list, so it spends vertical space generously on a proper info grid instead of a cramped pill row.
 */
export function ChallengeCard({ challenge, token, onNewTeam, onUseExistingTeam, onViewLeaderboard }: Props) {
    const [showExisting, setShowExisting] = useState(false);
    const [existingTeams, setExistingTeams] = useState<TeamSummary[] | null>(null);
    // Only populated when the challenge restricts players — null means "no restriction to
    // apply", not "not loaded yet" (both cases skip the extra filter below).
    const [eligibleTeamIds, setEligibleTeamIds] = useState<Set<string> | null>(null);
    const [existingError, setExistingError] = useState<string | null>(null);

    const fits = (team: TeamSummary) =>
        !team.is_drafting &&
        !team.is_archived &&
        (challenge.pts_limit == null || team.total_points <= challenge.pts_limit) &&
        team.roster_count >= challenge.roster_size &&
        (eligibleTeamIds === null || eligibleTeamIds.has(team.team_id));
    const left = challengeDaysLeft(challenge);
    const category = challengeCategoryMeta(challenge.category);
    const successRate = challengeSuccessRate(challenge);

    async function toggleExisting() {
        const next = !showExisting;
        setShowExisting(next);
        if (next && existingTeams === null && token) {
            try {
                const [teams, eligibleIds] = await Promise.all([
                    fetchUserTeams(token),
                    challenge.player_filters ? fetchEligibleTeamIds(challenge.instance_id, token) : Promise.resolve(null),
                ]);
                setExistingTeams(teams);
                setEligibleTeamIds(eligibleIds ? new Set(eligibleIds) : null);
            } catch (err) {
                setExistingError(err instanceof Error ? err.message : 'Failed to load your teams.');
            }
        }
    }

    return (
        <div
            className="flex flex-col gap-4 rounded-xl border border-(--divider) border-l-4 bg-(--background-secondary) p-5"
            style={{ borderLeftColor: `var(${category.cssVar})` }}
        >
            <div className="flex items-start justify-between gap-3">
                <div className="w-full">
                    <div className="flex justify-between items-start " >
                        <div className='space-y-1 flex flex-col' >
                            <span
                                className="inline-flex self-start items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-2 py-1 rounded-full"
                                style={{ color: `var(${category.cssVar})`, backgroundColor: `color-mix(in srgb, var(${category.cssVar}) 15%, transparent)` }}
                            >
                                {category.icon} {category.label}
                            </span>
                            <div className="flex gap-y-1 gap-x-2 items-center flex-wrap">
                                
                                <h3 className="text-[16px] font-black text-(--text-primary)">{challenge.title}</h3>
                                <span className="flex items-center gap-1 text-[11px] text-(--text-tertiary) bg-(--background-tertiary) px-2 py-1 rounded-full">
                                    <FaClock className="text-[10px]" />
                                    {left > 0 ? `${left}d left` : 'Expires today'}
                                </span>
                            </div>
                        </div>
                        
                        {onViewLeaderboard && (
                            <button
                                type="button"
                                onClick={() => onViewLeaderboard(challenge)}
                                className="flex items-center gap-1 text-sm font-bold text-tertiary hover:opacity-80 cursor-pointer transition-opacity"
                            >
                                <FaTrophy /> Leaderboard <FaChevronRight className="text-[9px]" />
                            </button>
                        )}
                    </div>
                    
                    <p className="text-[12px] text-(--text-secondary) mt-1.5 leading-relaxed">{challenge.description}</p>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
                <StatTile icon={<FaFlagCheckered />} label="Goal" value={challengeGoalLabel(challenge)} fullWidth />
                <StatTile icon={<FaCalendarDays />} label="Season" value={String(challenge.year)} />
                <StatTile icon={<FaShirt />} label="Take Over" value={challenge.replaces_abbr} />
                <StatTile icon={<FaSackDollar />} label="Budget" value={challenge.pts_limit != null ? `${challenge.pts_limit} pts` : 'No limit'} />
                <StatTile icon={<FaUsers />} label="Min Roster" value={`${challenge.roster_size} players`} />
                {successRate && (
                    <StatTile
                        icon={<FaTrophy />}
                        label="Success Rate"
                        value={`${successRate.pct}% · ${successRate.entrants} ${successRate.entrants === 1 ? 'entry' : 'entries'}`}
                    />
                )}
                {challengeRestrictionsLabel(challenge) && (
                    <StatTile icon={<FaFilter />} label="Player Restrictions" value={challengeRestrictionsLabel(challenge)!} fullWidth />
                )}
            </div>

            {token ? (
                <div className="flex flex-col gap-2">

                    <h5 className="text-[12px] font-bold text-(--text-primary) mb-1">
                        Build your team:
                    </h5>

                    <div className="grid grid-cols-2 gap-2">
                        <button
                            type="button"
                            onClick={() => onNewTeam(challenge)}
                            className="flex items-center justify-center gap-1.5 rounded-lg px-2.5 py-2.5 text-[11px] font-bold bg-(--secondary) text-(--background-primary) hover:opacity-90 cursor-pointer transition-opacity"
                        >
                            <FaPlus className="text-[10px]" /> New Team
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
                        <div className="flex flex-col gap-2 rounded-lg border border-(--divider) p-2 max-h-84 overflow-y-scroll scrollbar-hide">
                            {existingError && <p className="text-[11px] text-red-400">{existingError}</p>}
                            {!existingError && existingTeams === null && (
                                <div className="flex justify-center py-3"><FaSpinner className="animate-spin text-(--text-tertiary) text-[13px]" /></div>
                            )}
                            {existingTeams !== null && existingTeams.filter(fits).length === 0 && (
                                <p className="text-[11px] text-(--text-tertiary) px-1 py-1.5">
                                    None of your finished teams fit this challenge yet.
                                </p>
                            )}
                            {existingTeams?.filter(fits).map(t => (
                                <TeamCard key={t.team_id} team={t} onClick={() => onUseExistingTeam(challenge, t.team_id)} />
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
