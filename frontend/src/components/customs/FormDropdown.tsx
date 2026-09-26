/**
 * @fileoverview FormDropdown - Reusable dropdown form component
 * 
 * Provides a standardized dropdown interface for form inputs with consistent
 * styling and behavior. Wraps the CustomSelect component with form-specific
 * labeling and layout, commonly used throughout the card customization interface.
 */

import { type ReactNode } from "react";
import CustomSelect, { type CustomSelectProps } from "../shared/CustomSelect";

/**
 * Props for the FormDropdown component.
 * Inherits every CustomSelect prop (passed straight through) except `value`,
 * which is exposed as `selectedOption`, and `className`, which styles the
 * wrapper here — use `selectClassName` to target CustomSelect's container.
 */
type FormDropdownProps = Omit<CustomSelectProps, 'value' | 'className'> & {
    /** Display label for the dropdown field */
    label: ReactNode;
    /** Currently selected option value */
    selectedOption: string;
    /** Optional CSS class names for the wrapper element */
    className?: string;
    /** Optional CSS class names for the CustomSelect container */
    selectClassName?: string;
};

/**
 * FormDropdown - Standardized dropdown form component
 * 
 * Provides a consistent interface for dropdown selections throughout the custom
 * card builder. Handles option display, selection state, and change propagation
 * with proper form styling and accessibility.
 * 
 * @example
 * ```tsx
 * <FormDropdown
 *   label="Card Set"
 *   options={[
 *     { label: "Base Set", value: "BS" },
 *     { label: "Trading Deadline", value: "TD" }
 *   ]}
 *   selectedOption={form.expansion}
 *   onChange={(value) => setForm({ ...form, expansion: value })}
 * />
 * ```
 * 
 * @param label - Field label displayed above dropdown
 * @param options - Selectable options array
 * @param selectedOption - Current selection value
 * @param onChange - Selection change handler
 * @param className - Additional wrapper styling classes
 * @param selectClassName - Additional CustomSelect container classes
 * @param selectProps - Any remaining CustomSelect props, passed through
 * @returns Labeled dropdown form component
 */
const FormDropdown = ({ label, selectedOption, className = "", selectClassName, disabled = false, showDropdownArrow = true, ...selectProps }: FormDropdownProps) => {
    return (
        <div className={className}>
            {/* Form label with consistent styling */}
            <label className={`text-sm font-medium block ${disabled ? 'text-tertiary' : 'text-secondary'}`}>{label}</label>

            {/* Dropdown selection component */}
            <CustomSelect
                {...selectProps}
                value={selectedOption}
                className={selectClassName}
                disabled={disabled}
                showDropdownArrow={showDropdownArrow}
            />
        </div>
    );
}

export default FormDropdown;