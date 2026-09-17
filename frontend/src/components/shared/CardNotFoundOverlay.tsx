import { FaTriangleExclamation } from 'react-icons/fa6';

type CardNotFoundOverlayProps = {
    variant?: 'field' | 'row';
    /** Player name and/or MLB id to surface, so it's clear who the missing card belongs to. */
    playerName?: string;
    playerId?: number | string;
};

/**
 * Overlay shown over a card slot/placeholder when the underlying record (e.g. an award
 * recipient or roster assignment) is known but no matching card could be found in the card
 * database — distinguishes "we looked and found nothing" from a plain empty/add slot.
 *
 * `field` = on the dark field art (FieldView); `row` = on a panel background (list/section rows).
 */
export function CardNotFoundOverlay({ variant = 'field', playerName, playerId }: CardNotFoundOverlayProps) {
    const detail = playerName || playerId != null
        ? [playerName, playerId != null ? `#${playerId}` : undefined].filter(Boolean).join(' ')
        : undefined;

    return (
        <div
            className={`absolute inset-0 z-20 flex flex-col items-center justify-center gap-1 rounded-lg px-1.5 text-center backdrop-blur-[1px] pointer-events-none ${
                variant === 'field' ? 'bg-black/55' : 'bg-(--background-primary)/75'
            }`}
            title={detail ? `Card not found: ${detail}` : 'Card not found'}
        >
            <FaTriangleExclamation
                className={variant === 'field' ? 'text-white/90 text-sm' : 'text-(--text-secondary) text-xs'}
            />
            <span
                className={`text-[8px] font-semibold uppercase tracking-wide ${
                    variant === 'field' ? 'text-white/80' : 'text-(--text-secondary)'
                }`}
            >
                Card Not Found
            </span>
            {detail && (
                <span
                    className={`text-[8px] font-medium leading-tight line-clamp-2 ${
                        variant === 'field' ? 'text-white/70' : 'text-(--text-tertiary)'
                    }`}
                >
                    {detail}
                </span>
            )}
        </div>
    );
}
