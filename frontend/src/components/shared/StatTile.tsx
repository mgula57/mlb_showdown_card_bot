import type { ReactNode } from 'react';
import { CAPS_LABEL_CLASS } from './fieldStyles';

type StatTileSize = 'tile' | 'inline';

const SIZE_CLASSES: Record<StatTileSize, { container: string; value: string }> = {
    /** A silver tile with a headline number ("On-Base 9", "Card OPS .912"). */
    tile: {
        container: '@container flex-1 flex flex-col items-center justify-center gap-1 rounded-card py-2.5 px-3 bg-(--background-tertiary)',
        value: 'text-xl @[80px]:text-2xl',
    },
    /** A bare value-over-label pair for a row of small stats (ERA 3.21 · WHIP 1.10). */
    inline: {
        container: 'flex flex-col items-center gap-0.5',
        value: 'text-base',
    },
};

type StatTileProps = {
    label: ReactNode;
    value: ReactNode;
    size?: StatTileSize;
    /** Blurs the value behind placeholder data (empty states). */
    blurred?: boolean;
    className?: string;
};

/** A number over its caps label, the way a card prints a stat: the value in the upright condensed
 *  face with tabular figures, the label in the card-stat caps (see frontend/DESIGN.md). */
export function StatTile({ label, value, size = 'tile', blurred = false, className = '' }: StatTileProps) {
    const classes = SIZE_CLASSES[size];
    return (
        <div className={`${classes.container} ${className}`}>
            <span className={`font-display-upright leading-none tabular-nums ${classes.value} ${blurred ? 'blur-xs' : ''}`}>
                {value}
            </span>
            <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>{label}</span>
        </div>
    );
}

export default StatTile;
