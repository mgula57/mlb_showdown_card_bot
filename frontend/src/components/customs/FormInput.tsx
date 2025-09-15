import React from "react";
import { FaXmark } from "react-icons/fa6";

/** Props for the form input component */
type FormInputProps = {
    label: string;
    value: string | number;
    onChange?: (value: string | null) => void;
    className?: string;
    type?: string;
    inputMode?: "text" | "search" | "email" | "tel" | "url" | "none" | "numeric" | "decimal" | undefined;
    isClearable?: boolean;
    placeholder?: string;
    onChangeFile?: (file: File | null) => void;
    isTitleCase?: boolean;
};

/** 
 * FormInput component for text input fields with a label.
 * Handles changes and updates the parent state.
 */
const FormInput: React.FC<FormInputProps> = ({ label, value, onChange, className = "", type="text", inputMode="text", isClearable=false, placeholder, onChangeFile, isTitleCase }) => {

    const isFileInput = type === "file";

    const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!onChangeFile) return;
        const files = e.target.files;
        onChangeFile(files && files.length > 0 ? files[0] : null);
    };

    return (
        <div className={`${className}`}>
            {/* Label */}
            <label className="text-sm font-medium text-secondary">{label}</label>

            {/* Input Container */}
            <div className="flex items-stretch focus:outline-none border-2 border-form-element rounded-xl mt-1">

                {/* File input for file type */}
                {isFileInput ? (
                    
                    <input
                        type="file"
                        accept="image/*"
                        multiple={false}
                        onChange={handleFile}
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
                    />
                ) : (
                    <>

                        <input
                            type={type}
                            inputMode={inputMode}
                            value={value}
                            placeholder={placeholder}
                            autoComplete="off"
                            onChange={(e) => onChange && onChange(e.target.value)}
                            className={`
                                w-full py-2 pl-2 ${ isClearable ? 'pr-0' : 'pr-2' }
                                rounded-xl border-form-element
                                focus:outline-none
                            `}
                            style={isTitleCase ? { textTransform: 'capitalize' } : undefined}
                        />

                        {/* Optional Clear button */}
                        {isClearable && String(value).length > 0 && (
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