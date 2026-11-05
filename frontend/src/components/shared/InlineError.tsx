import type { ReactNode } from 'react';
import { FaTriangleExclamation } from 'react-icons/fa6';

const SIZE_CLASSES = {
    sm: 'text-[11px] px-2 py-1.5',
    md: 'text-[12px] px-3 py-2',
} as const;

type InlineErrorProps = {
    children: ReactNode;
    size?: keyof typeof SIZE_CLASSES;
    icon?: boolean;
    className?: string;
};

/**
 * Small red notice that sits inline with a form or panel: a validation message, a failed
 * upload, a sim that couldn't start (see frontend/DESIGN.md). Page-level failures use the
 * builder's larger error box instead. `icon` leads with a warning triangle, for validation
 * messages under a field or group.
 */
export function InlineError({ children, size = 'sm', icon = false, className = '' }: InlineErrorProps) {
    return (
        <div role="alert" className={`text-(--red) rounded-control border border-(--red)/30 bg-(--red)/5 ${SIZE_CLASSES[size]} ${icon ? 'flex items-center gap-1.5' : ''} ${className}`}>
            {icon && <FaTriangleExclamation className="shrink-0" />}
            {children}
        </div>
    );
}

export default InlineError;
