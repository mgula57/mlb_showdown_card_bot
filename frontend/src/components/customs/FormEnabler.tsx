import React from 'react';
import { FaCheckCircle, FaCircle } from 'react-icons/fa';

/** Props for the FormEnabler component */
type FormEnablerProps = {
    label: string;
    isEnabled: boolean;
    onChange: (isEnabled: boolean) => void;
};

/** 
 * FormEnabler component for toggling a form element's enabled state.
 * Displays a button that can be clicked to enable/disable the form element.
 */
const FormEnabler: React.FC<FormEnablerProps> = ({ label, isEnabled, onChange }) => {

    return (
        <button 
            type="button"
            className={`
                flex items-center gap-2
                rounded-lg p-2 
                font-semibold text-nowrap 
                ${isEnabled ? 'text-green-500' : 'text-gray-400 border-gray-200'}
                ${isEnabled ? 'border-green-500 border-1' : 'border border-form-element'}
            `} 
            onClick={() => onChange(isEnabled)}
        >
            {/* Show a checkmark or a circle based on the enabled state */}
            {isEnabled ? <FaCheckCircle /> : <FaCircle />}
            {label}
        </button>
    );
}

export default FormEnabler;