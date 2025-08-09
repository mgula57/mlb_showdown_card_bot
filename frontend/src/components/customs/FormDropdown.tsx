import React from "react";
import { CustomSelect, type SelectOption } from "../shared/CustomSelect";

/** Props for the form dropdown component */
type FormDropdownProps = {
    label: string;
    options: SelectOption[];
    selectedOption: string;
    onChange: (value: string) => void;
};

/** 
 * FormDropdown component for selecting an option from a dropdown list.
 * Handles changes and updates the parent state.
 */
const FormDropdown: React.FC<FormDropdownProps> = ({ label, options, selectedOption, onChange }) => {
    return (
        <div>
            {/* Label */}
            <label className="text-sm font-medium text-secondary">{label}</label>

            {/* Custom Select Dropdown */}
            <CustomSelect
                value={selectedOption}
                onChange={onChange}
                options={options}
            />
        </div>
    );
}

export default FormDropdown;