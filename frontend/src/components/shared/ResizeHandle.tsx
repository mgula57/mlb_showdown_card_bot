/**
 * @fileoverview The grab edge of a resizable panel (`useResizablePanel`): a hit area straddling the
 * panel's inner border that lights the border navy on hover, focus or drag. Drag it with a
 * mouse, pen or finger, use the arrow keys when it's focused, or double-click to reset.
 * Drop it inside the panel, which must be `relative`.
 */
import type { ResizeHandleProps } from "../../hooks/useResizablePanel";

type Props = ResizeHandleProps & {
    /** What's being resized, for screen readers, e.g. "Resize plays panel". */
    label: string;
    /** A visible grip, for touch screens where there's no hover to find the edge by. */
    showGrip?: boolean;
    className?: string;
};

export function ResizeHandle({ axis, edge, onPointerDown, onKeyDown, onDoubleClick, isResizing, value, min, max, label, showGrip = false, className = "" }: Props) {
    const isX = axis === "x";
    const isEnd = edge === "end";
    return (
        <div
            role="separator"
            tabIndex={0}
            aria-orientation={isX ? "vertical" : "horizontal"}
            aria-label={label}
            aria-valuenow={value ?? undefined}
            aria-valuemin={min}
            aria-valuemax={max}
            title="Drag to resize, double-click to reset"
            onPointerDown={onPointerDown}
            onKeyDown={onKeyDown}
            onDoubleClick={onDoubleClick}
            className={`group absolute z-20 flex touch-none items-center justify-center outline-none ${
                isX
                    ? `${isEnd ? "-left-1.5" : "-right-1.5"} inset-y-0 w-3 cursor-ew-resize`
                    : `${isEnd ? "-top-2" : "-bottom-2"} inset-x-0 h-4 cursor-ns-resize`
            } ${className}`}
        >
            <div className={`transition-colors group-hover:bg-(--showdown-blue) group-focus-visible:bg-(--showdown-blue) ${
                isResizing ? "bg-(--showdown-blue)" : "bg-transparent"
            } ${isX ? "h-full w-0.5" : "h-0.5 w-full"}`} />
            {showGrip && (
                <span className={`absolute rounded-plate bg-(--rule-strong) ${isX ? "h-8 w-1" : "h-1 w-10"}`} />
            )}
        </div>
    );
}

export default ResizeHandle;
