/**
 * @fileoverview SetMultiSelect - compact multi-select dropdown for the search bar (Showdown sets,
 * release editions). Mirrors the look of the single-select set override dropdown, but lets several
 * options be picked. Options show their icon (a set badge) when they have one, otherwise their label; `group`
 * adds a header above each run of options sharing it. An empty selection falls back to the default
 * set (shown via `defaultIcon`), or `placeholder` text when there's no default icon.
 * The `pill` variant renders a compact rounded trigger for the chip row (next to the sort button);
 * the `form` variant matches `MultiSelect`'s trigger (removable tags) for use inside forms/modals.
 */

import { Fragment, useEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { FaCaretDown, FaCheck, FaChevronDown, FaTimes } from 'react-icons/fa';

import { fieldClass, FIELD_FRAME_CLASS, CAPS_LABEL_CLASS, INLINE_FIELD_LABEL_CLASS, checkBoxClass } from '../shared/fieldStyles';
import { Plate } from '../shared/Plate';
export type SetMultiSelectOption = { value: string; icon?: ReactNode; label?: string; group?: string };

type SetMultiSelectProps = {
    options: SetMultiSelectOption[];
    /** Selected set values; empty = the default set */
    selections: string[];
    onChange: (values: string[]) => void;
    /** Icon shown when nothing is selected (the set the search falls back to) */
    defaultIcon?: ReactNode;
    /** Text shown when nothing is selected and there's no `defaultIcon` */
    placeholder?: string;
    className?: string;
    disabled?: boolean;
    /** `toolbar` (default) matches the search bar controls; `pill` matches the chip row's sort button;
     * `form` matches `MultiSelect`'s full-width trigger */
    variant?: 'toolbar' | 'pill' | 'form';
    /** Bold label shown before the selection (e.g. "Positions:") */
    prefix?: ReactNode;
};

export default function SetMultiSelect({ options, selections, onChange, defaultIcon, placeholder, className = '', disabled = false, variant = 'toolbar', prefix }: SetMultiSelectProps) {
    const isPill = variant === 'pill';
    const isForm = variant === 'form';
    const [isOpen, setIsOpen] = useState(false);
    const [menuPos, setMenuPos] = useState({ left: 0, top: 0, minWidth: 0 });
    const buttonRef = useRef<HTMLButtonElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);

    const toggle = (value: string) => {
        onChange(selections.includes(value) ? selections.filter(v => v !== value) : [...selections, value]);
    };

    useEffect(() => {
        if (!isOpen) return;
        const updatePosition = () => {
            const rect = buttonRef.current?.getBoundingClientRect();
            if (!rect) return;
            const left = Math.max(8, Math.min(rect.left, window.innerWidth - Math.max(rect.width, 180) - 8));
            setMenuPos({ left, top: rect.bottom, minWidth: rect.width });
        };
        const handleClickOutside = (e: MouseEvent) => {
            const target = e.target;
            if (!(target instanceof Node)) return;
            if (!menuRef.current?.contains(target) && !buttonRef.current?.contains(target)) setIsOpen(false);
        };
        updatePosition();
        window.addEventListener('resize', updatePosition);
        window.addEventListener('scroll', updatePosition, true);
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            window.removeEventListener('resize', updatePosition);
            window.removeEventListener('scroll', updatePosition, true);
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

    const selectedOptions = options.filter(o => selections.includes(o.value));

    return (
        <div className={`relative ${className}`}>
            {isForm ? (
                // Mirrors MultiSelect's trigger: full width, removable tags, chevron
                <button
                    type="button"
                    ref={buttonRef}
                    disabled={disabled}
                    onClick={() => setIsOpen(open => !open)}
                    className={`
                        w-full flex items-center justify-between px-3 py-1.5 min-h-10 text-sm text-left
                        ${FIELD_FRAME_CLASS}
                        ${isOpen ? 'border-(--showdown-blue)' : ''}
                        ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                >
                    <div className="flex flex-wrap gap-1 flex-1 mr-2">
                        {selectedOptions.length === 0 ? (
                            <span className="text-(--text-tertiary)">{placeholder}</span>
                        ) : selectedOptions.map(option => (
                            <Plate key={option.value} size="sm">
                                {option.label ?? option.value}
                                {!disabled && (
                                    <span
                                        role="button"
                                        tabIndex={0}
                                        onClick={(e) => { e.stopPropagation(); toggle(option.value); }}
                                        onKeyDown={(e) => { if (e.key === 'Enter') { e.stopPropagation(); toggle(option.value); } }}
                                        aria-label={`Remove ${option.label ?? option.value}`}
                                        className="cursor-pointer opacity-60 hover:opacity-100"
                                    >
                                        <FaTimes className="h-2.5 w-2.5" />
                                    </span>
                                )}
                            </Plate>
                        ))}
                    </div>
                    <FaChevronDown className={`h-3 w-3 shrink-0 transition-transform text-(--text-tertiary) ${isOpen ? 'rotate-180' : ''}`} />
                </button>
            ) : (
                <button
                    type="button"
                    ref={buttonRef}
                    disabled={disabled}
                    onClick={() => setIsOpen(open => !open)}
                    className={fieldClass(isPill ? 'sm' : 'lg', 'flex items-center cursor-pointer')}
                >
                    {prefix && <span className={`${INLINE_FIELD_LABEL_CLASS} mr-1`}>{prefix}</span>}
                    {/* Same footprint as the single-select set dropdown: one badge (first pick) + "+N" for extras */}
                    {(() => {
                        const shown = selectedOptions[0];
                        const icon = shown?.icon ?? defaultIcon;
                        return (
                            <>
                                {icon
                                    ? <span className="flex items-center shrink-0 mr-1">{icon}</span>
                                    : <span className={`${isPill ? '' : 'text-xs'} whitespace-nowrap truncate max-w-28 md:max-w-56 mr-1`}>{shown ? (shown.label ?? shown.value) : placeholder}</span>}
                                {selectedOptions.length > 1 && <span className={`${isPill ? '' : 'text-xs'} text-(--text-secondary) tabular-nums whitespace-nowrap`}>+{selectedOptions.length - 1}</span>}
                            </>
                        );
                    })()}
                    <FaCaretDown className={`ml-1 opacity-75 ${isOpen ? 'rotate-180' : ''}`} size={isPill ? 12 : 16} />
                </button>
            )}

            {isOpen && !disabled && createPortal(
                <div
                    ref={menuRef}
                    style={{ left: menuPos.left, top: menuPos.top, minWidth: menuPos.minWidth }}
                    className="
                        fixed z-1000 mt-1 max-h-[60vh]
                        bg-(--background-secondary) rounded-card shadow-overlay
                        border border-(--rule-strong)
                        overflow-auto scrollbar-hide
                    "
                >
                    <div className="flex justify-between px-3 py-2 gap-5 text-xs font-semibold border-b border-(--divider)">
                        <button type="button" onClick={() => onChange(options.map(o => o.value))} className="cursor-pointer text-(--showdown-blue) hover:underline">Select All</button>
                        <button type="button" onClick={() => onChange([])} className="cursor-pointer text-(--text-tertiary) hover:text-(--text-primary)">Clear All</button>
                    </div>
                    {options.map((option, index) => {
                        const isSelected = selections.includes(option.value);
                        const showGroupHeader = option.group !== undefined && option.group !== options[index - 1]?.group;
                        return (
                            <Fragment key={option.value}>
                                {showGroupHeader && (
                                    <div className={`px-3 pt-2 pb-1 ${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>
                                        {option.group}
                                    </div>
                                )}
                                <div
                                    onClick={() => toggle(option.value)}
                                    className={`
                                        flex items-center gap-3 px-3 py-2 cursor-pointer
                                        hover:bg-(--background-tertiary)
                                        border-b border-(--divider) last:border-b-0
                                        ${isSelected ? 'font-semibold' : ''}
                                    `}
                                >
                                    <span aria-hidden className={`w-4 h-4 text-[9px] ${checkBoxClass(isSelected)}`}>
                                        {isSelected && <FaCheck />}
                                    </span>
                                    {option.icon
                                        ? option.icon
                                        : <span className="text-sm whitespace-nowrap">{option.label ?? option.value}</span>}
                                </div>
                            </Fragment>
                        );
                    })}
                </div>,
                document.body
            )}
        </div>
    );
}
