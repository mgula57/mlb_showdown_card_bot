/**
 * @fileoverview ParallelPreview - Sample of the selected image parallel under its dropdown.
 *
 * Shows a zoomed-in sample with a description. Hovering the sample with a mouse pops the full
 * sample card beside it, portaled to the body so the builder's scrolling form panel can't clip it.
 */

import { useState } from 'react';
import { createPortal } from 'react-dom';
import { PARALLEL_SAMPLE_SET, type ImageParallelOption } from './cardStyle';

/** Full card popover height in px (`h-105`), used to keep it inside the viewport */
const FULL_CARD_HEIGHT = 420;
const POPOVER_GAP = 12;
const VIEWPORT_MARGIN = 8;

export function ParallelPreview({ parallel }: { parallel: ImageParallelOption }) {
    const [fullCardPosition, setFullCardPosition] = useState<{ left: number; top: number } | null>(null);

    // Mouse only: touch has no hover, and a tap shouldn't leave the popover stuck open
    const showFullCard = (event: React.PointerEvent<HTMLImageElement>) => {
        if (event.pointerType !== 'mouse' || !parallel.fullImage) return;
        const rect = event.currentTarget.getBoundingClientRect();
        const centeredTop = rect.top + rect.height / 2 - FULL_CARD_HEIGHT / 2;
        const maxTop = window.innerHeight - FULL_CARD_HEIGHT - VIEWPORT_MARGIN;
        setFullCardPosition({
            left: rect.right + POPOVER_GAP,
            top: Math.max(VIEWPORT_MARGIN, Math.min(centeredTop, maxTop)),
        });
    };

    return (
        <div className="col-span-full -mt-1 flex items-center gap-3">
            <img
                src={parallel.image}
                alt={`${parallel.label} parallel sample`}
                className="h-20 w-auto shrink-0 object-cover rounded-control border border-(--divider) cursor-zoom-in"
                onPointerEnter={showFullCard}
                onPointerLeave={() => setFullCardPosition(null)}
            />
            <div className="text-sm text-(--text-secondary)">
                <p>{parallel.description}</p>
                <p className="mt-1 text-xs text-(--text-tertiary)">Sample on a {PARALLEL_SAMPLE_SET} card</p>
            </div>

            {fullCardPosition && parallel.fullImage && createPortal(
                <img
                    src={parallel.fullImage}
                    alt={`${parallel.label} parallel full card sample`}
                    // design-ok: card art keeps its printed corner radius
                    className="fixed z-1000 h-105 w-auto pointer-events-none rounded-trading-card shadow-overlay border border-(--rule-strong)"
                    style={{ left: fullCardPosition.left, top: fullCardPosition.top }}
                />,
                document.body
            )}
        </div>
    );
}
