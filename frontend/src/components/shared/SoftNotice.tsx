import type { ReactNode } from 'react';
import { FaTriangleExclamation } from 'react-icons/fa6';

/** A neutral bordered note with a warning triangle, for something allowed but worth knowing
 *  (see DESIGN.md). Use `InlineError` only when something is wrong or blocked. */
export function SoftNotice({ children, className = '' }: { children: ReactNode; className?: string }) {
    return (
        <div role="status" className={`flex items-start gap-1.5 rounded-control border border-(--divider) px-2.5 py-1.5 text-[11px] text-(--text-secondary) ${className}`}>
            <FaTriangleExclamation className="shrink-0 mt-0.5 text-(--warning)" />
            <div className="flex-1 min-w-0">{children}</div>
        </div>
    );
}
