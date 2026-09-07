import { useEffect, useRef, useState } from 'react';
import { FaSpinner, FaTriangleExclamation } from 'react-icons/fa6';
import { cancelSimJob, fetchSimJob, fetchSimSeason, type ChallengeStanding, type SeasonSimSummary, type SimJob } from '../../../api/sim';
import BackButton from '../../shared/BackButton';
import { SimProgress } from './SimProgress';
import { SimResult } from './SimResult';

// Setup phases report no game counts, so polling a little faster keeps the phase label moving.
const POLL_INTERVAL_MS = 1000;

type Props = {
    jobId: string;
    teamName: string;
    token?: string;
    onBack: () => void;
    /** Shown only once this season resolves as a Team Challenge attempt (`challengeResult` is set) -
     *  a plain season sim has no Challenges-tab context to return to. */
    onBackToChallenges?: () => void;
    onRunAgain?: () => void;
    /** Challenge runs only: route back into the team editor with this challenge primed so the
     *  user can tweak the roster and re-run. Given the run's challenge instance id (or null). */
    onTryAgain?: (challengeInstanceId: string | null) => void;
};

/**
 * Shows one simulation, live or historical, at a URL keyed by job id.
 *
 * The job id is permanent even though the job row it names is not — job rows track progress and
 * expire after a week, but the season result they produce is stored forever under the same id.
 * So this always tries the season record first: for a past run (opened from history or the
 * leaderboard) that resolves immediately with no polling at all. Only when it 404s — meaning the
 * run hasn't finished yet — does this fall back to polling the job, then re-fetching the season
 * once it succeeds.
 */
export function SimSeasonView({ jobId, teamName, token, onBack, onBackToChallenges, onRunAgain, onTryAgain }: Props) {
    const [job, setJob] = useState<SimJob | null>(null);
    const [summary, setSummary] = useState<SeasonSimSummary | null>(null);
    const [challengeResult, setChallengeResult] = useState<'passed' | 'failed' | null>(null);
    const [challengeStanding, setChallengeStanding] = useState<ChallengeStanding | null>(null);
    const [challengeInstanceId, setChallengeInstanceId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    // Only true once the season record has 404'd and we're actually polling a live job. Keeps the
    // "playing the season" progress screen from flashing while the initial season fetch (a
    // historical run opened from history/leaderboard) is still in flight.
    const [polling, setPolling] = useState(false);
    const cancelled = useRef(false);

    useEffect(() => {
        cancelled.current = false;
        let timer: number | undefined;

        function applySeason(season: Awaited<ReturnType<typeof fetchSimSeason>>) {
            if (!season) return;
            setSummary(season.summary);
            setChallengeResult(season.challenge_result);
            setChallengeStanding(season.challenge_standing ?? null);
            setChallengeInstanceId(season.challenge_instance_id);
        }

        async function pollJob() {
            if (!token) {
                // Can't distinguish "still running" from "doesn't exist" without a token, since
                // job progress is owner-only. Not scary — just needs a sign-in to check.
                setError('Sign in to check on this simulation.');
                return;
            }
            try {
                const next = await fetchSimJob(jobId, token);
                if (cancelled.current) return;
                setJob(next);

                if (next.status === 'failed' || next.status === 'cancelled') {
                    setError(next.error ?? 'The simulation failed.');
                    return;
                }
                if (next.status === 'succeeded') {
                    // The record is written just before the job flips to 'succeeded', so it
                    // should already exist — this is the one re-fetch, not a poll.
                    const season = await fetchSimSeason(jobId, token);
                    if (cancelled.current) return;
                    if (season) {
                        applySeason(season);
                    } else {
                        setError('The simulation finished, but its result could not be found.');
                    }
                    return;
                }
                timer = window.setTimeout(pollJob, POLL_INTERVAL_MS);
            } catch (err: unknown) {
                if (!cancelled.current) setError(err instanceof Error ? err.message : 'Failed to load simulation.');
            }
        }

        async function start() {
            setPolling(false);
            try {
                const season = await fetchSimSeason(jobId, token);
                if (cancelled.current) return;
                if (season) {
                    applySeason(season);
                    return;
                }
            } catch (err: unknown) {
                if (!cancelled.current) setError(err instanceof Error ? err.message : 'Failed to load simulation.');
                return;
            }
            if (cancelled.current) return;
            setPolling(true);
            await pollJob();
        }

        start();
        return () => {
            cancelled.current = true;
            if (timer) window.clearTimeout(timer);
        };
    }, [jobId, token]);

    function handleCancel() {
        if (!token) return;
        // No local state change needed - the next poll tick (at most 1s away) picks up the
        // job's new 'cancelled' status.
        cancelSimJob(jobId, token).catch(() => {});
    }

    // A challenge run gets "Edit & Try Again" (back to the editor, challenge primed); a plain
    // takeover run keeps the simpler "Run again".
    const tryAgain = challengeResult !== null && onTryAgain
        ? () => onTryAgain(challengeInstanceId)
        : undefined;

    return (
        <div className="flex flex-col h-full overflow-y-auto">
            <div className="px-4 pt-4 flex items-center gap-2">
                <BackButton onBack={onBack} label="Back to team" />
                {challengeResult !== null && onBackToChallenges && (
                    <BackButton onBack={onBackToChallenges} label="Back to Challenges" />
                )}
            </div>

            {error ? (
                <div className="flex flex-col items-center justify-center gap-3 py-16 px-4 text-center">
                    <FaTriangleExclamation className="text-red-400 text-2xl" />
                    <p className="text-[13px] text-(--text-secondary) max-w-sm">{error}</p>
                    {(tryAgain || onRunAgain) && (
                        <button
                            type="button"
                            onClick={tryAgain ?? onRunAgain}
                            className="px-3 py-2 rounded-lg bg-(--background-tertiary) text-[12px] font-bold text-(--text-primary) hover:opacity-90 transition-opacity cursor-pointer"
                        >
                            Try again
                        </button>
                    )}
                </div>
            ) : summary ? (
                <SimResult
                    summary={summary}
                    challengeResult={challengeResult}
                    challengeStanding={challengeStanding}
                    onRunAgain={onRunAgain}
                    onTryAgain={tryAgain}
                />
            ) : polling ? (
                <SimProgress job={job} teamName={teamName} onCancel={token ? handleCancel : undefined} />
            ) : (
                <div className="flex items-center justify-center py-16">
                    <FaSpinner className="animate-spin text-(--text-tertiary) text-2xl" />
                </div>
            )}
        </div>
    );
}
