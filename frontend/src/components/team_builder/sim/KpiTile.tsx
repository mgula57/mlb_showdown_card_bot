import { InfoTooltip } from '../../shared/InfoTooltip';

/** A single labeled stat value — the small "KPI" tile shared by the season summary tab and the
 * batting/pitching tables (team totals shown above each roster). `info` adds a click-to-reveal
 * tooltip for values that need more explanation than the label alone gives (e.g. a "100 =
 * average" index). */
export function KpiTile({ label, value, info }: { label: string; value: string; info?: string }) {
    return (
        <div className="rounded-lg flex flex-col items-center border border-(--divider) bg-linear-to-b from-(--background-secondary) to-(--background-primary) px-3 py-2 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]">
            <div className="flex items-center gap-1">
                <p className="text-[11px] text-(--text-tertiary)">{label}</p>
                {info && <InfoTooltip text={info} />}
            </div>
            <p className="text-[18px] font-bold text-(--text-primary) tabular-nums">{value}</p>
        </div>
    );
}
