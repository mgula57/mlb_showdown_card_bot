import type { ReactNode } from 'react';
import { InlineError } from './InlineError';
import { buttonClass } from './buttonStyles';

type RetryableErrorProps = {
    children: ReactNode;
    onRetry: () => void;
    /** Other actions after Try again, such as a way back. */
    actions?: ReactNode;
    className?: string;
};

/** An `InlineError` for something that failed to load, with a Try again button under it (see frontend/DESIGN.md). */
export function RetryableError({ children, onRetry, actions, className = '' }: RetryableErrorProps) {
    return (
        <div className={`flex flex-col items-start gap-2 ${className}`}>
            <InlineError size="md" icon>{children}</InlineError>
            <div className="flex flex-wrap gap-2">
                <button type="button" onClick={onRetry} className={buttonClass('secondary', 'sm')}>Try again</button>
                {actions}
            </div>
        </div>
    );
}
