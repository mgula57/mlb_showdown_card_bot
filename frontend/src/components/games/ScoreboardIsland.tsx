/**
 * @fileoverview Tabs that grow out of the bottom edge of the scoreboard when there's something to
 * say and fold back into it when there isn't, the way the iPhone's Dynamic Island does. They hang
 * over the top of the board rather than taking a row, so appearing never pushes the field down, and
 * they're in the scoreboard's layer, so where they cross the field they're always on top.
 *
 *  - The center tab is the last play: it drops when the play lands, says it for a few seconds,
 *    then folds away.
 *  - A team tab hangs under that club's side of the scoreboard while the game waits on the club
 *    (`status`: "Your pitch", "Waiting on the Yankees to swing", a move that failed). When the club
 *    does something (plays a strategy card, makes a substitution: `TeamAnnouncement`) the tab says
 *    that for a few seconds instead, then goes back to the status.
 *  - On a narrow board the tabs would overlap, so the center tab steps aside while an announcement
 *    is out, and a status waits while the last play is out.
 */
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";

import { BOARD_OVERLAY_SURFACE_CLASS } from "./boardStyles";

/** Something a club just did, said under its side of the scoreboard. `key` is unique per move, so
 *  each one drops in fresh. */
export type TeamAnnouncement = { side: "away" | "home"; key: string; content: ReactNode };

/** How long a team announcement stays out. */
const TEAM_TAB_MS = 3200;

/** How long the last play stays out. */
const LAST_PLAY_MS = 4000;

/** What the game is waiting on a club for, said under that club's side until it changes. `key`
 *  changes with the message, so a new one pops in. */
export type TeamStatus = { side: "away" | "home"; key: string; content: ReactNode };

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
                    overflow-hidden rounded-b-card border border-t-0 border-(--divider) ${BOARD_OVERLAY_SURFACE_CLASS}
                    transition-[width,height,opacity] duration-300 ease-[cubic-bezier(0.34,1.3,0.64,1)]
                    ${isOpen ? "pointer-events-auto opacity-100" : "opacity-0"}
                `}
                style={{
                    width: isOpen && size ? size.width : 48,
                    height: isOpen && size ? size.height : 0,
                }}
            >
                <div>
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
    /** What the center tab says (the last play) for a few seconds after it changes. Nothing
     *  (null, false) folds it away. */
    content?: ReactNode;
    /** Changes whenever the message does, so the new one pops in and stays out a while. */
    contentKey: string;
    /** What the game is waiting on a club for, under that club's side. */
    status?: TeamStatus | null;
    /** What each club just did; the newest for each side drops from under it. */
    announcements?: TeamAnnouncement[];
    /** A narrow board: the center tab steps aside while a team tab is out, since they'd overlap. */
    isNarrow?: boolean;
    className?: string;
};

export default function ScoreboardIsland({ children, content, contentKey, status, announcements = [], isNarrow = false, className = "" }: ScoreboardIslandProps) {
    const newest = (side: TeamAnnouncement["side"]) => [...announcements].reverse().find((announcement) => announcement.side === side);
    const away = newest("away");
    const home = newest("home");
    const isAwayOut = useIsFresh(away?.key, TEAM_TAB_MS);
    const isHomeOut = useIsFresh(home?.key, TEAM_TAB_MS);
    const isCenterOut = useIsFresh(content ? contentKey : undefined, LAST_PLAY_MS) && !(isNarrow && (isAwayOut || isHomeOut));
    const isStatusAside = isNarrow && isCenterOut;

    /** A side's tab: its fresh announcement, else what the game is waiting on it for. */
    const sideTab = (side: TeamAnnouncement["side"], announcement: TeamAnnouncement | undefined, isOut: boolean) => {
        if (isOut && announcement) return { content: announcement.content, key: announcement.key };
        if (status?.side === side && !isStatusAside) return { content: status.content, key: `status:${status.key}` };
        return { content: null, key: announcement?.key ?? "" };
    };
    const awayTab = sideTab("away", away, isAwayOut);
    const homeTab = sideTab("home", home, isHomeOut);

    return (
        <div className={`relative ${className}`}>
            {children}
            <IslandTab at="center" content={isCenterOut ? content : null} contentKey={contentKey} />
            <IslandTab at="away" content={awayTab.content} contentKey={awayTab.key} />
            <IslandTab at="home" content={homeTab.content} contentKey={homeTab.key} />
        </div>
    );
}
