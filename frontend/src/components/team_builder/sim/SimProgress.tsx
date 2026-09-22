import { useState } from 'react';
import type { SimJob } from '../../../api/sim';
import { BetaBadge } from '../../shared/BetaBadge';
import { SectionCard } from './SectionCard';
import { SimDiceRoll } from './SimDiceRoll';
import { SimEngineExplainer } from './SimEngineExplainer';
import { SimWinPctChart } from './SimWinPctChart';

type Props = {
    job: SimJob | null;
    teamName: string;
    onCancel?: () => void;
};

// Setup phases report no game counts, so the bar would otherwise sit at 0% through all of card
// loading and schedule building. Stepping it through a few small ticks gives a sense of motion
// without implying real progress toward the games total. Setup occupies the first SETUP_MAX_PCT of
// the bar; once games start, progress continues from there up to 100% rather than resetting to 0.
//
// ORDER IS MEANINGFUL - an entry's index is its position in time, and that is the only thing
// driving the bar during setup. Keep it in the order the backend actually emits them: the two
// explicit `write_progress` calls at the top of `_run_sim_job`, then whatever `_friendly_phase`
// maps the engine's own status messages to (card pool -> schedule -> rosters). A label that
// appears at the wrong index makes the bar jump forward and then back.
const SETUP_PHASES = [
    'Starting simulation',
    'Preparing the season',
    'Loading players',
    'Building the schedule',
    'Setting up teams',
];
const SETUP_MAX_PCT = 25;

/**
 * Progress while a season runs. Setup (card loading, schedule, rosters) reports a phase with no
 * game counts, so the bar ticks through minor fixed increments until games start.
 */
export function SimProgress({ job, teamName, onCancel }: Props) {
    const total = job?.games_total ?? 0;
    const completed = job?.games_completed ?? 0;
    const phase = job?.phase ?? 'Starting simulation';

    const setupIndex = SETUP_PHASES.indexOf(phase);
    const setupPct = setupIndex >= 0 ? ((setupIndex + 1) / SETUP_PHASES.length) * SETUP_MAX_PCT : SETUP_MAX_PCT / 2;
    const rawPct = total > 0
        ? Math.min(100, Math.round(SETUP_MAX_PCT + (completed / total) * (100 - SETUP_MAX_PCT)))
        : setupPct;

    // A progress bar should never run backwards, whatever the phases do. SETUP_PHASES mirrors
    // backend strings it can't verify, so a rename or reorder there would otherwise show up here
    // as a visible stutter - which is exactly what a stale 'Setting up teams' label did. Keyed by
    // job so starting another sim in the same mounted component restarts at 0 rather than
    // inheriting the finished run's high-water mark.
    //
    // Adjusted during render rather than in an effect - React re-runs the component immediately
    // without committing the intermediate paint, so the bar never shows the lower value. Both
    // branches narrow on each pass, so this settles in one extra render.
    const jobId = job?.job_id ?? null;
    const [highWater, setHighWater] = useState({ jobId, pct: 0 });
    if (highWater.jobId !== jobId) {
        setHighWater({ jobId, pct: 0 });
    } else if (rawPct > highWater.pct) {
        setHighWater({ jobId, pct: rawPct });
    }
    const pct = Math.max(rawPct, highWater.pct);

    // Streamed once per throttled progress write (~1/s), so the line lengthens in ~15-20 game
    // steps and recharts animates each extension on its own. Only present for a takeover run.
    const timeline = job?.progress_games ?? [];
    const latest = timeline.length > 0 ? timeline[timeline.length - 1] : null;

    // A "resume from real standings" run's live timeline is already seeded with the real record
    // (`Season.simulate`'s `focus_wins`/`focus_losses`), so the very first streamed point is the
    // seed plus that one game - subtracting its own W/L back out recovers the seed itself, with no
    // extra data needed from the backend. Only meaningful once at least one game has streamed in.
    const isResumed = job?.config?.['resume_from_real_season'] === true;
    const seedRecord = isResumed && timeline.length > 0
        ? { wins: timeline[0].wins - (timeline[0].is_win ? 1 : 0), losses: timeline[0].losses - (timeline[0].is_win ? 0 : 1) }
        : null;

    return (
        <div className="fade-in flex flex-col items-center gap-4 px-4 py-10">
            {/* Hero panel: the dice, what's running, and how far along it is. Clipped, so the
                panel's top padding has to clear the top of the dice' toss arc (~29px). */}
            <div className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-(--divider) bg-linear-to-br from-(--background-tertiary) to-(--background-secondary) px-5 pt-8 pb-5 shadow-sm">
                <div
                    aria-hidden
                    className="pointer-events-none absolute inset-x-0 top-0 h-44"
                    style={{ background: 'radial-gradient(70% 100% at 50% 0%, color-mix(in srgb, var(--showdown-blue) 16%, transparent), transparent 72%)' }}
                />

                <div className="relative flex flex-col items-center gap-5">
                    <SimDiceRoll />

                    <div className="text-center">
                        <p className="flex items-center justify-center gap-2 text-[15px] font-bold text-primary">
                            Playing the season
                            <BetaBadge />
                        </p>
                        <p className="text-[13px] text-secondary">{teamName}</p>
                    </div>

                    <div className="flex w-full max-w-sm flex-col gap-2">
                        <div className="flex items-baseline justify-between gap-3">
                            {/* Keyed so each new phase crossfades in rather than swapping text in place. */}
                            <span key={phase} className="fade-in flex min-w-0 items-center gap-1.5 text-[12px] font-semibold text-secondary">
                                <span className="live-pulse h-1.5 w-1.5 shrink-0 rounded-full bg-(--showdown-blue)" />
                                <span className="truncate">{phase}</span>
                            </span>
                            <span className="shrink-0 text-[12px] font-bold tabular-nums text-primary">{Math.round(pct)}%</span>
                        </div>

                        <div className="h-2.5 overflow-hidden rounded-full bg-(--background-quaternary)">
                            <div
                                className="sim-progress-sheen relative h-full overflow-hidden rounded-full bg-(--showdown-blue) transition-[width] duration-700 ease-out"
                                style={{
                                    width: `${pct}%`,
                                    boxShadow: '0 0 10px color-mix(in srgb, var(--showdown-blue) 55%, transparent)',
                                }}
                            />
                        </div>

                        {/* Fixed height: the game count only exists once games start, and letting
                            it appear would otherwise shunt the whole panel up mid-run. */}
                        <p className="h-[15px] text-right text-[11px] tabular-nums text-tertiary">
                            {total > 0 ? `${completed.toLocaleString()} / ${total.toLocaleString()} games` : ''}
                        </p>
                    </div>
                </div>
            </div>

            <div className="w-full max-w-lg">
                <SectionCard title={latest ? `Win % Over Time · ${latest.wins}–${latest.losses}` : 'Win % Over Time'}>
                    <SimWinPctChart games={timeline} totalGames={job?.progress_games_total} seedRecord={seedRecord} />
                </SectionCard>
            </div>

            <SimEngineExplainer />

            <div className="flex flex-col items-center gap-2">
                <p className="text-[11px] text-tertiary">This usually takes under a minute.</p>

                {onCancel && (
                    <button
                        type="button"
                        onClick={onCancel}
                        className="cursor-pointer text-[11px] font-semibold text-tertiary underline underline-offset-2 transition-colors hover:text-primary"
                    >
                        Cancel simulation
                    </button>
                )}
            </div>
        </div>
    );
}
