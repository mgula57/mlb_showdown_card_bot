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
import { buttonClass } from './buttonStyles';
import { Heading } from './Heading';

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
            border border-(--divider)
            rounded-card shadow-overlay
            text-left z-50
            animate-fade-in
        ">

            <Heading level="panel" as="div" className="mb-1">{title}</Heading>
            <p className="text-xs text-secondary mb-3">
                {content}
            </p>
            <button
                type="button"
                onClick={onClose}
                className={buttonClass('primary', 'sm', 'w-full')}
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