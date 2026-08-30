import FormDropdown from '../customs/FormDropdown';
import { MANAGER_FIELDS, type ManagerPreference } from '../../api/manager';

type Props = {
    value: ManagerPreference;
    onChange: (next: ManagerPreference) => void;
    /** Heading above the four dropdowns. Defaults to "Manager style"; the single-game modal
     *  passes "Away manager" / "Home manager" to tell the two sides apart. */
    title?: string;
    disabled?: boolean;
    /** Extra classes on the wrapper — pass `col-span-full` when dropped into a `FormSection` grid. */
    className?: string;
};

/**
 * Four 1–5 dropdowns that set the team-wide tendencies for one club: steal aggression, extra-base
 * aggression, bullpen hook, and closer usage. Level 3 (the default everywhere) is neutral and a
 * no-op in the engine. Only the club being taken over is affected — every other team plays its
 * default style.
 */
export default function ManagerStyleFields({ value, onChange, title = 'Manager style', disabled, className = '' }: Props) {
    return (
        <div className={`flex flex-col gap-2 ${className}`}>
            <div className="text-[13px] font-bold text-(--text-secondary)">{title}</div>
            <p className="text-[11px] text-(--text-tertiary)">
                Sets how this club manages — 3 is the default, neutral setting. Only the club you
                control is affected.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {MANAGER_FIELDS.map(field => (
                    <FormDropdown
                        key={field.key}
                        label={field.label}
                        options={field.options}
                        selectedOption={String(value[field.key])}
                        onChange={next => onChange({ ...value, [field.key]: Number(next) })}
                        disabled={disabled}
                    />
                ))}
            </div>
        </div>
    );
}
