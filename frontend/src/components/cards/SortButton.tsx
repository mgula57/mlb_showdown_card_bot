import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import type { SelectOption } from '../shared/CustomSelect';

type SortOptionGroup = {
    label: string;
    options: SelectOption[];
};

type SortButtonProps = {
    selectedOption: SelectOption | null;
    sortDirection: string;
    sortOptionGroups: SortOptionGroup[];
    onSortByChange: (value: string) => void;
    onSortDirectionChange: (direction: string) => void;
    disableSortBy?: boolean;
    disableSortDirection?: boolean;
};

const SortButton: React.FC<SortButtonProps> = ({
    selectedOption,
    sortDirection,
    sortOptionGroups,
    onSortByChange,
    onSortDirectionChange,
    disableSortBy = false,
    disableSortDirection = false,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [openAbove, setOpenAbove] = useState(false);
    const [menuPos, setMenuPos] = useState<{ left: number; top: number; minWidth: number; maxWidth: number; maxHeight: number }>(
        { left: 0, top: 0, minWidth: 0, maxWidth: 400, maxHeight: 400 }
    );

    const buttonRef = useRef<HTMLDivElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const measureAndSetDirection = () => {
        if (!buttonRef.current) return;
        const btnRect = buttonRef.current.getBoundingClientRect();
        const spaceBelow = window.innerHeight - btnRect.bottom;
        const spaceAbove = btnRect.top;
        const menuH = dropdownRef.current?.getBoundingClientRect().height ?? 300;
        const MARGIN = 8;

        const shouldOpenAbove = spaceBelow < menuH && spaceAbove > spaceBelow;
        setOpenAbove(shouldOpenAbove);

        const maxHeight = (shouldOpenAbove ? spaceAbove : spaceBelow) - MARGIN;
        const minWidth = btnRect.width;
        const maxWidth = Math.min(240, window.innerWidth - btnRect.left - MARGIN);
        const left = Math.min(btnRect.left, window.innerWidth - maxWidth - MARGIN);

        setMenuPos({
            left: Math.max(0, left),
            top: shouldOpenAbove ? btnRect.top : btnRect.bottom,
            minWidth,
            maxWidth,
            maxHeight,
        });
    };

    useEffect(() => {
        if (!isOpen) return;

        measureAndSetDirection();

        const handleUpdate = () => measureAndSetDirection();
        const handleClickOutside = (e: MouseEvent) => {
            const target = e.target;
            if (!(target instanceof Node)) return;
            if (
                dropdownRef.current && !dropdownRef.current.contains(target) &&
                buttonRef.current && !buttonRef.current.contains(target)
            ) {
                setIsOpen(false);
            }
        };

        window.addEventListener('resize', handleUpdate);
        window.addEventListener('scroll', handleUpdate, true);
        document.addEventListener('mousedown', handleClickOutside);

        return () => {
            window.removeEventListener('resize', handleUpdate);
            window.removeEventListener('scroll', handleUpdate, true);
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

    if (!selectedOption) return null;

    return (
        <div ref={buttonRef} className="relative shrink-0">
            <div className="flex items-center bg-(--background-secondary) border border-form-element rounded-full text-sm text-nowrap overflow-hidden">
                <button
                    type="button"
                    className="flex flex-row gap-1 items-center px-2 py-1 cursor-pointer hover:bg-(--background-secondary-hover) disabled:opacity-40 disabled:cursor-not-allowed"
                    disabled={disableSortBy}
                    onClick={() => !disableSortBy && setIsOpen(prev => !prev)}
                >
                    <span className="text-primary font-semibold">Sort:</span>
                    {selectedOption.icon && <span className="text-primary">{selectedOption.icon}</span>}
                    <span>{selectedOption.label ?? 'N/A'}</span>
                </button>
                <button
                    type="button"
                    className="px-2 py-1 border-l border-form-element cursor-pointer hover:bg-(--background-secondary-hover) disabled:opacity-40 disabled:cursor-not-allowed font-semibold"
                    disabled={disableSortDirection}
                    onClick={() => onSortDirectionChange(sortDirection === 'asc' ? 'desc' : 'asc')}
                >
                    {sortDirection === 'asc' ? '↑' : '↓'}
                </button>
            </div>

            {isOpen && typeof document !== 'undefined' && createPortal(
                <div
                    ref={dropdownRef}
                    className={`
                        fixed z-1000
                        ${openAbove ? '-translate-y-full -mt-1' : 'mt-1'}
                        bg-(--background-primary) rounded-xl shadow-lg
                        border border-(--background-tertiary)
                        overflow-auto
                    `}
                    style={{
                        left: menuPos.left,
                        top: menuPos.top,
                        minWidth: menuPos.minWidth,
                        maxWidth: menuPos.maxWidth,
                        maxHeight: menuPos.maxHeight,
                    }}
                >
                    {sortOptionGroups.map(group => (
                        <div key={group.label}>
                            <div className="px-3 pt-3 pb-1 text-xs font-semibold text-tertiary uppercase tracking-wider select-none">
                                {group.label}
                            </div>
                            {group.options.map(option => (
                                <div
                                    key={option.value}
                                    className={`
                                        px-3 py-2
                                        cursor-pointer hover:bg-(--background-secondary)
                                        border-b border-(--background-tertiary) last:border-b-0
                                        flex items-center gap-2
                                        ${option.value === selectedOption.value ? 'bg-(--background-secondary) font-semibold' : ''}
                                    `}
                                    onClick={() => {
                                        onSortByChange(option.value);
                                        setIsOpen(false);
                                    }}
                                >
                                    {option.icon && <span className="text-primary shrink-0">{option.icon}</span>}
                                    <span className="flex-1 text-sm">{option.label}</span>
                                    {option.value === selectedOption.value && (
                                        <span className="ml-auto text-blue-400 text-xs">✓</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    ))}
                </div>,
                document.body
            )}
        </div>
    );
};

export default SortButton;
