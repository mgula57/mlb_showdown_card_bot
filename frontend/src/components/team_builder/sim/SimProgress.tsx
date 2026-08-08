import { FaSpinner } from 'react-icons/fa6';
import type { SimJob } from '../../../api/sim';

type Props = {
    job: SimJob | null;
    teamName: string;
};

/**
 * Progress while a season runs. Setup (card loading, schedule, rosters) reports a phase with no
 * game counts, so the bar only appears once games start.
 */
export function SimProgress({ job, teamName }: Props) {
    const total = job?.games_total ?? 0;
    const completed = job?.games_completed ?? 0;
    const pct = total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : 0;
    const phase = job?.phase ?? 'Starting simulation';

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
        </div>
    );
}
