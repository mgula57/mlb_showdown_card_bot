/**
 * @fileoverview FormInput - Versatile input form component
 * 
 * Provides a comprehensive input component supporting text, number, date, and file
 * inputs with features like clear buttons, title case formatting, and file upload
 * handling. Used throughout the custom card builder for various data entry needs.
 */

import React from "react";
import { FaXmark } from "react-icons/fa6";

/**
 * Props for the FormInput component
 */
type FormInputProps = {
    /** Display label for the input field */
    label: string;
    /** Current input value (text or number) */
    value: string | number;
    /** Callback function when input value changes */
    onChange?: (value: string | null) => void;
    /** Optional CSS class names for additional styling */
    className?: string;
    /** HTML input type (text, number, date, file, etc.) */
    type?: string;
    /** Mobile keyboard input mode hint */
    inputMode?: "text" | "search" | "email" | "tel" | "url" | "none" | "numeric" | "decimal" | undefined;
    /** Whether to show a clear button for resetting the field */
    isClearable?: boolean;
    /** Placeholder text when input is empty */
    placeholder?: string;
    /** Callback function for file upload handling */
    onChangeFile?: (file: File | null) => void;
    /** Whether to automatically format text in title case */
    isTitleCase?: boolean;
    /** Whether the input should be disabled */
    disabled?: boolean;
};

/**
 * FormInput - Multi-purpose input component with advanced features
 * 
 * Supports various input types including text, numbers, dates, and file uploads.
 * Provides optional features like clear buttons, title case formatting, and
 * specialized handling for different data types. Maintains consistent styling
 * and behavior across the form interface.
 * 
 * @example
 * ```tsx
 * // Text input with clear button
 * <FormInput
 *   label="Player Name"
 *   value={form.name}
 *   onChange={(value) => setForm({ ...form, name: value || '' })}
 *   isClearable={true}
 *   isTitleCase={true}
 * />
 * 
 * // File upload input
 * <FormInput
 *   label="Upload Image"
 *   type="file"
 *   value={form.image_upload?.name || ''}
 *   onChangeFile={(file) => setForm({ ...form, image_upload: file })}
 * />
 * ```
 * 
 * @param label - Field label displayed above input
 * @param value - Current input value
 * @param onChange - Text input change handler
 * @param className - Additional styling classes
 * @param type - HTML input type
 * @param inputMode - Mobile keyboard hint
 * @param isClearable - Show clear button option
 * @param placeholder - Empty state placeholder text
 * @param onChangeFile - File upload change handler
 * @param isTitleCase - Auto-format text in title case
 * @returns Versatile input component with label
 */
const FormInput: React.FC<FormInputProps> = ({ label, value, onChange, className = "", type="text", inputMode="text", isClearable=false, placeholder, onChangeFile, isTitleCase, disabled = false }) => {

    /** Check if this is a file upload input */
    const isFileInput = type === "file";

    /**
     * Handle file selection for upload inputs
     * Extracts the first selected file and passes it to the callback
     */
    const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!onChangeFile) return;
        const files = e.target.files;
        onChangeFile(files && files.length > 0 ? files[0] : null);
    };

    return (
        <div className={`${className}`}>
            {/* Form field label */}
            <label className="text-sm font-medium text-secondary">{label}</label>

            {/* Input container with border styling */}
            <div className="flex items-stretch focus:outline-none border-2 border-form-element rounded-xl mt-1">

                {/* File upload input with custom styling */}
                {isFileInput ? (
                    
                    <input
                        type="file"
                        accept="image/*"
                        multiple={false}
                        onChange={handleFile}
                        disabled={disabled}
                        className="
                            w-full py-2 pl-2 pr-2
                            rounded-xl
                            focus:outline-none
                            text-sm
                            file:mr-3 file:py-1 file:px-3
                            file:rounded-md file:border-0
                            file:bg-tertiary file:text-secondary
                            file:cursor-pointer
                        "
                        autoComplete="off"
                        spellCheck="false"
                    />
                ) : (
                    <>
                        {/* Standard text/number/date input */}
                        <input
                            type={type}
                            inputMode={inputMode}
                            value={value}
                            placeholder={placeholder}
                            autoComplete="off"
                            spellCheck="false"
                            onChange={(e) => onChange && onChange(e.target.value)}
                            disabled={disabled}
                            className={`
                                w-full py-2 pl-2 ${ isClearable ? 'pr-0' : 'pr-2' }
                                rounded-xl border-form-element
                                focus:outline-none
                            `}
                            style={isTitleCase ? { textTransform: 'capitalize' } : undefined}
                        />

                        {/* Clear button - shown when clearable and has content */}
                        {isClearable && String(value).length > 0 && !disabled && (
                            <button
                                type="button"
                                onClick={() => onChange && onChange("")}
                                className="
                                    ml-2 px-2 py-2
                                    border-l border-form-element
                                    cursor-pointer 
                                "
                            >
                                <FaXmark className="text-gray-500" />
                            </button>
                        )}
                    </>
                )}
                
            </div>
            
        </div>
    );
}

export default FormInput;