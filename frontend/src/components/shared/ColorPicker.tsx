type ColorPickerProps = {
    label: string;
    value: string;       // "rgb(r, g, b)" or "#rrggbb"
    onChange: (value: string) => void;
};

/** Converts "rgb(r, g, b)" or hex ("#rgb" / "#rrggbb") to the "#rrggbb" form <input type="color"> requires. */
function toInputHex(color: string): string {
    const hexMatch = color.trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
    if (hexMatch) {
        const digits = hexMatch[1];
        return `#${(digits.length === 3 ? digits.replace(/./g, c => c + c) : digits).toLowerCase()}`;
    }
    const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (!match) return '#000000';
    const r = parseInt(match[1]).toString(16).padStart(2, '0');
    const g = parseInt(match[2]).toString(16).padStart(2, '0');
    const b = parseInt(match[3]).toString(16).padStart(2, '0');
    return `#${r}${g}${b}`;
}

function hexToRgb(hex: string): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgb(${r}, ${g}, ${b})`;
}

export default function ColorPicker({ label, value, onChange }: ColorPickerProps) {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange(hexToRgb(e.target.value));
    };

    return (
        <div className="flex flex-col gap-1">
            <label className="text-[11px] font-semibold text-(--text-secondary) uppercase tracking-wide">
                {label}
            </label>
            <div className="flex items-center gap-2">
                <input
                    type="color"
                    value={toInputHex(value)}
                    onChange={handleChange}
                    className="w-8 h-8 rounded border border-(--divider) cursor-pointer p-0"
                />
                <span className="text-[12px] text-(--text-secondary) font-mono">{value}</span>
            </div>
        </div>
    );
}
