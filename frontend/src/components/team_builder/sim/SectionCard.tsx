import type { ReactNode } from 'react';

/** Titled panel used across the sim result and progress screens. A diagonal gradient, a hairline
 * border, and a soft shadow stand in for a flat background fill, so each section reads as a
 * distinct, considered panel rather than a plain color block. */
export function SectionCard({ title, count, children }: { title: string; count?: number; children: ReactNode }) {
    return (
        <div className="rounded-xl border border-(--divider) bg-linear-to-br from-(--background-tertiary) to-(--background-secondary) p-3 flex flex-col gap-2 min-w-0 shadow-sm">
            <p className="text-[12px] font-bold text-(--text-primary)">
                {title}
                {count != null && <span className="text-(--text-tertiary) font-semibold"> · {count}</span>}
            </p>
            {children}
        </div>
    );
}
