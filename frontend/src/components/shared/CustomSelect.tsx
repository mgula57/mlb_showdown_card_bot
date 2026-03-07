/**
 * @fileoverview CustomSelect Component
 * 
 * A highly customizable dropdown select component with support for:
 * - Rich option content (images, symbols, icons, custom colors)
 * - Portal-based dropdown positioning to avoid z-index issues
 * - Intelligent positioning (opens above when there's insufficient space below)
 * - Click-outside detection for UX consistency
 * - Extensive styling customization through className props
 * - Responsive behavior with viewport boundary detection
 * 
 * The component uses React portals to render the dropdown menu directly to document.body,
 * ensuring it appears above other elements regardless of parent container z-index or overflow settings.
 * 
 * @component
 * @example
 * ```tsx
 * <CustomSelect
 *   value={selectedTeam}
 *   onChange={setSelectedTeam}
 *   options={[
 *     { value: 'nyy', label: 'Yankees', image: '/teams/nyy.png' },
 *     { value: 'bos', label: 'Red Sox', symbol: '⚾' }
 *   ]}
 *   suffix="Team"
 * />
 * ```
 */

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

/**
 * Represents a single option in the custom select dropdown
 * Supports multiple content types for rich option display
 */
type SelectOption = {
    /** Unique identifier for the option */
    value: string;
    /** Display text for the option */
    label?: string;
    /** URL to an image to display alongside the option */
    image?: string;
    /** Single character or emoji symbol to display */
    symbol?: string;
    /** React component or element to display as an icon */
    icon?: React.ReactNode;
    /** Custom border color for the option when selected */
    borderColor?: string;
    /** Custom text color for the option */
    textColor?: string;
}

/**
 * Props for the CustomSelect component
 * Provides extensive customization options for styling and behavior
 */
type CustomSelectProps = {
    /** Currently selected value */
    value: string;
    /** Callback function called when selection changes */
    onChange: (value: string) => void;
    /** Array of selectable options */
    options: SelectOption[];
    /** Optional CSS class for the container element */
    className?: string;
    /** Optional CSS class for the select button */
    buttonClassName?: string;
    /** Optional CSS class for option images */
    imageClassName?: string;
    /** Optional CSS class for option labels */
    labelClassName?: string;
    /** Optional CSS class for the dropdown menu */
    dropdownClassName?: string;
    /** Optional text to display after the selected value */
    suffix?: string;
    /** Whether the select is disabled */
    disabled?: boolean;
};

/**
 * Custom select component with intelligent dropdown positioning and rich option support
 * 
 * Features:
 * - Portal-based dropdown rendering to avoid z-index issues
 * - Automatic positioning (above/below) based on available viewport space
 * - Support for images, symbols, and icons in options
 * - Extensive styling customization
 * - Click-outside detection for smooth UX
 * - Responsive positioning that updates on scroll/resize
 * 
 * @param props - Component props
 * @returns A customizable select dropdown component
 */
const CustomSelect: React.FC<CustomSelectProps> = ({ value, onChange, options, className = "", suffix = null, buttonClassName = "", imageClassName = "", labelClassName = "", dropdownClassName = "", disabled = false }) => {

    // State management for dropdown behavior and positioning
    /** Controls whether the dropdown menu is visible */
    const [isOpen, setIsOpen] = useState(false);
    /** Determines if dropdown should open above the button (when space below is limited) */
    const [openAbove, setOpenAbove] = useState(false);
    /** Absolute positioning coordinates for the portal dropdown */
    const [menuPos, setMenuPos] = useState<{ left: number; top: number; }>({ left: 0, top: 0 });

    // Refs for DOM element access and click-outside detection
    const buttonRef = useRef<HTMLButtonElement | null>(null);
    const dropdownRef = useRef<HTMLDivElement | null>(null);

    /** Toggles dropdown visibility when the select button is clicked */
    const handleToggle = () => {
        if (disabled) return;
        setIsOpen(!isOpen);
    };

    /** Handles option selection and closes the dropdown */
    const handleOptionClick = (optionValue: string) => {
        if (disabled) return;
        onChange(optionValue);
        setIsOpen(false);
    };

    /** 
     * Closes dropdown when clicking outside the component
     * Uses event delegation to detect clicks outside both button and dropdown
     */
    const handleClickOutside = (event: MouseEvent) => {
        const target = event.target;
        if (!(target instanceof Node)) return;

        // Close if click is outside both the button and dropdown elements
        if (
            dropdownRef.current &&
            !dropdownRef.current.contains(target) &&
            buttonRef.current &&
            !buttonRef.current.contains(target)
        ) {
            setIsOpen(false);
        }
    };

    /**
     * Calculates optimal dropdown positioning based on available viewport space
     * 
     * Intelligently determines whether to open above or below the button by:
     * - Measuring available space above and below the button
     * - Comparing against dropdown menu height
     * - Positioning the portal dropdown with fixed coordinates
     * - Ensuring dropdown stays within viewport boundaries
     */
    const measureAndSetDirection = () => {
        if (!buttonRef.current) return;
        
        const btnRect = buttonRef.current.getBoundingClientRect();
        const spaceBelow = window.innerHeight - btnRect.bottom;
        const spaceAbove = btnRect.top;
        const menuH = dropdownRef.current?.getBoundingClientRect().height ?? 0;
        
        // Open above if insufficient space below and more space above
        const shouldOpenAbove = spaceBelow < menuH && spaceAbove > spaceBelow;
        setOpenAbove(shouldOpenAbove);
        
        // Set fixed positioning coordinates for portal
        setMenuPos({ 
            left: btnRect.left, 
            top: shouldOpenAbove ? btnRect.top : btnRect.bottom 
        });
    };

    /**
     * Effect for managing dropdown positioning and event listeners
     * 
     * When dropdown opens:
     * - Calculates initial position
     * - Sets up responsive listeners for resize/scroll to maintain position
     * - Adds click-outside detection
     * 
     * Uses capture:true for scroll to catch events from any scrollable container
     */
    useEffect(() => {
        if (!isOpen) return;

        measureAndSetDirection();
        const handleUpdate = () => measureAndSetDirection();
        
        // Listen for viewport changes to maintain correct positioning
        window.addEventListener('resize', handleUpdate);
        window.addEventListener('scroll', handleUpdate, true); // Capture phase for nested scrollers
        document.addEventListener('mousedown', handleClickOutside);
        
        return () => {
            window.removeEventListener('resize', handleUpdate);
            window.removeEventListener('scroll', handleUpdate, true);
            document.removeEventListener('mousedown', handleClickOutside);
        };

    }, [isOpen, options.length]);

    /** 
     * Renders an image element for options that include image URLs
     * @param image - Optional image URL string
     * @returns Image element or null if no image provided
     */
    const renderImage = (image: string | undefined) => {
        if (image) {
            return <img src={image} alt="option image" className={imageClassName ? imageClassName : `mr-2 w-5 h-5 object-contain object-center`} />;
        }
        return null;
    };

    /** 
     * Renders a symbol/emoji for options that include symbol content
     * @param symbol - Optional symbol string (emoji, character, etc.)
     * @returns Span element with symbol or null if no symbol provided
     */
    const renderSymbol = (symbol: string | undefined) => {
        if (symbol) {
            return <span className="mr-2">{symbol}</span>;
        }
        return null;
    };

    /** 
     * Renders a React component/element for options that include custom icons
     * @param icon - Optional React node for icon display
     * @returns Span wrapper with icon or null if no icon provided
     */
    const renderIcon = (icon: React.ReactNode) => {
        if (icon) {
            return <span className="bg-(--background-secondary) my-auto mr-2">{icon}</span>;
        }
        return null;
    };

    /** Determines border color for the select button based on selected option's custom styling */
    const selectedBorderColor = options.find(option => option.value === value)?.borderColor || 'border-form-element';

    return (
        // Container
        <div className={`relative ${className}`}>
            {/* Dropdown button */}
            <button
                type="button"
                ref={buttonRef}
                className={buttonClassName ? buttonClassName : `
                    w-full px-3 py-2 
                    border-2 ${selectedBorderColor} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400
                    bg-secondary text-primary text-nowrap text-left 
                    overflow-clip
                    cursor-pointer
                `}
                onClick={handleToggle}
                disabled={disabled}
            >
                <div className="flex overflow-clip">
                    { renderImage(options.find(option => option.value === value)?.image) }
                    { renderSymbol(options.find(option => option.value === value)?.symbol) }
                    { renderIcon(options.find(option => option.value === value)?.icon) }
                    <span className={labelClassName}> {options.find(option => option.value === value)?.label || null} </span>
                    {suffix && <span className='ml-1'>{suffix}</span>}
                </div>
            </button>

            {/* Dropdown menu popup */}
            {isOpen && !disabled && typeof document !== 'undefined' && (
                createPortal(
                    <div 
                        ref={dropdownRef}
                        className={`
                            ${dropdownClassName}
                            fixed z-1000
                            left-0 transform
                            ${openAbove ? '-translate-y-full -mt-1' : 'mt-1'}
                            bg-(--background-primary) rounded-xl shadow-lg
                            text-nowrap overflow-auto max-h-[60vh]
                        `}
                        style={{ left: menuPos.left, top: menuPos.top }}
                    >
                        {options.map((option) => (
                            <div
                                key={option.value}
                                className={`
                                    ${className} px-2 py-2 
                                    cursor-pointer hover:bg-(--background-secondary)
                                    border-b border-(--background-tertiary) last:border-b-0
                                    flex ${option.textColor || 'text-inherit'}
                                `}
                                onClick={() => handleOptionClick(option.value)}
                            >
                                { renderImage(option.image) }
                                { renderSymbol(option.symbol) }
                                { renderIcon(option.icon) }
                                <span>{option.label}</span>
                            </div>
                        ))}
                    </div>,
                    document.body
                )
            )}
        </div>
    );
};

export type { SelectOption };
export default CustomSelect;