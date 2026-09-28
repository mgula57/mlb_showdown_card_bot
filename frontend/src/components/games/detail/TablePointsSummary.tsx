import PointsBadge from "../../cards/card_elements/PointsBadge";

export default function TablePointsSummary({ totalPoints, pointsChange, backgroundColor }: { totalPoints: number; pointsChange: number; backgroundColor?: string }) {
    if (totalPoints === 0) return null;

    return (
        <>
            <div className="ml-auto text-[10px] font-bold text-(--quaternary) flex gap-x-2">
                <span className={`${pointsChange < 0 ? 'text-(--red)' : pointsChange > 0 ? 'text-(--green)' : ''}`}>{pointsChange > 0 ? '▲' : pointsChange < 0 ? '▼' : ''}{pointsChange !== 0 ? Math.abs(pointsChange) : ''}</span>
                <PointsBadge points={totalPoints} bg_color={backgroundColor} className="text-[10px]"/>
            </div>
        </>
    );
}
