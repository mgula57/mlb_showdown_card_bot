import React from "react";
import {
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    flexRender,
    type ColumnDef,
    type SortingState,
} from "@tanstack/react-table";

export type BasicDataTableProps<TData> = {
    data: TData[];
    columns: ColumnDef<TData, any>[];
    className?: string;
    initialSorting?: SortingState;
    emptyState?: React.ReactNode;
};

export function BasicDataTable<TData>({ data, columns, className = "", initialSorting = [], emptyState = <div className="p-6 text-center text-sm opacity-70">No rows</div> }: BasicDataTableProps<TData>) {
    
    // State for sorting
    const [sorting, setSorting] = React.useState<SortingState>(initialSorting);

    const table = useReactTable({
        data,
        columns,
        state: { sorting },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
    });

    return (
        <div className={`overflow-auto rounded-lg border border-gray-700 ${className}`}>
            <table className="min-w-full text-sm">
                <thead className="bg-table-header">
                    {table.getHeaderGroups().map(hg => (
                        <tr key={hg.id}>
                            {hg.headers.map(h => (
                                <th
                                    key={h.id}
                                    className="px-3 py-2 text-left font-semibold select-none cursor-pointer"
                                    onClick={h.column.getToggleSortingHandler()}
                                >
                                    <div className="flex items-center gap-2">
                                        {flexRender(h.column.columnDef.header, h.getContext())}
                                        <span className="text-xs opacity-70">
                                            {{
                                                asc: "▲",
                                                desc: "▼",
                                            }[h.column.getIsSorted() as string] ?? ""}
                                        </span>
                                    </div>
                                </th>
                            ))}
                        </tr>
                    ))}
                </thead>
                <tbody>
                    {table.getRowModel().rows.length === 0 ? (
                        <tr>
                            <td colSpan={table.getAllLeafColumns().length}>{emptyState}</td>
                        </tr>
                    ) : (
                        table.getRowModel().rows.map(r => (
                            <tr key={r.id} className="odd:bg-gray-900">
                                {r.getVisibleCells().map(c => (
                                    <td key={c.id} className="px-3 py-2">
                                        {flexRender(c.column.columnDef.cell, c.getContext())}
                                    </td>
                                ))}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
}