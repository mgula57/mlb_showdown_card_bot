/**
 * @fileoverview TableOpponentBreakdown - Chart outcome analysis table
 * 
 * Displays breakdown of MLB Showdown card chart outcomes, showing the expected
 * values for different result categories (hits, walks, outs, etc.) when this
 * card faces opponents. Used to analyze card balance and performance expectations.
 */

import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type ShowdownBotCardChart } from "../../api/showdownBotCard";

/**
 * Chart outcome category with its expected value
 */
type ChartValue = {
    /** Outcome category name (e.g., "1B", "BB", "SO") */
    category: string;
    /** Number of results for this outcome */
    value: number;
}

/** TanStack table column helper for type-safe column definitions */
const h = createColumnHelper<ChartValue>();

/**
 * Column definitions for chart breakdown table
 * Shows outcome categories and their statistical values
 */
const chartAccuracyCategoryBreakdownColumns: ColumnDef<ChartValue, any>[] = [
    h.accessor("category", { header: "Category" }), // Outcome type
    h.accessor("value", {
        header: "Value", // Expected frequency/impact
        cell: info => `${(info.getValue<number>()).toFixed(2)}`,
    }),
];

/**
 * Props for TableOpponentBreakdown component
 */
type TableOpponentBreakdownProps = {
    /** MLB Showdown card chart data to analyze */
    chart?: ShowdownBotCardChart;
    /** Optional CSS class name for styling */
    className?: string;
};

/**
 * TableOpponentBreakdown - Displays chart outcome analysis
 * 
 * Shows breakdown of expected outcomes when this MLB Showdown card faces opponents,
 * including command rating, outs, and all possible result categories. Results are
 * ordered logically for easy analysis of card performance characteristics.
 * 
 * @param chart - Card chart data with outcome values
 * @param className - Optional styling class
 * @returns Table component showing chart outcome breakdown
 */
export function TableOpponentBreakdown({ chart, className }: TableOpponentBreakdownProps) {

    /**
     * Extract and organize chart outcome values with command/outs
     * Combines command rating, outs, and all result categories into sorted list
     * @returns Sorted array of chart outcome categories and values
     */
    const getChartValues = (): ChartValue[] => {
        const allRecords: ChartValue[] = [];

        // Add foundational chart stats (command rating and outs)
        allRecords.push({ 
            category: chart?.is_pitcher ? "Control" : "Onbase", 
            value: chart?.command || 0 
        });
        allRecords.push({ category: "Outs", value: chart?.outs || 0 });

        // Add all specific outcome categories from chart values
        for (const [category, value] of Object.entries(chart?.values || {})) {
            allRecords.push({ category, value });
        }
        
        // Sort by logical game order for easy analysis
        const categorySortOrder = [
            "Control", "Onbase", "Outs", "PU", "SO", "GB", "FB", 
            "BB", "1B", "1B+", "2B", "3B", "HR"
        ];
        return allRecords.sort((a, b) => 
            categorySortOrder.indexOf(a.category) - categorySortOrder.indexOf(b.category)
        );
    };

    return (
        <BasicDataTable
            data={getChartValues()}
            columns={chartAccuracyCategoryBreakdownColumns}
            className={className}
        />
    );
}