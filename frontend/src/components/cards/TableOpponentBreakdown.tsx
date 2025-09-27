import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type ShowdownBotCardChart } from "../../api/showdownBotCard";

type ChartValue = {
    category: string;
    value: number;
}
const h = createColumnHelper<ChartValue>();

/** Create a column helper that tells tanstack the format of the data*/
const chartAccuracyCategoryBreakdownColumns: ColumnDef<ChartValue, any>[] = [
    h.accessor("category", { header: "Category" }),
    h.accessor("value", {
        header: "Value",
        cell: info => `${(info.getValue<number>()).toFixed(2)}`,
    }),
];

type TableOpponentBreakdownProps = {
    chart?: ShowdownBotCardChart;
    className?: string;
};

export function TableOpponentBreakdown({ chart, className }: TableOpponentBreakdownProps) {

    // Add command and outs to chart values
    const getChartValues = (): ChartValue[] => {
        var allRecords: ChartValue[] = [];

        // Add command and outs first
        allRecords.push({ category: chart?.is_pitcher ? "Control" : "Onbase", value: chart?.command || 0 });
        allRecords.push({ category: "Outs", value: chart?.outs || 0 });

        for (const [category, value] of Object.entries(chart?.values || {})) {
            allRecords.push({ category, value });
        }
        // Sort by category name
        const categorySortOrder = ["Control", "Onbase", "Outs", "PU", "SO", "GB", "FB", "BB", "1B", "1B+", "2B", "3B", "HR",];
        return allRecords.sort((a, b) => categorySortOrder.indexOf(a.category) - categorySortOrder.indexOf(b.category));
    };

    return (
        <BasicDataTable
            data={getChartValues()}
            columns={chartAccuracyCategoryBreakdownColumns}
            className={className}
        />
    );
}