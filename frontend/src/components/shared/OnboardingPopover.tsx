/**
 * @fileoverview OnboardingPopover Component
 * 
 * Displays a popover with onboarding information and a close button.
 * Positioned relative to the parent container, with responsive styling.
 * - Uses absolute positioning to appear below the target element
 * - Includes a close button that triggers the onClose callback
 * - Styled with a background, border, and shadow for visibility
 * - Responsive width and padding for different screen sizes
 * - Example usage:
 * ```tsx
 * <OnboardingPopover onClose={() => setShowPopover(false)} />
 * ```
 * 
 * @component
 */
import React from 'react';

interface OnboardingPopoverProps {
    /** Title of the popover */
    title: string;
    /** Content of the popover */
    content?: string;
    /** Callback function to close the popover */
    onClose: () => void;
}

export const OnboardingPopover: React.FC<OnboardingPopoverProps> = ({
    title,
    content,
    onClose
}) => {
    return (
        <div className="
            absolute bottom-full left-0 mb-3
            w-56 p-3
            bg-(--background-secondary)
            border border-form-element
            rounded-xl shadow-xl
            text-left z-50
            animate-fade-in
        ">

            <p className="text-sm font-semibold text-primary mb-1">{title}</p>
            <p className="text-xs text-secondary mb-3">
                {content}
            </p>
            <button
                type="button"
                onClick={onClose}
                className="
                    w-full py-1.5 px-3
                    bg-(--showdown-red) hover:bg-(--showdown-red)/80
                    text-white text-xs font-semibold
                    rounded-lg cursor-pointer
                    transition-colors duration-150
                "
            >
                Got it
            </button>
            {/* Arrow pointing down */}
            <div className="
                absolute -bottom-2 left-4
                w-3 h-3
                bg-(--background-secondary)
                border-r border-b border-form-element
                rotate-45
            " />
        </div>
    );
};