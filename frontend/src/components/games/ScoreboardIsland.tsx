/**
 * @fileoverview Tabs that grow out of the bottom edge of the scoreboard when there's something to
 * say and fold back into it when there isn't, the way the iPhone's Dynamic Island does. They hang
 * over the top of the board rather than taking a row, so appearing never pushes the field down, and
 * they're in the scoreboard's layer, so where they cross the field they're always on top.
 *
 *  - The center tab is the game: whose turn it is, a move that failed, the last play.
 *  - A team tab drops from under that club's side of the scoreboard when the club does something:
 *    plays a strategy card, makes a substitution (`TeamAnnouncement`). It says it for a few
 *    seconds, then folds away. On a narrow board the center tab steps aside while one is out, so
 *    the two never overlap.
 */
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";

/** Something a club just did, said under its side of the scoreboard. `key` is unique per move, so
 *  each one drops in fresh. */
export type TeamAnnouncement = { side: "away" | "home"; key: string; content: ReactNode };

/** How long a team tab stays out. */
const TEAM_TAB_MS = 3200;

type Size = { width: number; height: number };

/** Measures `ref`'s box, kept current as it changes. A `ResizeObserver` reports once as soon as it
 *  starts observing, so that's the first measurement too. */
function useBoxSize(ref: React.RefObject<HTMLElement | null>): Size | null {
    const [size, setSize] = useState<Size | null>(null);
    useLayoutEffect(() => {
        const element = ref.current;
        if (!element) return;
        const observer = new ResizeObserver(() => setSize({ width: element.offsetWidth, height: element.offsetHeight }));
        observer.observe(element);
        return () => observer.disconnect();
    }, [ref]);
    return size;
}

/** True from when `key` arrives until `ms` later. A new key starts the clock again. */
function useIsFresh(key: string | undefined, ms: number): boolean {
    const [expired, setExpired] = useState<string | null>(null);
    useEffect(() => {
        if (!key) return;
        const timer = setTimeout(() => setExpired(key), ms);
        return () => clearTimeout(timer);
    }, [key, ms]);
    return !!key && key !== expired;
}

const TAB_POSITION = {
    center: "left-1/2 -translate-x-1/2 justify-center",
    away: "left-4 justify-start",
    home: "right-4 justify-end",
} as const;

const TAB_MAX_WIDTH = {
    center: "max-w-[min(22rem,80vw)]",
    away: "max-w-[min(16rem,44vw)]",
    home: "max-w-[min(16rem,44vw)]",
} as const;

/** One tab. Its own size animates, from a sliver tucked under the scoreboard to the message's
 *  measured size, so it grows out of the edge instead of fading in. Folding away keeps the last
 *  message on screen while it shrinks, rather than emptying first. */
function IslandTab({ content, contentKey, at }: { content?: ReactNode; contentKey: string; at: keyof typeof TAB_POSITION }) {
    const isOpen = !!content;
    const [last, setLast] = useState<{ content: ReactNode; key: string }>({ content, key: contentKey });
    if (isOpen && last.key !== contentKey) setLast({ content, key: contentKey });
    const shown = isOpen ? { content, key: contentKey } : last;

    const innerRef = useRef<HTMLDivElement>(null);
    const size = useBoxSize(innerRef);

    return (
        <div
            aria-live="polite"
            className={`pointer-events-none absolute top-full -mt-px flex ${at === "center" ? "z-20" : "z-30"} ${TAB_POSITION[at]}`}
        >
            <div
                className={`
                    overflow-hidden rounded-b-card border border-t-0 border-(--divider) bg-(--background-primary)
                    transition-[width,height,opacity] duration-300 ease-[cubic-bezier(0.34,1.3,0.64,1)]
                    ${isOpen ? "pointer-events-auto opacity-100" : "opacity-0"}
                `}
                style={{
                    width: isOpen && size ? size.width : 48,
                    height: isOpen && size ? size.height : 0,
                }}
            >
                <div className="bg-(--background-secondary)/30">
                    <div ref={innerRef} className={`w-max px-3 py-1.5 ${TAB_MAX_WIDTH[at]}`}>
                        <div key={shown.key} className={isOpen ? "island-content" : ""}>
                            {shown.content}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

type ScoreboardIslandProps = {
    /** The scoreboard it hangs from. */
    children: ReactNode;
    /** What the center tab says. Nothing (null, false) folds it away. */
    content?: ReactNode;
    /** Changes whenever the message does, so the new one pops in rather than swapping silently. */
    contentKey: string;
    /** What each club just did; the newest for each side drops from under it. */
    announcements?: TeamAnnouncement[];
    /** A narrow board: the center tab steps aside while a team tab is out, since they'd overlap. */
    isNarrow?: boolean;
    className?: string;
};

export default function ScoreboardIsland({ children, content, contentKey, announcements = [], isNarrow = false, className = "" }: ScoreboardIslandProps) {
    const newest = (side: TeamAnnouncement["side"]) => [...announcements].reverse().find((announcement) => announcement.side === side);
    const away = newest("away");
    const home = newest("home");
    const isAwayOut = useIsFresh(away?.key, TEAM_TAB_MS);
    const isHomeOut = useIsFresh(home?.key, TEAM_TAB_MS);
    const isCenterAside = isNarrow && (isAwayOut || isHomeOut);

    return (
        <div className={`relative ${className}`}>
            {children}
            <IslandTab at="center" content={isCenterAside ? null : content} contentKey={contentKey} />
            <IslandTab at="away" content={isAwayOut ? away?.content : null} contentKey={away?.key ?? ""} />
            <IslandTab at="home" content={isHomeOut ? home?.content : null} contentKey={home?.key ?? ""} />
        </div>
    );
}
