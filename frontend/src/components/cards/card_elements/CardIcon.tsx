import { getContrastTextColor } from "../../../functions/colors";

/**
 * Props for the CardIcon component
 */
type CardIconProps = {
    /** Complete card data containing chart ranges and styling information */
    color: string;
    value: string;
    circleSize: CircleSize;
    textSize: number;
};

type CircleSize = '3' | '4';

/** Full class strings so Tailwind can see them (it can't read `w-${size}`). */
const CIRCLE_SIZE_CLASSES: Record<CircleSize, string> = {
    '3': 'w-3 h-3',
    '4': 'w-4 h-4',
};

/**
 * CardIcon component displays an icon with a specified color and value.
 */
const CardIcon = ({ color, value, circleSize, textSize }: CardIconProps) => {
    const contrastColor = getContrastTextColor(color);
    const twoDigitTextSize = value.length === 2 ? (textSize - 1) : textSize;

    return (
        <div
            className={`
                ${CIRCLE_SIZE_CLASSES[circleSize]} flex items-center justify-center
                font-display-upright uppercase leading-none
                rounded-full shrink-0
            `}
            style={{ backgroundColor: color, color: contrastColor, fontSize: `${twoDigitTextSize}px` }}
        >
            {value}
        </div>
    );
};

export default CardIcon;