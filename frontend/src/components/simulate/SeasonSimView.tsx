import { useEffect, useRef, useState } from 'react';
import { FaTriangleExclamation } from 'react-icons/fa6';
import { cancelSimJob, fetchSimJob, fetchSimSeason, type SeasonSimSummary, type SimJob } from '../../api/sim';
import { SimProgress } from '../team_builder/sim/SimProgress';
import { SimResult } from '../team_builder/sim/SimResult';

// Setup phases report no game counts, so polling a little faster keeps the phase label moving.
const POLL_INTERVAL_MS = 1000;

type Props = {
    jobId: string;
    token?: string;
    /** Focus club to open the result on — the club the setup form's "Follow" field named. The
     *  result screen's own club switcher takes over from here. */
    initialFocusAbbr?: string;
    onRunAgain?: () => void;
};

function progressLabel(job: SimJob | null): string {
    const config = job?.config;
    const year = config && typeof config.year === 'number' ? config.year : null;
    const focusAbbr = config && typeof config.focus_abbr === 'string' ? config.focus_abbr : null;
    if (year && focusAbbr) return `${year} · ${focusAbbr}`;
    if (year) return `${year} Season`;
    return 'the season';
}

/**
 * Shows one open sim, live or historical, at a URL keyed by job id - the open-sim counterpart to
 * `team_builder/sim/SimSeasonView`. No team ownership or challenge context to resolve here, so
 * this is simpler: just poll the job until it succeeds, then render the result with a club
 * switcher instead of a fixed team.
 */
export function SeasonSimView({ jobId, token, initialFocusAbbr, onRunAgain }: Props) {
    const [job, setJob] = useState<SimJob | null>(null);
    const [summary, setSummary] = useState<SeasonSimSummary | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [focusAbbr, setFocusAbbr] = useState<string | undefined>(initialFocusAbbr);
    const cancelled = useRef(false);

    useEffect(() => {
        cancelled.current = false;
        let timer: number | undefined;

        function applySummary(next: SeasonSimSummary) {
            setSummary(next);
            setFocusAbbr(prev => prev ?? next.team?.replaced_abbr ?? Object.keys(next.identities)[0]);
        }

        async function pollJob() {
            if (!token) {
                // Can't distinguish "still running" from "doesn't exist" without a token, since
                // job progress is owner-only.
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
                    const season = await fetchSimSeason(jobId, token);
                    if (cancelled.current) return;
                    if (season) {
                        applySummary(season.summary);
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
            try {
                const season = await fetchSimSeason(jobId, token);
                if (cancelled.current) return;
                if (season) {
                    applySummary(season.summary);
                    return;
                }
            } catch (err: unknown) {
                if (!cancelled.current) setError(err instanceof Error ? err.message : 'Failed to load simulation.');
                return;
            }
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
        cancelSimJob(jobId, token).catch(() => {});
    }

    return (
        <div className="flex flex-col h-full overflow-y-auto">
            {error ? (
                <div className="flex flex-col items-center justify-center gap-3 py-16 px-4 text-center">
                    <FaTriangleExclamation className="text-red-400 text-2xl" />
                    <p className="text-[13px] text-(--text-secondary) max-w-sm">{error}</p>
                    {onRunAgain && (
                        <button
                            type="button"
                            onClick={onRunAgain}
                            className="px-3 py-2 rounded-lg bg-(--background-tertiary) text-[12px] font-bold text-(--text-primary) hover:opacity-90 transition-opacity cursor-pointer"
                        >
                            Try again
                        </button>
                    )}
                </div>
            ) : summary ? (
                <SimResult summary={summary} onRunAgain={onRunAgain} focusAbbr={focusAbbr} onFocusChange={setFocusAbbr} />
            ) : (
                <SimProgress job={job} teamName={progressLabel(job)} onCancel={token ? handleCancel : undefined} />
            )}
        </div>
    );
}
