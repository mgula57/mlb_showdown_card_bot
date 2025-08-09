import React from "react";
import { FaXmark } from "react-icons/fa6";

/** Props for the form input component */
type FormInputProps = {
    label: string;
    value: string;
    onChange?: (value: string | null) => void;
    className?: string;
    type?: string;
    isClearable?: boolean;
    placeholder?: string;
    onChangeFile?: (file: File | null) => void;
};

/** 
 * FormInput component for text input fields with a label.
 * Handles changes and updates the parent state.
 */
const FormInput: React.FC<FormInputProps> = ({ label, value, onChange, className = "", type="text", isClearable=false, placeholder, onChangeFile }) => {

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
            <div className="flex items-stretch focus:outline-none border border-form-element rounded-xl mt-1">

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
                            value={value}
                            placeholder={placeholder}
                            onChange={(e) => onChange && onChange(e.target.value)}
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