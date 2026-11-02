import { FaPen, FaTriangleExclamation } from 'react-icons/fa6';
import FormInput from '../customs/FormInput';
import { buttonClass } from '../shared/buttonStyles';
import { FIELD_LABEL_CLASS } from '../shared/fieldStyles';
import { parseSetSize, scopeSummary } from './editionScope';
import type { EditionScope, OutsideScopeCounts } from './editionScope';

const plural = (count: number, word: string) => `${count} ${word}${count === 1 ? '' : 's'}`;

/** Saved cards outside the scope. Soft: they stay in the pool, this only says what a Replace run would do. */
export function OutsideScopeNotice({ outside }: { outside: OutsideScopeCounts }) {
    const parts = [
        ...(outside.years > 0 ? [`${plural(outside.years, 'card')} from other seasons`] : []),
        ...(outside.sets > 0 ? [`${plural(outside.sets, 'card')} from other showdown sets`] : []),
    ];
    if (parts.length === 0) return null;
    return (
        <div role="status" className="flex items-start gap-1.5 rounded-control border border-(--divider) px-2.5 py-1.5 text-[11px] text-(--text-secondary)">
            <FaTriangleExclamation className="shrink-0 mt-0.5 text-(--warning)" />
            <span>
                {parts.join(' and ')} in the pool fall outside the edition scope. They stay in the pool, but running the Algorithm with Replace will drop them.
            </span>
        </div>
    );
}

type ScopeSummaryProps = {
    scope: EditionScope;
    outside: OutsideScopeCounts;
    /** Set size is the one scope field editable from the pool too. */
    onSetSizeChange: (size: number) => void;
    onEdit: () => void;
};

/** The edition's scope as the Player Pool step shows it: read-only, except set size, with a way back to Setup. */
export function ScopeSummary({ scope, outside, onSetSizeChange, onEdit }: ScopeSummaryProps) {
    const summary = scopeSummary(scope, { withSize: false });
    return (
        <div className="flex flex-col gap-2 px-3 py-2.5 border-b border-(--divider)">
            <div className="flex items-end gap-3">
                <FormInput
                    label="Set Size"
                    type="number"
                    className="w-24 shrink-0"
                    value={scope.set_size}
                    onChange={value => onSetSizeChange(parseSetSize(value))}
                />
                <div className="flex-1 min-w-0 flex flex-col gap-0.5 pb-1.5">
                    <span className={FIELD_LABEL_CLASS}>Edition Scope</span>
                    <span title={summary} className="text-[12px] font-semibold text-(--text-secondary) truncate">{summary}</span>
                </div>
                <button type="button" onClick={onEdit} title="Change the years, sets and other edition settings in Setup" className={buttonClass('secondary', 'sm', 'shrink-0')}>
                    <FaPen className="text-[10px]" /> Edit
                </button>
            </div>
            <OutsideScopeNotice outside={outside} />
        </div>
    );
}
