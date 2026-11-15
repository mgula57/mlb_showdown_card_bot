/**
 * @fileoverview The game board: the field as the surface of the page, with the rest of the
 * situation set around it in named zones. Layout only, so what fills a zone is up to `GameStage`,
 * and new board pieces get a zone here rather than a change to the field.
 *
 * The field is a fan, which leaves the bottom corners of its box empty. A wide board puts the
 * pitcher's and batter's cards there and sizes the field to whatever height is left. A narrow
 * board has no room for that, so it stacks: the field (zoomed by `NARROW_FIELD_ZOOM` until
 * expanded), `footer`, then `below`. On both, the `track` is laid over the top of the field, and
 * the field's own corners hold its controls (see `GameField`).
 */
import type { CSSProperties, ReactNode } from "react";

import { useElementHeight } from "../../hooks/useElementHeight";

import { FIELD_ART_HEADROOM, FIELD_ART_HEADROOM_PADDING, FIELD_ASPECT } from "./GameField";

/** The page background under the whole board. The field art (`GameField`'s `FieldArt`) is cut out
 *  of its own backdrop, so the field sits straight on this, and the panels around it sit on the
 *  dark rather than on grass. */
function BoardSurface() {
    return <div className="absolute inset-0 -z-10 bg-(--background-primary)" />;
}

/** Space kept clear under the field for the cards along the bottom edge. */
const BOTTOM_ZONE = '10.75rem';
/** Only foul ground is below the plate's dirt, so the field's box can sink this far behind the cards. */
const FIELD_SINK = 0.07;
const SIDE_GUTTER = '1.5rem';
/** The field stops growing here. Past it the page reads as a stadium, not a board at a table, and
 *  the cards drift out of reach of the plate. */
const FIELD_MAX_WIDTH = '50rem';

/** Collapsed, no one stands in the deep outfield, so this share of it (the wall and the grass in
 *  front of it, short of where the center fielder stands) runs up under the score track, which is
 *  laid over the field like the other panels, so the field reads as continuing beneath it. */
const OUTFIELD_TUCK = 0.6;
/** Height of the deep outfield left showing, as a share of the field box's height. */
const COLLAPSED_HEADROOM = FIELD_ART_HEADROOM * (1 - OUTFIELD_TUCK);

/** Fits the field to the stage, the smaller of its width and what its height allows. The field's
 *  height counts the art's deep outfield above the box (`FIELD_ART_HEADROOM`, the top padding
 *  `GameField` leaves for it). Expanded, the art clears the cards and all of the outfield shows,
 *  since that's where the outfielders stand, and `GameField`'s own bottom padding is what the
 *  `3rem` takes back out. Collapsed, the field rides up until `OUTFIELD_TUCK` of the outfield is
 *  behind the track, which also lifts the plate clear of the cards in the bottom corners. It only
 *  sinks behind them (`FIELD_SINK`) when the height runs out. */
function fieldStyle(isExpanded: boolean): CSSProperties {
    const heightLimit = isExpanded
        ? `(100cqh - ${BOTTOM_ZONE}) * ${FIELD_ASPECT / (1 + FIELD_ART_HEADROOM)}`
        : `(100cqh - ${BOTTOM_ZONE} - 0.5rem) * ${FIELD_ASPECT / (1 - FIELD_SINK + COLLAPSED_HEADROOM)}`;
    return {
        '--field-width': `min(${FIELD_MAX_WIDTH}, 100cqw - ${SIDE_GUTTER}, ${heightLimit})`,
        width: 'var(--field-width)',
        bottom: isExpanded
            ? `calc(${BOTTOM_ZONE} - 3rem)`
            : `max(${BOTTOM_ZONE} - var(--field-width) * ${FIELD_SINK / FIELD_ASPECT}, 100cqh - var(--field-width) * ${(1 + COLLAPSED_HEADROOM) / FIELD_ASPECT})`,
    } as CSSProperties;
}

/** How far a narrow board zooms the field (`GameField`'s `zoom`), so first and third sit near the
 *  screen's edges instead of a phone's width going to foul ground. Held where a runner's card on
 *  third or first still clears the edge. */
export const NARROW_FIELD_ZOOM = 1.18;

/** Narrow, the score track is laid over the top of the field rather than stacked above it, so the
 *  field's cell starts below the track (`trackClearance`) and the field reaches back up under it.
 *  Collapsed it reaches up by its whole deep outfield, as far as the top of the board, which keeps
 *  the diamond itself clear of the track. Expanded it stays below the track so the outfielders
 *  stand in the open. A percentage margin is of the width, which is what the field's own headroom
 *  padding is measured against. */
function narrowFieldStyle(isExpanded: boolean, trackClearance: number): CSSProperties {
    return {
        marginTop: isExpanded ? 0 : `calc(-1 * min(${trackClearance}px, ${FIELD_ART_HEADROOM_PADDING} * ${NARROW_FIELD_ZOOM}))`,
    };
}

type GameBoardProps = {
    /** Whether the board has the width for the corner layout. */
    isWide: boolean;
    /** Score and innings, along the top edge. */
    track: ReactNode;
    field: ReactNode;
    /** Laid over the stage, e.g. the post-game recap. Takes the place of the bottom corners. */
    overlay?: ReactNode;
    /** Pinned to the bottom edge, e.g. the transport strip. */
    footer?: ReactNode;
    isFieldExpanded?: boolean;
    bottomLeft?: ReactNode;
    bottomRight?: ReactNode;
    /** Takes over the bottom edge when there's no matchup for the corners, e.g. probable pitchers. */
    bottomSpan?: ReactNode;
    /** Narrow only: under the footer. */
    below?: ReactNode;
};

export default function GameBoard({
    isWide, track, field, overlay, footer, isFieldExpanded = false,
    bottomLeft, bottomRight, bottomSpan, below,
}: GameBoardProps) {
    const [trackRef, trackHeight] = useElementHeight<HTMLDivElement>();

    if (!isWide) {
        // The track's height plus the gap under it.
        const trackClearance = trackHeight + 8;
        return (
            <div className="relative z-10 isolate overflow-x-clip md:min-h-full">
                <BoardSurface />
                <div ref={trackRef} className="absolute inset-x-0 top-0 z-10 pt-2">{track}</div>
                <div className="space-y-2 pb-2">
                    {/* The field and the recap share one grid cell, so the field sits behind the
                        recap rather than pushing it down the column. */}
                    <div className="grid *:col-start-1 *:row-start-1" style={{ paddingTop: trackClearance }}>
                        <div className="relative z-0 transition-[margin] duration-300 ease-out" style={narrowFieldStyle(isFieldExpanded, trackClearance)}>{field}</div>
                        {overlay}
                    </div>
                    {footer}
                    {below}
                </div>
            </div>
        );
    }

    return (
        <div className="relative isolate flex h-full min-w-0 items-start justify-center overflow-hidden">
            <BoardSurface />
            {/* Bounded, so on a large monitor the zones stay gathered around the field rather than
                following the corners of the screen. Centered across but pinned to the top, so the
                score stays at the top of the page on a tall screen. */}
            <div className="flex h-full max-h-[48rem] w-full max-w-[68rem] min-w-0 flex-col">
                <div className="relative z-10 shrink-0 px-3 pt-3">{track}</div>

                <div className="relative min-h-0 flex-1" style={{ containerType: 'size' }}>
                    <div className="absolute left-1/2 z-0 -translate-x-1/2 transition-[width,bottom] duration-300 ease-out" style={fieldStyle(isFieldExpanded)}>
                        {field}
                    </div>

                    {!overlay && (
                        <>
                            {bottomSpan ? (
                                <div className="absolute inset-x-3 bottom-3 z-10">{bottomSpan}</div>
                            ) : (
                                <div className="pointer-events-none absolute inset-x-3 bottom-3 z-10 flex items-end justify-between gap-3">
                                    <div className="pointer-events-auto w-85 min-w-0">{bottomLeft}</div>
                                    <div className="pointer-events-auto w-85 min-w-0">{bottomRight}</div>
                                </div>
                            )}
                        </>
                    )}

                    {overlay && (
                        <div className="absolute inset-0 z-20 flex justify-center overflow-y-auto p-3 scrollbar-hide">
                            <div className="w-full max-w-3xl">{overlay}</div>
                        </div>
                    )}
                </div>

                {footer && <div className="relative z-10 shrink-0 px-3 pb-3">{footer}</div>}
            </div>
        </div>
    );
}
