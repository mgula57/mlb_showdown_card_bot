/**
 * @fileoverview The game board: the field as the surface of the page, with the rest of the
 * situation set around it in named zones. Layout only, so what fills a zone is up to `GameStage`,
 * and new board pieces get a zone here rather than a change to the field.
 *
 * The field is a fan, which leaves all four corners of its box empty. A wide board fills them
 * (`corners`) and sizes the field to whatever height is left. A narrow board has no room for
 * that, so it stacks: `track`, field, `footer`, then `below`.
 */
import type { CSSProperties, ReactNode } from "react";

import { FIELD_ART_HEADROOM, FIELD_ASPECT } from "./GameField";

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

/** Collapsed, no one stands in the deep outfield, so the top of it may run this far up behind the
 *  score track rather than shrink the field to fit. */
const OUTFIELD_TUCK = '4rem';

/** Fits the field to the stage, the smaller of its width and what its height allows. The field's
 *  height counts the art's deep outfield above the box (`FIELD_ART_HEADROOM`, the top padding
 *  `GameField` leaves for it). Expanded, the art clears the cards and all of the outfield shows,
 *  since that's where the outfielders stand. `GameField`'s own bottom padding is what the `3rem`
 *  takes back out. */
function fieldStyle(isExpanded: boolean): CSSProperties {
    const heightLimit = isExpanded
        ? `(100cqh - ${BOTTOM_ZONE}) * ${FIELD_ASPECT / (1 + FIELD_ART_HEADROOM)}`
        : `(100cqh - ${BOTTOM_ZONE} - 0.5rem + ${OUTFIELD_TUCK}) * ${FIELD_ASPECT / (1 - FIELD_SINK + FIELD_ART_HEADROOM)}`;
    return {
        '--field-width': `min(${FIELD_MAX_WIDTH}, 100cqw - ${SIDE_GUTTER}, ${heightLimit})`,
        width: 'var(--field-width)',
        bottom: isExpanded
            ? `calc(${BOTTOM_ZONE} - 3rem)`
            : `calc(${BOTTOM_ZONE} - var(--field-width) * ${FIELD_SINK / FIELD_ASPECT})`,
    } as CSSProperties;
}

type GameBoardProps = {
    /** Whether the board has the width for the corner layout. */
    isWide: boolean;
    /** Score and innings, along the top edge. */
    track: ReactNode;
    field: ReactNode;
    /** Laid over the stage, e.g. the post-game recap. Takes the place of every corner but the top left. */
    overlay?: ReactNode;
    /** Pinned to the bottom edge, e.g. the transport strip. */
    footer?: ReactNode;
    /** The player's own moves, above the footer: subs, strategy cards and the like. A roll belongs
     *  on the field, where the die lands. The stage gives up the height this takes. */
    actions?: ReactNode;
    isFieldExpanded?: boolean;
    topLeft?: ReactNode;
    topRight?: ReactNode;
    bottomLeft?: ReactNode;
    bottomRight?: ReactNode;
    /** Between the bottom corners, or under `topRight` once the cards leave it no room. Yields to
     *  the catcher when the field is expanded. */
    center?: ReactNode;
    /** Takes over the bottom edge when there's no matchup for the corners, e.g. probable pitchers. */
    bottomSpan?: ReactNode;
    /** Narrow only: under the footer. */
    below?: ReactNode;
};

export default function GameBoard({
    isWide, track, field, overlay, footer, actions, isFieldExpanded = false,
    topLeft, topRight, bottomLeft, bottomRight, center, bottomSpan, below,
}: GameBoardProps) {
    if (!isWide) {
        return (
            <div className="relative z-10 isolate overflow-x-clip md:min-h-full">
                <BoardSurface />
                <div className="space-y-2 py-2">
                    {track}
                    {/* The field and the recap share one grid cell, so the field sits behind the
                        recap rather than pushing it down the column. */}
                    <div className="grid *:col-start-1 *:row-start-1">
                        {field}
                        {overlay}
                    </div>
                    {actions}
                    {footer}
                    {below}
                </div>
            </div>
        );
    }

    const showCenter = !!center && !bottomSpan && !isFieldExpanded;

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

                    <div className="absolute left-3 top-3 z-10 w-48">{topLeft}</div>
                    {!overlay && (
                        <div className="absolute right-3 top-3 z-10 w-48 space-y-2">
                            {topRight}
                            {showCenter && <div className="@[62rem]:hidden">{center}</div>}
                        </div>
                    )}

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
                            {showCenter && (
                                <div className="absolute bottom-3 left-1/2 z-10 hidden w-[min(22rem,calc(100cqw-45.5rem))] -translate-x-1/2 @[62rem]:block">
                                    {center}
                                </div>
                            )}
                        </>
                    )}

                    {/* Clears the top-left panel, which holds the toggle that dismisses the recap. */}
                    {overlay && (
                        <div className="absolute inset-y-0 left-51 right-0 z-20 flex justify-center overflow-y-auto p-3 scrollbar-hide">
                            <div className="w-full max-w-3xl">{overlay}</div>
                        </div>
                    )}
                </div>

                {actions && <div className="relative z-10 shrink-0 px-3 pb-3">{actions}</div>}
                {footer && <div className="relative z-10 shrink-0 px-3 pb-3">{footer}</div>}
            </div>
        </div>
    );
}
