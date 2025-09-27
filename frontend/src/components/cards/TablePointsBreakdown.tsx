import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type PointsCategoryBreakdown, type PointsBreakdown } from "../../api/showdownBotCard";
import { formatStatValue, formatAsPct } from "../../functions/formatters";

const h = createColumnHelper<PointsCategoryBreakdown>();

/** Create a column helper that tells tanstack the format of the data*/
const pointsBreakdownColumns: ColumnDef<PointsCategoryBreakdown, any>[] = [
    h.accessor("metric", { 
        header: "Category",
        cell: info => {
            const originalValue = info.getValue<string>();
            if (originalValue.includes("DEFENSE") && !originalValue.includes("CLOSER")) {
                return originalValue.replace("DEFENSE", "DEF");
            }
            const mapMetricToAlias: Record<string, string> = {
                "AVERAGE": "BA*",
                "ONBASE": "OBP*",
                "SLUGGING": "SLG*",
                "HOME_RUNS": "HR*",
                "SPEED": "SPD",
                "DEFENSE-CLOSER": "CL BONUS",
                "OUT_DISTRIBUTION": "OUT DIST",
            };
            return mapMetricToAlias[originalValue] || originalValue;
        }
    }),
    h.accessor("value", {
        header: "Stat",
        cell: info => {
            const metric = info.row.getValue<string>("metric");
            const value = info.getValue<number>();

            // Return en dash if null
            if (value === null) {
                return '—'
            }

            // Handle special cases
            if (metric.includes("ICON")) {
                return '—'
            }
            if (metric == "DEFENSE-CLOSER") {
                return '—'
            }
            if (metric == "DECAY") {
                return `${value}x`
            }
            if (metric == "IPx") {
                return `IP ${value}`
            }
            if (metric.includes("DEFENSE") && value >= 0) {
                return `+${value}`
            }
            

            return formatStatValue(value, metric)
        }
    }),
    h.accessor("points", { 
        header: "Pts",
        cell: info => {
            const value = info.getValue<number>();
            const metric = info.row.getValue<string>("metric");

            // Handle special cases
            if (metric == "DECAY") {
                return `${value}+`
            }
            if (metric == "IPx") {
                return `${value}x`
            }
            return `${value.toFixed(0)}`
        }
    }),
    h.accessor("percentile", {
        header: "Pctile",
        cell: info => {
            const metric = info.row.getValue<string>("metric");
            const value = info.getValue<number>();

            // Return en dash if null
            if (value === null || Number.isNaN(value)) {
                return '—'
            }

            if (metric.includes("ICON")) {
                return '—'
            }
            if (["DEFENSE-CLOSER", "DECAY", "TOTAL", "IPx"].includes(metric)) {
                return '—'
            }
            return formatAsPct(value, 0);
        }
    }),
];

type TablePointsBreakdownProps = {
    pointsBreakdownData: PointsBreakdown | null;
    ip?: number | null;
    className?: string;
};

export function TablePointsBreakdown({ pointsBreakdownData, ip, className }: TablePointsBreakdownProps) {

    // Convert PointsBreakdown to list of Points Category Breakdowns
    const pointsCategoryBreakdowns = Object.entries(pointsBreakdownData?.breakdowns || {})
        .map(([key, breakdown]) => ({ ...breakdown, metric: key }))
        .sort((a, b) => b.points - a.points); // Sort by points descending

    // Add another row for IP multiplier if applicable
    // Use `ip` attribute in parent
    const ip_multiplier = pointsBreakdownData?.ip_multiplier || 1.0;
    if (ip_multiplier !== 1.0) {
        const ipRow: PointsCategoryBreakdown = {
            metric: "IPx",
            value: ip || 0,
            points: ip_multiplier,
        };
        pointsCategoryBreakdowns.push(ipRow);
    }

    // Add another row for `decay_rate`, stored in parent
    const decayRate = pointsBreakdownData?.decay_rate || 1.0;
    if (decayRate !== 1.0) {
        const decayRateRow: PointsCategoryBreakdown = {
            metric: "DECAY",
            value: decayRate,
            points: pointsBreakdownData?.decay_start || 0,
        };
        pointsCategoryBreakdowns.push(decayRateRow);
    }
    // Add total row
    const totalPoints = Object.entries(pointsBreakdownData?.breakdowns || {})
                                    .map(([key, breakdown]) => ({ ...breakdown, metric: key }))
                                    .reduce((sum, breakdown) => sum + (breakdown.points || 0), 0);
    const totalRow: PointsCategoryBreakdown = {
        metric: "TOTAL",
        value: null,
        points: totalPoints,
    };
    pointsCategoryBreakdowns.push(totalRow);

    return (
        <BasicDataTable 
            data={pointsCategoryBreakdowns}
            columns={pointsBreakdownColumns}
            className={className}
        />
    );
}