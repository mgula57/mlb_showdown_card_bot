import type { AlgorithmPositionTarget } from '../../api/releases';
import { POSITION_LABELS, allocateCounts } from './positionTargets';
import { CAPS_LABEL_CLASS } from '../shared/fieldStyles';

type PositionTargetsTableProps = {
    targets: AlgorithmPositionTarget[];
    setSize: number;
    onClear: () => void;
};

export default function PositionTargetsTable({ targets, setSize, onClear }: PositionTargetsTableProps) {
    const counts = allocateCounts(targets, setSize);

    return (
        <div className="flex flex-col gap-2">
            <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 gap-y-0.5 text-[12px]">
                <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Position</span>
                <span className={`text-right ${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Cards</span>
                <span className={`text-right ${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>Avg PTS</span>
                {targets.map((target, index) => (
                    <div key={target.position} className="contents">
                        <span className="font-semibold text-(--text-secondary)">{POSITION_LABELS[target.position] ?? target.position}</span>
                        <span className="font-bold text-(--text-primary) text-right tabular-nums">{counts[index]}</span>
                        <span className="text-(--text-secondary) text-right tabular-nums">{target.avg_points ?? '—'}</span>
                    </div>
                ))}
            </div>

            <div className="flex items-center justify-between gap-2">
                <p className="text-[11px] text-(--text-tertiary)">
                    Scaled to set size. Positions short on qualified players borrow multi-position players, then any hitter or pitcher.
                </p>
                <button
                    type="button"
                    onClick={onClear}
                    className="shrink-0 px-2.5 py-1.5 rounded-control border border-(--divider) text-[12px] font-semibold
                        text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--background-secondary) transition-colors cursor-pointer"
                >
                    Clear
                </button>
            </div>
        </div>
    );
}
