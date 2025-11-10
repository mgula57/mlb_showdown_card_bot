/**
 * @fileoverview RangeFilter - Numerical range filtering component
 * 
 * Provides a dual-input interface for setting minimum and maximum values for
 * numerical filtering. Features automatic number validation, clear functionality,
 * and consistent styling. Used for filtering datasets by numerical ranges like
 * years, statistics, or ratings.
 */

import FormInput from "./FormInput";
import { FaTimes } from "react-icons/fa";

/**
 * Props for the RangeFilter component
 */
type Props = {
    /** Display label for the range filter */
    label: string;
    /** Current minimum value (undefined if not set) */
    minValue?: number;
    /** Current maximum value (undefined if not set) */
    maxValue?: number;
    /** Callback when minimum value changes */
    onMinChange: (n?: number) => void;
    /** Callback when maximum value changes */
    onMaxChange: (n?: number) => void;
    /** Optional CSS class names for styling */
    className?: string;
};

/**
 * RangeFilter - Dual-input numerical range component
 * 
 * Creates a min/max input pair for filtering numerical data ranges. Provides
 * automatic number validation, clear button functionality, and consistent form
 * styling. Useful for filtering lists by numerical criteria like years, scores,
 * or statistical values.
 * 
 * @example
 * ```tsx
 * <RangeFilter
 *   label="Years Active"
 *   minValue={filters.minYear}
 *   maxValue={filters.maxYear}
 *   onMinChange={(min) => setFilters({ ...filters, minYear: min })}
 *   onMaxChange={(max) => setFilters({ ...filters, maxYear: max })}
 * />
 * ```
 * 
 * @param label - Field label displayed above inputs
 * @param minValue - Current minimum value
 * @param maxValue - Current maximum value
 * @param onMinChange - Minimum value change handler
 * @param onMaxChange - Maximum value change handler
 * @param className - Additional styling classes
 * @returns Range filter component with min/max inputs
 */
export default function RangeFilter({
    label,
    minValue,
    maxValue,
    onMinChange,
    onMaxChange,
    className
}: Props) {
    /**
     * Convert string input to number with validation
     * Returns undefined for invalid numbers
     */
    const toNum = (v?: string) => {
        const n = Number(v);
        return Number.isFinite(n) ? n : undefined;
    };

    /**
     * Clear both min and max values
     * Resets the range filter to empty state
     */
    const clear = () => {
        onMinChange(undefined);
        onMaxChange(undefined);
    };

    return (
        <div className="flex flex-col gap-1 border-1 p-2 rounded-xl border-form-element">
            {/* Header with label and clear button */}
            <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-secondary">{label}</label>
                {/* Clear button - only shown when values are set */}
                {(minValue !== undefined || maxValue !== undefined) && (
                    <button
                        type="button"
                        onClick={clear}
                        className="h-5 px-1 rounded-lg border border-form-element text-secondary hover:text-primary hover:border-primary"
                        title={`Clear ${label}`}
                    >
                        <FaTimes />
                    </button>
                )}
            </div>
            
            {/* Min/Max input pair */}
            <div className={`flex items-end gap-2 ${className || ""}`}>
                <div className="flex-1">
                    <FormInput
                        type="number"
                        inputMode="numeric"
                        label=''
                        placeholder="Min"
                        value={minValue?.toString() || ""}
                        onChange={(v) => onMinChange(toNum(v || undefined))}
                    />
                </div>
                <div className="flex-1">
                    <FormInput
                        type="number"
                        inputMode="numeric"
                        label=''
                        placeholder="Max"
                        value={maxValue?.toString() || ""}
                        onChange={(v) => onMaxChange(toNum(v || undefined))}
                    />
                </div>
            </div>
        </div>
    );
}