/**
 * @fileoverview FormSection - Collapsible form section component
 * 
 * Provides an expandable/collapsible container for organizing related form fields
 * into logical groups. Features toggle functionality, icons, custom headers, and
 * summary content when collapsed. Used to organize the card builder into manageable
 * sections like Player, Set, Image, and Chart settings.
 */

import React, { useState } from 'react';
import FormElementGrid from './FormElementGrid';
import { FaChevronDown } from 'react-icons/fa6';

/**
 * Props for the FormSection component
 */
type FormSectionProps = {
    /** Section title displayed in the header */
    title: string;
    /** Form elements to display when section is expanded */
    children: React.ReactNode;
    /** Optional icon to display next to the title */
    icon?: React.ReactNode;
    /** Whether the section should be open by default */
    isOpenByDefault?: boolean;
    /** Callback function when section is toggled */
    onToggle?: () => void;
    /** Summary content to show when section is collapsed */
    childrenWhenClosed?: React.ReactNode;
    /** When false, the section is always expanded with no toggle — for content that's too
     *  essential to hide (e.g. an Identity section). Defaults to true. */
    collapsible?: boolean;
};

/**
 * FormSection - Collapsible container for organizing form fields
 * 
 * Creates an expandable section with a clickable header that toggles visibility
 * of contained form elements. Supports icons, custom styling, and summary content
 * when collapsed. Helps organize complex forms into manageable, logical groups.
 * 
 * @example
 * ```tsx
 * <FormSection
 *   title="Player Settings"
 *   icon={<FaUser />}
 *   isOpenByDefault={true}
 *   onToggle={() => console.log('Section toggled')}
 *   childrenWhenClosed={<div>Name: {playerName}</div>}
 * >
 *   <FormInput label="Name" value={name} onChange={setName} />
 *   <FormInput label="Year" value={year} onChange={setYear} />
 * </FormSection>
 * ```
 * 
 * @param title - Section header title
 * @param children - Form elements when expanded
 * @param icon - Optional header icon
 * @param isOpenByDefault - Initial expanded state
 * @param onToggle - Toggle event handler
 * @param childrenWhenClosed - Summary content when collapsed
 * @returns Collapsible form section container
 */
const FormSection: React.FC<FormSectionProps> = ({ title, children, icon, isOpenByDefault=false, childrenWhenClosed=undefined, onToggle, collapsible=true }) => {

    /** Internal state for section expand/collapse */
    const [isOpen, setIsOpen] = useState(collapsible ? isOpenByDefault : true);
    /** True while the expand/collapse transition runs - content must clip until it settles */
    const [isAnimating, setIsAnimating] = useState(false);

    /**
     * Toggle section visibility and notify parent component
     * Updates internal state and calls optional callback
     */
    const toggleCollapse = () => {
        if (!collapsible) return;
        setIsAnimating(true);
        setIsOpen(!isOpen);
        if (onToggle) {
            onToggle();
        }
    };

    return (
        <div className="w-full px-3 py-2.5 border border-form-element rounded-xl bg-secondary">

            {/* Section header with title, icon, and (when collapsed) inline summary — clickable toggle only when collapsible */}
            <button
                type='button'
                className={`
                    flex items-start gap-3 w-full min-w-0 -mx-1.5 px-1.5 py-1 rounded-lg box-content
                    transition-colors ${collapsible ? 'cursor-pointer hover:bg-(--background-tertiary)/60' : 'cursor-default'}
                `}
                onClick={toggleCollapse}
                aria-expanded={collapsible ? isOpen : undefined}
            >
                <span className='flex items-center gap-2 shrink-0 text-sm font-bold text-secondary'>
                    {icon && <span className='text-xs text-(--tertiary)'>{icon}</span>}
                    {title}
                </span>

                {/* Summary content - shown inline when collapsed, wrapping onto extra rows if needed */}
                <span className='flex-1 min-w-0 pt-px'>
                    {!isOpen && childrenWhenClosed}
                </span>

                {/* Toggle chevron indicating section state */}
                {/* Wrapped in a title-height box so it stays level with the title when chips wrap */}
                {collapsible && (
                    <span className='flex items-center h-5 shrink-0'>
                        <FaChevronDown className={`text-xs text-(--tertiary) transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
                    </span>
                )}
            </button>

            {/* Content area - animates height via grid rows so no fixed max-height cap is needed */}
            <div
                className={`grid transition-[grid-template-rows] duration-200 ease-in-out ${isOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}
                onTransitionEnd={(e) => { if (e.target === e.currentTarget) setIsAnimating(false); }}
                inert={!isOpen}
            >
                {/* CLIP ONLY WHILE CLOSED OR MID-TRANSITION - ONCE FULLY OPEN, OVERFLOW STAYS VISIBLE
                    SO DROPDOWN MENUS INSIDE THE SECTION AREN'T CUT OFF */}
                <div className={`min-h-0 ${isOpen && !isAnimating ? 'overflow-visible' : 'overflow-hidden'}`}>
                    <div className="pt-3">
                        <FormElementGrid>
                            {children}
                        </FormElementGrid>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FormSection;