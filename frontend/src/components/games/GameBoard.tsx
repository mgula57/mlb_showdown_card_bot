/**
 * @fileoverview The game board: the field as the surface of the page, with the rest of the
 * situation set around it in named zones. Layout only, so what fills a zone is up to `GameStage`,
 * and new board pieces get a zone here rather than a change to the field.
 *
 * The field is a fan, which leaves the bottom corners of its box empty. A wide board puts the
 * pitcher's and batter's cards there, with what the matchup comes down to between them when
 * there's room (`bottomCenter`), and sizes the field to whatever height is left. A narrow
 * board has no room for that, so it stacks: the field (zoomed by `NARROW_FIELD_ZOOM` until
 * expanded), `footer`, then `below`. On both, the `track` is laid over the top of the field, and
 * the field's own corners hold its controls (see `GameField`).
 */
import type { CSSProperties, ReactNode } from "react";

import { useElementHeight, useElementSize } from "../../hooks/useElementHeight";

import { CARD_ASPECT } from "../cards/CardImageWithChart";
import { FIELD_ART_HEADROOM, FIELD_ART_HEADROOM_PADDING, FIELD_ASPECT } from "./GameField";
import { fullCardWidthIn, MatchupCardRoomContext } from "./matchupCardImages";

/** The page background under the whole board. The field art (`GameField`'s `FieldArt`) is cut out
 *  of its own backdrop, so the field sits straight on this, and the panels around it sit on the
 *  dark rather than on grass. */
function BoardSurface() {
    return <div className="absolute inset-0 -z-10 bg-(--background-primary)" />;
}

/** Space kept clear under the field for the cards along the bottom edge, at least. Taller cards
 *  (a card image's window) push it up to their measured height. */
const BOTTOM_ZONE_REM = 10.75;
const BOTTOM_ZONE = `${BOTTOM_ZONE_REM}rem`;
/** The cards' inset from the stage's bottom edge (`bottom-3`). */
const CARDS_INSET_REM = 0.75;
const CARDS_INSET = `${CARDS_INSET_REM}rem`;
/** Room left between the cards' top edge and the field's corner controls lifted above them. */
const CORNER_GAP = '0.5rem';
/** Only foul ground is below the plate's dirt, so the field's box can sink this far behind the cards. */
const FIELD_SINK = 0.07;
const SIDE_GUTTER_REM = 1.5;
const SIDE_GUTTER = `${SIDE_GUTTER_REM}rem`;

/** Collapsed, no one stands in the deep outfield, so this share of it (the wall and the grass in
 *  front of it, short of where the center fielder stands) runs up under the score track, which is
 *  laid over the field like the other panels, so the field reads as continuing beneath it. */
const OUTFIELD_TUCK = 0.6;
/** Height of the deep outfield left showing, as a share of the field box's height. */
const COLLAPSED_HEADROOM = FIELD_ART_HEADROOM * (1 - OUTFIELD_TUCK);

/** Room kept between the collapsed field and the cards. */
const FIELD_GAP_REM = 0.5;
/** px per rem, for sizing in script what the stage sizes in CSS. */
const REM_PX = 16;
/** A corner card's own chrome above its image: the label strip and the gap under it. */
const CORNER_CARD_CHROME_PX = 28;
/** A corner at its widest (a `CardItem`'s width), and the gap between it and the center panel. */
const CORNER_MAX_WIDTH_PX = 340;
const CORNERS_GAP_PX = 12;
/** The center panel shows only when it gets at least this width between the corners. */
const CENTER_MIN_WIDTH_PX = 208;

/** What the corner cards show, which sets how the field and the cards split the stage's height. */
export type BoardCardView = "image" | "item";

/** The collapsed field's width per px of height, its deep outfield included. */
const FIELD_WIDTH_PER_HEIGHT = FIELD_ASPECT / (1 - FIELD_SINK + COLLAPSED_HEADROOM);
/** With card images, the field grows first, to here. The cards get the height after that, and once
 *  they're whole cards a corner wide (`FULL_CARDS_ZONE_PX`), the field grows again. Card items are
 *  short and stay that way, so with them the field takes all the room the stage has. */
const IMAGE_FIELD_MAX_WIDTH_REM = 46;
/** The bottom zone holding whole card images at a corner's full width. */
const FULL_CARDS_ZONE_PX = CORNER_MAX_WIDTH_PX / CARD_ASPECT + CORNER_CARD_CHROME_PX + CARDS_INSET_REM * REM_PX;

/** The field's width cap for `cardView`, in CSS, or none. */
function fieldMaxWidth(cardView: BoardCardView): string | null {
    if (cardView === "item") return null;
    return `max(${IMAGE_FIELD_MAX_WIDTH_REM}rem, (100cqh - ${FULL_CARDS_ZONE_PX}px - ${FIELD_GAP_REM}rem) * ${FIELD_WIDTH_PER_HEIGHT})`;
}

/** How tall a corner card's image can stand (`MatchupCardRoomContext`) on a stage this size: the
 *  height left under the field at its `fieldMaxWidth` for card images. Mirrors `fieldStyle`'s
 *  collapsed sizing. */
function cornerCardRoom(stageWidth: number, stageHeight: number): number {
    const gap = FIELD_GAP_REM * REM_PX;
    const cap = Math.max(IMAGE_FIELD_MAX_WIDTH_REM * REM_PX, (stageHeight - FULL_CARDS_ZONE_PX - gap) * FIELD_WIDTH_PER_HEIGHT);
    const fieldWidth = Math.min(cap, stageWidth - SIDE_GUTTER_REM * REM_PX, (stageHeight - BOTTOM_ZONE_REM * REM_PX - gap) * FIELD_WIDTH_PER_HEIGHT);
    return Math.max(0, stageHeight - gap - fieldWidth / FIELD_WIDTH_PER_HEIGHT - CARDS_INSET_REM * REM_PX - CORNER_CARD_CHROME_PX);
}

/** Fits the field to the stage, the smallest of its width, `maxWidth` and what its height allows, above
 *  `bottomZone` (the cards' height, or `BOTTOM_ZONE`, whichever is taller). The field's
 *  height counts the art's deep outfield above the box (`FIELD_ART_HEADROOM`, the top padding
 *  `GameField` leaves for it). Expanded, the art clears the cards and all of the outfield shows,
 *  since that's where the outfielders stand, and `GameField`'s own bottom padding is what the
 *  `3rem` takes back out. Collapsed, the field rides up until `OUTFIELD_TUCK` of the outfield is
 *  behind the track, which also lifts the plate clear of the cards in the bottom corners. It only
 *  sinks behind them (`FIELD_SINK`) when the height runs out.
 *
 *  Either way the field's bottom corners can end up behind the cards, so `--field-corner-lift`
 *  tells `GameField` how far to raise its corner controls to clear the cards' top (`cardsTop`, from
 *  the stage's bottom edge). And since the field can stop short of the stage's sides,
 *  `--field-corner-reach` tells it how far past its sides the stage runs, so its corner controls
 *  can sit out over the cards at the stage's edges rather than at the field's. */
function fieldStyle(isExpanded: boolean, bottomZone: string, cardsTop: string, maxWidth: string | null): CSSProperties {
    const heightLimit = isExpanded
        ? `(100cqh - ${bottomZone}) * ${FIELD_ASPECT / (1 + FIELD_ART_HEADROOM)}`
        : `(100cqh - ${bottomZone} - ${FIELD_GAP_REM}rem) * ${FIELD_WIDTH_PER_HEIGHT}`;
    const bottom = isExpanded
        ? `(${bottomZone} - 3rem)`
        : `max(${bottomZone} - var(--field-width) * ${FIELD_SINK / FIELD_ASPECT}, 100cqh - var(--field-width) * ${(1 + COLLAPSED_HEADROOM) / FIELD_ASPECT})`;
    return {
        '--field-width': `min(${maxWidth ? `${maxWidth}, ` : ''}100cqw - ${SIDE_GUTTER}, ${heightLimit})`,
        '--field-corner-lift': `max(0px, ${cardsTop} + ${CORNER_GAP} - ${bottom})`,
        '--field-corner-reach': `max(0px, (100cqw - var(--field-width)) / 2 - ${CARDS_INSET})`,
        // The field's height (its deep outfield, the box inside `GameField`'s `px-1`, and the
        // catcher's padding when expanded) past the stage's top is under the track.
        '--field-top-cover': `max(0px, var(--field-width) * ${FIELD_ART_HEADROOM / FIELD_ASPECT} + (var(--field-width) - 0.5rem) / ${FIELD_ASPECT}${isExpanded ? ' + 3rem' : ''} + ${bottom} - 100cqh)`,
        width: 'var(--field-width)',
        bottom: `calc(${bottom})`,
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
        // At most the track's clearance is under the track (less when the outfield is shorter
        // than that, which only keeps the OF etching a little lower than it needs to be).
        '--field-top-cover': `${isExpanded ? 0 : trackClearance}px`,
    } as CSSProperties;
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
    /** Wide only: between the corner cards, when there's room for it. Fills the cards' height
     *  without adding to it, cutting off what doesn't fit. */
    bottomCenter?: ReactNode;
    /** Wide only: see `BoardCardView`. */
    cardView?: BoardCardView;
    /** Takes over the bottom edge when there's no matchup for the corners, e.g. probable pitchers. */
    bottomSpan?: ReactNode;
    /** Narrow only: under the footer. */
    below?: ReactNode;
};

export default function GameBoard({
    isWide, track, field, overlay, footer, isFieldExpanded = false,
    bottomLeft, bottomRight, bottomCenter, cardView = "item", bottomSpan, below,
}: GameBoardProps) {
    const [trackRef, trackHeight] = useElementHeight<HTMLDivElement>();
    const [cardsRef, cardsHeight] = useElementHeight<HTMLDivElement>();
    const [stageRef, stageSize] = useElementSize<HTMLDivElement>();

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

    // Measured, so taller cards (a card image's window) push the field up rather than covering it
    const hasCards = !overlay && cardsHeight > 0;
    const cardsTop = hasCards ? `(${cardsHeight}px + ${CARDS_INSET})` : '0px';
    const bottomZone = hasCards ? `max(${BOTTOM_ZONE}, ${cardsTop})` : BOTTOM_ZONE;
    // Card images: whole cards as wide as the room under the field allows, up to a corner's width
    const cardRoom = cardView === "image" ? cornerCardRoom(stageSize.width, stageSize.height) : null;
    const cornerWidth = Math.min(CORNER_MAX_WIDTH_PX, (cardRoom != null ? fullCardWidthIn(cardRoom) : null) ?? CORNER_MAX_WIDTH_PX);
    const centerWidth = stageSize.width - 2 * CARDS_INSET_REM * REM_PX - 2 * (cornerWidth + CORNERS_GAP_PX);

    return (
        <div className="relative isolate flex h-full min-w-0 items-start justify-center overflow-hidden">
            <BoardSurface />
            {/* Bounded across, so on a wide monitor the zones stay gathered around the field rather
                than following the corners of the screen. It takes the window's full height: the
                field and the corner cards split it (`fieldMaxWidth`). */}
            <div className="flex h-full w-full max-w-[68rem] min-w-0 flex-col">
                <div className="relative z-10 shrink-0 px-3 pt-3">{track}</div>

                <div ref={stageRef} className="relative min-h-0 flex-1" style={{ containerType: 'size' }}>
                    <div className="absolute left-1/2 z-0 -translate-x-1/2 transition-[width,bottom] duration-300 ease-out" style={fieldStyle(isFieldExpanded, bottomZone, cardsTop, fieldMaxWidth(cardView))}>
                        {field}
                    </div>

                    {!overlay && (
                        <>
                            {bottomSpan ? (
                                <div ref={cardsRef} className="absolute inset-x-3 bottom-3 z-10">{bottomSpan}</div>
                            ) : (
                                <MatchupCardRoomContext.Provider value={cardRoom}>
                                    <div ref={cardsRef} className="pointer-events-none absolute inset-x-3 bottom-3 z-10 flex items-end gap-3">
                                        <div className="pointer-events-auto min-w-0 shrink-0" style={{ width: cornerWidth }}>{bottomLeft}</div>
                                        {/* Laid out of flow, so the cards alone set the row's height */}
                                        <div className="relative min-w-0 flex-1 self-stretch">
                                            {bottomCenter && centerWidth >= CENTER_MIN_WIDTH_PX && (
                                                <div className="pointer-events-auto absolute inset-0">{bottomCenter}</div>
                                            )}
                                        </div>
                                        <div className="pointer-events-auto min-w-0 shrink-0" style={{ width: cornerWidth }}>{bottomRight}</div>
                                    </div>
                                </MatchupCardRoomContext.Provider>
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
