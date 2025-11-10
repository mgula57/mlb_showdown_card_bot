/**
 * @fileoverview FormEnabler - Toggle button form component
 * 
 * Provides a visual toggle button for boolean form options with checkmark icons
 * and dynamic styling. Used for enabling/disabling features in the card builder
 * such as borders, dark mode, or special effects.
 */

import React from 'react';
import { FaCheckCircle, FaRegCircle } from 'react-icons/fa';

/**
 * Props for the FormEnabler component
 */
type FormEnablerProps = {
    /** Display label for the toggle option */
    label: string;
    /** Current enabled/disabled state */
    isEnabled: boolean;
    /** Callback function when toggle state changes */
    onChange: (isEnabled: boolean) => void;
    /** Optional CSS class names for additional styling */
    className?: string;
};

/**
 * FormEnabler - Visual toggle button for boolean form options
 * 
 * Creates an interactive button that displays the current state with icons
 * (checkmark for enabled, circle for disabled) and dynamic styling. Provides
 * immediate visual feedback for boolean settings in the card customization.
 * 
 * @example
 * ```tsx
 * <FormEnabler
 *   label="Add Border"
 *   isEnabled={form.is_bordered}
 *   onChange={(enabled) => setForm({ ...form, is_bordered: enabled })}
 * />
 * ```
 * 
 * @param label - Text displayed next to the toggle icon
 * @param isEnabled - Current boolean state
 * @param onChange - Toggle state change handler
 * @param className - Additional styling classes
 * @returns Interactive toggle button component
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
            {/* Toggle icon - checkmark when enabled, empty circle when disabled */}
            {isEnabled ? <FaCheckCircle /> : <FaRegCircle />}
            {label}
        </button>
    );
}

export default FormEnabler;