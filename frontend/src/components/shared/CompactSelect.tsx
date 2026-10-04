type CompactSelectOption = { label: string; value: string };

type CompactSelectProps = {
    /** Small uppercase label rendered inside the control, before the selected value. */
    label: string;
    options: CompactSelectOption[];
    value: string;
    onChange: (value: string) => void;
    className?: string;
};

/** Compact single-row select with an inline label (e.g. "GROUP Team") — for toolbars where a stacked FormDropdown is too tall. */
export default function CompactSelect({ label, options, value, onChange, className }: CompactSelectProps) {
    return (
        <label className={`flex items-center h-9 rounded-lg border border-(--divider) hover:border-(--text-tertiary) transition-colors text-[13px] cursor-pointer focus-within:border-(--secondary) ${className ?? ''}`}>
            <span className="pl-2.5 pr-1 text-[10px] font-bold text-(--text-tertiary) uppercase tracking-wide whitespace-nowrap">{label}</span>
            <select
                value={value}
                onChange={e => onChange(e.target.value)}
                className="h-full pr-2 bg-transparent font-semibold text-(--text-primary) focus:outline-none cursor-pointer"
            >
                {options.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
            </select>
        </label>
    );
}
