import type { ReactNode } from 'react';
import { FaTriangleExclamation } from 'react-icons/fa6';

/** Compact red validation message shown under a form field or group. */
export default function InlineWarning({ children }: { children: ReactNode }) {
    return (
        <div className="text-[11px] text-red-400 px-2 py-1.5 rounded-md border border-red-400/30 bg-red-400/5 flex items-center gap-1.5">
            <FaTriangleExclamation className="shrink-0" />
            {children}
        </div>
    );
}
