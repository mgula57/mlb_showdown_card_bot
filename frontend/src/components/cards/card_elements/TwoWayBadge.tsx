import { FaBaseballBatBall } from 'react-icons/fa6';
import { Plate, type PlateSize } from '../../shared/Plate';

/**
 * The two-way player (TWP) mark: a navy plate with the bat-and-ball icon. Shown wherever a card
 * carries both a hitting and a pitching side. `iconOnly` drops the text for tight rows.
 */
export function TwoWayBadge({ size = 'sm', iconOnly = false, className = '' }: { size?: PlateSize; iconOnly?: boolean; className?: string }) {
    return (
        <Plate variant="navy" size={size} className={`shrink-0 ${className}`} title="Two-way player: one card that hits and pitches">
            <FaBaseballBatBall className="inline-block w-[1.1em] h-[1.1em]" aria-hidden />
            {iconOnly ? <span className="sr-only">Two-way</span> : <span>TWP</span>}
        </Plate>
    );
}

export default TwoWayBadge;
