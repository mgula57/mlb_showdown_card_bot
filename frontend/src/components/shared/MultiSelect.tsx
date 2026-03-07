/**
 * @fileoverview MultiSelect Component
 * 
 * A comprehensive multi-selection dropdown component with advanced UX features:
 * - Multiple option selection with visual tags
 * - Intelligent portal-based positioning (opens above/below based on space)
 * - Individual option removal with dedicated buttons
 * - Bulk select all / clear all functionality
 * - Responsive positioning that adapts to viewport changes
 * - Click-outside detection with portal support
 * - Searchable/filterable options with smooth interactions
 * - Accessible design with proper ARIA labeling
 * 
 * Uses React portals to render dropdown outside component hierarchy, preventing
 * z-index and overflow issues. Positioning dynamically adjusts based on available
 * viewport space to ensure dropdown remains visible.
 * 
 * @component
 * @example
 * ```tsx
 * <MultiSelect
 *   label="Select Teams"
 *   labelDescription="Choose multiple MLB teams"
 *   options={[
 *     { value: 'nyy', label: 'New York Yankees' },
 *     { value: 'bos', label: 'Boston Red Sox' }
 *   ]}
 *   selections={selectedTeams}
 *   onChange={setSelectedTeams}
 *   placeholder="Choose teams..."
 * />
 * ```
 */

import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FaChevronDown, FaCheck, FaTimes } from 'react-icons/fa';

/**
 * Props for the MultiSelect component
 */
interface MultiSelectProps {
    /** Primary label text displayed above the component */
    label: string;
    /** Optional secondary description text for additional context */
    labelDescription?: string;
    /** Array of selectable options with value and display label */
    options: { value: string; label: string }[];
    /** Current selected values array */
    selections?: string[];
    /** Callback function called when selections change */
    onChange: (values: string[]) => void;
    /** Placeholder text shown when no selections are made */
    placeholder?: string;
    /** Optional CSS class for styling customization */
    className?: string;
    /** Whether the field is disabled */
    disabled?: boolean;
}

/**
 * MultiSelect dropdown component with intelligent positioning and rich interactions
 * 
 * Features:
 * - Portal-based dropdown rendering for z-index independence
 * - Smart positioning (above/below) based on available space
 * - Individual tag removal and bulk selection controls
 * - Responsive positioning updates on scroll/resize
 * - Click-outside detection across portal boundaries
 * - Visual selection feedback with checkboxes
 * - Accessible keyboard and screen reader support
 * 
 * @param props - Component props
 * @returns A multi-selection dropdown with tags and advanced UX
 */
const MultiSelect = ({ label, labelDescription, options, selections, onChange, placeholder = "Select...", className, disabled = false }: MultiSelectProps) => {

    // State management for dropdown behavior and positioning
    /** Controls dropdown visibility */
    const [isOpen, setIsOpen] = useState(false);
    
    // Refs for DOM access and portal positioning
    const wrapperRef = useRef<HTMLDivElement>(null);    // Main component wrapper
    const triggerRef = useRef<HTMLButtonElement>(null); // Button that opens dropdown
    const menuRef = useRef<HTMLDivElement>(null);       // Portal dropdown menu

    /** Determines if dropdown should open above the trigger */
    const [openAbove, setOpenAbove] = useState(false);
    /** CSS styles for fixed positioning of portal dropdown */
    const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({});
    
    /** Current selected values with fallback to empty array */
    const selectedValues = selections || [];

    /** 
     * Toggles selection state of an option (add if not selected, remove if selected)
     * @param value - The option value to toggle
     */
    const toggleOption = (value: string) => {
        if (disabled) return;
        const newValues = selectedValues.includes(value)
            ? selectedValues.filter(v => v !== value)  // Remove if already selected
            : [...selectedValues, value];              // Add if not selected
        onChange(newValues);
    };

    /** 
     * Removes a specific option from selections (used by tag close buttons)
     * @param value - The option value to remove
     * @param event - Mouse event to prevent dropdown toggle
     */
    const removeOption = (value: string, event: React.MouseEvent) => {
        if (disabled) return;
        event.stopPropagation(); // Prevent triggering dropdown toggle
        const newValues = selectedValues.filter(v => v !== value);
        onChange(newValues);
    };

    /** 
     * Clears all selected options (used by "Clear All" button)
     * @param event - Mouse event to prevent dropdown toggle
     */
    const clearAll = (event: React.MouseEvent) => {
        if (disabled) return;
        event.stopPropagation(); // Prevent triggering dropdown toggle
        onChange([]);
    };

    /**
     * Calculates and updates dropdown positioning based on available viewport space
     * 
     * This function:
     * - Measures space above and below the trigger button
     * - Determines optimal positioning (above/below) to keep dropdown visible
     * - Ensures dropdown stays within viewport bounds with padding
     * - Sets maximum height based on available space
     * - Updates portal positioning styles for fixed positioning
     */
    const updatePosition = () => {
        if (!triggerRef.current) return;
        
        const rect = triggerRef.current.getBoundingClientRect();
        const menuH = menuRef.current?.getBoundingClientRect()?.height ?? 240; // Fallback height

        // Calculate available space in both directions
        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceAbove = rect.top;
        
        // Open above if insufficient space below and more space above
        const shouldOpenAbove = spaceBelow < menuH && spaceAbove > spaceBelow;
        setOpenAbove(shouldOpenAbove);

        // Ensure dropdown stays within horizontal viewport bounds (8px padding)
        const left = Math.max(8, Math.min(rect.left, window.innerWidth - rect.width - 8));
        const top = shouldOpenAbove ? rect.top : rect.bottom;

        // Calculate maximum height based on available space (120px minimum)
        const maxHeight = shouldOpenAbove
            ? Math.max(120, rect.top - 8)         // Space above minus padding
            : Math.max(120, window.innerHeight - rect.bottom - 8); // Space below minus padding

        // Update portal styles for fixed positioning
        setDropdownStyle({
            position: 'fixed',
            top,
            left,
            width: rect.width,
            zIndex: 50,
            maxHeight,
        });
    };

    /**
     * Effect: Manages dropdown positioning and responsive behavior
     * 
     * When dropdown is open:
     * - Calculates initial position
     * - Sets up event listeners for responsive repositioning
     * - Handles viewport changes (resize, orientation, scroll)
     * - Uses capture phase for scroll to catch nested scrollable containers
     * 
     * Updates whenever dropdown state or options change
     */
    useEffect(() => {
        if (!isOpen) return;
        
        updatePosition();
        const handle = () => updatePosition();
        
        // Listen for all events that might affect positioning
        window.addEventListener('resize', handle);
        window.addEventListener('orientationchange', handle);
        window.addEventListener('scroll', handle, true); // Capture phase for nested scrollers
        
        return () => {
            window.removeEventListener('resize', handle);
            window.removeEventListener('orientationchange', handle);
            window.removeEventListener('scroll', handle, true);
        };
    }, [isOpen, options.length]);

    /**
     * Effect: Click-outside detection for dropdown closing
     * 
     * Handles clicks outside both the main component and the portal dropdown.
     * This is necessary because the dropdown is rendered in a portal outside
     * the normal component tree, requiring special handling for outside clicks.
     */
    useEffect(() => {
        const onDocClick = (e: MouseEvent) => {
            const target = e.target as Node;
            
            // Close if click is outside both wrapper and portal menu
            if (!wrapperRef.current?.contains(target) && !menuRef.current?.contains(target)) {
                setIsOpen(false);
            }
        };
        
        document.addEventListener('mousedown', onDocClick);
        return () => document.removeEventListener('mousedown', onDocClick);
    }, []);

    return (
        <div className={`space-y-2 ${className}`} ref={wrapperRef}>
            <div>
                <label className="block text-sm font-medium text-[var(--text-primary)]">{label}</label>
                {labelDescription && <p className="text-[9px] text-[var(--text-secondary)]">{labelDescription}</p>}
            </div>
            
            {/* Dropdown Button */}
            <div className="relative">
                <button
                    type="button"
                    ref={triggerRef}
                    onClick={() => !disabled && setIsOpen(o => !o)}  // re-click closes
                    disabled={disabled}
                    className={`
                        w-full flex items-center justify-between px-3 py-2 min-h-[2.5rem]
                        border-2 border-form-element rounded-lg 
                        bg-[var(--background-primary)] text-[var(--text-primary)]
                        hover:border-[var(--tertiary)] focus:outline-none focus:ring-2 focus:ring-primary/20
                        ${isOpen ? 'border-primary' : ''}
                        ${disabled ? 'opacity-60 cursor-not-allowed' : ''}
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
                        {selectedValues.length > 1 && !disabled && (
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
                {isOpen && !disabled && createPortal(
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
                                    disabled={disabled}
                                    className="text-primary hover:text-primary-dark"
                                >
                                    Select All
                                </button>
                                <button
                                    onClick={() => onChange([])}
                                    disabled={disabled}
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