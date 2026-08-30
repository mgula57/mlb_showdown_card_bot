/**
 * @fileoverview Class-string builders for the app's underline tab style — a bottom border with a
 * filled pill only on the active tab, no standing background track. `tabButtonClass` is for plain
 * controlled buttons (used by `Tabs.tsx` and by call sites rendering their own button outside a
 * Radix `Tabs.Root`); `radixTabTriggerClass` is the same tokens for Radix's `Tabs.Trigger`, which
 * tracks active state itself via `data-state` rather than a boolean prop. Kept in a separate,
 * component-free module so `Tabs.tsx` stays Fast-Refresh-friendly.
 */
export type TabSize = 'sm' | 'md';

const SIZE_CLASSES: Record<TabSize, string> = {
    sm: 'px-3 py-1.5 text-[13px]',
    md: 'px-4 py-2 text-sm',
};

const BASE_TRIGGER_CLASS = 'flex items-center justify-center gap-1.5 rounded-lg whitespace-nowrap transition-colors cursor-pointer';

// Wraps a row of tab triggers: bottom border, horizontal scroll on mobile instead of wrapping.
export function tabListClass(fullWidth = false, className = '', hideBorder = false): string {
    return `${fullWidth ? 'flex' : 'inline-flex'} items-center gap-x-1 ${hideBorder ? '' : 'border-b border-(--divider)'} py-1 overflow-x-auto scrollbar-hide ${className}`;
}

export function tabButtonClass(active: boolean, size: TabSize = 'md', fullWidth = false): string {
    return `${BASE_TRIGGER_CLASS} ${SIZE_CLASSES[size]} ${fullWidth ? 'flex-1' : ''} ${
        active
            ? 'bg-(--background-quaternary) text-(--text-primary) font-bold'
            : 'text-(--text-tertiary) font-medium hover:bg-(--divider)'
    }`;
}

export function radixTabTriggerClass(size: TabSize = 'md', fullWidth = false): string {
    return `${BASE_TRIGGER_CLASS} ${SIZE_CLASSES[size]} ${fullWidth ? 'flex-1' : ''} ` +
        'data-[state=active]:bg-(--background-quaternary) data-[state=active]:text-(--text-primary) data-[state=active]:font-bold ' +
        'data-[state=inactive]:text-(--text-tertiary) data-[state=inactive]:font-medium data-[state=inactive]:hover:bg-(--divider)';
}
