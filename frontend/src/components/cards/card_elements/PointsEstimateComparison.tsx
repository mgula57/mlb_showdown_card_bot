/**
 * "EST: 5500 ▲610" readout comparing estimated points against actual points.
 * A positive diff (estimated > actual) means the card/team is underpriced, shown in green.
 */
export default function PointsEstimateComparison({ estimated, diff, className, diffClassName }: {
    /** Estimated points value */
    estimated: number;
    /** Estimated minus actual points */
    diff: number;
    className?: string;
    /** Classes for the ▲/▼ diff (e.g. font size) */
    diffClassName?: string;
}) {
    return (
        <div className={`flex items-center ${className ?? ''}`}>
            EST: {estimated}
            {diff !== 0 && (
                <span className={`ml-0.5 ${diffClassName ?? 'text-[8px]'} ${diff > 0 ? 'text-(--green)' : 'text-(--red)'}`}>
                    {diff > 0 ? '▲' : '▼'}
                    {Math.abs(diff)}
                </span>
            )}
        </div>
    );
}
