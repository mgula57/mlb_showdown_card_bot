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

import { useState, useRef, useEffect, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { FaChevronDown, FaCheck, FaTimes } from 'react-icons/fa';

import { FIELD_FRAME_CLASS, FIELD_LABEL_CLASS, checkBoxClass } from './fieldStyles';
import { Plate } from './Plate';
type MultiSelectOption = { value: string; label: string; icon?: ReactNode; iconCompact?: ReactNode };

/** Renders an option's icon when it has one (e.g. a set badge), otherwise its label (falling back to the raw value). */
const OptionContent = ({ option, value, isTag }: { option?: MultiSelectOption; value: string; isTag: boolean }) => {
    const icon = isTag ? (option?.iconCompact ?? option?.icon) : option?.icon;
    if (icon) return <>{icon}</>;
    return <>{option?.label || value}</>;
};

/**
 * Props for the MultiSelect component
 */
interface MultiSelectProps {
    /** Primary label text displayed above the component */
    label: string;
    /** Optional secondary description text for additional context */
    labelDescription?: string;
    /** Array of selectable options with value and display label. When `icon` is set it's shown
     * in place of the label (e.g. set badges); `iconCompact` is a compact version used in the tags. */
    options: MultiSelectOption[];
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
                <label className={FIELD_LABEL_CLASS}>{label}</label>
                {labelDescription && <p className="text-[9px] text-(--text-secondary)">{labelDescription}</p>}
            </div>

            {/* Dropdown Button */}
            <div className="relative">
                <button
                    type="button"
                    ref={triggerRef}
                    onClick={() => !disabled && setIsOpen(o => !o)}  // re-click closes
                    disabled={disabled}
                    className={`
                        w-full flex items-center justify-between px-3 py-1.5 min-h-10 text-sm text-left
                        ${FIELD_FRAME_CLASS}
                        ${isOpen ? 'border-(--showdown-blue)' : ''}
                        ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                >
                    <div className="flex flex-wrap gap-1 flex-1 mr-2">
                        {selectedValues.length === 0 ? (
                            <span className="text-(--text-tertiary)">{placeholder}</span>
                        ) : (
                            selectedValues.map(value => {
                                const option = options.find(opt => opt.value === value);
                                return (
                                    <Plate key={value} size="sm">
                                        <OptionContent option={option} value={value} isTag={true} />
                                        <span
                                            role="button"
                                            tabIndex={0}
                                            aria-label={`Remove ${option?.label ?? value}`}
                                            onClick={(e) => removeOption(value, e)}
                                            onKeyDown={(e) => e.key === 'Enter' && removeOption(value, e as unknown as React.MouseEvent)}
                                            className="cursor-pointer opacity-60 hover:opacity-100"
                                        >
                                            <FaTimes className="h-2.5 w-2.5" />
                                        </span>
                                    </Plate>
                                );
                            })
                        )}
                    </div>

                    <div className="flex items-center space-x-1">
                        {selectedValues.length > 1 && !disabled && (
                            <span
                                role="button"
                                tabIndex={0}
                                onClick={clearAll}
                                onKeyDown={(e) => e.key === 'Enter' && clearAll(e as unknown as React.MouseEvent)}
                                className="text-xs text-(--text-tertiary) hover:text-(--text-primary) p-1 cursor-pointer"
                                title="Clear all"
                            >
                                <FaTimes className="h-3 w-3" />
                            </span>
                        )}
                        <FaChevronDown
                            className={`h-3 w-3 transition-transform text-(--text-tertiary) ${isOpen ? 'rotate-180' : ''}`}
                        />
                    </div>
                </button>

                {/* Dropdown menu, styled like CustomSelect's */}
                {isOpen && !disabled && createPortal(
                    <div
                        ref={menuRef}
                        style={dropdownStyle}
                        className={`bg-(--background-secondary) border border-(--rule-strong) rounded-card shadow-overlay overflow-y-auto scrollbar-hide
                                    transform ${openAbove ? '-translate-y-full -mt-1' : 'mt-1'}`}
                    >
                        {/* Header with select all / clear all */}
                        <div className="px-3 py-2 border-b border-(--divider)">
                            <div className="flex justify-between text-xs font-semibold">
                                <button
                                    type="button"
                                    onClick={() => onChange(options.map(opt => opt.value))}
                                    disabled={disabled}
                                    className="cursor-pointer text-(--showdown-blue) hover:underline"
                                >
                                    Select All
                                </button>
                                <button
                                    type="button"
                                    onClick={() => onChange([])}
                                    disabled={disabled}
                                    className="cursor-pointer text-(--text-tertiary) hover:text-(--text-primary)"
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
                                    role="checkbox"
                                    aria-checked={isSelected}
                                    onClick={() => toggleOption(option.value)}
                                    className={`
                                        flex items-center gap-3 px-3 py-2 text-sm cursor-pointer hover:bg-(--background-tertiary)
                                        ${isSelected ? 'font-semibold' : ''}
                                    `}
                                >
                                    <span aria-hidden className={`w-4 h-4 text-[9px] ${checkBoxClass(isSelected)}`}>
                                        {isSelected && <FaCheck />}
                                    </span>
                                    <OptionContent option={option} value={option.value} isTag={false} />
                                </div>
                            );
                        })}

                        {/* No options message */}
                        {options.length === 0 && (
                            <div className="px-3 py-4 text-center text-(--text-tertiary) text-sm">
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