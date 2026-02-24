/**
 * @fileoverview FormDropdown - Reusable dropdown form component
 * 
 * Provides a standardized dropdown interface for form inputs with consistent
 * styling and behavior. Wraps the CustomSelect component with form-specific
 * labeling and layout, commonly used throughout the card customization interface.
 */

import { type SelectOption } from "../shared/CustomSelect";
import CustomSelect from "../shared/CustomSelect";

/**
 * Props for the FormDropdown component
 */
type FormDropdownProps = {
    /** Display label for the dropdown field */
    label: string;
    /** Array of selectable options with display and value properties */
    options: SelectOption[];
    /** Currently selected option value */
    selectedOption: string;
    /** Callback function when selection changes */
    onChange: (value: string) => void;
    /** Optional CSS class names for additional styling */
    className?: string;
    /** Whether this dropdown is disabled */
    disabled?: boolean;
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
 * @param className - Additional styling classes
 * @returns Labeled dropdown form component
 */
const FormDropdown = ({ label, options, selectedOption, onChange, className="", disabled = false }: FormDropdownProps) => {
    return (
        <div className={className}>
            {/* Form label with consistent styling */}
            <label className="text-sm font-medium text-secondary">{label}</label>

            {/* Dropdown selection component */}
            <CustomSelect
                value={selectedOption}
                onChange={onChange}
                options={options}
                disabled={disabled}
            />
        </div>
    );
}

export default FormDropdown;