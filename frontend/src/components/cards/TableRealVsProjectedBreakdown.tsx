/**
 * @fileoverview TableRealVsProjected - Statistical accuracy comparison table
 * 
 * Displays side-by-side comparison of real player statistics versus 
 * projected card performance, showing how accurately the generated card
 * would reproduce the player's actual statistical output.
 */

import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type RealVsProjectedStat } from "../../api/showdownBotCard";
import { formatStatValue } from "../../functions/formatters";

const h = createColumnHelper<RealVsProjectedStat>();

/**
 * Column definitions for the real vs projected statistics table
 * 
 * Columns include:
 * - Stat: Statistical category with data quality indicators
 * - Real: Player's actual statistical performance
 * - Bot: Card's projected statistical performance
 * - Diff: Difference between projected and real (with directional indicator)
 */
const realVsProjectedStatColumns: ColumnDef<RealVsProjectedStat, any>[] = [
    h.accessor("stat", { 
        header: "Stat",
        cell: info => {
            const value = info.getValue<string>();
            const isEstimated = info.row.original.is_real_estimated;
            const isProjectedCorrection = info.row.original.is_projected_correction;
            // Add indicators: * = estimated real value, ** = projected with corrections
            return `${value}${isEstimated ? "*" : ""}${isProjectedCorrection ? "**" : ""}`;
        }
    }),
    h.accessor("real", {
        header: "Real",
        cell: info => formatStatValue(info.getValue(), info.row.getValue<string>("stat"))
    }),
    h.accessor("projected", {
        header: "Bot",
        cell: info => formatStatValue(info.getValue(), info.row.getValue<string>("stat"))
    }),
    h.accessor("diff_str", {
        header: "Diff",
    }),
];

/**
 * Props for the TableRealVsProjected component
 */
type TableRealVsProjectedProps = {
    /** Array of statistical comparisons to display */
    realVsProjectedData: RealVsProjectedStat[];
    /** Optional CSS classes for styling */
    className?: string;
};

/**
 * TableRealVsProjected - Statistical accuracy comparison table
 * 
 * Provides a detailed breakdown comparing a player's real-world statistical
 * performance against what the generated Showdown card would produce in simulation.
 * 
 * **Key Features:**
 * - **Real vs Projected**: Side-by-side comparison of actual vs simulated stats
 * - **Accuracy Indicators**: Shows data quality and estimation methods used
 * - **Difference Tracking**: Highlights areas where the card over/under performs
 * - **Formatted Display**: Appropriate formatting for different stat types
 * 
 * **Data Quality Indicators:**
 * - `*` = Real value is estimated (limited sample size)
 * - `**` = Projected value includes accuracy corrections
 * 
 * This table helps evaluate how well the card generation algorithm captured
 * the player's actual performance profile.
 * 
 * @param realVsProjectedData - Statistical comparison data
 * @param className - Additional CSS classes
 * 
 * @example
 * ```tsx
 * <TableRealVsProjected 
 *   realVsProjectedData={card.real_vs_projected_stats}
 *   className="mt-4"
 * />
 * ```
 */
export function TableRealVsProjected({ realVsProjectedData, className }: TableRealVsProjectedProps) {

    return (
        <BasicDataTable 
            data={realVsProjectedData}
            columns={realVsProjectedStatColumns}
            className={className}
        />
    );
}