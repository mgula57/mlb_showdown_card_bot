/** A single labeled stat value — the small "KPI" tile shared by the season summary tab and the
 * batting/pitching tables (team totals shown above each roster). */
export function KpiTile({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-lg flex flex-col items-center bg-(--background-secondary) px-3 py-2">
            <p className="text-[11px] text-(--text-tertiary)">{label}</p>
            <p className="text-[18px] font-bold text-(--text-primary) tabular-nums">{value}</p>
        </div>
    );
}
