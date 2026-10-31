import { useState } from 'react';
import { FaPlus, FaXmark } from 'react-icons/fa6';
import FormInput from '../customs/FormInput';
import { InlineError } from '../shared/InlineError';
import { FIELD_LABEL_CLASS, fieldClass } from '../shared/fieldStyles';
import { choiceClass } from '../shared/choiceStyles';
import { parseYearsValue, serializeYears, validateYears, MIN_YEAR, MAX_YEAR } from './years';
import type { YearsMode, YearsDraft } from './years';

const MODES: { value: YearsMode; label: string }[] = [
    { value: 'single', label: 'One Year' },
    { value: 'range', label: 'Range' },
    { value: 'list', label: 'Specific Years' },
];

const digitsOnly = (value: string | null) => (value ?? '').replace(/\D/g, '').slice(0, 4);

type YearsInputProps = {
    /** Years in the backend's string format: "2023", "2000-2004" or "2006+2014". Empty while incomplete or invalid. */
    value: string;
    onChange: (value: string) => void;
    className?: string;
};

/** Picks the years a set draws from. Edits the backend's string format through guided fields
 * (one year, a from/to range, or a list of years) so a typo can't produce an unparseable value.
 * Emits '' while the entry is incomplete or invalid, which keeps Run disabled. */
export default function YearsInput({ value, onChange, className = '' }: YearsInputProps) {
    const [draft, setDraft] = useState<YearsDraft>(() => parseYearsValue(value));
    const [listEntry, setListEntry] = useState('');
    // The last value this input emitted (or read in) - anything else is an outside change
    const [syncedValue, setSyncedValue] = useState(value);

    // A template or reload swapped the value from outside - re-read it into the fields
    if (value !== syncedValue) {
        setSyncedValue(value);
        setDraft(parseYearsValue(value));
    }

    const validation = validateYears(draft);

    function update(next: YearsDraft) {
        setDraft(next);
        const serialized = validateYears(next).error ? '' : serializeYears(next);
        setSyncedValue(serialized);
        onChange(serialized);
    }

    function changeMode(mode: YearsMode) {
        if (mode === draft.mode) return;
        // Carry the current years over so switching modes doesn't lose what was typed
        const first = draft.mode === 'single' ? draft.single : draft.mode === 'range' ? draft.from : String(draft.list[0] ?? '');
        const last = draft.mode === 'range' ? draft.to : first;
        update({ ...draft, mode, single: first, from: first, to: last, list: draft.mode === 'list' ? draft.list : first ? [Number(first)] : [] });
    }

    function addListYears() {
        const entered = (listEntry.match(/\d+/g) ?? []).map(Number);
        if (entered.length === 0) return;
        const invalid = entered.find(year => year < MIN_YEAR || year > MAX_YEAR);
        if (invalid !== undefined) {
            setListEntry(listEntry);
            return;
        }
        update({ ...draft, list: [...new Set([...draft.list, ...entered])].sort((a, b) => a - b) });
        setListEntry('');
    }

    const listEntryError = (() => {
        const entered = (listEntry.match(/\d+/g) ?? []).map(Number);
        const invalid = entered.find(year => year < MIN_YEAR || year > MAX_YEAR);
        return invalid === undefined ? null : `${invalid} isn't a valid year (${MIN_YEAR}-${MAX_YEAR}).`;
    })();

    // Only complain once there's something to complain about - an empty field isn't an error yet
    const showError = validation.error && !validation.isBlank;

    return (
        <div className={`flex flex-col gap-1.5 ${className}`}>
            <span className={FIELD_LABEL_CLASS}>Years</span>
            <div className="flex flex-wrap gap-1.5" role="group" aria-label="Years format">
                {MODES.map(mode => (
                    <button
                        key={mode.value}
                        type="button"
                        onClick={() => changeMode(mode.value)}
                        aria-pressed={draft.mode === mode.value}
                        className={choiceClass(draft.mode === mode.value, 'sm')}
                    >
                        {mode.label}
                    </button>
                ))}
            </div>

            {draft.mode === 'single' && (
                <FormInput
                    label="Year"
                    inputMode="numeric"
                    maxLength={4}
                    placeholder={String(MAX_YEAR)}
                    value={draft.single}
                    onChange={v => update({ ...draft, single: digitsOnly(v) })}
                />
            )}

            {draft.mode === 'range' && (
                <div className="grid grid-cols-2 gap-2">
                    <FormInput
                        label="From"
                        inputMode="numeric"
                        maxLength={4}
                        placeholder="2000"
                        value={draft.from}
                        onChange={v => update({ ...draft, from: digitsOnly(v) })}
                    />
                    <FormInput
                        label="To"
                        inputMode="numeric"
                        maxLength={4}
                        placeholder="2004"
                        value={draft.to}
                        onChange={v => update({ ...draft, to: digitsOnly(v) })}
                    />
                </div>
            )}

            {draft.mode === 'list' && (
                <>
                    <div className="flex items-stretch gap-2">
                        <input
                            type="text"
                            inputMode="numeric"
                            value={listEntry}
                            placeholder="Add a year, e.g. 2006"
                            aria-label="Add a year"
                            autoComplete="off"
                            spellCheck={false}
                            onChange={e => setListEntry(e.target.value.replace(/[^\d,\s+]/g, ''))}
                            onKeyDown={e => {
                                if (e.key === 'Enter') {
                                    e.preventDefault();
                                    addListYears();
                                }
                            }}
                            className={`min-w-0 flex-1 focus:outline-none ${fieldClass('md')}`}
                        />
                        <button
                            type="button"
                            onClick={addListYears}
                            disabled={listEntry.trim() === '' || !!listEntryError}
                            className={`${choiceClass(false, 'md')} gap-1.5`}
                        >
                            <FaPlus className="text-[10px]" /> Add
                        </button>
                    </div>
                    {listEntryError && <InlineError icon>{listEntryError}</InlineError>}
                    {draft.list.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                            {draft.list.map(year => (
                                <span key={year} className="inline-flex items-center gap-1 rounded-control border border-(--divider) py-0.5 pl-2 pr-0.5 text-[12px] font-semibold tabular-nums text-(--text-secondary)">
                                    {year}
                                    <button
                                        type="button"
                                        onClick={() => update({ ...draft, list: draft.list.filter(y => y !== year) })}
                                        aria-label={`Remove ${year}`}
                                        className="flex items-center justify-center w-4 h-4 rounded-full text-(--text-tertiary) hover:bg-(--red)/90 hover:text-white transition-colors cursor-pointer"
                                    >
                                        <FaXmark className="text-[10px]" />
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                </>
            )}

            {showError ? (
                <InlineError icon>{validation.error}</InlineError>
            ) : (
                <p className="text-[11px] text-(--text-tertiary)">
                    {draft.mode === 'single' && 'Every card comes from this season.'}
                    {draft.mode === 'range' && 'Every season from the first year through the last (inclusive).'}
                    {draft.mode === 'list' && 'Only these seasons, like a Super Season mix. Paste several at once, separated by commas.'}
                </p>
            )}
        </div>
    );
}
