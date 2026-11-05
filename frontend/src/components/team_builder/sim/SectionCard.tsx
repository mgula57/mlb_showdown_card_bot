import type { ReactNode } from 'react';
import { InfoTooltip } from '../../shared/InfoTooltip';

/** Titled panel used across the sim result and progress screens: a flat surface with a hairline
 * border (see frontend/DESIGN.md). `info` adds a click-to-reveal tooltip next to the title for
 * context that doesn't fit in the title alone. */
export function SectionCard({ title, count, info, children }: { title: string; count?: number; info?: string; children: ReactNode }) {
    return (
        <div className="rounded-card border border-(--divider) bg-(--background-secondary) p-3 flex flex-col gap-2 min-w-0">
            <p className="flex items-center gap-1.5 text-[12px] font-bold text-(--text-primary)">
                {title}
                {count != null && <span className="text-(--text-tertiary) font-semibold"> · {count}</span>}
                {info && <InfoTooltip text={info} />}
            </p>
            {children}
        </div>
    );
}
