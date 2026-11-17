/**
 * @fileoverview A swing being rolled on a `CardItem`'s chart. While the die is in the air it sits
 * large over the card's header (the name and metadata), where there's room for it to read; once the
 * swing lands it shrinks and slides down onto the chart's top edge above the cell it landed on, as
 * that cell lights up. The image card's version is `CardImageWithChart`'s `chartDie`.
 */
import { useLayoutEffect, useState, type ReactNode, type RefObject } from "react";

/** How small the die gets on the chart, from its size over the header. */
const LANDED_SCALE = 0.6;

type Spot = { left: number; top: number; isLanded: boolean };

export function ChartDieOverlay({ cardRef, headerRef, chartRef, highlight, children }: {
    /** The positioned card the die is laid over. */
    cardRef: RefObject<HTMLElement | null>;
    /** Where the die waits: centered over it. */
    headerRef: RefObject<HTMLElement | null>;
    /** The chart, whose cells carry `data-chart-result` (`CardChart`). */
    chartRef: RefObject<HTMLElement | null>;
    /** The result the swing landed on, once it has. */
    highlight?: string;
    children: ReactNode;
}) {
    const [spot, setSpot] = useState<Spot | null>(null);

    // Measured whenever the card resizes (which a ResizeObserver also reports as it starts
    // observing) and as the swing lands, so the die follows the cell wherever the chart has scrolled.
    useLayoutEffect(() => {
        const card = cardRef.current;
        const header = headerRef.current;
        const chart = chartRef.current;
        if (!card || !header || !chart) return;
        const key = highlight?.toLowerCase();
        const observer = new ResizeObserver(() => {
            const base = card.getBoundingClientRect();
            const cell = key ? chart.querySelector<HTMLElement>(`[data-chart-result="${CSS.escape(key)}"]`) : null;
            if (cell) {
                const cellBox = cell.getBoundingClientRect();
                const chartBox = chart.getBoundingClientRect();
                setSpot({ left: cellBox.left + cellBox.width / 2 - base.left, top: chartBox.top - base.top, isLanded: true });
            } else {
                const headerBox = header.getBoundingClientRect();
                setSpot({ left: headerBox.left + headerBox.width / 2 - base.left, top: headerBox.top + headerBox.height / 2 - base.top, isLanded: false });
            }
        });
        observer.observe(card);
        return () => observer.disconnect();
    }, [cardRef, headerRef, chartRef, highlight]);

    // Placed only once measured, so it never slides in from the card's corner
    if (!spot) return null;
    return (
        <div
            aria-hidden
            className="pointer-events-none absolute z-10 transition-[left,top,transform] duration-300 ease-out"
            style={{
                left: spot.left,
                top: spot.top,
                transform: `translate(-50%, -50%) scale(${spot.isLanded ? LANDED_SCALE : 1})`,
            }}
        >
            {children}
        </div>
    );
}
