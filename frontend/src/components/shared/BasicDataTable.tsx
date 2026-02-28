/**
 * @fileoverview BasicDataTable Component
 * 
 * A reusable data table component built on TanStack Table that provides sorting,
 * custom styling, and row interaction capabilities. Features include:
 * - Sortable columns with visual indicators
 * - Custom column styling via meta className
 * - Configurable empty state display
 * - Optional row click handling
 * - Responsive design with scrolling
 * - Consistent theming with CSS variables
 * 
 * @component
 * @example
 * ```tsx
 * <BasicDataTable
 *   data={players}
 *   columns={[
 *     { accessorKey: 'name', header: 'Player Name' },
 *     { accessorKey: 'position', header: 'Position' }
 *   ]}
 *   onRowClick={(player) => console.log(player)}
 *   initialSorting={[{ id: 'name', desc: false }]}
 * />
 * ```
 */

import React from "react";
import {
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    flexRender,
    type ColumnDef,
    type SortingState,
} from "@tanstack/react-table";

// Extend TanStack Table's ColumnMeta interface to support custom CSS classes
declare module "@tanstack/react-table" {
    interface ColumnMeta<TData, TValue> {
        /** Optional CSS class name to apply to column cells */
        className?: string;
    }
}

/**
 * Props for the BasicDataTable component
 * @template TData - The type of data objects in the table rows
 */
export type BasicDataTableProps<TData> = {
    /** Array of data objects to display in the table */
    data: TData[];
    /** Column definitions including headers, accessors, and rendering */
    columns: ColumnDef<TData, any>[];
    /** Optional CSS class name for additional table styling */
    className?: string;
    /** Initial sorting state for the table */
    initialSorting?: SortingState;
    /** Custom content to display when table is empty */
    emptyState?: React.ReactNode;
    /** Optional callback function triggered when a row is clicked */
    onRowClick?: (row: TData) => void;
};

/**
 * A reusable data table component with sorting capabilities
 * 
 * This component provides a flexible table implementation with:
 * - Sortable columns with visual sort indicators (▲/▼)
 * - Custom empty state handling
 * - Row click interactions
 * - Responsive design with overflow scrolling
 * - Consistent styling with CSS variables
 * 
 * @template TData - The type of objects displayed in table rows
 * @param props - The component props
 * @returns A rendered data table with sorting and interaction capabilities
 */
export function BasicDataTable<TData>({ data, columns, className = "", initialSorting = [], emptyState = <div className="p-6 text-center text-sm opacity-70">No rows</div>, onRowClick }: BasicDataTableProps<TData>) {

    // Initialize sorting state with provided initial sorting configuration
    const [sorting, setSorting] = React.useState<SortingState>(initialSorting);

    // Configure TanStack Table with data, columns, and sorting capabilities
    const table = useReactTable({
        data,
        columns,
        state: { sorting },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(), // Core table functionality
        getSortedRowModel: getSortedRowModel(), // Enable column sorting
    });

    return (
        <div className={`overflow-scroll rounded-lg border-2 border-(--background-tertiary) ${className} text-sm`}>
            <table className="min-w-full">
                {/* Table Header with sortable columns */}
                <thead className="bg-table-header">
                    {table.getHeaderGroups().map(hg => (
                        <tr key={hg.id}>
                            {hg.headers.map(h => (
                                <th
                                    key={h.id}
                                    className={`px-3 py-2 text-left font-semibold select-none cursor-pointer ${h.column.columnDef.meta?.className || ''}`}
                                    onClick={h.column.getToggleSortingHandler()}
                                >
                                    <div className="flex items-center gap-2">
                                        {/* Render column header content */}
                                        {flexRender(h.column.columnDef.header, h.getContext())}
                                        {/* Display sort indicator based on current sort state */}
                                        <span className="text-xs opacity-70">
                                            {{
                                                asc: "▲",   // Ascending sort indicator
                                                desc: "▼",  // Descending sort indicator
                                            }[h.column.getIsSorted() as string] ?? ""}
                                        </span>
                                    </div>
                                </th>
                            ))}
                        </tr>
                    ))}
                </thead>
                <tbody>
                    {/* Handle empty state when no data is available */}
                    {table.getRowModel().rows.length === 0 ? (
                        <tr>
                            <td colSpan={table.getAllLeafColumns().length}>{emptyState}</td>
                        </tr>
                    ) : (
                        // Render data rows with alternating background colors and optional click handling
                        table.getRowModel().rows.map(r => (
                            <tr 
                                key={r.id} 
                                className={`
                                    odd:bg-(--table-banding)
                                    ${onRowClick ? 'cursor-pointer' : ''}
                                `}
                                onClick={() => onRowClick?.(r.original)}
                            >
                                {/* Render each cell in the row */}
                                {r.getVisibleCells().map(c => (
                                    <td key={c.id} className={`px-3 py-2 ${c.column.columnDef.meta?.className || ''}`}>
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