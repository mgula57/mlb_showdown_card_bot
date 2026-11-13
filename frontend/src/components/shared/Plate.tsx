import type { CSSProperties, ReactNode } from 'react';

/**
 * The stat box from the card front ("ON-BASE", "SPEED B (15)", "550 PT."): a 2px corner,
 * semibold caps in the body face, tabular numerals. The display italic is reserved for names and titles. Use it for key stats, points and short status tags in
 * place of rounded pills (see frontend/DESIGN.md).
 *
 * - `ink`: the default stat plate (silver in light mode, raised gray in dark mode)
 * - `navy` / `red`: brand emphasis, e.g. OFFICIAL or LIVE
 * - `outline`: quiet status (Draft, awards) that shouldn't compete with stat plates
 * - `success`: positive status (Published)
 * - `onField` / `onFieldOutline`: for plates sitting on a team-color field, which stay dark/white
 *   in both themes
 *
 * Team-colored plates pass `variant="custom"` with `style={{ backgroundColor, color }}`.
 */
export type PlateVariant = 'ink' | 'navy' | 'red' | 'outline' | 'success' | 'onField' | 'onFieldOutline' | 'custom';
export type PlateSize = 'xs' | 'sm' | 'md' | 'lg';

const VARIANT_CLASSES: Record<PlateVariant, string> = {
    ink: 'bg-(--plate) text-(--plate-ink)',
    navy: 'bg-(--showdown-blue-fill) text-white',
    red: 'bg-(--showdown-red-fill) text-white',
    outline: 'text-(--text-secondary) shadow-[inset_0_0_0_1.5px_var(--text-tertiary)]',
    success: 'text-(--green) shadow-[inset_0_0_0_1.5px_var(--green)]',
    onField: 'bg-(--field-ink) text-white',
    onFieldOutline: 'text-white shadow-[inset_0_0_0_1px_rgb(255_255_255/0.6)]',
    custom: '',
};

const TEXT_SIZE_CLASSES: Record<PlateSize, string> = {
    xs: 'text-[8px]',
    sm: 'text-[10px]',
    md: 'text-[13px]',
    lg: 'text-[22px]',
};

const SPACING_CLASSES: Record<PlateSize, string> = {
    xs: 'px-0.5 py-[2px] gap-0.5',
    sm: 'px-1 py-[3px] gap-1',
    md: 'px-1.5 py-1 gap-1.5',
    lg: 'px-2.5 py-1.5 gap-1.5',
};

type PlateProps = {
    children: ReactNode;
    variant?: PlateVariant;
    size?: PlateSize;
    /** Overrides the text size from `size` while keeping its padding. Pass a `PlateSize` to stay on
     *  the plate scale, or any text class (e.g. responsive `'text-[10px] md:text-[13px]'`). */
    textSize?: PlateSize | string;
    className?: string;
    style?: CSSProperties;
    title?: string;
};

export function Plate({ children, variant = 'ink', size = 'md', textSize, className = '', style, title }: PlateProps) {
    const textClass = textSize === undefined ? TEXT_SIZE_CLASSES[size] : (TEXT_SIZE_CLASSES[textSize as PlateSize] ?? textSize);
    return (
        <span
            title={title}
            style={style}
            className={`inline-flex items-center shrink-0 rounded-plate font-semibold uppercase leading-none whitespace-nowrap tabular-nums ${textClass} ${SPACING_CLASSES[size]} ${VARIANT_CLASSES[variant]} ${className}`}
        >
            {children}
        </span>
    );
}

export default Plate;
