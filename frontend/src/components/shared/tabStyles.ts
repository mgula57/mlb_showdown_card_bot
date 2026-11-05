/**
 * @fileoverview Class-string builders for the app's underline tab style — condensed italic caps
 * over a hairline, with a red bar under the active tab (see frontend/DESIGN.md). `tabButtonClass` is for plain
 * controlled buttons (used by `Tabs.tsx` and by call sites rendering their own button outside a
 * Radix `Tabs.Root`); `radixTabTriggerClass` is the same tokens for Radix's `Tabs.Trigger`, which
 * tracks active state itself via `data-state` rather than a boolean prop. Kept in a separate,
 * component-free module so `Tabs.tsx` stays Fast-Refresh-friendly.
 */
export type TabSize = 'sm' | 'md';

const SIZE_CLASSES: Record<TabSize, string> = {
    sm: 'px-2 pt-1.5 pb-1 text-[14px]',
    md: 'px-3 pt-2 pb-1.5 text-base',
};

const BASE_TRIGGER_CLASS = 'flex items-center justify-center gap-1.5 whitespace-nowrap font-display uppercase leading-none border-b-[3px] transition-colors cursor-pointer';

// Wraps a row of tab triggers: bottom border, horizontal scroll on mobile instead of wrapping.
export function tabListClass(fullWidth = false, className = '', hideBorder = false): string {
    return `${fullWidth ? 'flex' : 'inline-flex'} items-end gap-x-2 ${hideBorder ? '' : 'border-b border-(--divider)'} pt-1 overflow-x-auto scrollbar-hide ${className}`;
}

export function tabButtonClass(active: boolean, size: TabSize = 'md', fullWidth = false): string {
    return `${BASE_TRIGGER_CLASS} ${SIZE_CLASSES[size]} ${fullWidth ? 'flex-1' : ''} ${
        active
            ? 'border-(--showdown-red) text-(--text-primary)'
            : 'border-transparent text-(--text-tertiary) hover:text-(--text-primary)'
    }`;
}

export function radixTabTriggerClass(size: TabSize = 'md', fullWidth = false): string {
    return `${BASE_TRIGGER_CLASS} ${SIZE_CLASSES[size]} ${fullWidth ? 'flex-1' : ''} ` +
        'data-[state=active]:border-(--showdown-red) data-[state=active]:text-(--text-primary) ' +
        'data-[state=inactive]:border-transparent data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:hover:text-(--text-primary)';
}

// design-ok-start: the vertical tab primitive the custom-tab rule points to
/** A Radix trigger in a vertical nav list (the Seasons sidebar): the same red bar, on the left
 *  edge, over a quiet fill, in the body face since rows carry icons and badges. */
export function radixVerticalTabTriggerClass(): string {
    return 'flex items-center gap-x-2 px-3 py-2.5 text-sm rounded-r-control border-l-[3px] transition-colors cursor-pointer ' +
        'data-[state=active]:border-(--showdown-red) data-[state=active]:bg-(--background-tertiary) data-[state=active]:text-(--text-primary) data-[state=active]:font-semibold ' +
        'data-[state=inactive]:border-transparent data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:font-medium data-[state=inactive]:hover:text-(--text-primary) data-[state=inactive]:hover:bg-(--background-tertiary)/60';
}
// design-ok-end
