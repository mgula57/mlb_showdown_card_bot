import { useState, useRef, useEffect } from 'react';
import { FaChevronDown, FaCheck, FaTimes } from 'react-icons/fa';

// Props for MultiSelect
interface MultiSelectProps {
    label: string;
    options: { value: string; label: string }[];
    selections?: string[];
    onChange: (values: string[]) => void;
    placeholder?: string;
    className?: string;
}

// Multi-Select Dropdown Component
const MultiSelect = ({ label, options, selections, onChange, placeholder = "Select...", className }: MultiSelectProps) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const selectedValues = selections || [];

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleOption = (value: string) => {
        const newValues = selectedValues.includes(value)
            ? selectedValues.filter(v => v !== value)
            : [...selectedValues, value];
        onChange(newValues);
    };

    const removeOption = (value: string, event: React.MouseEvent) => {
        event.stopPropagation();
        const newValues = selectedValues.filter(v => v !== value);
        onChange(newValues);
    };

    const clearAll = (event: React.MouseEvent) => {
        event.stopPropagation();
        onChange([]);
    };

    return (
        <div className={`space-y-2 ${className}`} ref={dropdownRef}>
            <label className="block text-sm font-medium text-[var(--text-primary)]">{label}</label>
            
            {/* Dropdown Button */}
            <div className="relative">
                <button
                    type="button"
                    onClick={() => setIsOpen(!isOpen)}
                    className={`
                        w-full flex items-center justify-between px-3 py-2 min-h-[2.5rem]
                        border-2 border-form-element rounded-lg 
                        bg-[var(--background-primary)] text-[var(--text-primary)]
                        hover:border-[var(--tertiary)] focus:outline-none focus:ring-2 focus:ring-primary/20
                        ${isOpen ? 'border-primary' : ''}
                    `}
                >
                    <div className="flex flex-wrap gap-1 flex-1 mr-2">
                        {selectedValues.length === 0 ? (
                            <span className="text-[var(--tertiary)]">{placeholder}</span>
                        ) : (
                            selectedValues.map(value => {
                                const option = options.find(opt => opt.value === value);
                                return (
                                    <span
                                        key={value}
                                        className="inline-flex items-center px-2 py-1 bg-primary/20 text-primary text-xs rounded-md"
                                    >
                                        {option?.label || value}
                                        <button
                                            onClick={(e) => removeOption(value, e)}
                                            className="ml-1 hover:text-primary-dark"
                                        >
                                            <FaTimes className="h-3 w-3" />
                                        </button>
                                    </span>
                                );
                            })
                        )}
                    </div>
                    
                    <div className="flex items-center space-x-1">
                        {selectedValues.length > 1 && (
                            <button
                                onClick={clearAll}
                                className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] p-1"
                                title="Clear all"
                            >
                                <FaTimes className="h-3 w-3" />
                            </button>
                        )}
                        <FaChevronDown 
                            className={`h-4 w-4 transition-transform text-[var(--text-secondary)] ${isOpen ? 'rotate-180' : ''}`} 
                        />
                    </div>
                </button>

                {/* Dropdown Menu */}
                {isOpen && (
                    <div className="fixed z-50 min-w-64 mt-1 
                                    bg-[var(--background-primary)] 
                                    border border-[var(--border-primary)] 
                                    rounded-lg shadow-lg 
                                    max-h-72 overflow-y-auto">
                        {/* Header with select all / clear all */}
                        <div className="px-3 py-2 border-b border-[var(--border-secondary)] bg-[var(--background-secondary)]">
                            <div className="flex justify-between text-xs">
                                <button
                                    onClick={() => onChange(options.map(opt => opt.value))}
                                    className="text-primary hover:text-primary-dark"
                                >
                                    Select All
                                </button>
                                <button
                                    onClick={() => onChange([])}
                                    className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                                >
                                    Clear All
                                </button>
                            </div>
                        </div>

                        {/* Options */}
                        {options.map(option => {
                            const isSelected = selectedValues.includes(option.value);
                            return (
                                <div
                                    key={option.value}
                                    onClick={() => toggleOption(option.value)}
                                    className={`
                                        flex items-center px-3 py-2 cursor-pointer hover:bg-[var(--background-secondary)]
                                        ${isSelected ? 'bg-primary/10' : ''}
                                    `}
                                >
                                    <div className={`
                                        flex items-center justify-center w-4 h-4 mr-3 border rounded
                                        ${isSelected 
                                            ? 'bg-primary border-primary text-white' 
                                            : 'border-[var(--border-primary)]'
                                        }
                                    `}>
                                        {isSelected && <FaCheck className="h-2 w-2" />}
                                    </div>
                                    <span className="text-sm">{option.label}</span>
                                </div>
                            );
                        })}

                        {/* No options message */}
                        {options.length === 0 && (
                            <div className="px-3 py-4 text-center text-[var(--text-secondary)] text-sm">
                                No options available
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MultiSelect;