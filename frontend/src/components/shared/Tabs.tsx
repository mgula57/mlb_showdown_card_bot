/**
 * @fileoverview Underline tab group — the neutral, taller style first built for TeamDetail's
 * Depth Chart/Lineup/Draft tabs. For call sites built on Radix's `Tabs.Root` (which need
 * `Tabs.Trigger`/`Tabs.Content` for panel switching), use `tabListClass`/`radixTabTriggerClass`
 * from `tabStyles.ts` directly instead of this component, so every tab strip in the app — plain
 * or Radix — looks and behaves identically, including horizontal scroll on mobile when there
 * isn't room for every tab.
 */
import type { ReactNode } from 'react';
import { tabListClass, tabButtonClass, type TabSize } from './tabStyles';

export type TabItem<T extends string = string> = {
    id: T;
    label: string;
    // Shown instead of `label` below the `sm` breakpoint, when tabs are full width and space is tight.
    shortLabel?: string;
    icon?: ReactNode;
    title?: string;
};

type TabsProps<T extends string> = {
    tabs: TabItem<T>[];
    value: T;
    onChange: (id: T) => void;
    // Tabs stretch to fill the container width (TeamBuilder's top-level tabs). Default: inline,
    // sized to content (view switchers, sort toggles).
    fullWidth?: boolean;
    size?: TabSize;
    className?: string;
};

export function Tabs<T extends string>({ tabs, value, onChange, fullWidth = false, size = 'md', className = '' }: TabsProps<T>) {
    return (
        <div className={tabListClass(fullWidth, className)}>
            {tabs.map(tab => (
                <button
                    key={tab.id}
                    type="button"
                    title={tab.title}
                    onClick={() => onChange(tab.id)}
                    className={tabButtonClass(value === tab.id, size, fullWidth)}
                >
                    {tab.icon && <span>{tab.icon}</span>}
                    {tab.shortLabel ? (
                        <>
                            <span className="hidden sm:inline">{tab.label}</span>
                            <span className="sm:hidden">{tab.shortLabel}</span>
                        </>
                    ) : (
                        <span>{tab.label}</span>
                    )}
                </button>
            ))}
        </div>
    );
}
