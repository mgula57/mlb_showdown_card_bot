import { useEffect, useState } from "react";
import FormInput from "./FormInput";

type NumberInputProps = {
    label: string;
    /** Committed numeric value, already carrying whatever default the caller wants shown. */
    value: number;
    onChange: (value: number) => void;
    className?: string;
    step?: number | string;
};

/**
 * Numeric FormInput backed by local draft text, so the field can be cleared and
 * retyped freely instead of snapping back to `value` on every keystroke. The
 * default only reasserts itself if the field is left empty on blur.
 */
export default function NumberInput({ label, value, onChange, className, step }: NumberInputProps) {
    const [draft, setDraft] = useState(String(value));

    useEffect(() => {
        setDraft(String(value));
    }, [value]);

    return (
        <FormInput
            label={label}
            className={className}
            type="number"
            step={step}
            value={draft}
            onChange={v => {
                const next = v ?? "";
                setDraft(next);
                const n = Number(next);
                if (next.trim() !== "" && Number.isFinite(n)) onChange(n);
            }}
            onBlur={() => setDraft(String(value))}
        />
    );
}
