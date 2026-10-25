import { useState } from 'react';
import { InfoTooltip } from './InfoTooltip';
import { FIELD_FRAME_CLASS } from './fieldStyles';

type PercentageSliderProps = {
    label: string;
    /** Explanation shown in an (i) tooltip beside the label. */
    info?: string;
    /** Whole-number percentage, 0-100. */
    value: number;
    onChange: (value: number) => void;
    /** Tailwind background class for the filled portion of the bar. */
    fillClassName?: string;
    disabled?: boolean;
};

const clampPercent = (n: number) => Math.min(100, Math.max(0, Math.round(n)));

/** A draggable fill bar with a typeable % input at the end, for editing one share of a whole. */
export default function PercentageSlider({ label, info, value, onChange, fillClassName = 'bg-(--showdown-red)', disabled = false }: PercentageSliderProps) {
    // Holds the raw text while typing so clearing the field doesn't snap it back to 0.
    const [draft, setDraft] = useState<string | null>(null);
    const percent = clampPercent(value);

    return (
        <div className={`flex items-center gap-3 ${disabled ? 'opacity-50' : ''}`}>
            <span className={`${info ? 'w-20' : 'w-16'} shrink-0 flex items-center gap-1 text-[12px] font-semibold text-(--text-secondary)`}>
                {label}
                {info && <InfoTooltip text={info} openOnHover />}
            </span>

            <div className="relative flex-1 h-6 rounded-control bg-(--background-quaternary) overflow-hidden">
                <div className={`absolute inset-y-0 left-0 ${fillClassName}`} style={{ width: `${percent}%` }} />
                <input
                    type="range"
                    min={0}
                    max={100}
                    step={1}
                    value={percent}
                    disabled={disabled}
                    aria-label={label}
                    onChange={e => onChange(Number(e.target.value))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />
            </div>

            <div className={`flex items-center shrink-0 pr-2 ${FIELD_FRAME_CLASS}`}>
                <input
                    type="number"
                    inputMode="numeric"
                    min={0}
                    max={100}
                    value={draft ?? String(percent)}
                    disabled={disabled}
                    aria-label={`${label} percentage`}
                    onChange={e => {
                        setDraft(e.target.value);
                        if (e.target.value !== '') onChange(clampPercent(Number(e.target.value)));
                    }}
                    onBlur={() => setDraft(null)}
                    className="w-11 bg-transparent py-1 pl-2 text-right text-[12px] font-bold tabular-nums text-(--text-primary) outline-none
                        [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none
                        disabled:cursor-not-allowed"
                />
                <span className="text-[12px] text-(--text-tertiary)">%</span>
            </div>
        </div>
    );
}
