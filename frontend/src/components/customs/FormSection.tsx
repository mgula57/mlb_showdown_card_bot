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
import { FaCaretDown, FaCaretUp } from 'react-icons/fa';

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

    /**
     * Toggle section visibility and notify parent component
     * Updates internal state and calls optional callback
     */
    const toggleCollapse = () => {
        if (!collapsible) return;
        setIsOpen(!isOpen);
        if (onToggle) {
            onToggle();
        }
    };

    return (
        <div className="w-full px-4 py-3 border-2 border-form-element rounded-2xl overflow-hidden bg-secondary">

            {/* Section header with title and icon — clickable toggle only when collapsible */}
            <button
                type='button'
                className={`flex justify-between items-center w-full ${collapsible ? 'cursor-pointer' : 'cursor-default'}`}
                onClick={toggleCollapse}
                aria-expanded={collapsible ? isOpen : undefined}
            >
                <div className="flex justify-between items-center w-full text-secondary text-lg font-black">
                    <span className='flex items-center gap-2'>
                        {icon} {title}
                    </span>
                    {/* Toggle caret indicating section state */}
                    {collapsible && <span>{isOpen ? <FaCaretUp /> : <FaCaretDown />}</span>}
                </div>
            </button>

            {/* Content area with smooth expand/collapse animation */}
            <div className='transition-all duration-300 ease-in-out'>
                {/* Main form content - shown when expanded */}
                {isOpen && (
                    <div className={`${isOpen ? 'max-h-screen' : 'max-h-0 overflow-hidden'}`}>
                        <div className="mt-4">
                            <FormElementGrid>
                                {children}
                            </FormElementGrid>
                        </div>
                    </div>
                )}

                {/* Summary content - shown when collapsed */}
                {!isOpen && childrenWhenClosed && (
                    <button type="button" className="mt-2 cursor-pointer" onClick={toggleCollapse}>
                        {childrenWhenClosed}
                    </button>
                )}
            </div>
        </div>
    );
};

export default FormSection;