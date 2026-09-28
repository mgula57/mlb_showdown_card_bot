/**
 * @fileoverview CardBuildIcon - Composite card-builder icon
 *
 * Recreates the card builder app icon: an outlined 2.5:3.5 card holding a
 * baseball bat and a star. The card is a plain bordered element (no FA glyph
 * is a true trading-card rectangle); the bat and star are `react-icons/fa6`.
 */

import { FaBaseballBatBall, FaStar } from 'react-icons/fa6';

type CardBuildIconProps = {
    /** Overall icon size (any CSS length). Defaults to `1em`. */
    size?: string | number;
    /** Optional extra classes on the wrapper. */
    className?: string;
    /** Accessible label; omit for a purely decorative icon. */
    title?: string;
};

/**
 * CardBuildIcon - Card-builder icon.
 *
 * A borderless wrapper sized `size` x `size` centers an outlined card at the
 * standard trading-card aspect ratio (2.5 : 3.5). Inside it:
 *  - `FaBaseballBatBall` rotated across the middle
 *  - `FaStar` in the top-left corner
 *
 * The card border and bat use `currentColor`; the star is amber. Set the
 * wrapper's `color` (e.g. a Tailwind `text-*` class) to recolor the outline.
 *
 * @example
 * ```tsx
 * <CardBuildIcon size="2.5rem" className="text-sky-500" title="Card Builder" />
 * ```
 */
const CardBuildIcon = ({ size = '1em', className = '', title }: CardBuildIconProps) => (
    <span
        className={`inline-flex items-center justify-center align-middle ${className}`}
        style={{ width: size, height: size }}
        role={title ? 'img' : undefined}
        aria-label={title}
        aria-hidden={title ? undefined : true}
    >
        {/* Outlined card: 2.5 : 3.5, no fill */}
        <span
            className="relative rounded-[0.25em] border-[0.11em] border-current"
            style={{ height: '100%', aspectRatio: '2.75 / 3.5' }}
        >
            {/* Baseball bat laid diagonally across the card */}
            <FaBaseballBatBall
                className="absolute text-current"
                style={{
                    width: '78%',
                    height: '78%',
                    left: '11%',
                    top: '11%',
                    transform: 'rotate(0deg)',
                }}
            />

            {/* Star in the top-left corner */}
            <FaStar
                className="absolute text-current"
                style={{
                    width: '38%',
                    height: '38%',
                    left: '6%',
                    top: '6%',
                }}
            />
        </span>
    </span>
);

export default CardBuildIcon;
