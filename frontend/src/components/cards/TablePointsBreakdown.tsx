/**
 * @fileoverview TablePointsBreakdown - Point value calculation analysis table
 * 
 * Displays detailed breakdown of how a card's point value is calculated,
 * showing contribution from each statistical category and mathematical
 * adjustments applied during the point value algorithm.
 */

import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type PointsCategoryBreakdown, type PointsBreakdown } from "../../api/showdownBotCard";
import { formatStatValue, formatAsPct } from "../../functions/formatters";

const h = createColumnHelper<PointsCategoryBreakdown>();

/**
 * Column definitions for the points breakdown table
 * 
 * Displays statistical categories with readable aliases and appropriate
 * formatting for different value types (percentages, multipliers, etc.)
 */
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

/**
 * Props for the TablePointsBreakdown component
 */
type TablePointsBreakdownProps = {
    /** Complete points breakdown data from card generation */
    pointsBreakdownData: PointsBreakdown | null;
    /** Innings pitched value for pitcher multiplier calculations */
    ip?: number | null;
    /** Optional CSS classes for styling */
    className?: string;
};

/**
 * TablePointsBreakdown - Point value calculation analysis table
 * 
 * Provides detailed breakdown of how a card's total point value is calculated
 * by showing the contribution from each statistical category. Includes special
 * rows for mathematical adjustments like IP multipliers and decay rates.
 * 
 * **Features:**
 * - **Category Contributions**: Points earned from each statistical category
 * - **Percentile Rankings**: Player's percentile rank in each category
 * - **Mathematical Adjustments**: IP multipliers, decay rates, etc.
 * - **Total Calculation**: Final point value with all adjustments
 * 
 * **Special Rows:**
 * - `IPx`: Innings pitched multiplier for pitchers
 * - `DECAY`: Point decay for extremely high values
 * - `TOTAL`: Final calculated point value
 * 
 * Categories are sorted by point contribution (highest first) to show
 * which aspects of the player's performance drive their overall value.
 * 
 * @param pointsBreakdownData - Complete points calculation data
 * @param ip - Innings pitched for multiplier calculations
 * @param className - Additional CSS classes
 * 
 * @example
 * ```tsx
 * <TablePointsBreakdown 
 *   pointsBreakdownData={card.points_breakdown}
 *   ip={card.ip}
 *   className="mt-4"
 * />
 * ```
 */
export function TablePointsBreakdown({ pointsBreakdownData, ip, className }: TablePointsBreakdownProps) {
    /**
     * Convert points breakdown object to array format for table display
     * Sorted by point contribution (descending) to highlight most valuable categories
     */
    const pointsCategoryBreakdowns = Object.entries(pointsBreakdownData?.breakdowns || {})
        .map(([key, breakdown]) => ({ ...breakdown, metric: key }))
        .sort((a, b) => b.points - a.points);

    /**
     * Add IP multiplier row for pitchers if different from default (1.0)
     * Shows how innings pitched affects the final point calculation
     */
    const ip_multiplier = pointsBreakdownData?.ip_multiplier || 1.0;
    if (ip_multiplier !== 1.0) {
        const ipRow: PointsCategoryBreakdown = {
            metric: "IPx",
            value: ip || 0,
            points: ip_multiplier,
        };
        pointsCategoryBreakdowns.push(ipRow);
    }

    /**
     * Add decay rate row if point decay is applied
     * Shows penalty for extremely high statistical values to maintain game balance
     */
    const decayRate = pointsBreakdownData?.decay_rate || 1.0;
    if (decayRate !== 1.0) {
        const decayRateRow: PointsCategoryBreakdown = {
            metric: "DECAY",
            value: decayRate,
            points: pointsBreakdownData?.decay_start || 0,
        };
        pointsCategoryBreakdowns.push(decayRateRow);
    }

    /**
     * Calculate and add total points row
     * Sum of all individual category contributions
     */
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