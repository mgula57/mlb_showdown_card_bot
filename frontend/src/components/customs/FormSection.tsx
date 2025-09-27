import React, { useState } from 'react';
import FormElementGrid from './FormElementGrid';
import { FaCaretDown, FaCaretUp } from 'react-icons/fa';

/** Props for the form section component */
type FormSectionProps = {
    title: string;
    children: React.ReactNode;
    icon?: React.ReactNode; // Icon to display in the section header
    isOpenByDefault?: boolean;
    onToggle?: () => void; // Callback when section is toggled
    childrenWhenClosed?: React.ReactNode; // Content to show when section is closed
};

/** FormSection component that can be expanded or collapsed */
const FormSection: React.FC<FormSectionProps> = ({ title, children, icon, isOpenByDefault=false, childrenWhenClosed=undefined, onToggle }) => {

    // State to manage the open/closed state of the section
    const [isOpen, setIsOpen] = useState(isOpenByDefault);

    /** Toggle the open/closed state of the section */
    const toggleCollapse = () => {
        setIsOpen(!isOpen);
        if (onToggle) {
            onToggle();
        }
    };

    return (
        // Main section container
        <div className="w-full px-4 py-3 border-2 border-form-element rounded-2xl overflow-hidden bg-secondary">

            {/* Section Header and Open/Close Button */}
            <button
                type='button'
                className="flex justify-between items-center w-full cursor-pointer"
                onClick={toggleCollapse}
            >
                <div className="flex justify-between items-center w-full text-secondary text-lg font-black">
                    <span className='flex items-center gap-2'>
                        {icon} {title}
                    </span>
                    <span>{isOpen ? <FaCaretUp /> : <FaCaretDown />}</span>
                </div>
            </button>

            <div className='transition-all duration-300 ease-in-out'>
                {/* Collapsible main content */}
                {isOpen && (
                    <div className={`${isOpen ? 'max-h-screen' : 'max-h-0 overflow-hidden'}`}>
                        <div className="mt-4">
                            <FormElementGrid>
                                {children}
                            </FormElementGrid>
                        </div>
                    </div>
                )}

                {/* Content to show when section is closed */}
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