/**
 * @fileoverview SetMultiSelect - compact multi-select dropdown for the search bar (Showdown sets,
 * release editions). Mirrors the look of the single-select set override dropdown, but lets several
 * options be picked. Options show their logo when they have one, otherwise their label; `group`
 * adds a header above each run of options sharing it. An empty selection falls back to the default
 * set (shown via `defaultImage`), or `placeholder` text when there's no default image.
 */

import { Fragment, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { FaCaretDown, FaCheck } from 'react-icons/fa';

export type SetMultiSelectOption = { value: string; image?: string; label?: string; group?: string };

type SetMultiSelectProps = {
    options: SetMultiSelectOption[];
    /** Selected set values; empty = the default set */
    selections: string[];
    onChange: (values: string[]) => void;
    /** Image shown when nothing is selected (the set the search falls back to) */
    defaultImage?: string;
    /** Text shown when nothing is selected and there's no `defaultImage` */
    placeholder?: string;
    className?: string;
    disabled?: boolean;
};

export default function SetMultiSelect({ options, selections, onChange, defaultImage, placeholder, className = '', disabled = false }: SetMultiSelectProps) {
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
            <button
                type="button"
                ref={buttonRef}
                disabled={disabled}
                onClick={() => setIsOpen(open => !open)}
                className="
                    h-11 px-3
                    rounded-xl bg-(--background-secondary) border border-form-element
                    flex items-center cursor-pointer
                    hover:bg-(--background-secondary-hover)
                    disabled:opacity-40 disabled:cursor-not-allowed
                "
            >
                {/* Same footprint as the single-select set dropdown: one w-16 logo (first pick) + "+N" for extras */}
                {(() => {
                    const shown = selectedOptions[0];
                    const image = shown?.image ?? defaultImage;
                    return (
                        <>
                            {image
                                ? <img src={image} alt={shown?.value ?? 'default set'} className="object-contain object-center h-6 w-16 mr-1" />
                                : <span className="text-xs whitespace-nowrap truncate max-w-28 md:max-w-56 mr-1">{shown ? (shown.label ?? shown.value) : placeholder}</span>}
                            {selectedOptions.length > 1 && <span className="text-xs text-secondary whitespace-nowrap">+{selectedOptions.length - 1}</span>}
                        </>
                    );
                })()}
                <FaCaretDown className={`ml-1 opacity-75 ${isOpen ? 'rotate-180' : ''}`} size={16} />
            </button>

            {isOpen && !disabled && createPortal(
                <div
                    ref={menuRef}
                    style={{ left: menuPos.left, top: menuPos.top, minWidth: menuPos.minWidth }}
                    className="
                        fixed z-1000 mt-1 max-h-[60vh]
                        bg-(--background-primary) rounded-xl shadow-lg
                        border border-(--background-tertiary)
                        overflow-auto scrollbar-hide
                    "
                >
                    <div className="flex justify-between px-3 py-2 gap-5 text-xs border-b border-(--background-tertiary) bg-(--background-secondary)">
                        <button type="button" onClick={() => onChange(options.map(o => o.value))} className="text-primary cursor-pointer">Select All</button>
                        <button type="button" onClick={() => onChange([])} className="text-secondary cursor-pointer">Clear All</button>
                    </div>
                    {options.map((option, index) => {
                        const isSelected = selections.includes(option.value);
                        const showGroupHeader = option.group !== undefined && option.group !== options[index - 1]?.group;
                        return (
                            <Fragment key={option.value}>
                                {showGroupHeader && (
                                    <div className="px-3 pt-2 pb-1 text-[10px] font-bold uppercase tracking-wide text-(--text-tertiary) bg-(--background-secondary)">
                                        {option.group}
                                    </div>
                                )}
                                <div
                                    onClick={() => toggle(option.value)}
                                    className={`
                                        flex items-center gap-3 px-3 py-2 cursor-pointer
                                        hover:bg-(--background-secondary)
                                        border-b border-(--background-tertiary) last:border-b-0
                                        ${isSelected ? 'bg-primary/10' : ''}
                                    `}
                                >
                                    <div className={`flex items-center justify-center w-4 h-4 border rounded shrink-0 ${isSelected ? 'bg-primary border-primary' : 'border-(--border-primary)'}`}>
                                        {isSelected && <FaCheck className="h-2 w-2" />}
                                    </div>
                                    {option.image
                                        ? <img src={option.image} alt={option.value} className="object-contain object-center h-6 w-16" />
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
