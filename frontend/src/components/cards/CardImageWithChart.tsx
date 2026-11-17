/**
 * @fileoverview A rendered Showdown card seen through a window that zooms to the part that matters
 * right now: the Onbase/Control badge for the pitch, the chart once the advantage is won, with the
 * swing's result lit up on it (the row on 2000-2003 cards, the column on 2004+). The backend says
 * where each part sits (`chart_cell_boxes`, `command_box`), as fractions of the image, so the zoom
 * and highlight fit any display size. The image-first alternative to `CardItem` on the game board.
 *
 * With room (`isFullCard`) the window is the card's own shape and rests on the whole card, zooming
 * in only while a roll plays out. Without it, the window is short and always on one part.
 *
 * A swing being rolled on the chart (`chartDie`) sits at the chart's leading edge while it's in the
 * air, then slides along to the result it landed on as that cell lights up.
 */
import { useState, type ReactNode } from "react";

import type { CardImageBox } from "../../api/liveGame";
import AdvantageBadge from "./card_elements/AdvantageBadge";

/** The rendered card's shape (1488 x 2079, cropped to 63 x 88 mm), as width / height. */
export const CARD_ASPECT = 1488 / 2079;
const CARD_ASPECT_CLASS = "aspect-[1488/2079]";
/** The short window's shape, width / height: about as tall as a `CardItem`. */
const SHORT_WINDOW_ASPECT = 2;
const SHORT_WINDOW_ASPECT_CLASS = "aspect-[2/1]";
/** Room left around the focused part, as a share of the window. */
const FOCUS_PADDING = 0.85;
/** Where a die on the chart sits, as a share of the card: at the leading edge of the chart (its
 *  left on a chart of rows, its top on one of columns), level with the landed cell once there is one. */
function chartDieSpot(chartBox: CardImageBox, cells: CardImageBox[], cell?: CardImageBox) {
    const centers = cells.map(([x, y, w, h]) => [x + w / 2, y + h / 2]);
    const spread = (axis: 0 | 1) => Math.max(...centers.map((c) => c[axis])) - Math.min(...centers.map((c) => c[axis]));
    const isColumns = spread(0) > spread(1);
    const [x, y, w, h] = cell ?? chartBox;
    return isColumns
        ? { left: `${(x + w / 2) * 100}%`, top: `${chartBox[1] * 100}%` }
        : { left: `${chartBox[0] * 100}%`, top: `${(y + h / 2) * 100}%` };
}

/** Card widths across the window at most, so a small badge keeps some of its surroundings. */
const MAX_ZOOM = 3;

/** What the window shows: the whole card (a full-card window only), or zoomed to one part. */
export type CardImageFocus = "card" | "command" | "chart";

const windowAspectClass = (isFullCard: boolean) => (isFullCard ? CARD_ASPECT_CLASS : SHORT_WINDOW_ASPECT_CLASS);

/** The smallest box holding every box given. */
function unionBox(boxes: CardImageBox[]): CardImageBox | undefined {
    if (boxes.length === 0) return undefined;
    const left = Math.min(...boxes.map(([x]) => x));
    const top = Math.min(...boxes.map(([, y]) => y));
    const right = Math.max(...boxes.map(([x, , w]) => x + w));
    const bottom = Math.max(...boxes.map(([, y, , h]) => y + h));
    return [left, top, right - left, bottom - top];
}

/** Where the card sits behind a window of `windowAspect` to center `focus` in it, as CSS
 *  percentages of the window: the card's width and its left/top offsets. Zooms to fit the focus
 *  with some padding, no further than `MAX_ZOOM`, and never so far out the card leaves a gap at the
 *  window's edge. */
function framing([x, y, w, h]: CardImageBox, windowAspect: number) {
    const windowHeight = 1 / windowAspect; // in window widths
    // Card width in window widths: fit the focus's width and height, whichever is tighter
    const fitWidth = 1 / w;
    const fitHeight = windowHeight / (h / CARD_ASPECT);
    const cardWidth = Math.max(1, Math.min(MAX_ZOOM, Math.min(fitWidth, fitHeight) * FOCUS_PADDING));
    const cardHeight = cardWidth / CARD_ASPECT;
    const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));
    const left = clamp(0.5 - (x + w / 2) * cardWidth, 1 - cardWidth, 0);
    const top = clamp(windowHeight / 2 - (y + h / 2) * cardHeight, windowHeight - cardHeight, 0);
    return { width: `${cardWidth * 100}%`, left: `${left * 100}%`, top: `${(top / windowHeight) * 100}%` };
}

type CardImageWithChartProps = {
    imageUrl: string;
    /** Each chart result's box, keyed by result ("1B+"). */
    chartCells: Record<string, CardImageBox>;
    commandBox: CardImageBox;
    /** What the window shows. */
    focus: CardImageFocus;
    /** The window takes the card's shape, so `focus` "card" shows all of it. */
    isFullCard?: boolean;
    name?: string;
    /** The chart result the swing landed on (e.g. "1b+"), any case. */
    chartHighlight?: string;
    hasAdvantage?: boolean;
    /** A swing being rolled on this chart: a copy of its die (`RollMirrors`'s `MiniDie`). */
    chartDie?: ReactNode;
    onClick?: () => void;
    className?: string;
};

export default function CardImageWithChart({ imageUrl, chartCells, commandBox, focus, isFullCard = false, name, chartHighlight, hasAdvantage, chartDie, onClick, className = "" }: CardImageWithChartProps) {
    // Track which URL loaded so a new card shows its skeleton until its own image is in
    const [loadedUrl, setLoadedUrl] = useState<string | null>(null);
    const isLoaded = loadedUrl === imageUrl;
    const highlightKey = chartHighlight?.toLowerCase();
    const cell = highlightKey ? Object.entries(chartCells).find(([key]) => key.toLowerCase() === highlightKey)?.[1] : undefined;
    const chartBox = unionBox(Object.values(chartCells));
    const focusBox: CardImageBox = (focus === "card" && isFullCard)
        ? [0, 0, 1, 1]
        : (focus === "chart" ? chartBox : undefined) ?? commandBox;

    return (
        <div className={`relative ${className}`}>
            {hasAdvantage && <AdvantageBadge />}
            <div
                // A size container, so what's laid on the card (`chartDie`) can size off it
                className={`@container relative ${windowAspectClass(isFullCard)} w-full overflow-hidden rounded-trading-card border border-(--divider) bg-(--background-tertiary) ${onClick ? "cursor-pointer" : ""} ${hasAdvantage ? "card-advantage" : ""}`}
                onClick={onClick}
                title={name}
            >
                {!isLoaded && <div aria-hidden className="absolute inset-0 animate-pulse bg-(--background-tertiary)" />}
                {/* The whole card, slid and scaled behind the window */}
                <div
                    className={`absolute ${CARD_ASPECT_CLASS} transition-[left,top,width] duration-500 ease-out ${isLoaded ? "" : "opacity-0"}`}
                    style={framing(focusBox, isFullCard ? CARD_ASPECT : SHORT_WINDOW_ASPECT)}
                >
                    <img src={imageUrl} alt={name ?? "Card"} onLoad={() => setLoadedUrl(imageUrl)} className="absolute inset-0 h-full w-full" />
                    {isLoaded && cell && (
                        <div
                            // Keyed on the result so the landing replays for every new swing
                            key={`${imageUrl}|${highlightKey}`}
                            aria-hidden
                            className="chart-image-cell-landed pointer-events-none absolute rounded-plate"
                            style={{ left: `${cell[0] * 100}%`, top: `${cell[1] * 100}%`, width: `${cell[2] * 100}%`, height: `${cell[3] * 100}%` }}
                        />
                    )}
                    {isLoaded && chartDie && chartBox && (
                        <div
                            aria-hidden
                            className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-1/2 transition-[left,top] duration-300 ease-out"
                            style={chartDieSpot(chartBox, Object.values(chartCells), cell)}
                        >
                            {chartDie}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export function CardImageSkeleton({ isFullCard = false, className = "" }: { isFullCard?: boolean; className?: string }) {
    return <div aria-hidden className={`${windowAspectClass(isFullCard)} w-full animate-pulse rounded-trading-card border border-(--divider) bg-(--background-tertiary) ${className}`} />;
}
