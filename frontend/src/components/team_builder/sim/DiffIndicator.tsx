import { FaCaretUp, FaCaretDown, FaMinus } from 'react-icons/fa6';
import type { StatDiff } from './simStatColumns';

/** Renders a `computeDiff` result (`simStatColumns.ts`) as a colored up/down/flat caret plus the
 * absolute magnitude, formatted by the caller (percent, rate, whatever fits the stat). */
export function DiffBadge({ diff, format }: { diff: StatDiff; format: (absMagnitude: number) => string }) {
    return (
        <span className={`inline-flex items-center gap-0.5 font-semibold ${
            diff.direction === 'flat' ? 'text-(--text-tertiary)' : diff.isGood ? 'text-(--success)' : 'text-(--error)'
        }`}>
            {diff.direction === 'up' && <FaCaretUp className="text-[12px]" />}
            {diff.direction === 'down' && <FaCaretDown className="text-[12px]" />}
            {diff.direction === 'flat' && <FaMinus className="text-[8px]" />}
            {format(Math.abs(diff.magnitude))}
        </span>
    );
}
