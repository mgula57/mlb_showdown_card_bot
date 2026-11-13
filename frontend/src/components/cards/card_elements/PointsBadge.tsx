import { getContrastTextColor } from "../../../functions/colors";

export default function PointsBadge({ points, bg_color, textColor, className }: { points: number, bg_color?: string | null, textColor?: string, className?: string }) {
    return (
        <span
            className={`inline-flex items-center justify-center min-w-5 px-1 py-0.5 rounded-plate text-[9px] font-bold leading-none text-nowrap ${className ?? ''}`}
            style={
                { backgroundColor: bg_color ?? 'var(--secondary)/15', color: textColor ?? getContrastTextColor(bg_color ?? 'var(--secondary)/15') }}
        >
            {points} PT
        </span>
    );
}
