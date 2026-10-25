/**
 * @fileoverview FormEnabler - the app's one boolean toggle
 *
 * A field-height row with a small square checklist box, like the boxes on the old Showdown
 * checklist cards (see frontend/DESIGN.md): an empty box when off, a navy box with a white check
 * when on. It shares the field frame, so toggles line up with inputs and dropdowns in a grid.
 */

import React from 'react';
import { FaCheck } from 'react-icons/fa6';
import { FIELD_FRAME_CLASS, checkBoxClass } from '../shared/fieldStyles';

/**
 * Props for the FormEnabler component
 */
type FormEnablerProps = {
    /** Display label for the toggle option */
    label: React.ReactNode;
    /** One line under the label explaining what the option does */
    description?: React.ReactNode;
    /** Current enabled/disabled state */
    isEnabled: boolean;
    /** Called with the current state when clicked; the caller flips it */
    onChange: (isEnabled: boolean) => void;
    /** `md` sits in form grids next to inputs; `sm` fits a toolbar or tab strip */
    size?: 'sm' | 'md';
    /** Optional CSS class names for additional styling */
    className?: string;
    /** When true, the toggle is shown but interaction is blocked */
    isDisabled?: boolean;
    /** Tooltip shown when isDisabled is true, explaining why it can't be toggled */
    disabledReason?: string;
    /** Tooltip shown when the toggle is usable */
    title?: string;
};

const SIZE_CLASSES = {
    sm: 'min-h-8 px-2.5 py-1 gap-2 text-[12px]',
    md: 'min-h-10 px-3 py-2 gap-2.5 text-sm',
} as const;

const BOX_SIZE_CLASSES = {
    sm: 'w-3.5 h-3.5 text-[8px]',
    md: 'w-4 h-4 text-[9px]',
} as const;

/**
 * @example
 * ```tsx
 * <FormEnabler
 *   label="Add Border"
 *   isEnabled={form.is_bordered}
 *   onChange={(enabled) => setForm({ ...form, is_bordered: !enabled })}
 * />
 * ```
 */
const FormEnabler: React.FC<FormEnablerProps> = ({ label, description, isEnabled, onChange, size = 'md', className = "", isDisabled = false, disabledReason, title }) => {
    return (
        <button
            type="button"
            role="checkbox"
            aria-checked={isEnabled}
            aria-disabled={isDisabled}
            title={isDisabled ? disabledReason : title}
            className={`
                flex items-center text-left font-semibold
                ${FIELD_FRAME_CLASS} ${SIZE_CLASSES[size]}
                ${isEnabled ? 'border-(--showdown-blue)! text-(--text-primary)' : 'text-(--text-secondary)'}
                ${isDisabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
                ${className}
            `}
            onClick={() => { if (!isDisabled) onChange(isEnabled); }}
        >
            {/* Checklist box */}
            <span
                aria-hidden
                className={`${BOX_SIZE_CLASSES[size]} ${checkBoxClass(isEnabled)}`}
            >
                {isEnabled && <FaCheck />}
            </span>
            {description ? (
                <span className="min-w-0">
                    <span className="block">{label}</span>
                    <span className="block text-[11px] font-normal leading-snug text-(--text-tertiary)">{description}</span>
                </span>
            ) : label}
        </button>
    );
}

export default FormEnabler;
