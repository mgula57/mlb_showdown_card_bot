import React from 'react';
import { FaCheckCircle, FaRegCircle } from 'react-icons/fa';

/** Props for the FormEnabler component */
type FormEnablerProps = {
    label: string;
    isEnabled: boolean;
    onChange: (isEnabled: boolean) => void;
    className?: string; // Optional className for additional styling
};

/** 
 * FormEnabler component for toggling a form element's enabled state.
 * Displays a button that can be clicked to enable/disable the form element.
 */
const FormEnabler: React.FC<FormEnablerProps> = ({ label, isEnabled, onChange, className = "" }) => {

    return (
        <button 
            type="button"
            className={`
                flex items-center gap-2
                rounded-lg p-2 
                font-semibold
                cursor-pointer
                text-base md:text-sm xl:text-base
                ${isEnabled ? 'text-green-500' : 'text-gray-400 border-gray-200'}
                ${isEnabled ? 'border-green-500 border-1' : 'border border-form-element'}
                ${className}
            `} 
            onClick={() => onChange(isEnabled)}
        >
            {/* Show a checkmark or a circle based on the enabled state */}
            {isEnabled ? <FaCheckCircle /> : <FaRegCircle />}
            {label}
        </button>
    );
}

export default FormEnabler;