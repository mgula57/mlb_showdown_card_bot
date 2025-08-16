import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { BasicDataTable } from "../shared/BasicDataTable";
import { type RealVsProjectedStat } from "../../api/showdownBotCard";
import { formatStatValue } from "../../functions/formatters";

const h = createColumnHelper<RealVsProjectedStat>();

/** Create a column helper that tells tanstack the format of the data*/
const realVsProjectedStatColumns: ColumnDef<RealVsProjectedStat, any>[] = [
    h.accessor("stat", { header: "Stat" }),
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

type TableRealVsProjectedProps = {
    realVsProjectedData: RealVsProjectedStat[];
    className?: string;
};

export function TableRealVsProjected({ realVsProjectedData, className }: TableRealVsProjectedProps) {

    return (
        <BasicDataTable 
            data={realVsProjectedData}
            columns={realVsProjectedStatColumns}
            className={className}
        />
    );
}