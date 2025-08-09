import React, { useState, useRef, useEffect } from 'react';

/* Represents a single option in the custom select dropdown */
type SelectOption = {
    label: string;
    value: string;
    image?: string;
    symbol?: string;
    icon?: React.ReactNode;
    borderColor?: string;
    textColor?: string;
}

/** Props for the custom select component */
type CustomSelectProps = {
    value: string;
    onChange: (value: string) => void;
    options: SelectOption[];
};

/** Custom select component for selecting an option from a dropdown list. */
const CustomSelect: React.FC<CustomSelectProps> = ({ value, onChange, options }) => {

    /** State to manage dropdown open/close */
    const [isOpen, setIsOpen] = useState(false);
    const [openAbove, setOpenAbove] = useState(false); // NEW

    // Refs to manage click outside detection
    const buttonRef = useRef<HTMLButtonElement | null>(null);
    const dropdownRef = useRef<HTMLDivElement | null>(null);

    /** Open/close the dropdown when the button is clicked */
    const handleToggle = () => {
        setIsOpen(!isOpen);
    };

    /** User selects an option from the dropdown */
    const handleOptionClick = (optionValue: string) => {
        onChange(optionValue);
        setIsOpen(false);
    };

    /** Close the dropdown if clicking outside of it */
    const handleClickOutside = (event: MouseEvent) => {
        const target = event.target;
        if (!(target instanceof Node)) return;

        if (
            dropdownRef.current &&
            !dropdownRef.current.contains(target) &&
            buttonRef.current &&
            !buttonRef.current.contains(target)
        ) {
            setIsOpen(false);
        }
    };

    /** Measure the dropdown position and set direction based on available space */
    const measureAndSetDirection = () => {
        if (!buttonRef.current || !dropdownRef.current) return;
        const btnRect = buttonRef.current.getBoundingClientRect();
        const menuRect = dropdownRef.current.getBoundingClientRect();
        const spaceBelow = window.innerHeight - btnRect.bottom;
        const spaceAbove = btnRect.top;
        // Flip if not enough below and more space above
        setOpenAbove(spaceBelow < menuRect.height && spaceAbove > spaceBelow);
    };

    // Add event listener for clicks outside the dropdown when it is open
    useEffect(() => {
        if (!isOpen) return;

        measureAndSetDirection();
        const handleUpdate = () => measureAndSetDirection();
        window.addEventListener('resize', handleUpdate);
        window.addEventListener('scroll', handleUpdate, true);
        document.addEventListener('mousedown', handleClickOutside);
        
        return () => {
            window.removeEventListener('resize', handleUpdate);
            window.removeEventListener('scroll', handleUpdate, true);
            document.removeEventListener('mousedown', handleClickOutside);
        };

    }, [isOpen, options.length]);

    /** Helper functions to render any passed in image */
    const renderImage = (image: string | undefined) => {
        if (image) {
            return <img src={image} alt="flag" className="mr-2 w-5 h-5 object-contain object-center" />;
        }
        return null;
    };

    /** Helper functions to render any passed in symbol */
    const renderSymbol = (symbol: string | undefined) => {
        if (symbol) {
            return <span className="mr-2">{symbol}</span>;
        }
        return null;
    };

    /** Helper functions to render any passed in icon */
    const renderIcon = (icon: React.ReactNode) => {
        if (icon) {
            return <span className="bg-secondary">{icon}</span>;
        }
        return null;
    };

    /** Check if the selected option has a custom border color, otherwise use default */
    const selectedBorderColor = options.find(option => option.value === value)?.borderColor || 'border-form-element';

    return (
        // Container
        <div>
            {/* Dropdown button */}
            <button
                type="button"
                ref={buttonRef}
                className={`
                    w-full px-3 py-2 
                    border-2 ${selectedBorderColor} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400
                    bg-primary text-primary text-nowrap text-left 
                    overflow-clip
                `}
                onClick={handleToggle}
            >
                <div className="flex overflow-clip">
                    { renderImage(options.find(option => option.value === value)?.image) }
                    { renderSymbol(options.find(option => option.value === value)?.symbol) }
                    { renderIcon(options.find(option => option.value === value)?.icon) }
                    {options.find(option => option.value === value)?.label || null}
                </div>
            </button>

            {/* Dropdown menu popup */}
            {isOpen && (
                <div 
                    ref={dropdownRef}
                    className={`
                        absolute z-10
                        ${openAbove ? '-translate-y-[calc(100%+3rem)]' : 'mt-1'}
                        transform
                        min-w-2/3 md:min-w-48
                        bg-secondary rounded-xl shadow-lg 
                        text-nowrap overflow-clip
                    `}
                >
                    {options.map((option) => (
                        <div
                            key={option.value}
                            className={`px-4 py-2 cursor-pointer hover:bg-teritiary flex ${option.textColor || 'text-inherit'}`}
                            onClick={() => handleOptionClick(option.value)}
                        >
                            { renderImage(option.image) }
                            { renderSymbol(option.symbol) }
                            <span>{option.label}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export type { SelectOption };
export { CustomSelect };