import { FaSpinner } from 'react-icons/fa6';
import type { SimJob } from '../../../api/sim';
import { SimEngineExplainer } from './SimEngineExplainer';

type Props = {
    job: SimJob | null;
    teamName: string;
};

// Setup phases (see `_friendly_phase` in `api/sim.py`) report no game counts, so the bar would
// otherwise sit at 0% through all of card loading and schedule building. Stepping it through a
// few small ticks gives a sense of motion without implying real progress toward the games total.
const SETUP_PHASES = ['Starting simulation', 'Loading players', 'Building the schedule', 'Setting up teams'];
const SETUP_MAX_PCT = 8;

/**
 * Progress while a season runs. Setup (card loading, schedule, rosters) reports a phase with no
 * game counts, so the bar ticks through minor fixed increments until games start.
 */
export function SimProgress({ job, teamName }: Props) {
    const total = job?.games_total ?? 0;
    const completed = job?.games_completed ?? 0;
    const phase = job?.phase ?? 'Starting simulation';

    const setupIndex = SETUP_PHASES.indexOf(phase);
    const setupPct = setupIndex >= 0 ? ((setupIndex + 1) / SETUP_PHASES.length) * SETUP_MAX_PCT : SETUP_MAX_PCT / 2;
    const pct = total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : setupPct;

    return (
        <div className="flex flex-col items-center justify-center gap-4 py-16 px-4">
            <FaSpinner className="animate-spin text-(--text-tertiary) text-2xl" />
            <div className="text-center">
                <p className="text-[15px] font-bold text-(--text-primary)">Playing the season</p>
                <p className="text-[13px] text-(--text-secondary)">{teamName}</p>
            </div>

            <div className="w-full max-w-sm flex flex-col gap-1.5">
                <div className="h-2 rounded-full bg-(--background-tertiary) overflow-hidden">
                    <div
                        className="h-full bg-(--showdown-blue) transition-[width] duration-500 ease-out"
                        style={{ width: `${pct}%` }}
                    />
                </div>
                <div className="flex justify-between text-[11px] text-(--text-tertiary)">
                    <span>{phase}</span>
                    {total > 0 && <span>{completed.toLocaleString()} / {total.toLocaleString()} games</span>}
                </div>
            </div>

            <p className="text-[11px] text-(--text-tertiary)">This usually takes under a minute.</p>

            <SimEngineExplainer />
        </div>
    );
}
