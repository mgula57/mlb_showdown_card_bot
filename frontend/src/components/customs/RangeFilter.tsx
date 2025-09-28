import FormInput from "./FormInput";
import { FaTimes } from "react-icons/fa";

type Props = {
    label: string;
    minValue?: number;
    maxValue?: number;
    onMinChange: (n?: number) => void;
    onMaxChange: (n?: number) => void;
    className?: string;
};

export default function RangeFilter({
    label,
    minValue,
    maxValue,
    onMinChange,
    onMaxChange,
    className
}: Props) {
    const toNum = (v?: string) => {
        const n = Number(v);
        return Number.isFinite(n) ? n : undefined;
    };

    const clear = () => {
        onMinChange(undefined);
        onMaxChange(undefined);
    };

    return (
        <div className="flex flex-col gap-1 border-1 p-2 rounded-xl border-form-element">
            <div className="flex items-center justify-between">
                
                <label className="text-sm font-medium text-secondary">{label}</label>
                {(minValue !== undefined || maxValue !== undefined) && (
                    <button
                        type="button"
                        onClick={clear}
                        className="h-5 px-1 rounded-lg border border-form-element text-secondary hover:text-primary hover:border-primary"
                        title={`Clear ${label}`}
                    >
                        <FaTimes />
                    </button>
                )}
            </div>
            <div className={`flex items-end gap-2 ${className || ""}`}>
                <div className="flex-1">
                    <FormInput
                        type="number"
                        inputMode="numeric"
                        label=''
                        placeholder="Min"
                        value={minValue?.toString() || ""}
                        onChange={(v) => onMinChange(toNum(v || undefined))}
                    />
                </div>
                <div className="flex-1">
                    <FormInput
                        type="number"
                        inputMode="numeric"
                        label=''
                        placeholder="Max"
                        value={maxValue?.toString() || ""}
                        onChange={(v) => onMaxChange(toNum(v || undefined))}
                    />
                </div>
            </div>
        </div>
    );
}