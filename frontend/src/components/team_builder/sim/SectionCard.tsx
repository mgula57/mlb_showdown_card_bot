import type { ReactNode } from 'react';

/** Titled panel used across the sim result and progress screens. */
export function SectionCard({ title, children }: { title: string; children: ReactNode }) {
    return (
        <div className="rounded-xl bg-(--background-tertiary) p-3 flex flex-col gap-2 min-w-0">
            <p className="text-[12px] font-bold text-(--text-primary)">{title}</p>
            {children}
        </div>
    );
}
