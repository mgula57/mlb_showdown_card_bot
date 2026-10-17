import { FaArrowsUpDownLeftRight, FaSpinner, FaXmark } from 'react-icons/fa6';
import type { CardDatabaseRecord } from '../../api/card_db/cardDatabase';
import type { RosterMoveControls } from '../../hooks/useRosterMove';

type Props = {
    move: RosterMoveControls;
    cardMap: Record<string, CardDatabaseRecord | null>;
    className?: string;
};

/** While a player is being moved: who, what to tap next, and a way out. Shows the last move's
 *  error once it's put down. Renders nothing otherwise. */
export function RosterMoveBanner({ move, cardMap, className = '' }: Props) {
    if (!move.movingCardId) {
        return move.error ? <div className={`text-[12px] text-red-400 ${className}`}>{move.error}</div> : null;
    }
    const name = cardMap[move.movingCardId]?.name ?? 'player';
    return (
        <div className={`flex flex-col gap-1 ${className}`}>
            <div className="flex items-center gap-2 rounded-lg border border-(--secondary)/50 bg-(--secondary)/10 px-3 py-2 text-[12px]">
                {move.isSaving
                    ? <FaSpinner className="shrink-0 animate-spin text-(--secondary)" />
                    : <FaArrowsUpDownLeftRight className="shrink-0 text-(--secondary)" />}
                <span className="flex-1 min-w-0">
                    <span className="font-bold">Moving {name}</span>
                    <span className="text-(--text-secondary)"> · tap an open spot, or a player to swap</span>
                </span>
                <button
                    type="button"
                    onClick={move.cancel}
                    disabled={move.isSaving}
                    aria-label="Cancel move"
                    className="shrink-0 p-1 text-(--text-secondary) hover:text-(--text-primary) cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <FaXmark />
                </button>
            </div>
            {move.error && <span className="text-[12px] text-red-400">{move.error}</span>}
        </div>
    );
}
