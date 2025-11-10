/**
 * @fileoverview TableChartsBreakdown - Chart version comparison table component
 * 
 * Displays accuracy analysis comparing different MLB Showdown card chart versions,
 * showing projected vs actual OPS values and accuracy scores for each chart variant.
 * Used to evaluate which chart configuration best matches real performance.
 */

import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type ChartAccuracyCategoryBreakdown } from "../../api/showdownBotCard";
import { formatSlashlineValue } from "../../functions/formatters";

/**
 * Extended chart accuracy data with display formatting
 * Adds chart identifier for table display
 */
type ChartAccuracyCategoryBreakdownWithColumns = ChartAccuracyCategoryBreakdown & {
    /** Chart version identifier (e.g., "2001", "2004") */
    chart: string;
};


/** TanStack table column helper for type-safe column definitions */
const h = createColumnHelper<ChartAccuracyCategoryBreakdownWithColumns>();

/**
 * Column definitions for chart comparison table
 * Displays chart versions, accuracy scores, and OPS comparisons
 */
const chartAccuracyCategoryBreakdownColumns: ColumnDef<ChartAccuracyCategoryBreakdownWithColumns, any>[] = [
    h.accessor("chart", { 
        header: "Version" // MLB Showdown chart version (2001, 2004, etc.)
    }),
    h.accessor("accuracy", {
        header: "Score", // How closely this chart matches real performance
        cell: info => `${(info.getValue<number>() * 100).toFixed(2)}%`,
    }),
    h.accessor("comparison", {
        header: "Proj OPS", // Projected OPS using this chart version
        cell: info => formatSlashlineValue(info.getValue()),
    }),
    h.accessor("actual", {
        header: "Real OPS", // Player's actual MLB OPS for comparison
        cell: info => formatSlashlineValue(info.getValue()),
    }),
    h.accessor("notes", { header: "Notes" }), // Additional context about chart version
];

/**
 * Props for TableChartsBreakdown component
 */
type TableChartsBreakdownProps = {
    /** Chart accuracy data organized by chart version and stat category */
    chartAccuracyData: Record<string, Record<string, ChartAccuracyCategoryBreakdown>>;
    /** Optional CSS class name for styling */
    className?: string;
};

/**
 * TableChartsBreakdown - Displays comparison of different MLB Showdown chart versions
 * 
 * Shows accuracy analysis for various chart configurations, ranking them by how well
 * they predict real MLB performance. Focuses on overall accuracy and displays the
 * top 5 performing chart versions.
 * 
 * @param chartAccuracyData - Nested accuracy data by chart version and stat
 * @param className - Optional styling class
 * @returns Table component comparing chart accuracy
 */
export function TableChartsBreakdown({ chartAccuracyData, className }: TableChartsBreakdownProps) {

    /**
     * Process chart accuracy data to show only overall performance
     * Filters to "OVERALL" stat category, ranks by accuracy, and adds position numbers
     */
    const overallData: ChartAccuracyCategoryBreakdownWithColumns[] = Object
        .entries(chartAccuracyData) // Extract [chart, perStatRecord] pairs
        .flatMap(([chart, perStatRecord]) =>
            Object.entries(perStatRecord) // Extract [key, item] pairs
                .filter(([, item]) => item.stat.toUpperCase() === "OVERALL")
                .map(([, item]) => ({ ...item, chart }))
        )
        .sort((a, b) => b.accuracy - a.accuracy) // Rank by accuracy (best first)
        .slice(0, 5) // Show top 5 performers only
        .map((row, i) => ({ ...row, chart: `${i + 1}. ${row.chart}` })); // Add ranking numbers

    return (
        <BasicDataTable 
            data={overallData}
            columns={chartAccuracyCategoryBreakdownColumns}
            className={className}
        />
    );
}