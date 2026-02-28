/** Enhance the visibility of colors based on the theme */
export const enhanceColorVisibility = (color: string) => {
    const isDarkMode = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');

    if (isDarkMode) {
        return `color-mix(in srgb, ${color} 70%, white 30%)`;
    }

    return `color-mix(in srgb, ${color} 85%, black 15%)`;
};

const parseToRgb = (input: string): [number, number, number] | null => {
    const color = input.trim();

    if (color.startsWith('#')) {
        const hex = color.slice(1);
        if (hex.length === 3) {
            return [
                parseInt(hex[0] + hex[0], 16),
                parseInt(hex[1] + hex[1], 16),
                parseInt(hex[2] + hex[2], 16),
            ];
        }
        if (hex.length === 6) {
            return [
                parseInt(hex.slice(0, 2), 16),
                parseInt(hex.slice(2, 4), 16),
                parseInt(hex.slice(4, 6), 16),
            ];
        }
    }

    const match = color.match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i);
    if (match) {
        return [Number(match[1]), Number(match[2]), Number(match[3])];
    }

    return null;
};

const toLinear = (value: number): number => {
    const normalized = value / 255;
    return normalized <= 0.03928 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
};

const luminance = ([r, g, b]: [number, number, number]): number => {
    return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
};

const contrastRatioWithWhite = (rgb: [number, number, number]): number => {
    const whiteLuminance = 1;
    return (whiteLuminance + 0.05) / (luminance(rgb) + 0.05);
};

const mixWithBlack = ([r, g, b]: [number, number, number], amount: number): [number, number, number] => {
    const clamped = Math.max(0, Math.min(1, amount));
    return [
        Math.round(r * (1 - clamped)),
        Math.round(g * (1 - clamped)),
        Math.round(b * (1 - clamped)),
    ];
};

/**
 * Darken a color only when it is too bright against a white background.
 *
 * Returns original color when contrast is already sufficient.
 */
export const darkenIfLowContrastOnWhite = (
    color: string,
    minContrast = 3.5,
    stepPercent = 5,
    maxDarkenPercent = 60
): string => {
    const rgb = parseToRgb(color);
    if (!rgb) {
        return color;
    }

    if (contrastRatioWithWhite(rgb) >= minContrast) {
        return color;
    }

    const maxSteps = Math.floor(maxDarkenPercent / stepPercent);
    for (let step = 1; step <= maxSteps; step += 1) {
        const amount = (step * stepPercent) / 100;
        const candidate = mixWithBlack(rgb, amount);
        if (contrastRatioWithWhite(candidate) >= minContrast) {
            return `rgb(${candidate[0]}, ${candidate[1]}, ${candidate[2]})`;
        }
    }

    const fallback = mixWithBlack(rgb, maxDarkenPercent / 100);
    return `rgb(${fallback[0]}, ${fallback[1]}, ${fallback[2]})`;
};

