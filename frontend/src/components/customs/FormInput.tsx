import React from "react";
import { FaXmark } from "react-icons/fa6";

/** Props for the form input component */
type FormInputProps = {
    label: string;
    value: string;
    onChange: (value: string) => void;
    className?: string;
    type?: string;
    isClearable?: boolean;
};

/** 
 * FormInput component for text input fields with a label.
 * Handles changes and updates the parent state.
 */
const FormInput: React.FC<FormInputProps> = ({ label, value, onChange, className = "", type="text", isClearable=false }) => {
    return (
        <div className={`${className}`}>
            {/* Label */}
            <label className="text-sm font-medium text-secondary">{label}</label>

            {/* Input Container */}
            <div className="flex items-stretch focus:outline-none border border-form-element rounded-xl mt-1">
                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    className={`
                        w-full py-2 pl-2 ${ isClearable ? 'pr-0' : 'pr-2' }
                        rounded-xl border-form-element
                        focus:outline-none
                    `}
                />

                {/* Optional Clear button */}
                {isClearable && (
                    <button
                        type="button"
                        onClick={() => onChange("")}
                        className="
                            ml-2 px-2 py-2
                            border-l border-form-element
                            cursor-pointer 
                        "
                    >
                        <FaXmark className="text-gray-500" />
                    </button>
                )}
            </div>
            
        </div>
    );
}

export default FormInput;