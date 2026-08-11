/**
 * @fileoverview The bases-and-outs bug, previously reimplemented inline in both GameItem and
 * GameDetail's MatchupStrip at different sizes. Occupancy only — see GameField for the
 * full-size field with named runners.
 *
 * Every dimension (base markers, pips, gaps, box) is a fraction of the `size` number, so the
 * whole graphic scales continuously instead of jumping between fixed presets.
 */
import type { CSSProperties } from "react";

type BasesDiamondProps = {
    bases?: { first: unknown; second: unknown; third: unknown };
    /** Renders a row of out pips below the diamond when provided. */
    outs?: number;
    /** Diamond bounding-box diameter in pixels — everything else scales proportionally from
     * this one number. "sm"/"md" are convenience presets for the previous fixed sizes. */
    size?: number | "sm" | "md";
    className?: string;
};

const SIZE_PRESETS: Record<"sm" | "md", number> = { sm: 36, md: 48 };

export function BasesDiamond({ bases, outs, size = "sm", className = "" }: BasesDiamondProps) {
    const bd = typeof size === "number" ? size : SIZE_PRESETS[size];
    const occupied = (base: unknown) =>
        base ? "bg-(--live) border-(--live)" : "bg-transparent border-(--secondary)/40";
    const outCount = Math.max(0, Math.min(3, outs ?? 0));

    // Geometry, all in px derived from `bd`. The cluster is built from its own dimensions first
    // (marker size → its rotated half-diagonal → the vertical/horizontal gaps between markers),
    // then the box is sized to hug that cluster with a small margin — so there's no dead space
    // around it the way a plain square box left below the 1st/3rd row (home plate isn't drawn).
    const markerSize = bd * 0.3;
    const halfDiagonal = markerSize * Math.SQRT1_2; // center-to-corner distance of the rotated (45°) square
    const spreadY = bd * 0.34; // vertical gap between 2nd's center and the 1st/3rd row
    const halfSpreadX = bd * 0.27; // horizontal gap from center to 1st or 3rd
    const pad = bd * 0.05;

    const boxWidth = halfSpreadX * 2 + halfDiagonal * 2 + pad * 2;
    const boxHeight = spreadY + halfDiagonal * 2 + pad * 2;
    const centerX = boxWidth / 2;
    const secondY = halfDiagonal + pad;
    const cornerY = secondY + spreadY;

    const markerStyle = (x: number, y: number): CSSProperties => ({
        width: markerSize,
        height: markerSize,
        left: x,
        top: y,
        transform: "translate(-50%, -50%) rotate(45deg)",
    });
    const pipStyle: CSSProperties = { width: bd * 0.2222, height: bd * 0.2222 };

    return (
        <div className={`flex flex-col items-center ${className}`} style={{ gap: bd * 0.1 }}>
            <div className="relative" style={{ width: boxWidth, height: boxHeight }}>
                <div className={`absolute border transition-colors duration-300 ${occupied(bases?.second)}`} style={markerStyle(centerX, secondY)} />
                <div className={`absolute border transition-colors duration-300 ${occupied(bases?.third)}`} style={markerStyle(centerX - halfSpreadX, cornerY)} />
                <div className={`absolute border transition-colors duration-300 ${occupied(bases?.first)}`} style={markerStyle(centerX + halfSpreadX, cornerY)} />
            </div>

            {outs != null && (
                <div className="flex items-center" style={{ gap: bd * 0.1 }}>
                    {[0, 1, 2].map((index) => (
                        <span
                            key={index}
                            className={`rounded-full border transition-colors duration-300 ${index < outCount ? "bg-(--live) border-(--live)" : "border-(--secondary)/40"}`}
                            style={pipStyle}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

export default BasesDiamond;
