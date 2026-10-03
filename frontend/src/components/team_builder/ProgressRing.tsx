/** Tiny donut showing how full a roster bucket is. Inherits the chip's text color via
 *  `currentColor`, and shows a full ring once the bucket meets (or exceeds) its target. */
export function ProgressRing({ filled, target, size = 12, stroke = 2 }: {
    filled: number;
    target: number;
    size?: number;
    stroke?: number;
}) {
    const pct = target > 0 ? Math.min(1, filled / target) : (filled > 0 ? 1 : 0);
    const r = (size - stroke) / 2;
    const circumference = 2 * Math.PI * r;
    return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0 -rotate-90" aria-hidden>
            <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="currentColor" strokeOpacity={0.3} strokeWidth={stroke} />
            <circle
                cx={size / 2} cy={size / 2} r={r}
                fill="none" stroke="currentColor" strokeWidth={stroke} strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={circumference * (1 - pct)}
            />
        </svg>
    );
}
