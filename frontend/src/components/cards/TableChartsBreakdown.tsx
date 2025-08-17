import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type ChartAccuracyCategoryBreakdown } from "../../api/showdownBotCard";
import { formatSlashlineValue } from "../../functions/formatters";

/** 
 * Create a type that extends ChartAccuracyCategory breakdown with these columns
    - Chart: number 
*/
type ChartAccuracyCategoryBreakdownWithColumns = ChartAccuracyCategoryBreakdown & {
    chart: string;
};


const h = createColumnHelper<ChartAccuracyCategoryBreakdownWithColumns>();

/** Create a column helper that tells tanstack the format of the data*/
const chartAccuracyCategoryBreakdownColumns: ColumnDef<ChartAccuracyCategoryBreakdownWithColumns, any>[] = [
    h.accessor("chart", { header: "Version" }),
    h.accessor("accuracy", {
        header: "Score",
        cell: info => `${(info.getValue<number>() * 100).toFixed(2)}%`,
    }),
    h.accessor("comparison", {
        header: "Proj OPS",
        cell: info => formatSlashlineValue(info.getValue()),
    }),
    h.accessor("actual", {
        header: "Real OPS",
        cell: info => formatSlashlineValue(info.getValue()),
    }),
    h.accessor("notes", { header: "Notes" }),
];

type TableChartsBreakdownProps = {
    chartAccuracyData: Record<string, Record<string, ChartAccuracyCategoryBreakdown>>;
    className?: string;
};

export function TableChartsBreakdown({ chartAccuracyData, className }: TableChartsBreakdownProps) {

    // chartAccuracyData: { [chart: string]: { [key: string]: ChartAccuracyCategoryBreakdown } }
    // Keep only entries where inner item.stat === "OVERALL", and add outer key as `chart`
    // Limit to Top 5 based on accuracy
    const overallData: ChartAccuracyCategoryBreakdownWithColumns[] = Object
        .entries(chartAccuracyData) // [chart, perStatRecord][]
        .flatMap(([chart, perStatRecord]) =>
            Object.entries(perStatRecord) // [key, item][]
                .filter(([, item]) => item.stat.toUpperCase() === "OVERALL")
                .map(([, item]) => ({ ...item, chart }))
        )
        .sort((a, b) => b.accuracy - a.accuracy) // Sort by accuracy descending
        .slice(0, 5) // Limit to Top 5
        .map((row, i) => ({ ...row, chart: `${i + 1}. ${row.chart}` }));

    return (
        <BasicDataTable 
            data={overallData}
            columns={chartAccuracyCategoryBreakdownColumns}
            className={className}
        />
    );
}