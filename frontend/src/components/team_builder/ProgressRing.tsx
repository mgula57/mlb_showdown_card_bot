import type { ReactNode } from 'react';

/** Tiny donut showing how full a roster bucket is. Inherits the chip's text color via
 *  `currentColor`, and shows a full ring once the bucket meets (or exceeds) its target.
 *  `label` is centered inside the ring (size the ring to fit it). */
export function ProgressRing({ filled, target, size = 12, stroke = 2, label }: {
    filled: number;
    target: number;
    size?: number;
    stroke?: number;
    label?: ReactNode;
}) {
    const pct = target > 0 ? Math.min(1, filled / target) : (filled > 0 ? 1 : 0);
    const r = (size - stroke) / 2;
    const circumference = 2 * Math.PI * r;
    const ring = (
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
    if (label === undefined) return ring;
    return (
        <span className="relative inline-flex shrink-0 items-center justify-center" style={{ width: size, height: size }}>
            {ring}
            <span className="absolute inset-0 flex items-center justify-center font-black tabular-nums">{label}</span>
        </span>
    );
}
