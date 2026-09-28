import { useEffect, useMemo, useState } from 'react';
import { FaSpinner, FaPlay, FaFlagCheckered, FaClock, FaSackDollar, FaUsers, FaCircleCheck, FaXmark, FaShirt, FaCalendarDays } from 'react-icons/fa6';
import { Modal } from '../../shared/Modal';
import { tabButtonClass, tabListClass } from '../../shared/tabStyles';
import FormDropdown from '../../customs/FormDropdown';
import ManagerStyleFields from '../../simulate/ManagerStyleFields';
import { NEUTRAL_MANAGER, managerPayload, type ManagerPreference } from '../../../api/manager';
import {
    fetchSimSeasons, fetchSimSeasonTeams, fetchChallenges, fetchEligibleTeamIds, startSeasonSim,
    SimAlreadyRunningError, type TakeoverClub, type ChallengeInstance,
} from '../../../api/sim';
import { byChallengeCategory, challengeCategoryMeta } from './challengeCategory';
import { challengeGoalLabel, challengeDaysLeft, challengeRestrictionsLabel } from './challengeLabels';

function errorMessage(err: unknown): string {
    return err instanceof Error ? err.message : String(err);
}

/** The two ways a finished team can be put into play. */
type PlayMode = 'season' | 'challenge';

/** Result of the challenge's player_filters check for this team — only ever set for challenges
 *  that actually have restrictions, and only once the user has selected one. */
type FilterCheck = 'checking' | 'ok' | 'blocked';

type Props = {
    teamId: string;
    teamName: string;
    /** Set the team was built in — the sim runs with the same card set. */
    showdownSet: string;
    /** Team's current cost and roster count, checked against each challenge's limits up front. */
    teamPoints: number;
    rosterCount: number;
    token: string;
    /** The challenge this team was created for, if any. Opens the modal on the Challenge tab with
     *  that instance selected, and is merged into the list even if it has since rotated out. */
    presetChallenge?: ChallengeInstance;
    onCancel: () => void;
    /** Hand off to the queued job's own URL, which owns polling and the result. */
    onStarted: (jobId: string) => void;
    /** Jump straight to the user's already-running job — shown when a start is blocked by
     *  `SimAlreadyRunningError`. Its team may differ from this one, since the cap is per-user. */
    onViewExisting: (jobId: string, teamId: string | null) => void;
};

/** One labelled fact about a challenge, laid out inline in the selected challenge's summary. */
function ChallengeFact({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
    return (
        <span className="flex items-center gap-1.5 text-[11px] text-(--text-secondary)">
            <span className="text-(--text-tertiary) text-[10px] shrink-0">{icon}</span>
            {children}
        </span>
    );
}

/**
 * One challenge in the picker — a compact, selectable row rather than the full `ChallengeCard`,
 * since the team is already chosen and only the challenge is still in question.
 */
function ChallengeOption({ challenge, selected, blocked, onSelect }: {
    challenge: ChallengeInstance;
    selected: boolean;
    /** Fails a limit this team can't clear — still selectable so the reason can be shown. */
    blocked: boolean;
    onSelect: () => void;
}) {
    const category = challengeCategoryMeta(challenge.category);
    const left = challengeDaysLeft(challenge);
    return (
        <button
            type="button"
            onClick={onSelect}
            aria-pressed={selected}
            className={`flex items-start gap-3 text-left rounded-xl border px-3 py-2.5 transition-colors cursor-pointer ${
                selected
                    ? 'border-(--secondary) bg-(--background-tertiary)'
                    : 'border-(--divider) hover:border-(--text-tertiary)'
            } ${blocked ? 'opacity-50' : ''}`}
        >
            <span className="w-1 self-stretch rounded-full shrink-0" style={{ backgroundColor: `var(${category.cssVar})` }} />
            <span className="min-w-0 flex-1">
                <span className="flex items-center gap-2 flex-wrap">
                    <span className="text-[13px] font-bold text-(--text-primary)">{challenge.title}</span>
                    <span className="text-[10px] font-bold uppercase tracking-wide" style={{ color: `var(${category.cssVar})` }}>
                        {category.label}
                    </span>
                    {challenge.challenge_result === 'passed' && (
                        <span className="flex items-center gap-1 text-[10px] font-bold text-(--success)"><FaCircleCheck /> Passed</span>
                    )}
                </span>
                <span className="block text-[11px] text-(--text-tertiary) mt-0.5 truncate">
                    {challengeGoalLabel(challenge)} · {challenge.year} {challenge.replaces_abbr}
                    {challenge.pts_limit != null ? ` · ${challenge.pts_limit} pts` : ''}
                </span>
            </span>
            <span className="flex items-center gap-1 text-[10px] text-(--text-tertiary) shrink-0 mt-0.5">
                <FaClock className="text-[9px]" />
                {left > 0 ? `${left}d` : 'today'}
            </span>
        </button>
    );
}

/**
 * Everything a finished team can be dropped into, behind one "Play" button: a free-form season
 * takeover (pick any year and club) or a live Team Challenge (year, club, and budget all fixed by
 * the challenge). Both queue the same job and hand back its id.
 *
 * A team created from a challenge opens straight on that challenge, but is free to switch tabs —
 * a challenge team is a normal team, and nothing stops it from playing an open season too.
 */
export function PlayModal({
    teamId, teamName, showdownSet, teamPoints, rosterCount, token,
    presetChallenge, onCancel, onStarted, onViewExisting,
}: Props) {
    const [mode, setMode] = useState<PlayMode>(presetChallenge ? 'challenge' : 'season');

    // Season takeover
    const [seasons, setSeasons] = useState<number[]>([]);
    const [year, setYear] = useState<number | null>(null);
    // Clubs are stored with the year they belong to, so "still loading" is derived from a
    // mismatch rather than tracked as its own state.
    const [clubsFor, setClubsFor] = useState<{ year: number; teams: TakeoverClub[] } | null>(null);
    const [replaces, setReplaces] = useState<string>('');
    const [manager, setManager] = useState<ManagerPreference>(NEUTRAL_MANAGER);

    // Challenges
    const [challenges, setChallenges] = useState<ChallengeInstance[] | null>(null);
    const [challengesError, setChallengesError] = useState<string | null>(null);
    const [selectedInstanceId, setSelectedInstanceId] = useState<string | null>(presetChallenge?.instance_id ?? null);
    const [filterChecks, setFilterChecks] = useState<Record<string, FilterCheck>>({});

    // Shared launch state
    const [starting, setStarting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [runningJob, setRunningJob] = useState<{ jobId: string; teamId: string | null } | null>(null);

    useEffect(() => {
        fetchSimSeasons()
            .then(list => {
                setSeasons(list);
                // Default to the most recent completed season rather than the current one,
                // which may only be partway played.
                setYear(list[1] ?? list[0] ?? null);
            })
            .catch(err => setError(errorMessage(err)));
    }, []);

    useEffect(() => {
        if (year === null) return;
        let stale = false;
        fetchSimSeasonTeams(year)
            .then(({ teams, default: worst }) => {
                if (stale) return;
                setClubsFor({ year, teams });
                setReplaces(worst ?? teams[0]?.abbreviation ?? '');
            })
            .catch(err => { if (!stale) setError(errorMessage(err)); });
        return () => { stale = true; };
    }, [year]);

    useEffect(() => {
        let stale = false;
        fetchChallenges(token)
            .then(list => { if (!stale) setChallenges([...list].sort(byChallengeCategory)); })
            .catch(err => { if (!stale) setChallengesError(errorMessage(err)); });
        return () => { stale = true; };
    }, [token]);

    // A preset challenge may have rotated out of the live list, so it's shown regardless — and
    // shown immediately, without waiting on the fetch.
    const challengeOptions = useMemo(() => {
        const list = challenges ?? [];
        if (presetChallenge && !list.some(c => c.instance_id === presetChallenge.instance_id)) {
            return [presetChallenge, ...list];
        }
        return list;
    }, [challenges, presetChallenge]);

    const selectedChallenge = challengeOptions.find(c => c.instance_id === selectedInstanceId) ?? null;

    /** Limits this team fails on `challenge`, phrased for display. The same rules the backend
     *  re-enforces at launch — checked here so a doomed run isn't queued in the first place. */
    function blockersFor(challenge: ChallengeInstance): string[] {
        const blockers: string[] = [];
        if (challenge.pts_limit != null && teamPoints > challenge.pts_limit) {
            blockers.push(`This team costs ${teamPoints} pts, over the ${challenge.pts_limit} pt challenge limit.`);
        }
        if (rosterCount < challenge.roster_size) {
            blockers.push(`This team has ${rosterCount} players, under the challenge's ${challenge.roster_size}-player minimum.`);
        }
        if (filterChecks[challenge.instance_id] === 'blocked') {
            const restrictions = challengeRestrictionsLabel(challenge);
            blockers.push(`This team has players the challenge doesn't allow${restrictions ? ` (${restrictions})` : ''}.`);
        }
        return blockers;
    }

    function selectChallenge(challenge: ChallengeInstance) {
        setSelectedInstanceId(challenge.instance_id);
        setError(null);
        setRunningJob(null);
        if (!challenge.player_filters || filterChecks[challenge.instance_id]) return;
        setFilterChecks(prev => ({ ...prev, [challenge.instance_id]: 'checking' }));
        fetchEligibleTeamIds(challenge.instance_id, token)
            .then(ids => setFilterChecks(prev => ({ ...prev, [challenge.instance_id]: ids.includes(teamId) ? 'ok' : 'blocked' })))
            // A failed pre-check shouldn't hold up the launch — the backend enforces the same
            // rules, so let the attempt through and surface its error instead.
            .catch(() => setFilterChecks(prev => ({ ...prev, [challenge.instance_id]: 'ok' })));
    }

    // Preselecting from `presetChallenge` skips `selectChallenge`, so kick off its filter check here.
    useEffect(() => {
        if (presetChallenge) selectChallenge(presetChallenge);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [presetChallenge?.instance_id]);

    async function start(options: { year: number; replaces: string; manager?: ManagerPreference; challenge_instance_id?: string }) {
        setStarting(true);
        setError(null);
        setRunningJob(null);
        try {
            const { job_id } = await startSeasonSim({ team_id: teamId, set: showdownSet, ...options }, token);
            onStarted(job_id);
        } catch (err) {
            if (err instanceof SimAlreadyRunningError) setRunningJob({ jobId: err.jobId, teamId: err.teamId });
            setError(errorMessage(err));
            setStarting(false);
        }
    }

    const clubs = clubsFor?.year === year ? clubsFor.teams : [];
    const loadingClubs = year !== null && clubsFor?.year !== year;
    const selectedClub = clubs.find(club => club.abbreviation === replaces);

    const selectedBlockers = selectedChallenge ? blockersFor(selectedChallenge) : [];
    const checkingFilters = selectedChallenge ? filterChecks[selectedChallenge.instance_id] === 'checking' : false;
    const canPlay = mode === 'season'
        ? !loadingClubs && year !== null && !!replaces
        : !!selectedChallenge && selectedBlockers.length === 0 && !checkingFilters;

    function handlePlay() {
        if (starting || !canPlay) return;
        if (mode === 'season' && year !== null) {
            start({ year, replaces, manager: managerPayload(manager) });
        } else if (selectedChallenge) {
            // Year, club, and budget all come from the instance — the backend re-derives and
            // enforces them server-side regardless of what's sent here.
            start({
                year: selectedChallenge.year,
                replaces: selectedChallenge.replaces_abbr,
                challenge_instance_id: selectedChallenge.instance_id,
            });
        }
    }

    return (
        <Modal 
            title="Play a Season" 
            subtitle={teamName} 
            size="md" 
            onClose={onCancel}
            footer={
                <div className="flex justify-end gap-2">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="px-3 py-2 rounded-lg text-[12px] font-semibold text-(--text-secondary) hover:text-(--text-primary) transition-colors cursor-pointer"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={handlePlay}
                        disabled={starting || !canPlay}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-(--secondary) text-[12px] font-bold text-(--background-primary) hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {starting ? <FaSpinner className="animate-spin text-[10px]" /> : <FaPlay className="text-[10px]" />}
                        {mode === 'season' ? 'Play Season' : 'Play Challenge'}
                    </button>
                </div>
            }
        >
            <div className="flex flex-col gap-4 px-3 py-2">
                <div className={tabListClass(true)}>
                    <button type="button" onClick={() => setMode('season')} className={tabButtonClass(mode === 'season', 'sm', true)}>
                        <FaCalendarDays className="text-[11px]" /> Season Takeover
                    </button>
                    <button type="button" onClick={() => setMode('challenge')} className={tabButtonClass(mode === 'challenge', 'sm', true)}>
                        <FaFlagCheckered className="text-[11px]" /> Team Challenge
                    </button>
                </div>

                {mode === 'season' ? (
                    <>
                        <p className="text-[13px] text-(--text-secondary)">
                            Your team takes over a real club's schedule, division, and opponents for a full
                            season — then plays through the postseason.
                        </p>

                        <FormDropdown
                            label="Season"
                            options={seasons.map(season => ({ label: String(season), value: String(season) }))}
                            selectedOption={year === null ? '' : String(year)}
                            onChange={value => setYear(Number(value))}
                            placeholder="Select a season"
                        />

                        <FormDropdown
                            label="Replace"
                            options={clubs.map(club => ({
                                label: `${club.name} (${club.wins}-${club.losses})`,
                                value: club.abbreviation,
                            }))}
                            selectedOption={replaces}
                            onChange={setReplaces}
                            disabled={loadingClubs || clubs.length === 0}
                            placeholder={loadingClubs ? 'Loading teams…' : 'Select a team'}
                        />

                        {selectedClub && (
                            <p className="text-[12px] text-(--text-tertiary)">
                                The real {selectedClub.name} went {selectedClub.wins}-{selectedClub.losses}
                                {selectedClub.division ? ` in the ${selectedClub.division}` : ''}.
                            </p>
                        )}

                        <ManagerStyleFields value={manager} onChange={setManager} />
                    </>
                ) : (
                    <>
                        <p className="text-[13px] text-(--text-secondary)">
                            Clear the challenge's goal to pass it and land on its leaderboard.
                        </p>

                        {challengesError && (
                            <div className="text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                                {challengesError}
                            </div>
                        )}

                        <div className="flex flex-col gap-1.5">
                            {challengeOptions.map(challenge => (
                                <ChallengeOption
                                    key={challenge.instance_id}
                                    challenge={challenge}
                                    selected={challenge.instance_id === selectedInstanceId}
                                    blocked={blockersFor(challenge).length > 0}
                                    onSelect={() => selectChallenge(challenge)}
                                />
                            ))}
                            {challenges === null && !challengesError && (
                                <div className="flex justify-center py-4"><FaSpinner className="animate-spin text-(--text-tertiary) text-[13px]" /></div>
                            )}
                            {challenges !== null && challengeOptions.length === 0 && (
                                <p className="text-[12px] text-(--text-tertiary) py-4 text-center">
                                    No challenges are live right now — check back soon.
                                </p>
                            )}
                        </div>

                        {selectedChallenge && (
                            <div className="flex flex-col gap-2 rounded-xl bg-(--background-tertiary) px-3 py-2.5">
                                <p className="text-[12px] text-(--text-secondary) leading-relaxed">{selectedChallenge.description}</p>
                                <div className="flex items-center gap-x-4 gap-y-1 flex-wrap">
                                    <ChallengeFact icon={<FaFlagCheckered />}>{challengeGoalLabel(selectedChallenge)}</ChallengeFact>
                                    <ChallengeFact icon={<FaShirt />}>{selectedChallenge.year} {selectedChallenge.replaces_abbr}</ChallengeFact>
                                    <ChallengeFact icon={<FaSackDollar />}>
                                        {selectedChallenge.pts_limit != null ? `${teamPoints} / ${selectedChallenge.pts_limit} pts` : 'No limit'}
                                    </ChallengeFact>
                                    <ChallengeFact icon={<FaUsers />}>{rosterCount} / {selectedChallenge.roster_size} players</ChallengeFact>
                                </div>
                                {checkingFilters && (
                                    <span className="flex items-center gap-1.5 text-[11px] text-(--text-tertiary)">
                                        <FaSpinner className="animate-spin text-[10px]" /> Checking player restrictions…
                                    </span>
                                )}
                                {selectedBlockers.map(blocker => (
                                    <span key={blocker} className="flex items-start gap-1.5 text-[11px] text-red-400">
                                        <FaXmark className="text-[10px] mt-0.5 shrink-0" /> {blocker}
                                    </span>
                                ))}
                            </div>
                        )}
                    </>
                )}

                {error && (
                    <div className="flex items-center justify-between gap-2 text-[12px] text-red-400 px-3 py-2 rounded-lg border border-red-400/30 bg-red-400/5">
                        <span>{error}</span>
                        {runningJob && (
                            <button
                                type="button"
                                onClick={() => onViewExisting(runningJob.jobId, runningJob.teamId)}
                                className="shrink-0 font-semibold underline underline-offset-2 hover:opacity-80 transition-opacity cursor-pointer"
                            >
                                View it
                            </button>
                        )}
                    </div>
                )}

                
            </div>
        </Modal>
    );
}
