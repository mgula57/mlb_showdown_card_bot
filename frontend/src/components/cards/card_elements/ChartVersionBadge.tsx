/**
 * @fileoverview ChartVersionBadge - Flags a card built on an alternate (V2+) chart rather than its
 * most accurate one. Renders nothing for version 1.
 */

type ChartVersionBadgeProps = {
    chartVersion?: number | null;
    className?: string;
    /** Colors in place of the default blue, e.g. the team's colors */
    style?: React.CSSProperties;
};

export default function ChartVersionBadge({ chartVersion, className = '', style }: ChartVersionBadgeProps) {
    if (!chartVersion || chartVersion <= 1) return null;
    return (
        <div
            className={`
                flex items-center justify-center shrink-0
                text-[9px] font-bold leading-none tracking-tight
                rounded-card px-1 py-0.5
                ${style ? '' : 'bg-(--showdown-blue-fill) text-white'}
                ${className}
            `}
            style={style}
            title={`Chart Version ${chartVersion}: uses the card's #${chartVersion} most accurate chart`}
        >
            V{chartVersion}
        </div>
    );
}
