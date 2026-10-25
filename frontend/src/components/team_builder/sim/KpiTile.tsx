import { FaCaretUp, FaCaretDown, FaMinus } from 'react-icons/fa6';
import { InfoTooltip } from '../../shared/InfoTooltip';
import type { KpiComparison } from './simStatColumns';

/** A single labeled stat value — the small "KPI" tile shared by the season summary tab and the
 * batting/pitching tables (team totals shown above each roster). `info` adds a click-to-reveal
 * tooltip for values that need more explanation than the label alone gives (e.g. a "100 =
 * average" index). `comparison` renders a BI-style up/down indicator against the league average
 * below the value, colored by whether that direction is favorable for the stat (e.g. up is good
 * for OPS, but down is good for ERA). */
export function KpiTile({ label, value, info, comparison }: { label: string; value: string; info?: string; comparison?: KpiComparison }) {
    return (
        <div className="rounded-card flex flex-col items-center border border-(--divider) bg-(--background-secondary) px-3 py-2">
            <div className="flex items-center gap-1">
                <p className="text-[11px] text-(--text-tertiary)">{label}</p>
                {info && <InfoTooltip text={info} />}
            </div>
            <p className="text-[18px] font-bold text-(--text-primary) tabular-nums">{value}</p>
            {comparison && (
                <p className={`flex items-center gap-0.5 text-[10px] font-semibold tabular-nums ${
                    comparison.direction === 'flat' ? 'text-(--text-tertiary)' : comparison.isGood ? 'text-(--green)' : 'text-(--red)'
                }`}>
                    {comparison.direction === 'up' && <FaCaretUp className="text-[12px]" />}
                    {comparison.direction === 'down' && <FaCaretDown className="text-[12px]" />}
                    {comparison.direction === 'flat' && <FaMinus className="text-[8px]" />}
                    {comparison.label}
                </p>
            )}
        </div>
    );
}
