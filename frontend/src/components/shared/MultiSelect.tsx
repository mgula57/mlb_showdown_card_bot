import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
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
    const wrapperRef = useRef<HTMLDivElement>(null);    // outer component
    const triggerRef = useRef<HTMLButtonElement>(null); // button that triggers menu
    const menuRef = useRef<HTMLDivElement>(null);       // portal menu

    const [openAbove, setOpenAbove] = useState(false);
    const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({});
    const selectedValues = selections || [];

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

    // Recompute fixed position (and whether to open above)
    const updatePosition = () => {
        if (!triggerRef.current) return;
        const rect = triggerRef.current.getBoundingClientRect();
        const menuH = menuRef.current?.getBoundingClientRect()?.height ?? 240;

        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceAbove = rect.top;
        const shouldOpenAbove = spaceBelow < menuH && spaceAbove > spaceBelow;

        setOpenAbove(shouldOpenAbove);

        const left = Math.max(8, Math.min(rect.left, window.innerWidth - rect.width - 8));
        const top = shouldOpenAbove ? rect.top : rect.bottom;

        const maxHeight = shouldOpenAbove
            ? Math.max(120, rect.top - 8)
            : Math.max(120, window.innerHeight - rect.bottom - 8);

        setDropdownStyle({
            position: 'fixed',
            top,
            left,
            width: rect.width,
            zIndex: 50,
            maxHeight,
        });
    };

    // Position on open + keep updated on resize/scroll (capture to catch inner scrollers)
    useEffect(() => {
        if (!isOpen) return;
        updatePosition();
        const handle = () => updatePosition();
        window.addEventListener('resize', handle);
        window.addEventListener('orientationchange', handle);
        window.addEventListener('scroll', handle, true);
        return () => {
            window.removeEventListener('resize', handle);
            window.removeEventListener('orientationchange', handle);
            window.removeEventListener('scroll', handle, true);
        };
    }, [isOpen, options.length]);

    // Close when clicking outside (account for portal)
    useEffect(() => {
        const onDocClick = (e: MouseEvent) => {
            const target = e.target as Node;
            if (!wrapperRef.current?.contains(target) && !menuRef.current?.contains(target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', onDocClick);
        return () => document.removeEventListener('mousedown', onDocClick);
    }, []);

    return (
        <div className={`space-y-2 ${className}`} ref={wrapperRef}>
            <label className="block text-sm font-medium text-[var(--text-primary)]">{label}</label>
            
            {/* Dropdown Button */}
            <div className="relative">
                <button
                    type="button"
                    ref={triggerRef}
                    onClick={() => setIsOpen(o => !o)}  // re-click closes
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

                {/* Dropdown dropdown */}
                {isOpen && createPortal(
                    <div
                        ref={menuRef}
                        style={dropdownStyle}
                        className={`bg-[var(--background-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg overflow-y-auto
                                    transform ${openAbove ? '-translate-y-full -mt-1' : 'mt-1'}`}
                    >
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
                                            ? 'bg-primary border-primary'
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
                    </div>,
                    document.body
                )}
            </div>
        </div>
    );
};

export default MultiSelect;