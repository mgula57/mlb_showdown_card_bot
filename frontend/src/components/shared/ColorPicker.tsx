import { useState } from 'react';

type ColorPickerProps = {
    label: string;
    value: string;       // "rgb(r, g, b)"
    onChange: (value: string) => void;
};

function rgbToHex(rgb: string): string {
    const match = rgb.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
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
    const [hex, setHex] = useState(rgbToHex(value));

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newHex = e.target.value;
        setHex(newHex);
        onChange(hexToRgb(newHex));
    };

    return (
        <div className="flex flex-col gap-1">
            <label className="text-[11px] font-semibold text-(--text-secondary) uppercase tracking-wide">
                {label}
            </label>
            <div className="flex items-center gap-2">
                <input
                    type="color"
                    value={hex}
                    onChange={handleChange}
                    className="w-8 h-8 rounded border border-(--divider) cursor-pointer p-0"
                />
                <span className="text-[12px] text-(--text-secondary) font-mono">{value}</span>
            </div>
        </div>
    );
}
