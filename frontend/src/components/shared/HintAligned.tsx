/**
 * @fileoverview HintAligned - lines a grid field up with a neighbor that has hint text below it
 */

import React from 'react';

/** Hint line under a form field. Shared so `HintAligned`'s spacer is exactly one hint tall. */
export const FIELD_HINT_CLASS = 'text-[11px] text-(--text-tertiary)';

/** Bottom-aligns a field in its grid row and reserves one invisible hint line beneath it, so its
 * input lines up with a neighbor's input (e.g. YearsInput) instead of that neighbor's hint text. */
export default function HintAligned({ children }: { children: React.ReactNode }) {
    return (
        <div className="self-end flex flex-col gap-1.5">
            {children}
            <span aria-hidden className={`invisible ${FIELD_HINT_CLASS}`}>&nbsp;</span>
        </div>
    );
}
