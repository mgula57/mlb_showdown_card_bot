import { getContrastColor } from "../../shared/Color";

/**
 * Props for the CardIcon component
 */
type CardIconProps = {
    /** Complete card data containing chart ranges and styling information */
    color: string;
    value: string;
    circleSize: string;
    textSize: number;
};

/**
 * CardIcon component displays an icon with a specified color and value.
 */
const CardIcon = ({ color, value, circleSize, textSize }: CardIconProps) => {
    const contrastColor = getContrastColor(color);
    const twoDigitTextSize = value.length === 2 ? (textSize - 1) : textSize;

    return (
        <div 
            className={`
                text-[${twoDigitTextSize}px] flex w-${circleSize} h-${circleSize} 
                items-center font-bold justify-center 
                rounded-full tracking-tight shrink-0
            `} 
            style={{ backgroundColor: color, color: contrastColor }}
        >
            {value}
        </div>
    );
};

export default CardIcon;